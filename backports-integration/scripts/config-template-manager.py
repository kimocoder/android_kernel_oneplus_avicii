#!/usr/bin/env python3
"""
Wireless Configuration Template Manager

This script manages wireless configuration templates for different use cases
and provides tools for template selection, customization, and validation.
"""

import os
import sys
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class ConfigTemplate:
    """Configuration template information"""
    name: str
    filename: str
    description: str
    use_case: str
    features: List[str]
    warnings: List[str]
    requirements: List[str]
    regulatory_notes: List[str]

class ConfigTemplateManager:
    """Wireless configuration template manager"""
    
    def __init__(self, kernel_root: str = "."):
        """Initialize template manager"""
        self.kernel_root = Path(kernel_root).resolve()
        self.backports_dir = self.kernel_root / "backports-integration"
        self.configs_dir = self.backports_dir / "configs"
        self.scripts_dir = self.backports_dir / "scripts"
        
        # Load template database
        self.templates = self._load_template_database()
    
    def _load_template_database(self) -> Dict[str, ConfigTemplate]:
        """Load configuration template database"""
        return {
            "laptop-standard": ConfigTemplate(
                name="Laptop/Desktop Standard",
                filename="laptop-standard.config",
                description="Standard wireless configuration for laptops and desktop systems",
                use_case="everyday_use",
                features=[
                    "Standard wireless connectivity",
                    "Power management optimization",
                    "Enterprise security support",
                    "Multiple driver support (ath11k, ath10k, iwlwifi)",
                    "Regulatory compliance"
                ],
                warnings=[],
                requirements=[
                    "Modern wireless chipset",
                    "Kernel 4.19 or newer",
                    "Power management support"
                ],
                regulatory_notes=[
                    "Complies with standard regulatory requirements",
                    "No monitor mode or injection capabilities"
                ]
            ),
            
            "security-research-advanced": ConfigTemplate(
                name="Advanced Security Research",
                filename="security-research-advanced.config",
                description="Comprehensive security research configuration with monitor mode and injection",
                use_case="security_research",
                features=[
                    "Monitor mode with radiotap headers",
                    "Packet injection with full control",
                    "Multiple driver support for research",
                    "Spectral scan capabilities",
                    "Advanced debugging and tracing",
                    "Mesh networking support"
                ],
                warnings=[
                    "SECURITY WARNING: Enables security-sensitive features",
                    "REGULATORY WARNING: Monitor mode and injection may be restricted",
                    "Only use in isolated test environments",
                    "Requires proper authorization and legal compliance"
                ],
                requirements=[
                    "Compatible wireless chipset (ath11k, ath10k, ath9k, rt2x00)",
                    "Kernel debugging support",
                    "Root privileges for operation",
                    "Isolated test environment"
                ],
                regulatory_notes=[
                    "Monitor mode requires authorization in many jurisdictions",
                    "Packet injection may be prohibited in some regions",
                    "Ensure compliance with local regulations",
                    "Use only in authorized test environments"
                ]
            ),
            
            "mesh-networking": ConfigTemplate(
                name="Mesh Networking",
                filename="mesh-networking.config",
                description="802.11s mesh networking with advanced mesh features",
                use_case="mesh_networking",
                features=[
                    "802.11s mesh networking",
                    "Multi-hop routing",
                    "Mesh security with SAE",
                    "Power save for mesh nodes",
                    "Quality of Service support",
                    "Advanced path selection"
                ],
                warnings=[],
                requirements=[
                    "Mesh-capable wireless chipset",
                    "Routing and bridging support",
                    "Quality of Service kernel support"
                ],
                regulatory_notes=[
                    "Mesh networking generally allowed in most regions",
                    "Power limits and channel restrictions apply",
                    "Check local regulations for outdoor deployments"
                ]
            ),
            
            "enterprise-wireless": ConfigTemplate(
                name="Enterprise Wireless",
                filename="enterprise-wireless.config",
                description="Enterprise-grade wireless with advanced security and management",
                use_case="enterprise",
                features=[
                    "WPA3 Enterprise support",
                    "802.1X authentication",
                    "Advanced security features",
                    "Enterprise power management",
                    "SNMP monitoring support",
                    "Quality of Service",
                    "VLAN support"
                ],
                warnings=[
                    "Monitor mode and injection disabled for security",
                    "Requires enterprise infrastructure"
                ],
                requirements=[
                    "Enterprise wireless infrastructure",
                    "802.1X authentication server",
                    "Network management system",
                    "Quality of Service support"
                ],
                regulatory_notes=[
                    "Strict regulatory compliance enforced",
                    "Enterprise compliance features enabled",
                    "Suitable for corporate environments"
                ]
            ),
            
            "android-mobile": ConfigTemplate(
                name="Android Mobile",
                filename="android-mobile.config",
                description="Android mobile device configuration with power optimization",
                use_case="android_mobile",
                features=[
                    "Android framework integration",
                    "Mobile power optimization",
                    "Android security integration",
                    "Vendor driver compatibility",
                    "Battery optimization",
                    "Android wakelock support"
                ],
                warnings=[
                    "Monitor mode and injection disabled (Android security policy)",
                    "Requires Android kernel features"
                ],
                requirements=[
                    "Android kernel 4.19 or newer",
                    "Android framework support",
                    "Mobile wireless chipset",
                    "Power management support"
                ],
                regulatory_notes=[
                    "Android security policies enforced",
                    "Regulatory compliance for mobile devices",
                    "Location permission integration"
                ]
            ),
            
            "embedded-iot": ConfigTemplate(
                name="Embedded IoT",
                filename="embedded-iot.config",
                description="Minimal configuration for embedded IoT devices",
                use_case="embedded_iot",
                features=[
                    "Minimal resource usage",
                    "Ultra-low power consumption",
                    "Essential wireless features only",
                    "Optimized for constrained devices",
                    "Basic security features"
                ],
                warnings=[
                    "Limited feature set for resource constraints",
                    "No debugging or advanced features"
                ],
                requirements=[
                    "Embedded wireless chipset",
                    "Minimal kernel configuration",
                    "Power management support"
                ],
                regulatory_notes=[
                    "Basic regulatory compliance",
                    "Suitable for IoT deployments",
                    "Check regional IoT regulations"
                ]
            ),
            
            "monitor-only": ConfigTemplate(
                name="Monitor Mode Only",
                filename="monitor-only.config",
                description="Passive monitoring configuration without transmission capabilities",
                use_case="monitoring",
                features=[
                    "Monitor mode with radiotap",
                    "Passive packet capture",
                    "Channel switching support",
                    "Spectral scan capabilities",
                    "No transmission capabilities",
                    "Enhanced monitoring features"
                ],
                warnings=[
                    "REGULATORY NOTE: Monitor mode may require authorization",
                    "No transmission capabilities (receive only)",
                    "Ensure compliance with local regulations"
                ],
                requirements=[
                    "Monitor-capable wireless chipset",
                    "Packet capture applications",
                    "Debugging support"
                ],
                regulatory_notes=[
                    "Monitor mode authorization may be required",
                    "Passive monitoring generally more permissive",
                    "Check local regulations for monitoring activities",
                    "No transmission reduces regulatory concerns"
                ]
            ),
            
            "usb-adapters": ConfigTemplate(
                name="USB Wireless Adapters",
                filename="usb-adapters.config",
                description="Comprehensive USB wireless adapter support with RTW88 and MT76 drivers",
                use_case="usb_adapters",
                features=[
                    "RTW88 Realtek USB adapter support",
                    "MT76 MediaTek USB adapter support",
                    "Legacy RT2X00 USB adapter support",
                    "Monitor mode and packet injection",
                    "Mesh networking capabilities",
                    "Advanced debugging and analysis tools"
                ],
                warnings=[
                    "SECURITY WARNING: Enables monitor mode and injection",
                    "REGULATORY WARNING: Check local regulations for USB adapters",
                    "USB adapter performance may vary by chipset",
                    "Some features may require specific firmware versions"
                ],
                requirements=[
                    "USB wireless adapter with supported chipset",
                    "USB 2.0 or USB 3.0 port",
                    "Compatible firmware files",
                    "Root privileges for monitor mode operations"
                ],
                regulatory_notes=[
                    "USB adapters subject to same regulatory restrictions",
                    "Monitor mode and injection authorization may be required",
                    "Check adapter certification for your region",
                    "External antennas may have additional restrictions"
                ]
            ),
            
            "usb-adapters": ConfigTemplate(
                name="USB Wireless Adapters",
                filename="usb-adapters.config",
                description="Comprehensive USB wireless adapter support with RTW88 and MT76 drivers",
                use_case="usb_adapters",
                features=[
                    "RTW88 Realtek USB driver support",
                    "MT76 MediaTek USB driver support",
                    "Legacy rt2x00 USB driver support",
                    "Monitor mode and packet injection",
                    "Wi-Fi 6 support (MT7921U)",
                    "Comprehensive USB adapter coverage"
                ],
                warnings=[
                    "Monitor mode and injection may require authorization",
                    "USB adapter performance varies by chipset",
                    "Ensure proper USB power supply"
                ],
                requirements=[
                    "USB wireless adapter with supported chipset",
                    "USB 2.0 or higher port",
                    "Adequate power supply for USB adapter",
                    "Linux USB subsystem support"
                ],
                regulatory_notes=[
                    "Monitor mode and injection subject to local regulations",
                    "USB adapters generally easier to authorize than built-in",
                    "Check adapter specifications for regulatory compliance",
                    "Some adapters may have region-specific firmware"
                ]
            )
        }
    
    def list_templates(self) -> None:
        """List available configuration templates"""
        print("Available Wireless Configuration Templates:")
        print("=" * 50)
        
        for template_id, template in self.templates.items():
            print(f"\n{template.name} ({template_id})")
            print(f"  Description: {template.description}")
            print(f"  Use Case: {template.use_case}")
            print(f"  File: {template.filename}")
            
            if template.warnings:
                print("  Warnings:")
                for warning in template.warnings:
                    print(f"    ⚠️  {warning}")
    
    def show_template_details(self, template_id: str) -> None:
        """Show detailed information about a template"""
        if template_id not in self.templates:
            print(f"Error: Template '{template_id}' not found")
            return
        
        template = self.templates[template_id]
        
        print(f"Configuration Template: {template.name}")
        print("=" * 60)
        print(f"ID: {template_id}")
        print(f"File: {template.filename}")
        print(f"Use Case: {template.use_case}")
        print(f"Description: {template.description}")
        
        print("\nFeatures:")
        for feature in template.features:
            print(f"  ✓ {feature}")
        
        if template.warnings:
            print("\nWarnings:")
            for warning in template.warnings:
                print(f"  ⚠️  {warning}")
        
        print("\nRequirements:")
        for requirement in template.requirements:
            print(f"  • {requirement}")
        
        print("\nRegulatory Notes:")
        for note in template.regulatory_notes:
            print(f"  📋 {note}")
    
    def apply_template(self, template_id: str, output_file: Optional[str] = None) -> str:
        """Apply a configuration template"""
        if template_id not in self.templates:
            raise ValueError(f"Template '{template_id}' not found")
        
        template = self.templates[template_id]
        source_file = self.configs_dir / template.filename
        
        if not source_file.exists():
            raise FileNotFoundError(f"Template file not found: {source_file}")
        
        # Determine output file
        if output_file:
            output_path = Path(output_file)
        else:
            output_path = self.kernel_root / ".config"
        
        # Copy template to output
        shutil.copy2(source_file, output_path)
        
        print(f"✅ Applied template '{template.name}' to {output_path}")
        
        # Show warnings if any
        if template.warnings:
            print("\n⚠️  Important Warnings:")
            for warning in template.warnings:
                print(f"   {warning}")
        
        # Show regulatory notes
        if template.regulatory_notes:
            print("\n📋 Regulatory Notes:")
            for note in template.regulatory_notes:
                print(f"   {note}")
        
        return str(output_path)
    
    def customize_template(self, template_id: str, customizations: Dict[str, str]) -> str:
        """Customize a template with specific options"""
        if template_id not in self.templates:
            raise ValueError(f"Template '{template_id}' not found")
        
        template = self.templates[template_id]
        source_file = self.configs_dir / template.filename
        
        if not source_file.exists():
            raise FileNotFoundError(f"Template file not found: {source_file}")
        
        # Read template content
        with open(source_file, 'r') as f:
            content = f.read()
        
        # Apply customizations
        for option, value in customizations.items():
            # Handle different value types
            if value.lower() in ['y', 'yes', 'true', 'on']:
                new_line = f"CONFIG_{option}=y"
                old_patterns = [
                    f"# CONFIG_{option} is not set",
                    f"CONFIG_{option}=n",
                    f"CONFIG_{option}=m"
                ]
            elif value.lower() in ['n', 'no', 'false', 'off']:
                new_line = f"# CONFIG_{option} is not set"
                old_patterns = [
                    f"CONFIG_{option}=y",
                    f"CONFIG_{option}=m"
                ]
            elif value.lower() in ['m', 'module']:
                new_line = f"CONFIG_{option}=m"
                old_patterns = [
                    f"# CONFIG_{option} is not set",
                    f"CONFIG_{option}=y",
                    f"CONFIG_{option}=n"
                ]
            else:
                new_line = f"CONFIG_{option}={value}"
                old_patterns = [
                    f"CONFIG_{option}=.*"
                ]
            
            # Replace existing configuration
            import re
            for pattern in old_patterns:
                content = re.sub(pattern, new_line, content)
            
            # If option not found, add it
            if f"CONFIG_{option}" not in content:
                content += f"\n{new_line}\n"
        
        # Generate customized filename
        custom_filename = f"{template_id}-custom.config"
        custom_path = self.configs_dir / custom_filename
        
        # Write customized template
        with open(custom_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Created customized template: {custom_path}")
        return str(custom_path)
    
    def validate_template(self, template_file: str) -> Dict[str, any]:
        """Validate a configuration template"""
        template_path = Path(template_file)
        
        if not template_path.exists():
            return {"valid": False, "errors": [f"Template file not found: {template_file}"]}
        
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "info": {
                "total_options": 0,
                "enabled_options": 0,
                "disabled_options": 0,
                "module_options": 0
            }
        }
        
        try:
            with open(template_path, 'r') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    if line.startswith('# CONFIG_') and 'is not set' in line:
                        result["info"]["disabled_options"] += 1
                        result["info"]["total_options"] += 1
                    continue
                
                # Check CONFIG lines
                if line.startswith('CONFIG_'):
                    result["info"]["total_options"] += 1
                    
                    if '=y' in line:
                        result["info"]["enabled_options"] += 1
                    elif '=m' in line:
                        result["info"]["module_options"] += 1
                    elif '=n' in line:
                        result["info"]["disabled_options"] += 1
                    
                    # Validate format
                    if '=' not in line:
                        result["errors"].append(f"Line {line_num}: Invalid CONFIG format: {line}")
                        result["valid"] = False
            
            # Check for required options
            required_options = [
                "CONFIG_BACKPORTS",
                "CONFIG_BACKPORTS_CFG80211",
                "CONFIG_BACKPORTS_MAC80211"
            ]
            
            for option in required_options:
                if option not in content:
                    result["warnings"].append(f"Missing recommended option: {option}")
            
            # Check for conflicting options
            conflicting_pairs = [
                ("CONFIG_CFG80211=", "CONFIG_BACKPORTS_CFG80211="),
                ("CONFIG_MAC80211=", "CONFIG_BACKPORTS_MAC80211=")
            ]
            
            for native, backports in conflicting_pairs:
                if native in content and backports in content:
                    if not (f"# {native}" in content):  # Not disabled
                        result["warnings"].append(f"Potential conflict: {native} and {backports} both enabled")
        
        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Error reading template: {e}")
        
        return result
    
    def generate_template_report(self, output_file: Optional[str] = None) -> str:
        """Generate comprehensive template report"""
        report_lines = []
        report_lines.append("Wireless Configuration Templates Report")
        report_lines.append("=" * 50)
        report_lines.append(f"Generated: {__import__('time').ctime()}")
        report_lines.append("")
        
        # Template summary
        report_lines.append("Template Summary:")
        report_lines.append(f"  Total templates: {len(self.templates)}")
        
        use_cases = {}
        for template in self.templates.values():
            use_case = template.use_case
            if use_case not in use_cases:
                use_cases[use_case] = 0
            use_cases[use_case] += 1
        
        report_lines.append("  Templates by use case:")
        for use_case, count in use_cases.items():
            report_lines.append(f"    {use_case}: {count}")
        
        report_lines.append("")
        
        # Template details
        for template_id, template in self.templates.items():
            report_lines.append(f"Template: {template.name} ({template_id})")
            report_lines.append("-" * 40)
            report_lines.append(f"File: {template.filename}")
            report_lines.append(f"Use Case: {template.use_case}")
            report_lines.append(f"Description: {template.description}")
            
            # Validate template
            template_file = self.configs_dir / template.filename
            if template_file.exists():
                validation = self.validate_template(str(template_file))
                
                if validation["valid"]:
                    report_lines.append("Status: ✅ Valid")
                else:
                    report_lines.append("Status: ❌ Invalid")
                
                info = validation["info"]
                report_lines.append(f"Options: {info['total_options']} total, "
                                  f"{info['enabled_options']} enabled, "
                                  f"{info['module_options']} modules, "
                                  f"{info['disabled_options']} disabled")
                
                if validation["errors"]:
                    report_lines.append("Errors:")
                    for error in validation["errors"]:
                        report_lines.append(f"  - {error}")
                
                if validation["warnings"]:
                    report_lines.append("Warnings:")
                    for warning in validation["warnings"]:
                        report_lines.append(f"  - {warning}")
            else:
                report_lines.append("Status: ❌ File not found")
            
            report_lines.append("")
        
        report_content = "\n".join(report_lines)
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_content)
            print(f"Template report saved to: {output_file}")
        
        return report_content

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Wireless Configuration Template Manager")
    parser.add_argument("command", choices=[
        "list", "show", "apply", "customize", "validate", "report"
    ], help="Template management command")
    
    parser.add_argument("template", nargs="?", help="Template ID")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--customize", help="Customization options (JSON format)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    manager = ConfigTemplateManager()
    
    if args.command == "list":
        manager.list_templates()
    
    elif args.command == "show":
        if not args.template:
            print("Error: Template ID required")
            return 1
        
        manager.show_template_details(args.template)
    
    elif args.command == "apply":
        if not args.template:
            print("Error: Template ID required")
            return 1
        
        try:
            output_file = manager.apply_template(args.template, args.output)
            print(f"\nTemplate applied successfully to: {output_file}")
        except Exception as e:
            print(f"Error applying template: {e}")
            return 1
    
    elif args.command == "customize":
        if not args.template:
            print("Error: Template ID required")
            return 1
        
        if not args.customize:
            print("Error: Customization options required (JSON format)")
            return 1
        
        try:
            customizations = json.loads(args.customize)
            custom_file = manager.customize_template(args.template, customizations)
            print(f"Customized template created: {custom_file}")
        except Exception as e:
            print(f"Error customizing template: {e}")
            return 1
    
    elif args.command == "validate":
        if not args.template:
            print("Error: Template file required")
            return 1
        
        result = manager.validate_template(args.template)
        
        if result["valid"]:
            print("✅ Template validation passed")
        else:
            print("❌ Template validation failed")
        
        if args.verbose:
            info = result["info"]
            print(f"\nTemplate Statistics:")
            print(f"  Total options: {info['total_options']}")
            print(f"  Enabled: {info['enabled_options']}")
            print(f"  Modules: {info['module_options']}")
            print(f"  Disabled: {info['disabled_options']}")
        
        if result["errors"]:
            print("\nErrors:")
            for error in result["errors"]:
                print(f"  - {error}")
        
        if result["warnings"]:
            print("\nWarnings:")
            for warning in result["warnings"]:
                print(f"  - {warning}")
        
        return 0 if result["valid"] else 1
    
    elif args.command == "report":
        report = manager.generate_template_report(args.output)
        if not args.output:
            print(report)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())