#!/usr/bin/env python3
"""
Comprehensive Backports Validation Suite

This script runs all validation checks including configuration validation,
error reporting, and consistency checking in a unified interface.
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import our validation modules
sys.path.insert(0, str(Path(__file__).parent))

try:
    from validate_backports_config import BackportsConfigValidator
    from error_reporting_system import ErrorReportingSystem
    from consistency_checker import BackportsConsistencyChecker
    from enhanced_validator import EnhancedBackportsValidator
except ImportError as e:
    # Try alternative import method
    try:
        import importlib.util
        
        # Load modules dynamically
        script_dir = Path(__file__).parent
        
        spec = importlib.util.spec_from_file_location("validate_backports_config", 
                                                     script_dir / "validate-backports-config.py")
        validate_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(validate_module)
        BackportsConfigValidator = validate_module.BackportsConfigValidator
        
        spec = importlib.util.spec_from_file_location("error_reporting_system", 
                                                     script_dir / "error-reporting-system.py")
        error_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(error_module)
        ErrorReportingSystem = error_module.ErrorReportingSystem
        
        spec = importlib.util.spec_from_file_location("consistency_checker", 
                                                     script_dir / "consistency-checker.py")
        consistency_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(consistency_module)
        BackportsConsistencyChecker = consistency_module.BackportsConsistencyChecker
        
        spec = importlib.util.spec_from_file_location("enhanced_validator", 
                                                     script_dir / "enhanced-validator.py")
        enhanced_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(enhanced_module)
        EnhancedBackportsValidator = enhanced_module.EnhancedBackportsValidator
        
    except Exception as e2:
        print(f"Error importing validation modules: {e}")
        print(f"Alternative import also failed: {e2}")
        sys.exit(1)

class ComprehensiveValidator:
    """Comprehensive validation suite for backports configuration"""
    
    def __init__(self, kernel_root: str = "."):
        self.kernel_root = Path(kernel_root).resolve()
        
        # Initialize all validators
        self.config_validator = BackportsConfigValidator(str(self.kernel_root))
        self.error_reporter = ErrorReportingSystem()
        self.consistency_checker = BackportsConsistencyChecker(str(self.kernel_root))
        self.enhanced_validator = EnhancedBackportsValidator(str(self.kernel_root))
        
        self.results = {
            "config_validation": {},
            "consistency_check": {},
            "enhanced_validation": {},
            "overall_status": "unknown"
        }
    
    def run_all_validations(self) -> bool:
        """Run all validation checks"""
        print("🔍 Running comprehensive backports validation...")
        print("=" * 50)
        
        overall_success = True
        
        # 1. Basic configuration validation
        print("\n1️⃣  Configuration Validation")
        print("-" * 30)
        config_success = self.config_validator.validate_all()
        self.results["config_validation"] = self.config_validator.generate_report()
        
        if config_success:
            print("✅ Configuration validation passed")
        else:
            print("❌ Configuration validation failed")
            overall_success = False
        
        # 2. Consistency checking
        print("\n2️⃣  Consistency Checking")
        print("-" * 25)
        consistency_success = self.consistency_checker.run_consistency_checks()
        self.results["consistency_check"] = self.consistency_checker.generate_consistency_report()
        
        if consistency_success:
            print("✅ Consistency checking passed")
        else:
            print("❌ Consistency checking failed")
            overall_success = False
        
        # 3. Enhanced validation with suggestions
        print("\n3️⃣  Enhanced Validation")
        print("-" * 23)
        enhanced_success = self.enhanced_validator.validate_with_suggestions()
        self.results["enhanced_validation"] = self.enhanced_validator.generate_fix_recommendations()
        
        if enhanced_success:
            print("✅ Enhanced validation passed")
        else:
            print("❌ Enhanced validation found issues")
            # Don't fail overall for enhanced validation warnings
        
        # Set overall status
        self.results["overall_status"] = "passed" if overall_success else "failed"
        
        return overall_success
    
    def print_summary_report(self):
        """Print comprehensive summary report"""
        print("\n📊 VALIDATION SUMMARY")
        print("=" * 21)
        
        # Overall status
        status_icon = "✅" if self.results["overall_status"] == "passed" else "❌"
        print(f"Overall Status: {status_icon} {self.results['overall_status'].upper()}")
        print()
        
        # Configuration validation summary
        config_summary = self.results["config_validation"].get("summary", {})
        config_errors = config_summary.get("errors", 0)
        config_warnings = config_summary.get("warnings", 0)
        
        print(f"Configuration Validation:")
        print(f"  Errors: {config_errors}")
        print(f"  Warnings: {config_warnings}")
        print(f"  Status: {'✅ PASS' if config_errors == 0 else '❌ FAIL'}")
        print()
        
        # Consistency check summary
        consistency_summary = self.results["consistency_check"].get("summary", {})
        consistency_critical = consistency_summary.get("critical", 0)
        consistency_errors = consistency_summary.get("errors", 0)
        consistency_warnings = consistency_summary.get("warnings", 0)
        
        print(f"Consistency Checking:")
        print(f"  Critical: {consistency_critical}")
        print(f"  Errors: {consistency_errors}")
        print(f"  Warnings: {consistency_warnings}")
        print(f"  Status: {'✅ PASS' if consistency_critical == 0 and consistency_errors == 0 else '❌ FAIL'}")
        print()
        
        # Enhanced validation summary
        enhanced_summary = self.results["enhanced_validation"]
        critical_fixes = len(enhanced_summary.get("critical_fixes", []))
        recommended_fixes = len(enhanced_summary.get("recommended_fixes", []))
        automated_fixes = len(enhanced_summary.get("automated_fixes", []))
        
        print(f"Enhanced Validation:")
        print(f"  Critical fixes needed: {critical_fixes}")
        print(f"  Recommended fixes: {recommended_fixes}")
        print(f"  Automated fixes available: {automated_fixes}")
        print()
        
        # Recommendations
        if critical_fixes > 0 or consistency_critical > 0 or config_errors > 0:
            print("🚨 IMMEDIATE ACTION REQUIRED:")
            print("  Run with --fix to apply automated fixes")
            print("  Review critical issues manually")
            print()
        elif recommended_fixes > 0 or consistency_errors > 0 or config_warnings > 0:
            print("⚠️  RECOMMENDATIONS:")
            print("  Consider applying suggested fixes")
            print("  Review warnings and recommendations")
            print()
        else:
            print("🎉 CONFIGURATION LOOKS GOOD!")
            print("  No critical issues found")
            print("  Ready for build")
            print()
    
    def print_detailed_issues(self):
        """Print detailed issues from all validators"""
        print("\n📋 DETAILED ISSUES")
        print("=" * 17)
        
        # Configuration validation issues
        config_results = self.results["config_validation"].get("results", [])
        config_errors = [r for r in config_results if r["level"] == "error"]
        
        if config_errors:
            print("\n❌ Configuration Errors:")
            for i, result in enumerate(config_errors, 1):
                print(f"  {i}. {result['message']}")
                if result.get('suggestion'):
                    print(f"     → {result['suggestion']}")
        
        # Consistency check issues
        consistency_issues = self.results["consistency_check"].get("issues", [])
        critical_issues = [i for i in consistency_issues if i["level"] == "critical"]
        error_issues = [i for i in consistency_issues if i["level"] == "error"]
        
        if critical_issues:
            print("\n🚨 Critical Consistency Issues:")
            for i, issue in enumerate(critical_issues, 1):
                print(f"  {i}. {issue['description']}")
                if issue.get('fix_command'):
                    print(f"     Fix: {issue['fix_command']}")
        
        if error_issues:
            print("\n❌ Consistency Errors:")
            for i, issue in enumerate(error_issues, 1):
                print(f"  {i}. {issue['description']}")
                if issue.get('fix_command'):
                    print(f"     Fix: {issue['fix_command']}")
        
        # Enhanced validation critical fixes
        critical_fixes = self.results["enhanced_validation"].get("critical_fixes", [])
        if critical_fixes:
            print("\n🔧 Critical Fixes Available:")
            for i, fix in enumerate(critical_fixes, 1):
                print(f"  {i}. {fix['description']}")
                if fix.get('command'):
                    print(f"     Command: {fix['command']}")
    
    def apply_automated_fixes(self) -> bool:
        """Apply all available automated fixes"""
        print("🔧 Applying automated fixes...")
        
        fixes_applied = 0
        
        # Apply consistency checker fixes
        consistency_applied = self.consistency_checker.apply_auto_fixes()
        fixes_applied += consistency_applied
        
        # Apply enhanced validator fixes
        if self.enhanced_validator.generate_automated_fix_script("temp-fix-script.sh"):
            try:
                result = subprocess.run(["bash", "temp-fix-script.sh"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print("✅ Enhanced validator fixes applied")
                    fixes_applied += 1
                else:
                    print(f"❌ Enhanced validator fixes failed: {result.stderr}")
                
                # Clean up temporary script
                os.unlink("temp-fix-script.sh")
            except Exception as e:
                print(f"❌ Error applying enhanced fixes: {e}")
        
        if fixes_applied > 0:
            print(f"🎉 Applied {fixes_applied} automated fixes")
            
            # Re-run validation to check results
            print("\n🔄 Re-validating after fixes...")
            success = self.run_all_validations()
            return success
        else:
            print("ℹ️  No automated fixes were available")
            return False
    
    def export_comprehensive_report(self, output_file: str):
        """Export comprehensive validation report"""
        report_data = {
            "validation_timestamp": str(Path(self.kernel_root / ".config").stat().st_mtime),
            "kernel_root": str(self.kernel_root),
            "overall_status": self.results["overall_status"],
            "validation_results": self.results,
            "configuration_snapshot": {
                "backports_options": {
                    k: v for k, v in self.config_validator.config.items() 
                    if k.startswith('CONFIG_BACKPORTS')
                }
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"📄 Comprehensive report exported: {output_file}")
    
    def run_pre_build_validation(self) -> bool:
        """Run pre-build validation (critical checks only)"""
        print("🏗️  Pre-build validation...")
        
        # Run consistency pre-build check
        consistency_success = self.consistency_checker.validate_pre_build()
        
        # Check for critical configuration errors
        config_success = self.config_validator.validate_all()
        config_errors = len(self.config_validator.get_results_by_level(
            self.config_validator.ValidationLevel.ERROR))
        
        if not consistency_success or config_errors > 0:
            print("❌ Pre-build validation failed")
            return False
        
        print("✅ Pre-build validation passed")
        return True

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Comprehensive backports validation suite')
    parser.add_argument('--kernel-root', default='.', help='Path to kernel source root')
    parser.add_argument('--pre-build', action='store_true', help='Run pre-build validation only')
    parser.add_argument('--fix', action='store_true', help='Apply automated fixes')
    parser.add_argument('--detailed', action='store_true', help='Show detailed issues')
    parser.add_argument('--export', help='Export comprehensive report to file')
    parser.add_argument('--json', action='store_true', help='Output JSON format')
    parser.add_argument('--quiet', action='store_true', help='Minimal output')
    
    args = parser.parse_args()
    
    # Create comprehensive validator
    validator = ComprehensiveValidator(args.kernel_root)
    
    # Run appropriate validation
    if args.pre_build:
        success = validator.run_pre_build_validation()
    else:
        success = validator.run_all_validations()
        
        if not args.quiet:
            if args.json:
                print(json.dumps(validator.results, indent=2))
            else:
                validator.print_summary_report()
                
                if args.detailed:
                    validator.print_detailed_issues()
        
        # Apply fixes if requested
        if args.fix:
            validator.apply_automated_fixes()
        
        # Export report if requested
        if args.export:
            validator.export_comprehensive_report(args.export)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())