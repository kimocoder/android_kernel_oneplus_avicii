#!/usr/bin/env python3
"""
ath11k Configuration Generator

This script generates optimized configurations for different ath11k use cases
including monitor mode, security research, and enterprise deployment.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional

# Add the scripts directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from ath11k_integration import Ath11kIntegration, Ath11kChipset
except ImportError:
    print("Warning: Could not import ath11k_integration module")
    # Create minimal fallback
    class Ath11kIntegration:
        def __init__(self): pass
        def generate_ath11k_config(self, chipsets): return {}
        def create_monitor_mode_config(self): return {}
        def create_packet_injection_config(self): return {}
        def create_mesh_networking_config(self): return {}
    class Ath11kChipset:
        QCA6390 = "QCA6390"
        QCA6490 = "QCA6490"
        WCN6855 = "WCN6855"
        QCN9074 = "QCN9074"

class Ath11kConfigGenerator:
    """Generator for ath11k-specific configurations"""
    
    def __init__(self):
        """Initialize the configuration generator"""
        self.integration = Ath11kIntegration()
        
        # Define configuration templates
        self.config_templates = {
            "basic": {
                "name": "Basic ath11k",
                "description": "Basic ath11k configuration for standard connectivity",
                "chipsets": [Ath11kChipset.QCA6390, Ath11kChipset.QCA6490],
                "features": ["basic_wireless"],
                "use_case": "Standard wireless connectivity"
            },
            "monitor": {
                "name": "Monitor Mode",
                "description": "ath11k optimized for monitor mode and packet capture",
                "chipsets": [Ath11kChipset.QCA6390, Ath11kChipset.QCA6490, Ath11kChipset.WCN6855],
                "features": ["monitor_mode", "packet_capture", "radiotap"],
                "use_case": "Wireless monitoring and analysis"
            },
            "injection": {
                "name": "Packet Injection",
                "description": "ath11k with packet injection capabilities",
                "chipsets": [Ath11kChipset.QCA6390, Ath11kChipset.QCA6490],
                "features": ["monitor_mode", "packet_injection", "rate_control"],
                "use_case": "Wireless security testing"
            },
            "research": {
                "name": "Security Research",
                "description": "Full-featured ath11k for wireless security research",
                "chipsets": [Ath11kChipset.QCA6390, Ath11kChipset.QCA6490, Ath11kChipset.WCN6855],
                "features": ["monitor_mode", "packet_injection", "mesh_networking", "spectral_scan"],
                "use_case": "Comprehensive wireless security research"
            },
            "enterprise": {
                "name": "Enterprise",
                "description": "Enterprise-grade ath11k with all security features",
                "chipsets": [Ath11kChipset.QCA6490, Ath11kChipset.QCN9074],
                "features": ["wpa3", "sae", "owe", "mesh_networking", "beamforming"],
                "use_case": "Enterprise wireless deployment"
            },
            "high_performance": {
                "name": "High Performance",
                "description": "Maximum performance ath11k configuration",
                "chipsets": [Ath11kChipset.QCN9074],
                "features": ["beamforming", "mu_mimo", "ofdma", "spectral_scan"],
                "use_case": "High-performance wireless applications"
            }
        }
    
    def generate_config(self, template_name: str) -> Dict[str, str]:
        """Generate configuration for a specific template"""
        if template_name not in self.config_templates:
            raise ValueError(f"Unknown template: {template_name}")
        
        template = self.config_templates[template_name]
        config = {}
        
        # Base ath11k configuration
        base_config = self.integration.generate_ath11k_config(template["chipsets"])
        config.update(base_config)
        
        # Feature-specific configurations
        features = template["features"]
        
        if "monitor_mode" in features:
            monitor_config = self.integration.create_monitor_mode_config()
            config.update(monitor_config)
        
        if "packet_injection" in features:
            injection_config = self.integration.create_packet_injection_config()
            config.update(injection_config)
        
        if "mesh_networking" in features:
            mesh_config = self.integration.create_mesh_networking_config()
            config.update(mesh_config)
        
        # Template-specific optimizations
        if template_name == "research":
            config.update({
                "CONFIG_BACKPORTS_DEBUG": "y",
                "CONFIG_BACKPORTS_ATH11K_DEBUG": "y",
                "CONFIG_BACKPORTS_ATH11K_DEBUGFS": "y",
                "CONFIG_BACKPORTS_ATH11K_TRACING": "y",
                "CONFIG_BACKPORTS_STATISTICS": "y",
                "CONFIG_BACKPORTS_DIAGNOSTICS": "y"
            })
        
        elif template_name == "enterprise":
            config.update({
                "CONFIG_BACKPORTS_WIRELESS_CRYPTO": "y",
                "CONFIG_CRYPTO_CMAC": "y",
                "CONFIG_CRYPTO_CCMP": "y",
                "CONFIG_CRYPTO_GCMP": "y",
                "CONFIG_CRYPTO_SHA256": "y",
                "CONFIG_BACKPORTS_WIRELESS_SECURITY_ENHANCED": "y"
            })
        
        elif template_name == "high_performance":
            config.update({
                "CONFIG_BACKPORTS_ATH11K_SPECTRAL": "y",
                "CONFIG_BACKPORTS_STATISTICS": "y",
                "CONFIG_BACKPORTS_TRACING": "y"
            })
        
        return config
    
    def create_config_file(self, template_name: str, output_path: str) -> bool:
        """Create a configuration file for a template"""
        try:
            template = self.config_templates[template_name]
            config = self.generate_config(template_name)
            
            with open(output_path, 'w') as f:
                f.write(f"#\n# ath11k Configuration: {template['name']}\n")
                f.write(f"# {template['description']}\n")
                f.write(f"# Use case: {template['use_case']}\n")
                f.write(f"# Chipsets: {', '.join([c.value if hasattr(c, 'value') else str(c) for c in template['chipsets']])}\n")
                f.write(f"# Features: {', '.join(template['features'])}\n")
                f.write("#\n\n")
                
                # Write configuration options
                for option, value in sorted(config.items()):
                    if value == 'n':
                        f.write(f"# {option} is not set\n")
                    else:
                        f.write(f"{option}={value}\n")
            
            return True
        except Exception as e:
            print(f"Error creating config file: {e}")
            return False
    
    def create_all_configs(self, output_dir: str) -> Dict[str, bool]:
        """Create all configuration templates"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        for template_name in self.config_templates.keys():
            config_file = output_path / f"ath11k_{template_name}.config"
            success = self.create_config_file(template_name, str(config_file))
            results[template_name] = success
            
            if success:
                print(f"Created: {config_file}")
            else:
                print(f"Failed to create: {config_file}")
        
        return results
    
    def compare_configs(self, template1: str, template2: str) -> Dict[str, any]:
        """Compare two configuration templates"""
        if template1 not in self.config_templates or template2 not in self.config_templates:
            return {"error": "Invalid template names"}
        
        config1 = self.generate_config(template1)
        config2 = self.generate_config(template2)
        
        comparison = {
            "template1": template1,
            "template2": template2,
            "common_options": {},
            "different_options": {},
            "unique_to_template1": {},
            "unique_to_template2": {}
        }
        
        all_options = set(config1.keys()) | set(config2.keys())
        
        for option in all_options:
            value1 = config1.get(option)
            value2 = config2.get(option)
            
            if value1 is not None and value2 is not None:
                if value1 == value2:
                    comparison["common_options"][option] = value1
                else:
                    comparison["different_options"][option] = {
                        template1: value1,
                        template2: value2
                    }
            elif value1 is not None:
                comparison["unique_to_template1"][option] = value1
            elif value2 is not None:
                comparison["unique_to_template2"][option] = value2
        
        return comparison
    
    def generate_summary_report(self) -> Dict[str, any]:
        """Generate summary report of all templates"""
        report = {
            "templates": {},
            "chipset_usage": {},
            "feature_usage": {},
            "total_templates": len(self.config_templates)
        }
        
        # Analyze templates
        all_chipsets = set()
        all_features = set()
        
        for template_name, template in self.config_templates.items():
            report["templates"][template_name] = {
                "name": template["name"],
                "description": template["description"],
                "use_case": template["use_case"],
                "chipsets": [c.value if hasattr(c, 'value') else str(c) for c in template["chipsets"]],
                "features": template["features"],
                "config_options": len(self.generate_config(template_name))
            }
            
            # Collect chipsets and features
            for chipset in template["chipsets"]:
                chipset_name = chipset.value if hasattr(chipset, 'value') else str(chipset)
                all_chipsets.add(chipset_name)
            all_features.update(template["features"])
        
        # Analyze chipset usage
        for chipset in all_chipsets:
            usage_count = sum(1 for template in self.config_templates.values() 
                            if any((c.value if hasattr(c, 'value') else str(c)) == chipset for c in template["chipsets"]))
            report["chipset_usage"][chipset] = usage_count
        
        # Analyze feature usage
        for feature in all_features:
            usage_count = sum(1 for template in self.config_templates.values() 
                            if feature in template["features"])
            report["feature_usage"][feature] = usage_count
        
        return report

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ath11k Configuration Generator')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List templates
    list_parser = subparsers.add_parser('list', help='List available templates')
    
    # Generate config
    gen_parser = subparsers.add_parser('generate', help='Generate configuration')
    gen_parser.add_argument('template', help='Template name')
    gen_parser.add_argument('--output', '-o', help='Output file')
    
    # Generate all configs
    all_parser = subparsers.add_parser('generate-all', help='Generate all configurations')
    all_parser.add_argument('--output-dir', '-d', default='ath11k-configs', help='Output directory')
    
    # Compare configs
    comp_parser = subparsers.add_parser('compare', help='Compare two templates')
    comp_parser.add_argument('template1', help='First template')
    comp_parser.add_argument('template2', help='Second template')
    
    # Summary report
    report_parser = subparsers.add_parser('report', help='Generate summary report')
    report_parser.add_argument('--output', '-o', help='Output file (JSON)')
    
    args = parser.parse_args()
    
    generator = Ath11kConfigGenerator()
    
    if args.command == 'list':
        print("Available ath11k Configuration Templates:")
        print("=" * 50)
        for name, template in generator.config_templates.items():
            print(f"\n{name}: {template['name']}")
            print(f"  Description: {template['description']}")
            print(f"  Use case: {template['use_case']}")
            chipsets = [c.value if hasattr(c, 'value') else str(c) for c in template['chipsets']]
            print(f"  Chipsets: {', '.join(chipsets)}")
            print(f"  Features: {', '.join(template['features'])}")
        
        return 0
    
    elif args.command == 'generate':
        if args.template not in generator.config_templates:
            print(f"Error: Unknown template '{args.template}'")
            return 1
        
        if args.output:
            success = generator.create_config_file(args.template, args.output)
            if success:
                print(f"Configuration generated: {args.output}")
                return 0
            else:
                print("Failed to generate configuration")
                return 1
        else:
            # Print to stdout
            config = generator.generate_config(args.template)
            template = generator.config_templates[args.template]
            
            print(f"# ath11k Configuration: {template['name']}")
            print(f"# {template['description']}")
            print()
            
            for option, value in sorted(config.items()):
                if value == 'n':
                    print(f"# {option} is not set")
                else:
                    print(f"{option}={value}")
        
        return 0
    
    elif args.command == 'generate-all':
        results = generator.create_all_configs(args.output_dir)
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        print(f"\nGenerated {successful}/{total} configurations in {args.output_dir}")
        return 0 if successful == total else 1
    
    elif args.command == 'compare':
        comparison = generator.compare_configs(args.template1, args.template2)
        
        if "error" in comparison:
            print(f"Error: {comparison['error']}")
            return 1
        
        print(f"Comparing {args.template1} vs {args.template2}")
        print("=" * 50)
        
        print(f"\nCommon options: {len(comparison['common_options'])}")
        print(f"Different options: {len(comparison['different_options'])}")
        print(f"Unique to {args.template1}: {len(comparison['unique_to_template1'])}")
        print(f"Unique to {args.template2}: {len(comparison['unique_to_template2'])}")
        
        if comparison['different_options']:
            print(f"\nDifferent options:")
            for option, values in comparison['different_options'].items():
                print(f"  {option}:")
                print(f"    {args.template1}: {values[args.template1]}")
                print(f"    {args.template2}: {values[args.template2]}")
        
        return 0
    
    elif args.command == 'report':
        report = generator.generate_summary_report()
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"Report saved to: {args.output}")
        else:
            print("ath11k Configuration Templates Summary")
            print("=" * 50)
            print(f"Total templates: {report['total_templates']}")
            
            print(f"\nChipset usage:")
            for chipset, count in sorted(report['chipset_usage'].items()):
                print(f"  {chipset}: {count} templates")
            
            print(f"\nFeature usage:")
            for feature, count in sorted(report['feature_usage'].items()):
                print(f"  {feature}: {count} templates")
        
        return 0
    
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())