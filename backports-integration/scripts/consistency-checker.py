#!/usr/bin/env python3
"""
Backports Configuration Consistency Checker

Implements pre-build validation, consistency checks between backports and kernel options,
and runtime validation during configuration changes.
"""

import os
import sys
import re
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum
import argparse
import time

class ConsistencyLevel(Enum):
    """Consistency check severity levels"""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

@dataclass
class ConsistencyIssue:
    """Represents a configuration consistency issue"""
    level: ConsistencyLevel
    category: str
    description: str
    affected_options: List[str]
    resolution_steps: List[str]
    auto_fixable: bool = False
    fix_command: Optional[str] = None

class ConfigurationState:
    """Represents the current configuration state"""
    
    def __init__(self, config_file: str):
        self.config_file = Path(config_file)
        self.options: Dict[str, str] = {}
        self.timestamp = 0
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        if not self.config_file.exists():
            return
        
        self.timestamp = self.config_file.stat().st_mtime
        self.options.clear()
        
        with open(self.config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#') or not line or '=' not in line:
                    continue
                
                try:
                    key, value = line.split('=', 1)
                    self.options[key] = value
                except ValueError:
                    continue
    
    def is_modified(self) -> bool:
        """Check if configuration file has been modified"""
        if not self.config_file.exists():
            return False
        
        return self.config_file.stat().st_mtime > self.timestamp
    
    def get_value(self, option: str) -> Optional[str]:
        """Get option value"""
        return self.options.get(option)
    
    def is_enabled(self, option: str) -> bool:
        """Check if option is enabled (y or m)"""
        value = self.get_value(option)
        return value in ['y', 'm']
    
    def get_enabled_options(self, prefix: str = "") -> List[str]:
        """Get all enabled options with optional prefix filter"""
        enabled = []
        for option, value in self.options.items():
            if value in ['y', 'm'] and option.startswith(prefix):
                enabled.append(option)
        return enabled

class BackportsConsistencyChecker:
    """Comprehensive configuration consistency checker"""
    
    def __init__(self, kernel_root: str = "."):
        self.kernel_root = Path(kernel_root).resolve()
        self.config_state = ConfigurationState(self.kernel_root / ".config")
        self.issues: List[ConsistencyIssue] = []
        
        # Define consistency rules
        self.consistency_rules = self._build_consistency_rules()
        self.dependency_graph = self._build_dependency_graph()
        self.conflict_matrix = self._build_conflict_matrix()
        
    def _build_consistency_rules(self) -> Dict[str, Dict[str, Any]]:
        """Build comprehensive consistency rules"""
        return {
            # Core backports consistency
            "backports_core_consistency": {
                "description": "Core backports options must be consistent",
                "check_function": "check_backports_core_consistency",
                "critical": True
            },
            
            # Wireless stack consistency
            "wireless_stack_consistency": {
                "description": "Only one wireless stack can be active",
                "check_function": "check_wireless_stack_consistency",
                "critical": True
            },
            
            # Dependency consistency
            "dependency_consistency": {
                "description": "All dependencies must be satisfied",
                "check_function": "check_dependency_consistency",
                "critical": True
            },
            
            # Security consistency
            "security_consistency": {
                "description": "Security-sensitive features must have proper safeguards",
                "check_function": "check_security_consistency",
                "critical": False
            },
            
            # Performance consistency
            "performance_consistency": {
                "description": "Performance-impacting options should be reviewed",
                "check_function": "check_performance_consistency",
                "critical": False
            },
            
            # Android compatibility consistency
            "android_consistency": {
                "description": "Android-specific options must be compatible",
                "check_function": "check_android_consistency",
                "critical": True
            },
            
            # Build system consistency
            "build_consistency": {
                "description": "Build system configuration must be consistent",
                "check_function": "check_build_consistency",
                "critical": True
            },
            
            # Module consistency
            "module_consistency": {
                "description": "Module configuration must be consistent",
                "check_function": "check_module_consistency",
                "critical": False
            }
        }
    
    def _build_dependency_graph(self) -> Dict[str, List[str]]:
        """Build dependency graph for backports options"""
        return {
            "CONFIG_BACKPORTS": [
                "CONFIG_MODULES",
                "CONFIG_NET"
            ],
            "CONFIG_BACKPORTS_CFG80211": [
                "CONFIG_BACKPORTS",
                "CONFIG_RFKILL",
                "CONFIG_CRYPTO"
            ],
            "CONFIG_BACKPORTS_MAC80211": [
                "CONFIG_BACKPORTS_CFG80211",
                "CONFIG_CRYPTO_ARC4",
                "CONFIG_CRYPTO_AES",
                "CONFIG_CRC32"
            ],
            "CONFIG_BACKPORTS_MONITOR_MODE": [
                "CONFIG_BACKPORTS_MAC80211",
                "CONFIG_PACKET"
            ],
            "CONFIG_BACKPORTS_FRAME_INJECTION": [
                "CONFIG_BACKPORTS_MONITOR_MODE",
                "CONFIG_PACKET_MMAP"
            ],
            "CONFIG_BACKPORTS_ANDROID": [
                "CONFIG_BACKPORTS",
                "CONFIG_ANDROID"
            ],
            "CONFIG_BACKPORTS_DEBUG": [
                "CONFIG_BACKPORTS",
                "CONFIG_DEBUG_KERNEL"
            ]
        }
    
    def _build_conflict_matrix(self) -> Dict[str, List[str]]:
        """Build conflict matrix for incompatible options"""
        return {
            "CONFIG_BACKPORTS": [
                "CONFIG_CFG80211",
                "CONFIG_MAC80211"
            ],
            "CONFIG_BACKPORTS_CFG80211": [
                "CONFIG_CFG80211"
            ],
            "CONFIG_BACKPORTS_MAC80211": [
                "CONFIG_MAC80211"
            ],
            "CONFIG_BACKPORTS_ANDROID": [
                "CONFIG_QCACLD",
                "CONFIG_PRIMA_WLAN",
                "CONFIG_WCNSS_CORE"
            ]
        }
    
    def add_issue(self, level: ConsistencyLevel, category: str, description: str,
                  affected_options: List[str], resolution_steps: List[str],
                  auto_fixable: bool = False, fix_command: Optional[str] = None):
        """Add a consistency issue"""
        issue = ConsistencyIssue(
            level=level,
            category=category,
            description=description,
            affected_options=affected_options,
            resolution_steps=resolution_steps,
            auto_fixable=auto_fixable,
            fix_command=fix_command
        )
        self.issues.append(issue)
    
    def check_backports_core_consistency(self) -> bool:
        """Check core backports consistency"""
        success = True
        
        # Check if backports is enabled but no components are selected
        if self.config_state.is_enabled("CONFIG_BACKPORTS"):
            backports_components = [
                "CONFIG_BACKPORTS_CFG80211",
                "CONFIG_BACKPORTS_MAC80211"
            ]
            
            enabled_components = [opt for opt in backports_components 
                                if self.config_state.is_enabled(opt)]
            
            if not enabled_components:
                self.add_issue(
                    ConsistencyLevel.WARNING,
                    "core_consistency",
                    "Backports enabled but no components selected",
                    ["CONFIG_BACKPORTS"],
                    [
                        "Enable at least CONFIG_BACKPORTS_CFG80211",
                        "Consider enabling CONFIG_BACKPORTS_MAC80211 for full functionality"
                    ],
                    auto_fixable=True,
                    fix_command="scripts/kconfig-helper.sh enable CONFIG_BACKPORTS_CFG80211 m"
                )
        
        # Check for incomplete backports configuration
        if (self.config_state.is_enabled("CONFIG_BACKPORTS_MAC80211") and 
            not self.config_state.is_enabled("CONFIG_BACKPORTS_CFG80211")):
            self.add_issue(
                ConsistencyLevel.CRITICAL,
                "core_consistency",
                "MAC80211 enabled without CFG80211",
                ["CONFIG_BACKPORTS_MAC80211", "CONFIG_BACKPORTS_CFG80211"],
                [
                    "Enable CONFIG_BACKPORTS_CFG80211",
                    "CFG80211 is required for MAC80211 functionality"
                ],
                auto_fixable=True,
                fix_command="scripts/kconfig-helper.sh enable CONFIG_BACKPORTS_CFG80211 m"
            )
            success = False
        
        return success
    
    def check_wireless_stack_consistency(self) -> bool:
        """Check wireless stack consistency"""
        success = True
        
        backports_wireless = self.config_state.is_enabled("CONFIG_BACKPORTS")
        kernel_cfg80211 = self.config_state.is_enabled("CONFIG_CFG80211")
        kernel_mac80211 = self.config_state.is_enabled("CONFIG_MAC80211")
        
        # Check for conflicting wireless stacks
        if backports_wireless and (kernel_cfg80211 or kernel_mac80211):
            conflicting_options = []
            if kernel_cfg80211:
                conflicting_options.append("CONFIG_CFG80211")
            if kernel_mac80211:
                conflicting_options.append("CONFIG_MAC80211")
            
            self.add_issue(
                ConsistencyLevel.CRITICAL,
                "wireless_stack",
                "Conflicting wireless stacks detected",
                ["CONFIG_BACKPORTS"] + conflicting_options,
                [
                    "Disable kernel wireless stack (CONFIG_CFG80211, CONFIG_MAC80211)",
                    "OR disable backports wireless stack (CONFIG_BACKPORTS)",
                    "Only one wireless stack can be active at a time"
                ],
                auto_fixable=True,
                fix_command="scripts/kconfig-helper.sh disable CONFIG_CFG80211 && scripts/kconfig-helper.sh disable CONFIG_MAC80211"
            )
            success = False
        
        return success
    
    def check_dependency_consistency(self) -> bool:
        """Check dependency consistency"""
        success = True
        
        for option, dependencies in self.dependency_graph.items():
            if self.config_state.is_enabled(option):
                missing_deps = []
                
                for dep in dependencies:
                    if not self.config_state.is_enabled(dep):
                        missing_deps.append(dep)
                
                if missing_deps:
                    self.add_issue(
                        ConsistencyLevel.ERROR,
                        "dependency",
                        f"{option} missing required dependencies",
                        [option] + missing_deps,
                        [f"Enable {dep}" for dep in missing_deps] + 
                        ["Dependencies are required for proper functionality"],
                        auto_fixable=True,
                        fix_command=" && ".join([f"scripts/kconfig-helper.sh enable {dep}" for dep in missing_deps])
                    )
                    success = False
        
        return success
    
    def check_security_consistency(self) -> bool:
        """Check security consistency"""
        success = True
        
        # Check frame injection security
        if self.config_state.is_enabled("CONFIG_BACKPORTS_FRAME_INJECTION"):
            security_options = [
                "CONFIG_AUDIT",
                "CONFIG_NET_NS"
            ]
            
            missing_security = [opt for opt in security_options 
                              if not self.config_state.is_enabled(opt)]
            
            if missing_security:
                self.add_issue(
                    ConsistencyLevel.WARNING,
                    "security",
                    "Frame injection enabled without security safeguards",
                    ["CONFIG_BACKPORTS_FRAME_INJECTION"] + missing_security,
                    [
                        "Enable CONFIG_AUDIT for security logging",
                        "Enable CONFIG_NET_NS for network isolation",
                        "Review security policies for frame injection usage"
                    ],
                    auto_fixable=True,
                    fix_command=" && ".join([f"scripts/kconfig-helper.sh enable {opt}" for opt in missing_security])
                )
        
        # Check monitor mode security
        if self.config_state.is_enabled("CONFIG_BACKPORTS_MONITOR_MODE"):
            if not self.config_state.is_enabled("CONFIG_PACKET"):
                self.add_issue(
                    ConsistencyLevel.ERROR,
                    "security",
                    "Monitor mode enabled without packet socket support",
                    ["CONFIG_BACKPORTS_MONITOR_MODE", "CONFIG_PACKET"],
                    [
                        "Enable CONFIG_PACKET for packet socket support",
                        "Packet sockets are required for monitor mode functionality"
                    ],
                    auto_fixable=True,
                    fix_command="scripts/kconfig-helper.sh enable CONFIG_PACKET"
                )
                success = False
        
        return success
    
    def check_performance_consistency(self) -> bool:
        """Check performance consistency"""
        success = True
        
        # Check debug options impact
        debug_options = [
            "CONFIG_BACKPORTS_DEBUG",
            "CONFIG_BACKPORTS_DEBUG_VERBOSE"
        ]
        
        enabled_debug = [opt for opt in debug_options 
                        if self.config_state.is_enabled(opt)]
        
        if enabled_debug:
            self.add_issue(
                ConsistencyLevel.INFO,
                "performance",
                "Debug options enabled - may impact performance",
                enabled_debug,
                [
                    "Consider disabling debug options in production builds",
                    "Debug options increase kernel size and runtime overhead",
                    "Use debug options only during development and testing"
                ]
            )
        
        return success
    
    def check_android_consistency(self) -> bool:
        """Check Android-specific consistency"""
        success = True
        
        android_kernel = self.config_state.is_enabled("CONFIG_ANDROID")
        backports_android = self.config_state.is_enabled("CONFIG_BACKPORTS_ANDROID")
        
        # Check Android backports without Android kernel
        if backports_android and not android_kernel:
            self.add_issue(
                ConsistencyLevel.ERROR,
                "android",
                "Android backports enabled without Android kernel support",
                ["CONFIG_BACKPORTS_ANDROID", "CONFIG_ANDROID"],
                [
                    "Enable CONFIG_ANDROID for Android kernel support",
                    "OR disable CONFIG_BACKPORTS_ANDROID if not using Android"
                ],
                auto_fixable=True,
                fix_command="scripts/kconfig-helper.sh enable CONFIG_ANDROID"
            )
            success = False
        
        # Check for conflicting vendor drivers
        if self.config_state.is_enabled("CONFIG_BACKPORTS"):
            vendor_drivers = [
                "CONFIG_QCACLD",
                "CONFIG_PRIMA_WLAN",
                "CONFIG_WCNSS_CORE"
            ]
            
            conflicting_drivers = [driver for driver in vendor_drivers 
                                 if self.config_state.is_enabled(driver)]
            
            if conflicting_drivers:
                self.add_issue(
                    ConsistencyLevel.CRITICAL,
                    "android",
                    "Backports conflicts with vendor wireless drivers",
                    ["CONFIG_BACKPORTS"] + conflicting_drivers,
                    [
                        f"Disable {driver}" for driver in conflicting_drivers
                    ] + [
                        "Vendor drivers conflict with backports wireless stack"
                    ],
                    auto_fixable=True,
                    fix_command=" && ".join([f"scripts/kconfig-helper.sh disable {driver}" for driver in conflicting_drivers])
                )
                success = False
        
        return success
    
    def check_build_consistency(self) -> bool:
        """Check build system consistency"""
        success = True
        
        # Check module support
        if self.config_state.is_enabled("CONFIG_BACKPORTS"):
            backports_modules = [
                "CONFIG_BACKPORTS_CFG80211",
                "CONFIG_BACKPORTS_MAC80211"
            ]
            
            modular_backports = [opt for opt in backports_modules 
                               if self.config_state.get_value(opt) == 'm']
            
            if modular_backports and not self.config_state.is_enabled("CONFIG_MODULES"):
                self.add_issue(
                    ConsistencyLevel.CRITICAL,
                    "build",
                    "Modular backports enabled without module support",
                    ["CONFIG_MODULES"] + modular_backports,
                    [
                        "Enable CONFIG_MODULES for modular kernel support",
                        "OR change backports options to built-in (=y)"
                    ],
                    auto_fixable=True,
                    fix_command="scripts/kconfig-helper.sh enable CONFIG_MODULES"
                )
                success = False
        
        return success
    
    def check_module_consistency(self) -> bool:
        """Check module-specific consistency"""
        success = True
        
        # Check for mixed built-in and modular configurations
        cfg80211_value = self.config_state.get_value("CONFIG_BACKPORTS_CFG80211")
        mac80211_value = self.config_state.get_value("CONFIG_BACKPORTS_MAC80211")
        
        if (cfg80211_value in ['y', 'm'] and mac80211_value in ['y', 'm'] and 
            cfg80211_value != mac80211_value):
            self.add_issue(
                ConsistencyLevel.WARNING,
                "module",
                "Mixed built-in and modular wireless configuration",
                ["CONFIG_BACKPORTS_CFG80211", "CONFIG_BACKPORTS_MAC80211"],
                [
                    "Consider using consistent configuration (both =y or both =m)",
                    "Mixed configurations may cause dependency issues"
                ]
            )
        
        return success
    
    def run_consistency_checks(self) -> bool:
        """Run all consistency checks"""
        self.issues.clear()
        overall_success = True
        
        for rule_name, rule_info in self.consistency_rules.items():
            check_function = getattr(self, rule_info["check_function"])
            success = check_function()
            
            if not success and rule_info.get("critical", False):
                overall_success = False
        
        return overall_success
    
    def validate_pre_build(self) -> bool:
        """Pre-build validation"""
        print("🔍 Running pre-build consistency validation...")
        
        # Reload configuration
        self.config_state.load_config()
        
        # Run consistency checks
        success = self.run_consistency_checks()
        
        # Report results
        critical_issues = [i for i in self.issues if i.level == ConsistencyLevel.CRITICAL]
        error_issues = [i for i in self.issues if i.level == ConsistencyLevel.ERROR]
        
        if critical_issues:
            print(f"❌ {len(critical_issues)} critical consistency issues found")
            for issue in critical_issues:
                print(f"   • {issue.description}")
            return False
        
        if error_issues:
            print(f"⚠️  {len(error_issues)} error-level consistency issues found")
            for issue in error_issues:
                print(f"   • {issue.description}")
        
        if success:
            print("✅ Pre-build consistency validation passed")
        
        return success
    
    def monitor_runtime_changes(self, callback=None):
        """Monitor configuration changes at runtime"""
        print("👀 Monitoring configuration changes...")
        
        last_check = time.time()
        
        try:
            while True:
                time.sleep(1)  # Check every second
                
                if self.config_state.is_modified():
                    print("📝 Configuration change detected, validating...")
                    
                    # Reload and validate
                    self.config_state.load_config()
                    success = self.run_consistency_checks()
                    
                    # Report immediate issues
                    critical_issues = [i for i in self.issues if i.level == ConsistencyLevel.CRITICAL]
                    if critical_issues:
                        print("🚨 Critical consistency issues detected:")
                        for issue in critical_issues:
                            print(f"   • {issue.description}")
                            if issue.auto_fixable:
                                print(f"     Auto-fix: {issue.fix_command}")
                    
                    if callback:
                        callback(self.issues)
                    
                    last_check = time.time()
        
        except KeyboardInterrupt:
            print("\n⏹️  Stopped monitoring configuration changes")
    
    def generate_consistency_report(self) -> Dict[str, Any]:
        """Generate detailed consistency report"""
        return {
            "summary": {
                "total_issues": len(self.issues),
                "critical": len([i for i in self.issues if i.level == ConsistencyLevel.CRITICAL]),
                "errors": len([i for i in self.issues if i.level == ConsistencyLevel.ERROR]),
                "warnings": len([i for i in self.issues if i.level == ConsistencyLevel.WARNING]),
                "info": len([i for i in self.issues if i.level == ConsistencyLevel.INFO]),
                "auto_fixable": len([i for i in self.issues if i.auto_fixable])
            },
            "issues": [
                {
                    "level": issue.level.value,
                    "category": issue.category,
                    "description": issue.description,
                    "affected_options": issue.affected_options,
                    "resolution_steps": issue.resolution_steps,
                    "auto_fixable": issue.auto_fixable,
                    "fix_command": issue.fix_command
                }
                for issue in self.issues
            ],
            "configuration_state": {
                "enabled_backports_options": self.config_state.get_enabled_options("CONFIG_BACKPORTS"),
                "enabled_wireless_options": (
                    self.config_state.get_enabled_options("CONFIG_CFG80211") +
                    self.config_state.get_enabled_options("CONFIG_MAC80211")
                ),
                "timestamp": self.config_state.timestamp
            }
        }
    
    def print_consistency_report(self):
        """Print human-readable consistency report"""
        if not self.issues:
            print("✅ Configuration is consistent - no issues found!")
            return
        
        print("🔍 Configuration Consistency Report")
        print("=" * 40)
        print()
        
        # Group by level
        by_level = {}
        for issue in self.issues:
            level = issue.level.value
            if level not in by_level:
                by_level[level] = []
            by_level[level].append(issue)
        
        # Print by severity
        level_icons = {
            "critical": "🚨",
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️"
        }
        
        for level in ["critical", "error", "warning", "info"]:
            if level in by_level:
                issues = by_level[level]
                icon = level_icons[level]
                print(f"{icon} {level.upper()} ({len(issues)} issues):")
                print("-" * (len(level) + 12))
                
                for i, issue in enumerate(issues, 1):
                    print(f"{i}. {issue.description}")
                    print(f"   Affected: {', '.join(issue.affected_options)}")
                    
                    if issue.auto_fixable:
                        print(f"   🔧 Auto-fix: {issue.fix_command}")
                    else:
                        print("   📋 Resolution steps:")
                        for step in issue.resolution_steps:
                            print(f"      • {step}")
                    print()
    
    def apply_auto_fixes(self) -> int:
        """Apply all available auto-fixes"""
        auto_fixable = [i for i in self.issues if i.auto_fixable and i.fix_command]
        
        if not auto_fixable:
            print("ℹ️  No auto-fixable issues found")
            return 0
        
        print(f"🔧 Applying {len(auto_fixable)} auto-fixes...")
        
        applied = 0
        for issue in auto_fixable:
            try:
                print(f"   Fixing: {issue.description}")
                result = subprocess.run(issue.fix_command, shell=True, 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"   ✅ Applied: {issue.fix_command}")
                    applied += 1
                else:
                    print(f"   ❌ Failed: {result.stderr}")
            except Exception as e:
                print(f"   ❌ Error applying fix: {e}")
        
        print(f"🎉 Applied {applied}/{len(auto_fixable)} auto-fixes")
        return applied

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Backports configuration consistency checker')
    parser.add_argument('--kernel-root', default='.', help='Path to kernel source root')
    parser.add_argument('--pre-build', action='store_true', help='Run pre-build validation')
    parser.add_argument('--monitor', action='store_true', help='Monitor runtime changes')
    parser.add_argument('--auto-fix', action='store_true', help='Apply auto-fixes')
    parser.add_argument('--json', action='store_true', help='Output JSON report')
    parser.add_argument('--report-file', help='Save report to file')
    
    args = parser.parse_args()
    
    checker = BackportsConsistencyChecker(args.kernel_root)
    
    if args.monitor:
        checker.monitor_runtime_changes()
        return 0
    
    if args.pre_build:
        success = checker.validate_pre_build()
        return 0 if success else 1
    
    # Run consistency checks
    success = checker.run_consistency_checks()
    
    if args.json:
        report = checker.generate_consistency_report()
        if args.report_file:
            with open(args.report_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"Report saved to: {args.report_file}")
        else:
            print(json.dumps(report, indent=2))
    else:
        checker.print_consistency_report()
        
        if args.report_file:
            report = checker.generate_consistency_report()
            with open(args.report_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"Detailed report saved to: {args.report_file}")
    
    if args.auto_fix:
        checker.apply_auto_fixes()
        
        # Re-run checks after fixes
        print("\n🔄 Re-validating after auto-fixes...")
        success = checker.run_consistency_checks()
        checker.print_consistency_report()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())