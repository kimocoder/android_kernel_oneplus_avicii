#!/usr/bin/env python3
"""
Multi-Driver Integration Manager

This module provides comprehensive integration for multiple wireless driver families
including ath10k, iwlwifi, and rt2x00 with their specific configurations and features.
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class DriverFamily(Enum):
    """Supported driver families"""
    ATH10K = "ath10k"
    IWLWIFI = "iwlwifi"
    RT2X00 = "rt2x00"

@dataclass
class DriverConfig:
    """Configuration for a specific driver"""
    name: str
    family: DriverFamily
    description: str
    supported_chipsets: List[str]
    firmware_files: List[str]
    capabilities: List[str]
    power_management: bool
    monitor_mode: bool
    packet_injection: bool
    mesh_support: bool
    kernel_modules: List[str]
    config_options: Dict[str, str]

class MultiDriverIntegration:
    """Multi-driver integration manager"""
    
    def __init__(self, kernel_root: str = "."):
        """Initialize multi-driver integration"""
        self.kernel_root = Path(kernel_root).resolve()
        self.backports_dir = self.kernel_root / "backports-integration"
        
        # Define driver configurations
        self.driver_configs = {
            "ath10k": DriverConfig(
                name="ath10k",
                family=DriverFamily.ATH10K,
                description="Qualcomm Atheros 11ac wireless driver",
                supported_chipsets=["QCA988X", "QCA6174", "QCA9377", "QCA9984", "QCA4019"],
                firmware_files=[
                    "ath10k/QCA988X/hw2.0/firmware-5.bin",
                    "ath10k/QCA988X/hw2.0/board.bin",
                    "ath10k/QCA6174/hw3.0/firmware-4.bin",
                    "ath10k/QCA6174/hw3.0/board.bin"
                ],
                capabilities=["monitor_mode", "packet_injection", "mesh_networking", "spectral_scan"],
                power_management=True,
                monitor_mode=True,
                packet_injection=True,
                mesh_support=True,
                kernel_modules=["ath10k_core", "ath10k_pci", "ath"],
                config_options={
                    "CONFIG_BACKPORTS_ATH10K": "m",
                    "CONFIG_BACKPORTS_ATH10K_DEBUG": "y",
                    "CONFIG_BACKPORTS_ATH10K_DEBUGFS": "y",
                    "CONFIG_BACKPORTS_ATH10K_SPECTRAL": "y",
                    "CONFIG_BACKPORTS_ATH10K_TRACING": "y"
                }
            ),
            "iwlwifi": DriverConfig(
                name="iwlwifi",
                family=DriverFamily.IWLWIFI,
                description="Intel wireless driver",
                supported_chipsets=["7260", "8260", "9260", "AX200", "AX210", "AX201"],
                firmware_files=[
                    "iwlwifi-7260-17.ucode",
                    "iwlwifi-8260-36.ucode",
                    "iwlwifi-9260-th-b0-jf-b0-46.ucode",
                    "iwlwifi-cc-a0-50.ucode"
                ],
                capabilities=["monitor_mode", "wpa3_support", "power_management", "beamforming"],
                power_management=True,
                monitor_mode=True,
                packet_injection=False,  # Limited support
                mesh_support=False,
                kernel_modules=["iwlwifi", "iwlmvm", "iwldvm"],
                config_options={
                    "CONFIG_BACKPORTS_IWLWIFI": "m",
                    "CONFIG_BACKPORTS_IWLWIFI_DEBUG": "y",
                    "CONFIG_BACKPORTS_IWLWIFI_DEBUGFS": "y",
                    "CONFIG_BACKPORTS_IWLWIFI_DEVICE_TRACING": "y",
                    "CONFIG_BACKPORTS_IWLWIFI_LEDS": "y"
                }
            ),
            "rt2x00": DriverConfig(
                name="rt2x00",
                family=DriverFamily.RT2X00,
                description="Ralink/MediaTek wireless driver family",
                supported_chipsets=["RT2500", "RT2800", "RT3070", "RT5370", "RT5572", "MT7610U"],
                firmware_files=[
                    "rt2870.bin",
                    "rt3070.bin",
                    "rt2561.bin",
                    "rt2661.bin"
                ],
                capabilities=["monitor_mode", "packet_injection", "usb_support"],
                power_management=True,
                monitor_mode=True,
                packet_injection=True,
                mesh_support=False,
                kernel_modules=["rt2x00lib", "rt2800lib", "rt2800usb", "rt2800pci"],
                config_options={
                    "CONFIG_BACKPORTS_RT2X00": "m",
                    "CONFIG_BACKPORTS_RT2X00_DEBUG": "y",
                    "CONFIG_BACKPORTS_RT2X00_DEBUGFS": "y",
                    "CONFIG_BACKPORTS_RT2800USB": "m",
                    "CONFIG_BACKPORTS_RT2800PCI": "m"
                }
            )
        }
    
    def _run_command(self, cmd: List[str]) -> Tuple[int, str, str]:
        """Run a system command"""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return -1, "", str(e)    

    def generate_driver_config(self, drivers: List[str]) -> Dict[str, str]:
        """Generate kernel configuration for specified drivers"""
        config = {
            "CONFIG_BACKPORTS_WIRELESS_DRIVERS": "y",
            "CONFIG_BACKPORTS_ATH_DRIVERS": "y"  # Common for Atheros drivers
        }
        
        for driver_name in drivers:
            if driver_name not in self.driver_configs:
                continue
            
            driver_config = self.driver_configs[driver_name]
            config.update(driver_config.config_options)
            
            # Add capability-based configurations
            if driver_config.monitor_mode:
                config["CONFIG_BACKPORTS_MONITOR_MODE"] = "y"
                config["CONFIG_BACKPORTS_WIRELESS_MONITOR_ENHANCED"] = "y"
            
            if driver_config.packet_injection:
                config["CONFIG_BACKPORTS_FRAME_INJECTION"] = "y"
                config["CONFIG_BACKPORTS_WIRELESS_INJECTION_ENHANCED"] = "y"
            
            if driver_config.mesh_support:
                config["CONFIG_BACKPORTS_MAC80211_MESH"] = "y"
                config["CONFIG_BACKPORTS_WIRELESS_MESH_ENHANCED"] = "y"
            
            if driver_config.power_management:
                config["CONFIG_BACKPORTS_PM"] = "y"
                config["CONFIG_BACKPORTS_PM_SLEEP"] = "y"
        
        return config
    
    def create_ath10k_integration(self) -> Dict[str, str]:
        """Create ath10k-specific integration configuration"""
        config = {
            "CONFIG_BACKPORTS_ATH10K": "m",
            "CONFIG_BACKPORTS_ATH10K_PCI": "m",
            "CONFIG_BACKPORTS_ATH10K_DEBUG": "y",
            "CONFIG_BACKPORTS_ATH10K_DEBUGFS": "y",
            "CONFIG_BACKPORTS_ATH10K_SPECTRAL": "y",
            "CONFIG_BACKPORTS_ATH10K_TRACING": "y",
            
            # Firmware management
            "CONFIG_BACKPORTS_ATH10K_FIRMWARE_LOADING": "y",
            
            # Monitor mode and injection
            "CONFIG_BACKPORTS_MONITOR_MODE": "y",
            "CONFIG_BACKPORTS_FRAME_INJECTION": "y",
            
            # Mesh networking
            "CONFIG_BACKPORTS_MAC80211_MESH": "y"
        }
        
        return config
    
    def create_iwlwifi_integration(self) -> Dict[str, str]:
        """Create iwlwifi-specific integration configuration"""
        config = {
            "CONFIG_BACKPORTS_IWLWIFI": "m",
            "CONFIG_BACKPORTS_IWLMVM": "m",
            "CONFIG_BACKPORTS_IWLDVM": "m",
            "CONFIG_BACKPORTS_IWLWIFI_DEBUG": "y",
            "CONFIG_BACKPORTS_IWLWIFI_DEBUGFS": "y",
            "CONFIG_BACKPORTS_IWLWIFI_DEVICE_TRACING": "y",
            "CONFIG_BACKPORTS_IWLWIFI_LEDS": "y",
            
            # Power management (Intel-specific)
            "CONFIG_BACKPORTS_IWLWIFI_POWER_SAVE": "y",
            "CONFIG_BACKPORTS_IWLWIFI_UAPSD": "y",
            
            # Security features
            "CONFIG_BACKPORTS_WIRELESS_CRYPTO": "y",
            "CONFIG_CRYPTO_CMAC": "y",
            "CONFIG_CRYPTO_CCMP": "y",
            "CONFIG_CRYPTO_GCMP": "y",
            
            # Monitor mode (limited)
            "CONFIG_BACKPORTS_MONITOR_MODE": "y"
        }
        
        return config
    
    def create_rt2x00_integration(self) -> Dict[str, str]:
        """Create rt2x00-specific integration configuration"""
        config = {
            "CONFIG_BACKPORTS_RT2X00": "m",
            "CONFIG_BACKPORTS_RT2X00_LIB": "m",
            "CONFIG_BACKPORTS_RT2800_LIB": "m",
            "CONFIG_BACKPORTS_RT2800USB": "m",
            "CONFIG_BACKPORTS_RT2800PCI": "m",
            "CONFIG_BACKPORTS_RT2X00_DEBUG": "y",
            "CONFIG_BACKPORTS_RT2X00_DEBUGFS": "y",
            
            # USB support (common for RT2x00)
            "CONFIG_USB": "y",
            
            # Monitor mode and injection
            "CONFIG_BACKPORTS_MONITOR_MODE": "y",
            "CONFIG_BACKPORTS_FRAME_INJECTION": "y",
            
            # Firmware loading
            "CONFIG_BACKPORTS_RT2X00_FIRMWARE": "y"
        }
        
        return config
    
    def detect_hardware(self) -> Dict[str, List[Dict[str, str]]]:
        """Detect hardware for all supported driver families"""
        detected_hardware = {
            "ath10k": [],
            "iwlwifi": [],
            "rt2x00": []
        }
        
        # Check PCI devices
        exit_code, stdout, stderr = self._run_command(["lspci", "-nn"])
        if exit_code == 0:
            for line in stdout.strip().split('\n'):
                if not line:
                    continue
                
                # Check for Atheros devices (ath10k)
                if "168c:" in line:
                    # Known ath10k PCI IDs
                    ath10k_ids = ["003c", "003e", "0041", "0046", "0056"]
                    for pci_id in ath10k_ids:
                        if pci_id in line:
                            detected_hardware["ath10k"].append({
                                "description": line.strip(),
                                "pci_id": f"168c:{pci_id}",
                                "driver": "ath10k"
                            })
                
                # Check for Intel devices (iwlwifi)
                if "8086:" in line and ("wireless" in line.lower() or "wi-fi" in line.lower()):
                    detected_hardware["iwlwifi"].append({
                        "description": line.strip(),
                        "pci_id": "8086:xxxx",  # Extract actual ID if needed
                        "driver": "iwlwifi"
                    })
        
        # Check USB devices for RT2x00
        exit_code, stdout, stderr = self._run_command(["lsusb"])
        if exit_code == 0:
            for line in stdout.strip().split('\n'):
                if not line:
                    continue
                
                # Check for Ralink/MediaTek devices
                if any(vendor in line for vendor in ["148f:", "0bda:", "7392:"]):
                    detected_hardware["rt2x00"].append({
                        "description": line.strip(),
                        "usb_id": "xxxx:xxxx",  # Extract actual ID if needed
                        "driver": "rt2x00"
                    })
        
        return detected_hardware
    
    def validate_driver_setup(self, drivers: List[str]) -> Dict[str, any]:
        """Validate multi-driver setup"""
        validation = {
            "drivers_loaded": {},
            "firmware_status": {},
            "hardware_detected": {},
            "configuration_valid": True,
            "issues": [],
            "recommendations": []
        }
        
        # Check if drivers are loaded
        exit_code, stdout, stderr = self._run_command(["lsmod"])
        if exit_code == 0:
            for driver_name in drivers:
                if driver_name in self.driver_configs:
                    driver_config = self.driver_configs[driver_name]
                    validation["drivers_loaded"][driver_name] = any(
                        module in stdout for module in driver_config.kernel_modules
                    )
        
        # Check firmware status
        for driver_name in drivers:
            if driver_name not in self.driver_configs:
                continue
            
            driver_config = self.driver_configs[driver_name]
            validation["firmware_status"][driver_name] = {}
            
            for fw_file in driver_config.firmware_files:
                fw_path = Path("/lib/firmware") / fw_file
                validation["firmware_status"][driver_name][fw_file] = fw_path.exists()
        
        # Detect hardware
        validation["hardware_detected"] = self.detect_hardware()
        
        # Generate issues and recommendations
        for driver_name in drivers:
            if not validation["drivers_loaded"].get(driver_name, False):
                validation["issues"].append(f"{driver_name} driver not loaded")
                validation["recommendations"].append(f"Load {driver_name} driver modules")
        
        # Check for missing firmware
        missing_firmware = []
        for driver_name, fw_status in validation["firmware_status"].items():
            for fw_file, exists in fw_status.items():
                if not exists:
                    missing_firmware.append(f"{driver_name}: {fw_file}")
        
        if missing_firmware:
            validation["issues"].append(f"Missing firmware files: {', '.join(missing_firmware[:3])}...")
            validation["recommendations"].append("Install missing firmware files")
        
        validation["configuration_valid"] = len(validation["issues"]) == 0
        
        return validation
    
    def create_build_rules(self, drivers: List[str]) -> str:
        """Create Makefile build rules for multiple drivers"""
        rules = [
            "#",
            "# Multi-Driver Build Rules",
            "# Support for ath10k, iwlwifi, and rt2x00",
            "#",
            ""
        ]
        
        for driver_name in drivers:
            if driver_name not in self.driver_configs:
                continue
            
            driver_config = self.driver_configs[driver_name]
            
            if driver_name == "ath10k":
                rules.extend([
                    "# ath10k driver build rules",
                    "ifdef CONFIG_BACKPORTS_ATH10K",
                    "    obj-$(CONFIG_BACKPORTS_ATH10K) += ath10k/",
                    "    CFLAGS_ath10k += -DCONFIG_ATH10K_DEBUG",
                    "    ifdef CONFIG_BACKPORTS_ATH10K_SPECTRAL",
                    "        CFLAGS_ath10k += -DCONFIG_ATH10K_SPECTRAL",
                    "    endif",
                    "endif",
                    ""
                ])
            
            elif driver_name == "iwlwifi":
                rules.extend([
                    "# iwlwifi driver build rules",
                    "ifdef CONFIG_BACKPORTS_IWLWIFI",
                    "    obj-$(CONFIG_BACKPORTS_IWLWIFI) += iwlwifi/",
                    "    CFLAGS_iwlwifi += -DCONFIG_IWLWIFI_DEBUG",
                    "    ifdef CONFIG_BACKPORTS_IWLWIFI_DEVICE_TRACING",
                    "        CFLAGS_iwlwifi += -DCONFIG_IWLWIFI_DEVICE_TRACING",
                    "    endif",
                    "endif",
                    ""
                ])
            
            elif driver_name == "rt2x00":
                rules.extend([
                    "# rt2x00 driver build rules",
                    "ifdef CONFIG_BACKPORTS_RT2X00",
                    "    obj-$(CONFIG_BACKPORTS_RT2X00) += rt2x00/",
                    "    CFLAGS_rt2x00 += -DCONFIG_RT2X00_DEBUG",
                    "    ifdef CONFIG_BACKPORTS_RT2800USB",
                    "        obj-$(CONFIG_BACKPORTS_RT2800USB) += rt2x00/rt2800usb.o",
                    "    endif",
                    "endif",
                    ""
                ])
        
        # Add firmware installation rules
        rules.extend([
            "# Multi-driver firmware installation",
            "install-multi-driver-firmware:"
        ])
        
        for driver_name in drivers:
            if driver_name in self.driver_configs:
                rules.append(f"\t$(MAKE) install-{driver_name}-firmware")
        
        rules.extend([
            "",
            "# Multi-driver clean rules",
            "clean-multi-drivers:"
        ])
        
        for driver_name in drivers:
            if driver_name in self.driver_configs:
                rules.append(f"\t$(MAKE) clean-{driver_name}")
        
        rules.extend([
            "",
            ".PHONY: install-multi-driver-firmware clean-multi-drivers"
        ])
        
        return "\n".join(rules)
    
    def generate_integration_report(self, drivers: List[str]) -> Dict[str, any]:
        """Generate comprehensive multi-driver integration report"""
        report = {
            "supported_drivers": drivers,
            "driver_details": {},
            "configuration": self.generate_driver_config(drivers),
            "validation": self.validate_driver_setup(drivers),
            "hardware_detection": self.detect_hardware(),
            "capabilities_summary": {},
            "recommendations": []
        }
        
        # Add driver details
        for driver_name in drivers:
            if driver_name in self.driver_configs:
                driver_config = self.driver_configs[driver_name]
                report["driver_details"][driver_name] = {
                    "description": driver_config.description,
                    "family": driver_config.family.value,
                    "supported_chipsets": driver_config.supported_chipsets,
                    "capabilities": driver_config.capabilities,
                    "monitor_mode": driver_config.monitor_mode,
                    "packet_injection": driver_config.packet_injection,
                    "mesh_support": driver_config.mesh_support,
                    "power_management": driver_config.power_management,
                    "kernel_modules": driver_config.kernel_modules,
                    "firmware_files_count": len(driver_config.firmware_files)
                }
        
        # Aggregate capabilities
        all_capabilities = set()
        for driver_name in drivers:
            if driver_name in self.driver_configs:
                driver_config = self.driver_configs[driver_name]
                all_capabilities.update(driver_config.capabilities)
        
        report["capabilities_summary"] = {
            "monitor_mode": any(self.driver_configs[d].monitor_mode for d in drivers if d in self.driver_configs),
            "packet_injection": any(self.driver_configs[d].packet_injection for d in drivers if d in self.driver_configs),
            "mesh_networking": any(self.driver_configs[d].mesh_support for d in drivers if d in self.driver_configs),
            "power_management": any(self.driver_configs[d].power_management for d in drivers if d in self.driver_configs),
            "all_capabilities": list(all_capabilities)
        }
        
        # Generate recommendations
        validation = report["validation"]
        if not validation["configuration_valid"]:
            report["recommendations"].extend(validation["recommendations"])
        
        # Check for hardware without drivers
        hw_detected = report["hardware_detection"]
        for driver_family, devices in hw_detected.items():
            if devices and driver_family not in drivers:
                report["recommendations"].append(f"Consider enabling {driver_family} driver for detected hardware")
        
        return report

def main():
    """Main function for testing"""
    integration = MultiDriverIntegration()
    
    print("Multi-Driver Integration Manager")
    print("=" * 50)
    
    # Show supported drivers
    print("Supported Drivers:")
    for driver_name, driver_config in integration.driver_configs.items():
        print(f"  {driver_name}: {driver_config.description}")
        print(f"    Family: {driver_config.family.value}")
        print(f"    Chipsets: {', '.join(driver_config.supported_chipsets[:3])}...")
        print(f"    Capabilities: {', '.join(driver_config.capabilities)}")
        print(f"    Monitor Mode: {'✓' if driver_config.monitor_mode else '✗'}")
        print(f"    Packet Injection: {'✓' if driver_config.packet_injection else '✗'}")
        print(f"    Mesh Support: {'✓' if driver_config.mesh_support else '✗'}")
        print()
    
    # Detect hardware
    print("Hardware Detection:")
    hardware = integration.detect_hardware()
    for driver_family, devices in hardware.items():
        print(f"  {driver_family}: {len(devices)} device(s) detected")
        for device in devices[:2]:  # Show first 2 devices
            print(f"    - {device['description'][:60]}...")
    
    # Generate sample configuration
    test_drivers = ["ath10k", "iwlwifi", "rt2x00"]
    print(f"\nSample Configuration for {', '.join(test_drivers)}:")
    config = integration.generate_driver_config(test_drivers)
    
    # Show key configuration options
    key_options = [opt for opt in sorted(config.keys()) if opt.startswith("CONFIG_BACKPORTS") and any(driver in opt for driver in ["ATH10K", "IWLWIFI", "RT2X00"])]
    for option in key_options[:10]:  # Show first 10 options
        print(f"  {option}={config[option]}")
    
    if len(key_options) > 10:
        print(f"  ... and {len(key_options) - 10} more options")
    
    # Validate setup
    print(f"\nValidation Results:")
    validation = integration.validate_driver_setup(test_drivers)
    
    config_status = "✓" if validation["configuration_valid"] else "✗"
    print(f"  Configuration Valid: {config_status}")
    
    for driver_name in test_drivers:
        driver_status = "✓" if validation["drivers_loaded"].get(driver_name, False) else "✗"
        print(f"  {driver_name} Loaded: {driver_status}")
    
    if validation["issues"]:
        print(f"  Issues: {len(validation['issues'])}")
        for issue in validation["issues"][:3]:  # Show first 3 issues
            print(f"    - {issue}")
    
    if validation["recommendations"]:
        print(f"  Recommendations: {len(validation['recommendations'])}")
        for rec in validation["recommendations"][:3]:  # Show first 3 recommendations
            print(f"    - {rec}")

if __name__ == "__main__":
    main()