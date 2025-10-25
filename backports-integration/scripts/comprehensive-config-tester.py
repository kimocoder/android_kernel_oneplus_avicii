#!/usr/bin/env python3
"""
Comprehensive Configuration Testing Suite

This script performs comprehensive testing of all configuration combinations,
tests edge cases and error conditions, and verifies stability and reliability
of the configuration system.
"""

import os
import sys
import json
import tempfile
import shutil
import subprocess
import time
import itertools
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import argparse

class ConfigTestResult(Enum):
    """Configuration test result status"""
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    ERROR = "error"

@dataclass
class ConfigTestCase:
    """Represents a configuration test case"""
    name: str
    description: str
    config_options: Dict[str, str]
    expected_result: ConfigTestResult
    test_category: str
    priority: int = 1
    edge_case: bool = False

@dataclass
class ConfigTestExecution:
    """Represents configuration test execution result"""
    test_case: ConfigTestCase
    result: ConfigTestResult
    execution_time: float
    validation_output: str = ""
    error_message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

class ComprehensiveConfigTester:
    """Comprehensive configuration testing suite"""
    
    def __init__(self, kernel_root: str = "."):
        self.kernel_root = Path(kernel_root).resolve()
        self.temp_dir = None
        self.original_config = None
        self.test_cases = []
        self.execution_results = []
        
        # Load comprehensive test cases
        self._load_comprehensive_test_cases()
    
    def _load_comprehensive_test_cases(self):
        """Load comprehensive configuration test cases"""
        
        # Basic configuration combinations
        self._load_basic_combinations()
        
        # Edge cases and error conditions
        self._load_edge_cases()
        
        # Stress test configurations
        self._load_stress_tests()
        
        # Android-specific comprehensive tests
        self._load_android_comprehensive_tests()
        
        # Security configuration tests
        self._load_security_tests()
        
        # Performance configuration tests
        self._load_performance_tests()
    
    def _load_basic_combinations(self):
        """Load basic configuration combinations"""
        
        # All valid basic combinations
        basic_configs = [
            # Minimal configuration
            {
                "name": "minimal_backports",
                "description": "Minimal backports configuration",
                "config": {"CONFIG_BACKPORTS": "y"},
                "expected": ConfigTestResult.PASS,
                "category": "basic"
            },
            
            # Standard wireless configuration
            {
                "name": "standard_wireless",
                "description": "Standard wireless configuration",
                "config": {
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_CFG80211": "m",
                    "CONFIG_BACKPORTS_MAC80211": "m"
                },
                "expected": ConfigTestResult.PASS,
                "category": "basic"
            },
            
            # Built-in configuration
            {
                "name": "builtin_wireless",
                "description": "Built-in wireless configuration",
                "config": {
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_CFG80211": "y",
                    "CONFIG_BACKPORTS_MAC80211": "y"
                },
                "expected": ConfigTestResult.PASS,
                "category": "basic"
            }
        ]
        
        for config in basic_configs:
            self.test_cases.append(ConfigTestCase(
                name=config["name"],
                description=config["description"],
                config_options=config["config"],
                expected_result=config["expected"],
                test_category=config["category"]
            ))
    
    def _load_edge_cases(self):
        """Load edge cases and error conditions"""
        
        edge_cases = [
            # Missing dependencies
            {
                "name": "mac80211_without_cfg80211",
                "description": "MAC80211 without CFG80211 dependency",
                "config": {
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_MAC80211": "m"
                },
                "expected": ConfigTestResult.FAIL,
                "category": "edge_case"
            },
            
            # Conflicting configurations
            {
                "name": "backports_with_kernel_wireless",
                "description": "Backports with kernel wireless enabled",
                "config": {
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_CFG80211": "y",
                    "CONFIG_MAC80211": "y"
                },
                "expected": ConfigTestResult.FAIL,
                "category": "edge_case"
            },
            
            # Invalid combinations
            {
                "name": "modular_without_modules",
                "description": "Modular backports without module support",
                "config": {
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_CFG80211": "m",
                    "CONFIG_MODULES": "n"
                },
                "expected": ConfigTestResult.FAIL,
                "category": "edge_case"
            }
        ]
        
        for config in edge_cases:
            self.test_cases.append(ConfigTestCase(
                name=config["name"],
                description=config["description"],
                config_options=config["config"],
                expected_result=config["expected"],
                test_category=config["category"],
                edge_case=True
            ))
    
    def _load_stress_tests(self):
        """Load stress test configurations"""
        
        # Maximum feature configuration
        max_config = {
            "CONFIG_BACKPORTS": "y",
            "CONFIG_BACKPORTS_CFG80211": "m",
            "CONFIG_BACKPORTS_MAC80211": "m",
            "CONFIG_BACKPORTS_MONITOR_MODE": "y",
            "CONFIG_BACKPORTS_MONITOR_RADIOTAP": "y",
            "CONFIG_BACKPORTS_MONITOR_CHANNEL_SWITCH": "y",
            "CONFIG_BACKPORTS_FRAME_INJECTION": "y",
            "CONFIG_BACKPORTS_INJECTION_RATE_CONTROL": "y",
            "CONFIG_BACKPORTS_INJECTION_SECURITY_AUDIT": "y",
            "CONFIG_BACKPORTS_DEBUG": "y",
            "CONFIG_BACKPORTS_DEBUG_VERBOSE": "y",
            "CONFIG_BACKPORTS_TRACING": "y",
            "CONFIG_BACKPORTS_DIAGNOSTICS": "y",
            "CONFIG_BACKPORTS_STATISTICS": "y"
        }
        
        self.test_cases.append(ConfigTestCase(
            name="maximum_features",
            description="Maximum feature configuration stress test",
            config_options=max_config,
            expected_result=ConfigTestResult.PASS,
            test_category="stress",
            priority=2
        ))
    
    def _load_android_comprehensive_tests(self):
        """Load comprehensive Android tests"""
        
        android_configs = [
            # Complete Android integration
            {
                "name": "android_complete",
                "description": "Complete Android integration test",
                "config": {
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_ANDROID": "y",
                    "CONFIG_BACKPORTS_ANDROID_WAKELOCK": "y",
                    "CONFIG_BACKPORTS_SECURITY_ANDROID": "y",
                    "CONFIG_BACKPORTS_SELINUX_ANDROID": "y",
                    "CONFIG_BACKPORTS_VENDOR_COMPAT": "y",
                    "CONFIG_BACKPORTS_VENDOR_QCOM": "y"
                },
                "expected": ConfigTestResult.PASS,
                "category": "android"
            }
        ]
        
        for config in android_configs:
            self.test_cases.append(ConfigTestCase(
                name=config["name"],
                description=config["description"],
                config_options=config["config"],
                expected_result=config["expected"],
                test_category=config["category"],
                priority=2
            ))
    
    def _load_security_tests(self):
        """Load security configuration tests"""
        
        security_configs = [
            # Frame injection with security
            {
                "name": "secure_frame_injection",
                "description": "Frame injection with security features",
                "config": {
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_CFG80211": "m",
                    "CONFIG_BACKPORTS_MAC80211": "m",
                    "CONFIG_BACKPORTS_MONITOR_MODE": "y",
                    "CONFIG_BACKPORTS_FRAME_INJECTION": "y",
                    "CONFIG_BACKPORTS_INJECTION_SECURITY_AUDIT": "y"
                },
                "expected": ConfigTestResult.PASS,
                "category": "security"
            }
        ]
        
        for config in security_configs:
            self.test_cases.append(ConfigTestCase(
                name=config["name"],
                description=config["description"],
                config_options=config["config"],
                expected_result=config["expected"],
                test_category=config["category"],
                priority=2
            ))
    
    def _load_performance_tests(self):
        """Load performance configuration tests"""
        
        performance_configs = [
            # Debug impact test
            {
                "name": "debug_performance_impact",
                "description": "Debug features performance impact test",
                "config": {
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_DEBUG": "y",
                    "CONFIG_BACKPORTS_DEBUG_VERBOSE": "y"
                },
                "expected": ConfigTestResult.PASS,
                "category": "performance"
            }
        ]
        
        for config in performance_configs:
            self.test_cases.append(ConfigTestCase(
                name=config["name"],
                description=config["description"],
                config_options=config["config"],
                expected_result=config["expected"],
                test_category=config["category"],
                priority=3
            ))
    
    def setup_comprehensive_test_environment(self):
        """Set up comprehensive test environment"""
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp(prefix="backports_comprehensive_test_")
        
        # Backup original configuration
        config_file = self.kernel_root / ".config"
        if config_file.exists():
            self.original_config = config_file.read_text()
        
        print(f"🔧 Comprehensive test environment set up")
    
    def cleanup_comprehensive_test_environment(self):
        """Clean up comprehensive test environment"""
        # Restore original configuration
        if self.original_config:
            config_file = self.kernel_root / ".config"
            config_file.write_text(self.original_config)
        
        # Clean up temporary files
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
        
        print("🧹 Comprehensive test environment cleaned up")
    
    def create_test_configuration(self, test_case: ConfigTestCase) -> str:
        """Create test configuration file"""
        config_lines = []
        
        # Add basic required options
        config_lines.extend([
            "# Comprehensive test configuration",
            "CONFIG_MODULES=y",
            "CONFIG_NET=y",
            "CONFIG_CRYPTO=y",
            "CONFIG_CRC32=y"
        ])
        
        # Add test-specific options
        for option, value in test_case.config_options.items():
            if value == "n":
                config_lines.append(f"# {option} is not set")
            else:
                config_lines.append(f"{option}={value}")
        
        # Create config file
        config_file = self.kernel_root / ".config"
        config_file.write_text("\n".join(config_lines) + "\n")
        
        return str(config_file)
    
    def run_comprehensive_validation(self, test_case: ConfigTestCase) -> Tuple[ConfigTestResult, str, Dict[str, Any]]:
        """Run comprehensive validation on test configuration"""
        details = {}
        
        try:
            # Create test configuration
            self.create_test_configuration(test_case)
            
            # Run all validation tools
            validation_results = {}
            
            # 1. Basic configuration validation
            result = subprocess.run([
                "python3", "backports-integration/scripts/validate-backports-config.py", "--json"
            ], cwd=self.kernel_root, capture_output=True, text=True, timeout=60)
            
            validation_results["config_validation"] = {
                "returncode": result.returncode,
                "output": result.stdout + result.stderr
            }
            
            # 2. Consistency checking
            result = subprocess.run([
                "python3", "backports-integration/scripts/consistency-checker.py", "--json"
            ], cwd=self.kernel_root, capture_output=True, text=True, timeout=60)
            
            validation_results["consistency_check"] = {
                "returncode": result.returncode,
                "output": result.stdout + result.stderr
            }
            
            # 3. Dependency validation
            result = subprocess.run([
                "python3", "backports-integration/scripts/validate-backports-deps.py"
            ], cwd=self.kernel_root, capture_output=True, text=True, timeout=30)
            
            validation_results["dependency_validation"] = {
                "returncode": result.returncode,
                "output": result.stdout + result.stderr
            }
            
            # Analyze results
            config_errors = validation_results["config_validation"]["returncode"] != 0
            consistency_errors = validation_results["consistency_check"]["returncode"] != 0
            dependency_errors = validation_results["dependency_validation"]["returncode"] != 0
            
            details["validation_results"] = validation_results
            details["has_errors"] = config_errors or consistency_errors or dependency_errors
            
            # Determine result based on expected outcome
            if test_case.expected_result == ConfigTestResult.PASS:
                if not details["has_errors"]:
                    return ConfigTestResult.PASS, "Configuration validated successfully", details
                else:
                    return ConfigTestResult.FAIL, "Unexpected validation errors", details
            
            elif test_case.expected_result == ConfigTestResult.FAIL:
                if details["has_errors"]:
                    return ConfigTestResult.PASS, "Expected validation errors detected", details
                else:
                    return ConfigTestResult.FAIL, "Expected validation errors not detected", details
            
            else:
                return ConfigTestResult.ERROR, "Unknown expected result", details
        
        except Exception as e:
            return ConfigTestResult.ERROR, str(e), details
    
    def run_comprehensive_test_case(self, test_case: ConfigTestCase) -> ConfigTestExecution:
        """Run a comprehensive test case"""
        start_time = time.time()
        
        try:
            result, message, details = self.run_comprehensive_validation(test_case)
            
            execution_time = time.time() - start_time
            
            return ConfigTestExecution(
                test_case=test_case,
                result=result,
                execution_time=execution_time,
                validation_output=message,
                error_message=message if result in [ConfigTestResult.FAIL, ConfigTestResult.ERROR] else "",
                details=details
            )
        
        except Exception as e:
            return ConfigTestExecution(
                test_case=test_case,
                result=ConfigTestResult.ERROR,
                execution_time=time.time() - start_time,
                error_message=str(e)
            )
    
    def run_all_comprehensive_tests(self, categories: Optional[List[str]] = None,
                                   priorities: Optional[List[int]] = None,
                                   include_edge_cases: bool = True) -> List[ConfigTestExecution]:
        """Run all comprehensive configuration tests"""
        
        # Filter test cases
        filtered_tests = self.test_cases
        
        if categories:
            filtered_tests = [t for t in filtered_tests if t.test_category in categories]
        
        if priorities:
            filtered_tests = [t for t in filtered_tests if t.priority in priorities]
        
        if not include_edge_cases:
            filtered_tests = [t for t in filtered_tests if not t.edge_case]
        
        print(f"🧪 Running {len(filtered_tests)} comprehensive configuration tests...")
        print("=" * 70)
        
        # Set up environment
        self.setup_comprehensive_test_environment()
        
        try:
            results = []
            for i, test_case in enumerate(filtered_tests, 1):
                print(f"\n[{i}/{len(filtered_tests)}] {test_case.name}")
                print(f"  Description: {test_case.description}")
                print(f"  Category: {test_case.test_category}, Priority: {test_case.priority}")
                
                execution = self.run_comprehensive_test_case(test_case)
                results.append(execution)
                
                # Print result
                status_icon = {
                    ConfigTestResult.PASS: "✅",
                    ConfigTestResult.FAIL: "❌",
                    ConfigTestResult.SKIP: "⏭️",
                    ConfigTestResult.ERROR: "💥"
                }[execution.result]
                
                print(f"  {status_icon} {execution.result.value.upper()} ({execution.execution_time:.2f}s)")
                
                if execution.error_message:
                    print(f"    Error: {execution.error_message}")
            
            self.execution_results = results
            return results
        
        finally:
            # Clean up environment
            self.cleanup_comprehensive_test_environment()
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        if not self.execution_results:
            return {"error": "No comprehensive test results available"}
        
        # Calculate overall statistics
        total_tests = len(self.execution_results)
        passed = len([r for r in self.execution_results if r.result == ConfigTestResult.PASS])
        failed = len([r for r in self.execution_results if r.result == ConfigTestResult.FAIL])
        errors = len([r for r in self.execution_results if r.result == ConfigTestResult.ERROR])
        skipped = len([r for r in self.execution_results if r.result == ConfigTestResult.SKIP])
        
        # Calculate by category
        categories = {}
        for result in self.execution_results:
            category = result.test_case.test_category
            if category not in categories:
                categories[category] = {"total": 0, "passed": 0, "failed": 0, "errors": 0}
            
            categories[category]["total"] += 1
            if result.result == ConfigTestResult.PASS:
                categories[category]["passed"] += 1
            elif result.result == ConfigTestResult.FAIL:
                categories[category]["failed"] += 1
            elif result.result == ConfigTestResult.ERROR:
                categories[category]["errors"] += 1
        
        # Calculate edge case statistics
        edge_cases = [r for r in self.execution_results if r.test_case.edge_case]
        edge_case_passed = len([r for r in edge_cases if r.result == ConfigTestResult.PASS])
        
        # Calculate execution time
        total_time = sum(r.execution_time for r in self.execution_results)
        
        return {
            "summary": {
                "total_tests": total_tests,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "skipped": skipped,
                "success_rate": (passed / total_tests * 100) if total_tests > 0 else 0,
                "edge_cases_total": len(edge_cases),
                "edge_cases_passed": edge_case_passed,
                "total_execution_time": total_time
            },
            "categories": categories,
            "test_results": [
                {
                    "name": r.test_case.name,
                    "description": r.test_case.description,
                    "category": r.test_case.test_category,
                    "priority": r.test_case.priority,
                    "edge_case": r.test_case.edge_case,
                    "expected_result": r.test_case.expected_result.value,
                    "actual_result": r.result.value,
                    "execution_time": r.execution_time,
                    "error_message": r.error_message
                }
                for r in self.execution_results
            ]
        }
    
    def print_comprehensive_report(self):
        """Print human-readable comprehensive test report"""
        report = self.generate_comprehensive_report()
        
        if "error" in report:
            print(f"Error generating report: {report['error']}")
            return
        
        summary = report["summary"]
        
        print("\n" + "=" * 70)
        print("COMPREHENSIVE CONFIGURATION TEST REPORT")
        print("=" * 70)
        
        print(f"\nOverall Results:")
        print(f"  Total Tests: {summary['total_tests']}")
        print(f"  Passed: {summary['passed']} ✅")
        print(f"  Failed: {summary['failed']} ❌")
        print(f"  Errors: {summary['errors']} 💥")
        print(f"  Skipped: {summary['skipped']} ⏭️")
        print(f"  Success Rate: {summary['success_rate']:.1f}%")
        print(f"  Total Time: {summary['total_execution_time']:.2f}s")
        
        print(f"\nEdge Case Testing:")
        print(f"  Edge Cases: {summary['edge_cases_total']}")
        print(f"  Edge Cases Passed: {summary['edge_cases_passed']} ✅")
        
        # Print category breakdown
        print(f"\nResults by Category:")
        for category, stats in report["categories"].items():
            success_rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            print(f"  {category.title()}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")
        
        # Print failed tests
        failed_tests = [r for r in self.execution_results 
                       if r.result in [ConfigTestResult.FAIL, ConfigTestResult.ERROR]]
        if failed_tests:
            print(f"\nFailed Tests:")
            for result in failed_tests:
                icon = "❌" if result.result == ConfigTestResult.FAIL else "💥"
                edge_text = " (EDGE CASE)" if result.test_case.edge_case else ""
                print(f"  {icon} {result.test_case.name}{edge_text}: {result.error_message}")
        
        # Overall assessment
        if summary['success_rate'] >= 95:
            print(f"\n🎉 COMPREHENSIVE TESTING: EXCELLENT")
            print("   Configuration system is highly stable and reliable")
        elif summary['success_rate'] >= 85:
            print(f"\n✅ COMPREHENSIVE TESTING: GOOD")
            print("   Configuration system is stable with minor issues")
        elif summary['success_rate'] >= 70:
            print(f"\n⚠️  COMPREHENSIVE TESTING: ACCEPTABLE")
            print("   Configuration system works but has some issues")
        else:
            print(f"\n❌ COMPREHENSIVE TESTING: NEEDS IMPROVEMENT")
            print("   Configuration system has significant issues")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Comprehensive configuration testing suite')
    parser.add_argument('--kernel-root', default='.', help='Path to kernel source root')
    parser.add_argument('--categories', nargs='+', help='Test categories to run')
    parser.add_argument('--priorities', nargs='+', type=int, help='Test priorities to run')
    parser.add_argument('--no-edge-cases', action='store_true', help='Skip edge case tests')
    parser.add_argument('--json', action='store_true', help='Output JSON report')
    parser.add_argument('--report-file', help='Save report to file')
    
    args = parser.parse_args()
    
    # Create comprehensive tester
    tester = ComprehensiveConfigTester(args.kernel_root)
    
    # Run comprehensive tests
    results = tester.run_all_comprehensive_tests(
        categories=args.categories,
        priorities=args.priorities,
        include_edge_cases=not args.no_edge_cases
    )
    
    # Generate report
    if args.json:
        report = tester.generate_comprehensive_report()
        print(json.dumps(report, indent=2))
    else:
        tester.print_comprehensive_report()
    
    # Save report if requested
    if args.report_file:
        report = tester.generate_comprehensive_report()
        with open(args.report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Comprehensive test report saved to: {args.report_file}")
    
    # Return appropriate exit code
    report = tester.generate_comprehensive_report()
    success_rate = report["summary"]["success_rate"]
    return 0 if success_rate >= 80 else 1

if __name__ == "__main__":
    sys.exit(main())