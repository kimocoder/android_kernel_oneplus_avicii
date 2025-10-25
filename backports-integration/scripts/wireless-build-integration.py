#!/usr/bin/env python3
"""
Wireless Build Integration Script

This script provides advanced build integration for wireless drivers including
conditional compilation, dependency management, and build optimization.
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class WirelessBuildIntegration:
    """Wireless driver build integration manager"""
    
    def __init__(self, kernel_root: str = "."):
        """Initialize build integration"""
        self.kernel_root = Path(kernel_root).resolve()
        self.backports_dir = self.kernel_root / "backports-integration"
        self.build_config = self._load_build_config()
        
    def _load_build_config(self) -> Dict:
        """Load build configuration"""
        config_file = self.backports_dir / "configs" / "build.json"
        
        default_config = {
            "wireless_drivers": {
                "ath11k": {
                    "enabled": False,
                    "chipsets": ["QCA6390", "QCA6490", "WCN6855", "QCN9074"],
                    "dependencies": ["cfg80211", "mac80211", "crypto"],
                    "firmware_required": True,
                    "build_flags": ["-DCONFIG_ATH11K_DEBUG"],
                    "source_dir": "drivers/net/wireless/ath/ath11k"
                },
                "ath10k": {
                    "enabled": False,
                    "chipsets": ["QCA988X", "QCA6174", "QCA9377", "QCA4019"],
                    "dependencies": ["cfg80211", "mac80211", "crypto"],
                    "firmware_required": True,
                    "build_flags": ["-DCONFIG_ATH10K_DEBUG"],
                    "source_dir": "drivers/net/wireless/ath/ath10k"
                },
                "iwlwifi": {
                    "enabled": False,
                    "chipsets": ["AX200", "AX210", "9260", "8260"],
                    "dependencies": ["cfg80211", "mac80211"],
                    "firmware_required": True,
                    "build_flags": ["-DCONFIG_IWLWIFI_DEBUG"],
                    "source_dir": "drivers/net/wireless/intel/iwlwifi"
                },
                "rt2x00": {
                    "enabled": False,
                    "chipsets": ["RT3070", "RT2800", "RT5370"],
                    "dependencies": ["cfg80211", "mac80211"],
                    "firmware_required": True,
                    "build_flags": ["-DCONFIG_RT2X00_DEBUG"],
                    "source_dir": "drivers/net/wireless/ralink/rt2x00"
                }
            },
            "build_options": {
                "parallel_jobs": 0,  # 0 = auto-detect
                "verbose": False,
                "debug": False,
                "optimization": "O2",
                "warnings_as_errors": False
            },
            "firmware_options": {
                "auto_download": False,
                "validate_checksums": True,
                "install_optional": False
            }
        }
        
        try:
            if config_file.exists():
                with open(config_file, 'r') as f:
                    loaded_config = json.load(f)
                # Merge with defaults
                default_config.update(loaded_config)
        except Exception as e:
            print(f"Warning: Could not load build config: {e}")
        
        return default_config
    
    def detect_kconfig_settings(self) -> Dict[str, bool]:
        """Detect Kconfig settings from environment or .config"""
        settings = {}
        
        # Check environment variables first
        env_configs = [
            "CONFIG_BACKPORTS",
            "CONFIG_BACKPORTS_WIRELESS_DRIVERS",
            "CONFIG_BACKPORTS_ATH11K",
            "CONFIG_BACKPORTS_ATH10K",
            "CONFIG_BACKPORTS_ATH9K",
            "CONFIG_BACKPORTS_IWLWIFI",
            "CONFIG_BACKPORTS_RT2X00",
            "CONFIG_BACKPORTS_CFG80211",
            "CONFIG_BACKPORTS_MAC80211",
            "CONFIG_BACKPORTS_MONITOR_MODE",
            "CONFIG_BACKPORTS_FRAME_INJECTION"
        ]
        
        for config in env_configs:
            value = os.environ.get(config, "n")
            settings[config] = value.lower() in ["y", "yes", "1", "true"]
        
        # Try to read from .config file if available
        config_file = self.kernel_root / ".config"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("CONFIG_BACKPORTS"):
                            if "=y" in line:
                                config_name = line.split("=")[0]
                                settings[config_name] = True
                            elif "=n" in line or "is not set" in line:
                                config_name = line.split("=")[0] if "=" in line else line.split()[1]
                                settings[config_name] = False
            except Exception as e:
                print(f"Warning: Could not read .config: {e}")
        
        return settings
    
    def generate_build_flags(self, driver: str, kconfig: Dict[str, bool]) -> List[str]:
        """Generate build flags for a specific driver"""
        flags = []
        
        # Base flags
        build_opts = self.build_config["build_options"]
        
        if build_opts["debug"] or kconfig.get("CONFIG_BACKPORTS_DEBUG", False):
            flags.extend(["-DDEBUG", "-g"])
        
        flags.append(f"-{build_opts['optimization']}")
        
        if build_opts["warnings_as_errors"]:
            flags.append("-Werror")
        
        # Driver-specific flags
        driver_config = self.build_config["wireless_drivers"].get(driver, {})
        flags.extend(driver_config.get("build_flags", []))
        
        # Feature-specific flags
        if kconfig.get("CONFIG_BACKPORTS_MONITOR_MODE", False):
            flags.append("-DCONFIG_BACKPORTS_MONITOR_MODE")
        
        if kconfig.get("CONFIG_BACKPORTS_FRAME_INJECTION", False):
            flags.append("-DCONFIG_BACKPORTS_FRAME_INJECTION")
        
        if kconfig.get("CONFIG_BACKPORTS_SECURITY_ENHANCED", False):
            flags.append("-DCONFIG_BACKPORTS_SECURITY_ENHANCED")
        
        return flags
    
    def check_dependencies(self, driver: str, kconfig: Dict[str, bool]) -> Dict[str, any]:
        """Check dependencies for a driver"""
        result = {
            "satisfied": True,
            "missing": [],
            "warnings": []
        }
        
        driver_config = self.build_config["wireless_drivers"].get(driver, {})
        dependencies = driver_config.get("dependencies", [])
        
        # Check Kconfig dependencies
        dependency_map = {
            "cfg80211": "CONFIG_BACKPORTS_CFG80211",
            "mac80211": "CONFIG_BACKPORTS_MAC80211",
            "crypto": "CONFIG_CRYPTO"
        }
        
        for dep in dependencies:
            kconfig_name = dependency_map.get(dep, f"CONFIG_{dep.upper()}")
            if not kconfig.get(kconfig_name, False):
                result["missing"].append(dep)
                result["satisfied"] = False
        
        # Check source directory
        source_dir = driver_config.get("source_dir", "")
        if source_dir:
            full_source_path = self.kernel_root / "backports-generated-6.1" / source_dir
            if not full_source_path.exists():
                result["warnings"].append(f"Source directory not found: {full_source_path}")
        
        return result
    
    def generate_makefile_rules(self, enabled_drivers: List[str], kconfig: Dict[str, bool]) -> str:
        """Generate Makefile rules for enabled drivers"""
        rules = []
        
        rules.append("# Auto-generated wireless driver build rules")
        rules.append("# Generated by wireless-build-integration.py")
        rules.append("")
        
        # Add conditional compilation rules
        for driver in enabled_drivers:
            driver_config = self.build_config["wireless_drivers"].get(driver, {})
            source_dir = driver_config.get("source_dir", "")
            
            if source_dir:
                config_var = f"CONFIG_BACKPORTS_{driver.upper()}"
                rules.append(f"# {driver} driver build rules")
                rules.append(f"ifdef {config_var}")
                rules.append(f"obj-$({config_var}) += {source_dir}/")
                
                # Add build flags
                build_flags = self.generate_build_flags(driver, kconfig)
                if build_flags:
                    flags_str = " ".join(build_flags)
                    rules.append(f"EXTRA_CFLAGS += {flags_str}")
                
                rules.append("endif")
                rules.append("")
        
        # Add firmware rules
        if any(self.build_config["wireless_drivers"][d].get("firmware_required", False) 
               for d in enabled_drivers):
            rules.append("# Firmware installation rules")
            rules.append("firmware-install:")
            
            for driver in enabled_drivers:
                driver_config = self.build_config["wireless_drivers"].get(driver, {})
                if driver_config.get("firmware_required", False):
                    rules.append(f"\t@echo 'Installing {driver} firmware...'")
                    rules.append(f"\t$(Q)$(MAKE) -f $(src)/backports-integration/Makefile firmware_install_{driver}")
            
            rules.append("")
        
        return "\n".join(rules)
    
    def create_build_script(self, output_file: str) -> bool:
        """Create a comprehensive build script"""
        kconfig = self.detect_kconfig_settings()
        
        # Determine enabled drivers
        enabled_drivers = []
        for driver in self.build_config["wireless_drivers"]:
            config_var = f"CONFIG_BACKPORTS_{driver.upper()}"
            if kconfig.get(config_var, False):
                enabled_drivers.append(driver)
        
        script_content = f"""#!/bin/bash
#
# Auto-generated Wireless Driver Build Script
# Generated by wireless-build-integration.py at {time.ctime()}
#

set -e

# Build configuration
KERNEL_ROOT="{self.kernel_root}"
BACKPORTS_DIR="$KERNEL_ROOT/backports-generated-6.1"
PARALLEL_JOBS={self.build_config['build_options'].get('parallel_jobs', 0)}

# Auto-detect parallel jobs if not specified
if [ "$PARALLEL_JOBS" -eq 0 ]; then
    PARALLEL_JOBS=$(nproc)
fi

echo "Wireless Driver Build Script"
echo "============================"
echo "Kernel root: $KERNEL_ROOT"
echo "Backports dir: $BACKPORTS_DIR"
echo "Parallel jobs: $PARALLEL_JOBS"
echo "Enabled drivers: {' '.join(enabled_drivers)}"
echo ""

# Check prerequisites
if [ ! -d "$BACKPORTS_DIR" ]; then
    echo "ERROR: Backports directory not found: $BACKPORTS_DIR"
    exit 1
fi

# Build enabled drivers
"""

        for driver in enabled_drivers:
            driver_config = self.build_config["wireless_drivers"][driver]
            source_dir = driver_config.get("source_dir", "")
            build_flags = self.generate_build_flags(driver, kconfig)
            
            script_content += f"""
# Build {driver} driver
echo "Building {driver} driver..."
if [ -d "$BACKPORTS_DIR/{source_dir}" ]; then
    make -C "$BACKPORTS_DIR" \\
        M="{source_dir}" \\
        EXTRA_CFLAGS="{' '.join(build_flags)}" \\
        -j$PARALLEL_JOBS \\
        modules || {{
        echo "ERROR: {driver} build failed"
        exit 1
    }}
    echo "{driver} build completed successfully"
else
    echo "WARNING: {driver} source directory not found: $BACKPORTS_DIR/{source_dir}"
fi
"""

        script_content += """
echo ""
echo "All wireless drivers built successfully!"
echo "Use 'make wireless_install' to install the drivers"
"""

        try:
            with open(output_file, 'w') as f:
                f.write(script_content)
            
            # Make script executable
            os.chmod(output_file, 0o755)
            return True
        except Exception as e:
            print(f"Error creating build script: {e}")
            return False
    
    def validate_build_environment(self) -> Dict[str, any]:
        """Validate build environment"""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "info": []
        }
        
        # Check kernel source
        if not self.kernel_root.exists():
            validation["errors"].append(f"Kernel root not found: {self.kernel_root}")
            validation["valid"] = False
        
        # Check backports directory
        backports_generated = self.kernel_root / "backports-generated-6.1"
        if not backports_generated.exists():
            validation["errors"].append(f"Backports directory not found: {backports_generated}")
            validation["valid"] = False
        
        # Check build tools
        required_tools = ["make", "gcc", "ld"]
        for tool in required_tools:
            try:
                subprocess.run([tool, "--version"], capture_output=True, check=True)
                validation["info"].append(f"{tool}: available")
            except (subprocess.CalledProcessError, FileNotFoundError):
                validation["errors"].append(f"Required build tool not found: {tool}")
                validation["valid"] = False
        
        # Check Kconfig settings
        kconfig = self.detect_kconfig_settings()
        if not kconfig.get("CONFIG_BACKPORTS", False):
            validation["warnings"].append("CONFIG_BACKPORTS not enabled")
        
        # Check enabled drivers
        enabled_drivers = []
        for driver in self.build_config["wireless_drivers"]:
            config_var = f"CONFIG_BACKPORTS_{driver.upper()}"
            if kconfig.get(config_var, False):
                enabled_drivers.append(driver)
                
                # Check dependencies
                deps = self.check_dependencies(driver, kconfig)
                if not deps["satisfied"]:
                    validation["errors"].append(f"{driver}: missing dependencies: {deps['missing']}")
                    validation["valid"] = False
                
                validation["warnings"].extend(deps["warnings"])
        
        if enabled_drivers:
            validation["info"].append(f"Enabled drivers: {', '.join(enabled_drivers)}")
        else:
            validation["warnings"].append("No wireless drivers enabled")
        
        return validation
    
    def generate_build_report(self, output_file: Optional[str] = None) -> str:
        """Generate comprehensive build report"""
        kconfig = self.detect_kconfig_settings()
        validation = self.validate_build_environment()
        
        report_lines = []
        report_lines.append("Wireless Build Integration Report")
        report_lines.append("=" * 50)
        report_lines.append(f"Generated: {time.ctime()}")
        report_lines.append("")
        
        # Configuration summary
        report_lines.append("Configuration Summary:")
        report_lines.append(f"  Kernel Root: {self.kernel_root}")
        report_lines.append(f"  Backports Dir: {self.kernel_root}/backports-generated-6.1")
        report_lines.append("")
        
        # Kconfig settings
        report_lines.append("Kconfig Settings:")
        for config, enabled in sorted(kconfig.items()):
            status = "ENABLED" if enabled else "DISABLED"
            report_lines.append(f"  {config}: {status}")
        report_lines.append("")
        
        # Enabled drivers
        enabled_drivers = []
        for driver in self.build_config["wireless_drivers"]:
            config_var = f"CONFIG_BACKPORTS_{driver.upper()}"
            if kconfig.get(config_var, False):
                enabled_drivers.append(driver)
        
        report_lines.append("Enabled Wireless Drivers:")
        if enabled_drivers:
            for driver in enabled_drivers:
                driver_config = self.build_config["wireless_drivers"][driver]
                chipsets = ", ".join(driver_config.get("chipsets", []))
                report_lines.append(f"  - {driver}: {chipsets}")
        else:
            report_lines.append("  None")
        report_lines.append("")
        
        # Build validation
        report_lines.append("Build Environment Validation:")
        if validation["valid"]:
            report_lines.append("  Status: ✅ VALID")
        else:
            report_lines.append("  Status: ❌ INVALID")
        
        if validation["errors"]:
            report_lines.append("  Errors:")
            for error in validation["errors"]:
                report_lines.append(f"    - {error}")
        
        if validation["warnings"]:
            report_lines.append("  Warnings:")
            for warning in validation["warnings"]:
                report_lines.append(f"    - {warning}")
        
        if validation["info"]:
            report_lines.append("  Information:")
            for info in validation["info"]:
                report_lines.append(f"    - {info}")
        
        report_lines.append("")
        
        # Build recommendations
        report_lines.append("Build Recommendations:")
        if not validation["valid"]:
            report_lines.append("  - Fix validation errors before building")
        
        if enabled_drivers:
            report_lines.append("  - Run 'make wireless_drivers' to build enabled drivers")
            report_lines.append("  - Run 'make firmware_install' to install firmware")
            report_lines.append("  - Run 'make wireless_install' for complete installation")
        else:
            report_lines.append("  - Enable wireless drivers in Kconfig")
            report_lines.append("  - Run 'make menuconfig' to configure drivers")
        
        report_content = "\n".join(report_lines)
        
        # Save to file if requested
        if output_file:
            try:
                with open(output_file, 'w') as f:
                    f.write(report_content)
                print(f"Build report saved to: {output_file}")
            except Exception as e:
                print(f"Error saving report: {e}")
        
        return report_content

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Wireless Build Integration")
    parser.add_argument("--validate", action="store_true", help="Validate build environment")
    parser.add_argument("--report", "-r", help="Generate build report")
    parser.add_argument("--script", "-s", help="Generate build script")
    parser.add_argument("--makefile", "-m", help="Generate Makefile rules")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    integration = WirelessBuildIntegration()
    
    if args.validate:
        validation = integration.validate_build_environment()
        
        if validation["valid"]:
            print("✅ Build environment validation passed")
        else:
            print("❌ Build environment validation failed")
            
            if validation["errors"]:
                print("Errors:")
                for error in validation["errors"]:
                    print(f"  - {error}")
        
        if validation["warnings"]:
            print("Warnings:")
            for warning in validation["warnings"]:
                print(f"  - {warning}")
    
    elif args.report:
        report = integration.generate_build_report(args.report)
        if not args.report:
            print(report)
    
    elif args.script:
        success = integration.create_build_script(args.script)
        if success:
            print(f"✅ Build script created: {args.script}")
        else:
            print("❌ Failed to create build script")
    
    elif args.makefile:
        kconfig = integration.detect_kconfig_settings()
        enabled_drivers = []
        
        for driver in integration.build_config["wireless_drivers"]:
            config_var = f"CONFIG_BACKPORTS_{driver.upper()}"
            if kconfig.get(config_var, False):
                enabled_drivers.append(driver)
        
        makefile_rules = integration.generate_makefile_rules(enabled_drivers, kconfig)
        
        try:
            with open(args.makefile, 'w') as f:
                f.write(makefile_rules)
            print(f"✅ Makefile rules generated: {args.makefile}")
        except Exception as e:
            print(f"❌ Failed to generate Makefile rules: {e}")
    
    else:
        # Default: show status
        kconfig = integration.detect_kconfig_settings()
        validation = integration.validate_build_environment()
        
        print("Wireless Build Integration Status")
        print("=" * 40)
        
        enabled_count = sum(1 for k, v in kconfig.items() 
                          if k.startswith("CONFIG_BACKPORTS_") and v)
        print(f"Enabled configs: {enabled_count}")
        
        if validation["valid"]:
            print("Build environment: ✅ Valid")
        else:
            print("Build environment: ❌ Invalid")
            print(f"Errors: {len(validation['errors'])}")
        
        print(f"Warnings: {len(validation['warnings'])}")

if __name__ == "__main__":
    main()