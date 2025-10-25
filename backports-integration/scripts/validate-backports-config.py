#!/usr/bin/env python3
"""
Backports Configuration Validation Framework

This script provides comprehensive validation of backports configuration,
including checks for invalid option combinations, missing dependencies,
and security-sensitive features with appropriate warnings.
"""

import os
import sys
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass
from enum import Enum
import argparse

class ValidationLevel(Enum):
    """Validation severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ValidationResult:
    """Represents a validation result"""
    level: ValidationLevel
    category: str
    message: str
    option: Optional[str] = None
    suggestion: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class BackportsConfigValidator:
    """Comprehensive backports configuration validator"""
    
    def __init__(self, kernel_root: str = "."):
        self.kernel_root = Path(kernel_root).resolve()
        self.config_file = self.kernel_root / ".config"
        self.backports_dir = self.kernel_root / "backports-generated-6.1"
        
        self.results: List[ValidationResult] = []
        self.config: Dict[str, str] = {}
        
        # Validation rules database
        self.validation_rules = {
            # Core backports validation
            'CONFIG_BACKPORTS': {
                'type': 'bool',
                'description': 'Enable Linux Kernel Backports',
                'conflicts': ['CONFIG_CFG80211', 'CONFIG_MAC80211'],
                'requires_kernel_features': ['CONFIG_MODULES', 'CONFIG_NET'],
                'min_kernel_version': (4, 19, 0),
                'supported_architectures': ['arm64', 'x86_64', 'arm', 'x86']
            },
            
            # cfg80211 validation
            'CONFIG_BACKPORTS_CFG80211': {
                'type': 'tristate',
                'description': 'cfg80211 wireless configuration API',
                'depends': ['CONFIG_BACKPORTS'],
                'conflicts': ['CONFIG_CFG80211'],
                'requires_kernel_features': ['CONFIG_RFKILL', 'CONFIG_CRYPTO'],
                'recommends_kernel_features': ['CONFIG_WIRELESS_EXT'],
                'validation_checks': ['check_cfg80211_dependencies']
            },
            
            # mac80211 validation
            'CONFIG_BACKPORTS_MAC80211': {
                'type': 'tristate',
                'description': 'Generic IEEE 802.11 Networking Stack',
                'depends': ['CONFIG_BACKPORTS_CFG80211'],
                'conflicts': ['CONFIG_MAC80211'],
                'requires_kernel_features': [
                    'CONFIG_CRYPTO_ARC4', 'CONFIG_CRYPTO_AES', 'CONFIG_CRC32'
                ],
                'recommends_kernel_features': ['CONFIG_LEDS_CLASS', 'CONFIG_DEBUG_FS'],
                'validation_checks': ['check_mac80211_dependencies']
            },
            
            # Monitor mode validation
            'CONFIG_BACKPORTS_MONITOR_MODE': {
                'type': 'bool',
                'description': 'Enable monitor mode support',
                'depends': ['CONFIG_BACKPORTS_MAC80211'],
                'requires_kernel_features': ['CONFIG_PACKET'],
                'recommends_kernel_features': ['CONFIG_DEBUG_FS', 'CONFIG_NETFILTER'],
                'security_implications': True,
                'validation_checks': ['check_monitor_mode_security']
            },
            
            # Monitor mode radiotap support
            'CONFIG_BACKPORTS_MONITOR_RADIOTAP': {
                'type': 'bool',
                'description': 'Enable radiotap header support in monitor mode',
                'depends': ['CONFIG_BACKPORTS_MONITOR_MODE'],
                'validation_checks': ['check_radiotap_support']
            },
            
            # Monitor mode channel switching
            'CONFIG_BACKPORTS_MONITOR_CHANNEL_SWITCH': {
                'type': 'bool',
                'description': 'Enable monitor mode channel switching',
                'depends': ['CONFIG_BACKPORTS_MONITOR_MODE'],
                'requires_kernel_features': ['CONFIG_NL80211_TESTMODE'],
                'validation_checks': ['check_channel_switch_support']
            },
            
            # Frame injection validation
            'CONFIG_BACKPORTS_FRAME_INJECTION': {
                'type': 'bool',
                'description': 'Enable frame injection support',
                'depends': ['CONFIG_BACKPORTS_MONITOR_MODE'],
                'requires_kernel_features': ['CONFIG_PACKET_MMAP'],
                'security_implications': True,
                'security_level': 'high',
                'validation_checks': ['check_frame_injection_security']
            },
            
            # Frame injection rate control
            'CONFIG_BACKPORTS_INJECTION_RATE_CONTROL': {
                'type': 'bool',
                'description': 'Enable rate control for injected frames',
                'depends': ['CONFIG_BACKPORTS_FRAME_INJECTION'],
                'validation_checks': ['check_injection_rate_control']
            },
            
            # Frame injection security audit
            'CONFIG_BACKPORTS_INJECTION_SECURITY_AUDIT': {
                'type': 'bool',
                'description': 'Enable security auditing for frame injection',
                'depends': ['CONFIG_BACKPORTS_FRAME_INJECTION'],
                'requires_kernel_features': ['CONFIG_AUDIT'],
                'security_implications': True,
                'validation_checks': ['check_injection_audit']
            },
            
            # Android-specific validation
            'CONFIG_BACKPORTS_ANDROID': {
                'type': 'bool',
                'description': 'Android-specific adaptations',
                'depends': ['CONFIG_BACKPORTS'],
                'requires_kernel_features': ['CONFIG_ANDROID'],
                'conflicts': ['CONFIG_QCACLD', 'CONFIG_PRIMA_WLAN'],
                'validation_checks': ['check_android_compatibility']
            },
            
            # Android wakelock integration
            'CONFIG_BACKPORTS_ANDROID_WAKELOCK': {
                'type': 'bool',
                'description': 'Android wakelock integration',
                'depends': ['CONFIG_BACKPORTS_ANDROID'],
                'requires_kernel_features': ['CONFIG_ANDROID_WAKELOCK'],
                'validation_checks': ['check_android_wakelock']
            },
            
            # Android paranoid networking
            'CONFIG_BACKPORTS_ANDROID_PARANOID_NETWORK': {
                'type': 'bool',
                'description': 'Android paranoid networking integration',
                'depends': ['CONFIG_BACKPORTS_ANDROID'],
                'requires_kernel_features': ['CONFIG_ANDROID_PARANOID_NETWORK'],
                'validation_checks': ['check_android_paranoid_network']
            },
            
            # Vendor driver compatibility
            'CONFIG_BACKPORTS_VENDOR_COMPAT': {
                'type': 'bool',
                'description': 'Vendor driver compatibility layer',
                'depends': ['CONFIG_BACKPORTS'],
                'validation_checks': ['check_vendor_compatibility']
            },
            
            # Qualcomm vendor compatibility
            'CONFIG_BACKPORTS_VENDOR_QCOM': {
                'type': 'bool',
                'description': 'Qualcomm vendor driver compatibility',
                'depends': ['CONFIG_BACKPORTS_VENDOR_COMPAT'],
                'conflicts': ['CONFIG_QCACLD', 'CONFIG_PRIMA_WLAN', 'CONFIG_WCNSS_CORE'],
                'validation_checks': ['check_qcom_vendor_compatibility']
            },
            
            # Android security integration
            'CONFIG_BACKPORTS_SECURITY_ANDROID': {
                'type': 'bool',
                'description': 'Android security model integration',
                'depends': ['CONFIG_BACKPORTS_ANDROID'],
                'validation_checks': ['check_android_security']
            },
            
            # Android SELinux integration
            'CONFIG_BACKPORTS_SELINUX_ANDROID': {
                'type': 'bool',
                'description': 'Android SELinux policy integration',
                'depends': ['CONFIG_BACKPORTS_SECURITY_ANDROID'],
                'requires_kernel_features': ['CONFIG_SECURITY_SELINUX'],
                'validation_checks': ['check_android_selinux']
            },
            
            # Debug validation
            'CONFIG_BACKPORTS_DEBUG': {
                'type': 'bool',
                'description': 'Enable backports debugging',
                'depends': ['CONFIG_BACKPORTS'],
                'performance_impact': True,
                'validation_checks': ['check_debug_implications']
            },
            
            # Verbose debug validation
            'CONFIG_BACKPORTS_DEBUG_VERBOSE': {
                'type': 'bool',
                'description': 'Enable verbose debugging output',
                'depends': ['CONFIG_BACKPORTS_DEBUG'],
                'performance_impact': True,
                'validation_checks': ['check_verbose_debug_implications']
            },
            
            # Tracing support validation
            'CONFIG_BACKPORTS_TRACING': {
                'type': 'bool',
                'description': 'Enable backports tracing support',
                'depends': ['CONFIG_BACKPORTS'],
                'requires_kernel_features': ['CONFIG_TRACING'],
                'validation_checks': ['check_tracing_support']
            },
            
            # Diagnostics validation
            'CONFIG_BACKPORTS_DIAGNOSTICS': {
                'type': 'bool',
                'description': 'Enable backports diagnostic interfaces',
                'depends': ['CONFIG_BACKPORTS'],
                'requires_kernel_features': ['CONFIG_DEBUG_FS'],
                'validation_checks': ['check_diagnostics_support']
            }
        }
        
        # Security validation rules
        self.security_rules = {
            'frame_injection': {
                'options': ['CONFIG_BACKPORTS_FRAME_INJECTION'],
                'level': 'high',
                'description': 'Frame injection can be used for security testing and attacks',
                'recommendations': [
                    'Ensure proper access controls are in place',
                    'Consider network isolation for testing',
                    'Review local security policies',
                    'Enable audit logging if available'
                ]
            },
            'monitor_mode': {
                'options': ['CONFIG_BACKPORTS_MONITOR_MODE'],
                'level': 'medium',
                'description': 'Monitor mode allows packet capture and analysis',
                'recommendations': [
                    'Restrict access to monitor interfaces',
                    'Consider privacy implications',
                    'Enable appropriate logging'
                ]
            },
            'debug_features': {
                'options': ['CONFIG_BACKPORTS_DEBUG', 'CONFIG_BACKPORTS_MAC80211_DEBUGFS'],
                'level': 'low',
                'description': 'Debug features may expose internal information',
                'recommendations': [
                    'Disable in production environments',
                    'Restrict debugfs access permissions'
                ]
            }
        }
        
        # Performance impact rules
        self.performance_rules = {
            'debug_overhead': {
                'options': ['CONFIG_BACKPORTS_DEBUG', 'CONFIG_BACKPORTS_DEBUG_VERBOSE'],
                'impact': 'medium',
                'description': 'Debug options increase CPU and memory usage'
            },
            'crypto_overhead': {
                'options': ['CONFIG_BACKPORTS_MAC80211'],
                'requires': ['CONFIG_CRYPTO_ARC4', 'CONFIG_CRYPTO_AES'],
                'impact': 'low',
                'description': 'Cryptographic operations have CPU overhead'
            }
        }
    
    def add_result(self, level: ValidationLevel, category: str, message: str, 
                   option: Optional[str] = None, suggestion: Optional[str] = None,
                   details: Optional[Dict[str, Any]] = None):
        """Add a validation result"""
        result = ValidationResult(level, category, message, option, suggestion, details)
        self.results.append(result)
    
    def read_config(self) -> bool:
        """Read kernel configuration"""
        if not self.config_file.exists():
            self.add_result(ValidationLevel.WARNING, "config", 
                          f"Configuration file not found: {self.config_file}")
            return False
        
        try:
            with open(self.config_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line.startswith('#') or not line or '=' not in line:
                        continue
                    
                    try:
                        key, value = line.split('=', 1)
                        self.config[key] = value
                    except ValueError:
                        self.add_result(ValidationLevel.WARNING, "config",
                                      f"Invalid config line {line_num}: {line}")
            
            return True
        
        except Exception as e:
            self.add_result(ValidationLevel.ERROR, "config", 
                          f"Failed to read configuration: {e}")
            return False
    
    def get_config_value(self, option: str) -> Optional[str]:
        """Get configuration value"""
        return self.config.get(option)
    
    def is_enabled(self, option: str) -> bool:
        """Check if option is enabled (y or m)"""
        value = self.get_config_value(option)
        return value in ['y', 'm']
    
    def validate_option_type(self, option: str, rules: Dict[str, Any]) -> bool:
        """Validate option type (bool, tristate, etc.)"""
        if option not in self.config:
            return True  # Not set, which is valid
        
        value = self.config[option]
        option_type = rules.get('type', 'bool')
        
        if option_type == 'bool':
            if value not in ['y', 'n']:
                self.add_result(ValidationLevel.ERROR, "type",
                              f"{option} must be 'y' or 'n', got '{value}'",
                              option, "Set to 'y' or 'n'")
                return False
        elif option_type == 'tristate':
            if value not in ['y', 'm', 'n']:
                self.add_result(ValidationLevel.ERROR, "type",
                              f"{option} must be 'y', 'm', or 'n', got '{value}'",
                              option, "Set to 'y', 'm', or 'n'")
                return False
        
        return True
    
    def validate_dependencies(self, option: str, rules: Dict[str, Any]) -> bool:
        """Validate option dependencies"""
        if not self.is_enabled(option):
            return True  # Option not enabled, no need to check dependencies
        
        success = True
        
        # Check direct dependencies
        if 'depends' in rules:
            for dep in rules['depends']:
                if not self.is_enabled(dep):
                    self.add_result(ValidationLevel.ERROR, "dependency",
                                  f"{option} requires {dep} to be enabled",
                                  option, f"Enable {dep}")
                    success = False
        
        # Check kernel feature requirements
        if 'requires_kernel_features' in rules:
            for feature in rules['requires_kernel_features']:
                if not self.is_enabled(feature):
                    self.add_result(ValidationLevel.ERROR, "kernel_feature",
                                  f"{option} requires kernel feature {feature}",
                                  option, f"Enable {feature}")
                    success = False
        
        # Check recommended kernel features
        if 'recommends_kernel_features' in rules:
            for feature in rules['recommends_kernel_features']:
                if not self.is_enabled(feature):
                    self.add_result(ValidationLevel.WARNING, "recommendation",
                                  f"{option} recommends kernel feature {feature}",
                                  option, f"Consider enabling {feature}")
        
        return success
    
    def validate_conflicts(self, option: str, rules: Dict[str, Any]) -> bool:
        """Validate option conflicts"""
        if not self.is_enabled(option):
            return True  # Option not enabled, no conflicts
        
        success = True
        
        if 'conflicts' in rules:
            for conflict in rules['conflicts']:
                if self.is_enabled(conflict):
                    self.add_result(ValidationLevel.ERROR, "conflict",
                                  f"{option} conflicts with {conflict}",
                                  option, f"Disable {conflict}")
                    success = False
        
        return success
    
    def validate_security_implications(self, option: str, rules: Dict[str, Any]) -> bool:
        """Validate security implications"""
        if not self.is_enabled(option):
            return True
        
        if rules.get('security_implications'):
            security_level = rules.get('security_level', 'medium')
            
            if security_level == 'high':
                level = ValidationLevel.WARNING
            else:
                level = ValidationLevel.INFO
            
            self.add_result(level, "security",
                          f"{option} has security implications",
                          option, "Review security policies and access controls")
        
        return True
    
    def validate_performance_impact(self, option: str, rules: Dict[str, Any]) -> bool:
        """Validate performance implications"""
        if not self.is_enabled(option):
            return True
        
        if rules.get('performance_impact'):
            self.add_result(ValidationLevel.INFO, "performance",
                          f"{option} may impact system performance",
                          option, "Consider disabling in production")
        
        return True
    
    def check_cfg80211_dependencies(self, option: str) -> bool:
        """Custom validation for cfg80211"""
        if not self.is_enabled(option):
            return True
        
        success = True
        
        # Check for wireless extensions compatibility
        if self.is_enabled('CONFIG_WIRELESS_EXT') and not self.is_enabled('CONFIG_CFG80211_WEXT'):
            self.add_result(ValidationLevel.WARNING, "compatibility",
                          "Wireless extensions enabled but CFG80211_WEXT not found",
                          option, "Enable CONFIG_CFG80211_WEXT for compatibility")
        
        # Check regulatory domain support
        if not self.is_enabled('CONFIG_CFG80211_CERTIFICATION_ONUS'):
            self.add_result(ValidationLevel.INFO, "regulatory",
                          "Consider regulatory domain configuration",
                          option, "Review regulatory requirements")
        
        return success
    
    def check_mac80211_dependencies(self, option: str) -> bool:
        """Custom validation for mac80211"""
        if not self.is_enabled(option):
            return True
        
        success = True
        
        # Check rate control algorithms
        if not self.is_enabled('CONFIG_BACKPORTS_MAC80211_RC_MINSTREL'):
            self.add_result(ValidationLevel.WARNING, "rate_control",
                          "No rate control algorithm selected",
                          option, "Enable CONFIG_BACKPORTS_MAC80211_RC_MINSTREL")
        
        # Check mesh networking
        if self.is_enabled('CONFIG_BACKPORTS_MAC80211_MESH'):
            if not self.is_enabled('CONFIG_INET'):
                self.add_result(ValidationLevel.ERROR, "mesh",
                              "Mesh networking requires CONFIG_INET",
                              option, "Enable CONFIG_INET")
                success = False
        
        return success
    
    def check_monitor_mode_security(self, option: str) -> bool:
        """Custom validation for monitor mode security"""
        if not self.is_enabled(option):
            return True
        
        # Check for packet socket support
        if not self.is_enabled('CONFIG_PACKET'):
            self.add_result(ValidationLevel.ERROR, "monitor_mode",
                          "Monitor mode requires CONFIG_PACKET",
                          option, "Enable CONFIG_PACKET")
            return False
        
        # Security recommendations
        self.add_result(ValidationLevel.INFO, "security",
                      "Monitor mode allows packet capture - ensure proper access controls",
                      option, "Restrict access to monitor interfaces")
        
        return True
    
    def check_frame_injection_security(self, option: str) -> bool:
        """Custom validation for frame injection security"""
        if not self.is_enabled(option):
            return True
        
        # High security warning
        self.add_result(ValidationLevel.WARNING, "security",
                      "Frame injection has significant security implications",
                      option, "Implement strict access controls and audit logging")
        
        # Check for required capabilities
        if not self.is_enabled('CONFIG_PACKET_MMAP'):
            self.add_result(ValidationLevel.ERROR, "frame_injection",
                          "Frame injection requires CONFIG_PACKET_MMAP",
                          option, "Enable CONFIG_PACKET_MMAP")
            return False
        
        return True
    
    def check_android_compatibility(self, option: str) -> bool:
        """Custom validation for Android compatibility"""
        if not self.is_enabled(option):
            return True
        
        success = True
        
        # Check Android kernel features
        if not self.is_enabled('CONFIG_ANDROID'):
            self.add_result(ValidationLevel.ERROR, "android",
                          "Android backports require CONFIG_ANDROID",
                          option, "Enable CONFIG_ANDROID")
            success = False
        
        # Check for conflicting vendor drivers
        vendor_drivers = ['CONFIG_QCACLD', 'CONFIG_PRIMA_WLAN']
        for driver in vendor_drivers:
            if self.is_enabled(driver):
                self.add_result(ValidationLevel.ERROR, "android_conflict",
                              f"Android backports conflict with {driver}",
                              option, f"Disable {driver}")
                success = False
        
        return success
    
    def check_debug_implications(self, option: str) -> bool:
        """Custom validation for debug implications"""
        if not self.is_enabled(option):
            return True
        
        self.add_result(ValidationLevel.INFO, "debug",
                      "Debug features increase kernel size and may impact performance",
                      option, "Disable in production builds")
        
        # Check for verbose debugging
        if self.is_enabled('CONFIG_BACKPORTS_DEBUG_VERBOSE'):
            self.add_result(ValidationLevel.WARNING, "debug",
                          "Verbose debugging significantly increases log output",
                          option, "Use only for development")
        
        return True
    
    def check_radiotap_support(self, option: str) -> bool:
        """Custom validation for radiotap support"""
        if not self.is_enabled(option):
            return True
        
        self.add_result(ValidationLevel.INFO, "monitor_mode",
                      "Radiotap support provides detailed packet metadata",
                      option, "Essential for wireless analysis tools")
        
        return True
    
    def check_channel_switch_support(self, option: str) -> bool:
        """Custom validation for channel switching support"""
        if not self.is_enabled(option):
            return True
        
        # Check for nl80211 testmode support
        if not self.is_enabled('CONFIG_NL80211_TESTMODE'):
            self.add_result(ValidationLevel.WARNING, "monitor_mode",
                          "Channel switching may require nl80211 testmode support",
                          option, "Consider enabling CONFIG_NL80211_TESTMODE")
        
        return True
    
    def check_injection_rate_control(self, option: str) -> bool:
        """Custom validation for injection rate control"""
        if not self.is_enabled(option):
            return True
        
        self.add_result(ValidationLevel.INFO, "frame_injection",
                      "Rate control improves reliability of injected frames",
                      option, "Recommended for production frame injection")
        
        return True
    
    def check_injection_audit(self, option: str) -> bool:
        """Custom validation for injection security audit"""
        if not self.is_enabled(option):
            return True
        
        # Check for audit support
        if not self.is_enabled('CONFIG_AUDIT'):
            self.add_result(ValidationLevel.ERROR, "security",
                          "Security auditing requires CONFIG_AUDIT",
                          option, "Enable CONFIG_AUDIT")
            return False
        
        self.add_result(ValidationLevel.INFO, "security",
                      "Security auditing enabled for frame injection",
                      option, "Provides comprehensive logging of injection activities")
        
        return True
    
    def check_verbose_debug_implications(self, option: str) -> bool:
        """Custom validation for verbose debug implications"""
        if not self.is_enabled(option):
            return True
        
        self.add_result(ValidationLevel.WARNING, "debug",
                      "Verbose debugging generates significant log output",
                      option, "Use only for detailed debugging - impacts performance")
        
        return True
    
    def check_tracing_support(self, option: str) -> bool:
        """Custom validation for tracing support"""
        if not self.is_enabled(option):
            return True
        
        # Check for tracing support
        if not self.is_enabled('CONFIG_TRACING'):
            self.add_result(ValidationLevel.ERROR, "tracing",
                          "Tracing support requires CONFIG_TRACING",
                          option, "Enable CONFIG_TRACING")
            return False
        
        self.add_result(ValidationLevel.INFO, "tracing",
                      "Tracing support provides low-overhead profiling",
                      option, "Useful for performance analysis")
        
        return True
    
    def check_diagnostics_support(self, option: str) -> bool:
        """Custom validation for diagnostics support"""
        if not self.is_enabled(option):
            return True
        
        # Check for debugfs support
        if not self.is_enabled('CONFIG_DEBUG_FS'):
            self.add_result(ValidationLevel.ERROR, "diagnostics",
                          "Diagnostic interfaces require CONFIG_DEBUG_FS",
                          option, "Enable CONFIG_DEBUG_FS")
            return False
        
        self.add_result(ValidationLevel.INFO, "diagnostics",
                      "Diagnostic interfaces provide runtime debugging capabilities",
                      option, "Available in /sys/kernel/debug/backports/")
        
        return True
    
    def check_android_wakelock(self, option: str) -> bool:
        """Custom validation for Android wakelock integration"""
        if not self.is_enabled(option):
            return True
        
        # Check for Android wakelock support
        if not self.is_enabled('CONFIG_ANDROID_WAKELOCK'):
            self.add_result(ValidationLevel.ERROR, "android",
                          "Android wakelock integration requires CONFIG_ANDROID_WAKELOCK",
                          option, "Enable CONFIG_ANDROID_WAKELOCK")
            return False
        
        self.add_result(ValidationLevel.INFO, "android",
                      "Android wakelock integration provides proper power management",
                      option, "Essential for Android power management")
        
        return True
    
    def check_android_paranoid_network(self, option: str) -> bool:
        """Custom validation for Android paranoid networking"""
        if not self.is_enabled(option):
            return True
        
        # Check for paranoid networking support
        if not self.is_enabled('CONFIG_ANDROID_PARANOID_NETWORK'):
            self.add_result(ValidationLevel.ERROR, "android",
                          "Paranoid networking requires CONFIG_ANDROID_PARANOID_NETWORK",
                          option, "Enable CONFIG_ANDROID_PARANOID_NETWORK")
            return False
        
        self.add_result(ValidationLevel.INFO, "android",
                      "Paranoid networking provides Android security model compliance",
                      option, "Required for Android permission system integration")
        
        return True
    
    def check_vendor_compatibility(self, option: str) -> bool:
        """Custom validation for vendor driver compatibility"""
        if not self.is_enabled(option):
            return True
        
        self.add_result(ValidationLevel.INFO, "vendor",
                      "Vendor compatibility layer enables coexistence with vendor drivers",
                      option, "Useful for devices with existing vendor wireless drivers")
        
        return True
    
    def check_qcom_vendor_compatibility(self, option: str) -> bool:
        """Custom validation for Qualcomm vendor compatibility"""
        if not self.is_enabled(option):
            return True
        
        # Check for conflicting Qualcomm drivers
        qcom_drivers = ['CONFIG_QCACLD', 'CONFIG_PRIMA_WLAN', 'CONFIG_WCNSS_CORE']
        conflicting_drivers = [driver for driver in qcom_drivers if self.is_enabled(driver)]
        
        if conflicting_drivers:
            self.add_result(ValidationLevel.ERROR, "vendor",
                          f"Qualcomm compatibility conflicts with: {', '.join(conflicting_drivers)}",
                          option, f"Disable conflicting drivers: {', '.join(conflicting_drivers)}")
            return False
        
        self.add_result(ValidationLevel.INFO, "vendor",
                      "Qualcomm vendor compatibility provides QCACLD/PRIMA coexistence",
                      option, "Essential for Qualcomm-based Android devices")
        
        return True
    
    def check_android_security(self, option: str) -> bool:
        """Custom validation for Android security integration"""
        if not self.is_enabled(option):
            return True
        
        self.add_result(ValidationLevel.INFO, "security",
                      "Android security integration provides security model compliance",
                      option, "Essential for Android security policy compliance")
        
        return True
    
    def check_android_selinux(self, option: str) -> bool:
        """Custom validation for Android SELinux integration"""
        if not self.is_enabled(option):
            return True
        
        # Check for SELinux support
        if not self.is_enabled('CONFIG_SECURITY_SELINUX'):
            self.add_result(ValidationLevel.ERROR, "security",
                          "Android SELinux integration requires CONFIG_SECURITY_SELINUX",
                          option, "Enable CONFIG_SECURITY_SELINUX")
            return False
        
        self.add_result(ValidationLevel.INFO, "security",
                      "Android SELinux integration provides proper security contexts",
                      option, "Required for Android SELinux policy compliance")
        
        return True
    
    def run_custom_validations(self, option: str, rules: Dict[str, Any]) -> bool:
        """Run custom validation checks"""
        if 'validation_checks' not in rules:
            return True
        
        success = True
        for check_name in rules['validation_checks']:
            if hasattr(self, check_name):
                check_func = getattr(self, check_name)
                if not check_func(option):
                    success = False
            else:
                self.add_result(ValidationLevel.WARNING, "validation",
                              f"Unknown validation check: {check_name}",
                              option)
        
        return success
    
    def validate_global_consistency(self) -> bool:
        """Validate global configuration consistency"""
        success = True
        
        # Check for conflicting wireless stacks
        backports_enabled = self.is_enabled('CONFIG_BACKPORTS')
        kernel_cfg80211 = self.is_enabled('CONFIG_CFG80211')
        kernel_mac80211 = self.is_enabled('CONFIG_MAC80211')
        
        if backports_enabled and (kernel_cfg80211 or kernel_mac80211):
            self.add_result(ValidationLevel.ERROR, "global_conflict",
                          "Cannot enable both backports and kernel wireless stacks",
                          None, "Disable kernel wireless or backports")
            success = False
        
        # Check for incomplete backports configuration
        if self.is_enabled('CONFIG_BACKPORTS_MAC80211') and not self.is_enabled('CONFIG_BACKPORTS_CFG80211'):
            self.add_result(ValidationLevel.ERROR, "incomplete_config",
                          "MAC80211 requires CFG80211",
                          'CONFIG_BACKPORTS_MAC80211', "Enable CONFIG_BACKPORTS_CFG80211")
            success = False
        
        # Check for security configuration consistency
        if self.is_enabled('CONFIG_BACKPORTS_FRAME_INJECTION'):
            if not self.is_enabled('CONFIG_BACKPORTS_MONITOR_MODE'):
                self.add_result(ValidationLevel.ERROR, "security_config",
                              "Frame injection requires monitor mode",
                              'CONFIG_BACKPORTS_FRAME_INJECTION', 
                              "Enable CONFIG_BACKPORTS_MONITOR_MODE")
                success = False
        
        return success
    
    def validate_all(self) -> bool:
        """Run all validation checks"""
        if not self.read_config():
            return False
        
        overall_success = True
        
        # Validate each configured backports option
        for option, rules in self.validation_rules.items():
            if option in self.config:
                success = True
                success &= self.validate_option_type(option, rules)
                success &= self.validate_dependencies(option, rules)
                success &= self.validate_conflicts(option, rules)
                success &= self.validate_security_implications(option, rules)
                success &= self.validate_performance_impact(option, rules)
                success &= self.run_custom_validations(option, rules)
                
                if not success:
                    overall_success = False
        
        # Run global consistency checks
        if not self.validate_global_consistency():
            overall_success = False
        
        return overall_success
    
    def get_results_by_level(self, level: ValidationLevel) -> List[ValidationResult]:
        """Get results filtered by level"""
        return [r for r in self.results if r.level == level]
    
    def get_results_by_category(self, category: str) -> List[ValidationResult]:
        """Get results filtered by category"""
        return [r for r in self.results if r.category == category]
    
    def print_results(self, show_info: bool = True):
        """Print validation results"""
        # Count results by level
        error_count = len(self.get_results_by_level(ValidationLevel.ERROR))
        warning_count = len(self.get_results_by_level(ValidationLevel.WARNING))
        info_count = len(self.get_results_by_level(ValidationLevel.INFO))
        
        # Print summary
        print("Backports Configuration Validation Results")
        print("=" * 50)
        print(f"Errors: {error_count}")
        print(f"Warnings: {warning_count}")
        print(f"Info: {info_count}")
        print()
        
        # Print results by level
        for level in [ValidationLevel.ERROR, ValidationLevel.WARNING]:
            results = self.get_results_by_level(level)
            if results:
                level_name = level.value.upper()
                print(f"{level_name}S:")
                print("-" * (len(level_name) + 1))
                
                for result in results:
                    prefix = "❌" if level == ValidationLevel.ERROR else "⚠️ "
                    print(f"{prefix} [{result.category}] {result.message}")
                    if result.option:
                        print(f"   Option: {result.option}")
                    if result.suggestion:
                        print(f"   Suggestion: {result.suggestion}")
                    print()
        
        # Print info messages if requested
        if show_info:
            info_results = self.get_results_by_level(ValidationLevel.INFO)
            if info_results:
                print("INFO:")
                print("-----")
                for result in info_results:
                    print(f"ℹ️  [{result.category}] {result.message}")
                    if result.option:
                        print(f"   Option: {result.option}")
                    if result.suggestion:
                        print(f"   Suggestion: {result.suggestion}")
                    print()
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate detailed validation report"""
        return {
            'summary': {
                'total_results': len(self.results),
                'errors': len(self.get_results_by_level(ValidationLevel.ERROR)),
                'warnings': len(self.get_results_by_level(ValidationLevel.WARNING)),
                'info': len(self.get_results_by_level(ValidationLevel.INFO)),
                'success': len(self.get_results_by_level(ValidationLevel.ERROR)) == 0
            },
            'results': [
                {
                    'level': r.level.value,
                    'category': r.category,
                    'message': r.message,
                    'option': r.option,
                    'suggestion': r.suggestion,
                    'details': r.details
                }
                for r in self.results
            ],
            'configuration': {
                'backports_options': {
                    k: v for k, v in self.config.items() 
                    if k.startswith('CONFIG_BACKPORTS')
                }
            }
        }

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Validate backports configuration')
    parser.add_argument('--kernel-root', default='.', help='Path to kernel source root')
    parser.add_argument('--no-info', action='store_true', help='Hide info messages')
    parser.add_argument('--json', action='store_true', help='Output JSON report')
    parser.add_argument('--report-file', help='Save report to file')
    
    args = parser.parse_args()
    
    validator = BackportsConfigValidator(args.kernel_root)
    success = validator.validate_all()
    
    if args.json:
        report = validator.generate_report()
        if args.report_file:
            with open(args.report_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"Report saved to: {args.report_file}")
        else:
            print(json.dumps(report, indent=2))
    else:
        validator.print_results(show_info=not args.no_info)
        
        if args.report_file:
            report = validator.generate_report()
            with open(args.report_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"Detailed report saved to: {args.report_file}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())