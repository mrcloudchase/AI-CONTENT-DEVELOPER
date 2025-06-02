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
  "thinking": "1. Document analysis: I systematically analyzed the Azure CNI documentation and identified this as a technical implementation guide focused on container networking.\n2. Technology extraction: I extracted specific technologies including Azure CNI, Cilium, Kubernetes, and eBPF.\n3. Concept identification: Key concepts include endpoint slices, network policies, and automatic configuration.\n4. Microsoft product mapping: Products mentioned are AKS, Azure Virtual Network, and Azure Resource Manager.\n5. Summary synthesis: The document provides comprehensive coverage of advanced networking configuration with specific implementation examples.",
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

CRITICAL TYPE REQUIREMENTS: You MUST follow JSON type specifications exactly:
- Strings for text values (NOT arrays)
- Arrays for lists (NOT strings)
- Empty arrays [] if no items found (NOT null or omitted)

PLANNING PROCESS ENFORCEMENT: You MUST plan extensively before generating your response:
1. Carefully read through the entire content multiple times
2. Identify document type and primary technical focus
3. Extract ALL mentioned technologies, tools, and frameworks
4. Extract ALL key concepts, methodologies, and approaches  
5. Extract ALL Microsoft/Azure products and services
6. Document your complete analysis process in the thinking field
7. Create comprehensive summary covering purpose, scope, and technical value

JSON FORMAT ENFORCEMENT:
- thinking: MUST be a STRING with numbered steps (1., 2., 3., etc.) documenting complete step-by-step analysis process (minimum 100 words)
- main_topic: MUST be a STRING with concise primary subject (maximum 50 characters)
- technologies: MUST be an ARRAY of strings listing technical tools/frameworks mentioned
- key_concepts: MUST be an ARRAY of strings listing important concepts covered
- microsoft_products: MUST be an ARRAY of strings listing Microsoft/Azure products mentioned
- document_type: MUST be a STRING with specific document classification
- summary: MUST be a STRING with comprehensive overview (100-200 words)
- source: MUST be a STRING exactly matching provided source path

TYPE VALIDATION:
✓ ALL fields must be present (no omissions)
✓ thinking, main_topic, document_type, summary, source MUST be strings
✓ thinking MUST use numbered steps (1., 2., 3., etc.)
✓ technologies, key_concepts, microsoft_products MUST be arrays
✓ Arrays must contain strings only (not objects or numbers)
✓ Empty arrays [] are valid if nothing found (NOT null)

VALIDATION CHECKLIST:
✓ thinking field documents complete analysis methodology with numbered steps
✓ main_topic is concise and specific
✓ technologies array includes ALL technical tools mentioned
✓ key_concepts array includes ALL important concepts
✓ microsoft_products array includes ALL Microsoft/Azure references
✓ document_type is specific classification
✓ summary is comprehensive 100-200 word overview
✓ source exactly matches input
✓ All arrays contain relevant items (empty arrays only if nothing found)

CRITICAL: You MUST NOT fabricate information not present in the source content. Extract only what is explicitly mentioned. Return only valid JSON matching the exact format provided.""" 