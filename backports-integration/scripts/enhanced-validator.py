#!/usr/bin/env python3
"""
Enhanced Backports Configuration Validator

Integrates the validation framework with the error reporting and suggestions system
to provide comprehensive, user-friendly configuration validation.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import our modules
sys.path.insert(0, str(Path(__file__).parent))
from validate_backports_config import BackportsConfigValidator, ValidationLevel
from error_reporting_system import ErrorReportingSystem

class EnhancedBackportsValidator:
    """Enhanced validator with integrated error reporting and suggestions"""
    
    def __init__(self, kernel_root: str = "."):
        self.validator = BackportsConfigValidator(kernel_root)
        self.error_reporter = ErrorReportingSystem()
        self.enhanced_reports = []
    
    def validate_with_suggestions(self) -> bool:
        """Run validation and generate enhanced reports with suggestions"""
        # Run basic validation
        success = self.validator.validate_all()
        
        # Process validation results and enhance with suggestions
        for result in self.validator.results:
            enhanced_report = self._enhance_validation_result(result)
            if enhanced_report:
                self.enhanced_reports.append(enhanced_report)
        
        return success
    
    def _enhance_validation_result(self, result) -> Optional[Dict[str, Any]]:
        """Enhance validation result with error reporting and suggestions"""
        # Map validation categories to error types
        error_type_map = {
            "dependency": "missing_dependency",
            "conflict": "option_conflict",
            "security": "security_implication",
            "performance": "performance_impact",
            "android": "android_compatibility",
            "config": "invalid_combination"
        }
        
        error_type = error_type_map.get(result.category, "unknown")
        
        # Extract relevant information from the validation result
        kwargs = {}
        if result.option:
            kwargs['option'] = result.option
        
        # Parse additional information from the message
        if "requires" in result.message:
            # Extract dependency information
            parts = result.message.split("requires")
            if len(parts) > 1:
                dependency = parts[1].strip().split()[0]
                kwargs['dependency'] = dependency
                error_type = "missing_dependency"
        
        elif "conflicts with" in result.message:
            # Extract conflict information
            parts = result.message.split("conflicts with")
            if len(parts) > 1:
                conflicting_option = parts[1].strip().split()[0]
                kwargs['conflicting_option'] = conflicting_option
                error_type = "option_conflict"
        
        elif "wireless stack" in result.message.lower():
            error_type = "wireless_stack_conflict"
        
        elif "frame injection" in result.message.lower():
            error_type = "frame_injection_security"
        
        # Generate enhanced error report
        enhanced_report = self.error_reporter.generate_error_report(error_type, **kwargs)
        
        # Add original validation information
        enhanced_report['original_validation'] = {
            'level': result.level.value,
            'category': result.category,
            'message': result.message,
            'suggestion': result.suggestion
        }
        
        return enhanced_report
    
    def print_enhanced_results(self, show_info: bool = True, interactive: bool = False):
        """Print enhanced validation results with suggestions"""
        if not self.enhanced_reports:
            print("✅ No configuration issues found!")
            return
        
        print("🔍 Backports Configuration Analysis")
        print("=" * 40)
        print()
        
        # Group reports by severity
        errors = [r for r in self.enhanced_reports if r['original_validation']['level'] == 'error']
        warnings = [r for r in self.enhanced_reports if r['original_validation']['level'] == 'warning']
        info_reports = [r for r in self.enhanced_reports if r['original_validation']['level'] == 'info']
        
        # Print summary
        print(f"📊 Summary: {len(errors)} errors, {len(warnings)} warnings, {len(info_reports)} info")
        print()
        
        # Print errors with detailed suggestions
        if errors:
            print("🚨 CRITICAL ISSUES (must be fixed):")
            print("-" * 35)
            for i, report in enumerate(errors, 1):
                self._print_detailed_report(report, i, interactive)
        
        # Print warnings with suggestions
        if warnings:
            print("⚠️  WARNINGS (should be reviewed):")
            print("-" * 33)
            for i, report in enumerate(warnings, 1):
                self._print_detailed_report(report, i, interactive)
        
        # Print info if requested
        if show_info and info_reports:
            print("ℹ️  INFORMATION:")
            print("-" * 14)
            for i, report in enumerate(info_reports, 1):
                self._print_summary_report(report, i)
    
    def _print_detailed_report(self, report: Dict[str, Any], index: int, interactive: bool = False):
        """Print detailed report with suggestions"""
        print(f"{index}. {report['message']}")
        print()
        
        # Print top suggestions
        suggestions = report.get('suggestions', [])[:3]  # Show top 3 suggestions
        if suggestions:
            print("   💡 Suggested solutions:")
            for j, suggestion in enumerate(suggestions, 1):
                priority_icon = "🔥" if suggestion["priority"] == 1 else "⚠️" if suggestion["priority"] == 2 else "💭"
                auto_text = " [AUTOMATED]" if suggestion["automated"] else ""
                
                print(f"      {j}. {priority_icon} {suggestion['description']}{auto_text}")
                print(f"         → {suggestion['action']}")
                
                if suggestion.get('command'):
                    print(f"         Command: {suggestion['command']}")
        
        # Interactive mode
        if interactive and suggestions:
            print()
            choice = input("   Apply automated fix? (y/N): ").lower().strip()
            if choice == 'y':
                automated_suggestions = [s for s in suggestions if s['automated']]
                if automated_suggestions:
                    print(f"   ✅ Would apply: {automated_suggestions[0]['command']}")
                else:
                    print("   ❌ No automated fixes available")
        
        print()
    
    def _print_summary_report(self, report: Dict[str, Any], index: int):
        """Print summary report for info items"""
        print(f"{index}. {report['message']}")
        if report.get('suggestions'):
            top_suggestion = report['suggestions'][0]
            print(f"   💡 {top_suggestion['description']}")
        print()
    
    def generate_fix_recommendations(self) -> Dict[str, Any]:
        """Generate comprehensive fix recommendations"""
        recommendations = {
            "critical_fixes": [],
            "recommended_fixes": [],
            "optional_improvements": [],
            "configuration_templates": [],
            "automated_fixes": []
        }
        
        for report in self.enhanced_reports:
            level = report['original_validation']['level']
            suggestions = report.get('suggestions', [])
            
            for suggestion in suggestions:
                fix_info = {
                    "description": suggestion['description'],
                    "action": suggestion['action'],
                    "command": suggestion.get('command'),
                    "automated": suggestion['automated'],
                    "priority": suggestion['priority']
                }
                
                if level == 'error':
                    recommendations["critical_fixes"].append(fix_info)
                elif level == 'warning':
                    recommendations["recommended_fixes"].append(fix_info)
                else:
                    recommendations["optional_improvements"].append(fix_info)
                
                if suggestion['automated']:
                    recommendations["automated_fixes"].append(fix_info)
        
        # Suggest configuration templates
        requirements = self._analyze_requirements()
        template = self.error_reporter.suggest_configuration_template(requirements)
        if template:
            recommendations["configuration_templates"].append({
                "name": template,
                "description": self.error_reporter.fix_templates[template]["description"],
                "requirements": requirements
            })
        
        return recommendations
    
    def _analyze_requirements(self) -> List[str]:
        """Analyze configuration to determine requirements"""
        requirements = []
        
        config = self.validator.config
        
        if config.get('CONFIG_BACKPORTS_MONITOR_MODE') == 'y':
            requirements.append('monitor_mode')
        
        if config.get('CONFIG_BACKPORTS_FRAME_INJECTION') == 'y':
            requirements.append('frame_injection')
        
        if config.get('CONFIG_ANDROID') == 'y':
            requirements.append('android')
        
        if not requirements:
            requirements.append('basic')
        
        return requirements
    
    def generate_automated_fix_script(self, output_file: str = "fix-backports-config.sh"):
        """Generate automated fix script"""
        automated_suggestions = []
        
        for report in self.enhanced_reports:
            if report['original_validation']['level'] == 'error':
                for suggestion in report.get('suggestions', []):
                    if suggestion['automated'] and suggestion.get('command'):
                        automated_suggestions.append(suggestion)
        
        if automated_suggestions:
            self.error_reporter.generate_fix_script(automated_suggestions, output_file)
            print(f"📝 Automated fix script generated: {output_file}")
            return True
        else:
            print("ℹ️  No automated fixes available")
            return False
    
    def export_detailed_report(self, output_file: str):
        """Export detailed validation report"""
        report_data = {
            "summary": {
                "total_issues": len(self.enhanced_reports),
                "errors": len([r for r in self.enhanced_reports if r['original_validation']['level'] == 'error']),
                "warnings": len([r for r in self.enhanced_reports if r['original_validation']['level'] == 'warning']),
                "info": len([r for r in self.enhanced_reports if r['original_validation']['level'] == 'info'])
            },
            "issues": self.enhanced_reports,
            "recommendations": self.generate_fix_recommendations(),
            "configuration": {
                "backports_options": {
                    k: v for k, v in self.validator.config.items() 
                    if k.startswith('CONFIG_BACKPORTS')
                }
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"📄 Detailed report exported: {output_file}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Enhanced backports configuration validator')
    parser.add_argument('--kernel-root', default='.', help='Path to kernel source root')
    parser.add_argument('--no-info', action='store_true', help='Hide info messages')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode with fix prompts')
    parser.add_argument('--generate-fixes', action='store_true', help='Generate automated fix script')
    parser.add_argument('--export-report', help='Export detailed report to file')
    parser.add_argument('--json', action='store_true', help='Output JSON format')
    
    args = parser.parse_args()
    
    # Create enhanced validator
    validator = EnhancedBackportsValidator(args.kernel_root)
    
    # Run validation with suggestions
    success = validator.validate_with_suggestions()
    
    if args.json:
        # Output JSON report
        recommendations = validator.generate_fix_recommendations()
        print(json.dumps(recommendations, indent=2))
    else:
        # Print enhanced results
        validator.print_enhanced_results(
            show_info=not args.no_info,
            interactive=args.interactive
        )
        
        # Generate fixes if requested
        if args.generate_fixes:
            validator.generate_automated_fix_script()
        
        # Export detailed report if requested
        if args.export_report:
            validator.export_detailed_report(args.export_report)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())