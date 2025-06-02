---
title: Integrate Cilium with Azure Kubernetes Service (AKS) using Azure CNI
description: Step-by-step guide to configure Cilium with Azure CNI in AKS for enhanced networking capabilities.
ms.topic: how-to
---

# Integrate Cilium with Azure Kubernetes Service (AKS) using Azure CNI

## Introduction
Cilium is an open-source networking solution that enhances Kubernetes networking capabilities through advanced network policy enforcement and dynamic endpoint management. Integrating Cilium with Azure Kubernetes Service (AKS) using Azure CNI provides improved service routing, efficient network policy enforcement, and better observability of cluster traffic. This guide provides step-by-step instructions for integrating Cilium with AKS to leverage these benefits.

## Prerequisites

> [!div class="checklist"]
> * Basic understanding of Kubernetes and AKS
> * Access to an Azure account with permissions to configure AKS
> * Azure CLI version 2.48.1 or later

## Steps

### 1. Overview of Cilium Benefits for AKS
Cilium enhances AKS by providing:
- **Dynamic Endpoint Management**: Efficient service discovery and resource utilization.
- **Advanced Network Policies**: Granular security rules for enterprise compliance.
- **Improved Observability**: Detailed logging and metrics through Azure Monitor.

### 2. Configure Azure CNI with Cilium

#### Create a Resource Group and Virtual Network
```azurecli
az group create --name <resourceGroupName> --location <location>
az network vnet create --resource-group <resourceGroupName> --location <location> --name <vnetName> --address-prefixes <address prefix, example: 10.0.0.0/8> -o none
az network vnet subnet create --resource-group <resourceGroupName> --vnet-name <vnetName> --name nodesubnet --address-prefixes <address prefix, example: 10.240.0.0/16> -o none
az network vnet subnet create --resource-group <resourceGroupName> --vnet-name <vnetName> --name podsubnet --address-prefixes <address prefix, example: 10.241.0.0/16> -o none
```

#### Create an AKS Cluster with Cilium

**Option 1: Overlay Network**
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

**Option 2: Virtual Network**
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

### 3. Verification and Troubleshooting

> [!NOTE]
> Verify the integration by checking the Cilium pods and network policies.

- Use `kubectl get pods -n kube-system` to ensure Cilium pods are running.
- Check network policies using `kubectl get networkpolicies`.

> [!WARNING]
> Ensure compatibility with existing network policies to avoid disruptions.

## Next Steps

> [!div class="nextstepaction"]
> [Explore advanced Cilium features](https://learn.microsoft.com/en-us/azure/aks/azure-cni-powered-by-cilium)

> [!TIP]
> Consider performance tuning for large clusters to optimize resource utilization.