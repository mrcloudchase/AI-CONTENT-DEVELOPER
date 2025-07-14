"""
Interactive confirmation for content remediation steps
"""
import logging
from typing import Dict, Tuple, Optional

from .generic_interactive import GenericInteractive

logger = logging.getLogger(__name__)


class RemediationConfirmation(GenericInteractive):
    """Interactive confirmation for remediation steps"""
    
    def __init__(self, config, console_display):
        """Initialize with config and console display"""
        super().__init__(config)
        self.console_display = console_display
        self.auto_approve_remaining = False
        self.skip_all_remaining = False
    
    def confirm_step_result(self, original_content: str, remediated_content: str,
                           step_name: str, metadata: Dict, file_info: Dict) -> Tuple[bool, str]:
        """
        Confirm remediation step result with interactive options
        
        Args:
            original_content: Original content before remediation
            remediated_content: Content after remediation
            step_name: Name of the remediation step (SEO, Security, Accuracy)
            metadata: Metadata from the remediation processor
            file_info: Information about the file being processed
            
        Returns:
            Tuple of (approved: bool, content: str)
        """
        # Check for auto-approval modes
        if self.config.auto_confirm or self.auto_approve_remaining:
            return True, remediated_content
        
        if self.skip_all_remaining:
            return False, original_content
        
        # Show summary of changes
        self._display_remediation_summary(step_name, file_info, metadata)
        
        # Interactive confirmation loop
        while True:
            choice = input(
                f"\nAccept {step_name} changes? "
                "(y/n/v to view diff/d for details/a to accept all/s to skip all): "
            ).lower().strip()
            
            if choice == 'y':
                return True, remediated_content
            elif choice == 'n':
                if self.console_display:
                    self.console_display.show_status(
                        f"{step_name} changes rejected - keeping original", 
                        "warning"
                    )
                return False, original_content
            elif choice == 'v':
                # Show diff view
                if self.console_display:
                    self.console_display.show_content_diff(
                        original_content, 
                        remediated_content,
                        title=f"{step_name} Changes"
                    )
            elif choice == 'd':
                # Show detailed metadata
                self._show_detailed_metadata(metadata, step_name)
            elif choice == 'a':
                # Accept all remaining
                self.auto_approve_remaining = True
                if self.console_display:
                    self.console_display.show_status(
                        "Auto-approving all remaining remediation steps", 
                        "info"
                    )
                return True, remediated_content
            elif choice == 's':
                # Skip all remaining
                self.skip_all_remaining = True
                if self.console_display:
                    self.console_display.show_status(
                        "Skipping all remaining remediation steps", 
                        "warning"
                    )
                return False, original_content
            else:
                print("Invalid choice. Please enter y, n, v, d, a, or s.")
    
    def _display_remediation_summary(self, step_name: str, file_info: Dict, 
                                    metadata: Dict) -> None:
        """Display a summary of remediation changes"""
        if not self.console_display:
            return
        
        # Get step-specific summary
        if step_name == "SEO Optimization":
            self._show_seo_summary(metadata)
        elif step_name == "Security Remediation":
            self._show_security_summary(metadata)
        elif step_name == "Technical Accuracy":
            self._show_accuracy_summary(metadata)
    
    def _show_seo_summary(self, metadata: Dict) -> None:
        """Show SEO-specific summary"""
        improvements = metadata.get('seo_improvements', [])
        if improvements:
            for improvement in improvements[:5]:  # Show top 5
                self.console_display.show_status(f"  • {improvement}", "success")
            if len(improvements) > 5:
                self.console_display.show_status(
                    f"  ... and {len(improvements) - 5} more improvements", 
                    "info"
                )
        
        # Show meta description if added
        if meta_desc := metadata.get('meta_description'):
            self.console_display.show_status(
                f"  • Added meta description ({len(meta_desc)} chars)", 
                "success"
            )
    
    def _show_security_summary(self, metadata: Dict) -> None:
        """Show security-specific summary"""
        issues = metadata.get('security_issues_found', [])
        if issues:
            self.console_display.show_warning(f"Found {len(issues)} security issues:")
            for issue in issues[:5]:
                issue_type = issue.get('type', 'unknown')
                remediation = issue.get('remediation', 'fixed')
                self.console_display.show_status(
                    f"  • {issue_type}: {remediation}", 
                    "warning"
                )
            if len(issues) > 5:
                self.console_display.show_status(
                    f"  ... and {len(issues) - 5} more issues remediated", 
                    "warning"
                )
        else:
            self.console_display.show_status("  ✓ No security issues found", "success")
    
    def _show_accuracy_summary(self, metadata: Dict) -> None:
        """Show accuracy validation summary"""
        score = metadata.get('accuracy_score', 0.0)
        validation_result = metadata.get('validation_result', 'unknown')
        
        # Show score with appropriate styling
        if validation_result == 'pass':
            self.console_display.show_status(
                f"  ✓ Accuracy validated: {score * 100:.0f}%", 
                "success"
            )
        elif validation_result == 'pass_with_corrections':
            self.console_display.show_warning(
                f"  ⚠️  Accuracy validated with corrections: {score * 100:.0f}%"
            )
        else:
            self.console_display.show_error(
                f"  ❌ Validation concerns: {score * 100:.0f}%",
                "Accuracy"
            )
        
        # Show issues if any
        issues = metadata.get('accuracy_issues', [])
        if issues:
            for issue in issues[:3]:
                self.console_display.show_status(
                    f"  • {issue.get('type', 'unknown')}: {issue.get('issue', '')}",
                    "warning"
                )
            if len(issues) > 3:
                self.console_display.show_status(
                    f"  ... and {len(issues) - 3} more corrections",
                    "info"
                )
    
    def _show_detailed_metadata(self, metadata: Dict, step_name: str) -> None:
        """Show detailed metadata for a remediation step"""
        if not self.console_display:
            return
        
        # Show thinking if available
        if thinking := metadata.get('thinking'):
            self.console_display.show_thinking(thinking, f"🤔 {step_name} Analysis")
        
        # Show step-specific details
        if step_name == "SEO Optimization":
            if keywords := metadata.get('primary_keywords'):
                self.console_display.show_metric("Primary Keywords", ', '.join(keywords))
            if link_suggestions := metadata.get('internal_link_suggestions'):
                self.console_display.show_metric(
                    "Link Suggestions", 
                    f"{len(link_suggestions)} internal links suggested"
                )
        
        elif step_name == "Security Remediation":
            if warnings := metadata.get('security_warnings_added'):
                self.console_display.show_metric(
                    "Security Warnings Added", 
                    f"{len(warnings)} warnings"
                )
            if compliance := metadata.get('compliance_notes'):
                self.console_display.show_metric(
                    "Compliance Notes", 
                    f"{len(compliance)} notes"
                )
        
        elif step_name == "Technical Accuracy":
            if unsupported := metadata.get('unsupported_claims'):
                self.console_display.show_metric(
                    "Unsupported Claims", 
                    f"{len(unsupported)} claims need verification"
                )
            if suggestions := metadata.get('suggestions'):
                self.console_display.show_metric(
                    "Improvement Suggestions", 
                    f"{len(suggestions)} suggestions"
                )
    
    def reset_for_new_file(self) -> None:
        """Reset auto-approval flags for a new file"""
        # Keep the skip_all_remaining flag but reset auto_approve
        # This allows skipping all files while still reviewing each file that isn't skipped
        self.auto_approve_remaining = False 