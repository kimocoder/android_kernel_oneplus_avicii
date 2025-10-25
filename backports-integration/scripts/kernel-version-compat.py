#!/usr/bin/env python3
"""
Kernel Version Compatibility Detection and Configuration

This script detects the kernel version and configures compatibility
settings for wireless drivers across different kernel versions.
"""

import os
import sys
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class KernelVersionDetector:
    """Kernel version detection and compatibility configuration"""
    
    def __init__(self, kernel_root: str = "."):
        """Initialize kernel version detector"""
        self.kernel_root = Path(kernel_root).resolve()
        self.backports_dir = self.kernel_root / "backports-integration"
        self.compat_dir = self.backports_dir / "compat"
        
        # Kernel version information
        self.version_info = self._detect_kernel_version()
        
        # Compatibility matrix
        self.compatibility_matrix = self._load_compatibility_matrix()
    
    def _detect_kernel_version(self) -> Dict[str, any]:
        """Detect kernel version information"""
        version_info = {
            "version_string": "unknown",
            "major": 0,
            "minor": 0,
            "patch": 0,
            "version_code": 0,
            "is_android": False,
            "android_version": None,
            "is_lts": False,
            "architecture": "unknown",
            "config_options": []
        }
        
        try:
            # Try to get version from uname
            result = subprocess.run(["uname", "-r"], capture_output=True, text=True)
            if result.returncode == 0:
                version_string = result.stdout.strip()
                version_info["version_string"] = version_string
                
                # Parse version numbers
                match = re.match(r"(\d+)\.(\d+)\.(\d+)", version_string)
                if match:
                    version_info["major"] = int(match.group(1))
                    version_info["minor"] = int(match.group(2))
                    version_info["patch"] = int(match.group(3))
                    version_info["version_code"] = (
                        (version_info["major"] << 16) +
                        (version_info["minor"] << 8) +
                        version_info["patch"]
                    )
                
                # Check for Android kernel
                if "android" in version_string.lower():
                    version_info["is_android"] = True
                    
                    # Try to extract Android version
                    android_match = re.search(r"android(\d+)", version_string.lower())
                    if android_match:
                        version_info["android_version"] = int(android_match.group(1))
                
                # Check for LTS
                if "lts" in version_string.lower():
                    version_info["is_lts"] = True
        
        except Exception as e:
            print(f"Warning: Could not detect kernel version from uname: {e}")
        
        try:
            # Try to get architecture
            result = subprocess.run(["uname", "-m"], capture_output=True, text=True)
            if result.returncode == 0:
                version_info["architecture"] = result.stdout.strip()
        
        except Exception:
            pass
        
        # Try to read kernel config
        config_paths = [
            "/proc/config.gz",
            "/boot/config-" + version_info["version_string"],
            self.kernel_root / ".config"
        ]
        
        for config_path in config_paths:
            try:
                if Path(config_path).exists():
                    version_info["config_options"] = self._parse_kernel_config(config_path)
                    break
            except Exception:
                continue
        
        return version_info
    
    def _parse_kernel_config(self, config_path: Path) -> List[str]:
        """Parse kernel configuration file"""
        config_options = []
        
        try:
            if str(config_path).endswith(".gz"):
                import gzip
                with gzip.open(config_path, 'rt') as f:
                    content = f.read()
            else:
                with open(config_path, 'r') as f:
                    content = f.read()
            
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith("CONFIG_") and "=y" in line:
                    config_name = line.split('=')[0]
                    config_options.append(config_name)
        
        except Exception as e:
            print(f"Warning: Could not parse kernel config {config_path}: {e}")
        
        return config_options
    
    def _load_compatibility_matrix(self) -> Dict[str, Dict]:
        """Load kernel version compatibility matrix"""
        return {
            "4.19": {
                "android_optimized": True,
                "mobile_platform": True,
                "power_management": "advanced",
                "regulatory_api": "v2",
                "cfg80211_features": ["scan_info_v2", "connect_timeout"],
                "mac80211_features": ["txq_support", "airtime_fairness"],
                "netlink_features": ["ext_ack"],
                "skb_features": ["put_zero", "put_data"],
                "timer_api": "new",
                "workqueue_features": ["highpri"],
                "compatibility_shims": [
                    "android_wakelock",
                    "android_power",
                    "vendor_compat",
                    "regulatory_enforcement"
                ]
            },
            "5.4": {
                "android_optimized": False,
                "mobile_platform": False,
                "power_management": "standard",
                "regulatory_api": "v3",
                "cfg80211_features": ["scan_info_v2", "connect_timeout", "nan_support"],
                "mac80211_features": ["txq_support", "airtime_fairness", "he_support"],
                "netlink_features": ["ext_ack", "policy_validation"],
                "skb_features": ["put_zero", "put_data", "linear_data"],
                "timer_api": "new",
                "workqueue_features": ["highpri", "power_efficient"],
                "compatibility_shims": [
                    "regulatory_enforcement"
                ]
            },
            "5.10": {
                "android_optimized": False,
                "mobile_platform": False,
                "power_management": "standard",
                "regulatory_api": "v3",
                "cfg80211_features": ["scan_info_v2", "connect_timeout", "nan_support", "6ghz_support"],
                "mac80211_features": ["txq_support", "airtime_fairness", "he_support", "multi_bssid"],
                "netlink_features": ["ext_ack", "policy_validation", "strict_validation"],
                "skb_features": ["put_zero", "put_data", "linear_data", "frag_list"],
                "timer_api": "new",
                "workqueue_features": ["highpri", "power_efficient", "unbound"],
                "compatibility_shims": []
            },
            "6.1": {
                "android_optimized": False,
                "mobile_platform": False,
                "power_management": "advanced",
                "regulatory_api": "v4",
                "cfg80211_features": ["scan_info_v2", "connect_timeout", "nan_support", "6ghz_support", "eht_support"],
                "mac80211_features": ["txq_support", "airtime_fairness", "he_support", "multi_bssid", "eht_support"],
                "netlink_features": ["ext_ack", "policy_validation", "strict_validation", "genetlink_v2"],
                "skb_features": ["put_zero", "put_data", "linear_data", "frag_list", "gso_partial"],
                "timer_api": "new",
                "workqueue_features": ["highpri", "power_efficient", "unbound", "cpu_intensive"],
                "compatibility_shims": []
            }
        }
    
    def get_kernel_version_string(self) -> str:
        """Get kernel version string"""
        return f"{self.version_info['major']}.{self.version_info['minor']}"
    
    def is_android_kernel(self) -> bool:
        """Check if this is an Android kernel"""
        return self.version_info["is_android"]
    
    def is_mobile_platform(self) -> bool:
        """Check if this is a mobile platform"""
        arch = self.version_info["architecture"]
        return (arch in ["arm", "arm64", "aarch64"] or 
                self.version_info["is_android"])
    
    def get_compatibility_features(self) -> Dict[str, any]:
        """Get compatibility features for current kernel"""
        version_key = self.get_kernel_version_string()
        
        # Find closest matching version
        available_versions = list(self.compatibility_matrix.keys())
        available_versions.sort(key=lambda x: tuple(map(int, x.split('.'))))
        
        selected_version = None
        current_version_tuple = (self.version_info["major"], self.version_info["minor"])
        
        for version in available_versions:
            version_tuple = tuple(map(int, version.split('.')))
            if version_tuple <= current_version_tuple:
                selected_version = version
            else:
                break
        
        if not selected_version:
            selected_version = available_versions[0]  # Fallback to oldest
        
        features = self.compatibility_matrix[selected_version].copy()
        
        # Override based on detected platform
        if self.is_android_kernel():
            features["android_optimized"] = True
            features["mobile_platform"] = True
        
        if self.is_mobile_platform():
            features["mobile_platform"] = True
        
        return features
    
    def generate_compatibility_header(self) -> str:
        """Generate compatibility header content"""
        features = self.get_compatibility_features()
        version_string = self.get_kernel_version_string()
        
        header_lines = [
            "/* Auto-generated kernel compatibility configuration */",
            f"/* Kernel version: {self.version_info['version_string']} */",
            f"/* Generated on: {subprocess.run(['date'], capture_output=True, text=True).stdout.strip()} */",
            "",
            "#ifndef BACKPORTS_KERNEL_COMPAT_CONFIG_H",
            "#define BACKPORTS_KERNEL_COMPAT_CONFIG_H",
            "",
            "/* Kernel version information */",
            f"#define BACKPORTS_KERNEL_VERSION_MAJOR {self.version_info['major']}",
            f"#define BACKPORTS_KERNEL_VERSION_MINOR {self.version_info['minor']}",
            f"#define BACKPORTS_KERNEL_VERSION_PATCH {self.version_info['patch']}",
            f"#define BACKPORTS_KERNEL_VERSION_CODE {self.version_info['version_code']}",
            f"#define BACKPORTS_KERNEL_VERSION_STRING \"{self.version_info['version_string']}\"",
            "",
            "/* Platform detection */",
            f"#define BACKPORTS_IS_ANDROID_KERNEL {1 if self.is_android_kernel() else 0}",
            f"#define BACKPORTS_IS_MOBILE_PLATFORM {1 if self.is_mobile_platform() else 0}",
            f"#define BACKPORTS_IS_LTS_KERNEL {1 if self.version_info['is_lts'] else 0}",
            "",
            "/* Feature availability */",
        ]
        
        # Add feature definitions
        for feature_category, feature_list in features.items():
            if isinstance(feature_list, list):
                for feature in feature_list:
                    feature_name = f"BACKPORTS_HAS_{feature_category.upper()}_{feature.upper()}"
                    header_lines.append(f"#define {feature_name} 1")
            elif isinstance(feature_list, bool):
                feature_name = f"BACKPORTS_{feature_category.upper()}"
                header_lines.append(f"#define {feature_name} {1 if feature_list else 0}")
            elif isinstance(feature_list, str):
                feature_name = f"BACKPORTS_{feature_category.upper()}"
                header_lines.append(f"#define {feature_name} \"{feature_list}\"")
        
        # Add compatibility shim definitions
        if "compatibility_shims" in features:
            header_lines.append("")
            header_lines.append("/* Compatibility shims required */")
            for shim in features["compatibility_shims"]:
                shim_name = f"BACKPORTS_NEED_{shim.upper()}"
                header_lines.append(f"#define {shim_name} 1")
        
        header_lines.extend([
            "",
            "#endif /* BACKPORTS_KERNEL_COMPAT_CONFIG_H */"
        ])
        
        return "\n".join(header_lines)
    
    def generate_compatibility_makefile(self) -> str:
        """Generate compatibility Makefile content"""
        features = self.get_compatibility_features()
        
        makefile_lines = [
            "# Auto-generated kernel compatibility Makefile",
            f"# Kernel version: {self.version_info['version_string']}",
            f"# Generated on: {subprocess.run(['date'], capture_output=True, text=True).stdout.strip()}",
            "",
            "# Kernel version variables",
            f"KERNEL_VERSION_MAJOR := {self.version_info['major']}",
            f"KERNEL_VERSION_MINOR := {self.version_info['minor']}",
            f"KERNEL_VERSION_PATCH := {self.version_info['patch']}",
            f"KERNEL_VERSION_CODE := {self.version_info['version_code']}",
            "",
            "# Platform detection",
            f"IS_ANDROID_KERNEL := {1 if self.is_android_kernel() else 0}",
            f"IS_MOBILE_PLATFORM := {1 if self.is_mobile_platform() else 0}",
            "",
            "# Compatibility flags",
        ]
        
        # Add compatibility flags
        for feature_category, feature_value in features.items():
            if isinstance(feature_value, bool):
                flag_name = f"COMPAT_{feature_category.upper()}"
                makefile_lines.append(f"{flag_name} := {1 if feature_value else 0}")
        
        # Add conditional compilation rules
        makefile_lines.extend([
            "",
            "# Conditional compilation",
            "ifeq ($(IS_ANDROID_KERNEL),1)",
            "ccflags-y += -DBACKPORTS_ANDROID_KERNEL=1",
            "endif",
            "",
            "ifeq ($(IS_MOBILE_PLATFORM),1)", 
            "ccflags-y += -DBACKPORTS_MOBILE_PLATFORM=1",
            "endif",
            "",
            "# Version-specific flags",
            f"ccflags-y += -DKERNEL_VERSION_CODE={self.version_info['version_code']}",
        ])
        
        return "\n".join(makefile_lines)
    
    def write_compatibility_files(self) -> None:
        """Write compatibility configuration files"""
        # Ensure compat directory exists
        self.compat_dir.mkdir(parents=True, exist_ok=True)
        
        # Write compatibility header
        header_content = self.generate_compatibility_header()
        header_file = self.compat_dir / "kernel-compat-config.h"
        with open(header_file, 'w') as f:
            f.write(header_content)
        print(f"Generated compatibility header: {header_file}")
        
        # Write compatibility Makefile
        makefile_content = self.generate_compatibility_makefile()
        makefile_file = self.compat_dir / "kernel-compat.mk"
        with open(makefile_file, 'w') as f:
            f.write(makefile_content)
        print(f"Generated compatibility Makefile: {makefile_file}")
    
    def check_compatibility_requirements(self) -> List[str]:
        """Check compatibility requirements and return warnings"""
        warnings = []
        features = self.get_compatibility_features()
        
        # Check for Android kernel requirements
        if self.is_android_kernel():
            required_configs = [
                "CONFIG_ANDROID",
                "CONFIG_ANDROID_BINDER_IPC"
            ]
            
            for config in required_configs:
                if config not in self.version_info["config_options"]:
                    warnings.append(f"Android kernel missing required config: {config}")
        
        # Check for mobile platform requirements
        if self.is_mobile_platform():
            recommended_configs = [
                "CONFIG_PM_RUNTIME",
                "CONFIG_PM_SLEEP"
            ]
            
            for config in recommended_configs:
                if config not in self.version_info["config_options"]:
                    warnings.append(f"Mobile platform missing recommended config: {config}")
        
        # Check kernel version compatibility
        if self.version_info["major"] < 4 or (self.version_info["major"] == 4 and self.version_info["minor"] < 19):
            warnings.append("Kernel version may be too old for full compatibility")
        
        return warnings
    
    def generate_compatibility_report(self) -> str:
        """Generate comprehensive compatibility report"""
        features = self.get_compatibility_features()
        warnings = self.check_compatibility_requirements()
        
        report_lines = [
            "Kernel Version Compatibility Report",
            "=" * 40,
            f"Kernel Version: {self.version_info['version_string']}",
            f"Version Code: {self.version_info['version_code']}",
            f"Architecture: {self.version_info['architecture']}",
            f"Android Kernel: {'Yes' if self.is_android_kernel() else 'No'}",
            f"Mobile Platform: {'Yes' if self.is_mobile_platform() else 'No'}",
            f"LTS Kernel: {'Yes' if self.version_info['is_lts'] else 'No'}",
            "",
            "Compatibility Features:",
        ]
        
        for feature_category, feature_value in features.items():
            if isinstance(feature_value, list):
                report_lines.append(f"  {feature_category}: {', '.join(feature_value)}")
            else:
                report_lines.append(f"  {feature_category}: {feature_value}")
        
        if warnings:
            report_lines.extend([
                "",
                "Warnings:",
            ])
            for warning in warnings:
                report_lines.append(f"  - {warning}")
        
        report_lines.extend([
            "",
            "Compatibility Shims Required:",
        ])
        
        if "compatibility_shims" in features:
            for shim in features["compatibility_shims"]:
                report_lines.append(f"  - {shim}")
        else:
            report_lines.append("  None")
        
        return "\n".join(report_lines)

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Kernel Version Compatibility Detection")
    parser.add_argument("command", choices=[
        "detect", "generate", "check", "report"
    ], help="Compatibility command")
    
    parser.add_argument("--kernel-root", default=".", help="Kernel root directory")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    detector = KernelVersionDetector(args.kernel_root)
    
    if args.command == "detect":
        print("Kernel Version Detection:")
        print(f"Version: {detector.version_info['version_string']}")
        print(f"Version Code: {detector.version_info['version_code']}")
        print(f"Architecture: {detector.version_info['architecture']}")
        print(f"Android: {'Yes' if detector.is_android_kernel() else 'No'}")
        print(f"Mobile Platform: {'Yes' if detector.is_mobile_platform() else 'No'}")
        
        if args.verbose:
            features = detector.get_compatibility_features()
            print("\nCompatibility Features:")
            for key, value in features.items():
                print(f"  {key}: {value}")
    
    elif args.command == "generate":
        detector.write_compatibility_files()
        print("Compatibility files generated successfully")
    
    elif args.command == "check":
        warnings = detector.check_compatibility_requirements()
        
        if warnings:
            print("Compatibility Warnings:")
            for warning in warnings:
                print(f"  - {warning}")
            return 1
        else:
            print("✅ No compatibility issues detected")
            return 0
    
    elif args.command == "report":
        report = detector.generate_compatibility_report()
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(report)
            print(f"Compatibility report saved to: {args.output}")
        else:
            print(report)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())