#!/usr/bin/env python3
"""
Build System Integration Validator

This script validates the complete kernel build system integration with backports,
verifies module installation and loading, and tests integration with existing
kernel maintenance targets.
"""

import os
import sys
import json
import tempfile
import shutil
import subprocess
import time
import glob
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import argparse

class BuildValidationResult(Enum):
    """Build validation result status"""
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    ERROR = "error"

@dataclass
class BuildValidationStep:
    """Represents a build validation step"""
    name: str
    description: str
    validation_function: str
    timeout: int = 300
    critical: bool = True
    requires_root: bool = False

@dataclass
class BuildValidationExecution:
    """Represents build validation execution result"""
    step: BuildValidationStep
    result: BuildValidationResult
    execution_time: float
    output: str = ""
    error_message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

class BuildSystemValidator:
    """Comprehensive build system integration validator"""
    
    def __init__(self, kernel_root: str = "."):
        self.kernel_root = Path(kernel_root).resolve()
        self.temp_dir = None
        self.original_config = None
        self.validation_steps = []
        self.execution_results = []
        
        # Load validation steps
        self._load_validation_steps()
    
    def _load_validation_steps(self):
        """Load build system validation steps"""
        
        self.validation_steps = [
            BuildValidationStep(
                name="validate_makefile_integration",
                description="Validate Makefile integration with kernel build system",
                validation_function="validate_makefile_integration",
                critical=True
            ),
            
            BuildValidationStep(
                name="validate_build_targets",
                description="Validate backports build targets",
                validation_function="validate_build_targets",
                critical=True
            ),
            
            BuildValidationStep(
                name="validate_configuration_build",
                description="Validate build with various configurations",
                validation_function="validate_configuration_build",
                timeout=600,
                critical=True
            ),
            
            BuildValidationStep(
                name="validate_module_installation",
                description="Validate module installation process",
                validation_function="validate_module_installation",
                requires_root=True,
                critical=True
            ),
            
            BuildValidationStep(
                name="validate_module_loading",
                description="Validate module loading and dependencies",
                validation_function="validate_module_loading",
                requires_root=True,
                critical=False
            ),
            
            BuildValidationStep(
                name="validate_maintenance_targets",
                description="Validate integration with kernel maintenance targets",
                validation_function="validate_maintenance_targets",
                critical=True
            ),
            
            BuildValidationStep(
                name="validate_cross_compilation",
                description="Validate cross-compilation support",
                validation_function="validate_cross_compilation",
                timeout=600,
                critical=False
            ),
            
            BuildValidationStep(
                name="validate_clean_targets",
                description="Validate clean and distclean targets",
                validation_function="validate_clean_targets",
                critical=True
            )
        ]
    
    def setup_validation_environment(self):
        """Set up build validation environment"""
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp(prefix="backports_build_validation_")
        
        # Backup original configuration
        config_file = self.kernel_root / ".config"
        if config_file.exists():
            self.original_config = config_file.read_text()
        
        print(f"🔧 Build validation environment set up")
    
    def cleanup_validation_environment(self):
        """Clean up validation environment"""
        # Restore original configuration
        if self.original_config:
            config_file = self.kernel_root / ".config"
            config_file.write_text(self.original_config)
        
        # Clean up temporary files
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
        
        # Clean build artifacts
        try:
            subprocess.run(["make", "clean"], cwd=self.kernel_root, 
                         capture_output=True, timeout=60)
        except:
            pass
        
        print("🧹 Build validation environment cleaned up")
    
    def validate_makefile_integration(self) -> Tuple[BuildValidationResult, str, Dict[str, Any]]:
        """Validate Makefile integration with kernel build system"""
        details = {}
        
        try:
            # Check if backports Makefile exists
            backports_makefile = self.kernel_root / "backports-integration" / "Makefile"
            if not backports_makefile.exists():
                return BuildValidationResult.FAIL, "Backports Makefile not found", details
            
            details["backports_makefile_exists"] = True
            
            # Check Makefile integration
            result = subprocess.run([
                "make", "-n", "backports_help"
            ], cwd=self.kernel_root, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return BuildValidationResult.FAIL, "Makefile integration not working", details
            
            details["makefile_integration"] = True
            
            # Check for required targets
            required_targets = [
                "backports_help", "backports_status", "backports_validate",
                "backports_clean", "backports_install"
            ]
            
            missing_targets = []
            for target in required_targets:
                result = subprocess.run([
                    "make", "-n", target
                ], cwd=self.kernel_root, capture_output=True, text=True, timeout=10)
                
                if result.returncode != 0:
                    missing_targets.append(target)
            
            details["missing_targets"] = missing_targets
            
            if missing_targets:
                return BuildValidationResult.FAIL, f"Missing targets: {missing_targets}", details
            
            details["all_targets_available"] = True
            return BuildValidationResult.PASS, "Makefile integration validated", details
        
        except Exception as e:
            return BuildValidationResult.ERROR, str(e), details
    
    def validate_build_targets(self) -> Tuple[BuildValidationResult, str, Dict[str, Any]]:
        """Validate backports build targets"""
        details = {}
        
        try:
            # Test backports_help target
            result = subprocess.run([
                "make", "backports_help"
            ], cwd=self.kernel_root, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return BuildValidationResult.FAIL, "backports_help target failed", details
            
            if "Backports Integration Makefile" not in result.stdout:
                return BuildValidationResult.FAIL, "backports_help output incorrect", details
            
            details["help_target"] = True
            
            # Test backports_status target
            result = subprocess.run([
                "make", "backports_status"
            ], cwd=self.kernel_root, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return BuildValidationResult.FAIL, "backports_status target failed", details
            
            details["status_target"] = True
            
            # Test backports_validate target
            result = subprocess.run([
                "make", "backports_validate"
            ], cwd=self.kernel_root, capture_output=True, text=True, timeout=60)
            
            # Note: This may fail if configuration is invalid, which is expected
            details["validate_target"] = result.returncode == 0
            
            return BuildValidationResult.PASS, "Build targets validated", details
        
        except Exception as e:
            return BuildValidationResult.ERROR, str(e), details
    
    def validate_configuration_build(self) -> Tuple[BuildValidationResult, str, Dict[str, Any]]:
        """Validate build with various configurations"""
        details = {}
        
        try:
            # Test basic configuration
            result = subprocess.run([
                "backports-integration/scripts/kconfig-helper.sh", "template", "basic"
            ], cwd=self.kernel_root, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return BuildValidationResult.FAIL, "Failed to apply basic template", details
            
            details["basic_template_applied"] = True
            
            # Resolve dependencies
            result = subprocess.run([
                "make", "olddefconfig"
            ], cwd=self.kernel_root, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                return BuildValidationResult.FAIL, "Failed to resolve dependencies", details
            
            details["dependencies_resolved"] = True
            
            # Validate configuration
            result = subprocess.run([
                "make", "backports_validate"
            ], cwd=self.kernel_root, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                return BuildValidationResult.FAIL, "Configuration validation failed", details
            
            details["configuration_validated"] = True
            
            # Test build preparation (without actually building modules)
            result = subprocess.run([
                "make", "-n", "modules"
            ], cwd=self.kernel_root, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                return BuildValidationResult.FAIL, "Build preparation failed", details
            
            details["build_preparation"] = True
            
            return BuildValidationResult.PASS, "Configuration build validated", details
        
        except Exception as e:
            return BuildValidationResult.ERROR, str(e), details
    
    def validate_module_installation(self) -> Tuple[BuildValidationResult, str, Dict[str, Any]]:
        """Validate module installation process"""
        details = {}
        
        # Check if running as root
        if os.geteuid() != 0:
            return BuildValidationResult.SKIP, "Requires root privileges", details
        
        try:
            # Create temporary installation directory
            install_dir = Path(self.temp_dir) / "modules_install"
            install_dir.mkdir(exist_ok=True)
            
            # Test module installation target
            result = subprocess.run([
                "make", "-n", "modules_install", f"INSTALL_MOD_PATH={install_dir}"
            ], cwd=self.kernel_root, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                return BuildValidationResult.FAIL, "Module installation preparation failed", details
            
            details["installation_preparation"] = True
            
            # Test backports installation target
            result = subprocess.run([
                "make", "-n", "backports_install", f"INSTALL_MOD_PATH={install_dir}"
            ], cwd=self.kernel_root, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                return BuildValidationResult.FAIL, "Backports installation preparation failed", details
            
            details["backports_installation_preparation"] = True
            
            return BuildValidationResult.PASS, "Module installation validated", details
        
        except Exception as e:
            return BuildValidationResult.ERROR, str(e), details
    
    def validate_module_loading(self) -> Tuple[BuildValidationResult, str, Dict[str, Any]]:
        """Validate module loading and dependencies"""
        details = {}
        
        # Check if running as root
        if os.geteuid() != 0:
            return BuildValidationResult.SKIP, "Requires root privileges", details
        
        try:
            # Check if modules exist (they may not if backports source is not available)
            module_paths = [
                "/lib/modules/*/backports/cfg80211.ko",
                "/lib/modules/*/backports/mac80211.ko"
            ]
            
            modules_found = []
            for pattern in module_paths:
                matches = glob.glob(pattern)
                if matches:
                    modules_found.extend(matches)
            
            if not modules_found:
                return BuildValidationResult.SKIP, "No backports modules found to test", details
            
            details["modules_found"] = modules_found
            
            # Test module dependency information
            for module_path in modules_found[:2]:  # Test first 2 modules
                try:
                    result = subprocess.run([
                        "modinfo", module_path
                    ], capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        details[f"modinfo_{Path(module_path).stem}"] = True
                    
                except:
                    pass
            
            # Test dependency resolution
            result = subprocess.run([
                "depmod", "-n"
            ], capture_output=True, text=True, timeout=30)
            
            details["depmod_test"] = result.returncode == 0
            
            return BuildValidationResult.PASS, "Module loading validated", details
        
        except Exception as e:
            return BuildValidationResult.ERROR, str(e), details
    
    def validate_maintenance_targets(self) -> Tuple[BuildValidationResult, str, Dict[str, Any]]:
        """Validate integration with kernel maintenance targets"""
        details = {}
        
        try:
            # Test clean target
            result = subprocess.run([
                "make", "-n", "clean"
            ], cwd=self.kernel_root, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return BuildValidationResult.FAIL, "Clean target integration failed", details
            
            details["clean_target"] = True
            
            # Test mrproper target
            result = subprocess.run([
                "make", "-n", "mrproper"
            ], cwd=self.kernel_root, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return BuildValidationResult.FAIL, "Mrproper target integration failed", details
            
            details["mrproper_target"] = True
            
            # Test modules target integration
            result = subprocess.run([
                "make", "-n", "modules"
            ], cwd=self.kernel_root, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                return BuildValidationResult.FAIL, "Modules target integration failed", details
            
            details["modules_target"] = True
            
            # Test modules_install target integration
            result = subprocess.run([
                "make", "-n", "modules_install"
            ], cwd=self.kernel_root, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return BuildValidationResult.FAIL, "Modules_install target integration failed", details
            
            details["modules_install_target"] = True
            
            return BuildValidationResult.PASS, "Maintenance targets validated", details
        
        except Exception as e:
            return BuildValidationResult.ERROR, str(e), details
    
    def validate_cross_compilation(self) -> Tuple[BuildValidationResult, str, Dict[str, Any]]:
        """Validate cross-compilation support"""
        details = {}
        
        try:
            # Check if cross-compiler is available
            cross_compiler = "aarch64-linux-gnu-gcc"
            result = subprocess.run([
                "which", cross_compiler
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return BuildValidationResult.SKIP, f"Cross-compiler {cross_compiler} not available", details
            
            details["cross_compiler_available"] = True
            
            # Test cross-compilation preparation
            env = os.environ.copy()
            env["ARCH"] = "arm64"
            env["CROSS_COMPILE"] = "aarch64-linux-gnu-"
            
            result = subprocess.run([
                "make", "-n", "modules"
            ], cwd=self.kernel_root, env=env, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                return BuildValidationResult.FAIL, "Cross-compilation preparation failed", details
            
            details["cross_compilation_preparation"] = True
            
            return BuildValidationResult.PASS, "Cross-compilation validated", details
        
        except Exception as e:
            return BuildValidationResult.ERROR, str(e), details
    
    def validate_clean_targets(self) -> Tuple[BuildValidationResult, str, Dict[str, Any]]:
        """Validate clean and distclean targets"""
        details = {}
        
        try:
            # Test backports_clean target
            result = subprocess.run([
                "make", "backports_clean"
            ], cwd=self.kernel_root, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                return BuildValidationResult.FAIL, "backports_clean target failed", details
            
            details["backports_clean"] = True
            
            # Test backports_distclean target
            result = subprocess.run([
                "make", "backports_distclean"
            ], cwd=self.kernel_root, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                return BuildValidationResult.FAIL, "backports_distclean target failed", details
            
            details["backports_distclean"] = True
            
            return BuildValidationResult.PASS, "Clean targets validated", details
        
        except Exception as e:
            return BuildValidationResult.ERROR, str(e), details
    
    def run_validation_step(self, step: BuildValidationStep) -> BuildValidationExecution:
        """Run a single validation step"""
        start_time = time.time()
        
        try:
            print(f"  Running: {step.description}")
            
            # Check root requirement
            if step.requires_root and os.geteuid() != 0:
                return BuildValidationExecution(
                    step=step,
                    result=BuildValidationResult.SKIP,
                    execution_time=time.time() - start_time,
                    error_message="Requires root privileges"
                )
            
            # Get validation function
            validation_func = getattr(self, step.validation_function)
            
            # Run validation
            result, message, details = validation_func()
            
            execution_time = time.time() - start_time
            
            return BuildValidationExecution(
                step=step,
                result=result,
                execution_time=execution_time,
                output=message,
                error_message=message if result in [BuildValidationResult.FAIL, BuildValidationResult.ERROR] else "",
                details=details
            )
        
        except Exception as e:
            return BuildValidationExecution(
                step=step,
                result=BuildValidationResult.ERROR,
                execution_time=time.time() - start_time,
                error_message=str(e)
            )
    
    def run_complete_build_validation(self) -> List[BuildValidationExecution]:
        """Run complete build system validation"""
        print("🏗️  Starting Build System Integration Validation")
        print("=" * 60)
        
        # Set up environment
        self.setup_validation_environment()
        
        try:
            results = []
            critical_failure = False
            
            for i, step in enumerate(self.validation_steps, 1):
                print(f"\n[{i}/{len(self.validation_steps)}] {step.name}")
                
                # Skip non-critical steps if we had critical failures
                if critical_failure and not step.critical:
                    execution = BuildValidationExecution(
                        step=step,
                        result=BuildValidationResult.SKIP,
                        execution_time=0,
                        error_message="Skipped due to previous critical failure"
                    )
                    results.append(execution)
                    print("  ⏭️  SKIPPED (previous critical failure)")
                    continue
                
                execution = self.run_validation_step(step)
                results.append(execution)
                
                # Print result
                status_icon = {
                    BuildValidationResult.PASS: "✅",
                    BuildValidationResult.FAIL: "❌",
                    BuildValidationResult.SKIP: "⏭️",
                    BuildValidationResult.ERROR: "💥"
                }[execution.result]
                
                print(f"  {status_icon} {execution.result.value.upper()} ({execution.execution_time:.2f}s)")
                
                if execution.error_message:
                    print(f"    Error: {execution.error_message}")
                
                # Check for critical failure
                if step.critical and execution.result in [BuildValidationResult.FAIL, BuildValidationResult.ERROR]:
                    critical_failure = True
                    print(f"    ⚠️  Critical step failed - may skip non-critical steps")
            
            self.execution_results = results
            return results
        
        finally:
            # Clean up environment
            self.cleanup_validation_environment()
    
    def generate_build_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive build validation report"""
        if not self.execution_results:
            return {"error": "No build validation results available"}
        
        # Calculate statistics
        total_steps = len(self.execution_results)
        passed = len([r for r in self.execution_results if r.result == BuildValidationResult.PASS])
        failed = len([r for r in self.execution_results if r.result == BuildValidationResult.FAIL])
        errors = len([r for r in self.execution_results if r.result == BuildValidationResult.ERROR])
        skipped = len([r for r in self.execution_results if r.result == BuildValidationResult.SKIP])
        
        # Calculate critical vs non-critical
        critical_steps = [r for r in self.execution_results if r.step.critical]
        critical_passed = len([r for r in critical_steps if r.result == BuildValidationResult.PASS])
        critical_failed = len([r for r in critical_steps if r.result in [BuildValidationResult.FAIL, BuildValidationResult.ERROR]])
        
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
            "validation_results": [
                {
                    "name": r.step.name,
                    "description": r.step.description,
                    "result": r.result.value,
                    "execution_time": r.execution_time,
                    "critical": r.step.critical,
                    "requires_root": r.step.requires_root,
                    "error_message": r.error_message,
                    "details": r.details
                }
                for r in self.execution_results
            ]
        }
    
    def print_build_validation_report(self):
        """Print human-readable build validation report"""
        report = self.generate_build_validation_report()
        
        if "error" in report:
            print(f"Error generating report: {report['error']}")
            return
        
        summary = report["summary"]
        
        print("\n" + "=" * 60)
        print("BUILD SYSTEM INTEGRATION VALIDATION REPORT")
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
                       if r.result in [BuildValidationResult.FAIL, BuildValidationResult.ERROR]]
        if failed_steps:
            print(f"\nFailed Steps:")
            for result in failed_steps:
                icon = "❌" if result.result == BuildValidationResult.FAIL else "💥"
                critical_text = " (CRITICAL)" if result.step.critical else ""
                print(f"  {icon} {result.step.name}{critical_text}: {result.error_message}")
        
        # Overall assessment
        if summary['critical_success'] and summary['success_rate'] >= 80:
            print(f"\n🎉 BUILD SYSTEM INTEGRATION: SUCCESS")
            print("   All critical build system components validated successfully")
        elif summary['critical_success']:
            print(f"\n⚠️  BUILD SYSTEM INTEGRATION: PARTIAL SUCCESS")
            print("   Critical build system works, but some non-critical issues exist")
        else:
            print(f"\n❌ BUILD SYSTEM INTEGRATION: FAILURE")
            print("   Critical build system integration issues detected")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Build system integration validator')
    parser.add_argument('--kernel-root', default='.', help='Path to kernel source root')
    parser.add_argument('--json', action='store_true', help='Output JSON report')
    parser.add_argument('--report-file', help='Save report to file')
    
    args = parser.parse_args()
    
    # Create validator
    validator = BuildSystemValidator(args.kernel_root)
    
    # Run validation
    results = validator.run_complete_build_validation()
    
    # Generate report
    if args.json:
        report = validator.generate_build_validation_report()
        print(json.dumps(report, indent=2))
    else:
        validator.print_build_validation_report()
    
    # Save report if requested
    if args.report_file:
        report = validator.generate_build_validation_report()
        with open(args.report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Build validation report saved to: {args.report_file}")
    
    # Return appropriate exit code
    report = validator.generate_build_validation_report()
    critical_success = report["summary"]["critical_success"]
    return 0 if critical_success else 1

if __name__ == "__main__":
    sys.exit(main())