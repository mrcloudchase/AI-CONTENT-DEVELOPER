---
title: Deploy and manage Cilium networking in Azure Kubernetes Service (AKS)
description: Learn how to deploy, configure, and manage Cilium (including CiliumEndpointSlices) as the network plugin in Azure Kubernetes Service (AKS), leveraging Azure CNI powered by Cilium for advanced networking, security, and observability.
ms.topic: how-to
---

# Deploy and manage Cilium networking in Azure Kubernetes Service (AKS)

## Introduction

Cilium is a next-generation, eBPF-powered networking and security solution for Kubernetes. In Azure Kubernetes Service (AKS), Cilium can be integrated as the data plane via Azure CNI powered by Cilium, delivering advanced networking, dynamic endpoint management, and granular network policy enforcement. With support for CiliumEndpointSlices, AKS clusters gain improved service discovery, scalability, and observability, positioning AKS as a leader in managed Kubernetes networking.

This guide shows platform engineers how to deploy, configure, and manage Cilium in AKS, including enabling CiliumEndpointSlices, enforcing network policies, and integrating with Azure Monitor for observability.

> [!NOTE]
> Cilium in AKS is designed to enhance networking efficiency, security, and operational experience for large-scale, cloud-native workloads.

## Prerequisites

Before you begin, ensure you meet the following requirements:

- **Intermediate knowledge of AKS and Kubernetes networking concepts**
- **Azure subscription** with permissions to create and manage AKS clusters
- **Azure CLI** version 2.48.1 or later installed ([Install Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli))
- **Supported AKS and Cilium versions:**
  - Kubernetes 1.32 or later is required for CiliumEndpointSlices support
  - Cilium version compatibility:
    - 1.32: Cilium 1.17.0+
    - 1.31: Cilium 1.16.6+
    - 1.30: Cilium 1.14.19+
    - 1.29: Cilium 1.14.19+
    - 1.27/1.28: Cilium 1.13.18+
- **Familiarity with basic Kubernetes CLI operations**

> [!WARNING]
> Azure CNI powered by Cilium is currently supported **only on Linux nodes**. Windows node pools are not supported.

> [!WARNING]
> Network policies using `ipBlock` have limitations. Policies can't use `ipBlock` to allow access to node or pod IPs. See [Network Policy Enforcement](#network-policy-enforcement) for details and workarounds.

## Steps

### 1. Deploy an AKS cluster with Azure CNI powered by Cilium

Azure CNI powered by Cilium can be deployed in several IP assignment modes. Choose the method that best fits your network architecture.

#### [Azure CLI: Overlay Network](#tab/overlay)

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

#### [Azure CLI: Virtual Network](#tab/vnet)

```azurecli
# Create the resource group
az group create --name <resourceGroupName> --location <location>

# Create a virtual network with subnets for nodes and pods
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

#### [Azure CLI: Node Subnet](#tab/node-subnet)

> [!NOTE]
> Azure CLI version 2.69.0 or later is required for this method.

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
> The `--network-dataplane cilium` flag enables Azure CNI powered by Cilium. This replaces the deprecated `--enable-ebpf-dataplane` flag.

### 2. Enable and configure CiliumEndpointSlices

CiliumEndpointSlices are supported in AKS with Kubernetes version 1.32 and later. They provide scalable, dynamic grouping of pod endpoints for efficient service discovery and load balancing.

- **Automatic management:** CiliumEndpointSlices are automatically created, updated, and deleted based on pod status changes.
- **Manual override:** Mechanisms for manual override and re-synchronization are available for advanced troubleshooting ([see PRD requirements](#)).
- **Configuration:** AKS manages Cilium configuration; direct customization is not supported. For advanced needs, consider BYO CNI.

> [!NOTE]
> Configuration of how Cilium Endpoints are grouped is not supported. Priority namespaces via `cilium.io/ces-namespace` are not supported.

#### Verify CiliumEndpointSlices

```azurecli
kubectl get ciliumnodeslices.cilium.io
```

### 3. Network policy enforcement

Cilium enforces Kubernetes NetworkPolicy resources natively, providing fine-grained control over pod-to-pod and pod-to-external communications.

- **No need for separate network policy engines** (e.g., Calico or Azure Network Policy Manager)
- **Supports both ingress and egress policies**
- **Audit logging** is integrated with Azure Monitor and Log Analytics

#### Sample Cilium network policy YAML

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

> [!WARNING]
> Network policies using `ipBlock` can't be used to allow access to node or pod IPs. As a workaround, use `namespaceSelector` and `podSelector` to select pods:

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

> [!NOTE]
> It isn't currently possible to specify a NetworkPolicy with an `ipBlock` to allow traffic to node IPs.

### 4. Observability and monitoring

Cilium in AKS integrates with Azure Monitor and Log Analytics for comprehensive observability:

- **Metrics:** Endpoint slice health, latency, and error rates
- **Logs:** Detailed audit logs for network policy enforcement and endpoint slice operations
- **Dashboards:** Out-of-the-box dashboards visualize networking health and performance
- **Alerting:** Configure alerts for synchronization failures or policy breaches

#### Example: Enable monitoring during cluster creation

```azurecli
az aks create \
  --name <clusterName> \
  --resource-group <resourceGroupName> \
  --location <location> \
  --network-plugin azure \
  --network-dataplane cilium \
  --enable-addons monitoring \
  --workspace-resource-id <logAnalyticsWorkspaceResourceId> \
  --generate-ssh-keys
```

> [!TIP]
> For advanced observability, enable Advanced Container Networking Services (ACNS) to access Layer 7 metrics and flow logs.

### 5. Troubleshooting and known limitations

- **Linux-only:** Cilium is supported only on Linux nodes.
- **ipBlock limitations:** Network policies using `ipBlock` can't allow access to node or pod IPs.
- **No kube-proxy:** AKS clusters with Cilium as the data plane do not use kube-proxy.
- **No direct Cilium configuration:** AKS manages Cilium configuration; manual changes are not supported.
- **Host networking:** Network policies are not applied to pods using host networking (`spec.hostNetwork: true`).
- **Multiple services/host ports:** Multiple Kubernetes services can't use the same host port with different protocols.

> [!NOTE]
> For additional troubleshooting, review logs in Azure Monitor and consult the [AKS support team](mailto:aks-support@example.com).

### 6. Future considerations

- **Enhanced analytics:** Deeper analytics and predictive insights on endpoint slice behavior and policy effectiveness are planned.
- **UI enhancements:** Future portal updates will provide visualizations of endpoint slice metrics and network policy maps.
- **Multi-cloud integration:** Support for multi-cloud and hybrid environments is under consideration.
- **Performance tuning:** Ongoing optimizations for large-scale deployments are planned.

## Next Steps

- Explore advanced Cilium features such as multi-cluster networking and enhanced analytics.
- Integrate Cilium network policy management with GitOps workflows for automated, versioned policy deployment.
- Monitor and optimize AKS networking performance using Azure Monitor and Log Analytics.
- For more information, see [Configure Azure CNI Powered by Cilium in AKS](https://learn.microsoft.com/en-us/azure/aks/azure-cni-powered-by-cilium).
- Learn more about [Kubernetes networking best practices](https://learn.microsoft.com/en-us/azure/aks/concepts-network).

> [!div class="nextstepaction"]
> [Upgrade Azure CNI IPAM modes and Dataplane Technology](https://learn.microsoft.com/en-us/azure/aks/upgrade-networking)