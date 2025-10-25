#!/usr/bin/env python3
"""
Backports Error Reporting and Suggestions System

This module provides user-friendly error messages, context-aware help,
and automatic fix suggestions for backports configuration issues.
"""

import os
import sys
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum
import argparse
import textwrap

class ErrorCategory(Enum):
    """Error categories for better organization"""
    DEPENDENCY = "dependency"
    CONFLICT = "conflict"
    SECURITY = "security"
    PERFORMANCE = "performance"
    COMPATIBILITY = "compatibility"
    CONFIGURATION = "configuration"
    BUILD = "build"
    RUNTIME = "runtime"

class SuggestionType(Enum):
    """Types of suggestions"""
    ENABLE_OPTION = "enable_option"
    DISABLE_OPTION = "disable_option"
    CHANGE_VALUE = "change_value"
    ADD_DEPENDENCY = "add_dependency"
    REVIEW_SECURITY = "review_security"
    PERFORMANCE_TUNING = "performance_tuning"
    DOCUMENTATION = "documentation"

@dataclass
class ErrorSuggestion:
    """Represents a specific suggestion for fixing an error"""
    type: SuggestionType
    description: str
    action: str
    options: List[str] = field(default_factory=list)
    priority: int = 1  # 1=high, 2=medium, 3=low
    automated: bool = False  # Can be automatically applied
    command: Optional[str] = None  # Command to execute
    documentation_link: Optional[str] = None

@dataclass
class ContextualHelp:
    """Context-aware help information"""
    title: str
    description: str
    examples: List[str] = field(default_factory=list)
    related_options: List[str] = field(default_factory=list)
    troubleshooting_steps: List[str] = field(default_factory=list)
    common_mistakes: List[str] = field(default_factory=list)

class ErrorReportingSystem:
    """Enhanced error reporting with suggestions and context-aware help"""
    
    def __init__(self):
        self.error_database = self._build_error_database()
        self.help_database = self._build_help_database()
        self.fix_templates = self._build_fix_templates()
        
    def _build_error_database(self) -> Dict[str, Dict[str, Any]]:
        """Build comprehensive error database with solutions"""
        return {
            # Dependency errors
            "missing_dependency": {
                "category": ErrorCategory.DEPENDENCY,
                "template": "{option} requires {dependency} to be enabled",
                "suggestions": [
                    ErrorSuggestion(
                        SuggestionType.ENABLE_OPTION,
                        "Enable the required dependency",
                        "Enable {dependency}",
                        priority=1,
                        automated=True,
                        command="scripts/kconfig-enable.sh {dependency}"
                    ),
                    ErrorSuggestion(
                        SuggestionType.DOCUMENTATION,
                        "Review dependency documentation",
                        "Check documentation for {dependency}",
                        priority=2,
                        documentation_link="Documentation/backports/dependencies.rst"
                    )
                ],
                "context_help": "dependency_resolution"
            },
            
            "circular_dependency": {
                "category": ErrorCategory.DEPENDENCY,
                "template": "Circular dependency detected: {chain}",
                "suggestions": [
                    ErrorSuggestion(
                        SuggestionType.DISABLE_OPTION,
                        "Break the circular dependency by disabling one option",
                        "Disable one of: {options}",
                        priority=1
                    ),
                    ErrorSuggestion(
                        SuggestionType.DOCUMENTATION,
                        "Review dependency architecture",
                        "Check dependency design documentation",
                        priority=2,
                        documentation_link="Documentation/backports/architecture.rst"
                    )
                ]
            },
            
            # Conflict errors
            "option_conflict": {
                "category": ErrorCategory.CONFLICT,
                "template": "{option} conflicts with {conflicting_option}",
                "suggestions": [
                    ErrorSuggestion(
                        SuggestionType.DISABLE_OPTION,
                        "Disable the conflicting option",
                        "Disable {conflicting_option}",
                        priority=1,
                        automated=True,
                        command="scripts/kconfig-disable.sh {conflicting_option}"
                    ),
                    ErrorSuggestion(
                        SuggestionType.DISABLE_OPTION,
                        "Disable this option instead",
                        "Disable {option}",
                        priority=2,
                        automated=True,
                        command="scripts/kconfig-disable.sh {option}"
                    )
                ],
                "context_help": "conflict_resolution"
            },
            
            "wireless_stack_conflict": {
                "category": ErrorCategory.CONFLICT,
                "template": "Cannot enable both backports wireless stack and kernel wireless stack",
                "suggestions": [
                    ErrorSuggestion(
                        SuggestionType.DISABLE_OPTION,
                        "Disable kernel wireless stack (recommended)",
                        "Disable CONFIG_CFG80211 and CONFIG_MAC80211",
                        options=["CONFIG_CFG80211", "CONFIG_MAC80211"],
                        priority=1,
                        automated=True,
                        command="scripts/disable-kernel-wireless.sh"
                    ),
                    ErrorSuggestion(
                        SuggestionType.DISABLE_OPTION,
                        "Disable backports wireless stack",
                        "Disable CONFIG_BACKPORTS",
                        options=["CONFIG_BACKPORTS"],
                        priority=2,
                        automated=True,
                        command="scripts/kconfig-disable.sh CONFIG_BACKPORTS"
                    )
                ],
                "context_help": "wireless_stack_selection"
            },
            
            # Security errors
            "security_implication": {
                "category": ErrorCategory.SECURITY,
                "template": "{option} has security implications: {description}",
                "suggestions": [
                    ErrorSuggestion(
                        SuggestionType.REVIEW_SECURITY,
                        "Review security policies and access controls",
                        "Implement appropriate security measures",
                        priority=1,
                        documentation_link="Documentation/backports/security.rst"
                    ),
                    ErrorSuggestion(
                        SuggestionType.ENABLE_OPTION,
                        "Enable security logging and auditing",
                        "Enable CONFIG_AUDIT and related options",
                        options=["CONFIG_AUDIT", "CONFIG_AUDITSYSCALL"],
                        priority=2,
                        automated=True
                    )
                ],
                "context_help": "security_considerations"
            },
            
            "frame_injection_security": {
                "category": ErrorCategory.SECURITY,
                "template": "Frame injection capability enabled - high security risk",
                "suggestions": [
                    ErrorSuggestion(
                        SuggestionType.REVIEW_SECURITY,
                        "Implement strict access controls",
                        "Restrict access to injection interfaces",
                        priority=1
                    ),
                    ErrorSuggestion(
                        SuggestionType.ENABLE_OPTION,
                        "Enable network namespace isolation",
                        "Enable CONFIG_NET_NS for isolation",
                        options=["CONFIG_NET_NS"],
                        priority=1,
                        automated=True
                    ),
                    ErrorSuggestion(
                        SuggestionType.PERFORMANCE_TUNING,
                        "Consider disabling in production",
                        "Disable frame injection for production builds",
                        priority=2
                    )
                ],
                "context_help": "frame_injection_security"
            },
            
            # Performance errors
            "performance_impact": {
                "category": ErrorCategory.PERFORMANCE,
                "template": "{option} may impact system performance: {impact}",
                "suggestions": [
                    ErrorSuggestion(
                        SuggestionType.PERFORMANCE_TUNING,
                        "Consider disabling in production environments",
                        "Disable {option} for production builds",
                        priority=2
                    ),
                    ErrorSuggestion(
                        SuggestionType.DOCUMENTATION,
                        "Review performance optimization guide",
                        "Check performance tuning documentation",
                        priority=3,
                        documentation_link="Documentation/backports/performance.rst"
                    )
                ]
            },
            
            # Configuration errors
            "invalid_combination": {
                "category": ErrorCategory.CONFIGURATION,
                "template": "Invalid configuration combination: {options}",
                "suggestions": [
                    ErrorSuggestion(
                        SuggestionType.CHANGE_VALUE,
                        "Use a supported configuration template",
                        "Apply configuration template: {template}",
                        priority=1,
                        automated=True,
                        command="scripts/apply-config-template.sh {template}"
                    ),
                    ErrorSuggestion(
                        SuggestionType.DOCUMENTATION,
                        "Review configuration examples",
                        "Check configuration guide",
                        priority=2,
                        documentation_link="Documentation/backports/configuration.rst"
                    )
                ]
            },
            
            # Android-specific errors
            "android_compatibility": {
                "category": ErrorCategory.COMPATIBILITY,
                "template": "Android compatibility issue: {issue}",
                "suggestions": [
                    ErrorSuggestion(
                        SuggestionType.ENABLE_OPTION,
                        "Enable Android-specific backports options",
                        "Enable CONFIG_BACKPORTS_ANDROID",
                        options=["CONFIG_BACKPORTS_ANDROID"],
                        priority=1,
                        automated=True
                    ),
                    ErrorSuggestion(
                        SuggestionType.DISABLE_OPTION,
                        "Disable conflicting vendor drivers",
                        "Disable vendor wireless drivers",
                        priority=1
                    )
                ],
                "context_help": "android_integration"
            }
        }
    
    def _build_help_database(self) -> Dict[str, ContextualHelp]:
        """Build context-aware help database"""
        return {
            "dependency_resolution": ContextualHelp(
                title="Resolving Dependency Issues",
                description="Dependencies ensure that required kernel features are available when backports components are enabled.",
                examples=[
                    "CONFIG_BACKPORTS_MAC80211 requires CONFIG_BACKPORTS_CFG80211",
                    "CONFIG_BACKPORTS_MONITOR_MODE requires CONFIG_PACKET",
                    "CONFIG_BACKPORTS_FRAME_INJECTION requires CONFIG_PACKET_MMAP"
                ],
                related_options=[
                    "CONFIG_BACKPORTS", "CONFIG_BACKPORTS_CFG80211", "CONFIG_BACKPORTS_MAC80211"
                ],
                troubleshooting_steps=[
                    "Check if the dependency is available in your kernel version",
                    "Enable the dependency using 'make menuconfig'",
                    "Verify that the dependency doesn't conflict with other options",
                    "Check kernel documentation for the dependency"
                ],
                common_mistakes=[
                    "Forgetting to enable CONFIG_MODULES for modular builds",
                    "Missing CONFIG_NET for networking features",
                    "Not enabling CONFIG_CRYPTO for security features"
                ]
            ),
            
            "conflict_resolution": ContextualHelp(
                title="Resolving Configuration Conflicts",
                description="Conflicts occur when two options cannot be enabled simultaneously due to incompatible implementations.",
                examples=[
                    "CONFIG_BACKPORTS conflicts with CONFIG_CFG80211 (kernel version)",
                    "CONFIG_BACKPORTS_ANDROID conflicts with CONFIG_QCACLD",
                    "Multiple rate control algorithms cannot be enabled together"
                ],
                troubleshooting_steps=[
                    "Identify which option provides the functionality you need",
                    "Disable the conflicting option you don't need",
                    "Check if there's a compatibility layer available",
                    "Review the conflict reason in documentation"
                ],
                common_mistakes=[
                    "Enabling both backports and kernel wireless stacks",
                    "Enabling conflicting vendor drivers",
                    "Not understanding the purpose of conflicting options"
                ]
            ),
            
            "wireless_stack_selection": ContextualHelp(
                title="Choosing Between Wireless Stacks",
                description="You must choose between the kernel's built-in wireless stack and the backports wireless stack.",
                examples=[
                    "Use backports for newer wireless features on older kernels",
                    "Use kernel stack for stable, well-tested functionality",
                    "Use backports for monitor mode and frame injection"
                ],
                troubleshooting_steps=[
                    "Determine which features you need",
                    "Check kernel version compatibility",
                    "Disable the stack you don't want to use",
                    "Verify that all required features are available"
                ],
                common_mistakes=[
                    "Trying to enable both stacks simultaneously",
                    "Not understanding feature differences between stacks",
                    "Forgetting to disable vendor drivers when using backports"
                ]
            ),
            
            "security_considerations": ContextualHelp(
                title="Security Considerations for Backports",
                description="Some backports features have security implications that require careful consideration.",
                examples=[
                    "Monitor mode allows packet capture and analysis",
                    "Frame injection can be used for security testing and attacks",
                    "Debug features may expose sensitive information"
                ],
                troubleshooting_steps=[
                    "Review your security requirements and policies",
                    "Implement appropriate access controls",
                    "Enable audit logging for security-sensitive features",
                    "Consider network isolation for testing environments"
                ],
                common_mistakes=[
                    "Enabling security-sensitive features in production without controls",
                    "Not understanding the implications of monitor mode",
                    "Forgetting to restrict access to injection interfaces"
                ]
            ),
            
            "frame_injection_security": ContextualHelp(
                title="Frame Injection Security",
                description="Frame injection allows transmission of custom 802.11 frames, which has significant security implications.",
                examples=[
                    "Used for wireless security testing and penetration testing",
                    "Can be used to perform deauthentication attacks",
                    "Enables custom protocol implementation and testing"
                ],
                troubleshooting_steps=[
                    "Ensure proper user permissions and access controls",
                    "Use network namespaces for isolation",
                    "Enable comprehensive audit logging",
                    "Review local security policies and compliance requirements"
                ],
                common_mistakes=[
                    "Enabling frame injection without understanding security risks",
                    "Not implementing proper access controls",
                    "Using frame injection in production environments"
                ]
            ),
            
            "android_integration": ContextualHelp(
                title="Android Kernel Integration",
                description="Integrating backports with Android kernels requires special considerations for vendor drivers and security.",
                examples=[
                    "Disable Qualcomm QCACLD drivers when using backports",
                    "Enable CONFIG_BACKPORTS_ANDROID for Android-specific features",
                    "Consider Android security model implications"
                ],
                troubleshooting_steps=[
                    "Check for conflicting vendor drivers",
                    "Enable Android-specific backports options",
                    "Verify compatibility with Android security policies",
                    "Test with Android's networking stack"
                ],
                common_mistakes=[
                    "Not disabling conflicting vendor drivers",
                    "Forgetting Android-specific configuration options",
                    "Not considering Android security model"
                ]
            )
        }
    
    def _build_fix_templates(self) -> Dict[str, Dict[str, Any]]:
        """Build automated fix templates"""
        return {
            "enable_backports_basic": {
                "description": "Enable basic backports configuration",
                "options": {
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_CFG80211": "m",
                    "CONFIG_BACKPORTS_MAC80211": "m"
                },
                "disable_options": ["CONFIG_CFG80211", "CONFIG_MAC80211"]
            },
            
            "enable_monitor_mode": {
                "description": "Enable monitor mode support",
                "options": {
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_CFG80211": "m",
                    "CONFIG_BACKPORTS_MAC80211": "m",
                    "CONFIG_BACKPORTS_MONITOR_MODE": "y",
                    "CONFIG_PACKET": "y"
                },
                "disable_options": ["CONFIG_CFG80211", "CONFIG_MAC80211"]
            },
            
            "enable_frame_injection": {
                "description": "Enable frame injection (security testing)",
                "options": {
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_CFG80211": "m",
                    "CONFIG_BACKPORTS_MAC80211": "m",
                    "CONFIG_BACKPORTS_MONITOR_MODE": "y",
                    "CONFIG_BACKPORTS_FRAME_INJECTION": "y",
                    "CONFIG_PACKET": "y",
                    "CONFIG_PACKET_MMAP": "y"
                },
                "disable_options": ["CONFIG_CFG80211", "CONFIG_MAC80211"],
                "security_warning": True
            },
            
            "android_compatible": {
                "description": "Android-compatible backports configuration",
                "options": {
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_CFG80211": "m",
                    "CONFIG_BACKPORTS_MAC80211": "m",
                    "CONFIG_BACKPORTS_ANDROID": "y"
                },
                "disable_options": [
                    "CONFIG_CFG80211", "CONFIG_MAC80211", 
                    "CONFIG_QCACLD", "CONFIG_PRIMA_WLAN"
                ]
            }
        }
    
    def generate_error_report(self, error_type: str, **kwargs) -> Dict[str, Any]:
        """Generate comprehensive error report with suggestions"""
        if error_type not in self.error_database:
            return self._generate_generic_error_report(error_type, **kwargs)
        
        error_info = self.error_database[error_type]
        
        # Format error message
        message = error_info["template"].format(**kwargs)
        
        # Get suggestions
        suggestions = []
        for suggestion_template in error_info["suggestions"]:
            suggestion = ErrorSuggestion(
                type=suggestion_template.type,
                description=suggestion_template.description.format(**kwargs),
                action=suggestion_template.action.format(**kwargs),
                options=[opt.format(**kwargs) for opt in suggestion_template.options],
                priority=suggestion_template.priority,
                automated=suggestion_template.automated,
                command=suggestion_template.command.format(**kwargs) if suggestion_template.command else None,
                documentation_link=suggestion_template.documentation_link
            )
            suggestions.append(suggestion)
        
        # Get contextual help
        context_help = None
        if "context_help" in error_info:
            help_key = error_info["context_help"]
            if help_key in self.help_database:
                context_help = self.help_database[help_key]
        
        return {
            "error_type": error_type,
            "category": error_info["category"].value,
            "message": message,
            "suggestions": [
                {
                    "type": s.type.value,
                    "description": s.description,
                    "action": s.action,
                    "options": s.options,
                    "priority": s.priority,
                    "automated": s.automated,
                    "command": s.command,
                    "documentation_link": s.documentation_link
                }
                for s in sorted(suggestions, key=lambda x: x.priority)
            ],
            "context_help": {
                "title": context_help.title,
                "description": context_help.description,
                "examples": context_help.examples,
                "related_options": context_help.related_options,
                "troubleshooting_steps": context_help.troubleshooting_steps,
                "common_mistakes": context_help.common_mistakes
            } if context_help else None
        }
    
    def _generate_generic_error_report(self, error_type: str, **kwargs) -> Dict[str, Any]:
        """Generate generic error report for unknown error types"""
        return {
            "error_type": error_type,
            "category": "unknown",
            "message": f"Unknown error type: {error_type}",
            "suggestions": [
                {
                    "type": "documentation",
                    "description": "Check documentation for similar issues",
                    "action": "Review backports documentation",
                    "priority": 1,
                    "automated": False,
                    "documentation_link": "Documentation/backports/"
                }
            ],
            "context_help": None
        }
    
    def format_user_friendly_message(self, report: Dict[str, Any]) -> str:
        """Format error report as user-friendly message"""
        lines = []
        
        # Error header
        category = report["category"].upper()
        lines.append(f"🚨 {category} ERROR")
        lines.append("=" * (len(category) + 8))
        lines.append("")
        
        # Error message
        lines.append(f"Problem: {report['message']}")
        lines.append("")
        
        # Suggestions
        if report["suggestions"]:
            lines.append("💡 SUGGESTED SOLUTIONS:")
            lines.append("-" * 22)
            
            for i, suggestion in enumerate(report["suggestions"], 1):
                priority_icon = "🔥" if suggestion["priority"] == 1 else "⚠️" if suggestion["priority"] == 2 else "💭"
                auto_icon = " (automated)" if suggestion["automated"] else ""
                
                lines.append(f"{i}. {priority_icon} {suggestion['description']}{auto_icon}")
                lines.append(f"   Action: {suggestion['action']}")
                
                if suggestion["command"]:
                    lines.append(f"   Command: {suggestion['command']}")
                
                if suggestion["documentation_link"]:
                    lines.append(f"   Documentation: {suggestion['documentation_link']}")
                
                lines.append("")
        
        # Context help
        if report["context_help"]:
            help_info = report["context_help"]
            lines.append("📚 ADDITIONAL HELP:")
            lines.append("-" * 18)
            lines.append(f"Topic: {help_info['title']}")
            lines.append("")
            lines.append(textwrap.fill(help_info["description"], width=70))
            lines.append("")
            
            if help_info["examples"]:
                lines.append("Examples:")
                for example in help_info["examples"]:
                    lines.append(f"  • {example}")
                lines.append("")
            
            if help_info["troubleshooting_steps"]:
                lines.append("Troubleshooting steps:")
                for step in help_info["troubleshooting_steps"]:
                    lines.append(f"  1. {step}")
                lines.append("")
        
        return "\n".join(lines)
    
    def generate_fix_script(self, suggestions: List[Dict[str, Any]], output_file: str):
        """Generate automated fix script"""
        script_lines = [
            "#!/bin/bash",
            "# Automated backports configuration fix script",
            "# Generated by backports error reporting system",
            "",
            "set -e",
            "",
            "KERNEL_ROOT=${1:-.}",
            "CONFIG_FILE=\"$KERNEL_ROOT/.config\"",
            "",
            "echo 'Applying backports configuration fixes...'",
            ""
        ]
        
        for suggestion in suggestions:
            if suggestion["automated"] and suggestion["command"]:
                script_lines.append(f"# {suggestion['description']}")
                script_lines.append(f"echo 'Applying: {suggestion['description']}'")
                script_lines.append(suggestion["command"])
                script_lines.append("")
        
        script_lines.extend([
            "echo 'Configuration fixes applied successfully!'",
            "echo 'Please review the changes and rebuild your kernel.'",
            ""
        ])
        
        with open(output_file, 'w') as f:
            f.write("\n".join(script_lines))
        
        os.chmod(output_file, 0o755)
    
    def suggest_configuration_template(self, requirements: List[str]) -> Optional[str]:
        """Suggest appropriate configuration template based on requirements"""
        requirement_map = {
            "monitor_mode": "enable_monitor_mode",
            "frame_injection": "enable_frame_injection",
            "android": "android_compatible",
            "basic": "enable_backports_basic"
        }
        
        for req in requirements:
            if req in requirement_map:
                return requirement_map[req]
        
        return "enable_backports_basic"

def main():
    """Main function for testing the error reporting system"""
    parser = argparse.ArgumentParser(description='Test backports error reporting system')
    parser.add_argument('--error-type', required=True, help='Error type to test')
    parser.add_argument('--option', help='Configuration option')
    parser.add_argument('--dependency', help='Missing dependency')
    parser.add_argument('--conflicting-option', help='Conflicting option')
    parser.add_argument('--json', action='store_true', help='Output JSON format')
    
    args = parser.parse_args()
    
    reporting_system = ErrorReportingSystem()
    
    # Build kwargs from arguments
    kwargs = {}
    if args.option:
        kwargs['option'] = args.option
    if args.dependency:
        kwargs['dependency'] = args.dependency
    if args.conflicting_option:
        kwargs['conflicting_option'] = args.conflicting_option
    
    # Generate error report
    report = reporting_system.generate_error_report(args.error_type, **kwargs)
    
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        message = reporting_system.format_user_friendly_message(report)
        print(message)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())