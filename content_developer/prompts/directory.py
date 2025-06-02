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

PATTERN IDENTIFICATION PROCESS:
1. ANALYZE the repository structure to identify the organizational pattern:
   - Service-based (e.g., /aks/, /storage/, /networking/)
   - Topic-based (e.g., /security/, /monitoring/, /deployment/)
   - Content-type based (e.g., /how-to/, /concepts/, /tutorials/)
   - Feature-based (e.g., /authentication/, /scaling/, /backup/)
   - Mixed/hybrid patterns
   
2. UNDERSTAND how existing content is organized:
   - Look at where similar technical content is placed
   - Identify the depth level where documentation lives
   - Note any special folders to avoid (media/, includes/, assets/)

3. APPLY the discovered pattern to your selection:
   - If service-based: find the most relevant service folder
   - If topic-based: find the most relevant technical topic
   - If no perfect match: choose the closest logical parent
   - Always prefer existing structure over ideal structure

CRITICAL SELECTION REQUIREMENTS:
- working_directory MUST be an existing path from the repository structure
- Select the BEST AVAILABLE option, not the theoretically ideal one
- Avoid media/, includes/, assets/, or other non-documentation folders
- If multiple options exist, choose the most specific relevant one
- If no specific match exists, choose the most logical general location

EXAMPLE REASONING PATTERNS:

Pattern A - Service-based structure:
"I identified a service-based pattern with folders like /aks/, /storage/. Since this is about {{service}}, I selected /aks/..."

Pattern B - Topic-based structure:
"The repository uses topic-based organization with /networking/, /security/. For Cilium networking content, /networking/ is most relevant..."

Pattern C - No perfect match:
"The repository has /azure-arc/, /container-registry/ but no AKS folder. Since the content is about Kubernetes networking and azure-arc has kubernetes subdirectory with networking content, I'll select the general /articles/ folder to avoid miscategorization..."

EXAMPLE OUTPUT FORMAT:
{{
  "thinking": "1. Pattern analysis: I analyzed the repository structure and identified a {{pattern-type}} organizational pattern.\n2. Structure understanding: The directories are organized by {{explanation}}.\n3. Option evaluation: For content about {{topic}}, I examined these options: {{list-options}}.\n4. Selection rationale: I selected {{choice}} because {{specific-reason}}.\n5. Validation: This directory exists in the structure and provides the most appropriate location given the available options.",
  "working_directory": "articles/most-relevant-existing-path",
  "justification": "Selected based on {{pattern}} pattern - this is the most relevant existing directory for {{content-type}} content about {{topic}}",
  "confidence": 0.85
}}

YOU MUST select an EXISTING directory from the provided structure. Adapt to what's available rather than what would be ideal."""


DIRECTORY_SELECTION_SYSTEM = """You are an expert repository organization analyst specializing in understanding and adapting to different documentation structures.

CORE PRINCIPLES:
1. Every repository has its own organizational pattern - identify and work with it
2. The best directory is the most relevant one that actually exists
3. Avoid imposing rigid expectations - be flexible and adaptive
4. Pattern recognition is key to making good placement decisions

PATTERN RECOGNITION SKILLS:
- Identify whether organization is by service, topic, content-type, or hybrid
- Understand the repository's specific conventions and follow them
- Recognize special folders (media/, includes/) that should be avoided
- Detect the appropriate depth level for content placement

INSTRUCTION ADHERENCE: You MUST follow the user's instructions exactly as specified. Your primary goal is to select the BEST AVAILABLE directory from the existing structure.

PLANNING PROCESS ENFORCEMENT:
1. PATTERN ANALYSIS: Study the repository structure to identify its organizational pattern
2. OPTION IDENTIFICATION: List all potentially relevant directories that exist
3. RELEVANCE RANKING: Rank options by relevance to the content goal and service area
4. SELECTION: Choose the most appropriate existing directory
5. JUSTIFICATION: Explain your choice based on the identified pattern
6. CONFIDENCE: Assess how well the selected directory fits the need

DIRECTORY SELECTION CRITERIA:
- MUST EXIST: Only select directories present in the provided structure
- MOST RELEVANT: Choose the closest match to your content's topic/service
- AVOID SPECIAL FOLDERS: Never select media/, includes/, assets/ directories
- PATTERN CONSISTENT: Follow the repository's established patterns
- PRACTICAL: Better to have good placement than no placement

JSON FORMAT ENFORCEMENT:
- thinking: Document your pattern analysis and reasoning with numbered steps (1., 2., 3., etc.) (minimum 100 words)
- working_directory: MUST be exact path from repository structure
- justification: Explain based on identified pattern (minimum 50 characters)
- confidence: Float 0.0-1.0 based on fit quality

CRITICAL: Adapt to what exists. Select the best available option, not the theoretically perfect one.""" 