---
title: Configure and manage Cilium networking in AKS with Azure CNI
description: Step-by-step guide for platform engineers to configure, deploy, and manage Cilium as the networking solution in Azure Kubernetes Service (AKS) using Azure CNI, including advanced features, observability, and operational best practices.
ms.topic: how-to
---

# Configure and manage Cilium networking in AKS with Azure CNI

## Introduction

Cilium is an advanced, eBPF-based networking solution that enhances Azure Kubernetes Service (AKS) by providing high-performance networking, dynamic endpoint management, and advanced network policy enforcement. When integrated with Azure CNI, Cilium enables efficient service discovery, granular security, and improved observability for Kubernetes clusters. This guide walks platform engineers through configuring, deploying, and managing Cilium in AKS, leveraging features such as CiliumEndpointSlices, eBPF-based policies, and integration with Azure Monitor.

> [!NOTE]
> CiliumEndpointSlices in AKS allow for dynamic grouping of pod endpoints, improving scalability and service discovery performance, especially in large-scale environments.

## Prerequisites

Before you begin, ensure you meet the following requirements:

> [!div class="checklist"]
> * Familiarity with AKS and Kubernetes networking concepts
> * Access to an Azure subscription with permissions to create and manage AKS clusters
> * Azure CLI version 2.48.1 or later installed ([Install Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli))
> * If using ARM templates or REST API, AKS API version 2022-09-02-preview or later
> * Supported Kubernetes and Cilium versions:
>   * Kubernetes 1.27 (LTS) with Cilium 1.13.18+
>   * Kubernetes 1.29+ with Cilium 1.14.19+
>   * Kubernetes 1.32+ required for CiliumEndpointSlices support

> [!WARNING]
> Azure CNI powered by Cilium is available only for Linux nodes. Windows node support is not available. Network policies using ipBlock to allow node or pod IPs are not supported.

## Steps

### 1. Deploy an AKS Cluster with Azure CNI Powered by Cilium

You can deploy AKS with Cilium using either overlay or VNet IP assignment modes.

#### [Overlay Network](#tab/overlay)

Use this option to assign pod IPs from an overlay network:

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
> The `--network-dataplane cilium` flag enables Azure CNI powered by Cilium. This replaces the deprecated `--enable-ebpf-dataplane` flag.

#### [Virtual Network (VNet) Mode](#tab/vnet)

Assign pod IPs from a dedicated subnet in your Azure VNet:

```azurecli
# Create the resource group
az group create --name <resourceGroupName> --location <location>

# Create a virtual network and subnets for nodes and pods
az network vnet create \
  --resource-group <resourceGroupName> \
  --location <location> \
  --name <vnetName> \
  --address-prefixes <address-prefix, e.g., 10.0.0.0/8> -o none

az network vnet subnet create \
  --resource-group <resourceGroupName> \
  --vnet-name <vnetName> \
  --name nodesubnet \
  --address-prefixes <address-prefix, e.g., 10.240.0.0/16> -o none

az network vnet subnet create \
  --resource-group <resourceGroupName> \
  --vnet-name <vnetName> \
  --name podsubnet \
  --address-prefixes <address-prefix, e.g., 10.241.0.0/16> -o none

# Deploy AKS with Cilium
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

---

> [!TIP]
> For most production scenarios, using VNet mode provides better integration with Azure networking and security controls.

### 2. Configure CiliumEndpointSlices

CiliumEndpointSlices are supported in AKS clusters running Kubernetes 1.32 and above. They enable dynamic grouping of endpoints for improved scalability and policy enforcement.

- Endpoint slices are created, updated, and deleted automatically as pods are scheduled or removed.
- No manual grouping configuration is supported; grouping is managed by Cilium.

> [!NOTE]
> Priority namespaces via `cilium.io/ces-namespace` are not supported in AKS-managed CiliumEndpointSlices.

#### Example: Viewing CiliumEndpointSlices

```azurecli
kubectl get ciliumnodeslices
```

### 3. Enforce Network Policies with Cilium

Cilium provides advanced network policy enforcement, supporting both Kubernetes NetworkPolicy and Cilium-specific L3/L4 policies.

#### Example: Basic Network Policy YAML

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-nginx
spec:
  podSelector:
    matchLabels:
      app: nginx
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
```

> [!WARNING]
> Network policies using `ipBlock` cannot be used to allow traffic to pod or node IPs. To allow traffic to all pods, use `namespaceSelector` and `podSelector` instead.

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

### 4. Integrate with Azure Monitor and Log Analytics

Cilium in AKS integrates with Azure Monitor and Log Analytics for enhanced observability:

- Enable monitoring during cluster creation or via Azure Portal.
- View metrics, logs, and diagnostic information in Log Analytics workspaces.

> [!TIP]
> Use out-of-the-box dashboards to visualize endpoint slice health, latency, and error rates. Configure alerts for synchronization failures or policy enforcement breaches.

#### Example: Viewing Cilium Status and Observability

```azurecli
kubectl -n kube-system get pods -l k8s-app=cilium
kubectl -n kube-system logs <cilium-pod-name>
```

### 5. Configure Security with Azure Active Directory

- All communications between components are encrypted.
- AKS integrates with Azure Active Directory (AAD) for secure authentication and authorization.
- Use AAD-integrated RBAC to manage access to network policy and endpoint slice resources.

### 6. Operational Best Practices

- **Scalability:** AKS with CiliumEndpointSlices supports up to 5,000 pods across 500 nodes without performance degradation.
- **Reliability:** Target 99.99% uptime for networking subsystems.
- **Fallback Mechanisms:** If CiliumEndpointSlices fail, AKS reverts to traditional endpoint management automatically.
- **Maintainability:** Use modular configuration and leverage Azure Monitor for diagnostics.

> [!WARNING]
> Version compatibility is critical. Ensure your AKS, Cilium, and Azure CNI versions meet the documented requirements.

### 7. Known Limitations and Workarounds

- **Windows Support:** Only Linux nodes are supported.
- **ipBlock Restrictions:** Network policies with `ipBlock` cannot select pod or node IPs. Use `namespaceSelector` and `podSelector` as a workaround.
- **No kube-proxy:** AKS clusters with Cilium do not use kube-proxy. All service routing is handled by Cilium.
- **No manual Cilium configuration:** AKS manages Cilium configuration; custom modifications are not supported.

## Next Steps

- Explore [advanced network policy scenarios with Cilium](https://learn.microsoft.com/en-us/azure/aks/azure-cni-powered-by-cilium)
- Integrate with GitOps workflows for automated policy deployment
- Monitor and troubleshoot Cilium networking in production AKS clusters
- Review [Azure Kubernetes Service networking requirements](azure-arc/kubernetes/network-requirements.md)

> [!div class="nextstepaction"]
> [Learn more about Azure CNI powered by Cilium](https://learn.microsoft.com/en-us/azure/aks/azure-cni-powered-by-cilium)