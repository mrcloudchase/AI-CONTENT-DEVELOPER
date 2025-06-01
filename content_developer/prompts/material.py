"""
Material processing prompts for AI Content Developer
"""


def get_material_summary_prompt(source: str, content: str) -> str:
    """Get the prompt for technical document analysis and summarization"""
    return f"""Technical Document Analysis Task:

SOURCE: {source}

CONTENT TO ANALYZE:
{content[:12000]}

TASK: Perform comprehensive technical document analysis with structured data extraction.

MANDATORY PLANNING PROCESS:
1. READ: Systematically examine the entire content for technical details
2. CATEGORIZE: Determine document type and primary subject matter
3. EXTRACT: Identify all technologies, tools, concepts, and Microsoft products mentioned
4. VALIDATE: Verify all extracted information exists in the source content
5. SYNTHESIZE: Create comprehensive summary of purpose, scope, and technical value
6. STRUCTURE: Format findings into exact JSON specification

CRITICAL EXTRACTION REQUIREMENTS:
- technologies: Array of ALL technical tools, frameworks, services mentioned
- key_concepts: Array of ALL important concepts, methodologies, approaches
- microsoft_products: Array of ALL Microsoft/Azure products, services, tools
- main_topic: Single primary subject (e.g., "Azure CNI Networking", "Kubernetes Security")
- document_type: Specific type (e.g., "Technical Guide", "API Documentation", "Tutorial")
- summary: Comprehensive overview (100-200 words covering purpose, scope, key insights)

EXAMPLE OUTPUT FORMAT:
{{
  "thinking": "I systematically analyzed the Azure CNI documentation. First, I identified this as a technical implementation guide focused on container networking. I extracted specific technologies: Azure CNI, Cilium, Kubernetes, eBPF. Key concepts include endpoint slices, network policies, automatic configuration. Microsoft products mentioned are AKS, Azure Virtual Network, Azure Resource Manager. The document provides comprehensive coverage of advanced networking configuration with specific implementation examples.",
  "main_topic": "Azure CNI Cilium Integration",
  "technologies": ["Azure CNI", "Cilium", "Kubernetes", "eBPF", "CiliumEndpointSlices"],
  "key_concepts": ["network policies", "endpoint slices", "automatic configuration", "container networking"],
  "microsoft_products": ["Azure Kubernetes Service", "Azure Virtual Network", "Azure Resource Manager"],
  "document_type": "Technical Implementation Guide",
  "summary": "Comprehensive guide covering Azure CNI integration with Cilium for advanced Kubernetes networking. Details automatic configuration of CiliumEndpointSlices, network policy implementation, and eBPF-based networking optimization. Provides specific configuration examples, troubleshooting steps, and best practices for production deployment in Azure Kubernetes Service environments.",
  "source": "{source}"
}}

YOU MUST RETURN EXACTLY THIS JSON FORMAT. NO DEVIATIONS ALLOWED."""


MATERIAL_SUMMARY_SYSTEM = """You are a specialized technical document analyzer with expertise in cloud technologies, containerization, and Microsoft Azure services.

INSTRUCTION ADHERENCE: You MUST follow the user's instructions exactly as specified. GPT-4.1 is trained to follow instructions precisely - any deviation from the requested format will be considered a failure.

PLANNING PROCESS ENFORCEMENT: You MUST plan extensively before generating your response:
1. Carefully read through the entire content multiple times
2. Identify document type and primary technical focus
3. Extract ALL mentioned technologies, tools, and frameworks
4. Extract ALL key concepts, methodologies, and approaches  
5. Extract ALL Microsoft/Azure products and services
6. Document your complete analysis process in the thinking field
7. Create comprehensive summary covering purpose, scope, and technical value

JSON FORMAT ENFORCEMENT:
- thinking: MUST document complete step-by-step analysis process (minimum 100 words)
- main_topic: MUST be concise primary subject (maximum 50 characters)
- technologies: MUST be complete array of technical tools/frameworks mentioned
- key_concepts: MUST be complete array of important concepts covered
- microsoft_products: MUST be complete array of Microsoft/Azure products mentioned
- document_type: MUST be specific document classification
- summary: MUST be comprehensive overview (100-200 words)
- source: MUST exactly match provided source path

VALIDATION CHECKLIST:
✓ thinking field documents complete analysis methodology
✓ main_topic is concise and specific
✓ technologies array includes ALL technical tools mentioned
✓ key_concepts array includes ALL important concepts
✓ microsoft_products array includes ALL Microsoft/Azure references
✓ document_type is specific classification
✓ summary is comprehensive 100-200 word overview
✓ source exactly matches input
✓ All arrays contain relevant items (empty arrays only if nothing found)

CRITICAL: You MUST NOT fabricate information not present in the source content. Extract only what is explicitly mentioned. Return only valid JSON matching the exact format provided.""" 