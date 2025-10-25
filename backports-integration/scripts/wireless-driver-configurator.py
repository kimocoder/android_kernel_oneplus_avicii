#!/usr/bin/env python3
"""
Interactive Wireless Driver Configuration Wizard

This script provides an interactive wizard for configuring wireless drivers
with guided setup, validation, and configuration management.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import time

@dataclass
class WirelessConfig:
    """Wireless driver configuration"""
    timestamp: str
    use_case: str
    driver: str
    chipset: str
    regulatory_domain: str
    features: List[str]
    advanced_options: Dict[str, any]
    build_options: Dict[str, any]

class WirelessDriverConfigurator:
    """Interactive wireless driver configuration wizard"""
    
    def __init__(self, kernel_root: str = "."):
        """Initialize configurator"""
        self.kernel_root = Path(kernel_root).resolve()
        self.backports_dir = self.kernel_root / "backports-integration"
        self.config_dir = self.backports_dir / "configs"
        self.scripts_dir = self.backports_dir / "scripts"
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load driver database
        self.driver_db = self._load_driver_database()
        
        # Load use case templates
        self.use_case_templates = self._load_use_case_templates()
    
    def _load_driver_database(self) -> Dict:
        """Load driver database with capabilities and requirements"""
        return {
            "ath11k": {
                "name": "Qualcomm Atheros 11ac/11ax",
                "description": "Modern Qualcomm wireless driver for WiFi 6/6E",
                "chipsets": {
                    "QCA6390": {
                        "name": "QCA6390 (Common in laptops)",
                        "wifi_standard": "WiFi 6",
                        "bands": ["2.4GHz", "5GHz"],
                        "max_streams": "2x2"
                    },
                    "QCA6490": {
                        "name": "QCA6490 (Newer laptops)",
                        "wifi_standard": "WiFi 6",
                        "bands": ["2.4GHz", "5GHz"],
                        "max_streams": "2x2"
                    },
                    "WCN6855": {
                        "name": "WCN6855 (Latest generation)",
                        "wifi_standard": "WiFi 6E",
                        "bands": ["2.4GHz", "5GHz", "6GHz"],
                        "max_streams": "2x2"
                    },
                    "QCN9074": {
                        "name": "QCN9074 (Enterprise/AP)",
                        "wifi_standard": "WiFi 6",
                        "bands": ["2.4GHz", "5GHz"],
                        "max_streams": "4x4"
                    }
                },
                "features": ["monitor_mode", "packet_injection", "mesh_networking", "dfs_support"],
                "firmware_required": True,
                "regulatory_enforcement": True
            },
            "ath10k": {
                "name": "Qualcomm Atheros 11ac",
                "description": "Mature Qualcomm wireless driver for WiFi 5",
                "chipsets": {
                    "QCA988X": {
                        "name": "QCA988X (PCIe cards)",
                        "wifi_standard": "WiFi 5",
                        "bands": ["2.4GHz", "5GHz"],
                        "max_streams": "3x3"
                    },
                    "QCA6174": {
                        "name": "QCA6174 (Laptops)",
                        "wifi_standard": "WiFi 5",
                        "bands": ["2.4GHz", "5GHz"],
                        "max_streams": "2x2"
                    },
                    "QCA9377": {
                        "name": "QCA9377 (USB adapters)",
                        "wifi_standard": "WiFi 5",
                        "bands": ["2.4GHz", "5GHz"],
                        "max_streams": "1x1"
                    }
                },
                "features": ["monitor_mode", "packet_injection", "mesh_networking", "dfs_support"],
                "firmware_required": True,
                "regulatory_enforcement": True
            },
            "iwlwifi": {
                "name": "Intel Wireless",
                "description": "Intel wireless driver with enterprise features",
                "chipsets": {
                    "AX200": {
                        "name": "AX200 (WiFi 6)",
                        "wifi_standard": "WiFi 6",
                        "bands": ["2.4GHz", "5GHz"],
                        "max_streams": "2x2"
                    },
                    "AX210": {
                        "name": "AX210 (WiFi 6E)",
                        "wifi_standard": "WiFi 6E",
                        "bands": ["2.4GHz", "5GHz", "6GHz"],
                        "max_streams": "2x2"
                    },
                    "AC9560": {
                        "name": "AC9560 (WiFi 5)",
                        "wifi_standard": "WiFi 5",
                        "bands": ["2.4GHz", "5GHz"],
                        "max_streams": "2x2"
                    }
                },
                "features": ["monitor_mode", "enterprise_security", "power_management"],
                "firmware_required": True,
                "regulatory_enforcement": True
            },
            "rt2x00": {
                "name": "Ralink/MediaTek",
                "description": "Ralink/MediaTek driver family for USB adapters",
                "chipsets": {
                    "RT3070": {
                        "name": "RT3070 (Common USB)",
                        "wifi_standard": "WiFi 4",
                        "bands": ["2.4GHz"],
                        "max_streams": "1x1"
                    },
                    "RT5370": {
                        "name": "RT5370 (Newer USB)",
                        "wifi_standard": "WiFi 4",
                        "bands": ["2.4GHz"],
                        "max_streams": "1x1"
                    }
                },
                "features": ["monitor_mode", "packet_injection"],
                "firmware_required": True,
                "regulatory_enforcement": False
            },
            "rtw88": {
                "name": "Realtek RTW88",
                "description": "Modern Realtek wireless driver for 802.11ac USB adapters",
                "chipsets": {
                    "RTL8822B": {
                        "name": "RTL8822B (USB/PCIe 802.11ac 2x2)",
                        "wifi_standard": "WiFi 5",
                        "bands": ["2.4GHz", "5GHz"],
                        "max_streams": "2x2"
                    },
                    "RTL8822C": {
                        "name": "RTL8822C (USB/PCIe 802.11ac 2x2)",
                        "wifi_standard": "WiFi 5",
                        "bands": ["2.4GHz", "5GHz"],
                        "max_streams": "2x2"
                    },
                    "RTL8821C": {
                        "name": "RTL8821C (USB/PCIe 802.11ac 1x1)",
                        "wifi_standard": "WiFi 5",
                        "bands": ["2.4GHz", "5GHz"],
                        "max_streams": "1x1"
                    },
                    "RTL8723D": {
                        "name": "RTL8723D (USB 802.11n 1x1 + BT)",
                        "wifi_standard": "WiFi 4",
                        "bands": ["2.4GHz"],
                        "max_streams": "1x1"
                    }
                },
                "features": ["monitor_mode", "packet_injection", "mesh_networking", "dfs_support"],
                "firmware_required": True,
                "regulatory_enforcement": True
            },
            "mt76": {
                "name": "MediaTek MT76",
                "description": "MediaTek MT76 driver family for USB 802.11ac adapters",
                "chipsets": {
                    "MT7601U": {
                        "name": "MT7601U (USB 802.11n 1x1)",
                        "wifi_standard": "WiFi 4",
                        "bands": ["2.4GHz"],
                        "max_streams": "1x1"
                    },
                    "MT7610U": {
                        "name": "MT7610U (USB 802.11ac 1x1)",
                        "wifi_standard": "WiFi 5",
                        "bands": ["2.4GHz", "5GHz"],
                        "max_streams": "1x1"
                    },
                    "MT7612U": {
                        "name": "MT7612U (USB 802.11ac 2x2)",
                        "wifi_standard": "WiFi 5",
                        "bands": ["2.4GHz", "5GHz"],
                        "max_streams": "2x2"
                    },
                    "MT7663U": {
                        "name": "MT7663U (USB 802.11ac 2x2)",
                        "wifi_standard": "WiFi 5",
                        "bands": ["2.4GHz", "5GHz"],
                        "max_streams": "2x2"
                    },
                    "MT7921U": {
                        "name": "MT7921U (USB 802.11ax 2x2)",
                        "wifi_standard": "WiFi 6",
                        "bands": ["2.4GHz", "5GHz"],
                        "max_streams": "2x2"
                    }
                },
                "features": ["monitor_mode", "packet_injection", "mesh_networking", "dfs_support"],
                "firmware_required": True,
                "regulatory_enforcement": True
            },
            "rtw88": {
                "name": "Realtek RTW88",
                "description": "Realtek RTW88 driver family for USB and PCIe adapters",
                "chipsets": {
                    "RTL8822B": {
                        "name": "RTL8822B (USB/PCIe 802.11ac 2x2)",
                        "wifi_standard": "WiFi 5",
                        "bands": ["2.4GHz", "5GHz"],
                        "max_streams": "2x2"
                    },
                    "RTL8822C": {
                        "name": "RTL8822C (USB/PCIe 802.11ac 2x2)",
                        "wifi_standard": "WiFi 5",
                        "bands": ["2.4GHz", "5GHz"],
                        "max_streams": "2x2"
                    },
                    "RTL8821C": {
                        "name": "RTL8821C (USB/PCIe 802.11ac 1x1)",
                        "wifi_standard": "WiFi 5",
                        "bands": ["2.4GHz", "5GHz"],
                        "max_streams": "1x1"
                    },
                    "RTL8723D": {
                        "name": "RTL8723D (USB 802.11n 1x1 + BT)",
                        "wifi_standard": "WiFi 4",
                        "bands": ["2.4GHz"],
                        "max_streams": "1x1"
                    }
                },
                "features": ["monitor_mode", "packet_injection"],
                "firmware_required": True,
                "regulatory_enforcement": True
            },
            "mt76": {
                "name": "MediaTek MT76",
                "description": "MediaTek MT76 driver family for USB adapters",
                "chipsets": {
                    "MT7601U": {
                        "name": "MT7601U (USB 802.11n 1x1)",
                        "wifi_standard": "WiFi 4",
                        "bands": ["2.4GHz"],
                        "max_streams": "1x1"
                    },
                    "MT7610U": {
                        "name": "MT7610U (USB 802.11ac 1x1)",
                        "wifi_standard": "WiFi 5",
                        "bands": ["2.4GHz", "5GHz"],
                        "max_streams": "1x1"
                    },
                    "MT7612U": {
                        "name": "MT7612U (USB 802.11ac 2x2)",
                        "wifi_standard": "WiFi 5",
                        "bands": ["2.4GHz", "5GHz"],
                        "max_streams": "2x2"
                    },
                    "MT7663U": {
                        "name": "MT7663U (USB 802.11ac 2x2)",
                        "wifi_standard": "WiFi 5",
                        "bands": ["2.4GHz", "5GHz"],
                        "max_streams": "2x2"
                    },
                    "MT7921U": {
                        "name": "MT7921U (USB 802.11ax 2x2)",
                        "wifi_standard": "WiFi 6",
                        "bands": ["2.4GHz", "5GHz"],
                        "max_streams": "2x2"
                    }
                },
                "features": ["monitor_mode", "packet_injection", "mesh_networking"],
                "firmware_required": True,
                "regulatory_enforcement": True
            }
        }
    
    def _load_use_case_templates(self) -> Dict:
        """Load use case configuration templates"""
        return {
            "laptop": {
                "name": "Laptop/Desktop",
                "description": "Standard wireless usage for laptops and desktops",
                "recommended_drivers": ["ath11k", "iwlwifi", "ath10k"],
                "features": ["standard"],
                "regulatory_strict": True,
                "power_management": True
            },
            "security_research": {
                "name": "Security Research",
                "description": "Monitor mode and packet injection for security research",
                "recommended_drivers": ["ath11k", "ath10k", "rt2x00"],
                "features": ["monitor_mode", "packet_injection"],
                "regulatory_strict": False,
                "power_management": False,
                "warnings": [
                    "Monitor mode requires proper authorization",
                    "Packet injection must comply with regulations",
                    "Use only in authorized environments"
                ]
            },
            "mesh_networking": {
                "name": "Mesh Networking",
                "description": "Mesh networking and ad-hoc networks",
                "recommended_drivers": ["ath11k", "ath10k"],
                "features": ["mesh_networking"],
                "regulatory_strict": True,
                "power_management": False
            },
            "enterprise": {
                "name": "Enterprise",
                "description": "Enterprise wireless with security features",
                "recommended_drivers": ["iwlwifi", "ath11k"],
                "features": ["enterprise_security", "power_management"],
                "regulatory_strict": True,
                "power_management": True
            },
            "embedded": {
                "name": "Embedded System",
                "description": "Minimal configuration for embedded systems",
                "recommended_drivers": ["rt2x00", "ath10k"],
                "features": ["minimal"],
                "regulatory_strict": True,
                "power_management": True
            }
        }
    
    def run_interactive_setup(self) -> WirelessConfig:
        """Run interactive configuration wizard"""
        print("=" * 60)
        print("🛜  Wireless Driver Configuration Wizard")
        print("=" * 60)
        print()
        
        # Step 1: Use case selection
        use_case = self._select_use_case()
        template = self.use_case_templates[use_case]
        
        # Step 2: Driver selection
        driver = self._select_driver(template["recommended_drivers"])
        
        # Step 3: Chipset selection
        chipset = self._select_chipset(driver)
        
        # Step 4: Regulatory domain
        regulatory_domain = self._select_regulatory_domain()
        
        # Step 5: Feature configuration
        features = self._configure_features(driver, template["features"])
        
        # Step 6: Advanced options
        advanced_options = self._configure_advanced_options(driver, use_case)
        
        # Step 7: Build options
        build_options = self._configure_build_options()
        
        # Create configuration
        config = WirelessConfig(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            use_case=use_case,
            driver=driver,
            chipset=chipset,
            regulatory_domain=regulatory_domain,
            features=features,
            advanced_options=advanced_options,
            build_options=build_options
        )
        
        # Step 8: Review and confirm
        if self._review_configuration(config):
            return config
        else:
            print("Configuration cancelled by user")
            sys.exit(0)
    
    def _select_use_case(self) -> str:
        """Select use case with guided questions"""
        print("📋 Step 1: Select Your Use Case")
        print("-" * 30)
        
        # Show use case options
        use_cases = list(self.use_case_templates.keys())
        
        for i, use_case in enumerate(use_cases, 1):
            template = self.use_case_templates[use_case]
            print(f"{i}) {template['name']}")
            print(f"   {template['description']}")
            print()
        
        while True:
            try:
                choice = int(input(f"Enter choice (1-{len(use_cases)}): "))
                if 1 <= choice <= len(use_cases):
                    selected = use_cases[choice - 1]
                    
                    # Show warnings if any
                    template = self.use_case_templates[selected]
                    if "warnings" in template:
                        print("\n⚠️  Important Warnings:")
                        for warning in template["warnings"]:
                            print(f"   • {warning}")
                        
                        confirm = input("\nDo you understand and accept these warnings? (y/N): ")
                        if confirm.lower() != 'y':
                            continue
                    
                    return selected
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a valid number.")
    
    def _select_driver(self, recommended_drivers: List[str]) -> str:
        """Select wireless driver"""
        print("\n🔧 Step 2: Select Wireless Driver")
        print("-" * 30)
        
        # Show recommended drivers first
        print("Recommended drivers for your use case:")
        for i, driver in enumerate(recommended_drivers, 1):
            driver_info = self.driver_db[driver]
            print(f"{i}) {driver_info['name']}")
            print(f"   {driver_info['description']}")
            print()
        
        # Show all drivers
        all_drivers = list(self.driver_db.keys())
        print("All available drivers:")
        for i, driver in enumerate(all_drivers, 1):
            driver_info = self.driver_db[driver]
            recommended = "⭐" if driver in recommended_drivers else "  "
            print(f"{recommended} {i}) {driver} - {driver_info['name']}")
        
        print()
        
        while True:
            try:
                choice = int(input(f"Enter choice (1-{len(all_drivers)}): "))
                if 1 <= choice <= len(all_drivers):
                    return all_drivers[choice - 1]
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a valid number.")
    
    def _select_chipset(self, driver: str) -> str:
        """Select chipset variant"""
        print(f"\n💾 Step 3: Select {driver.upper()} Chipset")
        print("-" * 30)
        
        driver_info = self.driver_db[driver]
        chipsets = list(driver_info["chipsets"].keys())
        
        for i, chipset in enumerate(chipsets, 1):
            chipset_info = driver_info["chipsets"][chipset]
            print(f"{i}) {chipset_info['name']}")
            print(f"   WiFi: {chipset_info['wifi_standard']}")
            print(f"   Bands: {', '.join(chipset_info['bands'])}")
            print(f"   Streams: {chipset_info['max_streams']}")
            print()
        
        while True:
            try:
                choice = int(input(f"Enter choice (1-{len(chipsets)}): "))
                if 1 <= choice <= len(chipsets):
                    return chipsets[choice - 1]
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a valid number.")
    
    def _select_regulatory_domain(self) -> str:
        """Select regulatory domain"""
        print("\n🌍 Step 4: Select Regulatory Domain")
        print("-" * 30)
        
        domains = {
            "US": "United States (FCC) - Full features available",
            "EU": "European Union (ETSI) - Packet injection restricted",
            "JP": "Japan (MKK) - Monitor mode requires authorization",
            "CA": "Canada - Similar to US with some restrictions",
            "AU": "Australia - Similar to EU regulations",
            "CN": "China - Limited features and frequencies"
        }
        
        domain_list = list(domains.keys())
        
        for i, domain in enumerate(domain_list, 1):
            print(f"{i}) {domain}: {domains[domain]}")
        
        print()
        
        while True:
            try:
                choice = int(input(f"Enter choice (1-{len(domain_list)}): "))
                if 1 <= choice <= len(domain_list):
                    selected = domain_list[choice - 1]
                    
                    # Show domain-specific warnings
                    if selected in ["EU", "JP", "CN"]:
                        print(f"\n⚠️  Note: {domains[selected]}")
                        confirm = input("Continue with this domain? (y/N): ")
                        if confirm.lower() != 'y':
                            continue
                    
                    return selected
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a valid number.")
    
    def _configure_features(self, driver: str, template_features: List[str]) -> List[str]:
        """Configure driver features"""
        print("\n⚙️  Step 5: Configure Features")
        print("-" * 30)
        
        driver_info = self.driver_db[driver]
        available_features = driver_info["features"]
        
        selected_features = []
        
        # Add template features that are available
        for feature in template_features:
            if feature in available_features or feature == "standard":
                selected_features.append(feature)
        
        print("Available features for this driver:")
        
        feature_descriptions = {
            "monitor_mode": "Monitor mode (packet capture)",
            "packet_injection": "Packet injection capabilities",
            "mesh_networking": "Mesh networking support",
            "enterprise_security": "Enterprise security features",
            "power_management": "Advanced power management",
            "dfs_support": "DFS (radar detection) support",
            "standard": "Standard wireless features",
            "minimal": "Minimal feature set"
        }
        
        for i, feature in enumerate(available_features, 1):
            description = feature_descriptions.get(feature, feature)
            selected = "✓" if feature in selected_features else " "
            print(f"[{selected}] {i}) {description}")
        
        print()
        print("Current selection based on use case:")
        for feature in selected_features:
            description = feature_descriptions.get(feature, feature)
            print(f"  ✓ {description}")
        
        print()
        modify = input("Modify feature selection? (y/N): ")
        
        if modify.lower() == 'y':
            print("\nEnter feature numbers to toggle (space-separated), or 'done':")
            
            while True:
                selection = input("Features: ").strip()
                
                if selection.lower() == 'done':
                    break
                
                try:
                    indices = [int(x) - 1 for x in selection.split()]
                    
                    for idx in indices:
                        if 0 <= idx < len(available_features):
                            feature = available_features[idx]
                            if feature in selected_features:
                                selected_features.remove(feature)
                            else:
                                selected_features.append(feature)
                    
                    # Show current selection
                    print("Current selection:")
                    for feature in selected_features:
                        description = feature_descriptions.get(feature, feature)
                        print(f"  ✓ {description}")
                    
                except ValueError:
                    print("Invalid input. Enter numbers separated by spaces.")
        
        return selected_features
    
    def _configure_advanced_options(self, driver: str, use_case: str) -> Dict[str, any]:
        """Configure advanced driver options"""
        print("\n🔬 Step 6: Advanced Options")
        print("-" * 30)
        
        options = {}
        
        # Debug options
        debug = input("Enable debug logging? (y/N): ")
        options["debug_enabled"] = debug.lower() == 'y'
        
        # Power management
        if use_case in ["laptop", "enterprise"]:
            power_mgmt = input("Enable power management? (Y/n): ")
            options["power_management"] = power_mgmt.lower() != 'n'
        else:
            options["power_management"] = False
        
        # Firmware options
        if self.driver_db[driver]["firmware_required"]:
            auto_firmware = input("Automatically download firmware? (Y/n): ")
            options["auto_firmware"] = auto_firmware.lower() != 'n'
        
        # Regulatory enforcement
        if self.driver_db[driver]["regulatory_enforcement"]:
            strict_regulatory = input("Enable strict regulatory enforcement? (Y/n): ")
            options["strict_regulatory"] = strict_regulatory.lower() != 'n'
        
        return options
    
    def _configure_build_options(self) -> Dict[str, any]:
        """Configure build options"""
        print("\n🔨 Step 7: Build Options")
        print("-" * 30)
        
        options = {}
        
        # Build type
        print("Build configuration:")
        print("1) Release (optimized)")
        print("2) Debug (with debug symbols)")
        
        while True:
            try:
                choice = int(input("Enter choice (1-2): "))
                if choice == 1:
                    options["build_type"] = "release"
                    break
                elif choice == 2:
                    options["build_type"] = "debug"
                    break
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a valid number.")
        
        # Parallel build
        import multiprocessing
        max_jobs = multiprocessing.cpu_count()
        
        parallel = input(f"Use parallel build? (Y/n, max {max_jobs} jobs): ")
        if parallel.lower() != 'n':
            try:
                jobs = input(f"Number of parallel jobs (1-{max_jobs}, default {max_jobs}): ")
                options["parallel_jobs"] = int(jobs) if jobs else max_jobs
            except ValueError:
                options["parallel_jobs"] = max_jobs
        else:
            options["parallel_jobs"] = 1
        
        # Clean build
        clean = input("Clean before build? (Y/n): ")
        options["clean_build"] = clean.lower() != 'n'
        
        return options
    
    def _review_configuration(self, config: WirelessConfig) -> bool:
        """Review and confirm configuration"""
        print("\n📋 Step 8: Review Configuration")
        print("=" * 40)
        
        driver_info = self.driver_db[config.driver]
        chipset_info = driver_info["chipsets"][config.chipset]
        
        print(f"Use Case: {config.use_case}")
        print(f"Driver: {config.driver} ({driver_info['name']})")
        print(f"Chipset: {config.chipset} ({chipset_info['name']})")
        print(f"Regulatory Domain: {config.regulatory_domain}")
        print(f"Features: {', '.join(config.features)}")
        print()
        
        print("Advanced Options:")
        for key, value in config.advanced_options.items():
            print(f"  {key}: {value}")
        print()
        
        print("Build Options:")
        for key, value in config.build_options.items():
            print(f"  {key}: {value}")
        print()
        
        # Show warnings if applicable
        warnings = []
        
        if "monitor_mode" in config.features:
            warnings.append("Monitor mode requires proper authorization")
        
        if "packet_injection" in config.features:
            warnings.append("Packet injection must comply with regulations")
        
        if config.regulatory_domain in ["EU", "JP", "CN"]:
            warnings.append(f"Regulatory restrictions apply in {config.regulatory_domain}")
        
        if warnings:
            print("⚠️  Warnings:")
            for warning in warnings:
                print(f"   • {warning}")
            print()
        
        confirm = input("Save this configuration? (Y/n): ")
        return confirm.lower() != 'n'
    
    def save_configuration(self, config: WirelessConfig, name: Optional[str] = None) -> str:
        """Save configuration to file"""
        if not name:
            name = f"{config.driver}-{config.chipset}-{config.use_case}"
        
        config_file = self.config_dir / f"{name}.json"
        
        with open(config_file, 'w') as f:
            json.dump(asdict(config), f, indent=2)
        
        print(f"✅ Configuration saved to: {config_file}")
        return str(config_file)
    
    def load_configuration(self, config_file: str) -> WirelessConfig:
        """Load configuration from file"""
        with open(config_file, 'r') as f:
            data = json.load(f)
        
        return WirelessConfig(**data)
    
    def list_configurations(self) -> List[str]:
        """List available configurations"""
        config_files = list(self.config_dir.glob("*.json"))
        
        if not config_files:
            print("No saved configurations found")
            return []
        
        print("Available configurations:")
        for i, config_file in enumerate(config_files, 1):
            try:
                config = self.load_configuration(str(config_file))
                print(f"{i}) {config_file.stem}")
                print(f"   Driver: {config.driver} ({config.chipset})")
                print(f"   Use Case: {config.use_case}")
                print(f"   Created: {config.timestamp}")
                print()
            except Exception as e:
                print(f"{i}) {config_file.stem} (Error: {e})")
        
        return [str(f) for f in config_files]
    
    def generate_kconfig(self, config: WirelessConfig) -> str:
        """Generate Kconfig from configuration"""
        kconfig_file = self.config_dir / f"{config.driver}-{config.chipset}.config"
        
        lines = [
            "# Wireless driver configuration",
            f"# Generated from: {config.driver}-{config.chipset}-{config.use_case}",
            f"# Created: {config.timestamp}",
            "",
            "# Basic backports configuration",
            "CONFIG_BACKPORTS=y",
            "CONFIG_BACKPORTS_BUILD_COMPAT=y",
            "",
            "# Wireless stack",
            "CONFIG_BACKPORTS_CFG80211=y",
            "CONFIG_BACKPORTS_MAC80211=y",
            "CONFIG_BACKPORTS_MAC80211_RC_MINSTREL=y",
            "",
            "# Regulatory support",
            "CONFIG_BACKPORTS_CFG80211_CRDA_SUPPORT=y",
            ""
        ]
        
        # Driver-specific configuration
        if config.driver == "ath11k":
            lines.extend([
                "# ath11k driver",
                "CONFIG_BACKPORTS_ATH_COMMON=y",
                "CONFIG_BACKPORTS_ATH11K=y",
                "CONFIG_BACKPORTS_ATH11K_PCI=y"
            ])
        elif config.driver == "ath10k":
            lines.extend([
                "# ath10k driver", 
                "CONFIG_BACKPORTS_ATH_COMMON=y",
                "CONFIG_BACKPORTS_ATH10K=y",
                "CONFIG_BACKPORTS_ATH10K_PCI=y"
            ])
        elif config.driver == "iwlwifi":
            lines.extend([
                "# iwlwifi driver",
                "CONFIG_BACKPORTS_IWLWIFI=y",
                "CONFIG_BACKPORTS_IWLDVM=y",
                "CONFIG_BACKPORTS_IWLMVM=y"
            ])
        elif config.driver == "rt2x00":
            lines.extend([
                "# rt2x00 driver family",
                "CONFIG_BACKPORTS_RT2X00=y",
                "CONFIG_BACKPORTS_RT2800USB=y",
                "CONFIG_BACKPORTS_RT2X00_LIB=y"
            ])
        
        # Feature-specific configuration
        if "monitor_mode" in config.features:
            lines.append("CONFIG_BACKPORTS_MAC80211_DEBUGFS=y")
        
        if "mesh_networking" in config.features:
            lines.append("CONFIG_BACKPORTS_MAC80211_MESH=y")
        
        if config.advanced_options.get("debug_enabled", False):
            lines.append(f"CONFIG_BACKPORTS_{config.driver.upper()}_DEBUG=y")
        
        # Write configuration
        with open(kconfig_file, 'w') as f:
            f.write('\n'.join(lines) + '\n')
        
        print(f"✅ Kconfig generated: {kconfig_file}")
        return str(kconfig_file)

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Interactive Wireless Driver Configuration Wizard")
    parser.add_argument("command", choices=["setup", "load", "list", "generate"], 
                       help="Configuration command")
    parser.add_argument("--config", help="Configuration file to load")
    parser.add_argument("--name", help="Configuration name")
    parser.add_argument("--output", help="Output file")
    
    args = parser.parse_args()
    
    configurator = WirelessDriverConfigurator()
    
    if args.command == "setup":
        # Run interactive setup
        config = configurator.run_interactive_setup()
        config_file = configurator.save_configuration(config, args.name)
        
        # Generate Kconfig
        kconfig_file = configurator.generate_kconfig(config)
        
        print("\n🎉 Configuration completed successfully!")
        print(f"Configuration file: {config_file}")
        print(f"Kconfig file: {kconfig_file}")
        print("\nNext steps:")
        print("1. Review the generated configuration")
        print("2. Run the setup script with this configuration")
        print("3. Build and install the wireless driver")
    
    elif args.command == "load":
        if not args.config:
            print("Error: Configuration file required")
            return 1
        
        try:
            config = configurator.load_configuration(args.config)
            print("Configuration loaded successfully:")
            print(f"Driver: {config.driver} ({config.chipset})")
            print(f"Use Case: {config.use_case}")
            print(f"Features: {', '.join(config.features)}")
            
            # Generate Kconfig if requested
            if args.output:
                kconfig_file = configurator.generate_kconfig(config)
                print(f"Kconfig generated: {kconfig_file}")
        
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return 1
    
    elif args.command == "list":
        configurator.list_configurations()
    
    elif args.command == "generate":
        if not args.config:
            print("Error: Configuration file required")
            return 1
        
        try:
            config = configurator.load_configuration(args.config)
            kconfig_file = configurator.generate_kconfig(config)
            print(f"Kconfig generated: {kconfig_file}")
        
        except Exception as e:
            print(f"Error generating Kconfig: {e}")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())