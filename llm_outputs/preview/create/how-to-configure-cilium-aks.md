---
title: Configure Cilium with Azure CNI in AKS
description: Learn how to enable, configure, and validate Cilium as the network plugin for Azure CNI in Azure Kubernetes Service (AKS), including CiliumEndpointSlices management.
ms.topic: how-to
---

# Configure Cilium with Azure CNI in AKS

## Introduction

Cilium is an advanced networking and security plugin that leverages eBPF technology to provide high-performance networking, dynamic endpoint management, and fine-grained network policy enforcement in Kubernetes environments. When integrated with Azure CNI in Azure Kubernetes Service (AKS), Cilium enhances service discovery, scalability, observability, and security. This guide provides step-by-step instructions for platform engineers to enable and configure Cilium—including CiliumEndpointSlices—in AKS clusters, along with best practices for lifecycle management and troubleshooting.

> [!NOTE]
> CiliumEndpointSlices are supported in AKS clusters running Kubernetes version 1.32 and above with Azure CNI powered by Cilium. This feature is available only for Linux-based clusters.

## Prerequisites

- Familiarity with AKS cluster management and Kubernetes networking concepts
- [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) version 2.48.1 or later, installed and configured
- Access to an Azure subscription with permissions to create and modify AKS clusters
- For advanced configuration or troubleshooting, access to the Azure portal and Kubernetes YAML editing tools

> [!WARNING]
> Before changing the network plugin or enabling Cilium, ensure your cluster version is compatible and back up all critical workloads and configurations. Changing network plugins can impact existing workloads and may require downtime.

## Steps

### 1. Understand Cilium and Azure CNI Integration

Azure CNI powered by Cilium combines Azure's robust control plane with Cilium's eBPF-based data plane. This integration provides:
- Dynamic endpoint management with CiliumEndpointSlices for efficient service discovery and load balancing
- Advanced network policy enforcement using Cilium's policy engine
- Enhanced observability and diagnostics via Azure Monitor and Cilium tools
- Support for large-scale clusters with improved scalability and reliability

> [!TIP]
> Cilium replaces kube-proxy in AKS clusters using Azure CNI powered by Cilium, simplifying network policy management and improving performance.

### 2. Enable Cilium in a New AKS Cluster

You can enable Cilium as the network dataplane during AKS cluster creation using the Azure CLI. Choose the appropriate IP assignment method for your environment.

#### Option 1: Overlay Network

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

#### Option 2: Virtual Network (VNet) Assignment

```azurecli
# Create resource group and virtual network
az group create --name <resourceGroupName> --location <location>
az network vnet create --resource-group <resourceGroupName> --location <location> --name <vnetName> --address-prefixes <addressPrefix>
az network vnet subnet create --resource-group <resourceGroupName> --vnet-name <vnetName> --name nodesubnet --address-prefixes <nodeSubnetPrefix>
az network vnet subnet create --resource-group <resourceGroupName> --vnet-name <vnetName> --name podsubnet --address-prefixes <podSubnetPrefix>

# Create AKS cluster with Cilium
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

#### Option 3: Node Subnet Assignment

```azurecli
az aks create \
  --name <clusterName> \
  --resource-group <resourceGroupName> \
  --location <location> \
  --network-plugin azure \
  --network-dataplane cilium \
  --generate-ssh-keys
```

> [!NOTE]
> The `--network-dataplane cilium` flag enables Azure CNI powered by Cilium. This replaces the deprecated `--enable-ebpf-dataplane` flag.

### 3. Enable Cilium in an Existing AKS Cluster

Currently, AKS manages the Cilium configuration, and direct modification of Cilium settings is not supported. To migrate an existing cluster to use Cilium, upgrade the cluster to a supported Kubernetes version and use the Azure CLI to update the network dataplane. Refer to the [agent-upgrade.md](agent-upgrade.md) guide for upgrade procedures.

> [!WARNING]
> Migrating to Cilium may impact running workloads. Test the migration in a staging environment and ensure you have a rollback plan.

### 4. Configure and Validate CiliumEndpointSlices

CiliumEndpointSlices are automatically managed in AKS clusters with Cilium enabled (Kubernetes 1.32+). Manual configuration of how endpoints are grouped is not supported; AKS handles grouping and synchronization.

To view CiliumEndpointSlices:

```azurecli
kubectl get ciliumendpointslices -A
```

To inspect a specific CiliumEndpointSlice:

```azurecli
kubectl get ciliumendpointslice <slice-name> -n <namespace> -o yaml
```

> [!NOTE]
> CiliumEndpointSlices do not support configuration of grouping logic or priority namespaces in AKS. All management is handled by the platform.

#### Example: CiliumEndpointSlice YAML

```yaml
apiVersion: cilium.io/v2alpha1
kind: CiliumEndpointSlice
metadata:
  name: <slice-name>
  namespace: <namespace>
spec:
  endpoints:
    - name: <endpoint-name>
      ... # Endpoint details managed by AKS
```

> [!TIP]
> Use the Azure portal's YAML editor to view or troubleshoot CiliumEndpointSlices, but avoid making direct production changes. For production, use GitOps workflows. See [kubernetes-resource-view.md](kubernetes-resource-view.md) for details.

### 5. Best Practices for Managing Cilium Lifecycle and Upgrades

- Monitor AKS release notes for supported Cilium and Kubernetes versions.
- Use the Azure CLI and portal for upgrades; do not attempt to manually upgrade Cilium components.
- Integrate with Azure Monitor and Log Analytics for observability of network traffic and endpoint slice health.
- Regularly review network policies and audit logs to ensure compliance and security.
- For production environments, use GitOps to manage network policy and resource configurations.

### 6. Troubleshooting Common Issues

- **Network Policy Enforcement:**
  - Cilium enforces network policies natively. ipBlock-based policies cannot select pod or node IPs. Use `namespaceSelector` and `podSelector` as a workaround.
  - Example workaround:
    ```yaml
    apiVersion: networking.k8s.io/v1
    kind: NetworkPolicy
    metadata:
      name: allow-egress
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
- **Observability:**
  - Enable Azure Monitor integration for metrics and logs.
  - Use Cilium's built-in observability tools for deeper diagnostics.
- **Compatibility:**
  - Cilium is supported only on Linux nodes in AKS.
  - Ensure your cluster is running a supported Kubernetes version (1.32+ for CiliumEndpointSlices).

> [!WARNING]
> Do not edit or override Cilium configuration directly in managed AKS clusters. For advanced scenarios, consider AKS BYO CNI with manual Cilium installation.

## Verification

After enabling Cilium and deploying your AKS cluster, verify the status of Cilium and CiliumEndpointSlices:

```azurecli
# Check Cilium pods
kubectl get pods -n kube-system -l k8s-app=cilium

# List CiliumEndpointSlices
kubectl get ciliumendpointslices -A

# View network policies
kubectl get networkpolicies -A
```

Check logs for Cilium components:

```azurecli
kubectl logs -n kube-system -l k8s-app=cilium
```

> [!TIP]
> Use Azure Monitor dashboards to visualize endpoint slice health, latency, and error rates for proactive troubleshooting.

## Next Steps

- Explore advanced Cilium features such as network policies and observability tools.
- Integrate Cilium configuration and policies with GitOps workflows using Flux for production-grade automation.
- Monitor and upgrade Cilium in production environments following AKS best practices. See [agent-upgrade.md](agent-upgrade.md) for upgrade guidance.
- Learn how to edit Kubernetes resources safely in the Azure portal in [kubernetes-resource-view.md](kubernetes-resource-view.md).

> [!div class="nextstepaction"]
> [Learn more about AKS networking and Cilium integration](https://learn.microsoft.com/en-us/azure/aks/azure-cni-powered-by-cilium)