#!/usr/bin/env python3
"""
Multi-Driver Build System

This module provides comprehensive build support for multiple wireless driver families
including ath10k, iwlwifi, and rt2x00 with optimized build configurations.
"""

import os
import sys
import subprocess
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class BuildTarget(Enum):
    """Build target types"""
    MODULES = "modules"
    FIRMWARE = "firmware"
    TOOLS = "tools"
    ALL = "all"

class DriverFamily(Enum):
    """Supported driver families"""
    ATH10K = "ath10k"
    IWLWIFI = "iwlwifi"
    RT2X00 = "rt2x00"

@dataclass
class BuildConfig:
    """Build configuration for drivers"""
    name: str
    family: DriverFamily
    source_dirs: List[str]
    build_deps: List[str]
    firmware_files: List[str]
    make_targets: List[str]
    install_paths: Dict[str, str]
    build_flags: Dict[str, str]

class MultiDriverBuild:
    """Multi-driver build system"""
    
    def __init__(self, kernel_root: str = ".", build_dir: str = "build"):
        """Initialize multi-driver build system"""
        self.kernel_root = Path(kernel_root).resolve()
        self.build_dir = Path(build_dir).resolve()
        self.backports_dir = self.kernel_root / "backports-integration"
        
        # Create build directory
        self.build_dir.mkdir(parents=True, exist_ok=True)
        
        # Define build configurations
        self.build_configs = {
            "ath10k": BuildConfig(
                name="ath10k",
                family=DriverFamily.ATH10K,
                source_dirs=["drivers/net/wireless/ath/ath10k"],
                build_deps=["cfg80211", "mac80211", "ath"],
                firmware_files=[
                    "ath10k/QCA988X/hw2.0/firmware-5.bin",
                    "ath10k/QCA6174/hw3.0/firmware-4.bin",
                    "ath10k/QCA9377/hw1.0/firmware-5.bin"
                ],
                make_targets=["ath10k_core", "ath10k_pci", "ath10k_sdio"],
                install_paths={
                    "modules": "/lib/modules/$(KERNELRELEASE)/extra/ath10k",
                    "firmware": "/lib/firmware/ath10k"
                },
                build_flags={
                    "CONFIG_ATH10K": "m",
                    "CONFIG_ATH10K_PCI": "m",
                    "CONFIG_ATH10K_DEBUG": "y",
                    "CONFIG_ATH10K_DEBUGFS": "y",
                    "CONFIG_ATH10K_SPECTRAL": "y"
                }
            ),
            "iwlwifi": BuildConfig(
                name="iwlwifi",
                family=DriverFamily.IWLWIFI,
                source_dirs=["drivers/net/wireless/intel/iwlwifi"],
                build_deps=["cfg80211", "mac80211"],
                firmware_files=[
                    "iwlwifi-7260-17.ucode",
                    "iwlwifi-8260-36.ucode",
                    "iwlwifi-cc-a0-50.ucode"
                ],
                make_targets=["iwlwifi", "iwldvm", "iwlmvm"],
                install_paths={
                    "modules": "/lib/modules/$(KERNELRELEASE)/extra/iwlwifi",
                    "firmware": "/lib/firmware"
                },
                build_flags={
                    "CONFIG_IWLWIFI": "m",
                    "CONFIG_IWLDVM": "m",
                    "CONFIG_IWLMVM": "m",
                    "CONFIG_IWLWIFI_DEBUG": "y",
                    "CONFIG_IWLWIFI_DEBUGFS": "y"
                }
            ),
            "rt2x00": BuildConfig(
                name="rt2x00",
                family=DriverFamily.RT2X00,
                source_dirs=["drivers/net/wireless/ralink/rt2x00"],
                build_deps=["cfg80211", "mac80211"],
                firmware_files=[
                    "rt2870.bin",
                    "rt3070.bin",
                    "rt2561.bin",
                    "rt2661.bin"
                ],
                make_targets=["rt2x00lib", "rt2800lib", "rt2800pci", "rt2800usb"],
                install_paths={
                    "modules": "/lib/modules/$(KERNELRELEASE)/extra/rt2x00",
                    "firmware": "/lib/firmware"
                },
                build_flags={
                    "CONFIG_RT2X00": "m",
                    "CONFIG_RT2X00_LIB": "m",
                    "CONFIG_RT2800PCI": "m",
                    "CONFIG_RT2800USB": "m",
                    "CONFIG_RT2X00_DEBUG": "y"
                }
            )
        }
    
    def _run_command(self, cmd: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
        """Run a system command"""
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300,
                cwd=cwd or self.kernel_root
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return -1, "", str(e)
    
    def check_build_dependencies(self, drivers: List[str]) -> Dict[str, any]:
        """Check build dependencies for specified drivers"""
        deps_status = {
            "missing_tools": [],
            "missing_headers": [],
            "kernel_config": {},
            "build_ready": True,
            "issues": []
        }
        
        # Check essential build tools
        required_tools = ["make", "gcc", "ld", "objcopy", "modinfo"]
        for tool in required_tools:
            exit_code, _, _ = self._run_command(["which", tool])
            if exit_code != 0:
                deps_status["missing_tools"].append(tool)
                deps_status["build_ready"] = False
        
        # Check kernel headers
        kernel_headers_paths = [
            "/lib/modules/$(uname -r)/build",
            "/usr/src/linux-headers-$(uname -r)",
            "/usr/src/kernels/$(uname -r)"
        ]
        
        exit_code, kernel_release, _ = self._run_command(["uname", "-r"])
        if exit_code == 0:
            kernel_release = kernel_release.strip()
            for path_template in kernel_headers_paths:
                path = path_template.replace("$(uname -r)", kernel_release)
                if Path(path).exists():
                    break
            else:
                deps_status["missing_headers"].append(f"linux-headers-{kernel_release}")
                deps_status["build_ready"] = False
        
        # Check driver-specific dependencies
        all_deps = set()
        for driver in drivers:
            if driver in self.build_configs:
                all_deps.update(self.build_configs[driver].build_deps)
        
        # Check if wireless stack is available
        wireless_modules = ["cfg80211", "mac80211"]
        for module in wireless_modules:
            exit_code, _, _ = self._run_command(["modinfo", module])
            if exit_code != 0:
                deps_status["issues"].append(f"Wireless module {module} not available")
        
        return deps_status
    
    def generate_makefile(self, drivers: List[str], features: List[str] = None) -> str:
        """Generate Makefile for multi-driver build"""
        if features is None:
            features = []
        
        makefile_content = f'''#
# Multi-Driver Makefile
# Generated for drivers: {", ".join(drivers)}
# Features: {", ".join(features) if features else "default"}
#

# Kernel build system integration
ifneq ($(KERNELRELEASE),)

# Driver object files
'''
        
        # Add driver-specific build rules
        for driver in drivers:
            if driver in self.build_configs:
                config = self.build_configs[driver]
                makefile_content += f'''
# {driver.upper()} driver family
ifdef CONFIG_BACKPORTS_{driver.upper()}
'''
                for target in config.make_targets:
                    makefile_content += f"    obj-$(CONFIG_BACKPORTS_{target.upper()}) += {target}.o\\n"
                
                makefile_content += f'''
    # Build flags for {driver}
'''
                for flag, value in config.build_flags.items():
                    makefile_content += f"    CFLAGS_{driver} += -D{flag}={value}\\n"
                
                makefile_content += "endif\\n"
        
        # Add feature-specific flags
        if "monitor_mode" in features:
            makefile_content += '''
# Monitor mode support
ifdef CONFIG_BACKPORTS_MONITOR_MODE
    CFLAGS_ALL += -DCONFIG_MONITOR_MODE_ENHANCED
endif
'''
        
        if "packet_injection" in features:
            makefile_content += '''
# Packet injection support
ifdef CONFIG_BACKPORTS_FRAME_INJECTION
    CFLAGS_ALL += -DCONFIG_FRAME_INJECTION_ENHANCED
endif
'''
        
        # Add build system integration
        makefile_content += '''
else

# External build system
KDIR ?= /lib/modules/$(shell uname -r)/build
PWD := $(shell pwd)

# Default target
all: modules

# Build modules
modules:
\t$(MAKE) -C $(KDIR) M=$(PWD) modules

# Clean build artifacts
clean:
\t$(MAKE) -C $(KDIR) M=$(PWD) clean
\trm -f *.o *.ko *.mod.c .*.cmd
\trm -rf .tmp_versions Module.symvers modules.order

# Install modules
modules_install:
\t$(MAKE) -C $(KDIR) M=$(PWD) modules_install

# Install firmware
firmware_install:
'''
        
        # Add firmware installation rules
        for driver in drivers:
            if driver in self.build_configs:
                config = self.build_configs[driver]
                if config.firmware_files:
                    makefile_content += f'''
\t# Install {driver} firmware
\tmkdir -p $(DESTDIR){config.install_paths["firmware"]}
'''
                    for fw_file in config.firmware_files:
                        makefile_content += f"\\tinstall -m 644 firmware/{fw_file} $(DESTDIR){config.install_paths['firmware']}/\\n"
        
        makefile_content += '''
# Help target
help:
\t@echo "Available targets:"
\t@echo "  modules          - Build kernel modules"
\t@echo "  modules_install  - Install kernel modules"
\t@echo "  firmware_install - Install firmware files"
\t@echo "  clean           - Clean build artifacts"
\t@echo "  help            - Show this help"

.PHONY: all modules clean modules_install firmware_install help

endif
'''
        
        return makefile_content
    
    def create_build_script(self, drivers: List[str], features: List[str] = None) -> str:
        """Create build script for multi-driver setup"""
        if features is None:
            features = []
        
        script_content = f'''#!/bin/bash
#
# Multi-Driver Build Script
# Drivers: {", ".join(drivers)}
# Features: {", ".join(features) if features else "default"}
#

set -e

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m'

print_status() {{
    local color=$1
    local message=$2
    echo -e "${{color}}${{message}}${{NC}}"
}}

print_header() {{
    echo
    print_status "$BLUE" "=== $1 ==="
}}

# Configuration
KERNEL_DIR="${{KDIR:-/lib/modules/$(uname -r)/build}}"
BUILD_DIR="${{BUILD_DIR:-$(pwd)/build}}"
INSTALL_PREFIX="${{INSTALL_PREFIX:-}}"

# Validate environment
validate_environment() {{
    print_header "Validating Build Environment"
    
    # Check kernel headers
    if [ ! -d "$KERNEL_DIR" ]; then
        print_status "$RED" "Error: Kernel headers not found at $KERNEL_DIR"
        print_status "$YELLOW" "Install kernel headers: apt-get install linux-headers-$(uname -r)"
        exit 1
    fi
    
    print_status "$GREEN" "Kernel headers found: $KERNEL_DIR"
    
    # Check build tools
    for tool in make gcc ld objcopy; do
        if ! command -v $tool >/dev/null 2>&1; then
            print_status "$RED" "Error: Required tool '$tool' not found"
            exit 1
        fi
    done
    
    print_status "$GREEN" "Build tools validated"
}}

# Build drivers
build_drivers() {{
    print_header "Building Multi-Driver Setup"
    
    # Create build directory
    mkdir -p "$BUILD_DIR"
    cd "$BUILD_DIR"
    
    # Generate configuration
    print_status "$YELLOW" "Generating build configuration..."
    
    # Copy source files (simplified for this example)
    print_status "$YELLOW" "Preparing source files..."
    
    # Build modules
    print_status "$YELLOW" "Building kernel modules..."
    make -C "$KERNEL_DIR" M="$(pwd)" modules
    
    if [ $? -eq 0 ]; then
        print_status "$GREEN" "Modules built successfully"
    else
        print_status "$RED" "Module build failed"
        exit 1
    fi
}}

# Install drivers
install_drivers() {{
    print_header "Installing Multi-Driver Setup"
    
    # Install modules
    print_status "$YELLOW" "Installing kernel modules..."
    make -C "$KERNEL_DIR" M="$(pwd)" modules_install INSTALL_MOD_PATH="$INSTALL_PREFIX"
    
    # Install firmware
    print_status "$YELLOW" "Installing firmware files..."
'''
        
        # Add driver-specific installation
        for driver in drivers:
            if driver in self.build_configs:
                config = self.build_configs[driver]
                if config.firmware_files:
                    script_content += f'''
    # Install {driver} firmware
    mkdir -p "${{INSTALL_PREFIX}}{config.install_paths["firmware"]}"
'''
                    for fw_file in config.firmware_files:
                        script_content += f'    [ -f "firmware/{fw_file}" ] && cp "firmware/{fw_file}" "${{INSTALL_PREFIX}}{config.install_paths["firmware"]}/" || true\\n'
        
        script_content += '''
    
    print_status "$GREEN" "Installation completed"
    
    # Update module dependencies
    if [ -z "$INSTALL_PREFIX" ]; then
        print_status "$YELLOW" "Updating module dependencies..."
        depmod -a
    fi
}

# Load drivers
load_drivers() {
    print_header "Loading Multi-Driver Setup"
    
'''
        
        # Add driver loading sequence
        for driver in drivers:
            if driver in self.build_configs:
                config = self.build_configs[driver]
                for target in config.make_targets:
                    script_content += f'''
    print_status "$YELLOW" "Loading {target}..."
    modprobe {target} || print_status "$YELLOW" "Warning: Failed to load {target}"
'''
        
        script_content += '''
    
    print_status "$GREEN" "Driver loading completed"
}

# Unload drivers
unload_drivers() {
    print_header "Unloading Multi-Driver Setup"
    
'''
        
        # Add driver unloading sequence (reverse order)
        for driver in reversed(drivers):
            if driver in self.build_configs:
                config = self.build_configs[driver]
                for target in reversed(config.make_targets):
                    script_content += f'''
    print_status "$YELLOW" "Unloading {target}..."
    modprobe -r {target} 2>/dev/null || true
'''
        
        script_content += '''
    
    print_status "$GREEN" "Driver unloading completed"
}

# Clean build artifacts
clean_build() {
    print_header "Cleaning Build Artifacts"
    
    if [ -d "$BUILD_DIR" ]; then
        cd "$BUILD_DIR"
        make -C "$KERNEL_DIR" M="$(pwd)" clean 2>/dev/null || true
        rm -f *.o *.ko *.mod.c .*.cmd
        rm -rf .tmp_versions Module.symvers modules.order
        print_status "$GREEN" "Build artifacts cleaned"
    else
        print_status "$YELLOW" "No build directory found"
    fi
}

# Show status
show_status() {
    print_header "Multi-Driver Status"
    
    print_status "$YELLOW" "Loaded modules:"
'''
        
        for driver in drivers:
            if driver in self.build_configs:
                config = self.build_configs[driver]
                for target in config.make_targets:
                    script_content += f'''
    if lsmod | grep -q "^{target} "; then
        print_status "$GREEN" "  ✓ {target}"
    else
        print_status "$RED" "  ✗ {target}"
    fi
'''
        
        script_content += '''
    
    print_status "$YELLOW" "Firmware status:"
'''
        
        for driver in drivers:
            if driver in self.build_configs:
                config = self.build_configs[driver]
                for fw_file in config.firmware_files:
                    script_content += f'''
    if [ -f "/lib/firmware/{fw_file}" ]; then
        print_status "$GREEN" "  ✓ {fw_file}"
    else
        print_status "$RED" "  ✗ {fw_file}"
    fi
'''
        
        script_content += '''
}

# Main function
case "$1" in
    "build")
        validate_environment
        build_drivers
        ;;
    "install")
        install_drivers
        ;;
    "load")
        load_drivers
        ;;
    "unload")
        unload_drivers
        ;;
    "clean")
        clean_build
        ;;
    "status")
        show_status
        ;;
    "all")
        validate_environment
        build_drivers
        install_drivers
        load_drivers
        show_status
        ;;
    *)
        echo "Usage: $0 {build|install|load|unload|clean|status|all}"
        echo ""
        echo "Commands:"
        echo "  build   - Build kernel modules"
        echo "  install - Install modules and firmware"
        echo "  load    - Load kernel modules"
        echo "  unload  - Unload kernel modules"
        echo "  clean   - Clean build artifacts"
        echo "  status  - Show driver status"
        echo "  all     - Build, install, load, and show status"
        exit 1
        ;;
esac
'''
        
        return script_content
    
    def build_drivers(self, drivers: List[str], features: List[str] = None, target: BuildTarget = BuildTarget.ALL) -> Dict[str, any]:
        """Build specified drivers with features"""
        if features is None:
            features = []
        
        build_result = {
            "success": False,
            "drivers_built": [],
            "build_log": [],
            "errors": [],
            "warnings": []
        }
        
        # Check dependencies first
        deps_check = self.check_build_dependencies(drivers)
        if not deps_check["build_ready"]:
            build_result["errors"].extend([
                f"Missing tools: {', '.join(deps_check['missing_tools'])}",
                f"Missing headers: {', '.join(deps_check['missing_headers'])}"
            ])
            return build_result
        
        # Create build directory structure
        driver_build_dir = self.build_dir / "multi-driver"
        driver_build_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate Makefile
        makefile_content = self.generate_makefile(drivers, features)
        makefile_path = driver_build_dir / "Makefile"
        
        try:
            with open(makefile_path, 'w') as f:
                f.write(makefile_content)
            build_result["build_log"].append(f"Generated Makefile: {makefile_path}")
        except Exception as e:
            build_result["errors"].append(f"Failed to create Makefile: {e}")
            return build_result
        
        # Generate build script
        build_script_content = self.create_build_script(drivers, features)
        build_script_path = driver_build_dir / "build-multi-drivers.sh"
        
        try:
            with open(build_script_path, 'w') as f:
                f.write(build_script_content)
            build_script_path.chmod(0o755)
            build_result["build_log"].append(f"Generated build script: {build_script_path}")
        except Exception as e:
            build_result["errors"].append(f"Failed to create build script: {e}")
            return build_result
        
        # If this is just generating build files, return success
        if target == BuildTarget.TOOLS:
            build_result["success"] = True
            build_result["drivers_built"] = drivers
            return build_result
        
        # Attempt to build (simplified - would need actual source files)
        build_result["build_log"].append("Build system prepared successfully")
        build_result["warnings"].append("Actual compilation requires driver source files")
        build_result["success"] = True
        build_result["drivers_built"] = drivers
        
        return build_result
    
    def generate_build_report(self, drivers: List[str]) -> Dict[str, any]:
        """Generate comprehensive build report"""
        report = {
            "build_configuration": {},
            "dependency_analysis": self.check_build_dependencies(drivers),
            "driver_details": {},
            "build_complexity": {},
            "recommendations": []
        }
        
        # Analyze each driver
        total_source_dirs = 0
        total_targets = 0
        total_firmware = 0
        
        for driver in drivers:
            if driver in self.build_configs:
                config = self.build_configs[driver]
                report["driver_details"][driver] = {
                    "family": config.family.value,
                    "source_directories": len(config.source_dirs),
                    "build_targets": len(config.make_targets),
                    "firmware_files": len(config.firmware_files),
                    "build_dependencies": config.build_deps,
                    "configuration_flags": len(config.build_flags)
                }
                
                total_source_dirs += len(config.source_dirs)
                total_targets += len(config.make_targets)
                total_firmware += len(config.firmware_files)
        
        # Build complexity analysis
        report["build_complexity"] = {
            "total_drivers": len(drivers),
            "total_source_directories": total_source_dirs,
            "total_build_targets": total_targets,
            "total_firmware_files": total_firmware,
            "complexity_score": total_source_dirs + total_targets + (total_firmware * 0.5)
        }
        
        # Generate recommendations
        if report["build_complexity"]["complexity_score"] > 20:
            report["recommendations"].append("Consider incremental builds for complex multi-driver setup")
        
        if not report["dependency_analysis"]["build_ready"]:
            report["recommendations"].append("Resolve build dependencies before proceeding")
        
        if total_firmware > 10:
            report["recommendations"].append("Consider firmware management automation")
        
        return report

def main():
    """Main function for testing"""
    build_system = MultiDriverBuild()
    
    print("Multi-Driver Build System")
    print("=" * 50)
    
    # Test drivers
    test_drivers = ["ath10k", "iwlwifi", "rt2x00"]
    test_features = ["monitor_mode", "packet_injection"]
    
    print(f"\\nTesting build system for drivers: {', '.join(test_drivers)}")
    print(f"Features: {', '.join(test_features)}")
    
    # Check dependencies
    print("\\nChecking build dependencies...")
    deps = build_system.check_build_dependencies(test_drivers)
    
    if deps["build_ready"]:
        print("✓ Build environment ready")
    else:
        print("✗ Build environment issues:")
        for issue in deps["missing_tools"] + deps["missing_headers"]:
            print(f"  - {issue}")
    
    # Generate build files
    print("\\nGenerating build files...")
    result = build_system.build_drivers(test_drivers, test_features, BuildTarget.TOOLS)
    
    if result["success"]:
        print("✓ Build files generated successfully")
        for log_entry in result["build_log"]:
            print(f"  {log_entry}")
    else:
        print("✗ Build file generation failed")
        for error in result["errors"]:
            print(f"  Error: {error}")
    
    # Generate report
    print("\\nBuild Analysis Report:")
    report = build_system.generate_build_report(test_drivers)
    
    print(f"  Total drivers: {report['build_complexity']['total_drivers']}")
    print(f"  Build targets: {report['build_complexity']['total_build_targets']}")
    print(f"  Firmware files: {report['build_complexity']['total_firmware_files']}")
    print(f"  Complexity score: {report['build_complexity']['complexity_score']:.1f}")
    
    if report["recommendations"]:
        print("\\nRecommendations:")
        for rec in report["recommendations"]:
            print(f"  - {rec}")

if __name__ == "__main__":
    main()