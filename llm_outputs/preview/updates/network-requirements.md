---
title: Azure Arc-enabled Kubernetes network requirements
description: Learn about the networking requirements to connect Kubernetes clusters to Azure Arc.
ms.date: 04/15/2025
ms.topic: concept-article 
ms.custom: references-regions
---

# Azure Arc-enabled Kubernetes network requirements

This topic describes the networking requirements for connecting a Kubernetes cluster to Azure Arc and supporting various Arc-enabled Kubernetes scenarios.

> [!TIP]
> For the Azure public cloud, you can reduce the number of required endpoints by using the [Azure Arc gateway (preview)](arc-gateway-simplify-networking.md).

## Details

[!INCLUDE [network-requirement-principles](../includes/network-requirement-principles.md)]

[!INCLUDE [network-requirements](includes/network-requirements.md)]

## Additional endpoints

Depending on your scenario, you may need connectivity to other URLs, such as those used by the Azure portal, management tools, or other Azure services. In particular, review these lists to ensure that you allow connectivity to any necessary endpoints:

- [Azure portal URLs](../../azure-portal/azure-portal-safelist-urls.md)
- [Azure CLI endpoints for proxy bypass](/cli/azure/azure-cli-endpoints)

For a complete list of network requirements for Azure Arc features and Azure Arc-enabled services, see [Azure Arc network requirements](../network-requirements-consolidated.md).


## Cilium Integration with Azure CNI

Azure Kubernetes Service (AKS) now supports CiliumEndpointSlices with Azure CNI by Cilium, enhancing networking capabilities with dynamic endpoint management and advanced network policy enforcement. This integration allows for:

- Dynamic grouping of service endpoints for rapid service discovery.
- Utilization of Cilium’s native network policy engine for granular security rules.
- Enhanced observability through Azure Monitor and Cilium tools.
- Configurability during cluster provisioning via Azure Portal, CLI, and APIs.

For more details on configuring Azure CNI powered by Cilium, refer to the [Azure CNI Powered by Cilium Configuration Guide](https://learn.microsoft.com/en-us/azure/aks/azure-cni-powered-by-cilium).
## Next steps

- Understand [system requirements for Arc-enabled Kubernetes](system-requirements.md).
- Use our [quickstart](quickstart-connect-cluster.md) to connect your cluster.
- Review [frequently asked questions](faq.md) about Arc-enabled Kubernetes.
