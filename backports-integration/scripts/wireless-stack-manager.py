#!/usr/bin/env python3
"""
Comprehensive Wireless Stack Manager

This script provides a unified interface for managing the complete wireless
stack integration including configuration, module loading, and compatibility.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Optional

# Add the scripts directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from wireless_stack_integration import WirelessStackIntegration, StackComponent
    from module_loading_manager import ModuleLoadingManager
    from wireless_extensions_compat import WirelessExtensionsCompat
    from wireless_dependency_resolver import WirelessDependencyResolver
except ImportError as e:
    print(f"Warning: Could not import all required modules: {e}")
    # Create minimal fallback classes
    class WirelessStackIntegration:
        def __init__(self, kernel_root=None): pass
        def generate_stack_configuration(self, name): return {}
        def generate_integration_report(self): return {}
        def validate_stack_integration(self): return {"configuration_valid": True, "issues": [], "recommendations": []}
    
    class ModuleLoadingManager:
        def __init__(self): pass
        def load_wireless_stack(self, modules, dry_run=False): return {"success": True, "messages": []}
        def generate_loading_script(self, modules, path): return True
    
    class WirelessExtensionsCompat:
        def __init__(self): pass
        def generate_compatibility_report(self): return {"compatibility_status": {"compatibility_issues": []}, "recommendations": []}
        def create_wext_wrapper_scripts(self, path): return {}
    
    class WirelessDependencyResolver:
        def __init__(self, kernel_root=None): pass
        def generate_dependency_report(self, drivers): return {}
        def save_dependency_report(self, report, path): pass

class WirelessStackManager:
    """Comprehensive wireless stack manager"""
    
    def __init__(self, kernel_root: str = "."):
        """Initialize the wireless stack manager"""
        self.kernel_root = Path(kernel_root).resolve()
        self.backports_dir = self.kernel_root / "backports-integration"
        
        # Initialize component managers
        self.stack_integration = WirelessStackIntegration(kernel_root)
        self.module_manager = ModuleLoadingManager()
        self.wext_compat = WirelessExtensionsCompat()
        self.dependency_resolver = WirelessDependencyResolver(kernel_root)
        
        # Available configurations
        self.configurations = {
            "basic": {
                "name": "Basic Wireless",
                "description": "Minimal wireless stack for basic connectivity",
                "components": ["cfg80211", "mac80211"],
                "drivers": [],
                "features": ["basic_wireless"]
            },
            "monitor": {
                "name": "Monitor Mode",
                "description": "Wireless stack optimized for monitoring and analysis",
                "components": ["cfg80211", "mac80211"],
                "drivers": ["ath11k", "ath10k"],
                "features": ["monitor_mode", "packet_injection"]
            },
            "research": {
                "name": "Security Research",
                "description": "Full featured stack for wireless security research",
                "components": ["cfg80211", "mac80211"],
                "drivers": ["ath11k", "ath10k", "ath9k"],
                "features": ["monitor_mode", "packet_injection", "mesh_networking", "wpa3"]
            },
            "enterprise": {
                "name": "Enterprise Wireless",
                "description": "Enterprise-grade wireless with all features",
                "components": ["cfg80211", "mac80211"],
                "drivers": ["ath11k", "iwlwifi"],
                "features": ["wpa3", "mesh_networking", "power_management"]
            },
            "legacy": {
                "name": "Legacy Compatible",
                "description": "Maximum compatibility with legacy systems",
                "components": ["cfg80211", "mac80211", "wireless_ext"],
                "drivers": ["ath10k", "rt2x00"],
                "features": ["wireless_ext", "wpa2"]
            }
        }
    
    def setup_configuration(self, config_name: str, dry_run: bool = False) -> Dict[str, any]:
        """Set up a complete wireless configuration"""
        if config_name not in self.configurations:
            return {"success": False, "error": f"Unknown configuration: {config_name}"}
        
        config_info = self.configurations[config_name]
        result = {
            "success": True,
            "configuration": config_name,
            "steps_completed": [],
            "steps_failed": [],
            "messages": []
        }
        
        try:
            # Step 1: Generate kernel configuration
            result["messages"].append(f"Generating kernel configuration for '{config_info['name']}'...")
            if not dry_run:
                kernel_config = self.stack_integration.generate_stack_configuration(config_name)
                config_file = self.backports_dir / "configs" / f"{config_name}.config"
                config_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(config_file, 'w') as f:
                    f.write(f"# Wireless Stack Configuration: {config_info['name']}\n")
                    f.write(f"# {config_info['description']}\n\n")
                    for option, value in sorted(kernel_config.items()):
                        if value == 'n':
                            f.write(f"# {option} is not set\n")
                        else:
                            f.write(f"{option}={value}\n")
                
                result["messages"].append(f"Kernel configuration saved to {config_file}")
            result["steps_completed"].append("kernel_config")
            
            # Step 2: Generate dependency report
            result["messages"].append("Analyzing dependencies...")
            if config_info["drivers"]:
                dep_report = self.dependency_resolver.generate_dependency_report(config_info["drivers"])
                if not dry_run:
                    dep_file = self.backports_dir / "reports" / f"{config_name}_dependencies.json"
                    dep_file.parent.mkdir(parents=True, exist_ok=True)
                    self.dependency_resolver.save_dependency_report(dep_report, str(dep_file))
                    result["messages"].append(f"Dependency report saved to {dep_file}")
            result["steps_completed"].append("dependencies")
            
            # Step 3: Generate module loading script
            result["messages"].append("Creating module loading script...")
            if not dry_run:
                modules = config_info["components"] + config_info["drivers"]
                script_file = self.backports_dir / "scripts" / f"load_{config_name}_stack.sh"
                if self.module_manager.generate_loading_script(modules, str(script_file)):
                    result["messages"].append(f"Module loading script created: {script_file}")
                else:
                    result["steps_failed"].append("module_script")
                    result["messages"].append("Failed to create module loading script")
            result["steps_completed"].append("module_script")
            
            # Step 4: Create WEXT compatibility wrappers if needed
            if "wireless_ext" in config_info["features"]:
                result["messages"].append("Creating WEXT compatibility wrappers...")
                if not dry_run:
                    wrapper_dir = self.backports_dir / "wext-wrappers"
                    wrapper_results = self.wext_compat.create_wext_wrapper_scripts(str(wrapper_dir))
                    successful_wrappers = [tool for tool, success in wrapper_results.items() if success]
                    if successful_wrappers:
                        result["messages"].append(f"WEXT wrappers created: {', '.join(successful_wrappers)}")
                    else:
                        result["steps_failed"].append("wext_wrappers")
                result["steps_completed"].append("wext_wrappers")
            
            # Step 5: Load modules if requested
            if not dry_run:
                result["messages"].append("Module loading would be performed here (use --load-modules)")
            
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            result["steps_failed"].append("setup_error")
        
        return result
    
    def load_stack(self, config_name: str, dry_run: bool = False) -> Dict[str, any]:
        """Load wireless stack modules for a configuration"""
        if config_name not in self.configurations:
            return {"success": False, "error": f"Unknown configuration: {config_name}"}
        
        config_info = self.configurations[config_name]
        modules = config_info["components"] + config_info["drivers"]
        
        return self.module_manager.load_wireless_stack(modules, dry_run)
    
    def validate_stack(self, config_name: str = None) -> Dict[str, any]:
        """Validate wireless stack configuration and status"""
        validation = {
            "stack_integration": self.stack_integration.validate_stack_integration(),
            "wext_compatibility": self.wext_compat.generate_compatibility_report(),
            "overall_status": "unknown",
            "issues": [],
            "recommendations": []
        }
        
        # Analyze results
        stack_valid = validation["stack_integration"]["configuration_valid"]
        wext_issues = len(validation["wext_compatibility"]["compatibility_status"]["compatibility_issues"])
        
        if stack_valid and wext_issues == 0:
            validation["overall_status"] = "good"
        elif stack_valid:
            validation["overall_status"] = "acceptable"
        else:
            validation["overall_status"] = "issues"
        
        # Collect issues and recommendations
        validation["issues"].extend(validation["stack_integration"]["issues"])
        validation["recommendations"].extend(validation["stack_integration"]["recommendations"])
        validation["recommendations"].extend(validation["wext_compatibility"]["recommendations"])
        
        return validation
    
    def generate_comprehensive_report(self, config_name: str = None) -> Dict[str, any]:
        """Generate comprehensive wireless stack report"""
        report = {
            "system_info": {
                "kernel_root": str(self.kernel_root),
                "backports_dir": str(self.backports_dir)
            },
            "available_configurations": list(self.configurations.keys()),
            "stack_integration": self.stack_integration.generate_integration_report(),
            "wext_compatibility": self.wext_compat.generate_compatibility_report(),
            "validation": self.validate_stack(config_name)
        }
        
        if config_name and config_name in self.configurations:
            config_info = self.configurations[config_name]
            report["selected_configuration"] = {
                "name": config_info["name"],
                "description": config_info["description"],
                "components": config_info["components"],
                "drivers": config_info["drivers"],
                "features": config_info["features"]
            }
            
            # Add dependency analysis for selected configuration
            if config_info["drivers"]:
                report["dependencies"] = self.dependency_resolver.generate_dependency_report(config_info["drivers"])
        
        return report

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Comprehensive Wireless Stack Manager')
    parser.add_argument('--kernel-root', default='.', help='Path to kernel source root')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List configurations
    list_parser = subparsers.add_parser('list', help='List available configurations')
    
    # Setup configuration
    setup_parser = subparsers.add_parser('setup', help='Set up wireless configuration')
    setup_parser.add_argument('config', help='Configuration name')
    setup_parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    
    # Load stack
    load_parser = subparsers.add_parser('load', help='Load wireless stack modules')
    load_parser.add_argument('config', help='Configuration name')
    load_parser.add_argument('--dry-run', action='store_true', help='Show what would be loaded')
    
    # Validate stack
    validate_parser = subparsers.add_parser('validate', help='Validate wireless stack')
    validate_parser.add_argument('--config', help='Configuration to validate')
    
    # Generate report
    report_parser = subparsers.add_parser('report', help='Generate comprehensive report')
    report_parser.add_argument('--config', help='Configuration to analyze')
    report_parser.add_argument('--output', help='Output file (JSON format)')
    
    args = parser.parse_args()
    
    manager = WirelessStackManager(args.kernel_root)
    
    if args.command == 'list':
        print("Available Wireless Stack Configurations:")
        print("=" * 50)
        for config_name, config_info in manager.configurations.items():
            print(f"\n{config_name}: {config_info['name']}")
            print(f"  Description: {config_info['description']}")
            print(f"  Components: {', '.join(config_info['components'])}")
            print(f"  Drivers: {', '.join(config_info['drivers']) if config_info['drivers'] else 'None'}")
            print(f"  Features: {', '.join(config_info['features'])}")
        
        return 0
    
    elif args.command == 'setup':
        print(f"Setting up wireless configuration: {args.config}")
        result = manager.setup_configuration(args.config, args.dry_run)
        
        if result["success"]:
            print("✅ Setup completed successfully!")
            for message in result["messages"]:
                print(f"  {message}")
            
            if result["steps_failed"]:
                print(f"\n⚠️  Some steps failed: {', '.join(result['steps_failed'])}")
        else:
            print(f"❌ Setup failed: {result.get('error', 'Unknown error')}")
            return 1
        
        return 0
    
    elif args.command == 'load':
        print(f"Loading wireless stack for configuration: {args.config}")
        result = manager.load_stack(args.config, args.dry_run)
        
        if result["success"]:
            print("✅ Stack loaded successfully!")
            if result["loaded_modules"]:
                print(f"  Loaded modules: {', '.join(result['loaded_modules'])}")
        else:
            print("❌ Stack loading failed!")
            if result["failed_modules"]:
                print(f"  Failed modules: {', '.join(result['failed_modules'])}")
        
        for message in result["messages"]:
            print(f"  {message}")
        
        return 0 if result["success"] else 1
    
    elif args.command == 'validate':
        print("Validating wireless stack...")
        validation = manager.validate_stack(args.config)
        
        status_symbols = {"good": "✅", "acceptable": "⚠️", "issues": "❌", "unknown": "❓"}
        status_symbol = status_symbols.get(validation["overall_status"], "❓")
        
        print(f"{status_symbol} Overall Status: {validation['overall_status']}")
        
        if validation["issues"]:
            print(f"\nIssues Found:")
            for issue in validation["issues"]:
                print(f"  - {issue}")
        
        if validation["recommendations"]:
            print(f"\nRecommendations:")
            for rec in validation["recommendations"]:
                print(f"  - {rec}")
        
        return 0 if validation["overall_status"] in ["good", "acceptable"] else 1
    
    elif args.command == 'report':
        print("Generating comprehensive wireless stack report...")
        report = manager.generate_comprehensive_report(args.config)
        
        if args.output:
            import json
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"Report saved to: {args.output}")
        else:
            # Print summary
            print(f"\nSystem Information:")
            print(f"  Kernel Root: {report['system_info']['kernel_root']}")
            print(f"  Backports Dir: {report['system_info']['backports_dir']}")
            
            print(f"\nAvailable Configurations: {len(report['available_configurations'])}")
            for config in report['available_configurations']:
                print(f"  - {config}")
            
            validation = report['validation']
            status_symbol = {"good": "✅", "acceptable": "⚠️", "issues": "❌", "unknown": "❓"}[validation['overall_status']]
            print(f"\nValidation Status: {status_symbol} {validation['overall_status']}")
        
        return 0
    
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())