#!/usr/bin/env python3
"""
AI Content Developer - Main Entry Point

A tool for analyzing repositories and generating documentation based on support materials.
"""
import argparse
import sys
from pathlib import Path

from content_developer.models import Config
from content_developer.orchestrator import ContentDeveloperOrchestrator
from content_developer.display import display_results
from content_developer.constants import MAX_PHASES


def main():
    """Main entry point"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Validate arguments
    validate_arguments(parser, args)
    
    # Create configuration
    config = create_config_from_args(args)
    
    # Execute workflow
    execute_workflow(config)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser"""
    parser = argparse.ArgumentParser(
        description="AI Content Developer - Generate documentation from support materials",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=get_usage_examples()
    )
    
    add_required_arguments(parser)
    add_optional_arguments(parser)
    
    return parser


def get_usage_examples() -> str:
    """Get formatted usage examples for help text"""
    return """
Examples:
  # Run all phases by default (no --phases needed)
  python main.py https://github.com/user/repo "Create CNI docs" "Azure Kubernetes Service" material1.pdf material2.md
  
  # Run with specific audience
  python main.py https://github.com/user/repo "Create networking guide" "AKS" --audience "DevOps engineers" --audience-level advanced material.pdf
  
  # Run for beginners
  python main.py https://github.com/user/repo "Create tutorial" "AKS" --audience "developers new to Kubernetes" --audience-level beginner tutorial.md
  
  # Run specific phases only
  python main.py https://github.com/user/repo "Update networking guides" "AKS" --phases 12 material.docx
  
  # Auto-confirm selections
  python main.py https://github.com/user/repo "Create tutorials" "AKS" --auto-confirm tutorial.md
  
  # Apply generated content and update TOC (phases 3-4)
  python main.py https://github.com/user/repo "Update docs" "AKS" --phases 34 --apply-changes
        """


def add_required_arguments(parser: argparse.ArgumentParser):
    """Add required arguments to parser"""
    parser.add_argument("repo_url", help="Repository URL to analyze")
    parser.add_argument("content_goal", help="Goal for content creation/update")
    parser.add_argument("service_area", help="Service area (e.g., 'Azure Kubernetes Service')")


def add_optional_arguments(parser: argparse.ArgumentParser):
    """Add optional arguments to parser"""
    parser.add_argument("materials", nargs="*", help="Support material files/URLs")
    parser.add_argument("--audience", default="technical professionals", help="Target audience for the content")
    parser.add_argument("--audience-level", default="intermediate", 
                       choices=["beginner", "intermediate", "advanced"],
                       help="Technical level of the target audience")
    parser.add_argument("--auto-confirm", "-y", action="store_true", help="Auto-confirm all prompts")
    parser.add_argument("--work-dir", type=Path, default=Path.cwd() / "work" / "tmp", help="Working directory")
    parser.add_argument("--max-depth", type=int, default=3, help="Max repository depth to analyze")
    parser.add_argument("--content-limit", type=int, default=15000, help="Content extraction limit")
    parser.add_argument("--phases", default="all", help="Phases to run (1-4, or 'all' for all phases)")
    parser.add_argument("--debug-similarity", action="store_true", help="Show similarity scoring details")
    parser.add_argument("--apply-changes", action="store_true", help="Apply generated content to repository")
    parser.add_argument("--skip-toc", action="store_true", help="Skip TOC management (Phase 4) if TOC.yml is invalid")


def validate_arguments(parser: argparse.ArgumentParser, args: argparse.Namespace):
    """Validate parsed arguments"""
    valid_phases = "".join(str(i) for i in range(1, MAX_PHASES + 1))
    if args.phases != "all" and not all(phase in valid_phases for phase in args.phases):
        parser.error(f"Phases must be combination of {', '.join(valid_phases)}, or 'all'")


def create_config_from_args(args: argparse.Namespace) -> Config:
    """Create Config object from parsed arguments"""
    return Config(
        repo_url=args.repo_url,
        content_goal=args.content_goal,
        service_area=args.service_area,
        audience=args.audience,
        audience_level=args.audience_level.replace("-", "_"),  # Convert kebab-case to snake_case
        support_materials=args.materials,
        auto_confirm=args.auto_confirm,
        work_dir=args.work_dir,
        max_repo_depth=args.max_depth,
        content_limit=args.content_limit,
        phases=args.phases,
        debug_similarity=args.debug_similarity,
        apply_changes=args.apply_changes,
        skip_toc=args.skip_toc
    )


def execute_workflow(config: Config):
    """Execute the content development workflow"""
    try:
        orchestrator = ContentDeveloperOrchestrator(config)
        result = orchestrator.execute()
        display_results(result)
        
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        handle_error(e)


def handle_keyboard_interrupt():
    """Handle user cancellation"""
    print("\n\n⚠️  Operation cancelled by user")
    sys.exit(1)


def handle_error(error: Exception):
    """Handle general errors"""
    print(f"\n\n❌ Error: {error}")
    sys.exit(1)


if __name__ == "__main__":
    main() 