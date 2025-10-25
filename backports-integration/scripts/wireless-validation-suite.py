#!/usr/bin/env python3
"""
Wireless Driver Registry Validation Suite

This script provides comprehensive validation of the wireless driver registry
and metadata system including capability checking and chipset detection.
"""

import sys
import os
from pathlib import Path

# Add the scripts directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from simple_capability_checker import SimpleCapabilityChecker
except ImportError:
    # Create a minimal capability checker if import fails
    class SimpleCapabilityChecker:
        def check_all_capabilities(self):
            return {
                "monitor_mode": False,
                "packet_injection": False,
                "mesh_networking": False,
                "wpa3_support": False,
                "spectral_scan": False
            }

try:
    from chipset_detector import ChipsetDetector
except ImportError:
    # Create a minimal chipset detector if import fails
    class ChipsetDetector:
        def detect_all_wireless_devices(self):
            return []
        def identify_chipset_model(self, device):
            return None
        def validate_chipset_support(self, device):
            return {"identified": False}

try:
    from wireless_driver_registry import WirelessDriverRegistry, DriverCapability
except ImportError:
    # Create minimal classes if import fails
    class DriverCapability:
        MONITOR_MODE = "monitor_mode"
        PACKET_INJECTION = "packet_injection"
    
    class WirelessDriverRegistry:
        def __init__(self):
            pass
        def list_drivers(self):
            return ["ath11k", "ath10k", "iwlwifi", "rt2x00"]
        def list_chipsets(self):
            return ["QCA6390", "QCA6490", "AX200"]
        def get_driver(self, name):
            return None
        def find_drivers_by_capability(self, cap):
            return []
        def validate_driver_compatibility(self, driver, version):
            return True
        def check_driver_conflicts(self, drivers):
            return []

def run_capability_validation():
    """Run capability validation tests"""
    print("Running capability validation tests...")
    
    checker = SimpleCapabilityChecker()
    capabilities = checker.check_all_capabilities()
    
    results = {
        "total_tests": len(capabilities),
        "passed": sum(1 for supported in capabilities.values() if supported),
        "failed": sum(1 for supported in capabilities.values() if not supported),
        "capabilities": capabilities
    }
    
    return results

def run_chipset_detection():
    """Run chipset detection tests"""
    print("Running chipset detection tests...")
    
    detector = ChipsetDetector()
    devices = detector.detect_all_wireless_devices()
    
    results = {
        "devices_found": len(devices),
        "devices": []
    }
    
    for device in devices:
        chipset_model = detector.identify_chipset_model(device)
        support_info = detector.validate_chipset_support(device)
        
        device_info = {
            "vendor": device.vendor_name,
            "device": device.device_name,
            "pci_id": device.pci_id,
            "interface": device.interface,
            "chipset_model": chipset_model,
            "driver": device.driver,
            "support": support_info
        }
        
        results["devices"].append(device_info)
    
    return results

def run_registry_validation():
    """Run driver registry validation tests"""
    print("Running driver registry validation tests...")
    
    registry = WirelessDriverRegistry()
    
    results = {
        "drivers_loaded": len(registry.list_drivers()),
        "chipsets_loaded": len(registry.list_chipsets()),
        "drivers": registry.list_drivers(),
        "chipsets": registry.list_chipsets(),
        "validation_errors": []
    }
    
    # Validate each driver
    for driver_name in registry.list_drivers():
        driver = registry.get_driver(driver_name)
        if not driver:
            results["validation_errors"].append(f"Could not load driver: {driver_name}")
            continue
        
        # Check if driver has required fields
        required_fields = ["name", "family", "vendor", "kernel_module", "dependencies"]
        for field in required_fields:
            if not hasattr(driver, field) or not getattr(driver, field):
                results["validation_errors"].append(f"Driver {driver_name} missing {field}")
        
        # Check chipsets
        if not driver.supported_chipsets:
            results["validation_errors"].append(f"Driver {driver_name} has no supported chipsets")
    
    # Test capability searches
    monitor_drivers = registry.find_drivers_by_capability(DriverCapability.MONITOR_MODE)
    injection_drivers = registry.find_drivers_by_capability(DriverCapability.PACKET_INJECTION)
    
    results["monitor_capable_drivers"] = len(monitor_drivers)
    results["injection_capable_drivers"] = len(injection_drivers)
    
    return results

def run_compatibility_tests():
    """Run driver compatibility tests"""
    print("Running compatibility tests...")
    
    registry = WirelessDriverRegistry()
    
    results = {
        "compatibility_tests": [],
        "conflict_tests": []
    }
    
    # Test kernel version compatibility
    test_versions = ["4.19", "5.4", "5.15", "6.1"]
    
    for driver_name in registry.list_drivers():
        for version in test_versions:
            compatible = registry.validate_driver_compatibility(driver_name, version)
            results["compatibility_tests"].append({
                "driver": driver_name,
                "kernel_version": version,
                "compatible": compatible
            })
    
    # Test driver conflicts
    driver_combinations = [
        ["ath11k", "ath10k"],
        ["ath11k", "qcacld"],
        ["iwlwifi", "ath11k"]
    ]
    
    for combo in driver_combinations:
        conflicts = registry.check_driver_conflicts(combo)
        results["conflict_tests"].append({
            "drivers": combo,
            "conflicts": conflicts
        })
    
    return results

def generate_report(results):
    """Generate a comprehensive validation report"""
    print("\n" + "=" * 60)
    print("WIRELESS DRIVER REGISTRY VALIDATION REPORT")
    print("=" * 60)
    
    # Capability validation results
    cap_results = results["capabilities"]
    print(f"\n📡 CAPABILITY VALIDATION")
    print(f"   Total Tests: {cap_results['total_tests']}")
    print(f"   Passed: {cap_results['passed']}")
    print(f"   Failed: {cap_results['failed']}")
    
    for capability, supported in cap_results["capabilities"].items():
        status = "✓" if supported else "✗"
        print(f"   {status} {capability.replace('_', ' ').title()}")
    
    # Chipset detection results
    chipset_results = results["chipsets"]
    print(f"\n🔍 CHIPSET DETECTION")
    print(f"   Devices Found: {chipset_results['devices_found']}")
    
    for device in chipset_results["devices"]:
        print(f"   • {device['vendor']} - {device['device']}")
        if device['chipset_model']:
            print(f"     Model: {device['chipset_model']}")
        if device['driver']:
            print(f"     Driver: {device['driver']}")
        
        support = device['support']
        supported_drivers = []
        if support['ath11k_supported']:
            supported_drivers.append('ath11k')
        if support['ath10k_supported']:
            supported_drivers.append('ath10k')
        if support['iwlwifi_supported']:
            supported_drivers.append('iwlwifi')
        if support['rt2x00_supported']:
            supported_drivers.append('rt2x00')
        
        if supported_drivers:
            print(f"     Supported Drivers: {', '.join(supported_drivers)}")
    
    # Registry validation results
    registry_results = results["registry"]
    print(f"\n📚 REGISTRY VALIDATION")
    print(f"   Drivers Loaded: {registry_results['drivers_loaded']}")
    print(f"   Chipsets Loaded: {registry_results['chipsets_loaded']}")
    print(f"   Monitor Capable Drivers: {registry_results['monitor_capable_drivers']}")
    print(f"   Injection Capable Drivers: {registry_results['injection_capable_drivers']}")
    
    if registry_results["validation_errors"]:
        print(f"   ⚠️  Validation Errors:")
        for error in registry_results["validation_errors"]:
            print(f"      - {error}")
    else:
        print(f"   ✓ No validation errors found")
    
    # Compatibility test results
    compat_results = results["compatibility"]
    print(f"\n🔧 COMPATIBILITY TESTS")
    
    # Group compatibility results by driver
    driver_compat = {}
    for test in compat_results["compatibility_tests"]:
        driver = test["driver"]
        if driver not in driver_compat:
            driver_compat[driver] = []
        driver_compat[driver].append(test)
    
    for driver, tests in driver_compat.items():
        compatible_versions = [t["kernel_version"] for t in tests if t["compatible"]]
        print(f"   {driver}: Compatible with kernels {', '.join(compatible_versions)}")
    
    # Conflict test results
    print(f"\n   Conflict Tests:")
    for test in compat_results["conflict_tests"]:
        drivers = " + ".join(test["drivers"])
        if test["conflicts"]:
            print(f"   ⚠️  {drivers}: {', '.join(test['conflicts'])}")
        else:
            print(f"   ✓ {drivers}: No conflicts")
    
    # Overall status
    total_errors = len(registry_results["validation_errors"])
    failed_caps = cap_results["failed"]
    
    print(f"\n" + "=" * 60)
    if total_errors == 0 and failed_caps == 0:
        print("🎉 VALIDATION PASSED - All tests successful!")
        return 0
    else:
        print(f"❌ VALIDATION FAILED - {total_errors} registry errors, {failed_caps} capability failures")
        return 1

def main():
    """Main validation function"""
    print("Wireless Driver Registry Validation Suite")
    print("=" * 50)
    
    try:
        # Run all validation tests
        results = {
            "capabilities": run_capability_validation(),
            "chipsets": run_chipset_detection(),
            "registry": run_registry_validation(),
            "compatibility": run_compatibility_tests()
        }
        
        # Generate comprehensive report
        exit_code = generate_report(results)
        return exit_code
        
    except Exception as e:
        print(f"❌ Validation suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())