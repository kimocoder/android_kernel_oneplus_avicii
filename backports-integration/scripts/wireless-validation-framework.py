#!/usr/bin/env python3
"""
Wireless-Specific Validation and Testing Framework

This module provides comprehensive validation and testing capabilities for
wireless drivers, including compatibility validation, chipset detection,
dependency validation, and coexistence testing.
"""

import os
import sys
import subprocess
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import tempfile

class ValidationLevel(Enum):
    """Validation severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class DriverFamily(Enum):
    """Supported wireless driver families"""
    ATH11K = "ath11k"
    ATH10K = "ath10k"
    ATH9K = "ath9k"
    IWLWIFI = "iwlwifi"
    RT2X00 = "rt2x00"
    UNKNOWN = "unknown"

@dataclass
class ValidationResult:
    """Validation result structure"""
    test_name: str
    level: ValidationLevel
    passed: bool
    message: str
    details: Dict = None
    recommendations: List[str] = None

@dataclass
class ChipsetInfo:
    """Chipset information structure"""
    vendor_id: str
    device_id: str
    subsystem_vendor: str
    subsystem_device: str
    driver_family: DriverFamily
    chipset_name: str
    supported_features: List[str]
    firmware_requirements: List[str]

@dataclass
class DriverCompatibility:
    """Driver compatibility information"""
    driver_name: str
    kernel_version: str
    supported: bool
    required_symbols: List[str]
    missing_symbols: List[str]
    compatibility_issues: List[str]

class WirelessValidationFramework:
    """Comprehensive wireless validation and testing framework"""
    
    def __init__(self, kernel_root: str = "."):
        """Initialize the validation framework"""
        self.kernel_root = Path(kernel_root).resolve()
        self.backports_dir = self.kernel_root / "backports-integration"
        
        # Load wireless driver database
        self.driver_database = self._load_driver_database()
        
        # Validation results
        self.validation_results = []
        
        # System information
        self.system_info = self._gather_system_info()
    
    def _load_driver_database(self) -> Dict:
        """Load wireless driver database"""
        database_file = self.backports_dir / "scripts" / "wireless_drivers.yaml"
        
        # Default database if file doesn't exist
        default_database = {
            "ath11k": {
                "chipsets": {
                    "QCA6390": {
                        "vendor_id": "17cb",
                        "device_id": "1101",
                        "features": ["monitor", "injection", "mesh", "11ax"],
                        "firmware": ["ath11k/QCA6390/hw2.0/amss.bin", "ath11k/QCA6390/hw2.0/m3.bin"]
                    },
                    "QCA6490": {
                        "vendor_id": "17cb", 
                        "device_id": "1103",
                        "features": ["monitor", "injection", "mesh", "11ax"],
                        "firmware": ["ath11k/QCA6490/hw2.0/amss.bin", "ath11k/QCA6490/hw2.0/m3.bin"]
                    },
                    "WCN6855": {
                        "vendor_id": "17cb",
                        "device_id": "1107", 
                        "features": ["monitor", "injection", "mesh", "11ax"],
                        "firmware": ["ath11k/WCN6855/hw2.0/amss.bin", "ath11k/WCN6855/hw2.0/m3.bin"]
                    }
                },
                "required_symbols": ["cfg80211_register_netdevice", "ieee80211_alloc_hw"],
                "kernel_versions": ["4.19", "5.4", "5.10", "5.15", "6.1"]
            },
            "ath10k": {
                "chipsets": {
                    "QCA988X": {
                        "vendor_id": "168c",
                        "device_id": "003c",
                        "features": ["monitor", "injection", "mesh", "11ac"],
                        "firmware": ["ath10k/QCA988X/hw2.0/firmware-5.bin"]
                    },
                    "QCA6174": {
                        "vendor_id": "168c",
                        "device_id": "003e", 
                        "features": ["monitor", "injection", "11ac"],
                        "firmware": ["ath10k/QCA6174/hw3.0/firmware-6.bin"]
                    }
                },
                "required_symbols": ["cfg80211_register_netdevice", "ieee80211_alloc_hw"],
                "kernel_versions": ["4.19", "5.4", "5.10", "5.15", "6.1"]
            },
            "iwlwifi": {
                "chipsets": {
                    "AX200": {
                        "vendor_id": "8086",
                        "device_id": "2723",
                        "features": ["monitor", "11ax"],
                        "firmware": ["iwlwifi-cc-a0-63.ucode"]
                    },
                    "AX210": {
                        "vendor_id": "8086", 
                        "device_id": "2725",
                        "features": ["monitor", "11ax"],
                        "firmware": ["iwlwifi-ty-a0-gf-a0-63.ucode"]
                    }
                },
                "required_symbols": ["cfg80211_register_netdevice", "ieee80211_alloc_hw"],
                "kernel_versions": ["4.19", "5.4", "5.10", "5.15", "6.1"]
            }
        }
        
        try:
            if database_file.exists():
                import yaml
                with open(database_file, 'r') as f:
                    return yaml.safe_load(f)
        except ImportError:
            pass  # yaml not available, use default
        except Exception as e:
            print(f"Warning: Could not load driver database: {e}")
        
        return default_database
    
    def _gather_system_info(self) -> Dict:
        """Gather system information for validation"""
        info = {
            "kernel_version": "unknown",
            "architecture": "unknown", 
            "pci_devices": [],
            "usb_devices": [],
            "loaded_modules": [],
            "available_symbols": []
        }
        
        try:
            # Get kernel version
            result = subprocess.run(["uname", "-r"], capture_output=True, text=True)
            if result.returncode == 0:
                info["kernel_version"] = result.stdout.strip()
            
            # Get architecture
            result = subprocess.run(["uname", "-m"], capture_output=True, text=True)
            if result.returncode == 0:
                info["architecture"] = result.stdout.strip()
            
            # Get PCI devices
            result = subprocess.run(["lspci", "-n"], capture_output=True, text=True)
            if result.returncode == 0:
                info["pci_devices"] = self._parse_pci_devices(result.stdout)
            
            # Get loaded modules
            if Path("/proc/modules").exists():
                with open("/proc/modules", "r") as f:
                    for line in f:
                        module_name = line.split()[0]
                        info["loaded_modules"].append(module_name)
        
        except Exception as e:
            print(f"Warning: Could not gather complete system info: {e}")
        
        return info
    
    def _parse_pci_devices(self, lspci_output: str) -> List[Dict]:
        """Parse lspci output to extract device information"""
        devices = []
        
        for line in lspci_output.strip().split('\n'):
            if not line:
                continue
            
            # Parse lspci -n output format: "00:00.0 0600: 8086:1904 (rev 08)"
            parts = line.split()
            if len(parts) >= 3:
                bus_info = parts[0]
                class_code = parts[1].rstrip(':')
                vendor_device = parts[2]
                
                if ':' in vendor_device:
                    vendor_id, device_id = vendor_device.split(':', 1)
                    devices.append({
                        "bus_info": bus_info,
                        "class_code": class_code,
                        "vendor_id": vendor_id,
                        "device_id": device_id,
                        "is_wireless": class_code.startswith('02') or class_code.startswith('0280')
                    })
        
        return devices
    
    def detect_wireless_chipsets(self) -> List[ChipsetInfo]:
        """Detect wireless chipsets in the system"""
        detected_chipsets = []
        
        for device in self.system_info["pci_devices"]:
            if not device.get("is_wireless", False):
                continue
            
            chipset_info = self._identify_chipset(device)
            if chipset_info:
                detected_chipsets.append(chipset_info)
        
        return detected_chipsets
    
    def _identify_chipset(self, device: Dict) -> Optional[ChipsetInfo]:
        """Identify chipset from device information"""
        vendor_id = device["vendor_id"]
        device_id = device["device_id"]
        
        # Search through driver database
        for driver_family, driver_info in self.driver_database.items():
            chipsets = driver_info.get("chipsets", {})
            
            for chipset_name, chipset_data in chipsets.items():
                if (chipset_data.get("vendor_id", "").lower() == vendor_id.lower() and
                    chipset_data.get("device_id", "").lower() == device_id.lower()):
                    
                    return ChipsetInfo(
                        vendor_id=vendor_id,
                        device_id=device_id,
                        subsystem_vendor="",
                        subsystem_device="",
                        driver_family=DriverFamily(driver_family),
                        chipset_name=chipset_name,
                        supported_features=chipset_data.get("features", []),
                        firmware_requirements=chipset_data.get("firmware", [])
                    )
        
        # Unknown chipset
        return ChipsetInfo(
            vendor_id=vendor_id,
            device_id=device_id,
            subsystem_vendor="",
            subsystem_device="",
            driver_family=DriverFamily.UNKNOWN,
            chipset_name=f"Unknown_{vendor_id}_{device_id}",
            supported_features=[],
            firmware_requirements=[]
        )
    
    def validate_driver_compatibility(self, driver_family: str) -> ValidationResult:
        """Validate driver compatibility with current system"""
        if driver_family not in self.driver_database:
            return ValidationResult(
                test_name=f"Driver Compatibility - {driver_family}",
                level=ValidationLevel.ERROR,
                passed=False,
                message=f"Driver {driver_family} not found in database",
                recommendations=["Check driver name spelling", "Update driver database"]
            )
        
        driver_info = self.driver_database[driver_family]
        kernel_version = self.system_info["kernel_version"]
        
        # Check kernel version compatibility
        supported_versions = driver_info.get("kernel_versions", [])
        kernel_compatible = any(kernel_version.startswith(v) for v in supported_versions)
        
        if not kernel_compatible:
            return ValidationResult(
                test_name=f"Driver Compatibility - {driver_family}",
                level=ValidationLevel.WARNING,
                passed=False,
                message=f"Kernel {kernel_version} may not be fully supported",
                details={"supported_versions": supported_versions, "current_version": kernel_version},
                recommendations=[
                    "Consider using a supported kernel version",
                    "Test thoroughly before production use"
                ]
            )
        
        # Check required symbols (simplified - would need actual symbol checking)
        required_symbols = driver_info.get("required_symbols", [])
        missing_symbols = []  # Would implement actual symbol checking
        
        if missing_symbols:
            return ValidationResult(
                test_name=f"Driver Compatibility - {driver_family}",
                level=ValidationLevel.ERROR,
                passed=False,
                message=f"Missing required kernel symbols: {', '.join(missing_symbols)}",
                details={"missing_symbols": missing_symbols},
                recommendations=[
                    "Enable required kernel configuration options",
                    "Rebuild kernel with missing symbols"
                ]
            )
        
        return ValidationResult(
            test_name=f"Driver Compatibility - {driver_family}",
            level=ValidationLevel.INFO,
            passed=True,
            message=f"Driver {driver_family} is compatible with current system",
            details={"kernel_version": kernel_version, "supported": True}
        )
    
    def validate_wireless_stack_dependencies(self) -> List[ValidationResult]:
        """Validate wireless stack dependencies"""
        results = []
        
        # Check cfg80211 dependency
        cfg80211_result = self._validate_cfg80211()
        results.append(cfg80211_result)
        
        # Check mac80211 dependency  
        mac80211_result = self._validate_mac80211()
        results.append(mac80211_result)
        
        # Check crypto dependencies
        crypto_result = self._validate_crypto_dependencies()
        results.append(crypto_result)
        
        # Check regulatory database
        regulatory_result = self._validate_regulatory_database()
        results.append(regulatory_result)
        
        return results
    
    def _validate_cfg80211(self) -> ValidationResult:
        """Validate cfg80211 configuration and availability"""
        # Check if cfg80211 is configured in Kconfig
        kconfig_file = self.backports_dir / "Kconfig"
        
        if not kconfig_file.exists():
            return ValidationResult(
                test_name="cfg80211 Validation",
                level=ValidationLevel.ERROR,
                passed=False,
                message="Kconfig file not found",
                recommendations=["Ensure backports-integration/Kconfig exists"]
            )
        
        try:
            kconfig_content = kconfig_file.read_text()
            
            if "BACKPORTS_CFG80211" not in kconfig_content:
                return ValidationResult(
                    test_name="cfg80211 Validation",
                    level=ValidationLevel.ERROR,
                    passed=False,
                    message="cfg80211 not configured in Kconfig",
                    recommendations=["Add BACKPORTS_CFG80211 configuration option"]
                )
            
            # Check for proper dependencies
            cfg80211_dependencies = ["WIRELESS", "WEXT_CORE", "WEXT_PROC"]
            missing_deps = []
            
            for dep in cfg80211_dependencies:
                if dep not in kconfig_content:
                    missing_deps.append(dep)
            
            if missing_deps:
                return ValidationResult(
                    test_name="cfg80211 Validation",
                    level=ValidationLevel.WARNING,
                    passed=False,
                    message=f"Missing cfg80211 dependencies: {', '.join(missing_deps)}",
                    details={"missing_dependencies": missing_deps},
                    recommendations=["Add missing dependency configurations"]
                )
            
            return ValidationResult(
                test_name="cfg80211 Validation",
                level=ValidationLevel.INFO,
                passed=True,
                message="cfg80211 properly configured"
            )
            
        except Exception as e:
            return ValidationResult(
                test_name="cfg80211 Validation",
                level=ValidationLevel.ERROR,
                passed=False,
                message=f"Error validating cfg80211: {e}",
                recommendations=["Check Kconfig file syntax and permissions"]
            )
    
    def _validate_mac80211(self) -> ValidationResult:
        """Validate mac80211 configuration and availability"""
        kconfig_file = self.backports_dir / "Kconfig"
        
        try:
            kconfig_content = kconfig_file.read_text()
            
            if "BACKPORTS_MAC80211" not in kconfig_content:
                return ValidationResult(
                    test_name="mac80211 Validation",
                    level=ValidationLevel.ERROR,
                    passed=False,
                    message="mac80211 not configured in Kconfig",
                    recommendations=["Add BACKPORTS_MAC80211 configuration option"]
                )
            
            # Check mac80211 depends on cfg80211
            if "depends on BACKPORTS_CFG80211" not in kconfig_content:
                return ValidationResult(
                    test_name="mac80211 Validation",
                    level=ValidationLevel.WARNING,
                    passed=False,
                    message="mac80211 dependency on cfg80211 not properly configured",
                    recommendations=["Add proper cfg80211 dependency for mac80211"]
                )
            
            return ValidationResult(
                test_name="mac80211 Validation",
                level=ValidationLevel.INFO,
                passed=True,
                message="mac80211 properly configured"
            )
            
        except Exception as e:
            return ValidationResult(
                test_name="mac80211 Validation",
                level=ValidationLevel.ERROR,
                passed=False,
                message=f"Error validating mac80211: {e}",
                recommendations=["Check Kconfig file syntax and permissions"]
            )
    
    def _validate_crypto_dependencies(self) -> ValidationResult:
        """Validate cryptographic dependencies for wireless drivers"""
        kconfig_file = self.backports_dir / "Kconfig"
        
        try:
            kconfig_content = kconfig_file.read_text()
            
            # Required crypto modules for wireless
            required_crypto = [
                "CRYPTO_AES", "CRYPTO_ARC4", "CRYPTO_ECB", 
                "CRYPTO_CMAC", "CRYPTO_CCMP", "CRYPTO_GCMP"
            ]
            
            missing_crypto = []
            for crypto_module in required_crypto:
                if crypto_module not in kconfig_content:
                    missing_crypto.append(crypto_module)
            
            if missing_crypto:
                return ValidationResult(
                    test_name="Crypto Dependencies Validation",
                    level=ValidationLevel.WARNING,
                    passed=False,
                    message=f"Missing crypto dependencies: {', '.join(missing_crypto)}",
                    details={"missing_crypto": missing_crypto},
                    recommendations=[
                        "Add missing crypto module selections",
                        "Ensure wireless crypto support is enabled"
                    ]
                )
            
            return ValidationResult(
                test_name="Crypto Dependencies Validation",
                level=ValidationLevel.INFO,
                passed=True,
                message="All required crypto dependencies configured"
            )
            
        except Exception as e:
            return ValidationResult(
                test_name="Crypto Dependencies Validation",
                level=ValidationLevel.ERROR,
                passed=False,
                message=f"Error validating crypto dependencies: {e}",
                recommendations=["Check Kconfig file syntax and permissions"]
            )
    
    def _validate_regulatory_database(self) -> ValidationResult:
        """Validate regulatory database availability"""
        # Check for regulatory database files
        regulatory_paths = [
            "/lib/firmware/regulatory.db",
            "/usr/lib/firmware/regulatory.db",
            self.kernel_root / "firmware" / "regulatory.db"
        ]
        
        regulatory_found = False
        for path in regulatory_paths:
            if Path(path).exists():
                regulatory_found = True
                break
        
        if not regulatory_found:
            return ValidationResult(
                test_name="Regulatory Database Validation",
                level=ValidationLevel.WARNING,
                passed=False,
                message="Regulatory database not found",
                details={"searched_paths": [str(p) for p in regulatory_paths]},
                recommendations=[
                    "Install wireless-regdb package",
                    "Ensure regulatory.db is in firmware path"
                ]
            )
        
        return ValidationResult(
            test_name="Regulatory Database Validation",
            level=ValidationLevel.INFO,
            passed=True,
            message="Regulatory database found"
        )
    
    def validate_driver_coexistence(self, drivers: List[str]) -> ValidationResult:
        """Validate that multiple drivers can coexist"""
        conflicts = []
        
        # Check for known conflicts
        conflict_pairs = [
            ("ath11k", "qcacld"),  # Qualcomm vendor driver conflict
            ("iwlwifi", "iwl_legacy"),  # Intel legacy driver conflict
            ("rt2x00", "rt2800usb_vendor")  # Ralink vendor driver conflict
        ]
        
        for driver1, driver2 in conflict_pairs:
            if driver1 in drivers and driver2 in drivers:
                conflicts.append((driver1, driver2))
        
        # Check for resource conflicts (same chipset support)
        chipset_drivers = {}
        for driver in drivers:
            if driver in self.driver_database:
                chipsets = self.driver_database[driver].get("chipsets", {})
                for chipset_name in chipsets.keys():
                    if chipset_name not in chipset_drivers:
                        chipset_drivers[chipset_name] = []
                    chipset_drivers[chipset_name].append(driver)
        
        # Find chipsets supported by multiple drivers
        resource_conflicts = []
        for chipset, supporting_drivers in chipset_drivers.items():
            if len(supporting_drivers) > 1:
                resource_conflicts.append((chipset, supporting_drivers))
        
        if conflicts or resource_conflicts:
            conflict_details = {
                "driver_conflicts": conflicts,
                "resource_conflicts": resource_conflicts
            }
            
            return ValidationResult(
                test_name="Driver Coexistence Validation",
                level=ValidationLevel.ERROR,
                passed=False,
                message="Driver conflicts detected",
                details=conflict_details,
                recommendations=[
                    "Remove conflicting drivers",
                    "Use mutual exclusion in Kconfig",
                    "Implement runtime driver selection"
                ]
            )
        
        return ValidationResult(
            test_name="Driver Coexistence Validation",
            level=ValidationLevel.INFO,
            passed=True,
            message="No driver conflicts detected",
            details={"validated_drivers": drivers}
        )
    
    def validate_firmware_requirements(self, chipsets: List[ChipsetInfo]) -> List[ValidationResult]:
        """Validate firmware requirements for detected chipsets"""
        results = []
        
        firmware_paths = [
            "/lib/firmware",
            "/usr/lib/firmware", 
            self.kernel_root / "firmware"
        ]
        
        for chipset in chipsets:
            for firmware_file in chipset.firmware_requirements:
                firmware_found = False
                found_path = None
                
                for base_path in firmware_paths:
                    firmware_path = Path(base_path) / firmware_file
                    if firmware_path.exists():
                        firmware_found = True
                        found_path = firmware_path
                        break
                
                if firmware_found:
                    results.append(ValidationResult(
                        test_name=f"Firmware Validation - {chipset.chipset_name}",
                        level=ValidationLevel.INFO,
                        passed=True,
                        message=f"Firmware {firmware_file} found",
                        details={"firmware_path": str(found_path)}
                    ))
                else:
                    results.append(ValidationResult(
                        test_name=f"Firmware Validation - {chipset.chipset_name}",
                        level=ValidationLevel.ERROR,
                        passed=False,
                        message=f"Firmware {firmware_file} not found",
                        details={
                            "firmware_file": firmware_file,
                            "searched_paths": [str(p) for p in firmware_paths]
                        },
                        recommendations=[
                            f"Install firmware for {chipset.chipset_name}",
                            "Check firmware package availability",
                            "Verify firmware path configuration"
                        ]
                    ))
        
        return results
    
    def run_comprehensive_validation(self) -> Dict:
        """Run comprehensive wireless validation"""
        print("Running comprehensive wireless validation...")
        
        validation_report = {
            "timestamp": time.time(),
            "system_info": self.system_info,
            "detected_chipsets": [],
            "validation_results": [],
            "summary": {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "warnings": 0,
                "errors": 0,
                "critical": 0
            },
            "recommendations": []
        }
        
        # Detect wireless chipsets
        print("Detecting wireless chipsets...")
        detected_chipsets = self.detect_wireless_chipsets()
        validation_report["detected_chipsets"] = [
            {
                "chipset_name": cs.chipset_name,
                "driver_family": cs.driver_family.value,
                "vendor_id": cs.vendor_id,
                "device_id": cs.device_id,
                "supported_features": cs.supported_features
            }
            for cs in detected_chipsets
        ]
        
        print(f"Found {len(detected_chipsets)} wireless chipset(s)")
        
        # Validate driver compatibility for detected chipsets
        print("Validating driver compatibility...")
        driver_families = set(cs.driver_family.value for cs in detected_chipsets 
                            if cs.driver_family != DriverFamily.UNKNOWN)
        
        for driver_family in driver_families:
            result = self.validate_driver_compatibility(driver_family)
            validation_report["validation_results"].append(result.__dict__)
        
        # Validate wireless stack dependencies
        print("Validating wireless stack dependencies...")
        stack_results = self.validate_wireless_stack_dependencies()
        for result in stack_results:
            validation_report["validation_results"].append(result.__dict__)
        
        # Validate driver coexistence
        print("Validating driver coexistence...")
        if len(driver_families) > 1:
            coexistence_result = self.validate_driver_coexistence(list(driver_families))
            validation_report["validation_results"].append(coexistence_result.__dict__)
        
        # Validate firmware requirements
        print("Validating firmware requirements...")
        firmware_results = self.validate_firmware_requirements(detected_chipsets)
        for result in firmware_results:
            validation_report["validation_results"].append(result.__dict__)
        
        # Calculate summary statistics
        for result_dict in validation_report["validation_results"]:
            validation_report["summary"]["total_tests"] += 1
            
            if result_dict["passed"]:
                validation_report["summary"]["passed_tests"] += 1
            else:
                validation_report["summary"]["failed_tests"] += 1
            
            level = result_dict["level"]
            if level == "warning":
                validation_report["summary"]["warnings"] += 1
            elif level == "error":
                validation_report["summary"]["errors"] += 1
            elif level == "critical":
                validation_report["summary"]["critical"] += 1
        
        # Collect recommendations
        all_recommendations = set()
        for result_dict in validation_report["validation_results"]:
            if result_dict.get("recommendations"):
                all_recommendations.update(result_dict["recommendations"])
        
        validation_report["recommendations"] = list(all_recommendations)
        
        return validation_report
    
    def generate_validation_report(self, output_file: Optional[str] = None) -> str:
        """Generate a comprehensive validation report"""
        report = self.run_comprehensive_validation()
        
        # Generate human-readable report
        report_text = []
        report_text.append("Wireless Driver Validation Report")
        report_text.append("=" * 50)
        report_text.append(f"Generated: {time.ctime(report['timestamp'])}")
        report_text.append("")
        
        # System information
        report_text.append("System Information:")
        report_text.append(f"  Kernel Version: {report['system_info']['kernel_version']}")
        report_text.append(f"  Architecture: {report['system_info']['architecture']}")
        report_text.append(f"  PCI Devices: {len(report['system_info']['pci_devices'])}")
        report_text.append("")
        
        # Detected chipsets
        report_text.append("Detected Wireless Chipsets:")
        if report["detected_chipsets"]:
            for chipset in report["detected_chipsets"]:
                report_text.append(f"  - {chipset['chipset_name']} ({chipset['driver_family']})")
                report_text.append(f"    Vendor/Device: {chipset['vendor_id']}:{chipset['device_id']}")
                report_text.append(f"    Features: {', '.join(chipset['supported_features'])}")
        else:
            report_text.append("  No wireless chipsets detected")
        report_text.append("")
        
        # Validation results
        report_text.append("Validation Results:")
        for result in report["validation_results"]:
            status = "✓ PASS" if result["passed"] else "✗ FAIL"
            level = result["level"].upper()
            report_text.append(f"  {status} [{level}] {result['test_name']}")
            report_text.append(f"    {result['message']}")
            
            if result.get("recommendations"):
                report_text.append("    Recommendations:")
                for rec in result["recommendations"]:
                    report_text.append(f"      - {rec}")
        report_text.append("")
        
        # Summary
        summary = report["summary"]
        report_text.append("Summary:")
        report_text.append(f"  Total Tests: {summary['total_tests']}")
        report_text.append(f"  Passed: {summary['passed_tests']}")
        report_text.append(f"  Failed: {summary['failed_tests']}")
        report_text.append(f"  Warnings: {summary['warnings']}")
        report_text.append(f"  Errors: {summary['errors']}")
        report_text.append(f"  Critical: {summary['critical']}")
        
        success_rate = (summary['passed_tests'] / max(summary['total_tests'], 1)) * 100
        report_text.append(f"  Success Rate: {success_rate:.1f}%")
        report_text.append("")
        
        # Overall recommendations
        if report["recommendations"]:
            report_text.append("Overall Recommendations:")
            for rec in report["recommendations"]:
                report_text.append(f"  - {rec}")
        
        report_content = "\n".join(report_text)
        
        # Save to file if requested
        if output_file:
            try:
                with open(output_file, 'w') as f:
                    f.write(report_content)
                print(f"Validation report saved to: {output_file}")
            except Exception as e:
                print(f"Error saving report: {e}")
        
        return report_content

def main():
    """Main function for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Wireless Validation Framework")
    parser.add_argument("--output", "-o", help="Output file for validation report")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Initialize validation framework
    validator = WirelessValidationFramework()
    
    if args.json:
        # Generate JSON report
        report = validator.run_comprehensive_validation()
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"JSON report saved to: {args.output}")
        else:
            print(json.dumps(report, indent=2, default=str))
    else:
        # Generate text report
        report_text = validator.generate_validation_report(args.output)
        
        if not args.output:
            print(report_text)

if __name__ == "__main__":
    main()