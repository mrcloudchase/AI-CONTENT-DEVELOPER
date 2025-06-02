---
title: Deploy and configure Cilium with Azure CNI in AKS
description: Learn how to deploy, configure, and validate Cilium as the network plugin for Azure Kubernetes Service (AKS) using Azure CNI powered by Cilium, including CiliumEndpointSlices integration.
ms.topic: how-to
---

# Deploy and configure Cilium with Azure CNI in AKS

## Introduction

Cilium is an advanced, eBPF-based networking solution that brings high-performance networking, enhanced security, and deep observability to Kubernetes environments. In Azure Kubernetes Service (AKS), Azure CNI powered by Cilium combines the robust control plane of Azure CNI with Cilium’s data plane, enabling features such as dynamic endpoint management, efficient service routing, and advanced network policy enforcement.

With the integration of CiliumEndpointSlices, AKS clusters benefit from scalable, real-time management of pod endpoints, improving service discovery, load balancing, and security. This guide walks platform engineers through deploying, configuring, and validating Cilium as the network plugin for AKS using Azure CNI powered by Cilium, including enabling and managing CiliumEndpointSlices.

> [!NOTE]
> CiliumEndpointSlices are supported in AKS clusters running Kubernetes version 1.32 and above. Ensure your AKS version meets this requirement before proceeding.

## Prerequisites

Before you begin, ensure you have the following:

> [!div class="checklist"]
> * Intermediate familiarity with Azure Kubernetes Service (AKS)
> * Access to an Azure subscription with sufficient permissions to create and manage AKS clusters
> * Basic understanding of Kubernetes networking concepts
> * Azure CLI version 2.48.1 or later installed ([Install Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli))
> * `kubectl` installed and configured ([Install kubectl](https://learn.microsoft.com/en-us/azure/aks/kubernetes-walkthrough-portal))

> [!WARNING]
> Cilium and CiliumEndpointSlices are only supported on Linux-based AKS clusters. Windows node pools are not supported with Azure CNI powered by Cilium.

## Steps

### 1. Understand Cilium and Azure CNI Integration in AKS

Azure CNI powered by Cilium leverages:
- **Cilium’s eBPF data plane** for high-performance, kernel-level packet processing
- **Dynamic endpoint management** via CiliumEndpointSlices for scalable and efficient service discovery
- **Advanced network policy enforcement** using Cilium’s native policy engine
- **Enhanced observability** with integration to Azure Monitor and Cilium’s own observability tools

> [!TIP]
> With Cilium, you do not need to install a separate network policy engine such as Azure Network Policy Manager or Calico. Cilium natively enforces Kubernetes network policies and supports additional advanced features.

### 2. Plan Your AKS Cluster Networking

Azure CNI powered by Cilium supports multiple IP assignment models:
- **Overlay network**: Pod IPs are assigned from a dedicated CIDR, not tied to the underlying VNet
- **Virtual network (VNet)**: Pod IPs are assigned from a subnet within your Azure VNet
- **Node subnet**: Pod IPs are assigned from the node subnet

Choose the model that fits your environment and scaling needs. For large-scale clusters or advanced policy requirements, overlay or VNet-based models are recommended.

> [!NOTE]
> CiliumEndpointSlices do not support custom grouping or namespace prioritization. All grouping is managed automatically by AKS.

### 3. Create an AKS Cluster with Azure CNI Powered by Cilium

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
> Ensure your AKS cluster is running Kubernetes version 1.32 or later to enable CiliumEndpointSlices. Earlier versions do not support this feature.

### 4. Configure CiliumEndpointSlices

CiliumEndpointSlices are enabled by default in supported AKS clusters with Azure CNI powered by Cilium. Configuration options such as refresh intervals and slice size thresholds are managed by AKS and cannot be customized directly.

> [!NOTE]
> Manual customization of Cilium configuration is not supported in managed AKS clusters. For advanced customization, consider using BYO CNI and installing Cilium manually.

### 5. Apply and Manage Network Policies

Cilium enforces both Kubernetes `NetworkPolicy` and Cilium-specific L3/L4 policies. Example network policy YAML:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
spec:
  podSelector:
    matchLabels:
      app: backend
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
  policyTypes:
  - Ingress
```

> [!WARNING]
> The following limitations apply:
> - ipBlock rules in NetworkPolicy cannot be used to allow access to pod or node IPs.
> - Network policies are not enforced on pods using host networking (`spec.hostNetwork: true`).
> - ClusterwideCiliumNetworkPolicy is not supported.

### 6. Enable Observability and Monitoring

Cilium integrates with Azure Monitor and Log Analytics for:
- Endpoint slice health and error rates
- Network policy enforcement logs
- Real-time metrics and alerts

To enable advanced observability (FQDN filtering, L7 policies, flow logs), enable Advanced Container Networking Services (ACNS) on your cluster.

> [!TIP]
> Use Azure Monitor dashboards to visualize endpoint slice health and network policy effectiveness.

### 7. Best Practices and Troubleshooting

- **Version Compatibility**: Always verify AKS and Cilium version compatibility before upgrades.
- **Security**: Use RBAC to restrict who can manage network policies and endpoints.
- **Fallback**: If CiliumEndpointSlices encounter errors, AKS will revert to traditional endpoint management to maintain cluster stability.
- **Observability**: Regularly review logs and metrics for synchronization issues or policy enforcement breaches.
- **Scalability**: AKS with CiliumEndpointSlices supports up to 5,000 pods across 500 nodes with near real-time endpoint updates.

> [!WARNING]
> All communications between Cilium components are encrypted and integrated with Azure Active Directory for secure authentication and authorization.

## Verification

After deployment, validate that Cilium and CiliumEndpointSlices are functioning as expected.

### 1. Check Cilium Pods

```azurecli
kubectl get pods -n kube-system -l k8s-app=cilium
```

All Cilium pods should be in the `Running` state.

### 2. Inspect CiliumEndpointSlices

```azurecli
kubectl get ciliumepslices -A
```

This command lists all CiliumEndpointSlices across namespaces. You should see slices dynamically created and updated as pods are added or removed.

### 3. Validate Network Policy Enforcement

Apply a test network policy and verify connectivity is allowed or denied as intended. For example:

```azurecli
kubectl apply -f <network-policy-file>.yaml
```

Test pod-to-pod connectivity using `kubectl exec` or a connectivity test tool.

### 4. Review Observability Data

Check Azure Monitor or Log Analytics dashboards for endpoint slice health, policy enforcement logs, and error rates.

> [!TIP]
> For troubleshooting, refer to Cilium and AKS logs for synchronization failures or policy enforcement issues.

## Next Steps

- Explore advanced Cilium features such as [network policies](https://docs.cilium.io/en/stable/network/kubernetes/), observability, and Hubble integration.
- Integrate Cilium with Azure monitoring and logging tools for enhanced visibility.
- Review AKS [upgrade and maintenance procedures](agent-upgrade.md) for clusters using Cilium.
- Learn more about [connecting to your AKS cluster](quickstart-connect-cluster.md) and [managing secrets with extensions](secret-store-extension.md).

> [!div class="nextstepaction"]
> [Learn more about AKS networking](https://learn.microsoft.com/en-us/azure/aks/azure-cni-powered-by-cilium)