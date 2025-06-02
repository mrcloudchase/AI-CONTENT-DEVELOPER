---
title: Configure Cilium with Azure CNI in Azure Kubernetes Service (AKS)
description: Learn how to enable and configure Cilium as the network dataplane for Azure CNI in AKS, including CiliumEndpointSlices for enhanced networking.
ms.topic: how-to
---

# Configure Cilium with Azure CNI in Azure Kubernetes Service (AKS)

## Introduction

Azure Kubernetes Service (AKS) supports Cilium as the network dataplane for Azure CNI, delivering advanced networking, security, and observability features. By leveraging eBPF and CiliumEndpointSlices, AKS clusters gain dynamic endpoint management, improved service discovery, and efficient network policy enforcement. This guide provides step-by-step instructions for platform engineers to enable, configure, and validate Cilium with Azure CNI in AKS, including best practices for managing CiliumEndpointSlices.

> [!NOTE]
> CiliumEndpointSlices are supported in AKS clusters running Kubernetes version 1.32 and above. Ensure your cluster version meets this requirement before proceeding.

## Prerequisites

- Familiarity with AKS cluster creation and management
- Azure CLI version 2.48.1 or later installed and logged in
- Sufficient permissions to create and configure AKS clusters
- Basic understanding of Kubernetes networking concepts
- For CiliumEndpointSlices, Kubernetes version 1.32 or later is required

> [!WARNING]
> Cilium is only available for Linux-based AKS clusters. Windows node pools are not supported.

> [!TIP]
> Run `az --version` to verify your Azure CLI version. Upgrade if necessary to meet the minimum required version.

## Steps

### 1. Choose a Pod IP Assignment Mode

Cilium with Azure CNI supports multiple pod IP assignment modes. Select the mode that fits your network design:

- **Overlay network**: Assigns pod IPs from a dedicated CIDR, independent of your VNet.
- **Virtual network**: Assigns pod IPs from a dedicated subnet within your Azure VNet.
- **Node subnet**: Assigns pod IPs from the node subnet.

> [!NOTE]
> For overlay and virtual network modes, you must specify the appropriate network and subnet parameters during cluster creation.

### 2. Create a New AKS Cluster with Cilium as the Network Dataplane

#### [Overlay Network](#tab/overlay)

```azurecli
az aks create \
  --name <clusterName> \
  --resource-group <resourceGroupName> \
  --location <location> \
  --network-plugin azure \
  --network-plugin-mode overlay \
  --pod-cidr 192.168.0.0/16 \
  --network-dataplane cilium \
  --generate-ssh-keys
```

#### [Virtual Network](#tab/vnet)

```azurecli
# Create the resource group
az group create --name <resourceGroupName> --location <location>

# Create a virtual network and subnets
az network vnet create \
  --resource-group <resourceGroupName> \
  --location <location> \
  --name <vnetName> \
  --address-prefixes <vnetAddressPrefix> -o none

az network vnet subnet create \
  --resource-group <resourceGroupName> \
  --vnet-name <vnetName> \
  --name nodesubnet \
  --address-prefixes <nodeSubnetPrefix> -o none

az network vnet subnet create \
  --resource-group <resourceGroupName> \
  --vnet-name <vnetName> \
  --name podsubnet \
  --address-prefixes <podSubnetPrefix> -o none

# Create the AKS cluster
az aks create \
  --name <clusterName> \
  --resource-group <resourceGroupName> \
  --location <location> \
  --max-pods 250 \
  --network-plugin azure \
  --vnet-subnet-id /subscriptions/<subscriptionId>/resourceGroups/<resourceGroupName>/providers/Microsoft.Network/virtualNetworks/<vnetName>/subnets/nodesubnet \
  --pod-subnet-id /subscriptions/<subscriptionId>/resourceGroups/<resourceGroupName>/providers/Microsoft.Network/virtualNetworks/<vnetName>/subnets/podsubnet \
  --network-dataplane cilium \
  --generate-ssh-keys
```

#### [Node Subnet](#tab/nodesubnet)

> [!NOTE]
> Azure CLI version 2.69.0 or later is required for this option.

```azurecli
az aks create \
  --name <clusterName> \
  --resource-group <resourceGroupName> \
  --location <location> \
  --network-plugin azure \
  --network-dataplane cilium \
  --generate-ssh-keys
```

---

> [!WARNING]
> Migrating to Cilium may impact existing network policies. Review your policies and test thoroughly before deploying to production.

### 3. Validate Supported Kubernetes and Cilium Versions

| Kubernetes Version | Minimum Cilium Version |
|-------------------|-----------------------|
| 1.27 (LTS)        | 1.13.18               |
| 1.29              | 1.14.19               |
| 1.31              | 1.16.6                |
| 1.32              | 1.17.0                |

> [!NOTE]
> CiliumEndpointSlices require Kubernetes 1.32 or later. See [AKS supported versions](https://learn.microsoft.com/en-us/azure/aks/supported-kubernetes-versions) for details.

### 4. Configure CiliumEndpointSlices

CiliumEndpointSlices enable scalable, dynamic grouping of pod endpoints for efficient service discovery and load balancing. In AKS, CiliumEndpointSlices are enabled by default when using Cilium as the network dataplane on supported Kubernetes versions.

> [!NOTE]
> CiliumEndpointSlices do not support configuration of grouping parameters. Priority namespaces via `cilium.io/ces-namespace` are not supported in AKS.

No manual configuration is required for basic operation. To observe CiliumEndpointSlices:

```azurecli
kubectl get ciliumepslices -A
```

Sample output:
```output
NAMESPACE   NAME                      AGE
kube-system cilium-ces-1234567890     10m
```

To view details:
```azurecli
kubectl describe ciliumepslice <slice-name> -n <namespace>
```

### 5. Enable Observability and Logging

Cilium integrates with Azure Monitor and Log Analytics for enhanced observability. Enable monitoring during cluster creation or via the Azure Portal to collect metrics and logs related to network traffic, endpoint slice health, and policy enforcement.

> [!TIP]
> Use Azure Monitor dashboards to visualize endpoint slice health, latency, and error rates for proactive troubleshooting.

### 6. Best Practices and Troubleshooting

- **Policy Compatibility**: Cilium enforces both Kubernetes and Cilium network policies. ipBlock rules do not apply to pod or node IPs—use namespaceSelector or podSelector for pod-based rules.
- **No Kube-Proxy**: AKS clusters with Cilium do not use kube-proxy. Service routing is handled by Cilium.
- **Resource Management**: AKS does not set CPU or memory limits on the Cilium daemonset, as it is critical for networking.
- **Fallback**: If Cilium fails, AKS reverts to the default endpoint management system.
- **Security**: All communications are encrypted and integrated with Azure Active Directory for authentication and authorization.

> [!WARNING]
> Cilium is not supported for Windows node pools. Ensure all nodes are Linux-based.

## Verification

After deployment, verify that Cilium is running and managing network traffic:

### 1. Check Cilium Pods

```azurecli
kubectl get pods -n kube-system -l k8s-app=cilium
```

Expected output:
```output
NAME           READY   STATUS    RESTARTS   AGE
cilium-xxxxx   1/1     Running   0          5m
```

### 2. Confirm CiliumEndpointSlices

```azurecli
kubectl get ciliumepslices -A
```

### 3. Validate Network Policy Enforcement

Apply a sample network policy and verify traffic is allowed or denied as expected. For example:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-all-egress
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector: {}
    - podSelector: {}
```

> [!NOTE]
> ipBlock rules do not allow traffic to pod or node IPs in Cilium. Use selectors for pod-based rules.

## Next Steps

- Explore advanced Cilium features such as network policies and observability
- Integrate Cilium with GitOps workflows as described in [Use GitOps with Flux v2 in AKS](tutorial-use-gitops-flux2.md)
- Review [AKS release notes](https://learn.microsoft.com/en-us/azure/aks/release-notes) for updates to Cilium support
- For more on AKS extensions, see [Secret Store CSI Driver integration](secret-store-extension.md)

> [!div class="nextstepaction"]
> [Learn more about advanced networking in AKS](https://learn.microsoft.com/en-us/azure/aks/azure-cni-powered-by-cilium)