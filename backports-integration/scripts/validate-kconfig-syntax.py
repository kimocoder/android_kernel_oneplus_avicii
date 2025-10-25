#!/usr/bin/env python3
"""
Simple Kconfig syntax validator for backports integration
"""

import re
import sys
from pathlib import Path

def validate_kconfig_file(filepath):
    """Validate basic Kconfig syntax"""
    errors = []
    warnings = []
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Track if/endif pairs
    if_stack = []
    choice_stack = []
    in_help = False
    
    for line_num, line in enumerate(lines, 1):
        original_line = line
        line = line.strip()
        
        # Skip comments and empty lines
        if not line or line.startswith('#'):
            continue
        
        # Check if we're entering help text
        if line == 'help':
            in_help = True
            continue
        
        # Check if we're in help text (indented lines after help)
        if in_help and original_line.startswith('\t'):
            continue  # Skip help text lines
        elif in_help and not original_line.startswith('\t'):
            in_help = False  # End of help text
        
        # Check for if statements (but not in help text)
        if not in_help:
            if_match = re.match(r'^if\s+(\w+)', line)
            if if_match:
                if_stack.append((line_num, if_match.group(1)))
        
        # Check for endif statements (regardless of help text state)
        if line.startswith('endif'):
            if not if_stack:
                errors.append(f"Line {line_num}: 'endif' without matching 'if'")
            else:
                if_stack.pop()
        
        # Check for choice statements
        elif line.startswith('choice'):
            choice_stack.append(line_num)
        
        # Check for endchoice statements
        elif line.startswith('endchoice'):
            if not choice_stack:
                errors.append(f"Line {line_num}: 'endchoice' without matching 'choice'")
            else:
                choice_stack.pop()
        
        # Check for config statements
        elif line.startswith('config ') or line.startswith('menuconfig '):
            config_match = re.match(r'^(menu)?config\s+(\w+)', line)
            if not config_match:
                errors.append(f"Line {line_num}: Invalid config syntax: {line}")
        
        # Check for depends statements
        elif line.startswith('depends on'):
            depends_match = re.match(r'^depends on\s+(.+)', line)
            if not depends_match:
                errors.append(f"Line {line_num}: Invalid depends syntax: {line}")
        
        # Check for select statements
        elif line.startswith('select '):
            select_match = re.match(r'^select\s+(\w+)', line)
            if not select_match:
                errors.append(f"Line {line_num}: Invalid select syntax: {line}")
        
        # Check for help statements
        elif line == 'help':
            # Help should be followed by indented text
            continue
        
        # Check for bool/tristate statements
        elif line in ['bool', 'tristate', 'string', 'int', 'hex']:
            continue
        elif re.match(r'^(bool|tristate|string|int|hex)\s+".*"', line):
            continue
        
        # Check for default statements
        elif line.startswith('default '):
            continue
        
        # Check for prompt statements
        elif line.startswith('prompt '):
            continue
        
        # Skip if we're in help text
        elif in_help:
            continue
        
        # Unknown line type - might be an error
        else:
            if not re.match(r'^[A-Z_]+=', line):  # Not a variable assignment
                warnings.append(f"Line {line_num}: Unknown line type: {line}")
    
    # Check for unmatched if/endif
    if if_stack:
        for line_num, if_name in if_stack:
            errors.append(f"Line {line_num}: Unmatched 'if {if_name}' (missing endif)")
    
    # Check for unmatched choice/endchoice
    if choice_stack:
        for line_num in choice_stack:
            errors.append(f"Line {line_num}: Unmatched 'choice' (missing endchoice)")
    
    return errors, warnings

def main():
    """Main validation function"""
    kconfig_file = Path(__file__).parent.parent / "Kconfig"
    
    if not kconfig_file.exists():
        print(f"Error: {kconfig_file} not found")
        return 1
    
    print(f"Validating {kconfig_file}...")
    errors, warnings = validate_kconfig_file(kconfig_file)
    
    if errors:
        print(f"\n❌ Found {len(errors)} errors:")
        for error in errors:
            print(f"  {error}")
    
    if warnings:
        print(f"\n⚠️  Found {len(warnings)} warnings:")
        for warning in warnings:
            print(f"  {warning}")
    
    if not errors and not warnings:
        print("✅ Kconfig syntax validation passed!")
        return 0
    elif not errors:
        print("✅ Kconfig syntax validation passed with warnings")
        return 0
    else:
        print("❌ Kconfig syntax validation failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())