---
title: Integrate and Configure Cilium with Azure Kubernetes Service (AKS)
description: Step-by-step guide for platform engineers to integrate and configure Cilium with AKS, leveraging Azure CNI for enhanced networking capabilities.
ms.topic: how-to
---

# Integrate and Configure Cilium with Azure Kubernetes Service (AKS)

## Introduction
Cilium is a powerful networking solution that enhances Azure Kubernetes Service (AKS) by providing advanced network policy enforcement and efficient endpoint management. By integrating Cilium with Azure CNI, platform engineers can achieve improved service routing, better observability, and support for larger clusters. This guide provides a step-by-step approach to configuring Cilium with AKS, ensuring optimal performance and security.

## Prerequisites
> [!div class="checklist"]
> * Familiarity with Kubernetes and AKS
> * Access to an Azure account with AKS setup
> * Azure CLI version 2.48.1 or later

## Steps

### Step 1: Create a Resource Group and Virtual Network
```azurecli
# Create the resource group
az group create --name <resourceGroupName> --location <location>

# Create a virtual network with a subnet for nodes and a subnet for pods
az network vnet create --resource-group <resourceGroupName> --location <location> --name <vnetName> --address-prefixes <address prefix, example: 10.0.0.0/8> -o none
az network vnet subnet create --resource-group <resourceGroupName> --vnet-name <vnetName> --name nodesubnet --address-prefixes <address prefix, example: 10.240.0.0/16> -o none
az network vnet subnet create --resource-group <resourceGroupName> --vnet-name <vnetName> --name podsubnet --address-prefixes <address prefix, example: 10.241.0.0/16> -o none
```

### Step 2: Create an AKS Cluster with Azure CNI Powered by Cilium
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

> [!NOTE]
> The `--network-dataplane cilium` flag is used to enable Azure CNI Powered by Cilium.

### Step 3: Configure Network Policies
Cilium enables fine-grained network policy enforcement. Here's an example of a network policy:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-specific-namespace
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          project: myproject
```

> [!WARNING]
> Ensure that network policies are carefully configured to avoid unintentional traffic blocking.

## Best Practices
> [!TIP]
> Regularly monitor cluster traffic and performance using Azure Monitor and Cilium observability tools.

## Next Steps
> [!div class="nextstepaction"]
> [Explore advanced Cilium features](https://learn.microsoft.com/en-us/azure/aks/azure-cni-powered-by-cilium)
> [Implement network policies using Cilium](https://learn.microsoft.com/en-us/azure/aks/conceptual-connectivity-modes)

## Related Documentation
- [Azure Arc-enabled Kubernetes network requirements](network-requirements.md)
- [Conceptual Connectivity Modes](conceptual-connectivity-modes.md)