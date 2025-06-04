---
title: Configure Cilium as the data plane for Azure CNI in AKS
description: Learn how to deploy, configure, and validate Cilium as the data plane for Azure CNI in Azure Kubernetes Service (AKS), including CLI steps, configuration options, validation, and best practices for platform engineers.
ms.topic: how-to
---

# Configure Cilium as the data plane for Azure CNI in AKS

## Introduction

Azure Kubernetes Service (AKS) supports Azure CNI powered by Cilium, combining the robust control plane of Azure CNI with the high-performance, eBPF-based data plane of Cilium. This integration enables advanced networking, dynamic endpoint management, and granular network policy enforcement for large-scale, secure, and observable Kubernetes clusters.

This guide provides step-by-step instructions for platform engineers to deploy, configure, and validate Cilium as the data plane for Azure CNI in AKS. You'll learn how to choose between overlay and VNET IP assignment modes, apply network policies, validate deployment, and follow best practices for operational monitoring and migration.

## Prerequisites

> [!div class="checklist"]
> * An existing AKS cluster or permissions to create one
> * Azure CLI version 2.48.1 or later installed and configured ([Install Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli))
> * Basic familiarity with Kubernetes CLI tools (kubectl)
> * Sufficient Azure permissions to create resource groups, virtual networks, and AKS clusters

> [!NOTE]
> Azure CNI powered by Cilium is available only for Linux-based AKS clusters. Windows node pools are not supported.

### Supported Kubernetes and Cilium Versions

| Kubernetes Version | Minimum Cilium Version |
|-------------------|-----------------------|
| 1.27 (LTS)        | 1.13.18               |
| 1.28 (EOL)        | 1.13.18               |
| 1.29              | 1.14.19               |
| 1.30 (LTS)        | 1.14.19               |
| 1.31              | 1.16.6                |
| 1.32              | 1.17.0                |

> [!WARNING]
> Ensure your AKS cluster and CLI tooling meet the minimum version requirements. Cilium Endpoint Slices are supported in Kubernetes version 1.32 and above.

## Steps

### 1. Choose a Pod IP Assignment Model

Azure CNI powered by Cilium supports multiple pod IP assignment models:

- **Overlay network**: Pods receive IPs from a dedicated CIDR, decoupled from the VNET.
- **VNET assignment**: Pods receive IPs directly from an Azure VNET subnet.
- **Node subnet assignment**: Pods share IPs from the node subnet.

> [!TIP]
> Overlay mode is suitable for clusters where IP conservation is important. VNET mode is recommended for scenarios requiring direct pod-to-Azure resource connectivity.

### 2. Create an AKS Cluster with Azure CNI Powered by Cilium

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

> [!NOTE]
> The `--network-dataplane cilium` flag enables Cilium as the data plane. The deprecated `--enable-ebpf-dataplane` flag is no longer used.

#### [VNET Assignment](#tab/vnet)

1. Create a resource group and virtual network with separate subnets for nodes and pods:

```azurecli
az group create --name <resourceGroupName> --location <location>
az network vnet create \
  --resource-group <resourceGroupName> \
  --location <location> \
  --name <vnetName> \
  --address-prefixes <address-prefix> -o none
az network vnet subnet create \
  --resource-group <resourceGroupName> \
  --vnet-name <vnetName> \
  --name nodesubnet \
  --address-prefixes <node-subnet-prefix> -o none
az network vnet subnet create \
  --resource-group <resourceGroupName> \
  --vnet-name <vnetName> \
  --name podsubnet \
  --address-prefixes <pod-subnet-prefix> -o none
```

2. Create the AKS cluster:

```azurecli
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

#### [Node Subnet Assignment](#tab/node-subnet)

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

### 3. Configure Network Policies with Cilium

Cilium enforces both Kubernetes NetworkPolicy and CiliumNetworkPolicy resources. For most scenarios, use standard Kubernetes NetworkPolicy. For advanced features (FQDN filtering, Layer 7 policies), enable Advanced Container Networking Services.

#### Example: Basic Egress Policy

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-egress-to-external
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
```

> [!WARNING]
> Azure CNI powered by Cilium does **not** support using `ipBlock` to allow access to node or pod IPs. Use `namespaceSelector` and `podSelector` for pod-to-pod traffic.

#### Example: Allow All Pods in All Namespaces

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-all-pods
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector: {}
    - podSelector: {}
```

> [!TIP]
> For FQDN filtering and Layer 7 policies, see [Advanced Container Networking Services](https://learn.microsoft.com/azure/aks/azure-cni-powered-by-cilium#considerations).

### 4. Validate Cilium Deployment and Functionality

After deployment, validate that Cilium is running and enforcing policies:

#### Check Cilium DaemonSet Status

```azurecli
kubectl get daemonset -n kube-system cilium
```

#### View Cilium Pod Logs

```azurecli
kubectl logs -n kube-system -l k8s-app=cilium
```

#### Check Cilium Endpoint Slices (Kubernetes 1.32+)

```azurecli
kubectl get ciliumendpointslices -A
```

#### Validate Network Policy Enforcement

Apply a test NetworkPolicy and verify pod connectivity as expected.

### 5. Best Practices for Operational Monitoring

- Integrate AKS with Azure Monitor and Log Analytics to capture Cilium metrics, flow logs, and diagnostic events.
- Use out-of-the-box dashboards to visualize endpoint slice health, latency, and error rates.
- Configure alerts for critical events such as policy enforcement failures or endpoint synchronization issues.

> [!TIP]
> For detailed observability, enable Advanced Container Networking Services to access Cilium flow logs and metrics.

### 6. Migration Considerations

- AKS clusters created with Cilium as the data plane do **not** use kube-proxy. Existing clusters upgraded to Cilium will have workloads migrated to run without kube-proxy.
- Ensure all workloads are compatible with Cilium's networking model before migration.
- Cilium maintains backward compatibility with Azure CNI policy constructs, but review network policies for unsupported features (e.g., `ipBlock` limitations).
- Robust error handling and fallback mechanisms are in place; clusters without Cilium remain on the default endpoint management system.

> [!WARNING]
> Cilium is not supported on Windows node pools. Ensure all critical workloads are on Linux nodes before migration.

## Verification

- Use `kubectl get daemonset -n kube-system cilium` to confirm Cilium is running on all nodes.
- Check Cilium logs for errors: `kubectl logs -n kube-system -l k8s-app=cilium`
- Validate network policies by applying test policies and verifying pod connectivity.
- Monitor Cilium metrics and events in Azure Monitor/Log Analytics.

## Next Steps

- Explore [Advanced Cilium features](https://learn.microsoft.com/azure/aks/azure-cni-powered-by-cilium#considerations) such as FQDN filtering and Layer 7 policies.
- Integrate AKS with [Azure Monitor and Log Analytics](https://learn.microsoft.com/azure/aks/monitor-aks) for enhanced observability.
- Review [AKS networking requirements](../azure-arc/kubernetes/network-requirements.md) and [AKS overview](../azure-arc/kubernetes/overview.md).
- See [AKS troubleshooting and FAQ documentation](https://learn.microsoft.com/azure/aks/faq) for common issues and solutions.

> [!div class="nextstepaction"]
> [Learn more about networking in AKS](https://learn.microsoft.com/azure/aks/azure-cni-powered-by-cilium)