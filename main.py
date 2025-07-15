#!/usr/bin/env python3
"""
AI Content Developer - Main Entry Point

A tool for analyzing repositories and generating documentation based on support materials.
"""
import argparse
import sys
from pathlib import Path
import logging
import os
import shutil
from urllib.parse import urlparse

from content_developer.models import Config
from content_developer.orchestrator import ContentDeveloperOrchestrator
from content_developer.display import display_results
from content_developer.display.console_display import ConsoleDisplay
from content_developer.utils.logging_config import setup_dual_logging, get_console
from content_developer.constants import MAX_PHASES

# Import multi-agent system if available
try:
    from multi_agent_content_developer import MultiAgentContentDeveloper
    MULTI_AGENT_AVAILABLE = True
except ImportError:
    MULTI_AGENT_AVAILABLE = False


def perform_cleanup(console_display: ConsoleDisplay, work_dir: Path):
    """Clean up llm_outputs and work directory"""
    console_display.show_status("Cleaning up directories...", "info")
    
    # Directories to clean
    directories_to_clean = [
        "./llm_outputs",
        work_dir
    ]
    
    for directory in directories_to_clean:
        dir_path = Path(directory)
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                console_display.show_status(f"Removed: {directory}", "success")
            except Exception as e:
                console_display.show_error(f"Failed to remove {directory}: {e}", "Warning")
        else:
            console_display.show_status(f"Directory not found: {directory}", "info")
    
    console_display.show_status("Cleanup complete", "success")
    console_display.print_separator()


def main():
    """Main entry point"""
    # Set up argument parser first
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Set up dual logging before any other operations
    # Use INFO level for console if verbose, otherwise WARNING
    console_level = "INFO" if hasattr(args, 'verbose') and args.verbose else "WARNING"
    setup_dual_logging(console_level=console_level)
    
    # Create console display
    console = get_console()
    console_display = ConsoleDisplay(console)
    
    # Handle cleanup if requested
    if hasattr(args, 'clean') and args.clean:
        perform_cleanup(console_display, args.work_dir)
    
    # Validate arguments
    validate_arguments(parser, args)
    
    # Create configuration
    config = create_config_from_args(args)
    
    # Execute workflow with console display
    execute_workflow(config, console_display)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser"""
    parser = argparse.ArgumentParser(
        description="AI Content Developer - Generate documentation from support materials",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=get_usage_examples()
    )
    
    # Add all argument groups
    add_required_arguments(parser)
    add_material_arguments(parser)
    add_audience_arguments(parser)
    add_workflow_arguments(parser)
    add_output_arguments(parser)
    add_debug_arguments(parser)
    
    return parser


def get_usage_examples() -> str:
    """Get formatted usage examples for help text"""
    return """
Examples:
  # Basic usage with materials
  python main.py --repo https://github.com/user/repo --goal "Create CNI docs" \\
    --service "Azure Kubernetes Service" -m material1.pdf material2.md
  
  # Using raw text as material
  python main.py --repo https://github.com/user/repo --goal "Create docs" \\
    --service "AKS" -m "Azure CNI enables native Azure networking for pods"
  
  # Mixing files, URLs, and raw text
  python main.py --repo https://github.com/user/repo --goal "Update guide" \\
    --service "AKS" -m guide.pdf https://docs.azure.com/aks "Additional context here"
  
  # Clean previous runs and start fresh
  python main.py --repo https://github.com/user/repo --goal "Create tutorial" \\
    --service "AKS" --clean -m tutorial.md
  
  # Run with specific audience
  python main.py --repo https://github.com/user/repo --goal "Create networking guide" \\
    --service "AKS" --audience "DevOps engineers" --audience-level advanced \\
    -m material.pdf
  
  # Run for beginners
  python main.py --repo https://github.com/user/repo --goal "Create tutorial" \\
    --service "AKS" --audience "developers new to Kubernetes" \\
    --audience-level beginner -m tutorial.md
  
  # Run phases 1-3 only (analysis, strategy, generation)
  python main.py --repo https://github.com/user/repo --goal "Update networking guides" \\
    --service "AKS" --phases 3 -m material.docx
  
  # Auto-confirm selections and apply changes
  python main.py --repo https://github.com/user/repo --goal "Create tutorials" \\
    --service "AKS" --auto-confirm --apply-changes -m tutorial.md
  
  # Run all phases (1-5) and apply generated content
  python main.py --repo https://github.com/user/repo --goal "Update docs" \\
    --service "AKS" --apply-changes -m guide.pdf

Environment Variables:
  AZURE_OPENAI_ENDPOINT              - Azure OpenAI endpoint URL
  AZURE_OPENAI_COMPLETION_DEPLOYMENT - Deployment name for completion model
  AZURE_OPENAI_EMBEDDING_DEPLOYMENT  - Deployment name for embedding model
  AZURE_OPENAI_TEMPERATURE          - Temperature for completions (default: 0.3)
        """


def add_required_arguments(parser: argparse.ArgumentParser):
    """Add required arguments to parser"""
    required = parser.add_argument_group('required arguments')
    
    required.add_argument(
        "--repo", 
        required=True,
        dest="repo_url",
        help="Repository URL to analyze (e.g., https://github.com/user/repo)"
    )
    
    required.add_argument(
        "--goal", 
        required=True,
        dest="content_goal",
        help="Goal for content creation/update (e.g., 'Create networking guide')"
    )
    
    required.add_argument(
        "--service", 
        required=True,
        dest="service_area",
        help="Target Azure service area (e.g., 'Azure Kubernetes Service', 'AKS')"
    )
    
    required.add_argument(
        "-m", "--materials", 
        nargs="+", 
        required=True,
        help="Support materials: files, URLs, or raw text (e.g., file.pdf, https://example.com, or 'your raw text')"
    )


def add_material_arguments(parser: argparse.ArgumentParser):
    """Add material-related arguments"""
    materials = parser.add_argument_group('material configuration')
    
    materials.add_argument(
        "--content-limit", 
        type=int, 
        default=15000, 
        help="Maximum characters to extract from each material (default: 15000)"
    )


def add_audience_arguments(parser: argparse.ArgumentParser):
    """Add audience-related arguments"""
    audience = parser.add_argument_group('audience configuration')
    
    audience.add_argument(
        "--audience", 
        default="technical professionals", 
        help="Target audience description (default: 'technical professionals')"
    )
    
    audience.add_argument(
        "--audience-level", 
        default="intermediate", 
        choices=["beginner", "intermediate", "advanced"],
        help="Technical expertise level of the target audience (default: intermediate)"
    )


def add_workflow_arguments(parser: argparse.ArgumentParser):
    """Add workflow control arguments"""
    workflow_group = parser.add_argument_group(
        'Workflow Control',
        'Control the documentation workflow'
    )
    
    workflow_group.add_argument(
        '--phases', '-p',
        type=str,
        default=str(MAX_PHASES),
        help=f'Phases to execute (e.g., "1", "1-2", "3"). Default: "{MAX_PHASES}"'
    )
    
    workflow_group.add_argument(
        '--auto-confirm', '-y',
        action='store_true',
        help='Skip all confirmation prompts (useful for automation)'
    )
    
    workflow_group.add_argument(
        '--apply-changes', '-a',
        action='store_true',
        help='Apply generated changes to the repository'
    )
    
    workflow_group.add_argument(
        '--skip-toc',
        action='store_true',
        help='Skip updating the table of contents (toc.yml)'
    )
    
    workflow_group.add_argument(
        '--no-material-check',
        action='store_true',
        help='Skip material sufficiency check before content generation'
    )
    
    if MULTI_AGENT_AVAILABLE:
        workflow_group.add_argument(
            '--multi-agent',
            action='store_true',
            help='Use the multi-agent Azure AI Foundry system (requires Azure AI configuration)'
        )


def add_output_arguments(parser: argparse.ArgumentParser):
    """Add output configuration arguments"""
    output = parser.add_argument_group('output configuration')
    
    output.add_argument(
        "--work-dir", 
        type=Path, 
        default=Path.cwd() / "work" / "tmp", 
        help="Working directory for cloned repository (default: ./work/tmp)"
    )
    
    output.add_argument(
        "--max-depth", 
        type=int, 
        default=3, 
        help="Maximum repository depth to analyze (default: 3)"
    )


def add_debug_arguments(parser: argparse.ArgumentParser):
    """Add debugging arguments"""
    debug = parser.add_argument_group('debugging options')
    
    debug.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Show detailed console output (INFO level logging)"
    )
    
    debug.add_argument(
        "--debug-similarity", 
        action="store_true", 
        help="Show detailed similarity scoring for content matching"
    )


def validate_arguments(parser: argparse.ArgumentParser, args: argparse.Namespace):
    """Validate parsed arguments"""
    # Validate phases
    if args.phases != "all" and not (args.phases.isdigit() and 1 <= int(args.phases) <= MAX_PHASES):
        parser.error(f"--phases must be a number between 1 and {MAX_PHASES}, or 'all'")
    
    # Validate repository URL
    if not is_valid_url(args.repo_url):
        parser.error(f"Invalid repository URL: {args.repo_url}")
    
    # Validate materials - allow raw text, files, or URLs
    for material in args.materials:
        # If it's not a URL and not an existing file, treat it as raw text
        if not is_valid_url(material) and not Path(material).exists():
            # Will be treated as raw text input by ContentExtractor
            pass
    
    # Validate work directory
    try:
        args.work_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        parser.error(f"Cannot create work directory {args.work_dir}: {e}")
    
    # Check Azure OpenAI configuration
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        parser.error("AZURE_OPENAI_ENDPOINT environment variable not set. See --help for details.")
    
    # Check if accessing GitHub without token (informational only)
    if 'github.com' in args.repo_url and not os.getenv("GITHUB_TOKEN"):
        print("ℹ️  No GitHub token configured. Only public repositories will be accessible.")
        print("   For private repositories, add GITHUB_TOKEN to your .env file.")
        print("   See README.md for instructions on creating a token.\n")


def is_valid_url(url: str) -> bool:
    """Check if string is a valid URL"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def create_config_from_args(args: argparse.Namespace) -> Config:
    """Create Config object from parsed arguments"""
    return Config(
        repo_url=args.repo_url,
        content_goal=args.content_goal,
        service_area=args.service_area,
        audience=args.audience,
        audience_level=args.audience_level,
        support_materials=args.materials,
        auto_confirm=args.auto_confirm,
        work_dir=args.work_dir,
        max_repo_depth=args.max_depth,
        content_limit=args.content_limit,
        phases=args.phases,
        debug_similarity=args.debug_similarity,
        apply_changes=args.apply_changes,
        skip_toc=args.skip_toc,
        check_material_sufficiency=not args.no_material_check,
        multi_agent=getattr(args, 'multi_agent', False)
    )


def execute_workflow(config: Config, console_display: ConsoleDisplay):
    """Execute the content development workflow"""
    try:
        # Check if multi-agent mode is requested
        if hasattr(config, 'multi_agent') and config.multi_agent and MULTI_AGENT_AVAILABLE:
            repo_name = config.repo_url.split('/')[-1].replace('.git', '')
            console_display.show_header(f"{repo_name} (Multi-Agent)", config.content_goal, config.service_area)
            console_display.show_status("Using Azure AI Foundry multi-agent system", "info")
            
            # Use multi-agent system
            developer = MultiAgentContentDeveloper(config)
            try:
                result = developer.process_documentation_request()
                
                # Display results
                if result.success:
                    console_display.show_status(result.message, "success")
                else:
                    console_display.show_error(result.message, "Workflow Failed")
                    
            finally:
                # Clean up agents
                developer.cleanup()
        else:
            # Use traditional orchestrator
            repo_name = config.repo_url.split('/')[-1].replace('.git', '')
            console_display.show_header(repo_name, config.content_goal, config.service_area)
            
            # Initialize orchestrator
            orchestrator = ContentDeveloperOrchestrator(config, console_display)
            
            # Execute workflow
            result = orchestrator.execute()
            
            # Display results
            if result.success:
                display_results(result)
            else:
                console_display.show_error(result.message, "Workflow Failed")
        
        return result.success
        
    except KeyboardInterrupt:
        raise  # Re-raise to be handled by main
    except Exception as e:
        console_display.show_error(str(e), "Workflow Error")
        logging.exception("Workflow execution failed")
        return False


def handle_keyboard_interrupt(console_display: ConsoleDisplay):
    """Handle user cancellation"""
    console_display.show_error("Operation cancelled by user", "Cancelled")
    sys.exit(1)


def handle_error(error: Exception, console_display: ConsoleDisplay):
    """Handle general errors"""
    console_display.show_error(str(error), "Error")
    logging.exception("Fatal error occurred")
    sys.exit(1)


if __name__ == "__main__":
    main() 