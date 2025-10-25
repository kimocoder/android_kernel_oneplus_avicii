#!/usr/bin/env python3
"""
Wireless Driver Registry and Metadata System

This module provides a comprehensive registry for wireless drivers with
chipset information, capabilities, and dependency management.
"""

import json
import yaml
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict
from enum import Enum

class DriverCapability(Enum):
    """Enumeration of wireless driver capabilities"""
    MONITOR_MODE = "monitor_mode"
    PACKET_INJECTION = "packet_injection"
    MESH_NETWORKING = "mesh_networking"
    WPA3_SUPPORT = "wpa3_support"
    SAE_SUPPORT = "sae_support"
    OWE_SUPPORT = "owe_support"
    SPECTRAL_SCAN = "spectral_scan"
    POWER_MANAGEMENT = "power_management"
    MULTI_ANTENNA = "multi_antenna"
    BEAMFORMING = "beamforming"
    MU_MIMO = "mu_mimo"
    OFDMA = "ofdma"

class WirelessStandard(Enum):
    """Enumeration of wireless standards"""
    IEEE_802_11A = "802.11a"
    IEEE_802_11B = "802.11b"
    IEEE_802_11G = "802.11g"
    IEEE_802_11N = "802.11n"
    IEEE_802_11AC = "802.11ac"
    IEEE_802_11AX = "802.11ax"

@dataclass
class ChipsetInfo:
    """Information about a specific wireless chipset"""
    model: str
    vendor: str
    interface: str  # PCIe, USB, SDIO
    antenna_config: str  # 1x1, 2x2, 3x3, 4x4
    frequency_bands: List[str]  # 2.4GHz, 5GHz, 6GHz
    max_speed_mbps: int
    standards: List[WirelessStandard]
    capabilities: Set[DriverCapability]
    firmware_required: bool
    firmware_files: List[str]
    power_consumption_mw: Optional[int] = None
    
    def __post_init__(self):
        """Convert lists to sets for capabilities and standards"""
        if isinstance(self.capabilities, list):
            self.capabilities = set(self.capabilities)
        if isinstance(self.standards, list):
            self.standards = [WirelessStandard(s) if isinstance(s, str) else s for s in self.standards]

@dataclass
class DriverInfo:
    """Information about a wireless driver"""
    name: str
    family: str  # ath11k, ath10k, iwlwifi, rt2x00
    vendor: str
    description: str
    kernel_module: str
    supported_chipsets: List[ChipsetInfo]
    dependencies: List[str]
    conflicts: List[str]
    min_kernel_version: str
    max_kernel_version: Optional[str]
    android_compatible: bool
    capabilities: Set[DriverCapability]
    config_options: Dict[str, Any]
    
    def __post_init__(self):
        """Convert lists to sets for capabilities"""
        if isinstance(self.capabilities, list):
            self.capabilities = set(self.capabilities)

class WirelessDriverRegistry:
    """Registry for managing wireless driver information and metadata"""
    
    def __init__(self, registry_path: Optional[Path] = None):
        """Initialize the wireless driver registry"""
        self.registry_path = registry_path or Path(__file__).parent / "wireless_drivers.yaml"
        self.drivers: Dict[str, DriverInfo] = {}
        self.chipsets: Dict[str, ChipsetInfo] = {}
        self._load_registry()
    
    def _load_registry(self):
        """Load driver registry from YAML file"""
        if not self.registry_path.exists():
            self._create_default_registry()
            return
        
        try:
            with open(self.registry_path, 'r') as f:
                data = yaml.safe_load(f)
            
            # Load drivers
            for driver_name, driver_data in data.get('drivers', {}).items():
                chipsets = []
                for chipset_data in driver_data.get('supported_chipsets', []):
                    chipset = ChipsetInfo(**chipset_data)
                    chipsets.append(chipset)
                    self.chipsets[chipset.model] = chipset
                
                driver_data['supported_chipsets'] = chipsets
                driver = DriverInfo(**driver_data)
                self.drivers[driver_name] = driver
                
        except Exception as e:
            print(f"Error loading registry: {e}")
            self._create_default_registry()
    
    def _create_default_registry(self):
        """Create default registry with common wireless drivers"""
        # ath11k chipsets
        qca6390 = ChipsetInfo(
            model="QCA6390",
            vendor="Qualcomm",
            interface="PCIe",
            antenna_config="2x2",
            frequency_bands=["2.4GHz", "5GHz"],
            max_speed_mbps=1200,
            standards=[WirelessStandard.IEEE_802_11AX],
            capabilities={
                DriverCapability.MONITOR_MODE,
                DriverCapability.PACKET_INJECTION,
                DriverCapability.MESH_NETWORKING,
                DriverCapability.WPA3_SUPPORT,
                DriverCapability.SAE_SUPPORT,
                DriverCapability.OWE_SUPPORT,
                DriverCapability.POWER_MANAGEMENT,
                DriverCapability.MU_MIMO,
                DriverCapability.OFDMA
            },
            firmware_required=True,
            firmware_files=["ath11k/QCA6390/hw2.0/amss.bin", "ath11k/QCA6390/hw2.0/m3.bin"]
        )
        
        qca6490 = ChipsetInfo(
            model="QCA6490",
            vendor="Qualcomm",
            interface="PCIe",
            antenna_config="2x2",
            frequency_bands=["2.4GHz", "5GHz"],
            max_speed_mbps=1800,
            standards=[WirelessStandard.IEEE_802_11AX],
            capabilities={
                DriverCapability.MONITOR_MODE,
                DriverCapability.PACKET_INJECTION,
                DriverCapability.MESH_NETWORKING,
                DriverCapability.WPA3_SUPPORT,
                DriverCapability.SAE_SUPPORT,
                DriverCapability.OWE_SUPPORT,
                DriverCapability.POWER_MANAGEMENT,
                DriverCapability.MU_MIMO,
                DriverCapability.OFDMA,
                DriverCapability.BEAMFORMING
            },
            firmware_required=True,
            firmware_files=["ath11k/QCA6490/hw2.0/amss.bin", "ath11k/QCA6490/hw2.0/m3.bin"]
        )
        
        wcn6855 = ChipsetInfo(
            model="WCN6855",
            vendor="Qualcomm",
            interface="PCIe",
            antenna_config="2x2",
            frequency_bands=["2.4GHz", "5GHz"],
            max_speed_mbps=1200,
            standards=[WirelessStandard.IEEE_802_11AX],
            capabilities={
                DriverCapability.MONITOR_MODE,
                DriverCapability.PACKET_INJECTION,
                DriverCapability.MESH_NETWORKING,
                DriverCapability.WPA3_SUPPORT,
                DriverCapability.SAE_SUPPORT,
                DriverCapability.OWE_SUPPORT,
                DriverCapability.POWER_MANAGEMENT,
                DriverCapability.MU_MIMO,
                DriverCapability.OFDMA
            },
            firmware_required=True,
            firmware_files=["ath11k/WCN6855/hw2.0/amss.bin", "ath11k/WCN6855/hw2.0/m3.bin"]
        )
        
        qcn9074 = ChipsetInfo(
            model="QCN9074",
            vendor="Qualcomm",
            interface="PCIe",
            antenna_config="4x4",
            frequency_bands=["2.4GHz", "5GHz", "6GHz"],
            max_speed_mbps=4800,
            standards=[WirelessStandard.IEEE_802_11AX],
            capabilities={
                DriverCapability.MONITOR_MODE,
                DriverCapability.PACKET_INJECTION,
                DriverCapability.MESH_NETWORKING,
                DriverCapability.WPA3_SUPPORT,
                DriverCapability.SAE_SUPPORT,
                DriverCapability.OWE_SUPPORT,
                DriverCapability.SPECTRAL_SCAN,
                DriverCapability.MULTI_ANTENNA,
                DriverCapability.BEAMFORMING,
                DriverCapability.MU_MIMO,
                DriverCapability.OFDMA
            },
            firmware_required=True,
            firmware_files=["ath11k/QCN9074/hw1.0/amss.bin", "ath11k/QCN9074/hw1.0/m3.bin"]
        )
        
        # ath11k driver
        ath11k_driver = DriverInfo(
            name="ath11k",
            family="ath11k",
            vendor="Qualcomm",
            description="Qualcomm Atheros 11ac/11ax wireless driver",
            kernel_module="ath11k",
            supported_chipsets=[qca6390, qca6490, wcn6855, qcn9074],
            dependencies=["mac80211", "cfg80211", "crypto"],
            conflicts=["ath10k", "qcacld"],
            min_kernel_version="4.19",
            max_kernel_version=None,
            android_compatible=True,
            capabilities={
                DriverCapability.MONITOR_MODE,
                DriverCapability.PACKET_INJECTION,
                DriverCapability.MESH_NETWORKING,
                DriverCapability.WPA3_SUPPORT,
                DriverCapability.SAE_SUPPORT,
                DriverCapability.OWE_SUPPORT,
                DriverCapability.SPECTRAL_SCAN,
                DriverCapability.POWER_MANAGEMENT
            },
            config_options={
                "CONFIG_ATH11K": "m",
                "CONFIG_ATH11K_DEBUG": "y",
                "CONFIG_ATH11K_DEBUGFS": "y",
                "CONFIG_ATH11K_SPECTRAL": "y"
            }
        )
        
        # Store in registry
        self.drivers["ath11k"] = ath11k_driver
        for chipset in ath11k_driver.supported_chipsets:
            self.chipsets[chipset.model] = chipset
        
        # Add more drivers (ath10k, iwlwifi, rt2x00) here...
        self._add_ath10k_driver()
        self._add_iwlwifi_driver()
        self._add_rt2x00_driver()
        
        # Save the default registry
        self.save_registry()
    
    def _add_ath10k_driver(self):
        """Add ath10k driver to registry"""
        qca988x = ChipsetInfo(
            model="QCA988X",
            vendor="Qualcomm",
            interface="PCIe",
            antenna_config="3x3",
            frequency_bands=["2.4GHz", "5GHz"],
            max_speed_mbps=867,
            standards=[WirelessStandard.IEEE_802_11AC],
            capabilities={
                DriverCapability.MONITOR_MODE,
                DriverCapability.PACKET_INJECTION,
                DriverCapability.MESH_NETWORKING,
                DriverCapability.SPECTRAL_SCAN,
                DriverCapability.MULTI_ANTENNA
            },
            firmware_required=True,
            firmware_files=["ath10k/QCA988X/hw2.0/firmware.bin"]
        )
        
        qca6174 = ChipsetInfo(
            model="QCA6174",
            vendor="Qualcomm",
            interface="PCIe",
            antenna_config="2x2",
            frequency_bands=["2.4GHz", "5GHz"],
            max_speed_mbps=867,
            standards=[WirelessStandard.IEEE_802_11AC],
            capabilities={
                DriverCapability.MONITOR_MODE,
                DriverCapability.PACKET_INJECTION,
                DriverCapability.MESH_NETWORKING,
                DriverCapability.POWER_MANAGEMENT
            },
            firmware_required=True,
            firmware_files=["ath10k/QCA6174/hw3.0/firmware.bin"]
        )
        
        ath10k_driver = DriverInfo(
            name="ath10k",
            family="ath10k",
            vendor="Qualcomm",
            description="Qualcomm Atheros 11ac wireless driver",
            kernel_module="ath10k_core",
            supported_chipsets=[qca988x, qca6174],
            dependencies=["mac80211", "cfg80211", "crypto"],
            conflicts=["ath11k", "qcacld"],
            min_kernel_version="3.10",
            max_kernel_version=None,
            android_compatible=True,
            capabilities={
                DriverCapability.MONITOR_MODE,
                DriverCapability.PACKET_INJECTION,
                DriverCapability.MESH_NETWORKING,
                DriverCapability.SPECTRAL_SCAN
            },
            config_options={
                "CONFIG_ATH10K": "m",
                "CONFIG_ATH10K_DEBUG": "y",
                "CONFIG_ATH10K_DEBUGFS": "y"
            }
        )
        
        self.drivers["ath10k"] = ath10k_driver
        for chipset in ath10k_driver.supported_chipsets:
            self.chipsets[chipset.model] = chipset
    
    def _add_iwlwifi_driver(self):
        """Add iwlwifi driver to registry"""
        ax200 = ChipsetInfo(
            model="AX200",
            vendor="Intel",
            interface="PCIe",
            antenna_config="2x2",
            frequency_bands=["2.4GHz", "5GHz"],
            max_speed_mbps=2400,
            standards=[WirelessStandard.IEEE_802_11AX],
            capabilities={
                DriverCapability.MONITOR_MODE,
                DriverCapability.WPA3_SUPPORT,
                DriverCapability.SAE_SUPPORT,
                DriverCapability.OWE_SUPPORT,
                DriverCapability.POWER_MANAGEMENT,
                DriverCapability.MU_MIMO,
                DriverCapability.OFDMA
            },
            firmware_required=True,
            firmware_files=["iwlwifi-cc-a0-50.ucode"]
        )
        
        iwlwifi_driver = DriverInfo(
            name="iwlwifi",
            family="iwlwifi",
            vendor="Intel",
            description="Intel wireless driver",
            kernel_module="iwlwifi",
            supported_chipsets=[ax200],
            dependencies=["mac80211", "cfg80211", "crypto"],
            conflicts=[],
            min_kernel_version="4.19",
            max_kernel_version=None,
            android_compatible=True,
            capabilities={
                DriverCapability.MONITOR_MODE,
                DriverCapability.WPA3_SUPPORT,
                DriverCapability.SAE_SUPPORT,
                DriverCapability.OWE_SUPPORT,
                DriverCapability.POWER_MANAGEMENT
            },
            config_options={
                "CONFIG_IWLWIFI": "m",
                "CONFIG_IWLWIFI_DEBUG": "y"
            }
        )
        
        self.drivers["iwlwifi"] = iwlwifi_driver
        for chipset in iwlwifi_driver.supported_chipsets:
            self.chipsets[chipset.model] = chipset
    
    def _add_rt2x00_driver(self):
        """Add rt2x00 driver to registry"""
        rt5370 = ChipsetInfo(
            model="RT5370",
            vendor="Ralink",
            interface="USB",
            antenna_config="1x1",
            frequency_bands=["2.4GHz"],
            max_speed_mbps=150,
            standards=[WirelessStandard.IEEE_802_11N],
            capabilities={
                DriverCapability.MONITOR_MODE,
                DriverCapability.PACKET_INJECTION
            },
            firmware_required=True,
            firmware_files=["rt2870.bin"]
        )
        
        rt2x00_driver = DriverInfo(
            name="rt2x00",
            family="rt2x00",
            vendor="Ralink",
            description="Ralink/MediaTek wireless driver",
            kernel_module="rt2x00lib",
            supported_chipsets=[rt5370],
            dependencies=["mac80211", "cfg80211"],
            conflicts=[],
            min_kernel_version="3.10",
            max_kernel_version=None,
            android_compatible=True,
            capabilities={
                DriverCapability.MONITOR_MODE,
                DriverCapability.PACKET_INJECTION
            },
            config_options={
                "CONFIG_RT2X00": "m",
                "CONFIG_RT2X00_DEBUG": "y"
            }
        )
        
        self.drivers["rt2x00"] = rt2x00_driver
        for chipset in rt2x00_driver.supported_chipsets:
            self.chipsets[chipset.model] = chipset
    
    def save_registry(self):
        """Save the registry to YAML file"""
        data = {
            'drivers': {}
        }
        
        for driver_name, driver in self.drivers.items():
            driver_dict = asdict(driver)
            # Convert enums and sets to serializable formats
            for chipset in driver_dict['supported_chipsets']:
                chipset['capabilities'] = [cap.value for cap in chipset['capabilities']]
                chipset['standards'] = [std.value for std in chipset['standards']]
            driver_dict['capabilities'] = [cap.value for cap in driver_dict['capabilities']]
            data['drivers'][driver_name] = driver_dict
        
        with open(self.registry_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, indent=2)
    
    def get_driver(self, name: str) -> Optional[DriverInfo]:
        """Get driver information by name"""
        return self.drivers.get(name)
    
    def get_chipset(self, model: str) -> Optional[ChipsetInfo]:
        """Get chipset information by model"""
        return self.chipsets.get(model)
    
    def list_drivers(self) -> List[str]:
        """List all available drivers"""
        return list(self.drivers.keys())
    
    def list_chipsets(self) -> List[str]:
        """List all available chipsets"""
        return list(self.chipsets.keys())
    
    def find_drivers_by_capability(self, capability: DriverCapability) -> List[DriverInfo]:
        """Find drivers that support a specific capability"""
        return [driver for driver in self.drivers.values() 
                if capability in driver.capabilities]
    
    def find_chipsets_by_capability(self, capability: DriverCapability) -> List[ChipsetInfo]:
        """Find chipsets that support a specific capability"""
        return [chipset for chipset in self.chipsets.values() 
                if capability in chipset.capabilities]
    
    def validate_driver_compatibility(self, driver_name: str, kernel_version: str) -> bool:
        """Validate if a driver is compatible with a kernel version"""
        driver = self.get_driver(driver_name)
        if not driver:
            return False
        
        # Simple version comparison (should be enhanced for production)
        min_version = driver.min_kernel_version
        max_version = driver.max_kernel_version
        
        if min_version and kernel_version < min_version:
            return False
        if max_version and kernel_version > max_version:
            return False
        
        return True
    
    def check_driver_conflicts(self, driver_names: List[str]) -> List[str]:
        """Check for conflicts between multiple drivers"""
        conflicts = []
        
        for i, driver1_name in enumerate(driver_names):
            driver1 = self.get_driver(driver1_name)
            if not driver1:
                continue
                
            for j, driver2_name in enumerate(driver_names[i+1:], i+1):
                driver2 = self.get_driver(driver2_name)
                if not driver2:
                    continue
                
                if driver2_name in driver1.conflicts or driver1_name in driver2.conflicts:
                    conflicts.append(f"{driver1_name} conflicts with {driver2_name}")
        
        return conflicts

def main():
    """Main function for testing the registry"""
    registry = WirelessDriverRegistry()
    
    print("Wireless Driver Registry")
    print("=" * 50)
    
    print(f"Available drivers: {', '.join(registry.list_drivers())}")
    print(f"Available chipsets: {', '.join(registry.list_chipsets())}")
    
    # Test capability search
    monitor_drivers = registry.find_drivers_by_capability(DriverCapability.MONITOR_MODE)
    print(f"\nDrivers with monitor mode: {[d.name for d in monitor_drivers]}")
    
    # Test compatibility
    print(f"\nath11k compatible with kernel 4.19: {registry.validate_driver_compatibility('ath11k', '4.19')}")
    print(f"ath11k compatible with kernel 3.10: {registry.validate_driver_compatibility('ath11k', '3.10')}")
    
    # Test conflicts
    conflicts = registry.check_driver_conflicts(['ath11k', 'ath10k'])
    if conflicts:
        print(f"\nConflicts found: {conflicts}")
    else:
        print("\nNo conflicts found between ath11k and ath10k")

if __name__ == "__main__":
    main()