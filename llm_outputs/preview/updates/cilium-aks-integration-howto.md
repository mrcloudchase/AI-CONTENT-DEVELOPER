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
- Explore advanced network policy configurations with Cilium, including the use of Cilium’s rich network policy language for fine-grained security policies.
- Monitor cluster traffic and performance using Azure Monitor and Cilium observability tools, leveraging detailed logging and metrics for proactive troubleshooting.
- Review the [Azure CNI Documentation](https://learn.microsoft.com/en-us/azure/aks/azure-cni-powered-by-cilium) for more information on supported features and limitations.
- Consider enabling Advanced Container Networking services to gain capabilities such as FQDN-based filtering and Layer 7-based network policies.

For further assistance, contact the AKS support team at aks-support@example.com.

## Cilium Benefits

Integrating Cilium with Azure CNI in AKS offers several key benefits:

- **Enhanced Networking Efficiency**: Cilium enables dynamic grouping of service endpoints for rapid service discovery and efficient resource utilization.
- **Improved Security & Policy Enforcement**: Utilize Cilium’s native network policy engine to enforce granular security rules that align with enterprise compliance requirements.
- **Optimized Developer & Operator Experience**: Provides a seamless configuration experience via Azure Portal, CLI, and APIs, reducing operational overhead and accelerating deployments.
- **Operational Cost Efficiency**: Enhances the scalability and stability of clusters to reduce downtime and lower management costs, particularly in large-scale deployments.

## Architecture Overview

The architecture of Cilium integration with Azure CNI in AKS combines the robust control plane of Azure CNI with the data plane of Cilium. This integration leverages eBPF programs loaded into the Linux kernel to provide high-performance networking and security. Key architectural components include:

- **Cilium Endpoint Slices**: Automatically manages pod endpoints into slices for faster lookup and improved scalability. This feature allows for dynamic grouping and efficient load balancing, enhancing service discovery and resource utilization.
- **Network Policy Enforcement**: Cilium’s policy engine applies network security rules across all endpoint slices, supporting both ingress and egress policy enforcement. This includes fine-grained security policies that align with enterprise compliance requirements.
- **Observability**: Integrated with Azure Monitor and Cilium observability tools to provide detailed logging, metrics, and diagnostic information. This integration supports proactive troubleshooting and performance tuning.
- **IP Address Management (IPAM)**: Supports both overlay and virtual network models for assigning pod IPs, offering flexibility in network configuration. This flexibility is crucial for large-scale deployments.

## Advanced Network Policy Configurations

Cilium’s advanced network policy capabilities allow for the implementation of fine-grained security policies across dynamic endpoint slices. Key features include:

- **Dynamic Endpoint Management**: Automatically groups and manages pod endpoints into slices, enabling faster lookup and improved scalability.
- **Fine-Grained Security Policies**: Leverage Cilium’s rich network policy language to enforce detailed security rules, supporting both ingress and egress traffic.
- **Integration with Azure Monitor**: Provides detailed logging and metrics for network policy operations, enhancing observability and troubleshooting capabilities.
- **Configurable Parameters**: Allows customization of endpoint slice parameters such as refresh intervals and slice size thresholds to suit diverse operational needs.

These configurations are essential for maintaining high security standards and operational efficiency in large-scale AKS deployments.