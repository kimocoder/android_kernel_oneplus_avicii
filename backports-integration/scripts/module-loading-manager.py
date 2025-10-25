#!/usr/bin/env python3
"""
Wireless Module Loading Order Manager

This module manages the proper loading order for wireless stack modules
to ensure dependencies are met and avoid conflicts.
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class ModuleDependency:
    """Represents a module dependency relationship"""
    module: str
    depends_on: List[str]
    load_order: int
    optional: bool = False
    description: str = ""

class ModuleLoadingManager:
    """Manager for wireless module loading order"""
    
    def __init__(self):
        """Initialize module loading manager"""
        # Define the complete wireless stack loading order
        self.module_dependencies = [
            ModuleDependency(
                module="crypto_aes",
                depends_on=[],
                load_order=1,
                description="AES crypto support for wireless security"
            ),
            ModuleDependency(
                module="crypto_arc4",
                depends_on=[],
                load_order=2,
                description="ARC4 crypto support for legacy wireless"
            ),
            ModuleDependency(
                module="crypto_cmac",
                depends_on=[],
                load_order=3,
                optional=True,
                description="CMAC crypto support for WPA3"
            ),
            ModuleDependency(
                module="crypto_ccmp",
                depends_on=[],
                load_order=4,
                description="CCMP crypto support for WPA2/WPA3"
            ),
            ModuleDependency(
                module="crypto_gcmp",
                depends_on=[],
                load_order=5,
                optional=True,
                description="GCMP crypto support for WPA3"
            ),
            ModuleDependency(
                module="rfkill",
                depends_on=[],
                load_order=10,
                description="RF kill switch support"
            ),
            ModuleDependency(
                module="cfg80211",
                depends_on=["rfkill", "crypto_aes"],
                load_order=20,
                description="Wireless configuration API"
            ),
            ModuleDependency(
                module="mac80211",
                depends_on=["cfg80211", "crypto_aes", "crypto_arc4"],
                load_order=30,
                description="IEEE 802.11 networking stack"
            ),
            ModuleDependency(
                module="ath",
                depends_on=["cfg80211"],
                load_order=40,
                optional=True,
                description="Atheros wireless common code"
            ),
            ModuleDependency(
                module="ath11k",
                depends_on=["mac80211", "ath"],
                load_order=50,
                optional=True,
                description="Qualcomm Atheros 11ac/11ax driver"
            ),
            ModuleDependency(
                module="ath10k_core",
                depends_on=["mac80211", "ath"],
                load_order=51,
                optional=True,
                description="Qualcomm Atheros 11ac driver core"
            ),
            ModuleDependency(
                module="ath10k_pci",
                depends_on=["ath10k_core"],
                load_order=52,
                optional=True,
                description="Qualcomm Atheros 11ac PCIe driver"
            ),
            ModuleDependency(
                module="ath9k_hw",
                depends_on=["ath"],
                load_order=53,
                optional=True,
                description="Atheros 9k hardware support"
            ),
            ModuleDependency(
                module="ath9k_common",
                depends_on=["ath9k_hw"],
                load_order=54,
                optional=True,
                description="Atheros 9k common code"
            ),
            ModuleDependency(
                module="ath9k",
                depends_on=["mac80211", "ath9k_common"],
                load_order=55,
                optional=True,
                description="Atheros 9k wireless driver"
            ),
            ModuleDependency(
                module="iwlwifi",
                depends_on=["mac80211"],
                load_order=60,
                optional=True,
                description="Intel wireless driver"
            ),
            ModuleDependency(
                module="rt2x00lib",
                depends_on=["mac80211"],
                load_order=70,
                optional=True,
                description="Ralink RT2x00 library"
            ),
            ModuleDependency(
                module="rt2800lib",
                depends_on=["rt2x00lib"],
                load_order=71,
                optional=True,
                description="Ralink RT2800 library"
            ),
            ModuleDependency(
                module="rt2800usb",
                depends_on=["rt2800lib"],
                load_order=72,
                optional=True,
                description="Ralink RT2800 USB driver"
            )
        ]
    
    def _run_command(self, cmd: List[str]) -> Tuple[int, str, str]:
        """Run a system command"""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return -1, "", str(e)
    
    def is_module_loaded(self, module_name: str) -> bool:
        """Check if a module is currently loaded"""
        exit_code, stdout, stderr = self._run_command(["lsmod"])
        if exit_code == 0:
            return module_name in stdout
        return False
    
    def is_module_available(self, module_name: str) -> bool:
        """Check if a module is available for loading"""
        exit_code, stdout, stderr = self._run_command(["modinfo", module_name])
        return exit_code == 0
    
    def load_module(self, module_name: str, force: bool = False) -> Tuple[bool, str]:
        """Load a single module"""
        if not force and self.is_module_loaded(module_name):
            return True, f"Module {module_name} already loaded"
        
        if not self.is_module_available(module_name):
            return False, f"Module {module_name} not available"
        
        exit_code, stdout, stderr = self._run_command(["modprobe", module_name])
        if exit_code == 0:
            return True, f"Module {module_name} loaded successfully"
        else:
            return False, f"Failed to load {module_name}: {stderr}"
    
    def unload_module(self, module_name: str) -> Tuple[bool, str]:
        """Unload a single module"""
        if not self.is_module_loaded(module_name):
            return True, f"Module {module_name} not loaded"
        
        exit_code, stdout, stderr = self._run_command(["modprobe", "-r", module_name])
        if exit_code == 0:
            return True, f"Module {module_name} unloaded successfully"
        else:
            return False, f"Failed to unload {module_name}: {stderr}"
    
    def get_loading_order(self, modules: List[str]) -> List[ModuleDependency]:
        """Get the proper loading order for specified modules"""
        # Filter dependencies to only include requested modules
        filtered_deps = []
        
        for dep in self.module_dependencies:
            if dep.module in modules:
                filtered_deps.append(dep)
            # Also include required dependencies
            elif any(dep.module in req_dep.depends_on for req_dep in self.module_dependencies if req_dep.module in modules):
                filtered_deps.append(dep)
        
        # Sort by load order
        return sorted(filtered_deps, key=lambda x: x.load_order)
    
    def validate_dependencies(self, modules: List[str]) -> Dict[str, List[str]]:
        """Validate that all dependencies are available"""
        issues = {}
        
        for module in modules:
            module_dep = next((dep for dep in self.module_dependencies if dep.module == module), None)
            if not module_dep:
                issues[module] = [f"Unknown module: {module}"]
                continue
            
            missing_deps = []
            for dep in module_dep.depends_on:
                if dep not in modules and not self.is_module_loaded(dep):
                    missing_deps.append(dep)
            
            if missing_deps:
                issues[module] = missing_deps
        
        return issues
    
    def load_wireless_stack(self, modules: List[str], dry_run: bool = False) -> Dict[str, any]:
        """Load wireless stack modules in proper order"""
        result = {
            "success": True,
            "loaded_modules": [],
            "failed_modules": [],
            "skipped_modules": [],
            "messages": []
        }
        
        # Get proper loading order
        loading_order = self.get_loading_order(modules)
        
        # Validate dependencies
        dependency_issues = self.validate_dependencies(modules)
        if dependency_issues:
            result["success"] = False
            for module, missing_deps in dependency_issues.items():
                result["messages"].append(f"Module {module} missing dependencies: {', '.join(missing_deps)}")
            return result
        
        # Load modules in order
        for module_dep in loading_order:
            module_name = module_dep.module
            
            if dry_run:
                result["messages"].append(f"Would load: {module_name} ({module_dep.description})")
                continue
            
            # Check if module is requested or required
            if module_name not in modules and module_dep.optional:
                result["skipped_modules"].append(module_name)
                result["messages"].append(f"Skipping optional module: {module_name}")
                continue
            
            # Load the module
            success, message = self.load_module(module_name)
            result["messages"].append(message)
            
            if success:
                result["loaded_modules"].append(module_name)
                # Small delay to allow module initialization
                time.sleep(0.1)
            else:
                result["failed_modules"].append(module_name)
                if not module_dep.optional:
                    result["success"] = False
                    break
        
        return result
    
    def unload_wireless_stack(self, modules: List[str], dry_run: bool = False) -> Dict[str, any]:
        """Unload wireless stack modules in reverse order"""
        result = {
            "success": True,
            "unloaded_modules": [],
            "failed_modules": [],
            "messages": []
        }
        
        # Get loading order and reverse it
        loading_order = self.get_loading_order(modules)
        unloading_order = reversed(loading_order)
        
        # Unload modules in reverse order
        for module_dep in unloading_order:
            module_name = module_dep.module
            
            if dry_run:
                result["messages"].append(f"Would unload: {module_name}")
                continue
            
            if not self.is_module_loaded(module_name):
                result["messages"].append(f"Module {module_name} not loaded")
                continue
            
            # Unload the module
            success, message = self.unload_module(module_name)
            result["messages"].append(message)
            
            if success:
                result["unloaded_modules"].append(module_name)
                time.sleep(0.1)
            else:
                result["failed_modules"].append(module_name)
                # Continue trying to unload other modules
        
        return result
    
    def get_current_stack_status(self) -> Dict[str, Dict[str, any]]:
        """Get current status of wireless stack modules"""
        status = {}
        
        for module_dep in self.module_dependencies:
            module_name = module_dep.module
            status[module_name] = {
                "loaded": self.is_module_loaded(module_name),
                "available": self.is_module_available(module_name),
                "load_order": module_dep.load_order,
                "optional": module_dep.optional,
                "description": module_dep.description,
                "dependencies": module_dep.depends_on
            }
        
        return status
    
    def generate_loading_script(self, modules: List[str], script_path: str) -> bool:
        """Generate a shell script for loading modules"""
        loading_order = self.get_loading_order(modules)
        
        script_content = [
            "#!/bin/bash",
            "#",
            "# Wireless Stack Module Loading Script",
            "# Generated automatically",
            "#",
            "",
            "set -e",
            "",
            "# Colors for output",
            "RED='\\033[0;31m'",
            "GREEN='\\033[0;32m'",
            "YELLOW='\\033[1;33m'",
            "NC='\\033[0m' # No Color",
            "",
            "# Function to print colored output",
            "print_status() {",
            "    local color=$1",
            "    local message=$2",
            "    echo -e \"${color}${message}${NC}\"",
            "}",
            "",
            "# Function to load module with error checking",
            "load_module() {",
            "    local module=$1",
            "    local description=$2",
            "    local optional=$3",
            "    ",
            "    print_status \"$YELLOW\" \"Loading $module ($description)...\"",
            "    ",
            "    if lsmod | grep -q \"^$module \"; then",
            "        print_status \"$GREEN\" \"  $module already loaded\"",
            "        return 0",
            "    fi",
            "    ",
            "    if modprobe \"$module\" 2>/dev/null; then",
            "        print_status \"$GREEN\" \"  $module loaded successfully\"",
            "        return 0",
            "    else",
            "        if [ \"$optional\" = \"true\" ]; then",
            "            print_status \"$YELLOW\" \"  WARNING: Optional module $module failed to load\"",
            "            return 0",
            "        else",
            "            print_status \"$RED\" \"  ERROR: Failed to load required module $module\"",
            "            return 1",
            "        fi",
            "    fi",
            "}",
            "",
            "echo \"Starting wireless stack module loading...\"",
            "echo"
        ]
        
        # Add module loading commands
        for module_dep in loading_order:
            optional = "true" if module_dep.optional else "false"
            script_content.append(
                f"load_module {module_dep.module} \"{module_dep.description}\" {optional}"
            )
        
        script_content.extend([
            "",
            "echo",
            "print_status \"$GREEN\" \"Wireless stack loaded successfully!\"",
            "",
            "# Show loaded wireless modules",
            "echo \"Currently loaded wireless modules:\"",
            "lsmod | grep -E '(cfg80211|mac80211|ath|iwl|rt2)' || echo \"No wireless modules found\"",
            "",
            "# Check for wireless interfaces",
            "if command -v iw >/dev/null 2>&1; then",
            "    echo",
            "    echo \"Wireless interfaces:\"",
            "    iw dev 2>/dev/null || echo \"No wireless interfaces found\"",
            "fi"
        ])
        
        try:
            with open(script_path, 'w') as f:
                f.write('\n'.join(script_content))
            
            # Make script executable
            os.chmod(script_path, 0o755)
            return True
        except Exception as e:
            print(f"Error creating script: {e}")
            return False

def main():
    """Main function for testing"""
    manager = ModuleLoadingManager()
    
    print("Wireless Module Loading Order Manager")
    print("=" * 50)
    
    # Show current stack status
    print("Current Stack Status:")
    status = manager.get_current_stack_status()
    
    for module, info in status.items():
        loaded_status = "✓" if info["loaded"] else "✗"
        available_status = "✓" if info["available"] else "✗"
        optional_marker = " (optional)" if info["optional"] else ""
        
        print(f"  {loaded_status} {module}{optional_marker}")
        print(f"    Available: {available_status}, Order: {info['load_order']}")
        print(f"    {info['description']}")
        if info["dependencies"]:
            print(f"    Dependencies: {', '.join(info['dependencies'])}")
        print()
    
    # Test loading order for common drivers
    test_modules = ["cfg80211", "mac80211", "ath11k", "iwlwifi"]
    print(f"Loading order for {', '.join(test_modules)}:")
    
    loading_order = manager.get_loading_order(test_modules)
    for i, module_dep in enumerate(loading_order, 1):
        optional_marker = " (optional)" if module_dep.optional else ""
        print(f"  {i}. {module_dep.module}{optional_marker}")
        print(f"     {module_dep.description}")
    
    # Validate dependencies
    print(f"\nDependency Validation:")
    issues = manager.validate_dependencies(test_modules)
    if issues:
        for module, missing_deps in issues.items():
            print(f"  ✗ {module}: missing {', '.join(missing_deps)}")
    else:
        print("  ✓ All dependencies satisfied")
    
    # Dry run test
    print(f"\nDry Run Test:")
    result = manager.load_wireless_stack(test_modules, dry_run=True)
    for message in result["messages"]:
        print(f"  {message}")

if __name__ == "__main__":
    main()