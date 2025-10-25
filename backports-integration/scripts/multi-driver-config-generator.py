#!/usr/bin/env python3
"""
Multi-Driver Configuration Generator

This script generates optimized configurations for different multi-driver scenarios
including mixed vendor setups, enterprise deployments, and research configurations.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional

# Add the scripts directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from multi_driver_integration import MultiDriverIntegration, DriverFamily
except ImportError:
    print("Warning: Could not import multi_driver_integration module")
    # Create minimal fallback
    class MultiDriverIntegration:
        def __init__(self): pass
        def generate_driver_config(self, drivers): return {}
        def create_ath10k_integration(self): return {}
        def create_iwlwifi_integration(self): return {}
        def create_rt2x00_integration(self): return {}
    class DriverFamily:
        ATH10K = "ath10k"
        IWLWIFI = "iwlwifi"
        RT2X00 = "rt2x00"

class MultiDriverConfigGenerator:
    """Generator for multi-driver configurations"""
    
    def __init__(self):
        """Initialize the configuration generator"""
        self.integration = MultiDriverIntegration()
        
        # Define configuration scenarios
        self.config_scenarios = {
            "enterprise_mixed": {
                "name": "Enterprise Mixed Vendors",
                "description": "Enterprise setup with Intel and Qualcomm drivers",
                "drivers": ["ath10k", "iwlwifi"],
                "features": ["wpa3", "power_management", "enterprise_security"],
                "use_case": "Corporate environments with mixed hardware"
            },
            "research_comprehensive": {
                "name": "Research Comprehensive",
                "description": "All drivers for comprehensive wireless research",
                "drivers": ["ath10k", "iwlwifi", "rt2x00"],
                "features": ["monitor_mode", "packet_injection", "spectral_scan", "debugging"],
                "use_case": "Wireless security research and analysis"
            },
            "monitor_specialized": {
                "name": "Monitor Mode Specialized",
                "description": "Optimized for monitoring with injection-capable drivers",
                "drivers": ["ath10k", "rt2x00"],
                "features": ["monitor_mode", "packet_injection", "radiotap", "channel_switching"],
                "use_case": "Wireless monitoring and packet capture"
            },
            "usb_portable": {
                "name": "USB Portable Setup",
                "description": "USB-based wireless drivers for portable setups",
                "drivers": ["rt2x00"],
                "features": ["usb_support", "monitor_mode", "packet_injection", "low_power"],
                "use_case": "Portable wireless testing and analysis"
            },
            "intel_optimized": {
                "name": "Intel Optimized",
                "description": "Intel-specific optimizations and features",
                "drivers": ["iwlwifi"],
                "features": ["power_management", "wpa3", "beamforming", "enterprise_security"],
                "use_case": "Intel-based systems with power optimization"
            },
            "atheros_complete": {
                "name": "Atheros Complete",
                "description": "Complete Atheros driver stack (ath10k + ath11k compatibility)",
                "drivers": ["ath10k"],
                "features": ["monitor_mode", "packet_injection", "mesh_networking", "spectral_scan"],
                "use_case": "Atheros-based systems with full feature set"
            }
        }
    
    def generate_scenario_config(self, scenario_name: str) -> Dict[str, str]:
        """Generate configuration for a specific scenario"""
        if scenario_name not in self.config_scenarios:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        
        scenario = self.config_scenarios[scenario_name]
        config = {}
        
        # Base multi-driver configuration
        base_config = self.integration.generate_driver_config(scenario["drivers"])
        config.update(base_config)
        
        # Driver-specific configurations
        for driver in scenario["drivers"]:
            if driver == "ath10k":
                ath10k_config = self.integration.create_ath10k_integration()
                config.update(ath10k_config)
            elif driver == "iwlwifi":
                iwlwifi_config = self.integration.create_iwlwifi_integration()
                config.update(iwlwifi_config)
            elif driver == "rt2x00":
                rt2x00_config = self.integration.create_rt2x00_integration()
                config.update(rt2x00_config)
        
        # Feature-specific configurations
        features = scenario["features"]
        
        if "monitor_mode" in features:
            config.update({
                "CONFIG_BACKPORTS_MONITOR_MODE": "y",
                "CONFIG_BACKPORTS_MONITOR_RADIOTAP": "y",
                "CONFIG_BACKPORTS_MONITOR_CHANNEL_SWITCH": "y",
                "CONFIG_BACKPORTS_WIRELESS_MONITOR_ENHANCED": "y"
            })
        
        if "packet_injection" in features:
            config.update({
                "CONFIG_BACKPORTS_FRAME_INJECTION": "y",
                "CONFIG_BACKPORTS_INJECTION_RATE_CONTROL": "y",
                "CONFIG_BACKPORTS_INJECTION_SECURITY_AUDIT": "y",
                "CONFIG_BACKPORTS_WIRELESS_INJECTION_ENHANCED": "y"
            })
        
        if "wpa3" in features or "enterprise_security" in features:
            config.update({
                "CONFIG_BACKPORTS_WIRELESS_CRYPTO": "y",
                "CONFIG_CRYPTO_CMAC": "y",
                "CONFIG_CRYPTO_CCMP": "y",
                "CONFIG_CRYPTO_GCMP": "y",
                "CONFIG_CRYPTO_SHA256": "y",
                "CONFIG_BACKPORTS_WIRELESS_SECURITY_ENHANCED": "y"
            })
        
        if "power_management" in features:
            config.update({
                "CONFIG_BACKPORTS_PM": "y",
                "CONFIG_BACKPORTS_PM_SLEEP": "y",
                "CONFIG_BACKPORTS_PM_RUNTIME": "y"
            })
        
        if "debugging" in features:
            config.update({
                "CONFIG_BACKPORTS_DEBUG": "y",
                "CONFIG_BACKPORTS_DEBUG_VERBOSE": "y",
                "CONFIG_BACKPORTS_STATISTICS": "y",
                "CONFIG_BACKPORTS_DIAGNOSTICS": "y",
                "CONFIG_BACKPORTS_TRACING": "y"
            })
        
        if "spectral_scan" in features:
            config.update({
                "CONFIG_BACKPORTS_ATH10K_SPECTRAL": "y",
                "CONFIG_BACKPORTS_ATH11K_SPECTRAL": "y"
            })
        
        if "mesh_networking" in features:
            config.update({
                "CONFIG_BACKPORTS_MAC80211_MESH": "y",
                "CONFIG_BACKPORTS_WIRELESS_MESH": "y",
                "CONFIG_BACKPORTS_WIRELESS_MESH_ENHANCED": "y"
            })
        
        if "usb_support" in features:
            config.update({
                "CONFIG_USB": "y",
                "CONFIG_USB_SUPPORT": "y"
            })
        
        return config
    
    def create_scenario_file(self, scenario_name: str, output_path: str) -> bool:
        """Create a configuration file for a scenario"""
        try:
            scenario = self.config_scenarios[scenario_name]
            config = self.generate_scenario_config(scenario_name)
            
            with open(output_path, 'w') as f:
                f.write(f"#\n# Multi-Driver Configuration: {scenario['name']}\n")
                f.write(f"# {scenario['description']}\n")
                f.write(f"# Use case: {scenario['use_case']}\n")
                f.write(f"# Drivers: {', '.join(scenario['drivers'])}\n")
                f.write(f"# Features: {', '.join(scenario['features'])}\n")
                f.write("#\n\n")
                
                # Group configurations by driver
                driver_configs = {}
                general_configs = {}
                
                for option, value in sorted(config.items()):
                    if any(driver.upper() in option for driver in ["ATH10K", "IWLWIFI", "RT2X00"]):
                        # Driver-specific config
                        for driver in ["ATH10K", "IWLWIFI", "RT2X00"]:
                            if driver in option:
                                if driver not in driver_configs:
                                    driver_configs[driver] = {}
                                driver_configs[driver][option] = value
                                break
                    else:
                        # General config
                        general_configs[option] = value
                
                # Write general configurations first
                if general_configs:
                    f.write("# General wireless configuration\n")
                    for option, value in sorted(general_configs.items()):
                        if value == 'n':
                            f.write(f"# {option} is not set\n")
                        else:
                            f.write(f"{option}={value}\n")
                    f.write("\n")
                
                # Write driver-specific configurations
                for driver, driver_config in driver_configs.items():
                    if driver_config:
                        f.write(f"# {driver} driver configuration\n")
                        for option, value in sorted(driver_config.items()):
                            if value == 'n':
                                f.write(f"# {option} is not set\n")
                            else:
                                f.write(f"{option}={value}\n")
                        f.write("\n")
            
            return True
        except Exception as e:
            print(f"Error creating scenario file: {e}")
            return False
    
    def create_all_scenarios(self, output_dir: str) -> Dict[str, bool]:
        """Create all scenario configurations"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        for scenario_name in self.config_scenarios.keys():
            config_file = output_path / f"multi_driver_{scenario_name}.config"
            success = self.create_scenario_file(scenario_name, str(config_file))
            results[scenario_name] = success
            
            if success:
                print(f"Created: {config_file}")
            else:
                print(f"Failed to create: {config_file}")
        
        return results
    
    def compare_scenarios(self, scenario1: str, scenario2: str) -> Dict[str, any]:
        """Compare two configuration scenarios"""
        if scenario1 not in self.config_scenarios or scenario2 not in self.config_scenarios:
            return {"error": "Invalid scenario names"}
        
        config1 = self.generate_scenario_config(scenario1)
        config2 = self.generate_scenario_config(scenario2)
        
        comparison = {
            "scenario1": scenario1,
            "scenario2": scenario2,
            "drivers_comparison": {
                "scenario1_drivers": self.config_scenarios[scenario1]["drivers"],
                "scenario2_drivers": self.config_scenarios[scenario2]["drivers"],
                "common_drivers": list(set(self.config_scenarios[scenario1]["drivers"]) & 
                                     set(self.config_scenarios[scenario2]["drivers"])),
                "unique_to_scenario1": list(set(self.config_scenarios[scenario1]["drivers"]) - 
                                          set(self.config_scenarios[scenario2]["drivers"])),
                "unique_to_scenario2": list(set(self.config_scenarios[scenario2]["drivers"]) - 
                                          set(self.config_scenarios[scenario1]["drivers"]))
            },
            "config_differences": {},
            "common_options": {},
            "unique_to_scenario1": {},
            "unique_to_scenario2": {}
        }
        
        all_options = set(config1.keys()) | set(config2.keys())
        
        for option in all_options:
            value1 = config1.get(option)
            value2 = config2.get(option)
            
            if value1 is not None and value2 is not None:
                if value1 == value2:
                    comparison["common_options"][option] = value1
                else:
                    comparison["config_differences"][option] = {
                        scenario1: value1,
                        scenario2: value2
                    }
            elif value1 is not None:
                comparison["unique_to_scenario1"][option] = value1
            elif value2 is not None:
                comparison["unique_to_scenario2"][option] = value2
        
        return comparison
    
    def generate_summary_report(self) -> Dict[str, any]:
        """Generate summary report of all scenarios"""
        report = {
            "scenarios": {},
            "driver_usage": {},
            "feature_usage": {},
            "total_scenarios": len(self.config_scenarios)
        }
        
        # Analyze scenarios
        all_drivers = set()
        all_features = set()
        
        for scenario_name, scenario in self.config_scenarios.items():
            report["scenarios"][scenario_name] = {
                "name": scenario["name"],
                "description": scenario["description"],
                "use_case": scenario["use_case"],
                "drivers": scenario["drivers"],
                "features": scenario["features"],
                "config_options": len(self.generate_scenario_config(scenario_name))
            }
            
            # Collect drivers and features
            all_drivers.update(scenario["drivers"])
            all_features.update(scenario["features"])
        
        # Analyze driver usage
        for driver in all_drivers:
            usage_count = sum(1 for scenario in self.config_scenarios.values() 
                            if driver in scenario["drivers"])
            report["driver_usage"][driver] = usage_count
        
        # Analyze feature usage
        for feature in all_features:
            usage_count = sum(1 for scenario in self.config_scenarios.values() 
                            if feature in scenario["features"])
            report["feature_usage"][feature] = usage_count
        
        return report

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Multi-Driver Configuration Generator')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List scenarios
    list_parser = subparsers.add_parser('list', help='List available scenarios')
    
    # Generate config
    gen_parser = subparsers.add_parser('generate', help='Generate configuration')
    gen_parser.add_argument('scenario', help='Scenario name')
    gen_parser.add_argument('--output', '-o', help='Output file')
    
    # Generate all configs
    all_parser = subparsers.add_parser('generate-all', help='Generate all configurations')
    all_parser.add_argument('--output-dir', '-d', default='multi-driver-configs', help='Output directory')
    
    # Compare scenarios
    comp_parser = subparsers.add_parser('compare', help='Compare two scenarios')
    comp_parser.add_argument('scenario1', help='First scenario')
    comp_parser.add_argument('scenario2', help='Second scenario')
    
    # Summary report
    report_parser = subparsers.add_parser('report', help='Generate summary report')
    report_parser.add_argument('--output', '-o', help='Output file (JSON)')
    
    args = parser.parse_args()
    
    generator = MultiDriverConfigGenerator()
    
    if args.command == 'list':
        print("Available Multi-Driver Configuration Scenarios:")
        print("=" * 60)
        for name, scenario in generator.config_scenarios.items():
            print(f"\n{name}: {scenario['name']}")
            print(f"  Description: {scenario['description']}")
            print(f"  Use case: {scenario['use_case']}")
            print(f"  Drivers: {', '.join(scenario['drivers'])}")
            print(f"  Features: {', '.join(scenario['features'])}")
        
        return 0
    
    elif args.command == 'generate':
        if args.scenario not in generator.config_scenarios:
            print(f"Error: Unknown scenario '{args.scenario}'")
            return 1
        
        if args.output:
            success = generator.create_scenario_file(args.scenario, args.output)
            if success:
                print(f"Configuration generated: {args.output}")
                return 0
            else:
                print("Failed to generate configuration")
                return 1
        else:
            # Print to stdout
            config = generator.generate_scenario_config(args.scenario)
            scenario = generator.config_scenarios[args.scenario]
            
            print(f"# Multi-Driver Configuration: {scenario['name']}")
            print(f"# {scenario['description']}")
            print()
            
            for option, value in sorted(config.items()):
                if value == 'n':
                    print(f"# {option} is not set")
                else:
                    print(f"{option}={value}")
        
        return 0
    
    elif args.command == 'generate-all':
        results = generator.create_all_scenarios(args.output_dir)
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        print(f"\nGenerated {successful}/{total} configurations in {args.output_dir}")
        return 0 if successful == total else 1
    
    elif args.command == 'compare':
        comparison = generator.compare_scenarios(args.scenario1, args.scenario2)
        
        if "error" in comparison:
            print(f"Error: {comparison['error']}")
            return 1
        
        print(f"Comparing {args.scenario1} vs {args.scenario2}")
        print("=" * 60)
        
        # Driver comparison
        drivers_comp = comparison["drivers_comparison"]
        print(f"\nDriver Comparison:")
        print(f"  {args.scenario1}: {', '.join(drivers_comp['scenario1_drivers'])}")
        print(f"  {args.scenario2}: {', '.join(drivers_comp['scenario2_drivers'])}")
        print(f"  Common: {', '.join(drivers_comp['common_drivers']) if drivers_comp['common_drivers'] else 'None'}")
        
        # Configuration comparison
        print(f"\nConfiguration Comparison:")
        print(f"  Common options: {len(comparison['common_options'])}")
        print(f"  Different options: {len(comparison['config_differences'])}")
        print(f"  Unique to {args.scenario1}: {len(comparison['unique_to_scenario1'])}")
        print(f"  Unique to {args.scenario2}: {len(comparison['unique_to_scenario2'])}")
        
        return 0
    
    elif args.command == 'report':
        report = generator.generate_summary_report()
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"Report saved to: {args.output}")
        else:
            print("Multi-Driver Configuration Scenarios Summary")
            print("=" * 60)
            print(f"Total scenarios: {report['total_scenarios']}")
            
            print(f"\nDriver usage:")
            for driver, count in sorted(report['driver_usage'].items()):
                print(f"  {driver}: {count} scenarios")
            
            print(f"\nFeature usage:")
            for feature, count in sorted(report['feature_usage'].items()):
                print(f"  {feature}: {count} scenarios")
        
        return 0
    
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())