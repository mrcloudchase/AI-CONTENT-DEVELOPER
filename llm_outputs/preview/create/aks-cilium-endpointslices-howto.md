---
title: Integrate and configure CiliumEndpointSlices with Azure CNI in AKS
description: Learn how to enable and configure CiliumEndpointSlices with Azure CNI in Azure Kubernetes Service (AKS), enforce advanced network policies, and integrate observability using Azure Monitor and Log Analytics.
ms.topic: how-to
---

# Integrate and configure CiliumEndpointSlices with Azure CNI in AKS

## Introduction

This guide walks platform engineers through integrating and configuring CiliumEndpointSlices with Azure CNI in Azure Kubernetes Service (AKS). CiliumEndpointSlices provide dynamic grouping and management of pod endpoints, enabling rapid service discovery, efficient load balancing, and advanced network policy enforcement. Leveraging Cilium's eBPF-powered data plane, this integration enhances AKS networking with improved scalability, security, and observability.

You will learn how to:

> [!div class="checklist"]
> * Enable CiliumEndpointSlices in AKS clusters using Azure CNI
> * Configure advanced network policy enforcement with Cilium
> * Integrate with Azure Monitor and Log Analytics for observability
> * Apply best practices for operational efficiency, security, and scalability

## Prerequisites

Before you begin, ensure you meet the following requirements:

- Intermediate knowledge of AKS and Kubernetes networking concepts
- Access to an Azure subscription with permissions to create and manage AKS clusters
- Familiarity with Azure CLI (version 2.48.1 or later) and relevant AKS API versions (2023-02-02-preview or later)
- Understanding of Cilium and eBPF basics
- AKS cluster running Kubernetes version 1.32 or later (required for CiliumEndpointSlices support)

> [!NOTE]
> CiliumEndpointSlices are only supported in Kubernetes version 1.32 and above on AKS with Azure CNI powered by Cilium.

## Steps

### 1. Overview of CiliumEndpointSlices Integration with Azure CNI in AKS

CiliumEndpointSlices enable AKS to dynamically group and manage pod endpoints into slices, allowing for faster lookup, improved scalability, and efficient load balancing. The integration leverages Cilium’s advanced network policy engine for fine-grained security and provides deep observability through Azure Monitor and Log Analytics.

Key benefits include:
- Real-time endpoint management and synchronization
- Advanced network policy enforcement (ingress and egress)
- Granular audit logging and observability
- Scalability to thousands of pods and hundreds of nodes

> [!WARNING]
> CiliumEndpointSlices do not support configuration of how endpoints are grouped. Priority namespaces via `cilium.io/ces-namespace` are not supported.

### 2. Enable CiliumEndpointSlices with Azure CNI in AKS

#### a. Choose a Network Model

Azure CNI powered by Cilium supports multiple IP assignment models:
- Overlay network
- Virtual network (VNet)
- Node subnet

Refer to [Choosing a network model to use](https://learn.microsoft.com/en-us/azure/aks/azure-cni-powered-by-cilium) for details.

#### b. Create a New AKS Cluster with CiliumEndpointSlices Enabled

> [!NOTE]
> The `--network-dataplane cilium` flag enables Azure CNI powered by Cilium, which is required for CiliumEndpointSlices. Ensure your Kubernetes version is 1.32 or later.

##### Option 1: Overlay Network

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

##### Option 2: Virtual Network (VNet)

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
  --address-prefixes <node-subnet-prefix> -o none

az network vnet subnet create \
  --resource-group <resourceGroupName> \
  --vnet-name <vnetName> \
  --name podsubnet \
  --address-prefixes <pod-subnet-prefix> -o none

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

##### Option 3: Node Subnet

```azurecli
az aks create \
  --name <clusterName> \
  --resource-group <resourceGroupName> \
  --location <location> \
  --network-plugin azure \
  --network-dataplane cilium \
  --generate-ssh-keys
```

> [!WARNING]
> CiliumEndpointSlices are not available for Windows nodes. Only Linux nodes are supported.

#### c. Configure EndpointSlice Parameters

AKS manages Cilium configuration, including EndpointSlice parameters. Customization of how endpoints are grouped is not supported. For advanced configuration, consider BYO CNI scenarios.

> [!NOTE]
> Endpoint slice refresh intervals and slice size thresholds are managed by AKS and not user-configurable.

### 3. Configure Advanced Network Policy Enforcement with Cilium

Cilium provides a rich network policy language that supports both Kubernetes NetworkPolicy and Cilium-specific constructs. In AKS managed CNI, you can apply standard Kubernetes NetworkPolicy resources and, with Advanced Container Networking Services (ACNS), use FQDN filtering and Layer 7 policies.

#### Example: Basic NetworkPolicy

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
```

#### Example: Egress Policy with ipBlock and Workaround

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

> [!WARNING]
> Network policies using ipBlock cannot allow access to node or pod IPs. Use namespaceSelector and podSelector as a workaround. It is not possible to allow traffic to node IPs via ipBlock.

#### Advanced Features (with ACNS)
- FQDN filtering
- Layer 7 (HTTP/gRPC/Kafka) policies
- Enhanced container network observability

> [!TIP]
> Enable Advanced Container Networking Services to access FQDN filtering, Layer 7 policies, and advanced observability features.

### 4. Integrate with Azure Monitor and Log Analytics for Observability

Cilium integration with Azure Monitor and Log Analytics enables:
- Collection of metrics, events, and error logs for endpoint slice operations
- Visualization of endpoint slice health, latency, and error rates
- Alerting for synchronization failures or policy enforcement breaches

> [!NOTE]
> Observability settings are enabled during cluster provisioning and managed by AKS. Out-of-the-box dashboards are provided in Azure Monitor.

#### Example: Querying Cilium Logs in Log Analytics

```kusto
// Example Kusto query to find Cilium endpoint slice errors
ContainerLog
| where ContainerName contains "cilium"
| where LogEntry contains "endpoint-slice"
| where LogEntry contains "error"
| project TimeGenerated, LogEntry
```

### 5. Operational Best Practices for Production AKS Environments

- **Security**: Enforce least-privilege network policies. Use Azure Active Directory integration for authentication and authorization.
- **Scalability**: Design for up to 5,000 pods and 500 nodes per cluster. Monitor endpoint slice health and adjust workloads accordingly.
- **Reliability**: Target 99.99% uptime. Use Azure Monitor alerts for proactive incident response.
- **Maintainability**: Use modular policy definitions and leverage AKS-managed logging for diagnostics.
- **Fallback**: If CiliumEndpointSlices are disabled or fail, AKS reverts to traditional endpoint management to ensure cluster continuity.

> [!WARNING]
> CiliumEndpointSlices are only available in AKS clusters with Azure CNI powered by Cilium and Kubernetes version 1.32 or later. Not all Cilium features are supported; ClusterwideCiliumNetworkPolicy and custom Cilium configuration are not available in managed CNI mode.

### 6. Functional and Non-Functional Requirements

- **Performance**: Endpoint slice updates propagate within 100ms of pod state changes.
- **Reliability**: 99.99% uptime target for networking subsystem.
- **Security**: All component communications are encrypted; Azure AD is used for secure authentication.
- **Usability**: Feature is enabled and configured via Azure CLI, Portal, or ARM templates; no manual Cilium configuration is required.
- **Backward Compatibility**: Existing clusters without CiliumEndpointSlices continue to use default endpoint management. Robust error handling ensures automatic fallback if feature fails.

### 7. Dependencies and Compatibility Considerations

- **Cilium Version**: Requires Cilium 1.17.0 or later (for Kubernetes 1.32+)
- **AKS API Version**: 2023-02-02-preview or later
- **Azure CNI Components**: Integrated with Azure CNI powered by Cilium
- **Backward Compatibility**: Maintained with existing Azure CNI policy constructs

> [!WARNING]
> CiliumEndpointSlices are not supported for Windows nodes or clusters running Kubernetes versions earlier than 1.32. Customization of endpoint grouping is not supported in managed CNI mode.

## Verification

To verify that CiliumEndpointSlices are enabled and functioning in your AKS cluster:

1. Check that the CiliumEndpointSlice CRDs are present:

```azurecli
kubectl get ciliumendpointslices -A
```

2. Confirm that Cilium pods are running and healthy:

```azurecli
kubectl get pods -n kube-system -l k8s-app=cilium
```

3. Validate network policy enforcement by applying test policies and checking pod connectivity.

4. Review logs in Azure Monitor and Log Analytics for endpoint slice operations and errors.

> [!TIP]
> Use Azure Monitor dashboards to visualize endpoint slice health and latency metrics.

## Next Steps

- Explore advanced Cilium features such as Layer 7 policies and FQDN filtering with Advanced Container Networking Services.
- Integrate network policy management into your CI/CD pipelines for automated deployment and compliance.
- Monitor and troubleshoot Cilium in AKS using Azure Monitor and Log Analytics.
- Learn more about [Azure CNI powered by Cilium](https://learn.microsoft.com/en-us/azure/aks/azure-cni-powered-by-cilium).
- Review [Kubernetes networking best practices](https://learn.microsoft.com/en-us/azure/arc/kubernetes/network-requirements).

> [!div class="nextstepaction"]
> [Upgrade Azure CNI IPAM modes and Dataplane Technology](https://learn.microsoft.com/en-us/azure/aks/upgrade-networking)