#!/usr/bin/env python3
"""
Backports Dependency Validation Engine

This script validates backports configuration dependencies, checks for
required kernel features, and ensures compatibility with the target
kernel version and architecture.
"""

import os
import sys
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set

class BackportsDependencyValidator:
    """Validates backports dependencies and requirements"""
    
    def __init__(self, kernel_root: str = "."):
        self.kernel_root = Path(kernel_root).resolve()
        self.backports_dir = self.kernel_root / "backports-generated-6.1"
        self.config_file = self.kernel_root / ".config"
        self.errors = []
        self.warnings = []
        self.info = []
        
        # Minimum requirements
        self.min_kernel_version = (4, 19, 0)
        self.supported_architectures = {"arm64", "x86_64", "arm", "x86"}
        
        # Dependency graph
        self.dependencies = {
            'CONFIG_BACKPORTS': {
                'kernel_features': ['CONFIG_MODULES', 'CONFIG_NET'],
                'kernel_version': (4, 19, 0),
                'architectures': ['arm64', 'x86_64', 'arm', 'x86'],
                'conflicts': ['CONFIG_CFG80211', 'CONFIG_MAC80211'],
                'build_deps': ['make', 'gcc', 'python3']
            },
            'CONFIG_BACKPORTS_CFG80211': {
                'depends': ['CONFIG_BACKPORTS'],
                'kernel_features': ['CONFIG_RFKILL', 'CONFIG_CRYPTO'],
                'optional_features': ['CONFIG_WIRELESS_EXT'],
                'conflicts': ['CONFIG_CFG80211']
            },
            'CONFIG_BACKPORTS_MAC80211': {
                'depends': ['CONFIG_BACKPORTS_CFG80211'],
                'kernel_features': ['CONFIG_CRYPTO_ARC4', 'CONFIG_CRYPTO_AES', 'CONFIG_CRC32'],
                'optional_features': ['CONFIG_LEDS_CLASS', 'CONFIG_DEBUG_FS'],
                'conflicts': ['CONFIG_MAC80211']
            },
            'CONFIG_BACKPORTS_MONITOR_MODE': {
                'depends': ['CONFIG_BACKPORTS_MAC80211'],
                'kernel_features': ['CONFIG_PACKET'],
                'optional_features': ['CONFIG_NETFILTER']
            },
            'CONFIG_BACKPORTS_FRAME_INJECTION': {
                'depends': ['CONFIG_BACKPORTS_MONITOR_MODE'],
                'kernel_features': ['CONFIG_PACKET_MMAP'],
                'security_warning': True
            },
            'CONFIG_BACKPORTS_ANDROID': {
                'depends': ['CONFIG_BACKPORTS'],
                'kernel_features': ['CONFIG_ANDROID'],
                'optional_features': ['CONFIG_ANDROID_PARANOID_NETWORK']
            }
        }
    
    def log_error(self, message: str):
        """Log an error message"""
        self.errors.append(message)
        print(f"❌ ERROR: {message}")
    
    def log_warning(self, message: str):
        """Log a warning message"""
        self.warnings.append(message)
        print(f"⚠️  WARNING: {message}")
    
    def log_info(self, message: str):
        """Log an info message"""
        self.info.append(message)
        print(f"ℹ️  INFO: {message}")
    
    def get_kernel_version(self) -> Tuple[int, int, int]:
        """Get the kernel version from Makefile"""
        try:
            makefile = self.kernel_root / "Makefile"
            if not makefile.exists():
                self.log_error(f"Kernel Makefile not found: {makefile}")
                return (0, 0, 0)
            
            version_info = {}
            with open(makefile, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('VERSION ='):
                        version_info['VERSION'] = int(line.split('=')[1].strip())
                    elif line.startswith('PATCHLEVEL ='):
                        version_info['PATCHLEVEL'] = int(line.split('=')[1].strip())
                    elif line.startswith('SUBLEVEL ='):
                        version_info['SUBLEVEL'] = int(line.split('=')[1].strip())
                    
                    if len(version_info) == 3:
                        break
            
            return (version_info.get('VERSION', 0), 
                   version_info.get('PATCHLEVEL', 0), 
                   version_info.get('SUBLEVEL', 0))
        
        except Exception as e:
            self.log_error(f"Failed to get kernel version: {e}")
            return (0, 0, 0)
    
    def get_architecture(self) -> str:
        """Get the target architecture"""
        try:
            # Check ARCH environment variable first
            arch = os.environ.get('ARCH')
            if arch:
                return arch
            
            # Try to detect from kernel config
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    for line in f:
                        if line.startswith('CONFIG_ARM64=y'):
                            return 'arm64'
                        elif line.startswith('CONFIG_ARM=y'):
                            return 'arm'
                        elif line.startswith('CONFIG_X86_64=y'):
                            return 'x86_64'
                        elif line.startswith('CONFIG_X86=y'):
                            return 'x86'
            
            # Fallback to uname
            result = subprocess.run(['uname', '-m'], capture_output=True, text=True)
            if result.returncode == 0:
                machine = result.stdout.strip()
                arch_map = {
                    'aarch64': 'arm64',
                    'armv7l': 'arm',
                    'x86_64': 'x86_64',
                    'i386': 'x86',
                    'i686': 'x86'
                }
                return arch_map.get(machine, machine)
            
            return 'unknown'
        
        except Exception as e:
            self.log_warning(f"Failed to detect architecture: {e}")
            return 'unknown'
    
    def read_kernel_config(self) -> Dict[str, str]:
        """Read kernel configuration"""
        config = {}
        
        if not self.config_file.exists():
            self.log_warning(f"Kernel config file not found: {self.config_file}")
            return config
        
        try:
            with open(self.config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('#') or not line:
                        continue
                    
                    if '=' in line:
                        key, value = line.split('=', 1)
                        config[key] = value
        
        except Exception as e:
            self.log_error(f"Failed to read kernel config: {e}")
        
        return config
    
    def check_kernel_version(self) -> bool:
        """Check if kernel version meets minimum requirements"""
        current_version = self.get_kernel_version()
        
        if current_version == (0, 0, 0):
            self.log_error("Could not determine kernel version")
            return False
        
        if current_version < self.min_kernel_version:
            self.log_error(f"Kernel version {'.'.join(map(str, current_version))} is too old. "
                          f"Minimum required: {'.'.join(map(str, self.min_kernel_version))}")
            return False
        
        self.log_info(f"Kernel version {'.'.join(map(str, current_version))} meets requirements")
        return True
    
    def check_architecture(self) -> bool:
        """Check if architecture is supported"""
        arch = self.get_architecture()
        
        if arch == 'unknown':
            self.log_warning("Could not determine target architecture")
            return True  # Don't fail on unknown architecture
        
        if arch not in self.supported_architectures:
            self.log_error(f"Architecture '{arch}' is not supported. "
                          f"Supported: {', '.join(self.supported_architectures)}")
            return False
        
        self.log_info(f"Architecture '{arch}' is supported")
        return True
    
    def check_build_dependencies(self) -> bool:
        """Check if build dependencies are available"""
        build_deps = self.dependencies['CONFIG_BACKPORTS']['build_deps']
        missing_deps = []
        
        for dep in build_deps:
            try:
                result = subprocess.run(['which', dep], capture_output=True)
                if result.returncode != 0:
                    missing_deps.append(dep)
            except Exception:
                missing_deps.append(dep)
        
        if missing_deps:
            self.log_error(f"Missing build dependencies: {', '.join(missing_deps)}")
            return False
        
        self.log_info("All build dependencies are available")
        return True
    
    def check_backports_directory(self) -> bool:
        """Check if backports directory exists and is valid"""
        if not self.backports_dir.exists():
            self.log_error(f"Backports directory not found: {self.backports_dir}")
            return False
        
        required_files = ['Makefile', 'Kconfig', 'net/wireless/', 'net/mac80211/']
        missing_files = []
        
        for file_path in required_files:
            full_path = self.backports_dir / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            self.log_error(f"Missing backports files: {', '.join(missing_files)}")
            return False
        
        self.log_info("Backports directory structure is valid")
        return True
    
    def validate_config_dependencies(self, config: Dict[str, str]) -> bool:
        """Validate configuration dependencies"""
        success = True
        
        for config_option, requirements in self.dependencies.items():
            if config.get(config_option) not in ['y', 'm']:
                continue  # Option not enabled, skip validation
            
            self.log_info(f"Validating {config_option}...")
            
            # Check direct dependencies
            if 'depends' in requirements:
                for dep in requirements['depends']:
                    if config.get(dep) not in ['y', 'm']:
                        self.log_error(f"{config_option} requires {dep} to be enabled")
                        success = False
            
            # Check kernel feature dependencies
            if 'kernel_features' in requirements:
                for feature in requirements['kernel_features']:
                    if config.get(feature) not in ['y', 'm']:
                        self.log_error(f"{config_option} requires kernel feature {feature}")
                        success = False
            
            # Check optional features (warnings only)
            if 'optional_features' in requirements:
                for feature in requirements['optional_features']:
                    if config.get(feature) not in ['y', 'm']:
                        self.log_warning(f"{config_option} recommends kernel feature {feature}")
            
            # Check conflicts
            if 'conflicts' in requirements:
                for conflict in requirements['conflicts']:
                    if config.get(conflict) in ['y', 'm']:
                        self.log_error(f"{config_option} conflicts with {conflict}")
                        success = False
            
            # Security warnings
            if requirements.get('security_warning'):
                self.log_warning(f"{config_option} has security implications. "
                               "Ensure proper security measures are in place.")
        
        return success
    
    def check_cross_compilation(self) -> bool:
        """Check cross-compilation setup if needed"""
        arch = self.get_architecture()
        host_arch = subprocess.run(['uname', '-m'], capture_output=True, text=True).stdout.strip()
        
        # Map architectures for comparison
        arch_map = {'aarch64': 'arm64', 'armv7l': 'arm', 'x86_64': 'x86_64', 'i686': 'x86'}
        host_arch = arch_map.get(host_arch, host_arch)
        
        if arch != host_arch and arch != 'unknown':
            # Cross-compilation needed
            cross_compile = os.environ.get('CROSS_COMPILE')
            if not cross_compile:
                self.log_warning(f"Cross-compilation detected ({host_arch} -> {arch}) "
                               "but CROSS_COMPILE not set")
                return True  # Don't fail, just warn
            
            # Check if cross-compiler exists
            try:
                result = subprocess.run([f'{cross_compile}gcc', '--version'], 
                                      capture_output=True)
                if result.returncode != 0:
                    self.log_error(f"Cross-compiler not found: {cross_compile}gcc")
                    return False
            except Exception:
                self.log_error(f"Cross-compiler not found: {cross_compile}gcc")
                return False
            
            self.log_info(f"Cross-compilation setup validated ({cross_compile})")
        
        return True
    
    def generate_dependency_report(self, config: Dict[str, str]) -> str:
        """Generate a detailed dependency report"""
        report = []
        report.append("Backports Dependency Validation Report")
        report.append("=" * 50)
        report.append("")
        
        # System information
        kernel_version = self.get_kernel_version()
        arch = self.get_architecture()
        
        report.append("System Information:")
        report.append(f"  Kernel Version: {'.'.join(map(str, kernel_version))}")
        report.append(f"  Architecture: {arch}")
        report.append(f"  Kernel Root: {self.kernel_root}")
        report.append(f"  Backports Dir: {self.backports_dir}")
        report.append("")
        
        # Configuration summary
        report.append("Backports Configuration:")
        backports_configs = [k for k in config.keys() if k.startswith('CONFIG_BACKPORTS')]
        if backports_configs:
            for cfg in sorted(backports_configs):
                value = config[cfg]
                report.append(f"  {cfg}: {value}")
        else:
            report.append("  No backports configuration found")
        report.append("")
        
        # Validation results
        report.append("Validation Results:")
        if self.errors:
            report.append("  Errors:")
            for error in self.errors:
                report.append(f"    - {error}")
        
        if self.warnings:
            report.append("  Warnings:")
            for warning in self.warnings:
                report.append(f"    - {warning}")
        
        if not self.errors and not self.warnings:
            report.append("  ✓ All validations passed")
        
        report.append("")
        
        # Recommendations
        if self.warnings or self.errors:
            report.append("Recommendations:")
            if self.errors:
                report.append("  - Fix all errors before building backports")
            if self.warnings:
                report.append("  - Review warnings and enable recommended features if needed")
            report.append("  - Run 'make menuconfig' to adjust configuration")
            report.append("  - Check kernel documentation for feature requirements")
        
        return "\n".join(report)
    
    def validate_all(self) -> bool:
        """Run all validation checks"""
        print("Backports Dependency Validation")
        print("=" * 40)
        print()
        
        success = True
        
        # Basic system checks
        success &= self.check_kernel_version()
        success &= self.check_architecture()
        success &= self.check_build_dependencies()
        success &= self.check_backports_directory()
        success &= self.check_cross_compilation()
        
        # Configuration validation
        config = self.read_kernel_config()
        success &= self.validate_config_dependencies(config)
        
        print()
        print("Validation Summary:")
        print(f"  Errors: {len(self.errors)}")
        print(f"  Warnings: {len(self.warnings)}")
        print(f"  Info: {len(self.info)}")
        
        if success and not self.errors:
            print()
            print("✅ All dependency validations passed!")
            return True
        else:
            print()
            print("❌ Dependency validation failed!")
            return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate backports dependencies')
    parser.add_argument('--kernel-root', default='.', 
                       help='Path to kernel source root')
    parser.add_argument('--report', action='store_true',
                       help='Generate detailed report')
    parser.add_argument('--report-file', 
                       help='Save report to file')
    
    args = parser.parse_args()
    
    validator = BackportsDependencyValidator(args.kernel_root)
    success = validator.validate_all()
    
    if args.report or args.report_file:
        config = validator.read_kernel_config()
        report = validator.generate_dependency_report(config)
        
        if args.report_file:
            with open(args.report_file, 'w') as f:
                f.write(report)
            print(f"\nReport saved to: {args.report_file}")
        else:
            print("\n" + "=" * 50)
            print(report)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())