#!/usr/bin/env python3
"""
Enhanced Wireless Driver Dependency Resolution System

This module extends the existing backports dependency resolution to handle
wireless-specific dependencies, firmware requirements, crypto modules,
regulatory databases, and driver coexistence validation.
"""

import os
import sys
import json
import yaml
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Add the scripts directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from wireless_driver_registry import WirelessDriverRegistry, DriverCapability
    from resolve_backports_deps import BackportsDependencyResolver
except ImportError as e:
    print(f"Warning: Could not import required modules: {e}")
    # Create minimal fallback classes
    class WirelessDriverRegistry:
        def __init__(self): pass
        def list_drivers(self): return []
        def get_driver(self, name): return None
    class BackportsDependencyResolver:
        def __init__(self, kernel_root): pass

class DependencyType(Enum):
    """Types of dependencies"""
    KERNEL_MODULE = "kernel_module"
    CRYPTO_MODULE = "crypto_module"
    FIRMWARE_FILE = "firmware_file"
    REGULATORY_DB = "regulatory_db"
    KERNEL_CONFIG = "kernel_config"
    USERSPACE_TOOL = "userspace_tool"

@dataclass
class WirelessDependency:
    """Represents a wireless driver dependency"""
    name: str
    type: DependencyType
    required: bool
    description: str
    config_option: Optional[str] = None
    module_name: Optional[str] = None
    file_path: Optional[str] = None
    version_min: Optional[str] = None
    alternatives: List[str] = None
    
    def __post_init__(self):
        if self.alternatives is None:
            self.alternatives = []

class WirelessDependencyResolver:
    """Enhanced dependency resolver for wireless drivers"""
    
    def __init__(self, kernel_root: str = "."):
        """Initialize the wireless dependency resolver"""
        self.kernel_root = Path(kernel_root).resolve()
        self.registry = WirelessDriverRegistry()
        self.base_resolver = BackportsDependencyResolver(kernel_root)
        
        # Wireless-specific dependency definitions
        self.wireless_dependencies = self._load_wireless_dependencies()
        
        # Crypto module mappings for wireless security
        self.crypto_mappings = {
            "wpa3": ["CONFIG_CRYPTO_CMAC", "CONFIG_CRYPTO_CCMP", "CONFIG_CRYPTO_GCMP"],
            "sae": ["CONFIG_CRYPTO_CMAC", "CONFIG_CRYPTO_SHA256"],
            "owe": ["CONFIG_CRYPTO_ECDH", "CONFIG_CRYPTO_SHA256"],
            "wpa2": ["CONFIG_CRYPTO_AES", "CONFIG_CRYPTO_ARC4", "CONFIG_CRYPTO_CCMP"],
            "wep": ["CONFIG_CRYPTO_ARC4", "CONFIG_CRYPTO_ECB"],
            "tkip": ["CONFIG_CRYPTO_MICHAEL_MIC", "CONFIG_CRYPTO_ARC4"]
        }
        
        # Firmware path mappings
        self.firmware_paths = {
            "ath11k": "/lib/firmware/ath11k/",
            "ath10k": "/lib/firmware/ath10k/",
            "iwlwifi": "/lib/firmware/",
            "rt2x00": "/lib/firmware/"
        }
        
        # Regulatory database requirements
        self.regulatory_requirements = {
            "wireless-regdb": {
                "files": ["/lib/firmware/regulatory.db", "/lib/firmware/regulatory.db.p7s"],
                "config": ["CONFIG_CFG80211_CRDA_SUPPORT"],
                "description": "Wireless regulatory database"
            }
        }
    
    def _load_wireless_dependencies(self) -> Dict[str, List[WirelessDependency]]:
        """Load wireless driver dependency definitions"""
        dependencies = {
            "ath11k": [
                WirelessDependency(
                    name="mac80211",
                    type=DependencyType.KERNEL_MODULE,
                    required=True,
                    description="IEEE 802.11 networking stack",
                    config_option="CONFIG_BACKPORTS_MAC80211",
                    module_name="mac80211"
                ),
                WirelessDependency(
                    name="cfg80211",
                    type=DependencyType.KERNEL_MODULE,
                    required=True,
                    description="Wireless configuration API",
                    config_option="CONFIG_BACKPORTS_CFG80211",
                    module_name="cfg80211"
                ),
                WirelessDependency(
                    name="crypto_aes",
                    type=DependencyType.CRYPTO_MODULE,
                    required=True,
                    description="AES encryption for wireless security",
                    config_option="CONFIG_CRYPTO_AES",
                    module_name="aes_generic"
                ),
                WirelessDependency(
                    name="crypto_cmac",
                    type=DependencyType.CRYPTO_MODULE,
                    required=False,
                    description="CMAC for WPA3 support",
                    config_option="CONFIG_CRYPTO_CMAC",
                    module_name="cmac"
                ),
                WirelessDependency(
                    name="ath11k_firmware",
                    type=DependencyType.FIRMWARE_FILE,
                    required=True,
                    description="ath11k firmware files",
                    file_path="/lib/firmware/ath11k/"
                ),
                WirelessDependency(
                    name="regulatory_db",
                    type=DependencyType.REGULATORY_DB,
                    required=True,
                    description="Wireless regulatory database",
                    file_path="/lib/firmware/regulatory.db"
                )
            ],
            "ath10k": [
                WirelessDependency(
                    name="mac80211",
                    type=DependencyType.KERNEL_MODULE,
                    required=True,
                    description="IEEE 802.11 networking stack",
                    config_option="CONFIG_BACKPORTS_MAC80211",
                    module_name="mac80211"
                ),
                WirelessDependency(
                    name="cfg80211",
                    type=DependencyType.KERNEL_MODULE,
                    required=True,
                    description="Wireless configuration API",
                    config_option="CONFIG_BACKPORTS_CFG80211",
                    module_name="cfg80211"
                ),
                WirelessDependency(
                    name="crypto_aes",
                    type=DependencyType.CRYPTO_MODULE,
                    required=True,
                    description="AES encryption for wireless security",
                    config_option="CONFIG_CRYPTO_AES",
                    module_name="aes_generic"
                ),
                WirelessDependency(
                    name="ath10k_firmware",
                    type=DependencyType.FIRMWARE_FILE,
                    required=True,
                    description="ath10k firmware files",
                    file_path="/lib/firmware/ath10k/"
                )
            ],
            "iwlwifi": [
                WirelessDependency(
                    name="mac80211",
                    type=DependencyType.KERNEL_MODULE,
                    required=True,
                    description="IEEE 802.11 networking stack",
                    config_option="CONFIG_BACKPORTS_MAC80211",
                    module_name="mac80211"
                ),
                WirelessDependency(
                    name="cfg80211",
                    type=DependencyType.KERNEL_MODULE,
                    required=True,
                    description="Wireless configuration API",
                    config_option="CONFIG_BACKPORTS_CFG80211",
                    module_name="cfg80211"
                ),
                WirelessDependency(
                    name="iwlwifi_firmware",
                    type=DependencyType.FIRMWARE_FILE,
                    required=True,
                    description="Intel wireless firmware files",
                    file_path="/lib/firmware/"
                )
            ],
            "rt2x00": [
                WirelessDependency(
                    name="mac80211",
                    type=DependencyType.KERNEL_MODULE,
                    required=True,
                    description="IEEE 802.11 networking stack",
                    config_option="CONFIG_BACKPORTS_MAC80211",
                    module_name="mac80211"
                ),
                WirelessDependency(
                    name="cfg80211",
                    type=DependencyType.KERNEL_MODULE,
                    required=True,
                    description="Wireless configuration API",
                    config_option="CONFIG_BACKPORTS_CFG80211",
                    module_name="cfg80211"
                ),
                WirelessDependency(
                    name="rt2x00_firmware",
                    type=DependencyType.FIRMWARE_FILE,
                    required=True,
                    description="Ralink/MediaTek firmware files",
                    file_path="/lib/firmware/"
                )
            ]
        }
        
        return dependencies
    
    def resolve_wireless_dependencies(self, driver_names: List[str]) -> Dict[str, List[WirelessDependency]]:
        """Resolve dependencies for specified wireless drivers"""
        resolved_deps = {}
        
        for driver_name in driver_names:
            if driver_name in self.wireless_dependencies:
                resolved_deps[driver_name] = self.wireless_dependencies[driver_name].copy()
            else:
                print(f"Warning: No dependency information for driver {driver_name}")
                resolved_deps[driver_name] = []
        
        return resolved_deps
    
    def get_crypto_dependencies(self, security_features: List[str]) -> List[str]:
        """Get crypto module dependencies for security features"""
        crypto_configs = set()
        
        for feature in security_features:
            if feature.lower() in self.crypto_mappings:
                crypto_configs.update(self.crypto_mappings[feature.lower()])
        
        return list(crypto_configs)
    
    def validate_firmware_dependencies(self, driver_names: List[str]) -> Dict[str, Dict[str, bool]]:
        """Validate firmware dependencies for drivers"""
        firmware_status = {}
        
        for driver_name in driver_names:
            firmware_status[driver_name] = {}
            
            # Get driver info from registry
            driver = self.registry.get_driver(driver_name)
            if not driver:
                firmware_status[driver_name]["registry_found"] = False
                continue
            
            firmware_status[driver_name]["registry_found"] = True
            firmware_status[driver_name]["firmware_required"] = any(
                chipset.firmware_required for chipset in driver.supported_chipsets
            )
            
            # Check firmware files
            firmware_files = []
            for chipset in driver.supported_chipsets:
                firmware_files.extend(chipset.firmware_files)
            
            firmware_status[driver_name]["firmware_files"] = {}
            for fw_file in firmware_files:
                fw_path = Path("/lib/firmware") / fw_file
                firmware_status[driver_name]["firmware_files"][fw_file] = fw_path.exists()
        
        return firmware_status
    
    def validate_regulatory_dependencies(self) -> Dict[str, bool]:
        """Validate regulatory database dependencies"""
        regulatory_status = {}
        
        for name, req in self.regulatory_requirements.items():
            regulatory_status[name] = {}
            
            # Check files
            regulatory_status[name]["files"] = {}
            for file_path in req["files"]:
                regulatory_status[name]["files"][file_path] = Path(file_path).exists()
            
            # Check config options (would need to read kernel config)
            regulatory_status[name]["config_available"] = True  # Simplified for now
        
        return regulatory_status
    
    def check_driver_coexistence(self, driver_names: List[str]) -> Dict[str, List[str]]:
        """Check for driver coexistence issues"""
        conflicts = {}
        
        for i, driver1 in enumerate(driver_names):
            conflicts[driver1] = []
            
            driver1_info = self.registry.get_driver(driver1)
            if not driver1_info:
                continue
            
            for j, driver2 in enumerate(driver_names):
                if i >= j:  # Avoid duplicate checks
                    continue
                
                driver2_info = self.registry.get_driver(driver2)
                if not driver2_info:
                    continue
                
                # Check explicit conflicts
                if driver2 in driver1_info.conflicts:
                    conflicts[driver1].append(f"Explicit conflict with {driver2}")
                
                # Check chipset conflicts (same chipset supported by multiple drivers)
                driver1_chipsets = {chipset.model for chipset in driver1_info.supported_chipsets}
                driver2_chipsets = {chipset.model for chipset in driver2_info.supported_chipsets}
                
                common_chipsets = driver1_chipsets.intersection(driver2_chipsets)
                if common_chipsets:
                    conflicts[driver1].append(f"Chipset conflict with {driver2}: {', '.join(common_chipsets)}")
        
        return conflicts
    
    def generate_dependency_report(self, driver_names: List[str]) -> Dict:
        """Generate comprehensive dependency report"""
        report = {
            "drivers": driver_names,
            "dependencies": {},
            "crypto_requirements": {},
            "firmware_status": {},
            "regulatory_status": {},
            "conflicts": {},
            "recommendations": []
        }
        
        # Resolve dependencies
        report["dependencies"] = self.resolve_wireless_dependencies(driver_names)
        
        # Get crypto requirements
        security_features = ["wpa2", "wpa3", "sae", "owe"]  # Common features
        report["crypto_requirements"] = {
            "features": security_features,
            "config_options": self.get_crypto_dependencies(security_features)
        }
        
        # Validate firmware
        report["firmware_status"] = self.validate_firmware_dependencies(driver_names)
        
        # Validate regulatory
        report["regulatory_status"] = self.validate_regulatory_dependencies()
        
        # Check conflicts
        report["conflicts"] = self.check_driver_coexistence(driver_names)
        
        # Generate recommendations
        report["recommendations"] = self._generate_recommendations(report)
        
        return report
    
    def _generate_recommendations(self, report: Dict) -> List[str]:
        """Generate recommendations based on dependency analysis"""
        recommendations = []
        
        # Check for missing firmware
        for driver, fw_status in report["firmware_status"].items():
            if fw_status.get("firmware_required", False):
                missing_fw = [fw for fw, exists in fw_status.get("firmware_files", {}).items() if not exists]
                if missing_fw:
                    recommendations.append(f"Install missing firmware for {driver}: {', '.join(missing_fw)}")
        
        # Check for conflicts
        for driver, conflicts in report["conflicts"].items():
            if conflicts:
                recommendations.append(f"Resolve conflicts for {driver}: {'; '.join(conflicts)}")
        
        # Check regulatory database
        reg_status = report["regulatory_status"]
        for name, status in reg_status.items():
            missing_files = [path for path, exists in status.get("files", {}).items() if not exists]
            if missing_files:
                recommendations.append(f"Install regulatory database files: {', '.join(missing_files)}")
        
        return recommendations
    
    def create_wireless_config(self, driver_names: List[str], features: List[str] = None) -> Dict[str, str]:
        """Create wireless driver configuration"""
        if features is None:
            features = ["monitor_mode", "wpa3"]
        
        config = {}
        
        # Enable base backports
        config["CONFIG_BACKPORTS"] = "y"
        config["CONFIG_BACKPORTS_WIRELESS_DRIVERS"] = "y"
        
        # Enable wireless stack
        config["CONFIG_BACKPORTS_CFG80211"] = "m"
        config["CONFIG_BACKPORTS_MAC80211"] = "m"
        config["CONFIG_BACKPORTS_WIRELESS_REGULATORY"] = "y"
        
        # Enable crypto for security features
        crypto_deps = self.get_crypto_dependencies(features)
        for crypto_config in crypto_deps:
            config[crypto_config] = "y"
        
        # Enable specific drivers
        for driver_name in driver_names:
            if driver_name == "ath11k":
                config["CONFIG_BACKPORTS_ATH_DRIVERS"] = "y"
                config["CONFIG_BACKPORTS_ATH11K"] = "m"
                config["CONFIG_BACKPORTS_ATH11K_DEBUG"] = "y"
                config["CONFIG_BACKPORTS_ATH11K_DEBUGFS"] = "y"
            elif driver_name == "ath10k":
                config["CONFIG_BACKPORTS_ATH_DRIVERS"] = "y"
                config["CONFIG_BACKPORTS_ATH10K"] = "m"
                config["CONFIG_BACKPORTS_ATH10K_DEBUG"] = "y"
                config["CONFIG_BACKPORTS_ATH10K_DEBUGFS"] = "y"
            elif driver_name == "iwlwifi":
                config["CONFIG_BACKPORTS_IWLWIFI"] = "m"
                config["CONFIG_BACKPORTS_IWLWIFI_DEBUG"] = "y"
            elif driver_name == "rt2x00":
                config["CONFIG_BACKPORTS_RT2X00"] = "m"
                config["CONFIG_BACKPORTS_RT2X00_DEBUG"] = "y"
        
        # Enable features
        if "monitor_mode" in features:
            config["CONFIG_BACKPORTS_MONITOR_MODE"] = "y"
            config["CONFIG_BACKPORTS_WIRELESS_MONITOR_ENHANCED"] = "y"
        
        if "packet_injection" in features:
            config["CONFIG_BACKPORTS_FRAME_INJECTION"] = "y"
            config["CONFIG_BACKPORTS_WIRELESS_INJECTION_ENHANCED"] = "y"
        
        if "mesh_networking" in features:
            config["CONFIG_BACKPORTS_MAC80211_MESH"] = "y"
            config["CONFIG_BACKPORTS_WIRELESS_MESH"] = "y"
            config["CONFIG_BACKPORTS_WIRELESS_MESH_ENHANCED"] = "y"
        
        return config
    
    def save_dependency_report(self, report: Dict, output_file: str):
        """Save dependency report to file"""
        output_path = Path(output_file)
        
        try:
            if output_path.suffix.lower() == '.json':
                with open(output_path, 'w') as f:
                    json.dump(report, f, indent=2, default=str)
            else:
                with open(output_path, 'w') as f:
                    yaml.dump(report, f, default_flow_style=False, indent=2)
            
            print(f"Dependency report saved to: {output_path}")
        except Exception as e:
            print(f"Error saving report: {e}")

def main():
    """Main function for testing"""
    resolver = WirelessDependencyResolver()
    
    print("Wireless Dependency Resolution System")
    print("=" * 50)
    
    # Test with common drivers
    test_drivers = ["ath11k", "ath10k", "iwlwifi"]
    test_features = ["monitor_mode", "wpa3", "packet_injection"]
    
    print(f"Testing with drivers: {', '.join(test_drivers)}")
    print(f"Testing with features: {', '.join(test_features)}")
    print()
    
    # Generate dependency report
    report = resolver.generate_dependency_report(test_drivers)
    
    print("Dependency Analysis Results:")
    print("-" * 30)
    
    # Show crypto requirements
    crypto_reqs = report["crypto_requirements"]
    print(f"Crypto modules needed: {len(crypto_reqs['config_options'])}")
    for config in crypto_reqs["config_options"]:
        print(f"  - {config}")
    
    # Show firmware status
    print(f"\nFirmware Status:")
    for driver, status in report["firmware_status"].items():
        print(f"  {driver}: Registry found: {status.get('registry_found', False)}")
        if status.get("firmware_required", False):
            print(f"    Firmware required: Yes")
            fw_files = status.get("firmware_files", {})
            for fw_file, exists in fw_files.items():
                status_str = "✓" if exists else "✗"
                print(f"    {status_str} {fw_file}")
    
    # Show conflicts
    print(f"\nDriver Conflicts:")
    conflicts_found = False
    for driver, conflicts in report["conflicts"].items():
        if conflicts:
            conflicts_found = True
            print(f"  {driver}:")
            for conflict in conflicts:
                print(f"    - {conflict}")
    
    if not conflicts_found:
        print("  No conflicts detected")
    
    # Show recommendations
    print(f"\nRecommendations:")
    if report["recommendations"]:
        for rec in report["recommendations"]:
            print(f"  - {rec}")
    else:
        print("  No specific recommendations")
    
    # Generate configuration
    print(f"\nGenerated Configuration:")
    config = resolver.create_wireless_config(test_drivers, test_features)
    for option, value in sorted(config.items()):
        print(f"  {option}={value}")

if __name__ == "__main__":
    main()