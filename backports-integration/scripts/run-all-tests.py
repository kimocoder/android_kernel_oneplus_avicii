#!/usr/bin/env python3
"""
Comprehensive Backports Test Runner

This script runs all backports tests including configuration testing,
build testing, and integration testing in a unified interface.
"""

import os
import sys
import json
import argparse
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class TestSuiteResult:
    """Results from a test suite"""
    name: str
    success: bool
    execution_time: float
    total_tests: int
    passed: int
    failed: int
    skipped: int
    report_file: Optional[str] = None

class ComprehensiveTestRunner:
    """Runs all backports test suites"""
    
    def __init__(self, kernel_root: str = "."):
        self.kernel_root = Path(kernel_root).resolve()
        self.results: List[TestSuiteResult] = []
    
    def run_configuration_tests(self, categories: Optional[List[str]] = None,
                               priorities: Optional[List[int]] = None) -> TestSuiteResult:
        """Run configuration tests"""
        print("🔧 Running Configuration Tests...")
        start_time = time.time()
        
        cmd = [
            "python3",
            str(self.kernel_root / "backports-integration/scripts/test-backports-config.py"),
            "--kernel-root", str(self.kernel_root),
            "--json"
        ]
        
        if categories:
            cmd.extend(["--categories"] + categories)
        if priorities:
            cmd.extend(["--priorities"] + [str(p) for p in priorities])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                try:
                    report = json.loads(result.stdout)
                    summary = report.get("summary", {})
                    
                    return TestSuiteResult(
                        name="Configuration Tests",
                        success=True,
                        execution_time=execution_time,
                        total_tests=summary.get("total_tests", 0),
                        passed=summary.get("passed", 0),
                        failed=summary.get("failed", 0),
                        skipped=summary.get("skipped", 0)
                    )
                except json.JSONDecodeError:
                    pass
            
            return TestSuiteResult(
                name="Configuration Tests",
                success=False,
                execution_time=execution_time,
                total_tests=0,
                passed=0,
                failed=1,
                skipped=0
            )
        
        except subprocess.TimeoutExpired:
            return TestSuiteResult(
                name="Configuration Tests",
                success=False,
                execution_time=time.time() - start_time,
                total_tests=0,
                passed=0,
                failed=1,
                skipped=0
            )
    
    def run_build_tests(self, architectures: Optional[List[str]] = None,
                       priorities: Optional[List[int]] = None) -> TestSuiteResult:
        """Run build tests"""
        print("🏗️  Running Build Tests...")
        start_time = time.time()
        
        cmd = [
            "python3",
            str(self.kernel_root / "backports-integration/scripts/test-backports-build.py"),
            "--kernel-root", str(self.kernel_root),
            "--json"
        ]
        
        if architectures:
            cmd.extend(["--architectures"] + architectures)
        if priorities:
            cmd.extend(["--priorities"] + [str(p) for p in priorities])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                try:
                    report = json.loads(result.stdout)
                    summary = report.get("summary", {})
                    
                    return TestSuiteResult(
                        name="Build Tests",
                        success=True,
                        execution_time=execution_time,
                        total_tests=summary.get("total_builds", 0),
                        passed=summary.get("successful", 0),
                        failed=summary.get("failed", 0) + summary.get("errors", 0),
                        skipped=summary.get("skipped", 0)
                    )
                except json.JSONDecodeError:
                    pass
            
            return TestSuiteResult(
                name="Build Tests",
                success=False,
                execution_time=execution_time,
                total_tests=0,
                passed=0,
                failed=1,
                skipped=0
            )
        
        except subprocess.TimeoutExpired:
            return TestSuiteResult(
                name="Build Tests",
                success=False,
                execution_time=time.time() - start_time,
                total_tests=0,
                passed=0,
                failed=1,
                skipped=0
            )
    
    def run_integration_tests(self, test_types: Optional[List[str]] = None,
                             priorities: Optional[List[int]] = None) -> TestSuiteResult:
        """Run integration tests"""
        print("🔗 Running Integration Tests...")
        start_time = time.time()
        
        cmd = [
            "python3",
            str(self.kernel_root / "backports-integration/scripts/test-backports-integration.py"),
            "--kernel-root", str(self.kernel_root),
            "--json"
        ]
        
        if test_types:
            cmd.extend(["--test-types"] + test_types)
        if priorities:
            cmd.extend(["--priorities"] + [str(p) for p in priorities])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                try:
                    report = json.loads(result.stdout)
                    summary = report.get("summary", {})
                    
                    return TestSuiteResult(
                        name="Integration Tests",
                        success=True,
                        execution_time=execution_time,
                        total_tests=summary.get("total_tests", 0),
                        passed=summary.get("passed", 0),
                        failed=summary.get("failed", 0) + summary.get("errors", 0),
                        skipped=summary.get("skipped", 0)
                    )
                except json.JSONDecodeError:
                    pass
            
            return TestSuiteResult(
                name="Integration Tests",
                success=False,
                execution_time=execution_time,
                total_tests=0,
                passed=0,
                failed=1,
                skipped=0
            )
        
        except subprocess.TimeoutExpired:
            return TestSuiteResult(
                name="Integration Tests",
                success=False,
                execution_time=time.time() - start_time,
                total_tests=0,
                passed=0,
                failed=1,
                skipped=0
            )
    
    def run_all_tests(self, config_categories: Optional[List[str]] = None,
                     build_architectures: Optional[List[str]] = None,
                     integration_types: Optional[List[str]] = None,
                     priorities: Optional[List[int]] = None) -> List[TestSuiteResult]:
        """Run all test suites"""
        
        print("🚀 Starting Comprehensive Backports Testing")
        print("=" * 50)
        
        overall_start = time.time()
        results = []
        
        # Run configuration tests
        config_result = self.run_configuration_tests(config_categories, priorities)
        results.append(config_result)
        self._print_suite_result(config_result)
        
        # Run build tests
        build_result = self.run_build_tests(build_architectures, priorities)
        results.append(build_result)
        self._print_suite_result(build_result)
        
        # Run integration tests
        integration_result = self.run_integration_tests(integration_types, priorities)
        results.append(integration_result)
        self._print_suite_result(integration_result)
        
        overall_time = time.time() - overall_start
        
        # Print overall summary
        self._print_overall_summary(results, overall_time)
        
        self.results = results
        return results
    
    def _print_suite_result(self, result: TestSuiteResult):
        """Print individual test suite result"""
        status_icon = "✅" if result.success else "❌"
        print(f"\n{status_icon} {result.name}")
        print(f"   Tests: {result.total_tests}, Passed: {result.passed}, Failed: {result.failed}, Skipped: {result.skipped}")
        print(f"   Time: {result.execution_time:.1f}s")
    
    def _print_overall_summary(self, results: List[TestSuiteResult], total_time: float):
        """Print overall test summary"""
        print("\n" + "=" * 50)
        print("📊 OVERALL TEST SUMMARY")
        print("=" * 50)
        
        total_tests = sum(r.total_tests for r in results)
        total_passed = sum(r.passed for r in results)
        total_failed = sum(r.failed for r in results)
        total_skipped = sum(r.skipped for r in results)
        
        successful_suites = len([r for r in results if r.success])
        total_suites = len(results)
        
        print(f"\nTest Suites: {successful_suites}/{total_suites} successful")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {total_passed} ✅")
        print(f"Failed: {total_failed} ❌")
        print(f"Skipped: {total_skipped} ⏭️")
        
        if total_tests > 0:
            success_rate = (total_passed / total_tests) * 100
            print(f"Success Rate: {success_rate:.1f}%")
        
        print(f"Total Time: {total_time:.1f}s")
        
        # Overall status
        overall_success = all(r.success for r in results) and total_failed == 0
        status = "🎉 ALL TESTS PASSED!" if overall_success else "⚠️  SOME TESTS FAILED"
        print(f"\n{status}")
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        if not self.results:
            return {"error": "No test results available"}
        
        total_tests = sum(r.total_tests for r in self.results)
        total_passed = sum(r.passed for r in self.results)
        total_failed = sum(r.failed for r in self.results)
        total_skipped = sum(r.skipped for r in self.results)
        total_time = sum(r.execution_time for r in self.results)
        
        successful_suites = len([r for r in self.results if r.success])
        
        return {
            "summary": {
                "test_suites": len(self.results),
                "successful_suites": successful_suites,
                "total_tests": total_tests,
                "passed": total_passed,
                "failed": total_failed,
                "skipped": total_skipped,
                "success_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0,
                "total_execution_time": total_time,
                "overall_success": successful_suites == len(self.results) and total_failed == 0
            },
            "test_suites": [
                {
                    "name": r.name,
                    "success": r.success,
                    "execution_time": r.execution_time,
                    "total_tests": r.total_tests,
                    "passed": r.passed,
                    "failed": r.failed,
                    "skipped": r.skipped
                }
                for r in self.results
            ]
        }
    
    def save_comprehensive_report(self, filename: str):
        """Save comprehensive test report"""
        report = self.generate_comprehensive_report()
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Comprehensive test report saved to: {filename}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Comprehensive backports test runner')
    parser.add_argument('--kernel-root', default='.', help='Path to kernel source root')
    
    # Test filtering options
    parser.add_argument('--config-categories', nargs='+', help='Configuration test categories')
    parser.add_argument('--build-architectures', nargs='+', help='Build test architectures')
    parser.add_argument('--integration-types', nargs='+', help='Integration test types')
    parser.add_argument('--priorities', nargs='+', type=int, help='Test priorities to run')
    
    # Output options
    parser.add_argument('--report-file', help='Save comprehensive report to file')
    parser.add_argument('--json', action='store_true', help='Output JSON report')
    parser.add_argument('--quick', action='store_true', help='Run only high-priority tests')
    
    args = parser.parse_args()
    
    # Set priorities for quick mode
    priorities = [1] if args.quick else args.priorities
    
    # Create test runner
    runner = ComprehensiveTestRunner(args.kernel_root)
    
    # Run all tests
    results = runner.run_all_tests(
        config_categories=args.config_categories,
        build_architectures=args.build_architectures,
        integration_types=args.integration_types,
        priorities=priorities
    )
    
    # Generate report
    if args.json:
        report = runner.generate_comprehensive_report()
        print(json.dumps(report, indent=2))
    
    # Save report if requested
    if args.report_file:
        runner.save_comprehensive_report(args.report_file)
    
    # Return appropriate exit code
    overall_success = all(r.success for r in results)
    total_failed = sum(r.failed for r in results)
    
    return 0 if overall_success and total_failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())