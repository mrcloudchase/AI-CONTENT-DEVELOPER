#!/usr/bin/env python3
"""
Validate TOC.yml file syntax
"""
import sys
import yaml
from pathlib import Path


def validate_toc(toc_path: str):
    """Validate a TOC.yml file"""
    path = Path(toc_path)
    
    if not path.exists():
        print(f"❌ Error: File not found: {toc_path}")
        return False
    
    print(f"Validating: {path}")
    print(f"File size: {path.stat().st_size} bytes")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        print(f"Lines: {len(lines)}")
        
        # Try to parse YAML
        toc_data = yaml.safe_load(content)
        
        if not isinstance(toc_data, list):
            print(f"❌ Error: TOC root should be a list, got {type(toc_data)}")
            return False
        
        print(f"✅ Valid YAML with {len(toc_data)} top-level entries")
        
        # Count total entries
        total_entries = count_entries(toc_data)
        print(f"Total entries (including nested): {total_entries}")
        
        # Check for common issues
        issues = check_common_issues(toc_data)
        if issues:
            print("\n⚠️  Potential issues found:")
            for issue in issues:
                print(f"  - {issue}")
        
        return True
        
    except yaml.YAMLError as e:
        print(f"\n❌ YAML Error: {e}")
        
        # Try to show context
        if hasattr(e, 'problem_mark'):
            mark = e.problem_mark
            if mark.line < len(lines):
                print(f"\nContext around line {mark.line + 1}:")
                start = max(0, mark.line - 2)
                end = min(len(lines), mark.line + 3)
                for i in range(start, end):
                    prefix = ">>> " if i == mark.line else "    "
                    print(f"{prefix}{i+1}: {lines[i]}")
        
        return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def count_entries(items, level=0):
    """Recursively count all entries"""
    count = 0
    for item in items:
        if isinstance(item, dict):
            count += 1
            if 'items' in item and isinstance(item['items'], list):
                count += count_entries(item['items'], level + 1)
    return count


def check_common_issues(items, path=""):
    """Check for common TOC issues"""
    issues = []
    
    for i, item in enumerate(items):
        current_path = f"{path}[{i}]"
        
        if not isinstance(item, dict):
            issues.append(f"{current_path}: Entry should be a dictionary")
            continue
        
        # Check required fields
        if 'name' not in item and 'href' not in item:
            issues.append(f"{current_path}: Entry missing both 'name' and 'href'")
        
        # Check for duplicate keys (common YAML error)
        if 'href' in item and isinstance(item.get('href'), dict):
            issues.append(f"{current_path}: 'href' appears to be a dict (possible duplicate key)")
        
        # Recursively check items
        if 'items' in item:
            if not isinstance(item['items'], list):
                issues.append(f"{current_path}: 'items' should be a list")
            else:
                issues.extend(check_common_issues(item['items'], f"{current_path}.items"))
    
    return issues


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_toc.py <path-to-TOC.yml>")
        print("\nExample:")
        print("  python scripts/validate_toc.py work/tmp/azure-aks-docs/articles/aks/TOC.yml")
        sys.exit(1)
    
    toc_file = sys.argv[1]
    success = validate_toc(toc_file)
    
    sys.exit(0 if success else 1) 