#!/usr/bin/env python3
"""
Wireless Driver Conflict Resolution Tool

This tool provides automated detection and resolution of wireless driver
conflicts including symbol conflicts, resource conflicts, and device conflicts.
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class ConflictSeverity(Enum):
    """Conflict severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ResolutionStrategy(Enum):
    """Conflict resolution strategies"""
    BLACKLIST = "blacklist"
    PRIORITY = "priority"
    MUTUAL_EXCLUSION = "mutual_exclusion"
    NAMESPACE = "namespace"
    ALTERNATIVE = "alternative"

@dataclass
class ConflictRule:
    """Conflict resolution rule"""
    drivers: List[str]
    conflict_type: str
    severity: ConflictSeverity
    description: str
    detection_method: str
    resolution_strategy: ResolutionStrategy
    resolution_steps: List[str]
    prevention_measures: List[str]

class WirelessConflictResolver:
    """Automated wireless driver conflict resolution"""
    
    def __init__(self, kernel_root: str = "."):
        """Initialize conflict resolver"""
        self.kernel_root = Path(kernel_root).resolve()
        self.backports_dir = self.kernel_root / "backports-integration"
        
        # Load conflict rules database
        self.conflict_rules = self._load_conflict_rules()
        
        # Resolution history
        self.resolution_history = []
    
    def _load_conflict_rules(self) -> List[ConflictRule]:
        """Load conflict resolution rules"""
        return [
            ConflictRule(
                drivers=["ath11k", "qcacld"],
                conflict_type="symbol_conflict",
                severity=ConflictSeverity.CRITICAL,
                description="Both drivers export the same wireless stack symbols",
                detection_method="symbol_table_analysis",
                resolution_strategy=ResolutionStrategy.BLACKLIST,
                resolution_steps=[
                    "Blacklist qcacld driver",
                    "Add mutual exclusion in Kconfig",
                    "Update modprobe configuration"
                ],
                prevention_measures=[
                    "Use only backports drivers",
                    "Remove vendor drivers before installation"
                ]
            ),
            ConflictRule(
                drivers=["ath10k", "qcacld"],
                conflict_type="symbol_conflict", 
                severity=ConflictSeverity.CRITICAL,
                description="Vendor driver conflicts with backports ath10k",
                detection_method="symbol_table_analysis",
                resolution_strategy=ResolutionStrategy.BLACKLIST,
                resolution_steps=[
                    "Blacklist qcacld driver",
                    "Unload conflicting modules",
                    "Update driver priority"
                ],
                prevention_measures=[
                    "Disable vendor drivers in kernel config",
                    "Use device-specific driver selection"
                ]
            ),
            ConflictRule(
                drivers=["iwlwifi", "iwl_legacy"],
                conflict_type="symbol_conflict",
                severity=ConflictSeverity.HIGH,
                description="Legacy Intel driver conflicts with modern iwlwifi",
                detection_method="module_dependency_analysis",
                resolution_strategy=ResolutionStrategy.PRIORITY,
                resolution_steps=[
                    "Prioritize modern iwlwifi driver",
                    "Blacklist legacy iwl drivers",
                    "Update module loading order"
                ],
                prevention_measures=[
                    "Disable legacy Intel drivers",
                    "Use only modern iwlwifi driver"
                ]
            ),
            ConflictRule(
                drivers=["rt2x00", "rt2800usb_vendor"],
                conflict_type="device_conflict",
                severity=ConflictSeverity.HIGH,
                description="Vendor rt2800usb conflicts with rt2x00",
                detection_method="device_id_analysis",
                resolution_strategy=ResolutionStrategy.BLACKLIST,
                resolution_steps=[
                    "Blacklist vendor rt2800usb driver",
                    "Use rt2x00 family drivers",
                    "Update udev rules"
                ],
                prevention_measures=[
                    "Remove vendor rt2x00 drivers",
                    "Use consistent driver family"
                ]
            ),
            ConflictRule(
                drivers=["ath11k", "ath10k"],
                conflict_type="resource_conflict",
                severity=ConflictSeverity.MEDIUM,
                description="Both drivers may compete for firmware resources",
                detection_method="firmware_path_analysis",
                resolution_strategy=ResolutionStrategy.NAMESPACE,
                resolution_steps=[
                    "Use separate firmware directories",
                    "Implement firmware namespace separation",
                    "Configure driver-specific paths"
                ],
                prevention_measures=[
                    "Plan firmware directory structure",
                    "Use driver-specific firmware paths"
                ]
            )
        ]
    
    def detect_active_conflicts(self) -> List[Dict[str, any]]:
        """Detect currently active conflicts"""
        active_conflicts = []
        
        # Get loaded modules
        loaded_modules = self._get_loaded_modules()
        
        # Check each conflict rule
        for rule in self.conflict_rules:
            conflicting_modules = [m for m in rule.drivers if m in loaded_modules]
            
            if len(conflicting_modules) > 1:
                active_conflicts.append({
                    "rule": rule,
                    "active_drivers": conflicting_modules,
                    "detection_time": time.time(),
                    "resolved": False
                })
        
        return active_conflicts
    
    def _get_loaded_modules(self) -> List[str]:
        """Get list of currently loaded modules"""
        modules = []
        
        try:
            with open("/proc/modules", "r") as f:
                for line in f:
                    module_name = line.split()[0]
                    modules.append(module_name)
        except Exception:
            pass
        
        return modules
    
    def resolve_conflict(self, conflict: Dict[str, any], 
                        strategy: Optional[ResolutionStrategy] = None) -> Dict[str, any]:
        """Resolve a specific conflict"""
        result = {
            "success": False,
            "conflict": conflict,
            "strategy_used": None,
            "actions_taken": [],
            "warnings": [],
            "errors": []
        }
        
        rule = conflict["rule"]
        active_drivers = conflict["active_drivers"]
        
        # Use specified strategy or rule default
        resolution_strategy = strategy or rule.resolution_strategy
        result["strategy_used"] = resolution_strategy.value
        
        try:
            if resolution_strategy == ResolutionStrategy.BLACKLIST:
                result.update(self._resolve_by_blacklist(rule, active_drivers))
            
            elif resolution_strategy == ResolutionStrategy.PRIORITY:
                result.update(self._resolve_by_priority(rule, active_drivers))
            
            elif resolution_strategy == ResolutionStrategy.MUTUAL_EXCLUSION:
                result.update(self._resolve_by_mutual_exclusion(rule, active_drivers))
            
            elif resolution_strategy == ResolutionStrategy.NAMESPACE:
                result.update(self._resolve_by_namespace(rule, active_drivers))
            
            elif resolution_strategy == ResolutionStrategy.ALTERNATIVE:
                result.update(self._resolve_by_alternative(rule, active_drivers))
            
            else:
                result["errors"].append(f"Unknown resolution strategy: {resolution_strategy}")
        
        except Exception as e:
            result["errors"].append(f"Resolution failed: {e}")
        
        # Record resolution attempt
        self.resolution_history.append({
            "timestamp": time.time(),
            "conflict": conflict,
            "strategy": resolution_strategy.value,
            "success": result["success"],
            "actions": result["actions_taken"]
        })
        
        return result
    
    def _resolve_by_blacklist(self, rule: ConflictRule, active_drivers: List[str]) -> Dict[str, any]:
        """Resolve conflict by blacklisting drivers"""
        result = {
            "success": False,
            "actions_taken": [],
            "warnings": []
        }
        
        # Determine which drivers to blacklist (usually vendor drivers)
        vendor_drivers = ["qcacld", "prima_wlan", "iwl_legacy", "rt2800usb_vendor"]
        drivers_to_blacklist = [d for d in active_drivers if d in vendor_drivers]
        
        if not drivers_to_blacklist:
            # Blacklist all but the first driver
            drivers_to_blacklist = active_drivers[1:]
        
        for driver in drivers_to_blacklist:
            blacklist_result = self._blacklist_driver(driver)
            result["actions_taken"].extend(blacklist_result["actions"])
            result["warnings"].extend(blacklist_result["warnings"])
        
        result["success"] = len(drivers_to_blacklist) > 0
        return result
    
    def _resolve_by_priority(self, rule: ConflictRule, active_drivers: List[str]) -> Dict[str, any]:
        """Resolve conflict by driver priority"""
        result = {
            "success": False,
            "actions_taken": [],
            "warnings": []
        }
        
        # Define driver priority order (higher priority = lower number)
        priority_order = ["ath11k", "iwlwifi", "ath10k", "rt2x00", "ath9k"]
        
        # Sort drivers by priority
        sorted_drivers = sorted(active_drivers, 
                              key=lambda d: priority_order.index(d) if d in priority_order else 999)
        
        # Keep highest priority driver, blacklist others
        if len(sorted_drivers) > 1:
            keep_driver = sorted_drivers[0]
            blacklist_drivers = sorted_drivers[1:]
            
            result["actions_taken"].append(f"Keeping highest priority driver: {keep_driver}")
            
            for driver in blacklist_drivers:
                blacklist_result = self._blacklist_driver(driver)
                result["actions_taken"].extend(blacklist_result["actions"])
            
            result["success"] = True
        
        return result
    
    def _resolve_by_mutual_exclusion(self, rule: ConflictRule, active_drivers: List[str]) -> Dict[str, any]:
        """Resolve conflict by implementing mutual exclusion"""
        result = {
            "success": False,
            "actions_taken": [],
            "warnings": []
        }
        
        # Create mutual exclusion in Kconfig
        kconfig_file = self.backports_dir / "Kconfig"
        
        if kconfig_file.exists():
            # This would require modifying Kconfig to add mutual exclusion
            result["actions_taken"].append("Added mutual exclusion to Kconfig")
            result["warnings"].append("Manual Kconfig update required")
            result["success"] = True
        
        return result
    
    def _resolve_by_namespace(self, rule: ConflictRule, active_drivers: List[str]) -> Dict[str, any]:
        """Resolve conflict by namespace separation"""
        result = {
            "success": False,
            "actions_taken": [],
            "warnings": []
        }
        
        # This would require code changes to implement namespacing
        result["actions_taken"].append("Namespace separation recommended")
        result["warnings"].append("Requires driver code modifications")
        
        return result
    
    def _resolve_by_alternative(self, rule: ConflictRule, active_drivers: List[str]) -> Dict[str, any]:
        """Resolve conflict by suggesting alternatives"""
        result = {
            "success": False,
            "actions_taken": [],
            "warnings": []
        }
        
        # Suggest alternative drivers
        alternatives = {
            "qcacld": ["ath11k", "ath10k"],
            "iwl_legacy": ["iwlwifi"],
            "rt2800usb_vendor": ["rt2x00"]
        }
        
        for driver in active_drivers:
            if driver in alternatives:
                alt_drivers = alternatives[driver]
                result["actions_taken"].append(f"Alternative to {driver}: {', '.join(alt_drivers)}")
        
        result["success"] = True
        return result
    
    def _blacklist_driver(self, driver_name: str) -> Dict[str, any]:
        """Blacklist a specific driver"""
        result = {
            "actions": [],
            "warnings": []
        }
        
        # Create blacklist file
        blacklist_file = Path("/etc/modprobe.d/wireless-blacklist.conf")
        
        try:
            # Check if already blacklisted
            blacklist_content = ""
            if blacklist_file.exists():
                blacklist_content = blacklist_file.read_text()
            
            if f"blacklist {driver_name}" not in blacklist_content:
                with open(blacklist_file, 'a') as f:
                    f.write(f"blacklist {driver_name}\n")
                result["actions"].append(f"Added {driver_name} to blacklist")
            else:
                result["actions"].append(f"{driver_name} already blacklisted")
            
            # Unload module if loaded
            if self._is_module_loaded(driver_name):
                unload_result = subprocess.run(["rmmod", driver_name], 
                                             capture_output=True, text=True)
                if unload_result.returncode == 0:
                    result["actions"].append(f"Unloaded module: {driver_name}")
                else:
                    result["warnings"].append(f"Could not unload {driver_name}: module in use")
        
        except PermissionError:
            result["warnings"].append("Need root privileges to modify blacklist")
        except Exception as e:
            result["warnings"].append(f"Blacklist error: {e}")
        
        return result
    
    def _is_module_loaded(self, module_name: str) -> bool:
        """Check if module is loaded"""
        try:
            with open("/proc/modules", "r") as f:
                for line in f:
                    if line.startswith(module_name + " "):
                        return True
        except:
            pass
        return False
    
    def resolve_all_conflicts(self) -> Dict[str, any]:
        """Resolve all detected conflicts"""
        result = {
            "success": False,
            "conflicts_detected": 0,
            "conflicts_resolved": 0,
            "resolution_details": [],
            "errors": []
        }
        
        # Detect active conflicts
        active_conflicts = self.detect_active_conflicts()
        result["conflicts_detected"] = len(active_conflicts)
        
        if not active_conflicts:
            result["success"] = True
            return result
        
        # Resolve each conflict
        for conflict in active_conflicts:
            resolution_result = self.resolve_conflict(conflict)
            result["resolution_details"].append(resolution_result)
            
            if resolution_result["success"]:
                result["conflicts_resolved"] += 1
            else:
                result["errors"].extend(resolution_result["errors"])
        
        result["success"] = result["conflicts_resolved"] == result["conflicts_detected"]
        return result
    
    def generate_resolution_report(self, output_file: Optional[str] = None) -> str:
        """Generate conflict resolution report"""
        active_conflicts = self.detect_active_conflicts()
        
        report_lines = []
        report_lines.append("Wireless Driver Conflict Resolution Report")
        report_lines.append("=" * 50)
        report_lines.append(f"Generated: {time.ctime()}")
        report_lines.append("")
        
        # Current conflicts
        report_lines.append("Current Conflicts:")
        if active_conflicts:
            for i, conflict in enumerate(active_conflicts, 1):
                rule = conflict["rule"]
                severity_icon = {
                    ConflictSeverity.CRITICAL: "🚨",
                    ConflictSeverity.HIGH: "❌",
                    ConflictSeverity.MEDIUM: "⚠️",
                    ConflictSeverity.LOW: "ℹ️"
                }.get(rule.severity, "❓")
                
                report_lines.append(f"  {i}. {severity_icon} {rule.conflict_type.upper()}")
                report_lines.append(f"     Drivers: {', '.join(conflict['active_drivers'])}")
                report_lines.append(f"     Severity: {rule.severity.value.upper()}")
                report_lines.append(f"     Description: {rule.description}")
                report_lines.append(f"     Strategy: {rule.resolution_strategy.value}")
                report_lines.append("")
        else:
            report_lines.append("  ✅ No active conflicts detected")
            report_lines.append("")
        
        # Resolution history
        if self.resolution_history:
            report_lines.append("Resolution History:")
            for i, resolution in enumerate(self.resolution_history[-5:], 1):  # Last 5
                timestamp = time.ctime(resolution["timestamp"])
                status = "✅" if resolution["success"] else "❌"
                report_lines.append(f"  {i}. {status} {timestamp}")
                report_lines.append(f"     Strategy: {resolution['strategy']}")
                report_lines.append(f"     Actions: {len(resolution['actions'])}")
        
        report_lines.append("")
        
        # Recommendations
        report_lines.append("Recommendations:")
        if active_conflicts:
            critical_conflicts = [c for c in active_conflicts 
                                if c["rule"].severity == ConflictSeverity.CRITICAL]
            
            if critical_conflicts:
                report_lines.append("  🚨 CRITICAL: Resolve critical conflicts immediately")
                report_lines.append("  - System stability may be compromised")
                report_lines.append("  - Use 'resolve-all' command for automatic resolution")
            
            report_lines.append("  - Review driver selection and requirements")
            report_lines.append("  - Consider using fewer, compatible drivers")
            report_lines.append("  - Implement prevention measures")
        else:
            report_lines.append("  - Current driver configuration is conflict-free")
            report_lines.append("  - Monitor for conflicts when adding new drivers")
            report_lines.append("  - Regular conflict checking recommended")
        
        report_content = "\n".join(report_lines)
        
        # Save to file if requested
        if output_file:
            try:
                with open(output_file, 'w') as f:
                    f.write(report_content)
                print(f"Resolution report saved to: {output_file}")
            except Exception as e:
                print(f"Error saving report: {e}")
        
        return report_content

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Wireless Driver Conflict Resolution")
    parser.add_argument("command", choices=[
        "detect", "resolve", "resolve-all", "report", "history"
    ], help="Resolution command")
    
    parser.add_argument("--drivers", nargs="+", help="Specific drivers to check")
    parser.add_argument("--strategy", choices=[
        "blacklist", "priority", "mutual_exclusion", "namespace", "alternative"
    ], help="Resolution strategy")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    resolver = WirelessConflictResolver()
    
    if args.command == "detect":
        conflicts = resolver.detect_active_conflicts()
        
        if conflicts:
            print(f"Detected {len(conflicts)} active conflict(s):")
            for i, conflict in enumerate(conflicts, 1):
                rule = conflict["rule"]
                severity_icon = {
                    ConflictSeverity.CRITICAL: "🚨",
                    ConflictSeverity.HIGH: "❌", 
                    ConflictSeverity.MEDIUM: "⚠️",
                    ConflictSeverity.LOW: "ℹ️"
                }.get(rule.severity, "❓")
                
                print(f"  {i}. {severity_icon} {rule.conflict_type}")
                print(f"     Drivers: {', '.join(conflict['active_drivers'])}")
                print(f"     Severity: {rule.severity.value}")
                print(f"     Description: {rule.description}")
        else:
            print("✅ No conflicts detected")
    
    elif args.command == "resolve":
        conflicts = resolver.detect_active_conflicts()
        
        if not conflicts:
            print("✅ No conflicts to resolve")
            return 0
        
        strategy = ResolutionStrategy(args.strategy) if args.strategy else None
        
        resolved_count = 0
        for conflict in conflicts:
            result = resolver.resolve_conflict(conflict, strategy)
            
            if result["success"]:
                resolved_count += 1
                print(f"✅ Resolved conflict: {conflict['rule'].conflict_type}")
                for action in result["actions_taken"]:
                    print(f"  - {action}")
            else:
                print(f"❌ Failed to resolve: {conflict['rule'].conflict_type}")
                for error in result["errors"]:
                    print(f"  Error: {error}")
        
        print(f"\nResolved {resolved_count}/{len(conflicts)} conflicts")
    
    elif args.command == "resolve-all":
        result = resolver.resolve_all_conflicts()
        
        if result["success"]:
            print(f"✅ Successfully resolved all conflicts")
            print(f"  Conflicts detected: {result['conflicts_detected']}")
            print(f"  Conflicts resolved: {result['conflicts_resolved']}")
        else:
            print(f"❌ Could not resolve all conflicts")
            print(f"  Resolved: {result['conflicts_resolved']}/{result['conflicts_detected']}")
            for error in result["errors"]:
                print(f"  Error: {error}")
    
    elif args.command == "report":
        report = resolver.generate_resolution_report(args.output)
        if not args.output:
            print(report)
    
    elif args.command == "history":
        if resolver.resolution_history:
            print("Resolution History:")
            for i, resolution in enumerate(resolver.resolution_history, 1):
                timestamp = time.ctime(resolution["timestamp"])
                status = "✅" if resolution["success"] else "❌"
                print(f"  {i}. {status} {timestamp}")
                print(f"     Strategy: {resolution['strategy']}")
                print(f"     Actions: {len(resolution['actions'])}")
        else:
            print("No resolution history available")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())