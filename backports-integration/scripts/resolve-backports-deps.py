#!/usr/bin/env python3
"""
Backports Dependency Resolution Helper

This script provides automatic dependency resolution for backports configuration,
including interactive resolution for complex conflicts and configuration templates
for common use cases.
"""

import os
import sys
import re
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
import argparse

class BackportsDependencyResolver:
    """Resolves backports dependencies and provides configuration assistance"""
    
    def __init__(self, kernel_root: str = "."):
        self.kernel_root = Path(kernel_root).resolve()
        self.config_file = self.kernel_root / ".config"
        self.backports_dir = self.kernel_root / "backports-integration"
        
        # Configuration templates
        self.templates = {
            'basic': {
                'name': 'Basic Backports',
                'description': 'Basic cfg80211 and mac80211 support',
                'config': {
                    'CONFIG_BACKPORTS': 'y',
                    'CONFIG_BACKPORTS_CFG80211': 'm',
                    'CONFIG_BACKPORTS_MAC80211': 'm',
                    'CONFIG_BACKPORTS_MAC80211_RC_MINSTREL': 'y'
                },
                'required_kernel_features': [
                    'CONFIG_MODULES=y',
                    'CONFIG_NET=y',
                    'CONFIG_CRYPTO=y'
                ],
                'conflicts': [
                    'CONFIG_CFG80211',
                    'CONFIG_MAC80211'
                ]
            },
            'monitor': {
                'name': 'Monitor Mode Support',
                'description': 'Backports with monitor mode for packet capture',
                'config': {
                    'CONFIG_BACKPORTS': 'y',
                    'CONFIG_BACKPORTS_CFG80211': 'm',
                    'CONFIG_BACKPORTS_MAC80211': 'm',
                    'CONFIG_BACKPORTS_MAC80211_RC_MINSTREL': 'y',
                    'CONFIG_BACKPORTS_MAC80211_DEBUGFS': 'y',
                    'CONFIG_BACKPORTS_MONITOR_MODE': 'y'
                },
                'required_kernel_features': [
                    'CONFIG_MODULES=y',
                    'CONFIG_NET=y',
                    'CONFIG_CRYPTO=y',
                    'CONFIG_PACKET=y',
                    'CONFIG_DEBUG_FS=y'
                ],
                'conflicts': [
                    'CONFIG_CFG80211',
                    'CONFIG_MAC80211'
                ]
            },
            'injection': {
                'name': 'Frame Injection Support',
                'description': 'Full backports with monitor mode and frame injection',
                'config': {
                    'CONFIG_BACKPORTS': 'y',
                    'CONFIG_BACKPORTS_CFG80211': 'm',
                    'CONFIG_BACKPORTS_MAC80211': 'm',
                    'CONFIG_BACKPORTS_MAC80211_RC_MINSTREL': 'y',
                    'CONFIG_BACKPORTS_MAC80211_DEBUGFS': 'y',
                    'CONFIG_BACKPORTS_MONITOR_MODE': 'y',
                    'CONFIG_BACKPORTS_FRAME_INJECTION': 'y',
                    'CONFIG_BACKPORTS_DEBUG': 'y'
                },
                'required_kernel_features': [
                    'CONFIG_MODULES=y',
                    'CONFIG_NET=y',
                    'CONFIG_CRYPTO=y',
                    'CONFIG_PACKET=y',
                    'CONFIG_PACKET_MMAP=y',
                    'CONFIG_DEBUG_FS=y'
                ],
                'conflicts': [
                    'CONFIG_CFG80211',
                    'CONFIG_MAC80211'
                ]
            },
            'android': {
                'name': 'Android Optimized',
                'description': 'Backports optimized for Android devices',
                'config': {
                    'CONFIG_BACKPORTS': 'y',
                    'CONFIG_BACKPORTS_CFG80211': 'm',
                    'CONFIG_BACKPORTS_MAC80211': 'm',
                    'CONFIG_BACKPORTS_MAC80211_RC_MINSTREL': 'y',
                    'CONFIG_BACKPORTS_MONITOR_MODE': 'y',
                    'CONFIG_BACKPORTS_FRAME_INJECTION': 'y',
                    'CONFIG_BACKPORTS_ANDROID': 'y'
                },
                'required_kernel_features': [
                    'CONFIG_MODULES=y',
                    'CONFIG_NET=y',
                    'CONFIG_CRYPTO=y',
                    'CONFIG_ANDROID=y',
                    'CONFIG_PACKET=y'
                ],
                'conflicts': [
                    'CONFIG_CFG80211',
                    'CONFIG_MAC80211',
                    'CONFIG_QCACLD',
                    'CONFIG_PRIMA_WLAN'
                ]
            }
        }
        
        # Dependency resolution rules
        self.resolution_rules = {
            'CONFIG_BACKPORTS_CFG80211': {
                'enables': ['CONFIG_BACKPORTS'],
                'requires': ['CONFIG_MODULES', 'CONFIG_NET', 'CONFIG_CRYPTO'],
                'recommends': ['CONFIG_RFKILL', 'CONFIG_WIRELESS_EXT'],
                'disables': ['CONFIG_CFG80211']
            },
            'CONFIG_BACKPORTS_MAC80211': {
                'enables': ['CONFIG_BACKPORTS', 'CONFIG_BACKPORTS_CFG80211'],
                'requires': ['CONFIG_CRYPTO_ARC4', 'CONFIG_CRYPTO_AES', 'CONFIG_CRC32'],
                'recommends': ['CONFIG_LEDS_CLASS'],
                'disables': ['CONFIG_MAC80211']
            },
            'CONFIG_BACKPORTS_MONITOR_MODE': {
                'enables': ['CONFIG_BACKPORTS_MAC80211'],
                'requires': ['CONFIG_PACKET'],
                'recommends': ['CONFIG_DEBUG_FS', 'CONFIG_NETFILTER']
            },
            'CONFIG_BACKPORTS_FRAME_INJECTION': {
                'enables': ['CONFIG_BACKPORTS_MONITOR_MODE'],
                'requires': ['CONFIG_PACKET_MMAP'],
                'security_warning': True
            }
        }
    
    def read_config(self) -> Dict[str, str]:
        """Read current kernel configuration"""
        config = {}
        
        if not self.config_file.exists():
            return config
        
        try:
            with open(self.config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('#') or not line or '=' not in line:
                        continue
                    
                    key, value = line.split('=', 1)
                    config[key] = value
        except Exception as e:
            print(f"Error reading config: {e}")
        
        return config
    
    def write_config(self, config: Dict[str, str]) -> bool:
        """Write configuration to .config file"""
        try:
            # Create backup
            if self.config_file.exists():
                backup_file = self.config_file.with_suffix('.config.backup')
                shutil.copy2(self.config_file, backup_file)
                print(f"Configuration backup created: {backup_file}")
            
            with open(self.config_file, 'w') as f:
                f.write("#\n# Automatically generated configuration\n#\n")
                
                # Write backports configuration first
                backports_configs = {k: v for k, v in config.items() if k.startswith('CONFIG_BACKPORTS')}
                if backports_configs:
                    f.write("\n# Backports configuration\n")
                    for key in sorted(backports_configs.keys()):
                        value = backports_configs[key]
                        if value == 'n':
                            f.write(f"# {key} is not set\n")
                        else:
                            f.write(f"{key}={value}\n")
                
                # Write other configuration
                other_configs = {k: v for k, v in config.items() if not k.startswith('CONFIG_BACKPORTS')}
                if other_configs:
                    f.write("\n# Other configuration\n")
                    for key in sorted(other_configs.keys()):
                        value = other_configs[key]
                        if value == 'n':
                            f.write(f"# {key} is not set\n")
                        else:
                            f.write(f"{key}={value}\n")
            
            return True
        
        except Exception as e:
            print(f"Error writing config: {e}")
            return False
    
    def resolve_dependencies(self, target_config: str, current_config: Dict[str, str]) -> Dict[str, str]:
        """Resolve dependencies for a target configuration"""
        resolved_config = current_config.copy()
        
        if target_config not in self.resolution_rules:
            return resolved_config
        
        rules = self.resolution_rules[target_config]
        
        # Enable required dependencies
        if 'enables' in rules:
            for dep in rules['enables']:
                if dep not in resolved_config or resolved_config[dep] == 'n':
                    resolved_config[dep] = 'y'
                    print(f"  Enabling dependency: {dep}")
        
        # Check and enable required kernel features
        if 'requires' in rules:
            for req in rules['requires']:
                if req not in resolved_config or resolved_config[req] == 'n':
                    resolved_config[req] = 'y'
                    print(f"  Enabling required feature: {req}")
        
        # Recommend optional features
        if 'recommends' in rules:
            for rec in rules['recommends']:
                if rec not in resolved_config or resolved_config[rec] == 'n':
                    print(f"  Recommending optional feature: {rec}")
                    # Don't automatically enable, just inform
        
        # Disable conflicting options
        if 'disables' in rules:
            for conflict in rules['disables']:
                if conflict in resolved_config and resolved_config[conflict] in ['y', 'm']:
                    resolved_config[conflict] = 'n'
                    print(f"  Disabling conflicting option: {conflict}")
        
        # Security warnings
        if rules.get('security_warning'):
            print(f"  ⚠️  WARNING: {target_config} has security implications")
        
        return resolved_config
    
    def apply_template(self, template_name: str) -> bool:
        """Apply a configuration template"""
        if template_name not in self.templates:
            print(f"Error: Template '{template_name}' not found")
            return False
        
        template = self.templates[template_name]
        current_config = self.read_config()
        
        print(f"Applying template: {template['name']}")
        print(f"Description: {template['description']}")
        print()
        
        # Start with template configuration
        new_config = current_config.copy()
        new_config.update(template['config'])
        
        # Resolve dependencies for each backports option
        for option in template['config']:
            if option.startswith('CONFIG_BACKPORTS'):
                print(f"Resolving dependencies for {option}...")
                new_config = self.resolve_dependencies(option, new_config)
        
        # Apply required kernel features
        print("\nApplying required kernel features...")
        for feature in template['required_kernel_features']:
            key, value = feature.split('=')
            new_config[key] = value
            print(f"  Setting {key}={value}")
        
        # Disable conflicting options
        print("\nDisabling conflicting options...")
        for conflict in template['conflicts']:
            if conflict in new_config and new_config[conflict] in ['y', 'm']:
                new_config[conflict] = 'n'
                print(f"  Disabling {conflict}")
        
        # Write configuration
        if self.write_config(new_config):
            print(f"\n✅ Template '{template_name}' applied successfully!")
            print("Run 'make olddefconfig' to finalize configuration.")
            return True
        else:
            print(f"\n❌ Failed to apply template '{template_name}'")
            return False
    
    def interactive_resolution(self) -> bool:
        """Interactive dependency resolution"""
        print("Interactive Backports Configuration")
        print("=" * 40)
        print()
        
        current_config = self.read_config()
        
        # Ask about basic backports
        enable_backports = input("Enable backports? (y/n): ").lower().strip()
        if enable_backports != 'y':
            print("Backports not enabled. Exiting.")
            return True
        
        new_config = current_config.copy()
        new_config['CONFIG_BACKPORTS'] = 'y'
        
        # Ask about cfg80211
        enable_cfg80211 = input("Enable cfg80211 (wireless configuration API)? (y/n): ").lower().strip()
        if enable_cfg80211 == 'y':
            new_config['CONFIG_BACKPORTS_CFG80211'] = 'm'
            new_config = self.resolve_dependencies('CONFIG_BACKPORTS_CFG80211', new_config)
        
        # Ask about mac80211
        if enable_cfg80211 == 'y':
            enable_mac80211 = input("Enable mac80211 (networking stack)? (y/n): ").lower().strip()
            if enable_mac80211 == 'y':
                new_config['CONFIG_BACKPORTS_MAC80211'] = 'm'
                new_config = self.resolve_dependencies('CONFIG_BACKPORTS_MAC80211', new_config)
                
                # Ask about monitor mode
                enable_monitor = input("Enable monitor mode support? (y/n): ").lower().strip()
                if enable_monitor == 'y':
                    new_config['CONFIG_BACKPORTS_MONITOR_MODE'] = 'y'
                    new_config = self.resolve_dependencies('CONFIG_BACKPORTS_MONITOR_MODE', new_config)
                    
                    # Ask about frame injection
                    enable_injection = input("Enable frame injection (security sensitive)? (y/n): ").lower().strip()
                    if enable_injection == 'y':
                        new_config['CONFIG_BACKPORTS_FRAME_INJECTION'] = 'y'
                        new_config = self.resolve_dependencies('CONFIG_BACKPORTS_FRAME_INJECTION', new_config)
        
        # Ask about Android support
        if 'CONFIG_ANDROID' in current_config and current_config['CONFIG_ANDROID'] == 'y':
            enable_android = input("Enable Android-specific adaptations? (y/n): ").lower().strip()
            if enable_android == 'y':
                new_config['CONFIG_BACKPORTS_ANDROID'] = 'y'
        
        # Show configuration summary
        print("\nConfiguration Summary:")
        print("=" * 30)
        backports_options = {k: v for k, v in new_config.items() if k.startswith('CONFIG_BACKPORTS')}
        for option, value in sorted(backports_options.items()):
            print(f"  {option}: {value}")
        
        # Confirm and apply
        print()
        apply_config = input("Apply this configuration? (y/n): ").lower().strip()
        if apply_config == 'y':
            if self.write_config(new_config):
                print("\n✅ Configuration applied successfully!")
                print("Run 'make olddefconfig' to finalize configuration.")
                return True
            else:
                print("\n❌ Failed to apply configuration")
                return False
        else:
            print("Configuration not applied.")
            return True
    
    def list_templates(self):
        """List available configuration templates"""
        print("Available Configuration Templates:")
        print("=" * 40)
        print()
        
        for name, template in self.templates.items():
            print(f"Template: {name}")
            print(f"  Name: {template['name']}")
            print(f"  Description: {template['description']}")
            print(f"  Options: {len(template['config'])} configuration options")
            print(f"  Requirements: {len(template['required_kernel_features'])} kernel features")
            print()
    
    def validate_template(self, template_name: str) -> bool:
        """Validate if a template can be applied"""
        if template_name not in self.templates:
            print(f"Error: Template '{template_name}' not found")
            return False
        
        template = self.templates[template_name]
        current_config = self.read_config()
        
        print(f"Validating template: {template['name']}")
        print("=" * 40)
        
        issues = []
        
        # Check required kernel features
        for feature in template['required_kernel_features']:
            key, expected_value = feature.split('=')
            current_value = current_config.get(key, 'n')
            
            if current_value != expected_value:
                issues.append(f"Required feature {key} is {current_value}, expected {expected_value}")
        
        # Check conflicts
        for conflict in template['conflicts']:
            if current_config.get(conflict) in ['y', 'm']:
                issues.append(f"Conflicting option {conflict} is enabled")
        
        if issues:
            print("❌ Template validation failed:")
            for issue in issues:
                print(f"  - {issue}")
            print("\nRecommendations:")
            print("  - Run interactive resolution to fix issues")
            print("  - Manually adjust configuration")
            return False
        else:
            print("✅ Template validation passed!")
            print("Template can be applied safely.")
            return True
    
    def create_custom_template(self, name: str) -> bool:
        """Create a custom template from current configuration"""
        current_config = self.read_config()
        
        # Extract backports configuration
        backports_config = {k: v for k, v in current_config.items() if k.startswith('CONFIG_BACKPORTS')}
        
        if not backports_config:
            print("No backports configuration found in current config")
            return False
        
        template_file = self.backports_dir / "configs" / f"{name}.config"
        
        try:
            with open(template_file, 'w') as f:
                f.write(f"#\n# Custom Backports Configuration: {name}\n")
                f.write(f"# Generated from current kernel configuration\n#\n\n")
                
                for key in sorted(backports_config.keys()):
                    value = backports_config[key]
                    if value == 'n':
                        f.write(f"# {key} is not set\n")
                    else:
                        f.write(f"{key}={value}\n")
            
            print(f"✅ Custom template created: {template_file}")
            return True
        
        except Exception as e:
            print(f"❌ Failed to create template: {e}")
            return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Backports dependency resolution helper')
    parser.add_argument('--kernel-root', default='.', help='Path to kernel source root')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Template commands
    template_parser = subparsers.add_parser('template', help='Apply configuration template')
    template_parser.add_argument('name', help='Template name')
    
    list_parser = subparsers.add_parser('list', help='List available templates')
    
    validate_parser = subparsers.add_parser('validate', help='Validate template')
    validate_parser.add_argument('name', help='Template name')
    
    interactive_parser = subparsers.add_parser('interactive', help='Interactive configuration')
    
    custom_parser = subparsers.add_parser('create-template', help='Create custom template')
    custom_parser.add_argument('name', help='Template name')
    
    args = parser.parse_args()
    
    resolver = BackportsDependencyResolver(args.kernel_root)
    
    if args.command == 'template':
        return 0 if resolver.apply_template(args.name) else 1
    elif args.command == 'list':
        resolver.list_templates()
        return 0
    elif args.command == 'validate':
        return 0 if resolver.validate_template(args.name) else 1
    elif args.command == 'interactive':
        return 0 if resolver.interactive_resolution() else 1
    elif args.command == 'create-template':
        return 0 if resolver.create_custom_template(args.name) else 1
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())