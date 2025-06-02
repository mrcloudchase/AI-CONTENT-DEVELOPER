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

> [!NOTE]
> When integrating Cilium with Azure CNI, ensure that your network configuration meets the specific requirements for CiliumEndpointSlices, including necessary connectivity for Azure Monitor and Log Analytics.

## Additional endpoints

Depending on your scenario, you may need connectivity to other URLs, such as those used by the Azure portal, management tools, or other Azure services. In particular, review these lists to ensure that you allow connectivity to any necessary endpoints:

- [Azure portal URLs](../../azure-portal/azure-portal-safelist-urls.md)
- [Azure CLI endpoints for proxy bypass](/cli/azure/azure-cli-endpoints)

For a complete list of network requirements for Azure Arc features and Azure Arc-enabled services, see [Azure Arc network requirements](../network-requirements-consolidated.md).

## Next steps

- Understand [system requirements for Arc-enabled Kubernetes](system-requirements.md).
- Use our [quickstart](quickstart-connect-cluster.md) to connect your cluster.
- Review [frequently asked questions](faq.md) about Arc-enabled Kubernetes.


## Cilium Integration

Cilium integrates with Azure CNI to enhance networking capabilities in Azure Kubernetes Service (AKS). This integration leverages Cilium's dynamic endpoint management and advanced network policy enforcement to provide several architectural benefits:

- **Dynamic Endpoint Management**: CiliumEndpointSlices allow for automatic grouping and management of pod endpoints, resulting in faster service discovery and efficient load balancing.
- **Advanced Network Policies**: Cilium's rich policy language enables fine-grained security policies across dynamic endpoint slices, aligning with enterprise compliance requirements.
- **Improved Observability**: Integration with Azure Monitor and Cilium observability tools provides detailed logging, metrics, and diagnostic information, facilitating proactive troubleshooting and performance tuning.
- **Operational Efficiency**: The integration reduces operational overhead by providing a seamless configuration experience via Azure Portal, CLI, and APIs.

For practical implementation steps, refer to the [Cilium AKS How-To Guide](cilium-aks-how-to-guide.md).

```yaml
apiVersion: "cilium.io/v2"
kind: CiliumNetworkPolicy
metadata:
  name: "example-policy"
spec:
  endpointSelector:
    matchLabels:
      app: "my-app"
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: "frontend"
    toPorts:
    - ports:
      - port: "80"
        protocol: "TCP"
```