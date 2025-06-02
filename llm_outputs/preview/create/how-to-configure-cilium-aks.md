---
title: Configure Cilium networking in Azure Kubernetes Service (AKS)
description: Learn how to enable and configure Cilium as the network plugin in AKS, including CiliumEndpointSlices integration with Azure CNI, with step-by-step instructions and best practices.
ms.topic: how-to
---

# Configure Cilium networking in Azure Kubernetes Service (AKS)

## Introduction

Cilium is an advanced Kubernetes networking plugin that leverages eBPF (extended Berkeley Packet Filter) for high-performance networking, dynamic endpoint management, and fine-grained network policy enforcement. Integrating Cilium with Azure CNI in Azure Kubernetes Service (AKS) enables:

- Dynamic grouping and management of pod endpoints using CiliumEndpointSlices for efficient service discovery and load balancing
- Advanced network policy enforcement using Cilium’s native policy engine
- Enhanced observability and diagnostics through integration with Azure Monitor and Cilium tools
- Improved scalability and operational efficiency for large clusters

Azure CNI powered by Cilium combines the robust control plane of Azure CNI with Cilium’s data plane, providing improved service routing, efficient network policy enforcement, and better cluster traffic observability. This guide walks you through enabling and configuring Cilium in AKS, including CiliumEndpointSlices integration, and provides best practices for management and troubleshooting.

## Prerequisites

Before you begin, ensure you have the following:

> [!div class="checklist"]
> * Familiarity with Kubernetes networking concepts
> * Access to an Azure subscription with permissions to create and manage AKS clusters
> * Azure CLI version 2.48.1 or later installed and configured ([Install Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli))
> * Basic knowledge of AKS cluster creation

> [!NOTE]
> CiliumEndpointSlices are supported in AKS clusters running Kubernetes version 1.32 and above. Ensure your cluster version meets this requirement.

## Steps

### 1. Understand Cilium and Azure CNI Integration

Azure CNI powered by Cilium provides:

- Functionality equivalent to existing Azure CNI and Azure CNI Overlay plugins
- Improved service routing and efficient network policy enforcement
- Support for larger clusters (more nodes, pods, and services)
- Enhanced observability and integration with Azure Monitor

CiliumEndpointSlices allow AKS to dynamically manage pod endpoints, automatically grouping them into slices for faster lookup, improved scalability, and efficient load balancing. Cilium’s policy engine enforces security rules across these endpoint slices.

> [!WARNING]
> Cilium is only available for Linux nodes in AKS. Network policies using `ipBlock` cannot select pod or node IPs. CiliumEndpointSlices do not support custom grouping configuration or priority namespaces.

### 2. Create a New AKS Cluster with Cilium Networking

You can enable Cilium as the network dataplane when creating a new AKS cluster. Choose the networking mode that fits your requirements:

#### [Overlay Network](#tab/overlay)

Assign pod IPs from an overlay network:

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

Assign pod IPs from a virtual network:

```azurecli
# Create the resource group
az group create --name <resourceGroupName> --location <location>

# Create a virtual network and subnets
az network vnet create \
  --resource-group <resourceGroupName> \
  --location <location> \
  --name <vnetName> \
  --address-prefixes <address-prefix> -o none

az network vnet subnet create \
  --resource-group <resourceGroupName> \
  --vnet-name <vnetName> \
  --name nodesubnet \
  --address-prefixes <node-address-prefix> -o none

az network vnet subnet create \
  --resource-group <resourceGroupName> \
  --vnet-name <vnetName> \
  --name podsubnet \
  --address-prefixes <pod-address-prefix> -o none

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

Assign pod IPs from the node subnet (Azure CLI 2.69.0+ required):

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

> [!NOTE]
> The `--network-dataplane cilium` flag is required to enable Cilium. For clusters using ARM templates or REST API, use API version 2022-09-02-preview or later.

### 3. Enable and Configure CiliumEndpointSlices

CiliumEndpointSlices are enabled by default when using Azure CNI powered by Cilium on supported Kubernetes versions (1.32+). They provide scalable management of pod endpoints and improve service discovery and load balancing.

- Endpoint slices are created, updated, and deleted automatically based on pod status changes.
- Synchronization between the Kubernetes API and Cilium ensures accurate endpoint state.
- Cilium’s policy engine enforces network policies across all endpoint slices.

> [!NOTE]
> Customization of how Cilium endpoints are grouped in slices is not supported. Priority namespaces via `cilium.io/ces-namespace` are not supported.

#### Example: Viewing CiliumEndpointSlices

To view CiliumEndpointSlices in your cluster:

```azurecli
kubectl get ciliumepslices -A
```

#### Example: Inspecting a CiliumEndpointSlice

```azurecli
kubectl describe ciliumepslice <slice-name> -n <namespace>
```

> [!TIP]
> Use Azure Monitor and Log Analytics for observability of endpoint slice operations, health, and latency.

### 4. Upgrade Existing AKS Clusters to Use Cilium

To migrate an existing AKS cluster to use Cilium as the network dataplane, follow the documented AKS upgrade process and specify the `--network-dataplane cilium` flag. Refer to [AKS upgrade documentation](https://learn.microsoft.com/azure/aks/upgrade-cluster) for detailed steps.

> [!WARNING]
> Switching network plugins may cause temporary disruptions. Review compatibility and plan maintenance windows accordingly.

### 5. Configure and Enforce Network Policies

Cilium enforces Kubernetes NetworkPolicy resources and supports advanced L3/L4 policies. For FQDN filtering and Layer 7 policies, enable Advanced Container Networking Services.

> [!WARNING]
> Network policies using `ipBlock` cannot select pod or node IPs. Use `namespaceSelector` and `podSelector` as a workaround.

#### Example: NetworkPolicy with Workaround

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

### 6. Observability and Monitoring

- Integrate with Azure Monitor and Log Analytics to capture performance indicators, events, and error logs for endpoint slice operations.
- Use out-of-the-box dashboards for endpoint slice health and latency.
- Configure alerts for critical events such as synchronization failures or policy enforcement breaches.

### 7. Best Practices and Troubleshooting

- Ensure your AKS and Cilium versions are compatible (see [Supported Kubernetes Versions](https://learn.microsoft.com/azure/aks/supported-kubernetes-versions)).
- Monitor cluster health and endpoint slice synchronization regularly.
- Use Azure Monitor and Cilium observability tools for diagnostics.
- Maintain RBAC best practices for secure cluster management.
- Plan upgrades and network plugin changes during maintenance windows.

> [!WARNING]
> Misconfiguration of network policies may result in unintended traffic blocking or exposure. Always test policies in a non-production environment before applying to production clusters.

## Verification

After deploying or upgrading your AKS cluster with Cilium networking, verify that Cilium and CiliumEndpointSlices are operational:

### 1. Check Cilium DaemonSet Status

```azurecli
kubectl get daemonset cilium -n kube-system
```

Ensure all pods are in the `Ready` state.

### 2. List CiliumEndpointSlices

```azurecli
kubectl get ciliumepslices -A
```

You should see endpoint slices listed for your workloads.

### 3. Validate Network Policy Enforcement

Apply a test NetworkPolicy and verify traffic is allowed or denied as expected.

### 4. Monitor Logs and Metrics

Use Azure Monitor and Log Analytics to review logs and metrics related to Cilium and endpoint slices.

> [!TIP]
> For troubleshooting, consult both the Cilium and AKS documentation, and use diagnostic tools integrated with Azure Monitor.

## Next Steps

- Explore advanced Cilium features such as network policies and observability:
  - [Cilium documentation](https://docs.cilium.io/en/stable/)
  - [AKS documentation](https://docs.microsoft.com/azure/aks/)
- Integrate Cilium with Azure Monitor for enhanced visibility and diagnostics.
- Review [AKS upgrade considerations](https://learn.microsoft.com/azure/aks/upgrade-cluster) when using Cilium.
- Learn more about [networking in AKS](https://learn.microsoft.com/azure/aks/concepts-network).

> [!div class="nextstepaction"]
> [Learn more about configuring network policies in AKS](https://learn.microsoft.com/azure/aks/use-network-policies)