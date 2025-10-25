#!/usr/bin/env python3
"""
Final Integration Validator

This script performs the ultimate validation of the complete backports Kconfig
integration system by running all validation suites and providing a comprehensive
assessment of system readiness.
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import argparse

@dataclass
class ValidationSuite:
    """Represents a validation suite"""
    name: str
    description: str
    script: str
    args: List[str]
    timeout: int = 300
    critical: bool = True

class FinalIntegrationValidator:
    """Final comprehensive integration validator"""
    
    def __init__(self, kernel_root: str = "."):
        self.kernel_root = Path(kernel_root).resolve()
        self.validation_suites = []
        self.suite_results = {}
        
        # Load validation suites
        self._load_validation_suites()
    
    def _load_validation_suites(self):
        """Load all validation suites"""
        
        self.validation_suites = [
            ValidationSuite(
                name="system_integration",
                description="Complete system integration testing",
                script="backports-integration/scripts/system-integration-test.py",
                args=["--test-flow", "--test-recovery"],
                critical=True
            ),
            
            ValidationSuite(
                name="build_system_validation",
                description="Build system integration validation",
                script="backports-integration/scripts/build-system-validator.py",
                args=[],
                critical=True
            ),
            
            ValidationSuite(
                name="comprehensive_config_testing",
                description="Comprehensive configuration testing",
                script="backports-integration/scripts/comprehensive-config-tester.py",
                args=["--priorities", "1", "2"],
                timeout=600,
                critical=True
            ),
            
            ValidationSuite(
                name="configuration_testing",
                description="Automated configuration testing",
                script="backports-integration/scripts/test-backports-config.py",
                args=["--priorities", "1"],
                critical=True
            ),
            
            ValidationSuite(
                name="build_testing",
                description="Build testing framework",
                script="backports-integration/scripts/test-backports-build.py",
                args=["--priorities", "1"],
                timeout=600,
                critical=False
            ),
            
            ValidationSuite(
                name="integration_testing",
                description="Integration testing suite",
                script="backports-integration/scripts/test-backports-integration.py",
                args=["--priorities", "1"],
                critical=False
            )
        ]
    
    def run_validation_suite(self, suite: ValidationSuite) -> Dict[str, Any]:
        """Run a single validation suite"""
        print(f"🔍 Running {suite.name}...")
        print(f"   {suite.description}")
        
        start_time = time.time()
        
        try:
            # Build command
            cmd = ["python3", suite.script] + suite.args + ["--json"]
            
            # Run validation suite
            result = subprocess.run(
                cmd,
                cwd=self.kernel_root,
                capture_output=True,
                text=True,
                timeout=suite.timeout
            )
            
            execution_time = time.time() - start_time
            
            # Parse JSON output if available
            suite_report = {}
            if result.stdout.strip():
                try:
                    suite_report = json.loads(result.stdout)
                except json.JSONDecodeError:
                    suite_report = {"raw_output": result.stdout}
            
            # Determine success
            success = result.returncode == 0
            
            # Extract key metrics if available
            summary = suite_report.get("summary", {})
            
            return {
                "name": suite.name,
                "description": suite.description,
                "success": success,
                "critical": suite.critical,
                "execution_time": execution_time,
                "return_code": result.returncode,
                "summary": summary,
                "full_report": suite_report,
                "error_output": result.stderr if result.stderr else None
            }
        
        except subprocess.TimeoutExpired:
            return {
                "name": suite.name,
                "description": suite.description,
                "success": False,
                "critical": suite.critical,
                "execution_time": time.time() - start_time,
                "error": f"Timeout after {suite.timeout} seconds"
            }
        
        except Exception as e:
            return {
                "name": suite.name,
                "description": suite.description,
                "success": False,
                "critical": suite.critical,
                "execution_time": time.time() - start_time,
                "error": str(e)
            }
    
    def run_final_validation(self) -> Dict[str, Any]:
        """Run final comprehensive validation"""
        print("🚀 FINAL BACKPORTS INTEGRATION VALIDATION")
        print("=" * 60)
        print("Running comprehensive validation of all system components...")
        print()
        
        overall_start = time.time()
        results = []
        critical_failure = False
        
        for i, suite in enumerate(self.validation_suites, 1):
            print(f"[{i}/{len(self.validation_suites)}] {suite.name}")
            
            # Skip non-critical suites if critical failure occurred
            if critical_failure and not suite.critical:
                result = {
                    "name": suite.name,
                    "description": suite.description,
                    "success": False,
                    "critical": suite.critical,
                    "execution_time": 0,
                    "skipped": True,
                    "skip_reason": "Previous critical failure"
                }
                results.append(result)
                print("   ⏭️  SKIPPED (previous critical failure)")
                continue
            
            # Run validation suite
            result = self.run_validation_suite(suite)
            results.append(result)
            
            # Print result
            if result["success"]:
                print(f"   ✅ PASSED ({result['execution_time']:.1f}s)")
            else:
                icon = "💥" if suite.critical else "❌"
                print(f"   {icon} FAILED ({result['execution_time']:.1f}s)")
                if "error" in result:
                    print(f"      Error: {result['error']}")
                
                # Check for critical failure
                if suite.critical:
                    critical_failure = True
                    print("      ⚠️  Critical validation failed")
            
            print()
        
        total_time = time.time() - overall_start
        
        # Calculate overall statistics
        total_suites = len(results)
        passed_suites = len([r for r in results if r["success"]])
        failed_suites = len([r for r in results if not r["success"] and not r.get("skipped")])
        skipped_suites = len([r for r in results if r.get("skipped")])
        
        critical_suites = [r for r in results if r["critical"]]
        critical_passed = len([r for r in critical_suites if r["success"]])
        critical_failed = len([r for r in critical_suites if not r["success"]])
        
        # Generate final report
        final_report = {
            "overall_summary": {
                "total_suites": total_suites,
                "passed": passed_suites,
                "failed": failed_suites,
                "skipped": skipped_suites,
                "success_rate": (passed_suites / total_suites * 100) if total_suites > 0 else 0,
                "critical_suites": len(critical_suites),
                "critical_passed": critical_passed,
                "critical_failed": critical_failed,
                "critical_success": critical_failed == 0,
                "total_execution_time": total_time
            },
            "suite_results": results,
            "validation_timestamp": time.time()
        }
        
        self.suite_results = final_report
        return final_report
    
    def print_final_report(self):
        """Print final validation report"""
        if not self.suite_results:
            print("No validation results available")
            return
        
        summary = self.suite_results["overall_summary"]
        
        print("=" * 60)
        print("FINAL INTEGRATION VALIDATION REPORT")
        print("=" * 60)
        
        print(f"\nOverall Results:")
        print(f"  Total Validation Suites: {summary['total_suites']}")
        print(f"  Passed: {summary['passed']} ✅")
        print(f"  Failed: {summary['failed']} ❌")
        print(f"  Skipped: {summary['skipped']} ⏭️")
        print(f"  Success Rate: {summary['success_rate']:.1f}%")
        print(f"  Total Time: {summary['total_execution_time']:.1f}s")
        
        print(f"\nCritical Validation Suites:")
        print(f"  Total Critical: {summary['critical_suites']}")
        print(f"  Critical Passed: {summary['critical_passed']} ✅")
        print(f"  Critical Failed: {summary['critical_failed']} ❌")
        print(f"  Critical Success: {'✅ YES' if summary['critical_success'] else '❌ NO'}")
        
        # Print detailed results
        print(f"\nDetailed Results:")
        for result in self.suite_results["suite_results"]:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            if result.get("skipped"):
                status = "⏭️ SKIP"
            
            critical_text = " (CRITICAL)" if result["critical"] else ""
            print(f"  {status} {result['name']}{critical_text}")
            print(f"       {result['description']}")
            
            # Print suite-specific metrics if available
            if "summary" in result and result["summary"]:
                suite_summary = result["summary"]
                if "success_rate" in suite_summary:
                    print(f"       Success Rate: {suite_summary['success_rate']:.1f}%")
                if "total_tests" in suite_summary:
                    print(f"       Tests: {suite_summary['total_tests']}")
        
        # Final assessment
        print(f"\n" + "=" * 60)
        if summary['critical_success'] and summary['success_rate'] >= 90:
            print("🎉 FINAL ASSESSMENT: SYSTEM READY FOR PRODUCTION")
            print("   All critical components validated successfully")
            print("   Backports Kconfig integration is fully functional")
        elif summary['critical_success'] and summary['success_rate'] >= 75:
            print("✅ FINAL ASSESSMENT: SYSTEM READY WITH MINOR ISSUES")
            print("   Critical components work correctly")
            print("   Some non-critical issues may need attention")
        elif summary['critical_success']:
            print("⚠️  FINAL ASSESSMENT: SYSTEM FUNCTIONAL BUT NEEDS IMPROVEMENT")
            print("   Critical components work but significant issues exist")
            print("   Review failed validation suites before deployment")
        else:
            print("❌ FINAL ASSESSMENT: SYSTEM NOT READY")
            print("   Critical validation failures detected")
            print("   System requires fixes before deployment")
        
        print("=" * 60)
    
    def generate_deployment_readiness_report(self) -> Dict[str, Any]:
        """Generate deployment readiness assessment"""
        if not self.suite_results:
            return {"error": "No validation results available"}
        
        summary = self.suite_results["overall_summary"]
        
        # Determine readiness level
        if summary['critical_success'] and summary['success_rate'] >= 90:
            readiness = "production_ready"
            recommendation = "System is ready for production deployment"
        elif summary['critical_success'] and summary['success_rate'] >= 75:
            readiness = "ready_with_issues"
            recommendation = "System is ready but monitor for issues"
        elif summary['critical_success']:
            readiness = "functional_needs_improvement"
            recommendation = "System works but needs improvement before deployment"
        else:
            readiness = "not_ready"
            recommendation = "System requires fixes before deployment"
        
        # Identify key issues
        failed_critical = [r for r in self.suite_results["suite_results"] 
                          if r["critical"] and not r["success"]]
        failed_non_critical = [r for r in self.suite_results["suite_results"] 
                              if not r["critical"] and not r["success"] and not r.get("skipped")]
        
        return {
            "readiness_level": readiness,
            "recommendation": recommendation,
            "overall_success_rate": summary['success_rate'],
            "critical_success": summary['critical_success'],
            "failed_critical_suites": [r["name"] for r in failed_critical],
            "failed_non_critical_suites": [r["name"] for r in failed_non_critical],
            "validation_summary": summary,
            "timestamp": self.suite_results["validation_timestamp"]
        }

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Final integration validator')
    parser.add_argument('--kernel-root', default='.', help='Path to kernel source root')
    parser.add_argument('--json', action='store_true', help='Output JSON report')
    parser.add_argument('--report-file', help='Save report to file')
    parser.add_argument('--readiness-report', help='Save deployment readiness report')
    
    args = parser.parse_args()
    
    # Create final validator
    validator = FinalIntegrationValidator(args.kernel_root)
    
    # Run final validation
    results = validator.run_final_validation()
    
    # Generate reports
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        validator.print_final_report()
    
    # Save full report if requested
    if args.report_file:
        with open(args.report_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nFinal validation report saved to: {args.report_file}")
    
    # Save readiness report if requested
    if args.readiness_report:
        readiness = validator.generate_deployment_readiness_report()
        with open(args.readiness_report, 'w') as f:
            json.dump(readiness, f, indent=2)
        print(f"Deployment readiness report saved to: {args.readiness_report}")
    
    # Return appropriate exit code
    summary = results["overall_summary"]
    return 0 if summary["critical_success"] else 1

if __name__ == "__main__":
    sys.exit(main())