<content_type_selection_instructions>

<input_examples>
  <example_request>
    <user_request>We need documentation for Azure Private Endpoints in our organization</user_request>
    <materials>Private endpoint concepts, DNS configuration, network isolation benefits, setup procedures for storage accounts, approval workflows, troubleshooting connectivity issues</materials>
  </example_request>
  
  <example_request>
    <user_request>Document the new Azure Container Apps feature for our team</user_request>
    <materials>Container Apps overview, comparison with AKS and Container Instances, KEDA scaling, Dapr integration, deployment from GitHub Actions, revision management</materials>
  </example_request>
  
  <example_request>
    <user_request>Show developers working with our new Azure OpenAI implementation</user_request>
    <materials>API authentication, prompt engineering basics, token limits, model selection (GPT-4 vs GPT-3.5), sample Python code, rate limiting, estimated 15-minute basic implementation, 2-hour advanced scenarios</materials>
  </example_request>
  
  <example_request>
    <user_request>Need something for Azure Cognitive Search</user_request>
    <materials>Search index concepts, relevance scoring, analyzers, indexers, some API examples, pricing tiers, use cases</materials>
  </example_request>
</input_examples>

<task>
Analyze the provided user request and materials to select the most appropriate documentation content type from these options: overview, concept, quickstart, howto, tutorial.
</task>

<available_content_types>
  <content_type name="overview">
    <description>High-level technical explanation for new users</description>
    <use_when>
      - User asks "What is X?"
      - Introducing new service or technology
      - Comparing features across services
      - No procedural steps in materials
    </use_when>
    <restrictions>
      - No step-by-step instructions allowed
      - Must remain high-level
      - Technical perspective only (not marketing)
    </restrictions>
  </content_type>

  <content_type name="concept">
    <description>Deep technical explanation of how something works</description>
    <use_when>
      - User asks "How does X work?"
      - Architecture explanation needed
      - Design patterns or internal workings
      - Technical theory required
    </use_when>
    <restrictions>
      - Focus on understanding, not performing tasks
      - No procedural steps
      - Can include technical diagrams
    </restrictions>
  </content_type>

  <content_type name="quickstart">
    <description>Get users operational in under 10 minutes</description>
    <use_when>
      - User mentions "quickly" or "fast"
      - First-time setup requested
      - Day 1 experience needed
      - Procedure can complete in less than 10 minutes
    </use_when>
    <restrictions>
      - Must complete in under 10 minutes
      - Minimal prerequisites only
      - Must be production-ready
      - Must include resource cleanup
    </restrictions>
  </content_type>

  <content_type name="howto">
    <description>Steps to complete a specific task</description>
    <use_when>
      - User asks "How to...?" or "How do I...?"
      - Task-oriented request
      - Multiple approaches exist
      - Real-world implementation needed
    </use_when>
    <restrictions>
      - Can include multiple options
      - Should provide decision guidance
      - Flexible for different environments
    </restrictions>
  </content_type>

  <content_type name="tutorial">
    <description>Learning journey with single best path</description>
    <use_when>
      - User mentions "tutorial" or "learn"
      - Educational journey needed
      - Building complete example
      - Scenario-based learning requested
    </use_when>
    <restrictions>
      - Must follow single path
      - Requires learning objectives
      - Must include cleanup steps
      - Must be scenario-based
    </restrictions>
  </content_type>
</available_content_types>

<selection_process>
  <step number="1">
    <action>Check for explicit content type mention</action>
    <rule>If user explicitly names a content type, select it if materials support it</rule>
  </step>
  
  <step number="2">
    <action>Analyze material type</action>
    <rule>Classify materials as procedural (has steps) or conceptual (explains concepts)</rule>
  </step>
  
  <step number="3">
    <action>Estimate time if procedural</action>
    <rule>If procedural and takes more than 10 minutes, exclude quickstart option</rule>
  </step>
  
  <step number="4">
    <action>Match intent to content type</action>
    <rules>
      - Understanding request + high-level = overview
      - Understanding request + deep technical = concept
      - Task request + under 10 min = quickstart
      - Task request + learning focus = tutorial
      - Task request + general = howto
    </rules>
  </step>
</selection_process>

<keyword_indicators>
  <for_type name="overview">
    <keywords>what is, introduction to, overview of, features of, capabilities</keywords>
    <audience_hints>new users, unfamiliar with, getting started</audience_hints>
  </for_type>
  
  <for_type name="concept">
    <keywords>how it works, architecture, deep dive, understand, internals, design patterns</keywords>
    <audience_hints>developers, architects, technical professionals</audience_hints>
  </for_type>
  
  <for_type name="quickstart">
    <keywords>quickly, get started, try out, fast, immediate, first time</keywords>
    <time_hints>10 minutes, minimal setup, hello world</time_hints>
  </for_type>
  
  <for_type name="howto">
    <keywords>how to, configure, set up, implement, deploy, manage, troubleshoot</keywords>
    <content_hints>steps, procedures, commands, configuration options</content_hints>
  </for_type>
  
  <for_type name="tutorial">
    <keywords>tutorial, learn, walkthrough, build, hands-on, practice</keywords>
    <content_hints>scenario, project, learning objectives, complete example</content_hints>
  </for_type>
</keyword_indicators>

<required_output_format>
  <json_schema>
    {
      "type": "object",
      "properties": {
        "chain_of_thought": {
          "type": "array",
          "description": "Step-by-step reasoning process",
          "items": {
            "type": "string"
          },
          "minItems": 3,
          "maxItems": 10
        },
        "selected_type": {
          "type": "string",
          "description": "The selected content type",
          "enum": ["overview", "concept", "quickstart", "howto", "tutorial", "unable_to_determine"]
        },
        "confidence": {
          "type": "number",
          "description": "Confidence level in the selection",
          "minimum": 0.0,
          "maximum": 1.0
        },
        "reasoning": {
          "type": "object",
          "required": ["detected_intent", "material_classification", "matching_indicators", "estimated_time"],
          "properties": {
            "detected_intent": {
              "type": "string",
              "description": "What the user wants to achieve"
            },
            "material_classification": {
              "type": "string",
              "enum": ["procedural", "conceptual", "mixed"]
            },
            "matching_indicators": {
              "type": "array",
              "description": "Keywords or patterns found",
              "items": {
                "type": "string"
              },
              "minItems": 1
            },
            "estimated_time": {
              "type": "string",
              "description": "Time estimate or 'not applicable'",
              "pattern": "^(\\d+(-\\d+)? minutes?|not applicable)$"
            },
            "missing_information": {
              "type": "array",
              "description": "Information needed for selection (only when unable_to_determine)",
              "items": {
                "type": "string"
              }
            }
          }
        }
      }
    }
  </json_schema>
  
  <output_rules>
    - chain_of_thought: Array of strings, minimum 3 items, maximum 10 items
    - selected_type: Must be exactly one of: "overview", "concept", "quickstart", "howto", "tutorial", "unable_to_determine"
    - confidence: Decimal number between 0.0 and 1.0 (e.g., 0.85, not 85%)
    - detected_intent: String describing user's goal (or "unclear" if ambiguous)
    - material_classification: Must be exactly one of: "procedural", "conceptual", "mixed"
    - matching_indicators: Array of strings, minimum 1 item (can be empty array if unable_to_determine)
    - estimated_time: Either "X minutes", "X-Y minutes", or exactly "not applicable"
    - missing_information: Array of strings explaining what's needed (only include when selected_type is "unable_to_determine")
  </output_rules>
</required_output_format>

<selection_examples>
  <example id="1">
    <scenario>
      <user_request>Document how to configure network policies in Azure Kubernetes Service</user_request>
      <materials>Step-by-step commands for configuring network policies, multiple policy types</materials>
    </scenario>
    <correct_output>
      {
        "chain_of_thought": [
          "User request contains 'how to configure' - this is a task-oriented request",
          "Materials contain 'step-by-step commands' - clearly procedural content",
          "No explicit content type mentioned by user",
          "Time estimate: Multiple policy types suggest >10 minutes, ruling out quickstart",
          "No learning indicators like 'tutorial' or 'learn' present",
          "Multiple policy types indicate various approaches exist",
          "Best match is 'howto' - task-oriented with multiple approaches"
        ],
        "selected_type": "howto",
        "confidence": 0.95,
        "reasoning": {
          "detected_intent": "Configure network policies",
          "material_classification": "procedural",
          "matching_indicators": ["how to", "configure", "step-by-step"],
          "estimated_time": "15-20 minutes"
        }
      }
    </correct_output>
  </example>
  
  <example id="2">
    <scenario>
      <user_request>Explain what Azure Container Registry is to new users</user_request>
      <materials>Service description, feature list, use cases, no procedures</materials>
    </scenario>
    <correct_output>
      {
        "chain_of_thought": [
          "User request contains 'Explain what' - seeking understanding, not task completion",
          "Target audience specified as 'new users' - introductory content needed",
          "Materials are purely descriptive: service description, features, use cases",
          "No procedural content in materials - confirms conceptual nature",
          "High-level introduction for new users suggests 'overview' not deep 'concept'",
          "Keywords 'what' and 'new users' strongly indicate overview type"
        ],
        "selected_type": "overview",
        "confidence": 0.90,
        "reasoning": {
          "detected_intent": "Introduce service to new users",
          "material_classification": "conceptual",
          "matching_indicators": ["what", "new users", "feature list"],
          "estimated_time": "not applicable"
        }
      }
    </correct_output>
  </example>
  
  <example id="3">
    <scenario>
      <user_request>Create a quick tutorial to get started with Azure Functions</user_request>
      <materials>Simple hello world function, deployment steps, 5-minute setup</materials>
    </scenario>
    <correct_output>
      {
        "chain_of_thought": [
          "User explicitly mentions 'tutorial' - but also says 'quick'",
          "Materials show '5-minute setup' and 'hello world' - very basic content",
          "Conflicting signals: 'tutorial' suggests learning journey, 'quick' and '5-minute' suggest quickstart",
          "Checking time constraint: 5 minutes is under 10-minute quickstart limit",
          "Materials are minimal (hello world) fitting quickstart pattern",
          "Despite 'tutorial' mention, the 'quick' modifier and 5-minute timeframe better match quickstart",
          "Quickstart is more appropriate for this scenario"
        ],
        "selected_type": "quickstart",
        "confidence": 0.85,
        "reasoning": {
          "detected_intent": "Quick introduction to Azure Functions",
          "material_classification": "procedural",
          "matching_indicators": ["quick", "get started", "5-minute", "hello world"],
          "estimated_time": "5 minutes"
        }
      }
    </correct_output>
  </example>
  
  <example id="4">
    <scenario>
      <user_request>Need something for Azure Cognitive Search</user_request>
      <materials>Search index concepts, relevance scoring, analyzers, indexers, some API examples, pricing tiers, use cases</materials>
    </scenario>
    <correct_output>
      {
        "chain_of_thought": [
          "User request 'Need something' is extremely vague - no clear intent",
          "Could mean: overview for new users, how to implement, understanding architecture, or quick setup",
          "Materials are mixed: concepts (relevance scoring, analyzers) and 'some API examples' (procedural)",
          "No audience specified - could be for beginners or advanced users",
          "No time constraints or scope indicators provided",
          "Unable to determine if this should be understanding-focused or task-focused",
          "Cannot confidently select any content type without more context"
        ],
        "selected_type": "unable_to_determine",
        "confidence": 0.0,
        "reasoning": {
          "detected_intent": "unclear",
          "material_classification": "mixed",
          "matching_indicators": [],
          "estimated_time": "not applicable",
          "missing_information": [
            "What is the specific goal? (e.g., 'understand how it works', 'implement search', 'get started quickly')",
            "Who is the target audience? (new users, developers with search experience, etc.)",
            "What scope is needed? (high-level overview, specific feature like analyzers, end-to-end implementation)",
            "If implementation-focused, what's the complexity? (basic search, advanced features with custom analyzers)"
          ]
        }
      }
    </correct_output>
  </example>
</selection_examples>

<special_cases>
  <case name="ambiguous_request">
    <condition>User intent unclear and materials are mixed</condition>
    <action>Select based on primary material type (procedural vs conceptual)</action>
  </case>
  
  <case name="conflicting_requirements">
    <condition>User wants "quick tutorial" but task takes 30+ minutes</condition>
    <action>Select "howto" and note the time constraint conflict</action>
  </case>
  
  <case name="no_clear_match">
    <condition>No content type clearly matches</condition>
    <action>
      Return a response explaining:
      1. Why no content type could be confidently selected
      2. What specific information is missing or unclear
      3. What clarification would help make a selection
      
      Example output:
      {
        "selected_type": "unable_to_determine",
        "confidence": 0.0,
        "chain_of_thought": [
          "User request lacks clear intent indicators",
          "Materials contain both conceptual and procedural content equally",
          "No time estimates provided to distinguish quickstart vs full procedures",
          "Unable to determine if learning journey or task completion is desired"
        ],
        "reasoning": {
          "detected_intent": "unclear",
          "material_classification": "mixed",
          "matching_indicators": [],
          "estimated_time": "not applicable",
          "missing_information": [
            "Clear user intent: Is this for understanding or task completion?",
            "Target audience: New users or experienced developers?",
            "Scope: Quick introduction or comprehensive coverage?",
            "If procedural: How long should the task take to complete?"
          ]
        }
      }
    </action>
  </case>
</special_cases>

</content_type_selection_instructions> 