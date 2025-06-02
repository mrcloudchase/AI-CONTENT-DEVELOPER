"""
Console display manager using Rich for beautiful output
"""
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
import time

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.layout import Layout
from rich.live import Live
from rich.columns import Columns
from rich.text import Text
from rich.markdown import Markdown
from rich import box


class ConsoleDisplay:
    """Manages console output with Rich components"""
    
    def __init__(self, console: Optional[Console] = None):
        """Initialize console display manager"""
        self.console = console or Console()
        self.current_phase = None
        
    def show_header(self, repo_name: str, goal: str, service: str) -> None:
        """Show application header with run information"""
        header_content = f"""[bold cyan]AI Content Developer[/bold cyan]
        
[bold]Repository:[/bold] {repo_name}
[bold]Goal:[/bold] {goal}
[bold]Service:[/bold] {service}"""
        
        panel = Panel(
            header_content,
            box=box.ROUNDED,
            border_style="bright_blue",
            padding=(1, 2)
        )
        self.console.print(panel)
        self.console.print()
    
    @contextmanager
    def phase_progress(self, phase_name: str, total_steps: int = 100):
        """Context manager for phase progress display"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
            transient=False
        ) as progress:
            task_id = progress.add_task(f"📋 Phase {phase_name}", total=total_steps)
            
            # Provide progress updater
            def update(advance: int = 1, description: Optional[str] = None):
                if description:
                    progress.update(task_id, description=f"📋 Phase {phase_name}: {description}")
                progress.update(task_id, advance=advance)
            
            progress.update_func = update
            progress.task_id = task_id
            
            yield progress
            
            # Complete the progress
            progress.update(task_id, completed=total_steps)
    
    def show_operation(self, operation: str, emoji: str = "⚡") -> None:
        """Show current operation with spinner"""
        self.console.print(f"  {emoji} {operation}", style="dim")
    
    def show_thinking(self, thinking: str, title: str = "🤔 AI Thinking") -> None:
        """Display AI thinking in a formatted panel"""
        if not thinking:
            return
            
        # Clean up thinking text
        thinking = thinking.strip()
        
        # Create a panel with the thinking
        thinking_panel = Panel(
            thinking,
            title=title,
            title_align="left",
            border_style="yellow",
            box=box.ROUNDED,
            padding=(1, 2),
            width=min(100, self.console.width - 4)
        )
        
        self.console.print()
        self.console.print(thinking_panel)
        self.console.print()
    
    def show_decision(self, decision: Dict[str, Any]) -> None:
        """Display a content strategy decision"""
        action = decision.get('action', 'UNKNOWN')
        filename = decision.get('filename', 'unknown')
        reason = decision.get('reason', 'No reason provided')
        
        # Choose emoji and color based on action
        action_styles = {
            'CREATE': ('🆕', 'green'),
            'UPDATE': ('📝', 'yellow'),
            'SKIP': ('⏭️', 'dim')
        }
        emoji, color = action_styles.get(action, ('❓', 'white'))
        
        # Create decision text
        decision_text = f"{emoji} [bold {color}]{action}[/bold {color}]: {filename}"
        self.console.print(f"  {decision_text}")
        self.console.print(f"    [dim]Reason: {reason}[/dim]")
        self.console.print()
    
    def show_status(self, message: str, status: str = "info") -> None:
        """Show a status message with appropriate styling"""
        status_styles = {
            'success': ('✓', 'green'),
            'error': ('✗', 'red'),
            'warning': ('⚠', 'yellow'),
            'info': ('ℹ', 'blue')
        }
        
        emoji, color = status_styles.get(status, ('•', 'white'))
        self.console.print(f"  {emoji} [{color}]{message}[/{color}]")
    
    def show_results_table(self, title: str, results: List[Dict[str, Any]]) -> None:
        """Display results in a formatted table"""
        if not results:
            return
            
        table = Table(title=title, box=box.ROUNDED)
        
        # Add columns based on first result
        if results:
            for key in results[0].keys():
                table.add_column(key.replace('_', ' ').title())
            
            # Add rows
            for result in results:
                row = [str(result.get(key, '')) for key in results[0].keys()]
                table.add_row(*row)
        
        self.console.print(table)
        self.console.print()
    
    def show_file_preview(self, filename: str, content: str, max_lines: int = 20) -> None:
        """Show a preview of generated file content"""
        lines = content.split('\n')
        preview_lines = lines[:max_lines]
        
        if len(lines) > max_lines:
            preview_content = '\n'.join(preview_lines) + f"\n\n... ({len(lines) - max_lines} more lines)"
        else:
            preview_content = content
        
        # Use syntax highlighting for markdown
        syntax = Syntax(preview_content, "markdown", theme="monokai", line_numbers=True)
        
        panel = Panel(
            syntax,
            title=f"📄 {filename}",
            title_align="left",
            border_style="blue",
            box=box.ROUNDED
        )
        
        self.console.print(panel)
        self.console.print()
    
    def show_error(self, error: str, title: str = "Error") -> None:
        """Display an error message in a panel"""
        error_panel = Panel(
            f"[bold red]{error}[/bold red]",
            title=f"❌ {title}",
            title_align="left",
            border_style="red",
            box=box.ROUNDED,
            padding=(1, 2)
        )
        
        self.console.print()
        self.console.print(error_panel)
        self.console.print()
    
    def show_phase_summary(self, phase_name: str, summary: Dict[str, Any]) -> None:
        """Show a summary at the end of a phase"""
        # Create summary content
        summary_lines = []
        for key, value in summary.items():
            if isinstance(value, list):
                summary_lines.append(f"[bold]{key}:[/bold] {len(value)} items")
            elif isinstance(value, bool):
                summary_lines.append(f"[bold]{key}:[/bold] {'Yes' if value else 'No'}")
            else:
                summary_lines.append(f"[bold]{key}:[/bold] {value}")
        
        summary_content = '\n'.join(summary_lines)
        
        panel = Panel(
            summary_content,
            title=f"✅ Phase {phase_name} Complete",
            title_align="left",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2)
        )
        
        self.console.print()
        self.console.print(panel)
        self.console.print()
    
    @contextmanager
    def live_status(self, initial_status: str = "Processing..."):
        """Context manager for live updating status display"""
        with Live(
            Panel(initial_status, title="Status", border_style="blue"),
            console=self.console,
            refresh_per_second=4
        ) as live:
            def update_status(status: str, title: str = "Status", style: str = "blue"):
                live.update(Panel(status, title=title, border_style=style))
            
            live.update_status = update_status
            yield live
    
    def clear(self) -> None:
        """Clear the console"""
        self.console.clear()
    
    def print_separator(self) -> None:
        """Print a visual separator"""
        self.console.print("─" * min(80, self.console.width), style="dim")
        self.console.print() 