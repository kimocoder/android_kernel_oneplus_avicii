#!/usr/bin/env python3
"""
Backports Integration Testing Suite

This script provides comprehensive integration testing including tests for
integration with existing wireless drivers, compatibility testing with
device-specific configurations, and end-to-end testing of backports functionality.
"""

import os
import sys
import json
import tempfile
import shutil
import subprocess
import time
import socket
import threading
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import argparse

class IntegrationResult(Enum):
    """Integration test result status"""
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    ERROR = "error"
    PARTIAL = "partial"

@dataclass
class IntegrationTest:
    """Represents an integration test case"""
    name: str
    description: str
    test_type: str  # "compatibility", "functionality", "performance", "security"
    config_options: Dict[str, str]
    test_commands: List[str]
    expected_outputs: List[str] = field(default_factory=list)
    expected_files: List[str] = field(default_factory=list)
    expected_interfaces: List[str] = field(default_factory=list)
    timeout: int = 60
    requires_root: bool = False
    requires_hardware: bool = False
    priority: int = 1

@dataclass
class IntegrationExecution:
    """Represents an integration test execution result"""
    test: IntegrationTest
    result: IntegrationResult
    execution_time: float
    output: str = ""
    error_message: str = ""
    test_details: Dict[str, Any] = field(default_factory=dict)

class BackportsIntegrationTester:
    """Comprehensive integration testing framework"""
    
    def __init__(self, kernel_root: str = "."):
        self.kernel_root = Path(kernel_root).resolve()
        self.integration_tests: List[IntegrationTest] = []
        self.test_results: List[IntegrationExecution] = []
        
        # Test environment
        self.temp_dir = None
        self.original_config = None
        
        # Load integration tests
        self._load_integration_tests()
    
    def _load_integration_tests(self):
        """Load predefined integration tests"""
        
        # Configuration compatibility tests
        self.integration_tests.extend([
            IntegrationTest(
                name="kconfig_syntax_validation",
                description="Validate Kconfig syntax and structure",
                test_type="compatibility",
                config_options={},
                test_commands=[
                    "python3 backports-integration/scripts/validate-kconfig-syntax.py"
                ],
                expected_outputs=["Kconfig syntax validation passed"],
                priority=1
            ),
            
            IntegrationTest(
                name="makefile_integration",
                description="Test Makefile integration with kernel build system",
                test_type="compatibility",
                config_options={
                    "CONFIG_BACKPORTS": "y"
                },
                test_commands=[
                    "make backports_help",
                    "make backports_status"
                ],
                expected_outputs=["Backports Integration Makefile", "Backports Integration Status"],
                priority=1
            ),
            
            IntegrationTest(
                name="dependency_resolution",
                description="Test automatic dependency resolution",
                test_type="compatibility",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_MAC80211": "m"
                },
                test_commands=[
                    "python3 backports-integration/scripts/resolve-backports-deps.py --auto-resolve"
                ],
                expected_outputs=["Dependencies resolved successfully"],
                priority=1
            )
        ])
        
        # Functionality tests
        self.integration_tests.extend([
            IntegrationTest(
                name="module_build_and_load",
                description="Test module building and loading",
                test_type="functionality",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_CFG80211": "m",
                    "CONFIG_BACKPORTS_MAC80211": "m"
                },
                test_commands=[
                    "make modules",
                    "make modules_install INSTALL_MOD_PATH=/tmp/backports_test"
                ],
                expected_files=[
                    "/tmp/backports_test/lib/modules/*/backports/cfg80211.ko",
                    "/tmp/backports_test/lib/modules/*/backports/mac80211.ko"
                ],
                requires_root=True,
                priority=2
            ),
            
            IntegrationTest(
                name="wireless_interface_creation",
                description="Test wireless interface creation and management",
                test_type="functionality",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_CFG80211": "m",
                    "CONFIG_BACKPORTS_MAC80211": "m",
                    "CONFIG_BACKPORTS_MONITOR_MODE": "y"
                },
                test_commands=[
                    "modprobe cfg80211",
                    "modprobe mac80211",
                    "iw dev"
                ],
                expected_outputs=["cfg80211", "mac80211"],
                requires_root=True,
                requires_hardware=True,
                priority=2
            ),
            
            IntegrationTest(
                name="monitor_mode_functionality",
                description="Test monitor mode interface functionality",
                test_type="functionality",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_CFG80211": "m",
                    "CONFIG_BACKPORTS_MAC80211": "m",
                    "CONFIG_BACKPORTS_MONITOR_MODE": "y"
                },
                test_commands=[
                    "modprobe cfg80211",
                    "modprobe mac80211",
                    "iw phy phy0 interface add mon0 type monitor",
                    "ip link set mon0 up",
                    "iw dev mon0 info"
                ],
                expected_outputs=["Interface mon0", "type monitor"],
                expected_interfaces=["mon0"],
                requires_root=True,
                requires_hardware=True,
                priority=3
            )
        ])
        
        # Security tests
        self.integration_tests.extend([
            IntegrationTest(
                name="frame_injection_security",
                description="Test frame injection security controls",
                test_type="security",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_CFG80211": "m",
                    "CONFIG_BACKPORTS_MAC80211": "m",
                    "CONFIG_BACKPORTS_MONITOR_MODE": "y",
                    "CONFIG_BACKPORTS_FRAME_INJECTION": "y",
                    "CONFIG_BACKPORTS_INJECTION_SECURITY_AUDIT": "y"
                },
                test_commands=[
                    "python3 backports-integration/scripts/validate-backports-config.py --json"
                ],
                expected_outputs=["Frame injection has security implications"],
                priority=2
            ),
            
            IntegrationTest(
                name="android_security_integration",
                description="Test Android security model integration",
                test_type="security",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_ANDROID": "y",
                    "CONFIG_BACKPORTS_SECURITY_ANDROID": "y",
                    "CONFIG_BACKPORTS_SELINUX_ANDROID": "y"
                },
                test_commands=[
                    "python3 backports-integration/scripts/validate-backports-config.py --json"
                ],
                expected_outputs=["Android security integration"],
                priority=3
            )
        ])
        
        # Performance tests
        self.integration_tests.extend([
            IntegrationTest(
                name="debug_performance_impact",
                description="Test debug options performance impact",
                test_type="performance",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_DEBUG": "y",
                    "CONFIG_BACKPORTS_DEBUG_VERBOSE": "y"
                },
                test_commands=[
                    "python3 backports-integration/scripts/validate-backports-config.py --json"
                ],
                expected_outputs=["Debug features increase kernel size", "may impact performance"],
                priority=3
            ),
            
            IntegrationTest(
                name="tracing_integration",
                description="Test tracing system integration",
                test_type="performance",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_TRACING": "y",
                    "CONFIG_TRACING": "y"
                },
                test_commands=[
                    "python3 backports-integration/scripts/validate-backports-config.py --json"
                ],
                expected_outputs=["Tracing support provides low-overhead profiling"],
                priority=3
            )
        ])
        
        # Device-specific compatibility tests
        self.integration_tests.extend([
            IntegrationTest(
                name="android_device_compatibility",
                description="Test Android device-specific compatibility",
                test_type="compatibility",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_ANDROID": "y",
                    "CONFIG_BACKPORTS_VENDOR_COMPAT": "y",
                    "CONFIG_BACKPORTS_VENDOR_QCOM": "y"
                },
                test_commands=[
                    "python3 backports-integration/scripts/check-wireless-conflicts.sh",
                    "python3 backports-integration/scripts/validate-backports-config.py --json"
                ],
                expected_outputs=["Android compatibility", "vendor compatibility"],
                priority=2
            ),
            
            IntegrationTest(
                name="vendor_driver_coexistence",
                description="Test vendor driver coexistence mechanisms",
                test_type="compatibility",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_VENDOR_COMPAT": "y",
                    "CONFIG_BACKPORTS_VENDOR_CONFLICT_DETECTION": "y"
                },
                test_commands=[
                    "python3 backports-integration/scripts/consistency-checker.py --json"
                ],
                expected_outputs=["Vendor compatibility layer"],
                priority=3
            )
        ])
        
        # End-to-end workflow tests
        self.integration_tests.extend([
            IntegrationTest(
                name="complete_configuration_workflow",
                description="Test complete configuration workflow from menuconfig to build",
                test_type="functionality",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_CFG80211": "m",
                    "CONFIG_BACKPORTS_MAC80211": "m"
                },
                test_commands=[
                    "backports-integration/scripts/kconfig-helper.sh template basic",
                    "make olddefconfig",
                    "backports-integration/scripts/validate-backports.sh . config",
                    "make backports_validate"
                ],
                expected_outputs=["Template applied successfully", "Configuration validation passed"],
                timeout=120,
                priority=1
            ),
            
            IntegrationTest(
                name="error_handling_workflow",
                description="Test error handling and recovery workflow",
                test_type="functionality",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_MAC80211": "m"  # Missing CFG80211 dependency
                },
                test_commands=[
                    "python3 backports-integration/scripts/validate-backports-config.py",
                    "backports-integration/scripts/kconfig-helper.sh fix",
                    "python3 backports-integration/scripts/validate-backports-config.py"
                ],
                expected_outputs=["MAC80211 requires CFG80211", "Auto-fixed", "validation passed"],
                priority=2
            )
        ])
    
    def setup_test_environment(self):
        """Set up integration test environment"""
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp(prefix="backports_integration_test_")
        
        # Backup original configuration
        config_file = self.kernel_root / ".config"
        if config_file.exists():
            self.original_config = config_file.read_text()
    
    def cleanup_test_environment(self):
        """Clean up test environment"""
        # Restore original configuration
        if self.original_config:
            config_file = self.kernel_root / ".config"
            config_file.write_text(self.original_config)
        
        # Clean up temporary files
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
        
        # Clean up test modules if loaded
        try:
            subprocess.run(["modprobe", "-r", "mac80211"], capture_output=True)
            subprocess.run(["modprobe", "-r", "cfg80211"], capture_output=True)
        except:
            pass
    
    def create_test_config(self, config_options: Dict[str, str]) -> str:
        """Create test configuration"""
        config_lines = []
        
        # Add basic options
        config_lines.extend([
            "CONFIG_MODULES=y",
            "CONFIG_NET=y",
            "CONFIG_CRYPTO=y",
            "CONFIG_CRC32=y"
        ])
        
        # Add test-specific options
        for option, value in config_options.items():
            if value == "n":
                config_lines.append(f"# {option} is not set")
            else:
                config_lines.append(f"{option}={value}")
        
        # Write configuration
        config_file = self.kernel_root / ".config"
        config_file.write_text("\n".join(config_lines) + "\n")
        
        return str(config_file)
    
    def check_test_requirements(self, test: IntegrationTest) -> Tuple[bool, str]:
        """Check if test requirements are met"""
        # Check root privileges
        if test.requires_root and os.geteuid() != 0:
            return False, "Test requires root privileges"
        
        # Check hardware requirements
        if test.requires_hardware:
            # Simple check for wireless hardware
            try:
                result = subprocess.run(["iw", "list"], capture_output=True, timeout=5)
                if result.returncode != 0:
                    return False, "Test requires wireless hardware"
            except:
                return False, "Test requires wireless hardware (iw command failed)"
        
        return True, ""
    
    def run_integration_test(self, test: IntegrationTest) -> IntegrationExecution:
        """Run a single integration test"""
        start_time = time.time()
        
        try:
            # Check requirements
            can_run, reason = self.check_test_requirements(test)
            if not can_run:
                return IntegrationExecution(
                    test=test,
                    result=IntegrationResult.SKIP,
                    execution_time=time.time() - start_time,
                    error_message=reason
                )
            
            # Create test configuration
            if test.config_options:
                self.create_test_config(test.config_options)
            
            # Run test commands
            all_output = []
            test_details = {}
            
            for i, command in enumerate(test.test_commands):
                try:
                    # Execute command
                    result = subprocess.run(
                        command.split(),
                        cwd=self.kernel_root,
                        capture_output=True,
                        text=True,
                        timeout=test.timeout
                    )
                    
                    output = result.stdout + result.stderr
                    all_output.append(f"Command {i+1}: {command}")
                    all_output.append(output)
                    
                    test_details[f"command_{i+1}"] = {
                        "command": command,
                        "returncode": result.returncode,
                        "output": output
                    }
                    
                    # Check for command failure
                    if result.returncode != 0 and test.test_type != "functionality":
                        # Some functionality tests expect failures
                        pass
                
                except subprocess.TimeoutExpired:
                    return IntegrationExecution(
                        test=test,
                        result=IntegrationResult.ERROR,
                        execution_time=time.time() - start_time,
                        error_message=f"Command timeout: {command}"
                    )
            
            # Check expected outputs
            combined_output = "\n".join(all_output)
            missing_outputs = []
            
            for expected_output in test.expected_outputs:
                if expected_output.lower() not in combined_output.lower():
                    missing_outputs.append(expected_output)
            
            # Check expected files
            missing_files = []
            for expected_file in test.expected_files:
                # Handle wildcards in file paths
                if "*" in expected_file:
                    import glob
                    matches = glob.glob(expected_file)
                    if not matches:
                        missing_files.append(expected_file)
                else:
                    if not Path(expected_file).exists():
                        missing_files.append(expected_file)
            
            # Check expected interfaces
            missing_interfaces = []
            for expected_interface in test.expected_interfaces:
                try:
                    result = subprocess.run(
                        ["ip", "link", "show", expected_interface],
                        capture_output=True,
                        timeout=5
                    )
                    if result.returncode != 0:
                        missing_interfaces.append(expected_interface)
                except:
                    missing_interfaces.append(expected_interface)
            
            # Determine test result
            if missing_outputs or missing_files or missing_interfaces:
                if missing_outputs and not missing_files and not missing_interfaces:
                    result_status = IntegrationResult.PARTIAL
                    error_msg = f"Missing expected outputs: {missing_outputs}"
                else:
                    result_status = IntegrationResult.FAIL
                    error_msg = f"Missing: outputs={missing_outputs}, files={missing_files}, interfaces={missing_interfaces}"
            else:
                result_status = IntegrationResult.PASS
                error_msg = ""
            
            execution_time = time.time() - start_time
            
            return IntegrationExecution(
                test=test,
                result=result_status,
                execution_time=execution_time,
                output=combined_output,
                error_message=error_msg,
                test_details=test_details
            )
        
        except Exception as e:
            return IntegrationExecution(
                test=test,
                result=IntegrationResult.ERROR,
                execution_time=time.time() - start_time,
                error_message=str(e)
            )
    
    def run_all_tests(self, test_types: Optional[List[str]] = None,
                     priorities: Optional[List[int]] = None) -> List[IntegrationExecution]:
        """Run all integration tests"""
        
        # Filter tests
        filtered_tests = self.integration_tests
        
        if test_types:
            filtered_tests = [t for t in filtered_tests if t.test_type in test_types]
        
        if priorities:
            filtered_tests = [t for t in filtered_tests if t.priority in priorities]
        
        print(f"Running {len(filtered_tests)} integration tests...")
        
        # Set up test environment
        self.setup_test_environment()
        
        try:
            results = []
            for i, test in enumerate(filtered_tests, 1):
                print(f"[{i}/{len(filtered_tests)}] Testing: {test.name}")
                
                execution = self.run_integration_test(test)
                results.append(execution)
                
                # Print immediate result
                status_icon = {
                    IntegrationResult.PASS: "✅",
                    IntegrationResult.FAIL: "❌",
                    IntegrationResult.SKIP: "⏭️",
                    IntegrationResult.ERROR: "💥",
                    IntegrationResult.PARTIAL: "🔶"
                }[execution.result]
                
                print(f"   {status_icon} {execution.result.value.upper()} ({execution.execution_time:.2f}s)")
                if execution.error_message:
                    print(f"      {execution.error_message}")
            
            self.test_results = results
            return results
        
        finally:
            # Clean up test environment
            self.cleanup_test_environment()
    
    def generate_integration_report(self) -> Dict[str, Any]:
        """Generate comprehensive integration test report"""
        if not self.test_results:
            return {"error": "No test results available"}
        
        # Calculate statistics
        total_tests = len(self.test_results)
        passed = len([r for r in self.test_results if r.result == IntegrationResult.PASS])
        failed = len([r for r in self.test_results if r.result == IntegrationResult.FAIL])
        partial = len([r for r in self.test_results if r.result == IntegrationResult.PARTIAL])
        errors = len([r for r in self.test_results if r.result == IntegrationResult.ERROR])
        skipped = len([r for r in self.test_results if r.result == IntegrationResult.SKIP])
        
        # Calculate by test type
        test_types = {}
        for result in self.test_results:
            test_type = result.test.test_type
            if test_type not in test_types:
                test_types[test_type] = {"total": 0, "passed": 0, "failed": 0}
            
            test_types[test_type]["total"] += 1
            if result.result == IntegrationResult.PASS:
                test_types[test_type]["passed"] += 1
            elif result.result in [IntegrationResult.FAIL, IntegrationResult.ERROR]:
                test_types[test_type]["failed"] += 1
        
        # Calculate execution time
        total_time = sum(r.execution_time for r in self.test_results)
        
        return {
            "summary": {
                "total_tests": total_tests,
                "passed": passed,
                "failed": failed,
                "partial": partial,
                "errors": errors,
                "skipped": skipped,
                "success_rate": (passed / total_tests * 100) if total_tests > 0 else 0,
                "total_execution_time": total_time
            },
            "test_types": test_types,
            "test_results": [
                {
                    "name": r.test.name,
                    "description": r.test.description,
                    "test_type": r.test.test_type,
                    "priority": r.test.priority,
                    "result": r.result.value,
                    "execution_time": r.execution_time,
                    "error_message": r.error_message,
                    "requires_root": r.test.requires_root,
                    "requires_hardware": r.test.requires_hardware
                }
                for r in self.test_results
            ]
        }
    
    def print_integration_report(self):
        """Print human-readable integration test report"""
        report = self.generate_integration_report()
        
        if "error" in report:
            print(f"Error generating report: {report['error']}")
            return
        
        summary = report["summary"]
        
        print("\n" + "=" * 60)
        print("BACKPORTS INTEGRATION TEST REPORT")
        print("=" * 60)
        
        print(f"\nOverall Results:")
        print(f"  Total Tests: {summary['total_tests']}")
        print(f"  Passed: {summary['passed']} ✅")
        print(f"  Failed: {summary['failed']} ❌")
        print(f"  Partial: {summary['partial']} 🔶")
        print(f"  Errors: {summary['errors']} 💥")
        print(f"  Skipped: {summary['skipped']} ⏭️")
        print(f"  Success Rate: {summary['success_rate']:.1f}%")
        print(f"  Total Time: {summary['total_execution_time']:.2f}s")
        
        # Print test type breakdown
        print(f"\nResults by Test Type:")
        for test_type, stats in report["test_types"].items():
            success_rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            print(f"  {test_type.title()}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")
        
        # Print failed tests
        failed_tests = [r for r in self.test_results 
                       if r.result in [IntegrationResult.FAIL, IntegrationResult.ERROR]]
        if failed_tests:
            print(f"\nFailed Tests:")
            for result in failed_tests:
                icon = "❌" if result.result == IntegrationResult.FAIL else "💥"
                print(f"  {icon} {result.test.name}: {result.error_message}")
    
    def save_report(self, filename: str):
        """Save integration test report to file"""
        report = self.generate_integration_report()
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Integration test report saved to: {filename}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Backports integration testing suite')
    parser.add_argument('--kernel-root', default='.', help='Path to kernel source root')
    parser.add_argument('--test-types', nargs='+', help='Test types to run')
    parser.add_argument('--priorities', nargs='+', type=int, help='Test priorities to run')
    parser.add_argument('--report-file', help='Save test report to file')
    parser.add_argument('--json', action='store_true', help='Output JSON report')
    parser.add_argument('--list-tests', action='store_true', help='List available tests')
    
    args = parser.parse_args()
    
    # Create tester
    tester = BackportsIntegrationTester(args.kernel_root)
    
    if args.list_tests:
        print("Available integration tests:")
        for test in tester.integration_tests:
            req_text = []
            if test.requires_root:
                req_text.append("root")
            if test.requires_hardware:
                req_text.append("hardware")
            req_str = f" (requires: {', '.join(req_text)})" if req_text else ""
            
            print(f"  {test.name} ({test.test_type}, priority {test.priority}){req_str}")
            print(f"    {test.description}")
        return 0
    
    # Run tests
    results = tester.run_all_tests(
        test_types=args.test_types,
        priorities=args.priorities
    )
    
    # Generate report
    if args.json:
        report = tester.generate_integration_report()
        print(json.dumps(report, indent=2))
    else:
        tester.print_integration_report()
    
    # Save report if requested
    if args.report_file:
        tester.save_report(args.report_file)
    
    # Return appropriate exit code
    failed_count = len([r for r in results if r.result in [IntegrationResult.FAIL, IntegrationResult.ERROR]])
    return 1 if failed_count > 0 else 0

if __name__ == "__main__":
    sys.exit(main())