#!/usr/bin/env python3
"""
Comprehensive Wireless Driver Management CLI

This script provides a unified interface for wireless driver management,
including driver selection, firmware automation, conflict resolution,
and regulatory compliance checking.
"""

import os
import sys
import subprocess
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional

# Add the scripts directory to Python path for imports
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

try:
    from wireless_driver_manager import WirelessDriverManager
    from firmware_automation import FirmwareAutomation
    from wireless_conflict_resolver import WirelessConflictResolver
    from regulatory_manager import WirelessRegulatoryManager
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Note: Some functionality may be limited without all components")
    
    # Create minimal fallback classes
    class WirelessDriverManager:
        def __init__(self, *args, **kwargs):
            pass
        def list_drivers(self, *args, **kwargs):
            return []
        def get_driver_info(self, *args, **kwargs):
            return None
        def install_driver(self, *args, **kwargs):
            return {"success": False, "errors": ["Driver manager not available"]}
        def uninstall_driver(self, *args, **kwargs):
            return {"success": False, "errors": ["Driver manager not available"]}
        def check_regulatory_compliance(self, *args, **kwargs):
            return {"compliant": False, "errors": ["Compliance checker not available"]}
        def generate_management_report(self, *args, **kwargs):
            return "Driver management not available"
    
    class FirmwareAutomation:
        def __init__(self, *args, **kwargs):
            pass
        def download_firmware(self, *args, **kwargs):
            return {"success": False, "errors": ["Firmware automation not available"]}
        def install_firmware(self, *args, **kwargs):
            return {"success": False, "errors": ["Firmware automation not available"]}
        def validate_firmware(self, *args, **kwargs):
            return {"valid": False, "errors": ["Firmware automation not available"]}
        def cleanup_firmware(self, *args, **kwargs):
            return {"success": False, "errors": ["Firmware automation not available"]}
        def generate_firmware_report(self, *args, **kwargs):
            return "Firmware automation not available"
    
    class WirelessConflictResolver:
        def __init__(self, *args, **kwargs):
            pass
        def detect_active_conflicts(self, *args, **kwargs):
            return []
        def resolve_all_conflicts(self, *args, **kwargs):
            return {"success": False, "errors": ["Conflict resolver not available"]}
        def generate_resolution_report(self, *args, **kwargs):
            return "Conflict resolution not available"
    
    class WirelessRegulatoryManager:
        def __init__(self, *args, **kwargs):
            pass
        def check_regulatory_database(self, *args, **kwargs):
            return {"db_exists": False, "sig_exists": False}
        def download_regulatory_database(self, *args, **kwargs):
            return False
        def get_channel_list(self, *args, **kwargs):
            return []

class WirelessManagementCLI:
    """Unified wireless driver management CLI"""
    
    def __init__(self, kernel_root: str = "."):
        """Initialize management CLI"""
        self.kernel_root = Path(kernel_root).resolve()
        
        # Initialize management components
        try:
            self.driver_manager = WirelessDriverManager(str(self.kernel_root))
            self.firmware_automation = FirmwareAutomation(str(self.kernel_root))
            self.conflict_resolver = WirelessConflictResolver(str(self.kernel_root))
            self.regulatory_manager = WirelessRegulatoryManager()
        except Exception as e:
            print(f"Error initializing management components: {e}")
            sys.exit(1)
    
    def cmd_list_drivers(self, args) -> int:
        """List available wireless drivers"""
        try:
            drivers = self.driver_manager.list_drivers(args.status)
            
            if not drivers:
                print("No wireless drivers found")
                return 0
            
            print(f"Wireless Drivers ({len(drivers)} found):")
            print("-" * 60)
            
            for driver in drivers:
                status_icons = {
                    "loaded": "🟢",
                    "installed": "🟡", 
                    "available": "⚪",
                    "missing": "🔴",
                    "conflicted": "🔶"
                }
                
                icon = status_icons.get(driver.status.value, "❓")
                print(f"{icon} {driver.name:<12} {driver.status.value:<12} {driver.description}")
                
                if args.verbose:
                    print(f"   Version: {driver.version}")
                    print(f"   Chipsets: {', '.join(driver.chipsets)}")
                    print(f"   Features: {', '.join(driver.features)}")
                    print(f"   Dependencies: {', '.join(driver.dependencies)}")
                    if driver.firmware_files:
                        print(f"   Firmware: {len(driver.firmware_files)} files required")
                    print()
            
            return 0
        
        except Exception as e:
            print(f"Error listing drivers: {e}")
            return 1
    
    def cmd_driver_info(self, args) -> int:
        """Show detailed driver information"""
        if not args.driver:
            print("Error: Driver name required")
            return 1
        
        try:
            driver_info = self.driver_manager.get_driver_info(args.driver)
            
            if not driver_info:
                print(f"Driver not found: {args.driver}")
                return 1
            
            print(f"Driver Information: {driver_info.name}")
            print("=" * 50)
            print(f"Description: {driver_info.description}")
            print(f"Version: {driver_info.version}")
            print(f"Status: {driver_info.status.value}")
            print(f"Module Path: {driver_info.module_path or 'Not found'}")
            print()
            
            print("Supported Chipsets:")
            for chipset in driver_info.chipsets:
                print(f"  - {chipset}")
            print()
            
            print("Features:")
            for feature in driver_info.features:
                print(f"  - {feature}")
            print()
            
            print("Dependencies:")
            for dep in driver_info.dependencies:
                print(f"  - {dep}")
            print()
            
            if driver_info.firmware_files:
                print("Required Firmware:")
                for fw in driver_info.firmware_files:
                    print(f"  - {fw}")
            
            return 0
        
        except Exception as e:
            print(f"Error getting driver info: {e}")
            return 1
    
    def cmd_install_driver(self, args) -> int:
        """Install a wireless driver"""
        if not args.driver:
            print("Error: Driver name required")
            return 1
        
        try:
            print(f"Installing wireless driver: {args.driver}")
            if args.chipset:
                print(f"Target chipset: {args.chipset}")
            
            # Install driver
            result = self.driver_manager.install_driver(args.driver, args.chipset)
            
            if result["success"]:
                print(f"✅ Successfully installed driver: {args.driver}")
                
                print("\nActions taken:")
                for action in result["actions_taken"]:
                    print(f"  - {action}")
                
                if result["warnings"]:
                    print("\nWarnings:")
                    for warning in result["warnings"]:
                        print(f"  ⚠️  {warning}")
                
                # Check for conflicts after installation
                if args.check_conflicts:
                    print("\nChecking for conflicts...")
                    conflicts = self.conflict_resolver.detect_active_conflicts()
                    
                    if conflicts:
                        print(f"⚠️  {len(conflicts)} conflict(s) detected")
                        if args.resolve_conflicts:
                            print("Resolving conflicts...")
                            resolution_result = self.conflict_resolver.resolve_all_conflicts()
                            if resolution_result["success"]:
                                print("✅ All conflicts resolved")
                            else:
                                print("❌ Some conflicts could not be resolved")
                    else:
                        print("✅ No conflicts detected")
                
                return 0
            else:
                print(f"❌ Failed to install driver: {args.driver}")
                for error in result["errors"]:
                    print(f"  Error: {error}")
                return 1
        
        except Exception as e:
            print(f"Error installing driver: {e}")
            return 1
    
    def cmd_uninstall_driver(self, args) -> int:
        """Uninstall a wireless driver"""
        if not args.driver:
            print("Error: Driver name required")
            return 1
        
        try:
            print(f"Uninstalling wireless driver: {args.driver}")
            
            result = self.driver_manager.uninstall_driver(args.driver)
            
            if result["success"]:
                print(f"✅ Successfully uninstalled driver: {args.driver}")
                
                for action in result["actions_taken"]:
                    print(f"  - {action}")
                
                return 0
            else:
                print(f"❌ Failed to uninstall driver: {args.driver}")
                for error in result["errors"]:
                    print(f"  Error: {error}")
                return 1
        
        except Exception as e:
            print(f"Error uninstalling driver: {e}")
            return 1
    
    def cmd_firmware_management(self, args) -> int:
        """Manage firmware for wireless drivers"""
        if not args.driver:
            print("Error: Driver name required")
            return 1
        
        try:
            if args.action == "download":
                print(f"Downloading firmware for {args.driver}")
                if args.chipset:
                    print(f"Target chipset: {args.chipset}")
                
                result = self.firmware_automation.download_firmware(
                    args.driver, args.chipset or "default", args.target_dir
                )
                
                if result["success"]:
                    print(f"✅ Successfully downloaded firmware")
                    print(f"  Files: {len(result['downloaded_files'])}")
                    print(f"  Size: {result['total_size']} bytes")
                    print(f"  Time: {result['total_time']:.2f} seconds")
                else:
                    print(f"❌ Failed to download firmware")
                    for error in result["errors"]:
                        print(f"  Error: {error}")
            
            elif args.action == "install":
                print(f"Installing firmware for {args.driver}")
                
                result = self.firmware_automation.install_firmware(args.driver, args.chipset or "default")
                
                if result["success"]:
                    print(f"✅ Successfully installed firmware")
                    for action in result["actions"]:
                        print(f"  - {action}")
                else:
                    print(f"❌ Failed to install firmware")
                    for error in result["errors"]:
                        print(f"  Error: {error}")
            
            elif args.action == "validate":
                print(f"Validating firmware for {args.driver}")
                
                result = self.firmware_automation.validate_firmware(args.driver, args.chipset or "default")
                
                if result["valid"]:
                    print(f"✅ Firmware validation passed")
                    print(f"  Found files: {len(result['found_files'])}")
                else:
                    print(f"❌ Firmware validation failed")
                    if result["missing_files"]:
                        print(f"  Missing files: {', '.join(result['missing_files'])}")
                    for error in result["errors"]:
                        print(f"  Error: {error}")
            
            elif args.action == "cleanup":
                print(f"Cleaning up firmware for {args.driver}")
                
                result = self.firmware_automation.cleanup_firmware(args.driver, args.chipset or "default")
                
                if result["success"]:
                    print(f"✅ Successfully cleaned up firmware")
                    print(f"  Removed files: {len(result['removed_files'])}")
                else:
                    print(f"❌ Failed to cleanup firmware")
                    for error in result["errors"]:
                        print(f"  Error: {error}")
            
            return 0
        
        except Exception as e:
            print(f"Error managing firmware: {e}")
            return 1
    
    def cmd_conflict_management(self, args) -> int:
        """Manage driver conflicts"""
        try:
            if args.action == "detect":
                print("Detecting wireless driver conflicts...")
                
                conflicts = self.conflict_resolver.detect_active_conflicts()
                
                if conflicts:
                    print(f"Detected {len(conflicts)} active conflict(s):")
                    
                    for i, conflict in enumerate(conflicts, 1):
                        rule = conflict["rule"]
                        severity_icons = {
                            "critical": "🚨",
                            "high": "❌",
                            "medium": "⚠️", 
                            "low": "ℹ️"
                        }
                        
                        icon = severity_icons.get(rule.severity.value, "❓")
                        print(f"\n{i}. {icon} {rule.conflict_type.upper()}")
                        print(f"   Drivers: {', '.join(conflict['active_drivers'])}")
                        print(f"   Severity: {rule.severity.value.upper()}")
                        print(f"   Description: {rule.description}")
                        print(f"   Resolution: {rule.resolution_strategy.value}")
                else:
                    print("✅ No conflicts detected")
            
            elif args.action == "resolve":
                print("Resolving wireless driver conflicts...")
                
                result = self.conflict_resolver.resolve_all_conflicts()
                
                if result["success"]:
                    print(f"✅ Successfully resolved all conflicts")
                    print(f"  Conflicts detected: {result['conflicts_detected']}")
                    print(f"  Conflicts resolved: {result['conflicts_resolved']}")
                else:
                    print(f"❌ Could not resolve all conflicts")
                    print(f"  Resolved: {result['conflicts_resolved']}/{result['conflicts_detected']}")
                    for error in result["errors"]:
                        print(f"  Error: {error}")
            
            elif args.action == "report":
                print("Generating conflict resolution report...")
                
                report = self.conflict_resolver.generate_resolution_report(args.output)
                
                if args.output:
                    print(f"Report saved to: {args.output}")
                else:
                    print(report)
            
            return 0
        
        except Exception as e:
            print(f"Error managing conflicts: {e}")
            return 1
    
    def cmd_regulatory_compliance(self, args) -> int:
        """Check regulatory compliance"""
        try:
            if args.action == "check":
                if not args.driver:
                    print("Error: Driver name required for compliance check")
                    return 1
                
                print(f"Checking regulatory compliance for {args.driver}")
                if args.country:
                    print(f"Country/Region: {args.country}")
                
                # Check driver compliance
                result = self.driver_manager.check_regulatory_compliance(args.driver, args.country)
                
                if result["compliant"]:
                    print(f"✅ {args.driver} is regulatory compliant ({result['regulatory_domain']})")
                else:
                    print(f"❌ {args.driver} has compliance issues ({result['regulatory_domain']})")
                    for error in result["errors"]:
                        print(f"  Error: {error}")
                
                for warning in result["warnings"]:
                    print(f"  ⚠️  {warning}")
                
                if result["recommendations"]:
                    print("\nRecommendations:")
                    for rec in result["recommendations"]:
                        print(f"  - {rec}")
            
            elif args.action == "database":
                print("Checking regulatory database status...")
                
                status = self.regulatory_manager.check_regulatory_database()
                
                db_status = "✅" if status["db_exists"] else "❌"
                sig_status = "✅" if status["sig_exists"] else "❌"
                
                print(f"{db_status} regulatory.db ({status['db_size']} bytes)")
                print(f"{sig_status} regulatory.db.p7s ({status['sig_size']} bytes)")
                
                if not status["db_exists"] or not status["sig_exists"]:
                    print("\nTo download regulatory database:")
                    print("  sudo python3 wireless-management-cli.py regulatory download-db")
            
            elif args.action == "download-db":
                print("Downloading regulatory database...")
                
                success = self.regulatory_manager.download_regulatory_database(force=args.force)
                
                if success:
                    print("✅ Successfully downloaded regulatory database")
                else:
                    print("❌ Failed to download regulatory database")
                    return 1
            
            elif args.action == "channels":
                if not args.country:
                    print("Error: Country code required for channel list")
                    return 1
                
                print(f"Available channels in {args.country}:")
                
                channels = self.regulatory_manager.get_channel_list(args.country, args.band or "both")
                
                if channels:
                    current_band = None
                    for channel in channels:
                        if channel["band"] != current_band:
                            current_band = channel["band"]
                            print(f"\n{current_band}:")
                        
                        flags_str = f" ({', '.join(channel['flags'])})" if channel["flags"] else ""
                        print(f"  Channel {channel['channel']:3d}: {channel['frequency']} MHz, "
                              f"Max {channel['max_power']} dBm{flags_str}")
                else:
                    print(f"No channels available for {args.country}")
            
            return 0
        
        except Exception as e:
            print(f"Error checking regulatory compliance: {e}")
            return 1
    
    def cmd_generate_report(self, args) -> int:
        """Generate comprehensive management report"""
        try:
            print("Generating comprehensive wireless management report...")
            
            # Generate driver management report
            driver_report = self.driver_manager.generate_management_report()
            
            # Generate firmware report
            firmware_report = self.firmware_automation.generate_firmware_report()
            
            # Generate conflict resolution report
            conflict_report = self.conflict_resolver.generate_resolution_report()
            
            # Combine reports
            combined_report = f"""
Comprehensive Wireless Management Report
========================================

{driver_report}

{firmware_report}

{conflict_report}
"""
            
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(combined_report)
                print(f"✅ Comprehensive report saved to: {args.output}")
            else:
                print(combined_report)
            
            return 0
        
        except Exception as e:
            print(f"Error generating report: {e}")
            return 1

def create_parser():
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        description="Comprehensive Wireless Driver Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all wireless drivers
  %(prog)s list
  
  # Install ath11k driver for QCA6390 chipset
  %(prog)s install ath11k --chipset QCA6390
  
  # Download firmware for ath11k
  %(prog)s firmware ath11k download --chipset QCA6390
  
  # Check for conflicts and resolve them
  %(prog)s conflicts detect
  %(prog)s conflicts resolve
  
  # Check regulatory compliance
  %(prog)s regulatory check ath11k --country US
  
  # Generate comprehensive report
  %(prog)s report --output wireless-report.txt
"""
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Management commands")
    
    # List drivers command
    list_parser = subparsers.add_parser("list", help="List wireless drivers")
    list_parser.add_argument("--status", choices=["loaded", "installed", "available", "missing"],
                           help="Filter by driver status")
    list_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    # Driver info command
    info_parser = subparsers.add_parser("info", help="Show driver information")
    info_parser.add_argument("driver", help="Driver name")
    
    # Install driver command
    install_parser = subparsers.add_parser("install", help="Install wireless driver")
    install_parser.add_argument("driver", help="Driver name")
    install_parser.add_argument("--chipset", help="Target chipset")
    install_parser.add_argument("--check-conflicts", action="store_true", help="Check for conflicts after install")
    install_parser.add_argument("--resolve-conflicts", action="store_true", help="Auto-resolve conflicts")
    
    # Uninstall driver command
    uninstall_parser = subparsers.add_parser("uninstall", help="Uninstall wireless driver")
    uninstall_parser.add_argument("driver", help="Driver name")
    
    # Firmware management command
    firmware_parser = subparsers.add_parser("firmware", help="Manage firmware")
    firmware_parser.add_argument("driver", help="Driver name")
    firmware_parser.add_argument("action", choices=["download", "install", "validate", "cleanup"],
                               help="Firmware action")
    firmware_parser.add_argument("--chipset", help="Target chipset")
    firmware_parser.add_argument("--target-dir", help="Target directory for download")
    
    # Conflict management command
    conflicts_parser = subparsers.add_parser("conflicts", help="Manage driver conflicts")
    conflicts_parser.add_argument("action", choices=["detect", "resolve", "report"],
                                help="Conflict action")
    conflicts_parser.add_argument("--output", "-o", help="Output file for report")
    
    # Regulatory compliance command
    regulatory_parser = subparsers.add_parser("regulatory", help="Regulatory compliance")
    regulatory_parser.add_argument("action", choices=["check", "database", "download-db", "channels"],
                                 help="Regulatory action")
    regulatory_parser.add_argument("driver", nargs="?", help="Driver name (for check action)")
    regulatory_parser.add_argument("--country", help="Country code")
    regulatory_parser.add_argument("--band", choices=["2.4", "5", "both"], help="Frequency band")
    regulatory_parser.add_argument("--force", action="store_true", help="Force download")
    
    # Report generation command
    report_parser = subparsers.add_parser("report", help="Generate comprehensive report")
    report_parser.add_argument("--output", "-o", help="Output file")
    
    return parser

def main():
    """Main function"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Initialize CLI
    try:
        cli = WirelessManagementCLI()
    except Exception as e:
        print(f"Error initializing wireless management CLI: {e}")
        return 1
    
    # Execute command
    command_map = {
        "list": cli.cmd_list_drivers,
        "info": cli.cmd_driver_info,
        "install": cli.cmd_install_driver,
        "uninstall": cli.cmd_uninstall_driver,
        "firmware": cli.cmd_firmware_management,
        "conflicts": cli.cmd_conflict_management,
        "regulatory": cli.cmd_regulatory_compliance,
        "report": cli.cmd_generate_report
    }
    
    command_func = command_map.get(args.command)
    if command_func:
        return command_func(args)
    else:
        print(f"Unknown command: {args.command}")
        return 1

if __name__ == "__main__":
    sys.exit(main())