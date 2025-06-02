---
title: Deploy and configure Cilium with Azure CNI in AKS
description: Learn how to deploy, configure, and operate Azure CNI powered by Cilium in Azure Kubernetes Service (AKS), including advanced features such as CiliumEndpointSlices, enhanced network policy enforcement, and integration with Azure Monitor.
ms.topic: how-to
---

# Deploy and configure Cilium with Azure CNI in AKS

## Introduction

Azure CNI powered by Cilium brings advanced networking capabilities to Azure Kubernetes Service (AKS) by combining the robust Azure CNI control plane with Cilium's high-performance eBPF data plane. This integration enables dynamic endpoint management, enhanced network policy enforcement, and improved observability, making it ideal for platform engineers managing scalable, secure, and efficient Kubernetes environments.

With CiliumEndpointSlices, AKS clusters benefit from dynamic grouping of pod endpoints, enabling rapid service discovery, efficient load balancing, and granular security controls. Integration with Azure Monitor and Cilium observability tools further enhances operational insight and troubleshooting capabilities.

> [!NOTE]
> Cilium on AKS is currently supported only on Linux nodes. Ensure your cluster meets all prerequisites before proceeding.

## Prerequisites

Before deploying or configuring Azure CNI powered by Cilium in AKS, ensure the following:

- **Familiarity with AKS and Kubernetes networking concepts**
- **Azure CLI** version 2.48.1 or later installed and authenticated
- **Access to an Azure subscription** with permissions to create and manage AKS clusters
- **Supported AKS and Cilium versions**:
  - Kubernetes 1.27 (LTS): Cilium 1.13.18+
  - Kubernetes 1.28: Cilium 1.13.18+
  - Kubernetes 1.29: Cilium 1.14.19+
  - Kubernetes 1.30 (LTS): Cilium 1.14.19+
  - Kubernetes 1.31: Cilium 1.16.6+
  - Kubernetes 1.32: Cilium 1.17.0+
- **Linux-based AKS node pools only** (Windows nodes are not supported)
- **AKS API version** 2022-09-02-preview or later if using ARM templates or REST API

> [!WARNING]
> Azure CNI powered by Cilium is not available for Windows nodes. Network policies using `ipBlock` have limitations—see Limitations below.

## Steps

### 1. Choose a Pod IP Assignment Method
Azure CNI powered by Cilium supports multiple modes for assigning pod IPs:
- **Overlay network** (similar to Azure CNI Overlay)
- **Virtual network** (dynamic pod IP assignment)
- **Node subnet**

#### [Overlay Network](#tab/overlay)
Create a new AKS cluster with Cilium and overlay networking:

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

> [!NOTE]
> The `--network-dataplane cilium` flag replaces the deprecated `--enable-ebpf-dataplane` flag.

#### [Virtual Network](#tab/vnet)
Provision a virtual network and subnets, then create the AKS cluster:

```azurecli
# Create the resource group
az group create --name <resourceGroupName> --location <location>

# Create a virtual network with node and pod subnets
az network vnet create --resource-group <resourceGroupName> --location <location> --name <vnetName> --address-prefixes <vnetAddressPrefix> -o none
az network vnet subnet create --resource-group <resourceGroupName> --vnet-name <vnetName> --name nodesubnet --address-prefixes <nodeSubnetPrefix> -o none
az network vnet subnet create --resource-group <resourceGroupName> --vnet-name <vnetName> --name podsubnet --address-prefixes <podSubnetPrefix> -o none

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
Create a cluster using the node subnet with Cilium:

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

### 2. Enable CiliumEndpointSlices
CiliumEndpointSlices are supported in Kubernetes 1.32 and above. They provide scalable, dynamic grouping of pod endpoints for efficient service discovery and policy enforcement.

> [!NOTE]
> CiliumEndpointSlices do not support custom grouping configuration or priority namespaces via `cilium.io/ces-namespace`.

No manual configuration is required to enable CiliumEndpointSlices if your cluster is running a supported version. Endpoint slices are managed automatically by Cilium and AKS.

#### Example: Viewing CiliumEndpointSlices
```bash
kubectl get ciliumepslices -A
```

### 3. Configure Network Policies with Cilium
Cilium enforces Kubernetes NetworkPolicy resources natively. You can define policies for fine-grained control over pod communication.

#### Example: Basic NetworkPolicy
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: frontend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: backend
```

> [!WARNING]
> Network policies using `ipBlock` cannot select pod or node IPs. To allow traffic to all pods, use `namespaceSelector` and `podSelector` instead.

#### Example: Workaround for ipBlock Limitation
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
    - ipBlock:
        cidr: 0.0.0.0/0
    - namespaceSelector: {}
    - podSelector: {}
```

### 4. Integrate with Azure Monitor and Cilium Observability
Cilium provides detailed logging, metrics, and diagnostics. Integration with Azure Monitor and Log Analytics enables proactive troubleshooting and performance tuning.

- Enable advanced container networking services for observability features (metrics, flow logs, FQDN filtering, Layer 7 policies).
- Configure Log Analytics workspace and connect it to your AKS cluster as per standard Azure Monitor integration steps.

> [!NOTE]
> Out-of-the-box dashboards visualize endpoint slice health, latency, and error rates. Alerts can be configured for synchronization failures or policy enforcement breaches.

### 5. Operational Best Practices
- **Scalability:** Azure CNI powered by Cilium supports up to 5,000 pods across 500 nodes per cluster.
- **Reliability:** Target 99.99% uptime for networking subsystems.
- **Fallback:** If CiliumEndpointSlices fail, AKS reverts to traditional endpoint management automatically.
- **Security:** All component communications are encrypted and integrate with Azure Active Directory.
- **Maintainability:** Use robust error handling and monitor logs for diagnostics.

> [!TIP]
> For production environments, regularly review Azure Monitor dashboards and configure alerts for critical networking events.

### 6. Limitations and Supported Scenarios
- **Linux-only:** Cilium is not supported on Windows nodes.
- **ipBlock Restrictions:** Network policies using `ipBlock` cannot allow traffic to pod or node IPs.
- **No kube-proxy:** Clusters with Cilium dataplane do not use kube-proxy.
- **No manual Cilium configuration:** AKS manages Cilium configuration; for custom setups, use BYO CNI.
- **CiliumEndpointSlices:** Supported in Kubernetes 1.32+; grouping configuration is not customizable.
- **No support for ClusterwideCiliumNetworkPolicy.**

## Verification

After deployment, verify that Cilium and endpoint slices are functioning:

```bash
kubectl get pods -n kube-system -l k8s-app=cilium
kubectl get ciliumepslices -A
```

Check Azure Monitor dashboards for networking metrics and alerts.

## Next Steps

- [Implement advanced network policies using Cilium](https://learn.microsoft.com/en-us/azure/aks/azure-cni-powered-by-cilium)
- [Monitor and troubleshoot Cilium-powered networking in AKS](https://learn.microsoft.com/en-us/azure/aks/azure-cni-powered-by-cilium)
- [Explore multi-cloud or hybrid scenarios with Cilium and Azure Arc](/articles/azure-arc/kubernetes/network-requirements.md)
- [Use GitOps with Flux v2 for AKS configuration management](/articles/azure-arc/kubernetes/tutorial-use-gitops-flux2.md)

> [!div class="nextstepaction"]
> [Learn more about AKS networking and Cilium integration](https://learn.microsoft.com/en-us/azure/aks/azure-cni-powered-by-cilium)