#!/usr/bin/env python3
"""
Wireless Driver Management Script

This script provides comprehensive wireless driver management including
driver selection, configuration, firmware management, and conflict resolution.
"""

import os
import sys
import subprocess
import json
import time
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class DriverStatus(Enum):
    """Driver status enumeration"""
    AVAILABLE = "available"
    INSTALLED = "installed"
    LOADED = "loaded"
    CONFLICTED = "conflicted"
    MISSING = "missing"

class ConflictType(Enum):
    """Conflict type enumeration"""
    SYMBOL = "symbol"
    RESOURCE = "resource"
    DEVICE = "device"
    FIRMWARE = "firmware"

@dataclass
class DriverInfo:
    """Driver information structure"""
    name: str
    description: str
    version: str
    status: DriverStatus
    chipsets: List[str]
    features: List[str]
    dependencies: List[str]
    conflicts: List[str]
    firmware_files: List[str]
    module_path: Optional[str] = None

@dataclass
class ConflictInfo:
    """Conflict information structure"""
    type: ConflictType
    drivers: List[str]
    description: str
    severity: str
    resolution: List[str]

class WirelessDriverManager:
    """Comprehensive wireless driver management system"""
    
    def __init__(self, kernel_root: str = "."):
        """Initialize wireless driver manager"""
        self.kernel_root = Path(kernel_root).resolve()
        self.backports_dir = self.kernel_root / "backports-integration"
        
        # Load driver database and configuration
        self.driver_database = self._load_driver_database()
        self.config = self._load_configuration()
        
        # Initialize validation tools
        self._init_validation_tools()
    
    def _load_driver_database(self) -> Dict:
        """Load wireless driver database"""
        database_file = self.backports_dir / "configs" / "build.json"
        
        try:
            if database_file.exists():
                with open(database_file, 'r') as f:
                    config = json.load(f)
                return config.get("wireless_drivers", {})
        except Exception as e:
            print(f"Warning: Could not load driver database: {e}")
        
        # Return default database
        return {
            "ath11k": {
                "description": "Qualcomm Atheros 11ac/11ax wireless driver",
                "chipsets": ["QCA6390", "QCA6490", "WCN6855", "QCN9074"],
                "features": ["monitor_mode", "packet_injection", "mesh_networking"],
                "dependencies": ["cfg80211", "mac80211", "crypto"],
                "firmware_files": ["ath11k/QCA6390/hw2.0/amss.bin"]
            }
        }  
  
    def _load_configuration(self) -> Dict:
        """Load manager configuration"""
        config_file = self.backports_dir / "configs" / "driver-manager.json"
        
        default_config = {
            "auto_resolve_conflicts": True,
            "auto_download_firmware": False,
            "backup_before_changes": True,
            "validate_before_install": True,
            "regulatory_domain": "US",
            "preferred_drivers": ["ath11k", "iwlwifi", "ath10k", "rt2x00"],
            "blacklisted_drivers": [],
            "firmware_sources": [
                "https://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git/plain/",
                "https://github.com/kvalo/ath11k-firmware/raw/master/",
                "https://github.com/kvalo/ath10k-firmware/raw/master/"
            ]
        }
        
        try:
            if config_file.exists():
                with open(config_file, 'r') as f:
                    loaded_config = json.load(f)
                default_config.update(loaded_config)
        except Exception as e:
            print(f"Warning: Could not load configuration: {e}")
        
        return default_config
    
    def _init_validation_tools(self):
        """Initialize validation tools"""
        self.validation_tools = {}
        
        # Initialize validation tool paths
        tools = [
            "wireless-validation-framework.py",
            "chipset-validation-tool.py", 
            "driver-coexistence-tester.py",
            "firmware-validation-tool.py"
        ]
        
        for tool in tools:
            tool_path = self.backports_dir / "scripts" / tool
            if tool_path.exists():
                self.validation_tools[tool] = tool_path
    
    def detect_available_drivers(self) -> List[DriverInfo]:
        """Detect available wireless drivers"""
        drivers = []
        
        for driver_name, driver_config in self.driver_database.items():
            # Determine driver status
            status = self._get_driver_status(driver_name)
            
            # Get version information
            version = self._get_driver_version(driver_name)
            
            # Create driver info
            driver_info = DriverInfo(
                name=driver_name,
                description=driver_config.get("description", ""),
                version=version,
                status=status,
                chipsets=driver_config.get("chipsets", []),
                features=driver_config.get("supported_features", []),
                dependencies=driver_config.get("dependencies", []),
                conflicts=[],  # Will be populated by conflict detection
                firmware_files=driver_config.get("firmware_files", []),
                module_path=self._find_module_path(driver_name)
            )
            
            drivers.append(driver_info)
        
        return drivers
    
    def _get_driver_status(self, driver_name: str) -> DriverStatus:
        """Get current status of a driver"""
        # Check if module is loaded
        if self._is_module_loaded(driver_name):
            return DriverStatus.LOADED
        
        # Check if module is installed
        if self._is_module_installed(driver_name):
            return DriverStatus.INSTALLED
        
        # Check if driver source is available
        if self._is_driver_available(driver_name):
            return DriverStatus.AVAILABLE
        
        return DriverStatus.MISSING
    
    def _is_module_loaded(self, module_name: str) -> bool:
        """Check if module is currently loaded"""
        try:
            with open("/proc/modules", "r") as f:
                for line in f:
                    if line.startswith(module_name + " "):
                        return True
        except:
            pass
        return False
    
    def _is_module_installed(self, module_name: str) -> bool:
        """Check if module is installed"""
        try:
            result = subprocess.run(["modinfo", module_name], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def _is_driver_available(self, driver_name: str) -> bool:
        """Check if driver source is available"""
        # Check in backports directory
        backports_generated = self.kernel_root / "backports-generated-6.1"
        driver_paths = [
            backports_generated / "drivers" / "net" / "wireless" / "ath" / driver_name,
            backports_generated / "drivers" / "net" / "wireless" / "intel" / driver_name,
            backports_generated / "drivers" / "net" / "wireless" / "ralink" / driver_name
        ]
        
        return any(path.exists() for path in driver_paths)
    
    def _get_driver_version(self, driver_name: str) -> str:
        """Get driver version"""
        try:
            result = subprocess.run(["modinfo", driver_name], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith("version:"):
                        return line.split(":", 1)[1].strip()
        except:
            pass
        return "unknown"
    
    def _find_module_path(self, driver_name: str) -> Optional[str]:
        """Find module path"""
        try:
            result = subprocess.run(["modinfo", "-n", driver_name], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None    
 
    def select_driver(self, driver_name: str, chipset: Optional[str] = None) -> Dict[str, any]:
        """Select and configure a wireless driver"""
        result = {
            "success": False,
            "driver": driver_name,
            "chipset": chipset,
            "actions_taken": [],
            "warnings": [],
            "errors": []
        }
        
        # Validate driver exists
        if driver_name not in self.driver_database:
            result["errors"].append(f"Unknown driver: {driver_name}")
            return result
        
        driver_config = self.driver_database[driver_name]
        
        # Validate chipset if specified
        if chipset and chipset not in driver_config.get("chipsets", []):
            result["errors"].append(f"Chipset {chipset} not supported by {driver_name}")
            return result
        
        # Check dependencies
        dependency_result = self._check_dependencies(driver_name)
        if not dependency_result["satisfied"]:
            result["errors"].extend(dependency_result["missing"])
            return result
        
        result["warnings"].extend(dependency_result["warnings"])
        
        # Check for conflicts
        conflicts = self.detect_conflicts([driver_name])
        if conflicts:
            if self.config["auto_resolve_conflicts"]:
                resolution_result = self._resolve_conflicts(conflicts)
                result["actions_taken"].extend(resolution_result["actions"])
                result["warnings"].extend(resolution_result["warnings"])
            else:
                result["errors"].append("Driver conflicts detected - use --resolve-conflicts")
                return result
        
        # Configure driver
        config_result = self._configure_driver(driver_name, chipset)
        result["actions_taken"].extend(config_result["actions"])
        result["warnings"].extend(config_result["warnings"])
        
        if config_result["success"]:
            result["success"] = True
            result["actions_taken"].append(f"Successfully selected driver: {driver_name}")
        else:
            result["errors"].extend(config_result["errors"])
        
        return result
    
    def _check_dependencies(self, driver_name: str) -> Dict[str, any]:
        """Check driver dependencies"""
        result = {
            "satisfied": True,
            "missing": [],
            "warnings": []
        }
        
        driver_config = self.driver_database.get(driver_name, {})
        dependencies = driver_config.get("dependencies", [])
        
        for dep in dependencies:
            if not self._is_dependency_satisfied(dep):
                result["missing"].append(f"Missing dependency: {dep}")
                result["satisfied"] = False
        
        return result
    
    def _is_dependency_satisfied(self, dependency: str) -> bool:
        """Check if a dependency is satisfied"""
        # Check common dependencies
        if dependency == "cfg80211":
            return self._is_module_available("cfg80211") or self._is_module_available("backports_cfg80211")
        elif dependency == "mac80211":
            return self._is_module_available("mac80211") or self._is_module_available("backports_mac80211")
        elif dependency == "crypto":
            return Path("/proc/crypto").exists()
        
        # Generic module check
        return self._is_module_available(dependency)
    
    def _is_module_available(self, module_name: str) -> bool:
        """Check if module is available (loaded or installable)"""
        return self._is_module_loaded(module_name) or self._is_module_installed(module_name)
    
    def _configure_driver(self, driver_name: str, chipset: Optional[str]) -> Dict[str, any]:
        """Configure a wireless driver"""
        result = {
            "success": False,
            "actions": [],
            "warnings": [],
            "errors": []
        }
        
        try:
            # Generate Kconfig settings
            kconfig_settings = self._generate_kconfig_settings(driver_name, chipset)
            result["actions"].append(f"Generated Kconfig settings for {driver_name}")
            
            # Update configuration files
            config_result = self._update_configuration_files(driver_name, kconfig_settings)
            result["actions"].extend(config_result["actions"])
            result["warnings"].extend(config_result["warnings"])
            
            # Validate configuration
            if self.config["validate_before_install"]:
                validation_result = self._validate_driver_configuration(driver_name)
                if not validation_result["valid"]:
                    result["errors"].extend(validation_result["errors"])
                    return result
                result["actions"].append("Configuration validation passed")
            
            result["success"] = True
            
        except Exception as e:
            result["errors"].append(f"Configuration failed: {e}")
        
        return result
    
    def _generate_kconfig_settings(self, driver_name: str, chipset: Optional[str]) -> Dict[str, str]:
        """Generate Kconfig settings for driver"""
        settings = {
            "CONFIG_BACKPORTS": "y",
            "CONFIG_BACKPORTS_CFG80211": "y",
            "CONFIG_BACKPORTS_MAC80211": "y",
            "CONFIG_BACKPORTS_WIRELESS_DRIVERS": "y"
        }
        
        # Driver-specific settings
        if driver_name == "ath11k":
            settings.update({
                "CONFIG_BACKPORTS_ATH_DRIVERS": "y",
                "CONFIG_BACKPORTS_ATH11K": "y"
            })
        elif driver_name == "ath10k":
            settings.update({
                "CONFIG_BACKPORTS_ATH_DRIVERS": "y", 
                "CONFIG_BACKPORTS_ATH10K": "y"
            })
        elif driver_name == "iwlwifi":
            settings["CONFIG_BACKPORTS_IWLWIFI"] = "y"
        elif driver_name == "rt2x00":
            settings["CONFIG_BACKPORTS_RT2X00"] = "y"
        
        # Chipset-specific settings
        if chipset:
            chipset_config = self._get_chipset_config(driver_name, chipset)
            settings.update(chipset_config)
        
        return settings
    
    def _get_chipset_config(self, driver_name: str, chipset: str) -> Dict[str, str]:
        """Get chipset-specific configuration"""
        config = {}
        
        if driver_name == "ath11k":
            if chipset in ["QCA6390", "QCA6490", "WCN6855"]:
                config["CONFIG_BACKPORTS_ATH11K_PCI"] = "y"
            elif chipset == "QCN9074":
                config["CONFIG_BACKPORTS_ATH11K_AHB"] = "y"
        
        return config
    
    def _update_configuration_files(self, driver_name: str, settings: Dict[str, str]) -> Dict[str, any]:
        """Update configuration files"""
        result = {
            "actions": [],
            "warnings": []
        }
        
        # Update .config file if it exists
        config_file = self.kernel_root / ".config"
        if config_file.exists():
            self._update_kconfig_file(config_file, settings)
            result["actions"].append(f"Updated {config_file}")
        
        # Create driver-specific config
        driver_config_file = self.backports_dir / "configs" / f"{driver_name}.config"
        self._create_driver_config_file(driver_config_file, settings)
        result["actions"].append(f"Created {driver_config_file}")
        
        return result
    
    def _update_kconfig_file(self, config_file: Path, settings: Dict[str, str]):
        """Update Kconfig file with new settings"""
        if self.config["backup_before_changes"]:
            backup_file = config_file.with_suffix(".config.backup")
            config_file.rename(backup_file)
        
        # Read existing config
        existing_config = {}
        if config_file.exists():
            with open(config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        existing_config[key] = value
        
        # Update with new settings
        existing_config.update(settings)
        
        # Write updated config
        with open(config_file, 'w') as f:
            for key, value in sorted(existing_config.items()):
                f.write(f"{key}={value}\n")
    
    def _create_driver_config_file(self, config_file: Path, settings: Dict[str, str]):
        """Create driver-specific configuration file"""
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            f.write(f"# Wireless driver configuration\n")
            f.write(f"# Generated by wireless-driver-manager.py\n")
            f.write(f"# Generated at: {time.ctime()}\n\n")
            
            for key, value in sorted(settings.items()):
                f.write(f"{key}={value}\n")
    
    def _validate_driver_configuration(self, driver_name: str) -> Dict[str, any]:
        """Validate driver configuration"""
        result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Use validation framework if available
        validation_tool = self.validation_tools.get("wireless-validation-framework.py")
        if validation_tool:
            try:
                validation_result = subprocess.run([
                    "python3", str(validation_tool), "--json"
                ], capture_output=True, text=True)
                
                if validation_result.returncode == 0:
                    validation_data = json.loads(validation_result.stdout)
                    # Process validation results
                    if validation_data.get("summary", {}).get("failed_tests", 0) > 0:
                        result["valid"] = False
                        result["errors"].append("Configuration validation failed")
                else:
                    result["warnings"].append("Could not run validation framework")
            except Exception as e:
                result["warnings"].append(f"Validation error: {e}")
        
        return result 
   
    def detect_conflicts(self, drivers: List[str]) -> List[ConflictInfo]:
        """Detect conflicts between drivers"""
        conflicts = []
        
        # Known conflict patterns
        conflict_patterns = [
            {
                "drivers": ["ath11k", "qcacld"],
                "type": ConflictType.SYMBOL,
                "description": "Both drivers export the same wireless stack symbols",
                "severity": "critical",
                "resolution": ["Use only one driver", "Blacklist conflicting driver"]
            },
            {
                "drivers": ["ath10k", "qcacld"],
                "type": ConflictType.SYMBOL,
                "description": "Symbol conflicts with vendor driver",
                "severity": "critical", 
                "resolution": ["Use only one driver", "Blacklist vendor driver"]
            },
            {
                "drivers": ["iwlwifi", "iwl_legacy"],
                "type": ConflictType.SYMBOL,
                "description": "Legacy and modern Intel drivers conflict",
                "severity": "high",
                "resolution": ["Use modern iwlwifi driver", "Remove legacy driver"]
            }
        ]
        
        # Check for pattern matches
        for pattern in conflict_patterns:
            pattern_drivers = set(pattern["drivers"])
            active_drivers = set(drivers)
            
            if pattern_drivers.issubset(active_drivers):
                conflicts.append(ConflictInfo(
                    type=pattern["type"],
                    drivers=list(pattern_drivers),
                    description=pattern["description"],
                    severity=pattern["severity"],
                    resolution=pattern["resolution"]
                ))
        
        # Use coexistence tester if available
        coexistence_tool = self.validation_tools.get("driver-coexistence-tester.py")
        if coexistence_tool and len(drivers) > 1:
            try:
                result = subprocess.run([
                    "python3", str(coexistence_tool), "--test"] + drivers,
                    capture_output=True, text=True
                )
                
                if result.returncode != 0:
                    conflicts.append(ConflictInfo(
                        type=ConflictType.RESOURCE,
                        drivers=drivers,
                        description="Runtime coexistence test failed",
                        severity="medium",
                        resolution=["Check driver compatibility", "Use alternative drivers"]
                    ))
            except Exception as e:
                print(f"Warning: Could not run coexistence test: {e}")
        
        return conflicts
    
    def _resolve_conflicts(self, conflicts: List[ConflictInfo]) -> Dict[str, any]:
        """Automatically resolve driver conflicts"""
        result = {
            "actions": [],
            "warnings": []
        }
        
        for conflict in conflicts:
            if conflict.severity == "critical":
                # For critical conflicts, disable lower priority driver
                preferred_drivers = self.config["preferred_drivers"]
                conflict_drivers = conflict.drivers
                
                # Find highest priority driver
                best_driver = None
                best_priority = float('inf')
                
                for driver in conflict_drivers:
                    try:
                        priority = preferred_drivers.index(driver)
                        if priority < best_priority:
                            best_priority = priority
                            best_driver = driver
                    except ValueError:
                        pass  # Driver not in preferred list
                
                if best_driver:
                    # Disable other drivers
                    for driver in conflict_drivers:
                        if driver != best_driver:
                            self._disable_driver(driver)
                            result["actions"].append(f"Disabled conflicting driver: {driver}")
                    
                    result["actions"].append(f"Kept preferred driver: {best_driver}")
                else:
                    result["warnings"].append(f"Could not resolve conflict: {conflict.description}")
            
            elif conflict.severity in ["high", "medium"]:
                result["warnings"].append(f"Conflict detected: {conflict.description}")
                result["warnings"].append(f"Recommended actions: {', '.join(conflict.resolution)}")
        
        return result
    
    def _disable_driver(self, driver_name: str):
        """Disable a driver"""
        # Add to blacklist
        if driver_name not in self.config["blacklisted_drivers"]:
            self.config["blacklisted_drivers"].append(driver_name)
        
        # Unload module if loaded
        if self._is_module_loaded(driver_name):
            try:
                subprocess.run(["rmmod", driver_name], check=True)
            except subprocess.CalledProcessError:
                pass  # Module might be in use
        
        # Add to modprobe blacklist
        blacklist_file = Path("/etc/modprobe.d/wireless-blacklist.conf")
        try:
            with open(blacklist_file, 'a') as f:
                f.write(f"blacklist {driver_name}\n")
        except PermissionError:
            pass  # Need root privileges
    
    def install_driver(self, driver_name: str, chipset: Optional[str] = None) -> Dict[str, any]:
        """Install a wireless driver"""
        result = {
            "success": False,
            "driver": driver_name,
            "actions_taken": [],
            "warnings": [],
            "errors": []
        }
        
        # Select and configure driver first
        select_result = self.select_driver(driver_name, chipset)
        if not select_result["success"]:
            result["errors"].extend(select_result["errors"])
            return result
        
        result["actions_taken"].extend(select_result["actions_taken"])
        result["warnings"].extend(select_result["warnings"])
        
        # Install firmware if required
        driver_config = self.driver_database[driver_name]
        if driver_config.get("firmware_required", False):
            firmware_result = self.install_firmware(driver_name, chipset)
            result["actions_taken"].extend(firmware_result["actions_taken"])
            result["warnings"].extend(firmware_result["warnings"])
            
            if not firmware_result["success"]:
                result["warnings"].append("Firmware installation failed - driver may not work properly")
        
        # Build and install driver
        build_result = self._build_and_install_driver(driver_name)
        result["actions_taken"].extend(build_result["actions"])
        result["warnings"].extend(build_result["warnings"])
        
        if build_result["success"]:
            result["success"] = True
            result["actions_taken"].append(f"Successfully installed driver: {driver_name}")
        else:
            result["errors"].extend(build_result["errors"])
        
        return result
    
    def _build_and_install_driver(self, driver_name: str) -> Dict[str, any]:
        """Build and install a driver"""
        result = {
            "success": False,
            "actions": [],
            "warnings": [],
            "errors": []
        }
        
        try:
            # Use Makefile to build driver
            makefile = self.backports_dir / "Makefile"
            
            if makefile.exists():
                # Build wireless drivers
                build_cmd = [
                    "make", "-f", str(makefile), "wireless_drivers"
                ]
                
                build_result = subprocess.run(build_cmd, capture_output=True, text=True)
                
                if build_result.returncode == 0:
                    result["actions"].append("Driver build completed")
                    
                    # Install driver
                    install_cmd = [
                        "make", "-f", str(makefile), "wireless_install"
                    ]
                    
                    install_result = subprocess.run(install_cmd, capture_output=True, text=True)
                    
                    if install_result.returncode == 0:
                        result["success"] = True
                        result["actions"].append("Driver installation completed")
                    else:
                        result["errors"].append(f"Installation failed: {install_result.stderr}")
                else:
                    result["errors"].append(f"Build failed: {build_result.stderr}")
            else:
                result["errors"].append("Makefile not found")
        
        except Exception as e:
            result["errors"].append(f"Build/install error: {e}")
        
        return result 
   
    def install_firmware(self, driver_name: str, chipset: Optional[str] = None) -> Dict[str, any]:
        """Install firmware for a wireless driver"""
        result = {
            "success": False,
            "driver": driver_name,
            "chipset": chipset,
            "actions_taken": [],
            "warnings": [],
            "errors": []
        }
        
        driver_config = self.driver_database.get(driver_name, {})
        firmware_files = driver_config.get("firmware_files", [])
        
        if not firmware_files:
            result["success"] = True
            result["actions_taken"].append(f"No firmware required for {driver_name}")
            return result
        
        # Use firmware validation tool if available
        firmware_tool = self.validation_tools.get("firmware-validation-tool.py")
        if firmware_tool:
            try:
                # Validate current firmware
                validate_cmd = [
                    "python3", str(firmware_tool), "--validate", driver_name
                ]
                
                if chipset:
                    validate_cmd.append(chipset)
                
                validate_result = subprocess.run(validate_cmd, capture_output=True, text=True)
                
                if validate_result.returncode == 0:
                    result["success"] = True
                    result["actions_taken"].append("Firmware validation passed")
                    return result
                
                # Download missing firmware if auto-download is enabled
                if self.config["auto_download_firmware"]:
                    download_result = self._download_firmware(driver_name, chipset)
                    result["actions_taken"].extend(download_result["actions"])
                    result["warnings"].extend(download_result["warnings"])
                    
                    if download_result["success"]:
                        result["success"] = True
                    else:
                        result["errors"].extend(download_result["errors"])
                else:
                    result["errors"].append("Firmware validation failed - enable auto-download or install manually")
            
            except Exception as e:
                result["errors"].append(f"Firmware validation error: {e}")
        else:
            # Manual firmware installation
            install_result = self._install_firmware_manual(driver_name, firmware_files)
            result["actions_taken"].extend(install_result["actions"])
            result["warnings"].extend(install_result["warnings"])
            result["success"] = install_result["success"]
            
            if not install_result["success"]:
                result["errors"].extend(install_result["errors"])
        
        return result
    
    def _download_firmware(self, driver_name: str, chipset: Optional[str]) -> Dict[str, any]:
        """Download firmware for driver"""
        result = {
            "success": False,
            "actions": [],
            "warnings": [],
            "errors": []
        }
        
        firmware_tool = self.validation_tools.get("firmware-validation-tool.py")
        if not firmware_tool:
            result["errors"].append("Firmware validation tool not available")
            return result
        
        try:
            download_cmd = [
                "python3", str(firmware_tool), "--download", driver_name
            ]
            
            if chipset:
                download_cmd.append(chipset)
            
            download_result = subprocess.run(download_cmd, capture_output=True, text=True)
            
            if download_result.returncode == 0:
                result["success"] = True
                result["actions"].append(f"Downloaded firmware for {driver_name}")
            else:
                result["errors"].append(f"Firmware download failed: {download_result.stderr}")
        
        except Exception as e:
            result["errors"].append(f"Download error: {e}")
        
        return result
    
    def _install_firmware_manual(self, driver_name: str, firmware_files: List[str]) -> Dict[str, any]:
        """Manually install firmware files"""
        result = {
            "success": False,
            "actions": [],
            "warnings": [],
            "errors": []
        }
        
        firmware_dir = Path("/lib/firmware")
        if not firmware_dir.exists():
            result["errors"].append("Firmware directory /lib/firmware not found")
            return result
        
        # Check if firmware files exist
        missing_files = []
        for firmware_file in firmware_files:
            firmware_path = firmware_dir / firmware_file
            if not firmware_path.exists():
                missing_files.append(firmware_file)
        
        if missing_files:
            result["errors"].append(f"Missing firmware files: {', '.join(missing_files)}")
            result["warnings"].append("Install firmware package or enable auto-download")
        else:
            result["success"] = True
            result["actions"].append(f"All firmware files present for {driver_name}")
        
        return result
    
    def uninstall_driver(self, driver_name: str) -> Dict[str, any]:
        """Uninstall a wireless driver"""
        result = {
            "success": False,
            "driver": driver_name,
            "actions_taken": [],
            "warnings": [],
            "errors": []
        }
        
        try:
            # Unload module if loaded
            if self._is_module_loaded(driver_name):
                unload_result = subprocess.run(["rmmod", driver_name], 
                                             capture_output=True, text=True)
                if unload_result.returncode == 0:
                    result["actions_taken"].append(f"Unloaded module: {driver_name}")
                else:
                    result["warnings"].append(f"Could not unload module: {unload_result.stderr}")
            
            # Remove from configuration
            self._remove_driver_configuration(driver_name)
            result["actions_taken"].append(f"Removed configuration for {driver_name}")
            
            # Use Makefile to uninstall
            makefile = self.backports_dir / "Makefile"
            if makefile.exists():
                uninstall_cmd = [
                    "make", "-f", str(makefile), "wireless_uninstall"
                ]
                
                uninstall_result = subprocess.run(uninstall_cmd, capture_output=True, text=True)
                
                if uninstall_result.returncode == 0:
                    result["actions_taken"].append("Driver files removed")
                else:
                    result["warnings"].append("Could not remove all driver files")
            
            result["success"] = True
            result["actions_taken"].append(f"Successfully uninstalled driver: {driver_name}")
        
        except Exception as e:
            result["errors"].append(f"Uninstall error: {e}")
        
        return result
    
    def _remove_driver_configuration(self, driver_name: str):
        """Remove driver configuration"""
        # Remove driver-specific config file
        driver_config_file = self.backports_dir / "configs" / f"{driver_name}.config"
        if driver_config_file.exists():
            driver_config_file.unlink()
        
        # Update main config file
        config_file = self.kernel_root / ".config"
        if config_file.exists():
            self._remove_driver_from_kconfig(config_file, driver_name)
    
    def _remove_driver_from_kconfig(self, config_file: Path, driver_name: str):
        """Remove driver settings from Kconfig file"""
        if self.config["backup_before_changes"]:
            backup_file = config_file.with_suffix(".config.backup")
            if not backup_file.exists():
                config_file.rename(backup_file)
        
        # Read and filter config
        filtered_lines = []
        with open(config_file, 'r') as f:
            for line in f:
                # Skip driver-specific lines
                if driver_name.upper() not in line:
                    filtered_lines.append(line)
        
        # Write filtered config
        with open(config_file, 'w') as f:
            f.writelines(filtered_lines)    

    def check_regulatory_compliance(self, driver_name: str, regulatory_domain: str = None) -> Dict[str, any]:
        """Check regulatory compliance for a driver"""
        result = {
            "compliant": True,
            "driver": driver_name,
            "regulatory_domain": regulatory_domain or self.config["regulatory_domain"],
            "warnings": [],
            "errors": [],
            "recommendations": []
        }
        
        # Use regulatory manager if available
        regulatory_tool = self.backports_dir / "scripts" / "regulatory-manager.py"
        if regulatory_tool.exists():
            try:
                compliance_cmd = [
                    "python3", str(regulatory_tool), 
                    "--check-compliance", driver_name,
                    "--domain", result["regulatory_domain"]
                ]
                
                compliance_result = subprocess.run(compliance_cmd, capture_output=True, text=True)
                
                if compliance_result.returncode == 0:
                    # Parse compliance output
                    if "compliant" in compliance_result.stdout.lower():
                        result["compliant"] = True
                    else:
                        result["compliant"] = False
                        result["errors"].append("Regulatory compliance check failed")
                else:
                    result["warnings"].append("Could not run regulatory compliance check")
            
            except Exception as e:
                result["warnings"].append(f"Regulatory check error: {e}")
        
        # Basic compliance checks
        driver_config = self.driver_database.get(driver_name, {})
        
        # Check if driver supports monitor mode/injection
        features = driver_config.get("supported_features", [])
        if "packet_injection" in features:
            result["warnings"].append("Driver supports packet injection - ensure regulatory compliance")
            result["recommendations"].append("Use packet injection only in authorized environments")
        
        if "monitor_mode" in features:
            result["recommendations"].append("Monitor mode usage must comply with local privacy laws")
        
        # Domain-specific warnings
        domain = result["regulatory_domain"]
        if domain == "EU" and "packet_injection" in features:
            result["warnings"].append("Packet injection may be restricted in EU")
        elif domain == "JP" and "monitor_mode" in features:
            result["warnings"].append("Monitor mode may require authorization in Japan")
        
        return result
    
    def list_drivers(self, status_filter: Optional[str] = None) -> List[DriverInfo]:
        """List available wireless drivers"""
        drivers = self.detect_available_drivers()
        
        if status_filter:
            try:
                filter_status = DriverStatus(status_filter)
                drivers = [d for d in drivers if d.status == filter_status]
            except ValueError:
                pass  # Invalid filter, return all
        
        return drivers
    
    def get_driver_info(self, driver_name: str) -> Optional[DriverInfo]:
        """Get detailed information about a driver"""
        drivers = self.detect_available_drivers()
        
        for driver in drivers:
            if driver.name == driver_name:
                return driver
        
        return None
    
    def generate_management_report(self, output_file: Optional[str] = None) -> str:
        """Generate comprehensive driver management report"""
        drivers = self.detect_available_drivers()
        conflicts = self.detect_conflicts([d.name for d in drivers if d.status == DriverStatus.LOADED])
        
        report_lines = []
        report_lines.append("Wireless Driver Management Report")
        report_lines.append("=" * 50)
        report_lines.append(f"Generated: {time.ctime()}")
        report_lines.append("")
        
        # Driver summary
        report_lines.append("Driver Summary:")
        status_counts = {}
        for driver in drivers:
            status = driver.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for status, count in status_counts.items():
            report_lines.append(f"  {status.title()}: {count}")
        report_lines.append("")
        
        # Detailed driver information
        report_lines.append("Driver Details:")
        for driver in drivers:
            status_icon = {
                DriverStatus.LOADED: "🟢",
                DriverStatus.INSTALLED: "🟡", 
                DriverStatus.AVAILABLE: "⚪",
                DriverStatus.MISSING: "🔴"
            }.get(driver.status, "❓")
            
            report_lines.append(f"  {status_icon} {driver.name} ({driver.status.value})")
            report_lines.append(f"    Description: {driver.description}")
            report_lines.append(f"    Version: {driver.version}")
            report_lines.append(f"    Chipsets: {', '.join(driver.chipsets)}")
            report_lines.append(f"    Features: {', '.join(driver.features)}")
            
            if driver.firmware_files:
                report_lines.append(f"    Firmware: {len(driver.firmware_files)} files required")
        
        report_lines.append("")
        
        # Conflicts
        if conflicts:
            report_lines.append("Detected Conflicts:")
            for conflict in conflicts:
                severity_icon = {"critical": "🚨", "high": "❌", "medium": "⚠️", "low": "ℹ️"}.get(conflict.severity, "❓")
                report_lines.append(f"  {severity_icon} {conflict.type.value.upper()}")
                report_lines.append(f"    Drivers: {', '.join(conflict.drivers)}")
                report_lines.append(f"    Description: {conflict.description}")
                report_lines.append(f"    Resolution: {', '.join(conflict.resolution)}")
        else:
            report_lines.append("✅ No conflicts detected")
        
        report_lines.append("")
        
        # Recommendations
        report_lines.append("Recommendations:")
        loaded_drivers = [d for d in drivers if d.status == DriverStatus.LOADED]
        
        if not loaded_drivers:
            report_lines.append("  - No wireless drivers currently loaded")
            report_lines.append("  - Use 'wireless-driver-manager.py install <driver>' to install a driver")
        else:
            report_lines.append(f"  - {len(loaded_drivers)} driver(s) currently active")
            
            if conflicts:
                report_lines.append("  - Resolve driver conflicts for optimal performance")
            
            for driver in loaded_drivers:
                compliance = self.check_regulatory_compliance(driver.name)
                if not compliance["compliant"]:
                    report_lines.append(f"  - Check regulatory compliance for {driver.name}")
        
        report_content = "\n".join(report_lines)
        
        # Save to file if requested
        if output_file:
            try:
                with open(output_file, 'w') as f:
                    f.write(report_content)
                print(f"Management report saved to: {output_file}")
            except Exception as e:
                print(f"Error saving report: {e}")
        
        return report_content

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Wireless Driver Management")
    parser.add_argument("command", choices=[
        "list", "info", "select", "install", "uninstall", 
        "conflicts", "compliance", "report"
    ], help="Management command")
    
    parser.add_argument("driver", nargs="?", help="Driver name")
    parser.add_argument("--chipset", help="Specific chipset")
    parser.add_argument("--status", help="Filter by status")
    parser.add_argument("--domain", help="Regulatory domain")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--resolve-conflicts", action="store_true", help="Auto-resolve conflicts")
    parser.add_argument("--auto-firmware", action="store_true", help="Auto-download firmware")
    
    args = parser.parse_args()
    
    # Initialize manager
    manager = WirelessDriverManager()
    
    # Update configuration based on arguments
    if args.resolve_conflicts:
        manager.config["auto_resolve_conflicts"] = True
    if args.auto_firmware:
        manager.config["auto_download_firmware"] = True
    if args.domain:
        manager.config["regulatory_domain"] = args.domain
    
    # Execute command
    if args.command == "list":
        drivers = manager.list_drivers(args.status)
        
        print(f"Wireless Drivers ({len(drivers)} found):")
        for driver in drivers:
            status_icon = {
                DriverStatus.LOADED: "🟢",
                DriverStatus.INSTALLED: "🟡",
                DriverStatus.AVAILABLE: "⚪", 
                DriverStatus.MISSING: "🔴"
            }.get(driver.status, "❓")
            
            print(f"  {status_icon} {driver.name} - {driver.description} ({driver.status.value})")
    
    elif args.command == "info":
        if not args.driver:
            print("Error: Driver name required for info command")
            return 1
        
        driver_info = manager.get_driver_info(args.driver)
        if driver_info:
            print(f"Driver Information: {driver_info.name}")
            print(f"  Description: {driver_info.description}")
            print(f"  Version: {driver_info.version}")
            print(f"  Status: {driver_info.status.value}")
            print(f"  Chipsets: {', '.join(driver_info.chipsets)}")
            print(f"  Features: {', '.join(driver_info.features)}")
            print(f"  Dependencies: {', '.join(driver_info.dependencies)}")
            print(f"  Firmware files: {len(driver_info.firmware_files)}")
        else:
            print(f"Driver not found: {args.driver}")
            return 1
    
    elif args.command == "select":
        if not args.driver:
            print("Error: Driver name required for select command")
            return 1
        
        result = manager.select_driver(args.driver, args.chipset)
        
        if result["success"]:
            print(f"✅ Successfully selected driver: {args.driver}")
            for action in result["actions_taken"]:
                print(f"  - {action}")
        else:
            print(f"❌ Failed to select driver: {args.driver}")
            for error in result["errors"]:
                print(f"  Error: {error}")
        
        for warning in result["warnings"]:
            print(f"  Warning: {warning}")
    
    elif args.command == "install":
        if not args.driver:
            print("Error: Driver name required for install command")
            return 1
        
        result = manager.install_driver(args.driver, args.chipset)
        
        if result["success"]:
            print(f"✅ Successfully installed driver: {args.driver}")
            for action in result["actions_taken"]:
                print(f"  - {action}")
        else:
            print(f"❌ Failed to install driver: {args.driver}")
            for error in result["errors"]:
                print(f"  Error: {error}")
        
        for warning in result["warnings"]:
            print(f"  Warning: {warning}")
    
    elif args.command == "uninstall":
        if not args.driver:
            print("Error: Driver name required for uninstall command")
            return 1
        
        result = manager.uninstall_driver(args.driver)
        
        if result["success"]:
            print(f"✅ Successfully uninstalled driver: {args.driver}")
            for action in result["actions_taken"]:
                print(f"  - {action}")
        else:
            print(f"❌ Failed to uninstall driver: {args.driver}")
            for error in result["errors"]:
                print(f"  Error: {error}")
    
    elif args.command == "conflicts":
        drivers = manager.list_drivers()
        loaded_drivers = [d.name for d in drivers if d.status == DriverStatus.LOADED]
        
        conflicts = manager.detect_conflicts(loaded_drivers)
        
        if conflicts:
            print(f"Detected {len(conflicts)} conflict(s):")
            for conflict in conflicts:
                severity_icon = {"critical": "🚨", "high": "❌", "medium": "⚠️", "low": "ℹ️"}.get(conflict.severity, "❓")
                print(f"  {severity_icon} {conflict.type.value.upper()}: {conflict.description}")
                print(f"    Drivers: {', '.join(conflict.drivers)}")
                print(f"    Resolution: {', '.join(conflict.resolution)}")
        else:
            print("✅ No conflicts detected")
    
    elif args.command == "compliance":
        if not args.driver:
            print("Error: Driver name required for compliance command")
            return 1
        
        result = manager.check_regulatory_compliance(args.driver, args.domain)
        
        if result["compliant"]:
            print(f"✅ {args.driver} is regulatory compliant ({result['regulatory_domain']})")
        else:
            print(f"❌ {args.driver} has compliance issues ({result['regulatory_domain']})")
            for error in result["errors"]:
                print(f"  Error: {error}")
        
        for warning in result["warnings"]:
            print(f"  Warning: {warning}")
        
        for rec in result["recommendations"]:
            print(f"  Recommendation: {rec}")
    
    elif args.command == "report":
        report = manager.generate_management_report(args.output)
        if not args.output:
            print(report)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())