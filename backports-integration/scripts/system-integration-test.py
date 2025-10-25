#!/usr/bin/env python3
"""
Backports System Integration Test

This script performs comprehensive system integration testing by wiring together
all Kconfig components and testing the complete configuration flow from menuconfig
to module installation.
"""

import os
import sys
import json
import tempfile
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import argparse

class IntegrationResult(Enum):
    """Integration test result status"""
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    ERROR = "error"

@dataclass
class IntegrationStep:
    """Represents a system integration step"""
    name: str
    description: str
    command: List[str]
    expected_files: List[str] = field(default_factory=list)
    expected_outputs: List[str] = field(default_factory=list)
    timeout: int = 60
    critical: bool = True

@dataclass
class IntegrationExecution:
    """Represents integration step execution result"""
    step: IntegrationStep
    result: IntegrationResult
    execution_time: float
    output: str = ""
    error_message: str = ""

class SystemIntegrationTester:
    """Comprehensive system integration tester"""
    
    def __init__(self, kernel_root: str = "."):
        self.kernel_root = Path(kernel_root).resolve()
        self.temp_dir = None
        self.original_config = None
        self.integration_steps = []
        self.execution_results = []
        
        # Load integration test steps
        self._load_integration_steps()
    
    def _load_integration_steps(self):
        """Load system integration test steps"""
        
        # Step 1: Validate system prerequisites
        self.integration_steps.append(IntegrationStep(
            name="validate_prerequisites",
            description="Validate system prerequisites and dependencies",
            command=["python3", "backports-integration/scripts/validate-backports-deps.py"],
            expected_outputs=["validation passed", "dependencies satisfied"],
            critical=True
        ))
        
        # Step 2: Test Kconfig syntax and structure
        self.integration_steps.append(IntegrationStep(
            name="validate_kconfig_syntax",
            description="Validate Kconfig syntax and structure",
            command=["python3", "backports-integration/scripts/validate-kconfig-syntax.py"],
            expected_outputs=["syntax validation passed"],
            critical=True
        ))
        
        # Step 3: Test configuration template application
        self.integration_steps.append(IntegrationStep(
            name="test_configuration_templates",
            description="Test configuration template application",
            command=["backports-integration/scripts/kconfig-helper.sh", "template", "basic"],
            expected_outputs=["Template applied successfully"],
            critical=True
        ))
        
        # Step 4: Test dependency resolution
        self.integration_steps.append(IntegrationStep(
            name="test_dependency_resolution",
            description="Test automatic dependency resolution",
            command=["make", "olddefconfig"],
            expected_files=[".config"],
            critical=True
        ))
        
        # Step 5: Test configuration validation
        self.integration_steps.append(IntegrationStep(
            name="test_configuration_validation",
            description="Test comprehensive configuration validation",
            command=["backports-integration/scripts/validate-backports.sh", ".", "config"],
            expected_outputs=["Configuration validation passed"],
            critical=True
        ))
        
        # Step 6: Test consistency checking
        self.integration_steps.append(IntegrationStep(
            name="test_consistency_checking",
            description="Test configuration consistency checking",
            command=["python3", "backports-integration/scripts/consistency-checker.py"],
            expected_outputs=["consistency validation passed"],
            critical=True
        ))
        
        # Step 7: Test Makefile integration
        self.integration_steps.append(IntegrationStep(
            name="test_makefile_integration",
            description="Test Makefile integration and build targets",
            command=["make", "backports_help"],
            expected_outputs=["Backports Integration Makefile"],
            critical=True
        ))
        
        # Step 8: Test build system validation
        self.integration_steps.append(IntegrationStep(
            name="test_build_validation",
            description="Test build system validation",
            command=["make", "backports_validate"],
            expected_outputs=["validation passed"],
            critical=True
        ))
        
        # Step 9: Test module building (if possible)
        self.integration_steps.append(IntegrationStep(
            name="test_module_building",
            description="Test module building process",
            command=["make", "modules", "M=backports-integration"],
            expected_files=["backports-integration/modules.builtin"],
            timeout=300,
            critical=False  # May fail due to missing backports source
        ))
        
        # Step 10: Test error handling and recovery
        self.integration_steps.append(IntegrationStep(
            name="test_error_handling",
            description="Test error handling and automatic recovery",
            command=["backports-integration/scripts/kconfig-helper.sh", "fix"],
            expected_outputs=["Auto-fixed", "No auto-fixable issues found"],
            critical=True
        ))
        
        # Step 11: Test comprehensive validation suite
        self.integration_steps.append(IntegrationStep(
            name="test_comprehensive_validation",
            description="Test comprehensive validation suite",
            command=["backports-integration/scripts/validate-backports.sh", ".", "full"],
            expected_outputs=["validation complete"],
            timeout=120,
            critical=True
        ))
        
        # Step 12: Test configuration cleanup
        self.integration_steps.append(IntegrationStep(
            name="test_configuration_cleanup",
            description="Test configuration cleanup and maintenance",
            command=["make", "backports_clean"],
            expected_outputs=["Cleaning backports"],
            critical=True
        ))
    
    def setup_integration_environment(self):
        """Set up integration test environment"""
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp(prefix="backports_integration_")
        
        # Backup original configuration
        config_file = self.kernel_root / ".config"
        if config_file.exists():
            self.original_config = config_file.read_text()
        
        print(f"🔧 Integration test environment set up in {self.temp_dir}")
    
    def cleanup_integration_environment(self):
        """Clean up integration test environment"""
        # Restore original configuration
        if self.original_config:
            config_file = self.kernel_root / ".config"
            config_file.write_text(self.original_config)
        
        # Clean up temporary files
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
        
        # Clean build artifacts
        try:
            subprocess.run(["make", "backports_clean"], 
                         cwd=self.kernel_root, capture_output=True, timeout=30)
        except:
            pass
        
        print("🧹 Integration test environment cleaned up")
    
    def run_integration_step(self, step: IntegrationStep) -> IntegrationExecution:
        """Run a single integration step"""
        start_time = time.time()
        
        try:
            print(f"  Running: {step.description}")
            
            # Execute command
            result = subprocess.run(
                step.command,
                cwd=self.kernel_root,
                capture_output=True,
                text=True,
                timeout=step.timeout
            )
            
            output = result.stdout + result.stderr
            execution_time = time.time() - start_time
            
            # Check expected outputs
            missing_outputs = []
            if step.expected_outputs:
                for expected_output in step.expected_outputs:
                    if expected_output.lower() not in output.lower():
                        missing_outputs.append(expected_output)
            
            # Check expected files
            missing_files = []
            for expected_file in step.expected_files:
                file_path = self.kernel_root / expected_file
                if not file_path.exists():
                    missing_files.append(expected_file)
            
            # Determine result
            if result.returncode == 0 and not missing_outputs and not missing_files:
                test_result = IntegrationResult.PASS
                error_msg = ""
            elif result.returncode != 0:
                test_result = IntegrationResult.FAIL
                error_msg = f"Command failed with exit code {result.returncode}"
            elif missing_outputs or missing_files:
                test_result = IntegrationResult.FAIL
                error_msg = f"Missing outputs: {missing_outputs}, files: {missing_files}"
            else:
                test_result = IntegrationResult.PASS
                error_msg = ""
            
            return IntegrationExecution(
                step=step,
                result=test_result,
                execution_time=execution_time,
                output=output,
                error_message=error_msg
            )
        
        except subprocess.TimeoutExpired:
            return IntegrationExecution(
                step=step,
                result=IntegrationResult.ERROR,
                execution_time=time.time() - start_time,
                error_message=f"Step timeout after {step.timeout} seconds"
            )
        
        except Exception as e:
            return IntegrationExecution(
                step=step,
                result=IntegrationResult.ERROR,
                execution_time=time.time() - start_time,
                error_message=str(e)
            )
    
    def run_complete_integration_test(self) -> List[IntegrationExecution]:
        """Run complete system integration test"""
        print("🚀 Starting Complete System Integration Test")
        print("=" * 60)
        
        # Set up environment
        self.setup_integration_environment()
        
        try:
            results = []
            critical_failure = False
            
            for i, step in enumerate(self.integration_steps, 1):
                print(f"\n[{i}/{len(self.integration_steps)}] {step.name}")
                
                # Skip non-critical steps if we had critical failures
                if critical_failure and not step.critical:
                    execution = IntegrationExecution(
                        step=step,
                        result=IntegrationResult.SKIP,
                        execution_time=0,
                        error_message="Skipped due to previous critical failure"
                    )
                    results.append(execution)
                    print("  ⏭️  SKIPPED (previous critical failure)")
                    continue
                
                execution = self.run_integration_step(step)
                results.append(execution)
                
                # Print result
                status_icon = {
                    IntegrationResult.PASS: "✅",
                    IntegrationResult.FAIL: "❌",
                    IntegrationResult.SKIP: "⏭️",
                    IntegrationResult.ERROR: "💥"
                }[execution.result]
                
                print(f"  {status_icon} {execution.result.value.upper()} ({execution.execution_time:.2f}s)")
                
                if execution.error_message:
                    print(f"    Error: {execution.error_message}")
                
                # Check for critical failure
                if step.critical and execution.result in [IntegrationResult.FAIL, IntegrationResult.ERROR]:
                    critical_failure = True
                    print(f"    ⚠️  Critical step failed - may skip non-critical steps")
            
            self.execution_results = results
            return results
        
        finally:
            # Clean up environment
            self.cleanup_integration_environment()
    
    def test_configuration_flow(self) -> Dict[str, Any]:
        """Test complete configuration flow from menuconfig to installation"""
        print("\n🔄 Testing Complete Configuration Flow")
        print("-" * 40)
        
        flow_steps = [
            "Apply configuration template",
            "Resolve dependencies", 
            "Validate configuration",
            "Check consistency",
            "Prepare for build"
        ]
        
        flow_results = {}
        
        try:
            # Step 1: Apply template
            print("1. Applying basic configuration template...")
            result = subprocess.run([
                "backports-integration/scripts/kconfig-helper.sh", "template", "basic"
            ], cwd=self.kernel_root, capture_output=True, text=True, timeout=30)
            
            flow_results["template_application"] = {
                "success": result.returncode == 0,
                "output": result.stdout + result.stderr
            }
            
            if result.returncode == 0:
                print("  ✅ Template applied successfully")
            else:
                print("  ❌ Template application failed")
                return flow_results
            
            # Step 2: Resolve dependencies
            print("2. Resolving dependencies...")
            result = subprocess.run([
                "make", "olddefconfig"
            ], cwd=self.kernel_root, capture_output=True, text=True, timeout=60)
            
            flow_results["dependency_resolution"] = {
                "success": result.returncode == 0,
                "output": result.stdout + result.stderr
            }
            
            if result.returncode == 0:
                print("  ✅ Dependencies resolved")
            else:
                print("  ❌ Dependency resolution failed")
                return flow_results
            
            # Step 3: Validate configuration
            print("3. Validating configuration...")
            result = subprocess.run([
                "backports-integration/scripts/validate-backports.sh", ".", "config"
            ], cwd=self.kernel_root, capture_output=True, text=True, timeout=60)
            
            flow_results["configuration_validation"] = {
                "success": result.returncode == 0,
                "output": result.stdout + result.stderr
            }
            
            if result.returncode == 0:
                print("  ✅ Configuration validated")
            else:
                print("  ❌ Configuration validation failed")
                return flow_results
            
            # Step 4: Check consistency
            print("4. Checking consistency...")
            result = subprocess.run([
                "python3", "backports-integration/scripts/consistency-checker.py"
            ], cwd=self.kernel_root, capture_output=True, text=True, timeout=60)
            
            flow_results["consistency_check"] = {
                "success": result.returncode == 0,
                "output": result.stdout + result.stderr
            }
            
            if result.returncode == 0:
                print("  ✅ Consistency check passed")
            else:
                print("  ❌ Consistency check failed")
                return flow_results
            
            # Step 5: Test build preparation
            print("5. Testing build preparation...")
            result = subprocess.run([
                "make", "backports_validate"
            ], cwd=self.kernel_root, capture_output=True, text=True, timeout=60)
            
            flow_results["build_preparation"] = {
                "success": result.returncode == 0,
                "output": result.stdout + result.stderr
            }
            
            if result.returncode == 0:
                print("  ✅ Build preparation successful")
            else:
                print("  ❌ Build preparation failed")
            
            flow_results["overall_success"] = all(
                step["success"] for step in flow_results.values() 
                if isinstance(step, dict) and "success" in step
            )
            
        except Exception as e:
            flow_results["error"] = str(e)
            flow_results["overall_success"] = False
        
        return flow_results
    
    def test_error_recovery(self) -> Dict[str, Any]:
        """Test error handling and recovery mechanisms"""
        print("\n🔧 Testing Error Recovery Mechanisms")
        print("-" * 40)
        
        recovery_results = {}
        
        try:
            # Create an invalid configuration
            print("1. Creating invalid configuration...")
            config_file = self.kernel_root / ".config"
            invalid_config = """
CONFIG_BACKPORTS=y
CONFIG_BACKPORTS_MAC80211=m
# Missing CONFIG_BACKPORTS_CFG80211 - should cause error
CONFIG_MODULES=y
CONFIG_NET=y
"""
            config_file.write_text(invalid_config)
            print("  ✅ Invalid configuration created")
            
            # Test validation detects error
            print("2. Testing error detection...")
            result = subprocess.run([
                "python3", "backports-integration/scripts/validate-backports-config.py"
            ], cwd=self.kernel_root, capture_output=True, text=True, timeout=30)
            
            error_detected = result.returncode != 0 or "error" in result.stdout.lower()
            recovery_results["error_detection"] = {
                "success": error_detected,
                "output": result.stdout + result.stderr
            }
            
            if error_detected:
                print("  ✅ Error correctly detected")
            else:
                print("  ❌ Error not detected")
                return recovery_results
            
            # Test automatic recovery
            print("3. Testing automatic recovery...")
            result = subprocess.run([
                "backports-integration/scripts/kconfig-helper.sh", "fix"
            ], cwd=self.kernel_root, capture_output=True, text=True, timeout=30)
            
            recovery_results["automatic_recovery"] = {
                "success": result.returncode == 0,
                "output": result.stdout + result.stderr
            }
            
            if result.returncode == 0:
                print("  ✅ Automatic recovery successful")
            else:
                print("  ❌ Automatic recovery failed")
                return recovery_results
            
            # Test validation after recovery
            print("4. Testing validation after recovery...")
            result = subprocess.run([
                "python3", "backports-integration/scripts/validate-backports-config.py"
            ], cwd=self.kernel_root, capture_output=True, text=True, timeout=30)
            
            recovery_results["post_recovery_validation"] = {
                "success": result.returncode == 0,
                "output": result.stdout + result.stderr
            }
            
            if result.returncode == 0:
                print("  ✅ Post-recovery validation passed")
            else:
                print("  ❌ Post-recovery validation failed")
            
            recovery_results["overall_success"] = all(
                step["success"] for step in recovery_results.values() 
                if isinstance(step, dict) and "success" in step
            )
            
        except Exception as e:
            recovery_results["error"] = str(e)
            recovery_results["overall_success"] = False
        
        return recovery_results
    
    def generate_integration_report(self) -> Dict[str, Any]:
        """Generate comprehensive integration test report"""
        if not self.execution_results:
            return {"error": "No integration test results available"}
        
        # Calculate statistics
        total_steps = len(self.execution_results)
        passed = len([r for r in self.execution_results if r.result == IntegrationResult.PASS])
        failed = len([r for r in self.execution_results if r.result == IntegrationResult.FAIL])
        errors = len([r for r in self.execution_results if r.result == IntegrationResult.ERROR])
        skipped = len([r for r in self.execution_results if r.result == IntegrationResult.SKIP])
        
        # Calculate critical vs non-critical
        critical_steps = [r for r in self.execution_results if r.step.critical]
        critical_passed = len([r for r in critical_steps if r.result == IntegrationResult.PASS])
        critical_failed = len([r for r in critical_steps if r.result in [IntegrationResult.FAIL, IntegrationResult.ERROR]])
        
        # Calculate execution time
        total_time = sum(r.execution_time for r in self.execution_results)
        
        return {
            "summary": {
                "total_steps": total_steps,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "skipped": skipped,
                "success_rate": (passed / total_steps * 100) if total_steps > 0 else 0,
                "critical_steps": len(critical_steps),
                "critical_passed": critical_passed,
                "critical_failed": critical_failed,
                "critical_success": critical_failed == 0,
                "total_execution_time": total_time
            },
            "step_results": [
                {
                    "name": r.step.name,
                    "description": r.step.description,
                    "result": r.result.value,
                    "execution_time": r.execution_time,
                    "critical": r.step.critical,
                    "error_message": r.error_message
                }
                for r in self.execution_results
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
        print("SYSTEM INTEGRATION TEST REPORT")
        print("=" * 60)
        
        print(f"\nOverall Results:")
        print(f"  Total Steps: {summary['total_steps']}")
        print(f"  Passed: {summary['passed']} ✅")
        print(f"  Failed: {summary['failed']} ❌")
        print(f"  Errors: {summary['errors']} 💥")
        print(f"  Skipped: {summary['skipped']} ⏭️")
        print(f"  Success Rate: {summary['success_rate']:.1f}%")
        print(f"  Total Time: {summary['total_execution_time']:.2f}s")
        
        print(f"\nCritical Steps:")
        print(f"  Total Critical: {summary['critical_steps']}")
        print(f"  Critical Passed: {summary['critical_passed']} ✅")
        print(f"  Critical Failed: {summary['critical_failed']} ❌")
        print(f"  Critical Success: {'✅ YES' if summary['critical_success'] else '❌ NO'}")
        
        # Print failed steps
        failed_steps = [r for r in self.execution_results 
                       if r.result in [IntegrationResult.FAIL, IntegrationResult.ERROR]]
        if failed_steps:
            print(f"\nFailed Steps:")
            for result in failed_steps:
                icon = "❌" if result.result == IntegrationResult.FAIL else "💥"
                critical_text = " (CRITICAL)" if result.step.critical else ""
                print(f"  {icon} {result.step.name}{critical_text}: {result.error_message}")
        
        # Overall assessment
        if summary['critical_success'] and summary['success_rate'] >= 80:
            print(f"\n🎉 SYSTEM INTEGRATION: SUCCESS")
            print("   All critical components integrated successfully")
        elif summary['critical_success']:
            print(f"\n⚠️  SYSTEM INTEGRATION: PARTIAL SUCCESS")
            print("   Critical components work, but some non-critical issues exist")
        else:
            print(f"\n❌ SYSTEM INTEGRATION: FAILURE")
            print("   Critical integration issues detected")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Backports system integration tester')
    parser.add_argument('--kernel-root', default='.', help='Path to kernel source root')
    parser.add_argument('--test-flow', action='store_true', help='Test configuration flow')
    parser.add_argument('--test-recovery', action='store_true', help='Test error recovery')
    parser.add_argument('--json', action='store_true', help='Output JSON report')
    parser.add_argument('--report-file', help='Save report to file')
    
    args = parser.parse_args()
    
    # Create integration tester
    tester = SystemIntegrationTester(args.kernel_root)
    
    # Run integration tests
    results = tester.run_complete_integration_test()
    
    # Test configuration flow if requested
    flow_results = None
    if args.test_flow:
        flow_results = tester.test_configuration_flow()
    
    # Test error recovery if requested
    recovery_results = None
    if args.test_recovery:
        recovery_results = tester.test_error_recovery()
    
    # Generate report
    if args.json:
        report = tester.generate_integration_report()
        if flow_results:
            report["configuration_flow"] = flow_results
        if recovery_results:
            report["error_recovery"] = recovery_results
        print(json.dumps(report, indent=2))
    else:
        tester.print_integration_report()
        
        if flow_results:
            print(f"\nConfiguration Flow Test: {'✅ PASS' if flow_results.get('overall_success') else '❌ FAIL'}")
        
        if recovery_results:
            print(f"Error Recovery Test: {'✅ PASS' if recovery_results.get('overall_success') else '❌ FAIL'}")
    
    # Save report if requested
    if args.report_file:
        report = tester.generate_integration_report()
        if flow_results:
            report["configuration_flow"] = flow_results
        if recovery_results:
            report["error_recovery"] = recovery_results
        
        with open(args.report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Integration test report saved to: {args.report_file}")
    
    # Return appropriate exit code
    report = tester.generate_integration_report()
    critical_success = report["summary"]["critical_success"]
    return 0 if critical_success else 1

if __name__ == "__main__":
    sys.exit(main())