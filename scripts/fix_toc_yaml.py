#!/usr/bin/env python3
"""
Fix common YAML issues in TOC.yml files
"""
import sys
import re
from pathlib import Path


def fix_toc_yaml(toc_path: str, output_path: str = None):
    """Fix common YAML issues in TOC.yml"""
    path = Path(toc_path)
    
    if not path.exists():
        print(f"❌ Error: File not found: {toc_path}")
        return False
    
    print(f"Reading: {path}")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_lines = content.split('\n')
        fixed_lines = []
        issues_fixed = 0
        
        for i, line in enumerate(original_lines, 1):
            fixed_line = line
            
            # Fix 1: Remove trailing spaces
            if line != line.rstrip():
                fixed_line = line.rstrip()
                issues_fixed += 1
                print(f"  Line {i}: Removed trailing spaces")
            
            # Fix 2: Ensure proper spacing after colons
            if ':' in fixed_line and not fixed_line.strip().endswith(':'):
                # Check if there's a value after the colon
                parts = fixed_line.split(':', 1)
                if len(parts) == 2 and parts[1] and not parts[1].startswith(' '):
                    fixed_line = parts[0] + ': ' + parts[1].lstrip()
                    issues_fixed += 1
                    print(f"  Line {i}: Added space after colon")
            
            # Fix 3: Check for tabs and replace with spaces
            if '\t' in fixed_line:
                # Count leading spaces/tabs to determine indent level
                indent_level = len(fixed_line) - len(fixed_line.lstrip())
                fixed_line = fixed_line.replace('\t', '  ')  # Replace tabs with 2 spaces
                issues_fixed += 1
                print(f"  Line {i}: Replaced tabs with spaces")
            
            # Fix 4: Check for duplicate keys on same level (basic check)
            if fixed_line.strip().startswith('- name:'):
                # This is a basic check - more complex validation would need full YAML parsing
                if i < len(original_lines) - 1:
                    next_line = original_lines[i].strip()
                    if next_line.startswith('name:'):
                        print(f"  ⚠️  Line {i}: Possible duplicate 'name' key")
            
            fixed_lines.append(fixed_line)
        
        # Create fixed content
        fixed_content = '\n'.join(fixed_lines)
        
        # Determine output path
        if output_path is None:
            output_path = str(path.parent / f"{path.stem}_fixed{path.suffix}")
        
        # Write fixed content
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print(f"\n✅ Fixed {issues_fixed} issues")
        print(f"Output written to: {output_path}")
        
        # Validate the fixed file
        print("\nValidating fixed file...")
        import yaml
        try:
            with open(output_path, 'r') as f:
                yaml.safe_load(f)
            print("✅ Fixed file is valid YAML!")
            return True
        except yaml.YAMLError as e:
            print(f"❌ Fixed file still has YAML errors: {e}")
            print("\nThe file may need manual editing to fix structural issues.")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_toc_yaml.py <path-to-TOC.yml> [output-path]")
        print("\nExample:")
        print("  python scripts/fix_toc_yaml.py work/tmp/azure-aks-docs/articles/aks/TOC.yml")
        print("  python scripts/fix_toc_yaml.py input.yml output.yml")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = fix_toc_yaml(input_file, output_file)
    sys.exit(0 if success else 1) 