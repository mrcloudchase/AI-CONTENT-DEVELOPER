# Interactive Content Remediation

## Overview

The AI Content Developer now includes interactive content remediation functionality in Phase 4. When running without the `--auto-confirm` flag, users can review and approve or reject changes at each remediation step.

## How It Works

During Phase 4 (Content Remediation), the tool processes each generated file through three sequential steps:

1. **SEO Optimization** - Improves search engine visibility
2. **Security Remediation** - Removes sensitive information
3. **Technical Accuracy Validation** - Ensures content accuracy

At each step, you're presented with:
- A summary of changes made
- Interactive options to review and control the process

## Interactive Options

When prompted at each remediation step, you have these options:

- **`y`** - Accept the changes and proceed
- **`n`** - Reject the changes and keep the original content
- **`v`** - View a detailed diff showing what changed
- **`d`** - Display detailed metadata about the remediation
- **`a`** - Accept all remaining remediation steps automatically
- **`s`** - Skip all remaining remediation steps

## Example Interaction

```
Step 1: SEO Optimization
  • Title optimized: "Network Policies" → "Azure Kubernetes Service Network Policies"
  • Added meta description (156 chars)
  • Improved 3 heading structures
  • Added 5 internal link suggestions

Accept SEO Optimization changes? (y/n/v to view diff/d for details/a to accept all/s to skip all): v

📝 SEO Optimization Changes
───────────────────────────────────────────────────────────
--- Original
+++ After Remediation
@@ -1,5 +1,11 @@
-# Network Policies
+---
+title: Azure Kubernetes Service Network Policies: Secure Pod Communication
+description: Learn how to implement and manage network policies in AKS...
+ms.date: 2024-01-15
+---
+
+# Azure Kubernetes Service Network Policies: Secure Pod Communication

-This document covers network policies.
+Learn how to implement and manage network policies in Azure Kubernetes 
+Service (AKS) to control traffic flow between pods and enhance security.
───────────────────────────────────────────────────────────
Changes: +8 lines, -2 lines

Accept SEO Optimization changes? (y/n/v to view diff/d for details/a to accept all/s to skip all): y
✓ SEO changes applied
```

## Viewing Diffs

When you press `v`, the tool displays a unified diff view with:
- **Red lines** (`-`) showing removed content
- **Green lines** (`+`) showing added content
- **Blue lines** (`@`) showing line numbers
- Context lines around changes for clarity

The diff is displayed in a scrollable panel if it's too long, with a summary of total lines added/removed.

## Batch Operations

### Accept All Remaining (`a`)
When you press `a`, all remaining remediation steps for all files will be automatically approved. This is useful when:
- You've reviewed a few files and trust the remediation process
- The changes look consistently good
- You want to speed up the process

### Skip All Remaining (`s`)
When you press `s`, all remaining remediation steps will be skipped. This is useful when:
- You want to keep the original content
- You plan to do manual remediation later
- You see issues with the automated remediation

## Per-File Reset

The "accept all" flag resets for each new file, allowing you to:
- Auto-approve all steps for one file
- Still review the next file interactively
- Maintain control over the process

The "skip all" flag persists across files once set.

## With Auto-Confirm

When running with `--auto-confirm`, the remediation process works exactly as before:
- All remediation steps are automatically applied
- No interactive prompts are shown
- The process runs unattended

## Phase Summary

After remediation completes, the phase summary shows:
- Success rates for each remediation type
- Number of files with rejected steps
- Rejection rates (if any steps were rejected)

Example:
```
✅ Phase 4: Content Remediation Complete
─────────────────────────────────────────
Files Processed: 5
SEO Optimized: 80%
Security Checked: 100%
Accuracy Validated: 60%
All Steps Complete: 3
Files with Rejections: 2
SEO Rejected: 20%
Accuracy Rejected: 40%
```

## Testing

Use the provided test script to try the interactive functionality:

```bash
./scripts/test_interactive_remediation.sh
```

This script:
1. Creates a test material with security issues
2. Runs the tool through Phase 4
3. Allows you to interact with each remediation step
4. Shows the final remediated content

## Implementation Details

The interactive functionality is implemented through:

1. **`RemediationConfirmation`** class in `content_developer/interactive/remediation.py`
   - Handles user interaction for each remediation step
   - Manages auto-approve and skip-all flags
   - Displays summaries and detailed metadata

2. **Enhanced `ConsoleDisplay`** with `show_content_diff()` method
   - Generates unified diffs with syntax highlighting
   - Shows changes in an easy-to-read format
   - Provides change statistics

3. **Modified `ContentRemediationProcessor`**
   - Integrates interactive confirmation at each step
   - Tracks rejected steps
   - Maintains the last approved content version

The implementation maintains backward compatibility - existing scripts and workflows continue to work exactly as before when using `--auto-confirm`. 