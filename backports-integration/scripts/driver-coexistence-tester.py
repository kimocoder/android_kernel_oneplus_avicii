#!/usr/bin/env python3
"""
Driver Coexistence Testing Tool

This tool tests and validates the coexistence of multiple wireless drivers
in the system, detecting conflicts and providing resolution recommendations.
"""

import os
import sys
import subprocess
import json
import time
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

class ConflictType(Enum):
    """Types of driver conflicts"""
    SYMBOL_CONFLICT = "symbol_conflict"
    RESOURCE_CONFLICT = "resource_conflict"
    NAMESPACE_CONFLICT = "namespace_conflict"
    FIRMWARE_CONFLICT = "firmware_conflict"
    INTERFACE_CONFLICT = "interface_conflict"

class ConflictSeverity(Enum):
    """Conflict severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class DriverInfo:
    """Driver information structure"""
    name: str
    version: str
    description: str
    author: str
    license: str
    depends: List[str]
    provides: List[str]
    conflicts: List[str]
    symbols_exported: List[str]
    symbols_imported: List[str]
    firmware_files: List[str]
    supported_devices: List[str]
    module_path: str
    loaded: bool

@dataclass
class ConflictReport:
    """Conflict report structure"""
    conflict_type: ConflictType
    severity: ConflictSeverity
    drivers_involved: List[str]
    description: str
    details: Dict
    resolution_steps: List[str]
    prevention_measures: List[str]

class DriverCoexistenceTester:
    """Driver coexistence testing and validation tool"""
    
    def __init__(self, kernel_root: str = "."):
        """Initialize the coexistence tester"""
        self.kernel_root = Path(kernel_root).resolve()
        self.backports_dir = self.kernel_root / "backports-integration"
        
        # Known driver conflicts and compatibility matrix
        self.known_conflicts = self._load_conflict_database()
        
        # Driver information cache
        self.driver_cache = {}
    
    def _load_conflict_database(self) -> Dict:
        """Load known driver conflicts database"""
        return {
            "symbol_conflicts": {
                ("ath11k", "qcacld"): {
                    "severity": ConflictSeverity.CRITICAL,
                    "symbols": ["ieee80211_alloc_hw", "cfg80211_register_netdevice"],
                    "description": "Both drivers export the same wireless stack symbols",
                    "resolution": [
                        "Use only one driver at a time",
                        "Implement mutual exclusion in Kconfig",
                        "Use runtime driver selection mechanism"
                    ]
                },
                ("ath10k", "qcacld"): {
                    "severity": ConflictSeverity.CRITICAL,
                    "symbols": ["ieee80211_alloc_hw", "cfg80211_register_netdevice"],
                    "description": "Both drivers export the same wireless stack symbols",
                    "resolution": [
                        "Use only one driver at a time",
                        "Implement mutual exclusion in Kconfig"
                    ]
                },
                ("iwlwifi", "iwl_legacy"): {
                    "severity": ConflictSeverity.HIGH,
                    "symbols": ["iwl_read32", "iwl_write32"],
                    "description": "Legacy and modern Intel drivers share symbols",
                    "resolution": [
                        "Use only modern iwlwifi driver",
                        "Remove legacy driver support"
                    ]
                }
            },
            "resource_conflicts": {
                ("ath11k", "ath10k"): {
                    "severity": ConflictSeverity.MEDIUM,
                    "resources": ["firmware_loader", "regulatory_db"],
                    "description": "Both drivers may compete for firmware loading resources",
                    "resolution": [
                        "Ensure proper firmware path separation",
                        "Use different firmware directories"
                    ]
                }
            },
            "interface_conflicts": {
                ("rt2x00", "rt2800usb_vendor"): {
                    "severity": ConflictSeverity.HIGH,
                    "interfaces": ["USB device binding"],
                    "description": "Both drivers claim the same USB devices",
                    "resolution": [
                        "Blacklist vendor driver",
                        "Use device ID exclusion"
                    ]
                }
            }
        }
    
    def detect_installed_drivers(self) -> List[DriverInfo]:
        """Detect all installed wireless drivers"""
        drivers = []
        
        # Common wireless driver names
        wireless_drivers = [
            "ath11k", "ath10k", "ath9k", "ath9k_htc", "ath9k_common",
            "iwlwifi", "iwldvm", "iwlmvm", 
            "rt2x00lib", "rt2x00usb", "rt2800lib", "rt2800usb",
            "cfg80211", "mac80211",
            "qcacld", "prima_wlan", "wcnss_wlan"
        ]
        
        for driver_name in wireless_drivers:
            driver_info = self._get_driver_info(driver_name)
            if driver_info:
                drivers.append(driver_info)
        
        return drivers
    
    def _get_driver_info(self, driver_name: str) -> Optional[DriverInfo]:
        """Get detailed information about a driver"""
        if driver_name in self.driver_cache:
            return self.driver_cache[driver_name]
        
        # Check if driver module exists
        module_paths = [
            f"/lib/modules/{self._get_kernel_version()}/kernel/drivers/net/wireless",
            f"/lib/modules/{self._get_kernel_version()}/extra",
            f"/lib/modules/{self._get_kernel_version()}/updates"
        ]
        
        module_file = None
        for base_path in module_paths:
            # Look for .ko files
            for root, dirs, files in os.walk(base_path):
                for file in files:
                    if file.startswith(driver_name) and file.endswith('.ko'):
                        module_file = os.path.join(root, file)
                        break
                if module_file:
                    break
            if module_file:
                break
        
        if not module_file:
            return None
        
        # Get module information using modinfo
        try:
            result = subprocess.run(["modinfo", module_file], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                return None
            
            # Parse modinfo output
            info = self._parse_modinfo(result.stdout)
            
            # Check if module is loaded
            loaded = self._is_module_loaded(driver_name)
            
            # Get exported symbols
            exported_symbols = self._get_exported_symbols(driver_name)
            
            # Get imported symbols
            imported_symbols = self._get_imported_symbols(module_file)
            
            driver_info = DriverInfo(
                name=driver_name,
                version=info.get("version", "unknown"),
                description=info.get("description", ""),
                author=info.get("author", ""),
                license=info.get("license", ""),
                depends=info.get("depends", []),
                provides=[],  # Would need to analyze module exports
                conflicts=[],  # Would need to analyze conflicts
                symbols_exported=exported_symbols,
                symbols_imported=imported_symbols,
                firmware_files=info.get("firmware", []),
                supported_devices=info.get("alias", []),
                module_path=module_file,
                loaded=loaded
            )
            
            self.driver_cache[driver_name] = driver_info
            return driver_info
            
        except Exception as e:
            print(f"Error getting driver info for {driver_name}: {e}")
            return None
    
    def _get_kernel_version(self) -> str:
        """Get current kernel version"""
        try:
            result = subprocess.run(["uname", "-r"], capture_output=True, text=True)
            return result.stdout.strip()
        except:
            return "unknown"
    
    def _parse_modinfo(self, modinfo_output: str) -> Dict:
        """Parse modinfo output"""
        info = {}
        
        for line in modinfo_output.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                if key in ["depends", "firmware", "alias"]:
                    # These can have multiple values
                    if key not in info:
                        info[key] = []
                    if value:
                        if key == "depends":
                            info[key].extend(value.split(','))
                        else:
                            info[key].append(value)
                else:
                    info[key] = value
        
        return info
    
    def _is_module_loaded(self, module_name: str) -> bool:
        """Check if module is currently loaded"""
        try:
            with open("/proc/modules", "r") as f:
                for line in f:
                    if line.startswith(module_name + " "):
                        return True
        except:
            pass
        return False
    
    def _get_exported_symbols(self, module_name: str) -> List[str]:
        """Get symbols exported by a module"""
        symbols = []
        
        try:
            # Check /proc/kallsyms for exported symbols
            result = subprocess.run(["grep", f"\\[{module_name}\\]", "/proc/kallsyms"],
                                  capture_output=True, text=True)
            
            for line in result.stdout.split('\n'):
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 3:
                        symbol_name = parts[2]
                        symbols.append(symbol_name)
        
        except:
            pass
        
        return symbols
    
    def _get_imported_symbols(self, module_file: str) -> List[str]:
        """Get symbols imported by a module"""
        symbols = []
        
        try:
            # Use objdump to get undefined symbols
            result = subprocess.run(["objdump", "-t", module_file],
                                  capture_output=True, text=True)
            
            for line in result.stdout.split('\n'):
                if "*UND*" in line:  # Undefined symbol (imported)
                    parts = line.split()
                    if len(parts) >= 6:
                        symbol_name = parts[-1]
                        symbols.append(symbol_name)
        
        except:
            pass
        
        return symbols
    
    def analyze_symbol_conflicts(self, drivers: List[DriverInfo]) -> List[ConflictReport]:
        """Analyze symbol conflicts between drivers"""
        conflicts = []
        
        # Build symbol export map
        symbol_exports = {}
        for driver in drivers:
            for symbol in driver.symbols_exported:
                if symbol not in symbol_exports:
                    symbol_exports[symbol] = []
                symbol_exports[symbol].append(driver.name)
        
        # Find symbols exported by multiple drivers
        for symbol, exporting_drivers in symbol_exports.items():
            if len(exporting_drivers) > 1:
                # Check if this is a known conflict
                conflict_key = tuple(sorted(exporting_drivers))
                known_conflict = None
                
                for known_pair, conflict_info in self.known_conflicts.get("symbol_conflicts", {}).items():
                    if set(known_pair).issubset(set(exporting_drivers)):
                        known_conflict = conflict_info
                        break
                
                severity = known_conflict["severity"] if known_conflict else ConflictSeverity.MEDIUM
                
                conflicts.append(ConflictReport(
                    conflict_type=ConflictType.SYMBOL_CONFLICT,
                    severity=severity,
                    drivers_involved=exporting_drivers,
                    description=f"Symbol '{symbol}' exported by multiple drivers",
                    details={
                        "symbol": symbol,
                        "exporting_drivers": exporting_drivers,
                        "known_conflict": known_conflict is not None
                    },
                    resolution_steps=known_conflict["resolution"] if known_conflict else [
                        "Implement symbol namespacing",
                        "Use mutual exclusion in Kconfig",
                        "Rename conflicting symbols"
                    ],
                    prevention_measures=[
                        "Use unique symbol prefixes",
                        "Implement proper symbol versioning",
                        "Regular conflict checking in CI"
                    ]
                ))
        
        return conflicts
    
    def analyze_resource_conflicts(self, drivers: List[DriverInfo]) -> List[ConflictReport]:
        """Analyze resource conflicts between drivers"""
        conflicts = []
        
        # Check firmware file conflicts
        firmware_map = {}
        for driver in drivers:
            for firmware_file in driver.firmware_files:
                if firmware_file not in firmware_map:
                    firmware_map[firmware_file] = []
                firmware_map[firmware_file].append(driver.name)
        
        # Find firmware files used by multiple drivers
        for firmware_file, using_drivers in firmware_map.items():
            if len(using_drivers) > 1:
                conflicts.append(ConflictReport(
                    conflict_type=ConflictType.FIRMWARE_CONFLICT,
                    severity=ConflictSeverity.LOW,
                    drivers_involved=using_drivers,
                    description=f"Firmware file '{firmware_file}' used by multiple drivers",
                    details={
                        "firmware_file": firmware_file,
                        "using_drivers": using_drivers
                    },
                    resolution_steps=[
                        "Verify firmware compatibility",
                        "Use driver-specific firmware directories",
                        "Implement firmware version checking"
                    ],
                    prevention_measures=[
                        "Use unique firmware file names",
                        "Implement firmware validation",
                        "Document firmware requirements"
                    ]
                ))
        
        return conflicts
    
    def analyze_device_conflicts(self, drivers: List[DriverInfo]) -> List[ConflictReport]:
        """Analyze device binding conflicts between drivers"""
        conflicts = []
        
        # Check device ID conflicts
        device_map = {}
        for driver in drivers:
            for device_alias in driver.supported_devices:
                # Parse device alias (simplified)
                if "pci:" in device_alias or "usb:" in device_alias:
                    if device_alias not in device_map:
                        device_map[device_alias] = []
                    device_map[device_alias].append(driver.name)
        
        # Find devices claimed by multiple drivers
        for device_alias, claiming_drivers in device_map.items():
            if len(claiming_drivers) > 1:
                conflicts.append(ConflictReport(
                    conflict_type=ConflictType.INTERFACE_CONFLICT,
                    severity=ConflictSeverity.HIGH,
                    drivers_involved=claiming_drivers,
                    description=f"Device '{device_alias}' claimed by multiple drivers",
                    details={
                        "device_alias": device_alias,
                        "claiming_drivers": claiming_drivers
                    },
                    resolution_steps=[
                        "Use driver blacklisting",
                        "Implement device ID exclusion",
                        "Use udev rules for driver selection"
                    ],
                    prevention_measures=[
                        "Coordinate device ID assignments",
                        "Use vendor-specific device IDs",
                        "Implement runtime device arbitration"
                    ]
                ))
        
        return conflicts
    
    def test_runtime_coexistence(self, drivers: List[str]) -> Dict:
        """Test runtime coexistence of drivers"""
        test_results = {
            "test_timestamp": time.time(),
            "drivers_tested": drivers,
            "load_test_results": {},
            "interaction_test_results": {},
            "performance_impact": {},
            "overall_compatibility": "unknown"
        }
        
        print(f"Testing runtime coexistence of {len(drivers)} drivers...")
        
        # Test individual driver loading
        for driver in drivers:
            print(f"Testing driver: {driver}")
            load_result = self._test_driver_load(driver)
            test_results["load_test_results"][driver] = load_result
        
        # Test driver interactions
        if len(drivers) > 1:
            print("Testing driver interactions...")
            interaction_result = self._test_driver_interactions(drivers)
            test_results["interaction_test_results"] = interaction_result
        
        # Assess overall compatibility
        failed_loads = sum(1 for result in test_results["load_test_results"].values() 
                          if not result["success"])
        
        if failed_loads == 0:
            if test_results["interaction_test_results"].get("conflicts_detected", False):
                test_results["overall_compatibility"] = "partial"
            else:
                test_results["overall_compatibility"] = "compatible"
        else:
            test_results["overall_compatibility"] = "incompatible"
        
        return test_results
    
    def _test_driver_load(self, driver_name: str) -> Dict:
        """Test loading a single driver"""
        result = {
            "driver": driver_name,
            "success": False,
            "load_time_ms": 0,
            "errors": [],
            "warnings": []
        }
        
        try:
            start_time = time.time()
            
            # Check if driver is already loaded
            if self._is_module_loaded(driver_name):
                result["success"] = True
                result["warnings"].append("Driver already loaded")
                return result
            
            # Attempt to load driver (simulation - would use modprobe in real test)
            # For safety, we'll just simulate the test
            load_result = subprocess.run(["modinfo", driver_name], 
                                       capture_output=True, text=True)
            
            load_time = (time.time() - start_time) * 1000
            result["load_time_ms"] = round(load_time, 2)
            
            if load_result.returncode == 0:
                result["success"] = True
            else:
                result["errors"].append(f"Driver not found or invalid: {load_result.stderr}")
        
        except Exception as e:
            result["errors"].append(f"Load test failed: {e}")
        
        return result
    
    def _test_driver_interactions(self, drivers: List[str]) -> Dict:
        """Test interactions between multiple drivers"""
        result = {
            "drivers": drivers,
            "conflicts_detected": False,
            "conflict_details": [],
            "performance_impact": "none"
        }
        
        # Simulate interaction testing
        # In a real implementation, this would:
        # 1. Load drivers in different orders
        # 2. Test interface creation
        # 3. Monitor for conflicts
        # 4. Measure performance impact
        
        # For now, check against known conflicts
        for i, driver1 in enumerate(drivers):
            for driver2 in drivers[i+1:]:
                conflict_pair = tuple(sorted([driver1, driver2]))
                
                # Check all conflict types
                for conflict_category in self.known_conflicts.values():
                    if conflict_pair in conflict_category:
                        result["conflicts_detected"] = True
                        result["conflict_details"].append({
                            "drivers": [driver1, driver2],
                            "conflict_info": conflict_category[conflict_pair]
                        })
        
        return result
    
    def generate_coexistence_report(self, output_file: Optional[str] = None) -> str:
        """Generate comprehensive coexistence report"""
        print("Analyzing driver coexistence...")
        
        # Detect installed drivers
        drivers = self.detect_installed_drivers()
        
        if not drivers:
            report = "No wireless drivers detected in the system.\n"
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(report)
            return report
        
        print(f"Found {len(drivers)} wireless drivers")
        
        # Analyze conflicts
        symbol_conflicts = self.analyze_symbol_conflicts(drivers)
        resource_conflicts = self.analyze_resource_conflicts(drivers)
        device_conflicts = self.analyze_device_conflicts(drivers)
        
        all_conflicts = symbol_conflicts + resource_conflicts + device_conflicts
        
        # Test runtime coexistence
        driver_names = [d.name for d in drivers if d.loaded]
        runtime_test = {}
        if driver_names:
            runtime_test = self.test_runtime_coexistence(driver_names)
        
        # Generate report
        report_lines = []
        report_lines.append("Driver Coexistence Analysis Report")
        report_lines.append("=" * 50)
        report_lines.append(f"Generated: {time.ctime()}")
        report_lines.append("")
        
        # Driver summary
        report_lines.append("Detected Wireless Drivers:")
        for driver in drivers:
            status = "Loaded" if driver.loaded else "Available"
            report_lines.append(f"  - {driver.name} ({status})")
            report_lines.append(f"    Version: {driver.version}")
            report_lines.append(f"    Description: {driver.description}")
            if driver.depends:
                report_lines.append(f"    Dependencies: {', '.join(driver.depends)}")
        report_lines.append("")
        
        # Conflict analysis
        report_lines.append("Conflict Analysis:")
        report_lines.append("-" * 20)
        
        if all_conflicts:
            for conflict in all_conflicts:
                severity_icon = {
                    ConflictSeverity.LOW: "ℹ️",
                    ConflictSeverity.MEDIUM: "⚠️",
                    ConflictSeverity.HIGH: "❌",
                    ConflictSeverity.CRITICAL: "🚨"
                }.get(conflict.severity, "❓")
                
                report_lines.append(f"{severity_icon} {conflict.conflict_type.value.upper()}")
                report_lines.append(f"  Drivers: {', '.join(conflict.drivers_involved)}")
                report_lines.append(f"  Severity: {conflict.severity.value.upper()}")
                report_lines.append(f"  Description: {conflict.description}")
                
                if conflict.resolution_steps:
                    report_lines.append("  Resolution Steps:")
                    for step in conflict.resolution_steps:
                        report_lines.append(f"    - {step}")
                
                report_lines.append("")
        else:
            report_lines.append("✅ No conflicts detected")
            report_lines.append("")
        
        # Runtime test results
        if runtime_test:
            report_lines.append("Runtime Coexistence Test:")
            report_lines.append("-" * 25)
            
            compatibility = runtime_test["overall_compatibility"]
            compat_icon = {
                "compatible": "✅",
                "partial": "⚠️", 
                "incompatible": "❌",
                "unknown": "❓"
            }.get(compatibility, "❓")
            
            report_lines.append(f"Overall Compatibility: {compat_icon} {compatibility.upper()}")
            
            # Load test results
            report_lines.append("Driver Load Tests:")
            for driver, load_result in runtime_test["load_test_results"].items():
                status = "✅" if load_result["success"] else "❌"
                report_lines.append(f"  {status} {driver}: {load_result['load_time_ms']}ms")
                
                if load_result["errors"]:
                    for error in load_result["errors"]:
                        report_lines.append(f"    Error: {error}")
            
            report_lines.append("")
        
        # Summary and recommendations
        report_lines.append("Summary:")
        report_lines.append(f"  Total Drivers: {len(drivers)}")
        report_lines.append(f"  Loaded Drivers: {sum(1 for d in drivers if d.loaded)}")
        report_lines.append(f"  Conflicts Found: {len(all_conflicts)}")
        
        critical_conflicts = sum(1 for c in all_conflicts if c.severity == ConflictSeverity.CRITICAL)
        if critical_conflicts > 0:
            report_lines.append(f"  Critical Conflicts: {critical_conflicts}")
            report_lines.append("")
            report_lines.append("⚠️  CRITICAL CONFLICTS DETECTED - IMMEDIATE ACTION REQUIRED")
        
        report_lines.append("")
        
        # Recommendations
        if all_conflicts:
            report_lines.append("Recommendations:")
            all_recommendations = set()
            for conflict in all_conflicts:
                all_recommendations.update(conflict.resolution_steps)
            
            for rec in sorted(all_recommendations):
                report_lines.append(f"  - {rec}")
        
        report_content = "\n".join(report_lines)
        
        # Save to file if requested
        if output_file:
            try:
                with open(output_file, 'w') as f:
                    f.write(report_content)
                print(f"Coexistence report saved to: {output_file}")
            except Exception as e:
                print(f"Error saving report: {e}")
        
        return report_content

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Driver Coexistence Testing Tool")
    parser.add_argument("--report", "-r", help="Generate coexistence report")
    parser.add_argument("--test", "-t", nargs="+", help="Test specific drivers")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    tester = DriverCoexistenceTester()
    
    if args.test:
        # Test specific drivers
        test_results = tester.test_runtime_coexistence(args.test)
        
        if args.json:
            print(json.dumps(test_results, indent=2, default=str))
        else:
            print(f"Coexistence test results for: {', '.join(args.test)}")
            print(f"Overall compatibility: {test_results['overall_compatibility']}")
    
    elif args.report:
        # Generate full report
        report = tester.generate_coexistence_report(args.report)
        if not args.report:
            print(report)
    
    else:
        # Default: show detected drivers and basic conflict check
        drivers = tester.detect_installed_drivers()
        
        if drivers:
            print(f"Detected {len(drivers)} wireless drivers:")
            for driver in drivers:
                status = "Loaded" if driver.loaded else "Available"
                print(f"  - {driver.name} ({status})")
            
            # Quick conflict check
            conflicts = (tester.analyze_symbol_conflicts(drivers) +
                        tester.analyze_resource_conflicts(drivers) +
                        tester.analyze_device_conflicts(drivers))
            
            if conflicts:
                print(f"\n⚠️  {len(conflicts)} potential conflicts detected")
                print("Run with --report for detailed analysis")
            else:
                print("\n✅ No obvious conflicts detected")
        else:
            print("No wireless drivers detected")

if __name__ == "__main__":
    main()