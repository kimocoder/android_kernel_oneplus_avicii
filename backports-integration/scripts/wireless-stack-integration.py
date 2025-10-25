#!/usr/bin/env python3
"""
Wireless Stack Integration Manager

This module provides comprehensive integration for the wireless networking stack
including mac80211, cfg80211, nl80211, and wireless extensions compatibility.
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum

class StackComponent(Enum):
    """Wireless stack components"""
    CFG80211 = "cfg80211"
    MAC80211 = "mac80211"
    NL80211 = "nl80211"
    WIRELESS_EXT = "wireless_ext"
    REGULATORY = "regulatory"

@dataclass
class ModuleInfo:
    """Information about a kernel module"""
    name: str
    description: str
    dependencies: List[str]
    config_option: str
    load_order: int
    required: bool = True

class WirelessStackIntegration:
    """Manager for wireless stack integration"""
    
    def __init__(self, kernel_root: str = "."):
        """Initialize wireless stack integration"""
        self.kernel_root = Path(kernel_root).resolve()
        self.backports_dir = self.kernel_root / "backports-integration"
        
        # Define wireless stack modules with proper loading order
        self.stack_modules = {
            StackComponent.CFG80211: ModuleInfo(
                name="cfg80211",
                description="Wireless configuration API",
                dependencies=["rfkill", "crypto"],
                config_option="CONFIG_BACKPORTS_CFG80211",
                load_order=1
            ),
            StackComponent.MAC80211: ModuleInfo(
                name="mac80211",
                description="IEEE 802.11 networking stack",
                dependencies=["cfg80211", "crypto_aes", "crypto_arc4"],
                config_option="CONFIG_BACKPORTS_MAC80211",
                load_order=2
            ),
            StackComponent.NL80211: ModuleInfo(
                name="nl80211",
                description="Netlink interface for wireless configuration",
                dependencies=["cfg80211", "genetlink"],
                config_option="CONFIG_BACKPORTS_NL80211",
                load_order=3,
                required=False
            ),
            StackComponent.WIRELESS_EXT: ModuleInfo(
                name="wext",
                description="Wireless extensions compatibility",
                dependencies=["cfg80211"],
                config_option="CONFIG_BACKPORTS_WIRELESS_EXT",
                load_order=4,
                required=False
            ),
            StackComponent.REGULATORY: ModuleInfo(
                name="regulatory",
                description="Wireless regulatory framework",
                dependencies=["cfg80211"],
                config_option="CONFIG_BACKPORTS_WIRELESS_REGULATORY",
                load_order=5
            )
        }
        
        # Configuration templates for different use cases
        self.stack_configurations = {
            "basic": {
                "name": "Basic Wireless Stack",
                "description": "Minimal wireless stack configuration",
                "components": [StackComponent.CFG80211, StackComponent.MAC80211],
                "features": ["basic_wireless"]
            },
            "full": {
                "name": "Full Wireless Stack",
                "description": "Complete wireless stack with all features",
                "components": [
                    StackComponent.CFG80211, 
                    StackComponent.MAC80211,
                    StackComponent.NL80211,
                    StackComponent.REGULATORY
                ],
                "features": ["basic_wireless", "nl80211", "regulatory"]
            },
            "legacy": {
                "name": "Legacy Compatible Stack",
                "description": "Wireless stack with legacy wireless extensions",
                "components": [
                    StackComponent.CFG80211,
                    StackComponent.MAC80211,
                    StackComponent.WIRELESS_EXT
                ],
                "features": ["basic_wireless", "wireless_ext"]
            },
            "monitor": {
                "name": "Monitor Mode Stack",
                "description": "Wireless stack optimized for monitoring",
                "components": [
                    StackComponent.CFG80211,
                    StackComponent.MAC80211,
                    StackComponent.NL80211
                ],
                "features": ["basic_wireless", "monitor_mode", "packet_injection"]
            }
        }
    
    def _run_command(self, cmd: List[str]) -> Tuple[int, str, str]:
        """Run a system command"""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return -1, "", str(e)
    
    def check_stack_status(self) -> Dict[str, Dict[str, any]]:
        """Check the status of wireless stack components"""
        status = {}
        
        for component, module_info in self.stack_modules.items():
            status[component.value] = {
                "module_name": module_info.name,
                "loaded": False,
                "config_enabled": False,
                "dependencies_met": True,
                "missing_dependencies": []
            }
            
            # Check if module is loaded
            exit_code, stdout, stderr = self._run_command(["lsmod"])
            if exit_code == 0:
                status[component.value]["loaded"] = module_info.name in stdout
            
            # Check dependencies
            for dep in module_info.dependencies:
                if dep not in stdout:
                    status[component.value]["dependencies_met"] = False
                    status[component.value]["missing_dependencies"].append(dep)
        
        return status
    
    def generate_module_loading_script(self, components: List[StackComponent]) -> str:
        """Generate script for proper module loading order"""
        script_lines = [
            "#!/bin/bash",
            "#",
            "# Wireless Stack Module Loading Script",
            "# Generated automatically - loads modules in proper order",
            "#",
            "",
            "set -e",
            "",
            "# Function to load module with error checking",
            "load_module() {",
            "    local module=$1",
            "    local description=$2",
            "    ",
            "    echo \"Loading $module ($description)...\"",
            "    if lsmod | grep -q \"^$module \"; then",
            "        echo \"  $module already loaded\"",
            "    else",
            "        if modprobe $module; then",
            "            echo \"  $module loaded successfully\"",
            "        else",
            "            echo \"  ERROR: Failed to load $module\"",
            "            return 1",
            "        fi",
            "    fi",
            "}",
            "",
            "# Load modules in proper order"
        ]
        
        # Sort components by load order
        sorted_components = sorted(components, key=lambda c: self.stack_modules[c].load_order)
        
        for component in sorted_components:
            module_info = self.stack_modules[component]
            script_lines.append(f"load_module {module_info.name} \"{module_info.description}\"")
        
        script_lines.extend([
            "",
            "echo \"Wireless stack loaded successfully!\"",
            "",
            "# Verify stack is working",
            "if command -v iw >/dev/null 2>&1; then",
            "    echo \"Checking wireless interfaces...\"",
            "    iw dev || true",
            "fi"
        ])
        
        return "\n".join(script_lines)
    
    def create_cfg80211_integration(self) -> Dict[str, str]:
        """Create cfg80211 configuration and integration"""
        config = {
            "CONFIG_BACKPORTS_CFG80211": "m",
            "CONFIG_BACKPORTS_CFG80211_DEBUGFS": "y",
            "CONFIG_BACKPORTS_CFG80211_WEXT": "y",
            "CONFIG_BACKPORTS_CFG80211_CRDA_SUPPORT": "y",
            "CONFIG_BACKPORTS_CFG80211_CERTIFICATION_ONUS": "n",
            "CONFIG_BACKPORTS_CFG80211_REG_CELLULAR_HINTS": "y",
            "CONFIG_BACKPORTS_CFG80211_REG_RELAX_NO_IR": "n"
        }
        
        return config
    
    def create_mac80211_integration(self) -> Dict[str, str]:
        """Create mac80211 configuration and integration"""
        config = {
            "CONFIG_BACKPORTS_MAC80211": "m",
            "CONFIG_BACKPORTS_MAC80211_HAS_RC": "y",
            "CONFIG_BACKPORTS_MAC80211_RC_MINSTREL": "y",
            "CONFIG_BACKPORTS_MAC80211_RC_DEFAULT_MINSTREL": "y",
            "CONFIG_BACKPORTS_MAC80211_RC_DEFAULT": "minstrel_ht",
            "CONFIG_BACKPORTS_MAC80211_MESH": "y",
            "CONFIG_BACKPORTS_MAC80211_LEDS": "y",
            "CONFIG_BACKPORTS_MAC80211_DEBUGFS": "y",
            "CONFIG_BACKPORTS_MAC80211_MESSAGE_TRACING": "y",
            "CONFIG_BACKPORTS_MAC80211_DEBUG_MENU": "y",
            "CONFIG_BACKPORTS_MAC80211_NOINLINE": "n",
            "CONFIG_BACKPORTS_MAC80211_VERBOSE_DEBUG": "n",
            "CONFIG_BACKPORTS_MAC80211_MLME_DEBUG": "n",
            "CONFIG_BACKPORTS_MAC80211_STA_DEBUG": "n",
            "CONFIG_BACKPORTS_MAC80211_HT_DEBUG": "n",
            "CONFIG_BACKPORTS_MAC80211_OCB_DEBUG": "n",
            "CONFIG_BACKPORTS_MAC80211_IBSS_DEBUG": "n",
            "CONFIG_BACKPORTS_MAC80211_PS_DEBUG": "n",
            "CONFIG_BACKPORTS_MAC80211_MPL_DEBUG": "n",
            "CONFIG_BACKPORTS_MAC80211_MPATH_DEBUG": "n",
            "CONFIG_BACKPORTS_MAC80211_MHWMP_DEBUG": "n",
            "CONFIG_BACKPORTS_MAC80211_MESH_SYNC_DEBUG": "n",
            "CONFIG_BACKPORTS_MAC80211_MESH_CSA_DEBUG": "n",
            "CONFIG_BACKPORTS_MAC80211_MESH_PS_DEBUG": "n",
            "CONFIG_BACKPORTS_MAC80211_TDLS_DEBUG": "n"
        }
        
        return config
    
    def create_nl80211_integration(self) -> Dict[str, str]:
        """Create nl80211 netlink interface integration"""
        config = {
            "CONFIG_BACKPORTS_NL80211_TESTMODE": "y",
            "CONFIG_BACKPORTS_CFG80211_DEVELOPER_WARNINGS": "n",
            "CONFIG_BACKPORTS_CFG80211_DEFAULT_PS": "y",
            "CONFIG_BACKPORTS_CFG80211_DEBUGFS": "y"
        }
        
        return config
    
    def create_wireless_ext_compatibility(self) -> Dict[str, str]:
        """Create wireless extensions compatibility layer"""
        config = {
            "CONFIG_BACKPORTS_WIRELESS_EXT": "y",
            "CONFIG_BACKPORTS_WEXT_CORE": "y",
            "CONFIG_BACKPORTS_WEXT_PROC": "y",
            "CONFIG_BACKPORTS_WEXT_SPY": "y",
            "CONFIG_BACKPORTS_WEXT_PRIV": "y",
            "CONFIG_BACKPORTS_CFG80211_WEXT": "y"
        }
        
        return config
    
    def create_regulatory_integration(self) -> Dict[str, str]:
        """Create regulatory framework integration"""
        config = {
            "CONFIG_BACKPORTS_WIRELESS_REGULATORY": "y",
            "CONFIG_BACKPORTS_CFG80211_CRDA_SUPPORT": "y",
            "CONFIG_BACKPORTS_CFG80211_REG_CELLULAR_HINTS": "y",
            "CONFIG_BACKPORTS_CFG80211_REG_RELAX_NO_IR": "n"
        }
        
        return config
    
    def generate_stack_configuration(self, config_name: str) -> Dict[str, str]:
        """Generate complete stack configuration"""
        if config_name not in self.stack_configurations:
            raise ValueError(f"Unknown configuration: {config_name}")
        
        stack_config = self.stack_configurations[config_name]
        config = {}
        
        # Add base configuration
        config["CONFIG_BACKPORTS"] = "y"
        config["CONFIG_BACKPORTS_WIRELESS_DRIVERS"] = "y"
        
        # Add component-specific configurations
        for component in stack_config["components"]:
            if component == StackComponent.CFG80211:
                config.update(self.create_cfg80211_integration())
            elif component == StackComponent.MAC80211:
                config.update(self.create_mac80211_integration())
            elif component == StackComponent.NL80211:
                config.update(self.create_nl80211_integration())
            elif component == StackComponent.WIRELESS_EXT:
                config.update(self.create_wireless_ext_compatibility())
            elif component == StackComponent.REGULATORY:
                config.update(self.create_regulatory_integration())
        
        # Add feature-specific configurations
        features = stack_config["features"]
        if "monitor_mode" in features:
            config["CONFIG_BACKPORTS_MONITOR_MODE"] = "y"
            config["CONFIG_BACKPORTS_WIRELESS_MONITOR_ENHANCED"] = "y"
        
        if "packet_injection" in features:
            config["CONFIG_BACKPORTS_FRAME_INJECTION"] = "y"
            config["CONFIG_BACKPORTS_WIRELESS_INJECTION_ENHANCED"] = "y"
        
        return config
    
    def create_module_loading_order_file(self, components: List[StackComponent]) -> str:
        """Create module loading order configuration file"""
        order_config = {
            "wireless_stack_loading_order": {
                "description": "Proper loading order for wireless stack modules",
                "modules": []
            }
        }
        
        # Sort by load order
        sorted_components = sorted(components, key=lambda c: self.stack_modules[c].load_order)
        
        for component in sorted_components:
            module_info = self.stack_modules[component]
            order_config["wireless_stack_loading_order"]["modules"].append({
                "name": module_info.name,
                "description": module_info.description,
                "dependencies": module_info.dependencies,
                "config_option": module_info.config_option,
                "load_order": module_info.load_order,
                "required": module_info.required
            })
        
        return json.dumps(order_config, indent=2)
    
    def validate_stack_integration(self) -> Dict[str, any]:
        """Validate wireless stack integration"""
        validation = {
            "stack_status": self.check_stack_status(),
            "configuration_valid": True,
            "issues": [],
            "recommendations": []
        }
        
        # Check for common issues
        stack_status = validation["stack_status"]
        
        # Check if cfg80211 is loaded before mac80211
        cfg80211_loaded = stack_status.get("cfg80211", {}).get("loaded", False)
        mac80211_loaded = stack_status.get("mac80211", {}).get("loaded", False)
        
        if mac80211_loaded and not cfg80211_loaded:
            validation["issues"].append("mac80211 loaded without cfg80211")
            validation["configuration_valid"] = False
        
        # Check dependencies
        for component, status in stack_status.items():
            if not status["dependencies_met"]:
                validation["issues"].append(f"{component} missing dependencies: {', '.join(status['missing_dependencies'])}")
                validation["recommendations"].append(f"Load missing dependencies for {component}")
        
        # Check for wireless tools
        exit_code, stdout, stderr = self._run_command(["which", "iw"])
        if exit_code != 0:
            validation["recommendations"].append("Install iw wireless tools")
        
        return validation
    
    def generate_integration_report(self) -> Dict:
        """Generate comprehensive integration report"""
        report = {
            "stack_components": {},
            "configurations": list(self.stack_configurations.keys()),
            "validation": self.validate_stack_integration(),
            "recommendations": []
        }
        
        # Add component information
        for component, module_info in self.stack_modules.items():
            report["stack_components"][component.value] = {
                "name": module_info.name,
                "description": module_info.description,
                "dependencies": module_info.dependencies,
                "config_option": module_info.config_option,
                "load_order": module_info.load_order,
                "required": module_info.required
            }
        
        # Generate recommendations
        if not report["validation"]["configuration_valid"]:
            report["recommendations"].append("Fix stack configuration issues")
        
        if report["validation"]["issues"]:
            report["recommendations"].append("Address identified integration issues")
        
        return report

def main():
    """Main function for testing"""
    integration = WirelessStackIntegration()
    
    print("Wireless Stack Integration Manager")
    print("=" * 50)
    
    # Show available configurations
    print("Available Stack Configurations:")
    for config_name, config_info in integration.stack_configurations.items():
        print(f"  {config_name}: {config_info['name']}")
        print(f"    {config_info['description']}")
        print(f"    Components: {', '.join([c.value for c in config_info['components']])}")
        print()
    
    # Check current stack status
    print("Current Stack Status:")
    status = integration.check_stack_status()
    for component, info in status.items():
        loaded_status = "✓" if info["loaded"] else "✗"
        deps_status = "✓" if info["dependencies_met"] else "✗"
        print(f"  {loaded_status} {component}: {info['module_name']}")
        print(f"    Dependencies: {deps_status}")
        if info["missing_dependencies"]:
            print(f"    Missing: {', '.join(info['missing_dependencies'])}")
    
    # Generate sample configuration
    print("\nSample 'full' Configuration:")
    config = integration.generate_stack_configuration("full")
    for option, value in sorted(config.items()):
        if option.startswith("CONFIG_BACKPORTS"):
            print(f"  {option}={value}")
    
    # Generate integration report
    print("\nIntegration Report:")
    report = integration.generate_integration_report()
    
    validation = report["validation"]
    if validation["configuration_valid"]:
        print("  ✓ Stack configuration is valid")
    else:
        print("  ✗ Stack configuration has issues")
        for issue in validation["issues"]:
            print(f"    - {issue}")
    
    if report["recommendations"]:
        print("  Recommendations:")
        for rec in report["recommendations"]:
            print(f"    - {rec}")

if __name__ == "__main__":
    main()