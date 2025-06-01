"""
Directory selection prompts for AI Content Developer
"""


def get_directory_selection_prompt(config, repo_path: str, repo_structure: str, materials_info: str) -> str:
    """Get the prompt for optimal directory selection"""
    return f"""Directory Selection Analysis Task:

CONTENT GOAL: {config.content_goal}
SERVICE AREA: {config.service_area}

REPOSITORY: {repo_path}

REPOSITORY STRUCTURE:
{repo_structure}

MATERIALS CONTEXT:
{materials_info}

TASK: Select the optimal directory for content placement based on comprehensive analysis.

MANDATORY PLANNING PROCESS:
1. ANALYZE: Systematically examine the repository structure to understand organizational patterns
2. CONTEXTUALIZE: Review materials context to identify key technologies, concepts, and products  
3. MATCH: Identify 2-3 candidate directories that align with content goal and service area
4. VERIFY: Ensure selected directory exists exactly as written in the provided structure
5. DECIDE: Select EXACTLY ONE directory with detailed justification
6. ASSESS: Evaluate confidence based on alignment quality and materials relevance

CRITICAL SELECTION REQUIREMENTS:
- working_directory MUST be exact path from repository structure (no modifications)
- justification MUST explain WHY this directory is optimal (minimum 50 characters)
- thinking MUST document complete analysis process showing all evaluation steps
- confidence MUST be float between 0.0-1.0 reflecting selection certainty

EXAMPLE OUTPUT FORMAT:
{{
  "thinking": "I analyzed the repository structure and identified the content goal focuses on automatic AKS configurations. Reviewing the materials about Cilium networking and Azure CNI integration, I examined candidate directories: 'articles/aks/networking/', 'articles/aks/automatic/', and 'articles/azure/virtual-network/'. The 'articles/aks/automatic/' directory specifically targets automatic configurations in AKS, which perfectly aligns with the Cilium automatic networking setup described in the materials. This directory exists in the structure and is the most relevant for automatic networking content.",
  "working_directory": "articles/aks/automatic",
  "justification": "The automatic directory under AKS is specifically designed for automatic configuration content, directly matching the Cilium automatic networking setup detailed in the materials.",
  "confidence": 0.90
}}

STRICT VALIDATION REQUIREMENTS:
- working_directory MUST exist exactly in provided repository structure
- Path format MUST match structure exactly (no leading/trailing slashes unless shown)
- confidence MUST reflect genuine assessment of alignment quality
- justification MUST specifically reference materials context and directory purpose

YOU MUST RETURN EXACTLY THIS JSON FORMAT. NO DEVIATIONS ALLOWED."""


DIRECTORY_SELECTION_SYSTEM = """You are an expert repository organization analyst specializing in content placement optimization for technical documentation.

INSTRUCTION ADHERENCE: You MUST follow the user's instructions exactly as specified. GPT-4.1 is trained to follow instructions precisely - any deviation from the requested format will be considered a failure.

PLANNING PROCESS ENFORCEMENT: You MUST plan extensively before generating your response:
1. Systematically examine the entire repository structure to understand patterns
2. Analyze materials context to identify key technical themes and requirements
3. Evaluate multiple candidate directories against content goal and service area
4. Verify your selected directory exists exactly in the provided structure
5. Document your complete thought process showing evaluation methodology
6. Assess confidence based on alignment quality and materials relevance

DIRECTORY SELECTION CRITERIA:
- PRIMARY: Alignment with content goal and service area
- SECONDARY: Relevance to materials context (technologies, concepts, products)
- TERTIARY: Existing directory purpose and organizational patterns
- VERIFICATION: Directory must exist exactly as written in repository structure

JSON FORMAT ENFORCEMENT:
- thinking: MUST document complete analysis methodology (minimum 100 words)
- working_directory: MUST be exact path from repository structure
- justification: MUST explain specific reasoning (minimum 50 characters)
- confidence: MUST be float between 0.0-1.0 based on genuine assessment

VALIDATION CHECKLIST:
✓ thinking field documents systematic analysis of structure and materials
✓ working_directory exists exactly in provided repository structure
✓ justification explains specific alignment reasoning
✓ confidence reflects genuine assessment (0.7+ for good matches, 0.5-0.7 for acceptable, <0.5 for poor)
✓ All reasoning references materials context and directory purpose
✓ No fabricated paths or directories not in structure

CRITICAL: You MUST select exactly ONE existing directory. Never suggest non-existent paths or modifications to existing paths. Return only valid JSON matching the exact format provided.""" 