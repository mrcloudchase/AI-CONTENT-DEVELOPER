---
title: Configure Cilium with Azure CNI in AKS
description: Step-by-step guide to configure Cilium with Azure CNI in Azure Kubernetes Service (AKS).
ms.topic: how-to
---

# Configure Cilium with Azure CNI in AKS

## Introduction
This guide provides step-by-step instructions for configuring Cilium with Azure CNI in Azure Kubernetes Service (AKS). By integrating Cilium, users can leverage enhanced networking capabilities such as dynamic endpoint management, advanced network policy enforcement, and improved observability. This integration aims to optimize networking efficiency, security, and scalability within AKS clusters.

## Prerequisites
Before proceeding with the configuration, ensure that you have the following prerequisites:

- **Azure CLI**: Version 2.48.1 or later. Verify your version with `az --version`.
- **AKS API Version**: 2022-09-02-preview or later.
- **Kubernetes Version**: 1.32 or above for Cilium Endpoint Slices support.
- **Azure Subscription**: Ensure you have the necessary permissions to create and manage resources.

## Steps

### Step 1: Choose a Network Model
Azure CNI powered by Cilium supports two methods for assigning pod IPs:
- **Overlay Network**: Assigns IP addresses from an overlay network.
- **Virtual Network**: Assigns IP addresses from a virtual network.

### Step 2: Create a Resource Group and Virtual Network (if using Virtual Network)
```bash
# Create the resource group
az group create --name <resourceGroupName> --location <location>

# Create a virtual network with a subnet for nodes and a subnet for pods
az network vnet create --resource-group <resourceGroupName> --location <location> --name <vnetName> --address-prefixes <address prefix, example: 10.0.0.0/8> -o none
az network vnet subnet create --resource-group <resourceGroupName> --vnet-name <vnetName> --name nodesubnet --address-prefixes <address prefix, example: 10.240.0.0/16> -o none
az network vnet subnet create --resource-group <resourceGroupName> --vnet-name <vnetName> --name podsubnet --address-prefixes <address prefix, example: 10.241.0.0/16> -o none
```

### Step 3: Create an AKS Cluster with Cilium
#### Option 1: Overlay Network
```bash
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

#### Option 2: Virtual Network
```bash
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

### Step 4: Verify the Configuration
After creating the cluster, verify that Cilium is correctly configured and running:
- Check the status of the Cilium pods using `kubectl get pods -n kube-system`.
- Ensure that network policies are enforced as expected.

## Code Examples
The code snippets provided in the Steps section illustrate how to create a resource group, virtual network, and AKS cluster with Cilium enabled.

## Next Steps
- Explore advanced network policy configurations with Cilium.
- Monitor cluster traffic and performance using Azure Monitor and Cilium observability tools.
- Review the [Azure CNI Documentation](https://learn.microsoft.com/en-us/azure/aks/azure-cni-powered-by-cilium) for more information on supported features and limitations.

For further assistance, contact the AKS support team at aks-support@example.com.