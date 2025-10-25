#!/usr/bin/env python3
"""
Automated Backports Configuration Testing Framework

This script provides comprehensive automated testing for backports configuration
including test cases for valid and invalid configuration combinations and
regression testing for configuration changes.
"""

import os
import sys
import json
import tempfile
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import argparse
import time

class TestResult(Enum):
    """Test result status"""
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    ERROR = "error"

@dataclass
class TestCase:
    """Represents a configuration test case"""
    name: str
    description: str
    config_options: Dict[str, str]
    expected_result: TestResult
    expected_errors: List[str] = field(default_factory=list)
    expected_warnings: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    category: str = "general"
    priority: int = 1  # 1=high, 2=medium, 3=low

@dataclass
class TestExecution:
    """Represents a test execution result"""
    test_case: TestCase
    result: TestResult
    execution_time: float
    output: str = ""
    error_message: str = ""
    validation_results: Dict[str, Any] = field(default_factory=dict)

class BackportsConfigTester:
    """Automated configuration testing framework"""
    
    def __init__(self, kernel_root: str = "."):
        self.kernel_root = Path(kernel_root).resolve()
        self.test_cases: List[TestCase] = []
        self.test_results: List[TestExecution] = []
        
        # Test environment setup
        self.temp_dir = None
        self.original_config = None
        
        # Load test cases
        self._load_test_cases()
    
    def _load_test_cases(self):
        """Load predefined test cases"""
        
        # Basic configuration tests
        self.test_cases.extend([
            TestCase(
                name="basic_backports_enable",
                description="Test basic backports enablement",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_CFG80211": "m",
                    "CONFIG_BACKPORTS_MAC80211": "m"
                },
                expected_result=TestResult.PASS,
                category="basic",
                priority=1
            ),
            
            TestCase(
                name="backports_without_modules",
                description="Test backports without module support",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_CFG80211": "m",
                    "CONFIG_MODULES": "n"
                },
                expected_result=TestResult.FAIL,
                expected_errors=["Modular backports enabled without module support"],
                category="basic",
                priority=1
            ),
            
            TestCase(
                name="mac80211_without_cfg80211",
                description="Test MAC80211 without CFG80211",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_MAC80211": "m"
                },
                expected_result=TestResult.FAIL,
                expected_errors=["MAC80211 requires CFG80211"],
                category="dependency",
                priority=1
            )
        ])
        
        # Conflict detection tests
        self.test_cases.extend([
            TestCase(
                name="backports_kernel_wireless_conflict",
                description="Test conflict between backports and kernel wireless",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_CFG80211": "y",
                    "CONFIG_MAC80211": "y"
                },
                expected_result=TestResult.FAIL,
                expected_errors=["Cannot enable both backports and kernel wireless stacks"],
                category="conflict",
                priority=1
            ),
            
            TestCase(
                name="android_vendor_driver_conflict",
                description="Test Android backports with conflicting vendor drivers",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_ANDROID": "y",
                    "CONFIG_QCACLD": "y"
                },
                expected_result=TestResult.FAIL,
                expected_errors=["conflicts with vendor wireless drivers"],
                category="conflict",
                priority=1
            )
        ])
        
        # Monitor mode and frame injection tests
        self.test_cases.extend([
            TestCase(
                name="monitor_mode_basic",
                description="Test basic monitor mode configuration",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_CFG80211": "m",
                    "CONFIG_BACKPORTS_MAC80211": "m",
                    "CONFIG_BACKPORTS_MONITOR_MODE": "y",
                    "CONFIG_PACKET": "y"
                },
                expected_result=TestResult.PASS,
                category="monitor",
                priority=2
            ),
            
            TestCase(
                name="monitor_mode_without_packet",
                description="Test monitor mode without packet support",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_CFG80211": "m",
                    "CONFIG_BACKPORTS_MAC80211": "m",
                    "CONFIG_BACKPORTS_MONITOR_MODE": "y"
                },
                expected_result=TestResult.FAIL,
                expected_errors=["Monitor mode requires CONFIG_PACKET"],
                category="monitor",
                priority=2
            ),
            
            TestCase(
                name="frame_injection_security",
                description="Test frame injection with security features",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_CFG80211": "m",
                    "CONFIG_BACKPORTS_MAC80211": "m",
                    "CONFIG_BACKPORTS_MONITOR_MODE": "y",
                    "CONFIG_BACKPORTS_FRAME_INJECTION": "y",
                    "CONFIG_PACKET": "y",
                    "CONFIG_PACKET_MMAP": "y",
                    "CONFIG_BACKPORTS_INJECTION_SECURITY_AUDIT": "y",
                    "CONFIG_AUDIT": "y"
                },
                expected_result=TestResult.PASS,
                expected_warnings=["Frame injection has security implications"],
                category="security",
                priority=2
            ),
            
            TestCase(
                name="frame_injection_without_audit",
                description="Test frame injection security audit without audit support",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_CFG80211": "m",
                    "CONFIG_BACKPORTS_MAC80211": "m",
                    "CONFIG_BACKPORTS_MONITOR_MODE": "y",
                    "CONFIG_BACKPORTS_FRAME_INJECTION": "y",
                    "CONFIG_PACKET": "y",
                    "CONFIG_PACKET_MMAP": "y",
                    "CONFIG_BACKPORTS_INJECTION_SECURITY_AUDIT": "y"
                },
                expected_result=TestResult.FAIL,
                expected_errors=["Security auditing requires CONFIG_AUDIT"],
                category="security",
                priority=2
            )
        ])
        
        # Android-specific tests
        self.test_cases.extend([
            TestCase(
                name="android_basic_integration",
                description="Test basic Android integration",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_ANDROID": "y",
                    "CONFIG_ANDROID": "y"
                },
                expected_result=TestResult.PASS,
                category="android",
                priority=2
            ),
            
            TestCase(
                name="android_without_kernel_support",
                description="Test Android backports without Android kernel support",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_ANDROID": "y"
                },
                expected_result=TestResult.FAIL,
                expected_errors=["Android backports require CONFIG_ANDROID"],
                category="android",
                priority=2
            ),
            
            TestCase(
                name="android_wakelock_integration",
                description="Test Android wakelock integration",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_ANDROID": "y",
                    "CONFIG_BACKPORTS_ANDROID_WAKELOCK": "y",
                    "CONFIG_ANDROID": "y",
                    "CONFIG_ANDROID_WAKELOCK": "y"
                },
                expected_result=TestResult.PASS,
                category="android",
                priority=3
            ),
            
            TestCase(
                name="android_selinux_integration",
                description="Test Android SELinux integration",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_ANDROID": "y",
                    "CONFIG_BACKPORTS_SECURITY_ANDROID": "y",
                    "CONFIG_BACKPORTS_SELINUX_ANDROID": "y",
                    "CONFIG_ANDROID": "y",
                    "CONFIG_SECURITY_SELINUX": "y"
                },
                expected_result=TestResult.PASS,
                category="android",
                priority=3
            )
        ])
        
        # Debug and diagnostic tests
        self.test_cases.extend([
            TestCase(
                name="debug_basic",
                description="Test basic debugging configuration",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_DEBUG": "y"
                },
                expected_result=TestResult.PASS,
                expected_warnings=["Debug features increase kernel size"],
                category="debug",
                priority=3
            ),
            
            TestCase(
                name="tracing_without_kernel_support",
                description="Test tracing without kernel tracing support",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_TRACING": "y"
                },
                expected_result=TestResult.FAIL,
                expected_errors=["Tracing support requires CONFIG_TRACING"],
                category="debug",
                priority=3
            ),
            
            TestCase(
                name="diagnostics_without_debugfs",
                description="Test diagnostics without debugfs support",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_DIAGNOSTICS": "y"
                },
                expected_result=TestResult.FAIL,
                expected_errors=["Diagnostic interfaces require CONFIG_DEBUG_FS"],
                category="debug",
                priority=3
            )
        ])
        
        # Vendor compatibility tests
        self.test_cases.extend([
            TestCase(
                name="vendor_compat_basic",
                description="Test basic vendor compatibility",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_VENDOR_COMPAT": "y"
                },
                expected_result=TestResult.PASS,
                category="vendor",
                priority=3
            ),
            
            TestCase(
                name="qcom_vendor_compat",
                description="Test Qualcomm vendor compatibility",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_VENDOR_COMPAT": "y",
                    "CONFIG_BACKPORTS_VENDOR_QCOM": "y"
                },
                expected_result=TestResult.PASS,
                category="vendor",
                priority=3
            )
        ])
    
    def setup_test_environment(self):
        """Set up isolated test environment"""
        # Create temporary directory for test configurations
        self.temp_dir = tempfile.mkdtemp(prefix="backports_test_")
        
        # Backup original configuration if it exists
        config_file = self.kernel_root / ".config"
        if config_file.exists():
            self.original_config = config_file.read_text()
    
    def cleanup_test_environment(self):
        """Clean up test environment"""
        # Restore original configuration
        if self.original_config:
            config_file = self.kernel_root / ".config"
            config_file.write_text(self.original_config)
        
        # Remove temporary directory
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def create_test_config(self, config_options: Dict[str, str]) -> str:
        """Create a test configuration file"""
        config_lines = []
        
        # Add basic required options
        config_lines.append("# Test configuration")
        config_lines.append("CONFIG_MODULES=y")
        config_lines.append("CONFIG_NET=y")
        
        # Add test-specific options
        for option, value in config_options.items():
            if value == "n":
                config_lines.append(f"# {option} is not set")
            else:
                config_lines.append(f"{option}={value}")
        
        # Create temporary config file
        config_file = Path(self.temp_dir) / "test.config"
        config_file.write_text("\n".join(config_lines) + "\n")
        
        return str(config_file)
    
    def run_validation(self, config_file: str) -> Dict[str, Any]:
        """Run validation on test configuration"""
        try:
            # Copy test config to kernel root
            kernel_config = self.kernel_root / ".config"
            shutil.copy2(config_file, kernel_config)
            
            # Run validation script
            validator_script = self.kernel_root / "backports-integration/scripts/validate-backports-config.py"
            if not validator_script.exists():
                return {"error": "Validator script not found"}
            
            result = subprocess.run([
                "python3", str(validator_script),
                "--kernel-root", str(self.kernel_root),
                "--json"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return {"error": "Invalid JSON output from validator"}
            else:
                return {"error": f"Validator failed: {result.stderr}"}
        
        except subprocess.TimeoutExpired:
            return {"error": "Validation timeout"}
        except Exception as e:
            return {"error": f"Validation error: {e}"}
    
    def run_consistency_check(self, config_file: str) -> Dict[str, Any]:
        """Run consistency check on test configuration"""
        try:
            # Copy test config to kernel root
            kernel_config = self.kernel_root / ".config"
            shutil.copy2(config_file, kernel_config)
            
            # Run consistency checker
            checker_script = self.kernel_root / "backports-integration/scripts/consistency-checker.py"
            if not checker_script.exists():
                return {"error": "Consistency checker not found"}
            
            result = subprocess.run([
                "python3", str(checker_script),
                "--kernel-root", str(self.kernel_root),
                "--json"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return {"error": "Invalid JSON output from consistency checker"}
            else:
                return {"error": f"Consistency checker failed: {result.stderr}"}
        
        except subprocess.TimeoutExpired:
            return {"error": "Consistency check timeout"}
        except Exception as e:
            return {"error": f"Consistency check error: {e}"}
    
    def evaluate_test_result(self, test_case: TestCase, validation_results: Dict[str, Any]) -> Tuple[TestResult, str]:
        """Evaluate test results against expected outcomes"""
        if "error" in validation_results:
            return TestResult.ERROR, validation_results["error"]
        
        # Check validation summary
        summary = validation_results.get("summary", {})
        errors = summary.get("errors", 0)
        warnings = summary.get("warnings", 0)
        
        # Get actual error and warning messages
        results = validation_results.get("results", [])
        actual_errors = [r["message"] for r in results if r["level"] == "error"]
        actual_warnings = [r["message"] for r in results if r["level"] == "warning"]
        
        # Evaluate based on expected result
        if test_case.expected_result == TestResult.PASS:
            if errors > 0:
                return TestResult.FAIL, f"Expected pass but got {errors} errors: {actual_errors}"
            return TestResult.PASS, "Test passed as expected"
        
        elif test_case.expected_result == TestResult.FAIL:
            if errors == 0:
                return TestResult.FAIL, "Expected failure but test passed"
            
            # Check if expected errors are present
            if test_case.expected_errors:
                for expected_error in test_case.expected_errors:
                    found = any(expected_error.lower() in error.lower() for error in actual_errors)
                    if not found:
                        return TestResult.FAIL, f"Expected error not found: {expected_error}"
            
            return TestResult.PASS, "Test failed as expected"
        
        return TestResult.ERROR, "Unknown expected result"
    
    def run_test_case(self, test_case: TestCase) -> TestExecution:
        """Run a single test case"""
        start_time = time.time()
        
        try:
            # Create test configuration
            config_file = self.create_test_config(test_case.config_options)
            
            # Run validation
            validation_results = self.run_validation(config_file)
            
            # Run consistency check
            consistency_results = self.run_consistency_check(config_file)
            
            # Combine results
            combined_results = {
                "validation": validation_results,
                "consistency": consistency_results
            }
            
            # Evaluate results
            result, message = self.evaluate_test_result(test_case, validation_results)
            
            execution_time = time.time() - start_time
            
            return TestExecution(
                test_case=test_case,
                result=result,
                execution_time=execution_time,
                output=message,
                validation_results=combined_results
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            return TestExecution(
                test_case=test_case,
                result=TestResult.ERROR,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    def run_all_tests(self, categories: Optional[List[str]] = None, 
                     priorities: Optional[List[int]] = None) -> List[TestExecution]:
        """Run all test cases with optional filtering"""
        
        # Filter test cases
        filtered_tests = self.test_cases
        
        if categories:
            filtered_tests = [t for t in filtered_tests if t.category in categories]
        
        if priorities:
            filtered_tests = [t for t in filtered_tests if t.priority in priorities]
        
        print(f"Running {len(filtered_tests)} test cases...")
        
        # Set up test environment
        self.setup_test_environment()
        
        try:
            results = []
            for i, test_case in enumerate(filtered_tests, 1):
                print(f"[{i}/{len(filtered_tests)}] Running: {test_case.name}")
                
                execution = self.run_test_case(test_case)
                results.append(execution)
                
                # Print immediate result
                status_icon = {
                    TestResult.PASS: "✅",
                    TestResult.FAIL: "❌",
                    TestResult.SKIP: "⏭️",
                    TestResult.ERROR: "💥"
                }[execution.result]
                
                print(f"   {status_icon} {execution.result.value.upper()} ({execution.execution_time:.2f}s)")
                if execution.error_message:
                    print(f"      Error: {execution.error_message}")
                elif execution.output:
                    print(f"      {execution.output}")
            
            self.test_results = results
            return results
        
        finally:
            # Clean up test environment
            self.cleanup_test_environment()
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        if not self.test_results:
            return {"error": "No test results available"}
        
        # Calculate statistics
        total_tests = len(self.test_results)
        passed = len([r for r in self.test_results if r.result == TestResult.PASS])
        failed = len([r for r in self.test_results if r.result == TestResult.FAIL])
        errors = len([r for r in self.test_results if r.result == TestResult.ERROR])
        skipped = len([r for r in self.test_results if r.result == TestResult.SKIP])
        
        # Calculate by category
        categories = {}
        for result in self.test_results:
            category = result.test_case.category
            if category not in categories:
                categories[category] = {"total": 0, "passed": 0, "failed": 0, "errors": 0}
            
            categories[category]["total"] += 1
            if result.result == TestResult.PASS:
                categories[category]["passed"] += 1
            elif result.result == TestResult.FAIL:
                categories[category]["failed"] += 1
            elif result.result == TestResult.ERROR:
                categories[category]["errors"] += 1
        
        # Calculate execution time
        total_time = sum(r.execution_time for r in self.test_results)
        
        return {
            "summary": {
                "total_tests": total_tests,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "skipped": skipped,
                "success_rate": (passed / total_tests * 100) if total_tests > 0 else 0,
                "total_execution_time": total_time
            },
            "categories": categories,
            "test_results": [
                {
                    "name": r.test_case.name,
                    "description": r.test_case.description,
                    "category": r.test_case.category,
                    "priority": r.test_case.priority,
                    "result": r.result.value,
                    "execution_time": r.execution_time,
                    "output": r.output,
                    "error_message": r.error_message,
                    "config_options": r.test_case.config_options
                }
                for r in self.test_results
            ]
        }
    
    def print_test_report(self):
        """Print human-readable test report"""
        report = self.generate_test_report()
        
        if "error" in report:
            print(f"Error generating report: {report['error']}")
            return
        
        summary = report["summary"]
        
        print("\n" + "=" * 60)
        print("BACKPORTS CONFIGURATION TEST REPORT")
        print("=" * 60)
        
        print(f"\nOverall Results:")
        print(f"  Total Tests: {summary['total_tests']}")
        print(f"  Passed: {summary['passed']} ✅")
        print(f"  Failed: {summary['failed']} ❌")
        print(f"  Errors: {summary['errors']} 💥")
        print(f"  Skipped: {summary['skipped']} ⏭️")
        print(f"  Success Rate: {summary['success_rate']:.1f}%")
        print(f"  Total Time: {summary['total_execution_time']:.2f}s")
        
        # Print category breakdown
        print(f"\nResults by Category:")
        for category, stats in report["categories"].items():
            success_rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            print(f"  {category.title()}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")
        
        # Print failed tests
        failed_tests = [r for r in self.test_results if r.result in [TestResult.FAIL, TestResult.ERROR]]
        if failed_tests:
            print(f"\nFailed Tests:")
            for result in failed_tests:
                icon = "❌" if result.result == TestResult.FAIL else "💥"
                print(f"  {icon} {result.test_case.name}: {result.output or result.error_message}")
    
    def save_report(self, filename: str):
        """Save test report to file"""
        report = self.generate_test_report()
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Test report saved to: {filename}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Automated backports configuration testing')
    parser.add_argument('--kernel-root', default='.', help='Path to kernel source root')
    parser.add_argument('--categories', nargs='+', help='Test categories to run')
    parser.add_argument('--priorities', nargs='+', type=int, help='Test priorities to run (1=high, 2=medium, 3=low)')
    parser.add_argument('--report-file', help='Save test report to file')
    parser.add_argument('--json', action='store_true', help='Output JSON report')
    parser.add_argument('--list-tests', action='store_true', help='List available tests')
    
    args = parser.parse_args()
    
    # Create tester
    tester = BackportsConfigTester(args.kernel_root)
    
    if args.list_tests:
        print("Available test cases:")
        for test in tester.test_cases:
            print(f"  {test.name} ({test.category}, priority {test.priority})")
            print(f"    {test.description}")
        return 0
    
    # Run tests
    results = tester.run_all_tests(
        categories=args.categories,
        priorities=args.priorities
    )
    
    # Generate report
    if args.json:
        report = tester.generate_test_report()
        print(json.dumps(report, indent=2))
    else:
        tester.print_test_report()
    
    # Save report if requested
    if args.report_file:
        tester.save_report(args.report_file)
    
    # Return appropriate exit code
    failed_count = len([r for r in results if r.result in [TestResult.FAIL, TestResult.ERROR]])
    return 1 if failed_count > 0 else 0

if __name__ == "__main__":
    sys.exit(main())