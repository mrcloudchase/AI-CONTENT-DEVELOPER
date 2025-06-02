---
title: Configure Azure CNI powered by Cilium in Azure Kubernetes Service (AKS)
description: Learn how to enable and configure Azure CNI powered by Cilium in AKS, including CiliumEndpointSlices and eBPF-powered networking enhancements.
ms.topic: how-to
---

# Configure Azure CNI powered by Cilium in Azure Kubernetes Service (AKS)

## Introduction

Azure Kubernetes Service (AKS) now supports Azure CNI powered by Cilium, combining the robust control plane of Azure CNI with the advanced data plane of Cilium. This integration leverages eBPF (extended Berkeley Packet Filter) technology to deliver high-performance networking, dynamic endpoint management, and granular network policy enforcement. With the introduction of CiliumEndpointSlices, AKS clusters benefit from improved service discovery, scalability, and observability, making it easier to manage large-scale, secure, and efficient Kubernetes deployments.

This guide walks you through configuring Azure CNI powered by Cilium in AKS, enabling CiliumEndpointSlices, and verifying that advanced networking features are active. It also highlights best practices and important considerations for production environments.

## Prerequisites

Before you begin, ensure you have the following:

> [!div class="checklist"]
> * Basic understanding of AKS and Kubernetes networking concepts
> * Permissions to create and manage AKS clusters in your Azure subscription
> * Azure CLI version 2.48.1 or later installed and configured ([Install Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli))
> * Familiarity with Kubernetes manifests and YAML
> * (Optional) Access to Azure Monitor and Log Analytics for observability features

> [!NOTE]
> CiliumEndpointSlices are supported in AKS clusters running Kubernetes version 1.32 and above. Ensure your cluster version meets this requirement.

## Steps

### 1. Overview of Cilium Integration with Azure CNI in AKS

Azure CNI powered by Cilium provides:
- Functionality equivalent to existing Azure CNI and Azure CNI Overlay plugins
- Improved service routing and efficient network policy enforcement
- Enhanced observability of cluster traffic
- Support for larger clusters (more nodes, pods, and services)
- Native integration with Azure Monitor and Log Analytics for advanced diagnostics

Cilium uses eBPF programs loaded into the Linux kernel to provide high-performance packet processing, dynamic endpoint management, and advanced security policies.

> [!WARNING]
> Azure CNI powered by Cilium is only available for Linux nodes. Windows node support is not available.

### 2. Create an AKS Cluster with Azure CNI Powered by Cilium

You can enable Azure CNI powered by Cilium during cluster creation using the Azure CLI. There are three primary network models:

#### [Overlay Network](#tab/overlay)
Assign pod IP addresses from an overlay network.

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
Assign pod IP addresses from a dedicated subnet in a virtual network.

```azurecli
# Create the resource group
az group create --name <resourceGroupName> --location <location>

# Create a virtual network and subnets
az network vnet create \
  --resource-group <resourceGroupName> \
  --location <location> \
  --name <vnetName> \
  --address-prefixes <addressPrefix> -o none

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
Assign pod IP addresses from the node subnet.

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
> Azure CNI powered by Cilium is not supported on Windows nodes. Ensure all nodes in your cluster are Linux-based.

> [!TIP]
> For guidance on choosing a network model, see [AKS networking concepts](https://learn.microsoft.com/azure/aks/network-concepts).

### 3. Enable and Configure CiliumEndpointSlices

CiliumEndpointSlices provide scalable management and grouping of pod endpoints, improving service discovery and load balancing.

- CiliumEndpointSlices are automatically supported in AKS clusters running Kubernetes version 1.32 and above with Azure CNI powered by Cilium.
- No manual configuration is required to enable CiliumEndpointSlices in supported clusters.
- Customization of how Cilium endpoints are grouped is not supported in managed AKS; priority namespaces via `cilium.io/ces-namespace` are not available.

> [!NOTE]
> CiliumEndpointSlices do not support manual configuration of grouping in AKS. AKS manages these settings automatically.

#### Example: Viewing CiliumEndpointSlices

```azurecli
kubectl get ciliumepslices -A
```

### 4. How Cilium Uses eBPF for Networking Enhancements

Cilium leverages eBPF (extended Berkeley Packet Filter) to:
- Implement high-performance packet filtering and forwarding in the Linux kernel
- Enforce network policies at Layers 3/4 (IP/port) and, with Advanced Container Networking Services, at Layer 7 (HTTP/gRPC/Kafka)
- Replace kube-proxy for service routing, reducing latency and improving scalability
- Provide detailed observability and telemetry for network traffic

> [!TIP]
> eBPF enables Cilium to dynamically update network rules without kernel module reloads, resulting in faster policy enforcement and lower operational overhead.

### 5. Best Practices for Production Environments

- **Cluster Version:** Use Kubernetes version 1.32 or later to ensure full support for CiliumEndpointSlices.
- **Observability:** Integrate with Azure Monitor and Log Analytics for real-time visibility into endpoint slice health, latency, and error rates.
- **Security:** Use Cilium’s network policy engine to enforce granular security rules. All communications between components are encrypted and integrate with Azure Active Directory for authentication.
- **Compatibility:** Review existing network policies for compatibility. Some features, such as `ipBlock` in network policies, have limitations (see below).
- **Fallback:** AKS provides robust error handling and will revert to traditional endpoint management if CiliumEndpointSlices fail.

> [!WARNING]
> Network policies using `ipBlock` cannot allow access to node or pod IPs. Use `namespaceSelector` and `podSelector` as a workaround. See the example below.

#### Example: NetworkPolicy Workaround

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: example-ipblock
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

> [!TIP]
> For advanced features such as FQDN filtering and Layer 7 policies, enable Advanced Container Networking Services (ACNS) on your cluster.

## Verification

After deploying your AKS cluster with Azure CNI powered by Cilium, verify that Cilium is active and functioning as expected.

### 1. Check Cilium Pods

```azurecli
kubectl get pods -n kube-system -l k8s-app=cilium
```

Expected output:

```output
NAME             READY   STATUS    RESTARTS   AGE
cilium-xxxxx     1/1     Running   0          5m
cilium-xxxxx     1/1     Running   0          5m
...
```

### 2. Confirm CiliumEndpointSlices

```azurecli
kubectl get ciliumepslices -A
```

Expected output:

```output
NAMESPACE   NAME                AGE
kube-system ciliumepslice-xxx   2m
...
```

### 3. Validate Network Policy Enforcement

Apply a test NetworkPolicy and verify traffic is allowed or denied as expected. Review Cilium logs for policy enforcement events:

```azurecli
kubectl logs -n kube-system -l k8s-app=cilium
```

> [!TIP]
> For detailed observability, use Azure Monitor dashboards and Cilium’s built-in metrics.

## Next Steps

- Explore advanced Cilium features such as network policies and observability tools.
- Integrate Cilium with Azure Monitor for comprehensive network telemetry and diagnostics.
- Review [AKS upgrade and maintenance considerations](https://learn.microsoft.com/azure/aks/upgrade-cluster) for Cilium-enabled clusters.
- Learn more about [AKS networking concepts](https://learn.microsoft.com/azure/aks/network-concepts).

> [!div class="nextstepaction"]
> [Learn more about AKS networking](https://learn.microsoft.com/azure/aks/network-concepts)