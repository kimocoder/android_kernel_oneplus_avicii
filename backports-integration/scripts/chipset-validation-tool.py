#!/usr/bin/env python3
"""
Chipset Detection and Validation Tool

This tool provides comprehensive chipset detection, validation, and compatibility
checking for wireless devices in the system.
"""

import os
import sys
import subprocess
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import tempfile

@dataclass
class ChipsetDetails:
    """Detailed chipset information"""
    bus_info: str
    vendor_id: str
    device_id: str
    subsystem_vendor: str
    subsystem_device: str
    class_code: str
    driver_in_use: str
    driver_modules: List[str]
    chipset_name: str
    manufacturer: str
    generation: str
    supported_standards: List[str]
    max_spatial_streams: int
    supported_bands: List[str]
    monitor_mode_support: bool
    injection_support: bool
    mesh_support: bool
    firmware_files: List[str]
    power_management: Dict[str, bool]
    regulatory_domains: List[str]

class ChipsetValidationTool:
    """Comprehensive chipset detection and validation tool"""
    
    def __init__(self):
        """Initialize the chipset validation tool"""
        self.chipset_database = self._load_chipset_database()
        self.vendor_names = self._load_vendor_names()
        
    def _load_chipset_database(self) -> Dict:
        """Load comprehensive chipset database"""
        return {
            # Qualcomm Atheros chipsets
            "168c:003c": {  # QCA988X
                "name": "QCA988X",
                "manufacturer": "Qualcomm Atheros",
                "generation": "802.11ac Wave 1",
                "standards": ["802.11a", "802.11b", "802.11g", "802.11n", "802.11ac"],
                "spatial_streams": 3,
                "bands": ["2.4GHz", "5GHz"],
                "monitor_mode": True,
                "injection": True,
                "mesh": True,
                "firmware": ["ath10k/QCA988X/hw2.0/firmware-5.bin", "ath10k/QCA988X/hw2.0/board.bin"],
                "power_management": {"runtime_pm": True, "wowlan": True},
                "regulatory": ["US", "EU", "JP", "CN"]
            },
            "168c:003e": {  # QCA6174
                "name": "QCA6174",
                "manufacturer": "Qualcomm Atheros", 
                "generation": "802.11ac Wave 1",
                "standards": ["802.11a", "802.11b", "802.11g", "802.11n", "802.11ac"],
                "spatial_streams": 2,
                "bands": ["2.4GHz", "5GHz"],
                "monitor_mode": True,
                "injection": True,
                "mesh": False,
                "firmware": ["ath10k/QCA6174/hw3.0/firmware-6.bin", "ath10k/QCA6174/hw3.0/board.bin"],
                "power_management": {"runtime_pm": True, "wowlan": True},
                "regulatory": ["US", "EU", "JP"]
            },
            "17cb:1101": {  # QCA6390
                "name": "QCA6390",
                "manufacturer": "Qualcomm Atheros",
                "generation": "802.11ax (Wi-Fi 6)",
                "standards": ["802.11a", "802.11b", "802.11g", "802.11n", "802.11ac", "802.11ax"],
                "spatial_streams": 2,
                "bands": ["2.4GHz", "5GHz"],
                "monitor_mode": True,
                "injection": True,
                "mesh": True,
                "firmware": ["ath11k/QCA6390/hw2.0/amss.bin", "ath11k/QCA6390/hw2.0/m3.bin"],
                "power_management": {"runtime_pm": True, "wowlan": True, "deep_sleep": True},
                "regulatory": ["US", "EU", "JP", "CN", "KR"]
            },
            "17cb:1103": {  # QCA6490
                "name": "QCA6490",
                "manufacturer": "Qualcomm Atheros",
                "generation": "802.11ax (Wi-Fi 6E)",
                "standards": ["802.11a", "802.11b", "802.11g", "802.11n", "802.11ac", "802.11ax"],
                "spatial_streams": 2,
                "bands": ["2.4GHz", "5GHz", "6GHz"],
                "monitor_mode": True,
                "injection": True,
                "mesh": True,
                "firmware": ["ath11k/QCA6490/hw2.0/amss.bin", "ath11k/QCA6490/hw2.0/m3.bin"],
                "power_management": {"runtime_pm": True, "wowlan": True, "deep_sleep": True},
                "regulatory": ["US", "EU", "JP", "CN", "KR"]
            },
            # Intel chipsets
            "8086:2723": {  # AX200
                "name": "Intel Wi-Fi 6 AX200",
                "manufacturer": "Intel",
                "generation": "802.11ax (Wi-Fi 6)",
                "standards": ["802.11a", "802.11b", "802.11g", "802.11n", "802.11ac", "802.11ax"],
                "spatial_streams": 2,
                "bands": ["2.4GHz", "5GHz"],
                "monitor_mode": True,
                "injection": False,
                "mesh": False,
                "firmware": ["iwlwifi-cc-a0-63.ucode"],
                "power_management": {"runtime_pm": True, "wowlan": True, "d3_cold": True},
                "regulatory": ["US", "EU", "JP"]
            },
            "8086:2725": {  # AX210
                "name": "Intel Wi-Fi 6E AX210",
                "manufacturer": "Intel",
                "generation": "802.11ax (Wi-Fi 6E)",
                "standards": ["802.11a", "802.11b", "802.11g", "802.11n", "802.11ac", "802.11ax"],
                "spatial_streams": 2,
                "bands": ["2.4GHz", "5GHz", "6GHz"],
                "monitor_mode": True,
                "injection": False,
                "mesh": False,
                "firmware": ["iwlwifi-ty-a0-gf-a0-63.ucode"],
                "power_management": {"runtime_pm": True, "wowlan": True, "d3_cold": True},
                "regulatory": ["US", "EU", "JP"]
            },
            # Ralink/MediaTek chipsets
            "1814:3070": {  # RT3070
                "name": "RT3070",
                "manufacturer": "Ralink/MediaTek",
                "generation": "802.11n",
                "standards": ["802.11a", "802.11b", "802.11g", "802.11n"],
                "spatial_streams": 1,
                "bands": ["2.4GHz", "5GHz"],
                "monitor_mode": True,
                "injection": True,
                "mesh": True,
                "firmware": ["rt2870.bin"],
                "power_management": {"runtime_pm": False, "wowlan": False},
                "regulatory": ["US", "EU", "JP"]
            }
        }
    
    def _load_vendor_names(self) -> Dict[str, str]:
        """Load PCI vendor ID to name mapping"""
        return {
            "168c": "Qualcomm Atheros",
            "17cb": "Qualcomm Atheros", 
            "8086": "Intel Corporation",
            "1814": "Ralink Technology",
            "14e4": "Broadcom Corporation",
            "10ec": "Realtek Semiconductor"
        }
    
    def detect_wireless_devices(self) -> List[Dict]:
        """Detect all wireless devices in the system"""
        devices = []
        
        try:
            # Use lspci to get PCI devices
            result = subprocess.run(["lspci", "-nnv"], capture_output=True, text=True)
            if result.returncode != 0:
                print("Warning: Could not run lspci")
                return devices
            
            current_device = {}
            for line in result.stdout.split('\n'):
                line = line.strip()
                
                # New device entry
                if re.match(r'^[0-9a-f]{2}:[0-9a-f]{2}\.[0-9a-f]', line):
                    if current_device and self._is_wireless_device(current_device):
                        devices.append(current_device)
                    
                    # Parse device line: "00:14.3 Network controller [0280]: Intel Corporation ..."
                    parts = line.split(': ', 1)
                    if len(parts) >= 2:
                        bus_info = parts[0].split()[0]
                        device_info = parts[1]
                        
                        current_device = {
                            "bus_info": bus_info,
                            "description": device_info,
                            "vendor_id": "",
                            "device_id": "",
                            "subsystem_vendor": "",
                            "subsystem_device": "",
                            "class_code": "",
                            "driver": "",
                            "modules": []
                        }
                        
                        # Extract vendor:device IDs from brackets
                        id_match = re.search(r'\[([0-9a-f]{4}):([0-9a-f]{4})\]', line)
                        if id_match:
                            current_device["vendor_id"] = id_match.group(1)
                            current_device["device_id"] = id_match.group(2)
                
                # Parse additional device information
                elif current_device:
                    if line.startswith("Subsystem:"):
                        subsys_match = re.search(r'\[([0-9a-f]{4}):([0-9a-f]{4})\]', line)
                        if subsys_match:
                            current_device["subsystem_vendor"] = subsys_match.group(1)
                            current_device["subsystem_device"] = subsys_match.group(2)
                    
                    elif line.startswith("Kernel driver in use:"):
                        current_device["driver"] = line.split(": ", 1)[1]
                    
                    elif line.startswith("Kernel modules:"):
                        modules = line.split(": ", 1)[1].split(", ")
                        current_device["modules"] = modules
            
            # Don't forget the last device
            if current_device and self._is_wireless_device(current_device):
                devices.append(current_device)
        
        except Exception as e:
            print(f"Error detecting wireless devices: {e}")
        
        return devices
    
    def _is_wireless_device(self, device: Dict) -> bool:
        """Check if device is a wireless network device"""
        description = device.get("description", "").lower()
        
        # Check for wireless keywords
        wireless_keywords = [
            "wireless", "wi-fi", "wifi", "802.11", "wlan", 
            "network controller", "ethernet controller"
        ]
        
        # Check class code (0280 = Network controller, wireless)
        if "0280" in description:
            return True
        
        # Check description for wireless keywords
        return any(keyword in description for keyword in wireless_keywords)
    
    def get_chipset_details(self, device: Dict) -> ChipsetDetails:
        """Get detailed information about a chipset"""
        vendor_id = device.get("vendor_id", "")
        device_id = device.get("device_id", "")
        chipset_key = f"{vendor_id}:{device_id}"
        
        # Look up in database
        chipset_info = self.chipset_database.get(chipset_key, {})
        
        # Get vendor name
        vendor_name = self.vendor_names.get(vendor_id, f"Unknown ({vendor_id})")
        
        # Create detailed chipset information
        details = ChipsetDetails(
            bus_info=device.get("bus_info", ""),
            vendor_id=vendor_id,
            device_id=device_id,
            subsystem_vendor=device.get("subsystem_vendor", ""),
            subsystem_device=device.get("subsystem_device", ""),
            class_code="0280",  # Wireless network controller
            driver_in_use=device.get("driver", ""),
            driver_modules=device.get("modules", []),
            chipset_name=chipset_info.get("name", f"Unknown_{vendor_id}_{device_id}"),
            manufacturer=chipset_info.get("manufacturer", vendor_name),
            generation=chipset_info.get("generation", "Unknown"),
            supported_standards=chipset_info.get("standards", []),
            max_spatial_streams=chipset_info.get("spatial_streams", 0),
            supported_bands=chipset_info.get("bands", []),
            monitor_mode_support=chipset_info.get("monitor_mode", False),
            injection_support=chipset_info.get("injection", False),
            mesh_support=chipset_info.get("mesh", False),
            firmware_files=chipset_info.get("firmware", []),
            power_management=chipset_info.get("power_management", {}),
            regulatory_domains=chipset_info.get("regulatory", [])
        )
        
        return details
    
    def validate_chipset_support(self, chipset: ChipsetDetails) -> Dict:
        """Validate chipset support and compatibility"""
        validation = {
            "chipset_name": chipset.chipset_name,
            "supported": False,
            "driver_available": False,
            "firmware_available": False,
            "issues": [],
            "recommendations": [],
            "capabilities": {
                "monitor_mode": chipset.monitor_mode_support,
                "packet_injection": chipset.injection_support,
                "mesh_networking": chipset.mesh_support
            }
        }
        
        # Check if chipset is in database (known/supported)
        chipset_key = f"{chipset.vendor_id}:{chipset.device_id}"
        if chipset_key in self.chipset_database:
            validation["supported"] = True
        else:
            validation["issues"].append("Chipset not in supported database")
            validation["recommendations"].append("Check for driver updates or community support")
        
        # Check driver availability
        if chipset.driver_in_use:
            validation["driver_available"] = True
        elif chipset.driver_modules:
            validation["driver_available"] = True
            validation["issues"].append("Driver modules available but not loaded")
            validation["recommendations"].append("Load appropriate driver module")
        else:
            validation["issues"].append("No driver available for this chipset")
            validation["recommendations"].append("Install appropriate wireless driver")
        
        # Check firmware availability
        firmware_found = []
        firmware_missing = []
        
        firmware_paths = ["/lib/firmware", "/usr/lib/firmware"]
        
        for firmware_file in chipset.firmware_files:
            found = False
            for base_path in firmware_paths:
                firmware_path = Path(base_path) / firmware_file
                if firmware_path.exists():
                    firmware_found.append(firmware_file)
                    found = True
                    break
            
            if not found:
                firmware_missing.append(firmware_file)
        
        if chipset.firmware_files:
            if firmware_missing:
                validation["issues"].append(f"Missing firmware files: {', '.join(firmware_missing)}")
                validation["recommendations"].append("Install missing firmware files")
            else:
                validation["firmware_available"] = True
        else:
            validation["firmware_available"] = True  # No firmware required
        
        # Additional validation checks
        if not chipset.supported_standards:
            validation["issues"].append("No supported wireless standards information")
        
        if chipset.max_spatial_streams == 0:
            validation["issues"].append("Spatial streams information not available")
        
        if not chipset.supported_bands:
            validation["issues"].append("Supported frequency bands information not available")
        
        return validation
    
    def check_driver_conflicts(self, devices: List[ChipsetDetails]) -> Dict:
        """Check for potential driver conflicts"""
        conflicts = {
            "conflicts_found": False,
            "conflict_details": [],
            "recommendations": []
        }
        
        # Group devices by driver
        drivers_in_use = {}
        for device in devices:
            if device.driver_in_use:
                if device.driver_in_use not in drivers_in_use:
                    drivers_in_use[device.driver_in_use] = []
                drivers_in_use[device.driver_in_use].append(device)
        
        # Check for known problematic combinations
        problematic_combinations = [
            ("ath11k", "qcacld"),
            ("ath10k", "qcacld"),
            ("iwlwifi", "iwl_legacy"),
            ("rt2x00usb", "rt2800usb")
        ]
        
        active_drivers = set(drivers_in_use.keys())
        
        for driver1, driver2 in problematic_combinations:
            if driver1 in active_drivers and driver2 in active_drivers:
                conflicts["conflicts_found"] = True
                conflicts["conflict_details"].append({
                    "type": "driver_conflict",
                    "drivers": [driver1, driver2],
                    "description": f"Conflicting drivers {driver1} and {driver2} both active"
                })
                conflicts["recommendations"].append(f"Disable either {driver1} or {driver2}")
        
        # Check for multiple devices using same driver (potential resource conflict)
        for driver, device_list in drivers_in_use.items():
            if len(device_list) > 1:
                conflicts["conflict_details"].append({
                    "type": "resource_sharing",
                    "driver": driver,
                    "devices": [d.chipset_name for d in device_list],
                    "description": f"Multiple devices using driver {driver}"
                })
                conflicts["recommendations"].append(f"Verify {driver} supports multiple devices")
        
        return conflicts
    
    def generate_compatibility_report(self, output_file: Optional[str] = None) -> str:
        """Generate comprehensive compatibility report"""
        print("Detecting wireless devices...")
        devices = self.detect_wireless_devices()
        
        if not devices:
            report = "No wireless devices detected in the system.\n"
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(report)
            return report
        
        print(f"Found {len(devices)} wireless device(s)")
        
        # Get detailed information for each device
        chipset_details = []
        for device in devices:
            details = self.get_chipset_details(device)
            chipset_details.append(details)
        
        # Generate report
        report_lines = []
        report_lines.append("Wireless Chipset Compatibility Report")
        report_lines.append("=" * 50)
        report_lines.append(f"Generated: {time.ctime()}")
        report_lines.append("")
        
        # Device summary
        report_lines.append("Detected Wireless Devices:")
        for i, chipset in enumerate(chipset_details, 1):
            report_lines.append(f"{i}. {chipset.chipset_name}")
            report_lines.append(f"   Bus: {chipset.bus_info}")
            report_lines.append(f"   Vendor/Device: {chipset.vendor_id}:{chipset.device_id}")
            report_lines.append(f"   Manufacturer: {chipset.manufacturer}")
            report_lines.append(f"   Generation: {chipset.generation}")
            report_lines.append(f"   Driver: {chipset.driver_in_use or 'None'}")
            report_lines.append("")
        
        # Detailed validation for each chipset
        report_lines.append("Chipset Validation Results:")
        report_lines.append("-" * 30)
        
        for chipset in chipset_details:
            validation = self.validate_chipset_support(chipset)
            
            report_lines.append(f"Chipset: {chipset.chipset_name}")
            report_lines.append(f"  Supported: {'✓' if validation['supported'] else '✗'}")
            report_lines.append(f"  Driver Available: {'✓' if validation['driver_available'] else '✗'}")
            report_lines.append(f"  Firmware Available: {'✓' if validation['firmware_available'] else '✗'}")
            
            # Capabilities
            caps = validation['capabilities']
            report_lines.append("  Capabilities:")
            report_lines.append(f"    Monitor Mode: {'✓' if caps['monitor_mode'] else '✗'}")
            report_lines.append(f"    Packet Injection: {'✓' if caps['packet_injection'] else '✗'}")
            report_lines.append(f"    Mesh Networking: {'✓' if caps['mesh_networking'] else '✗'}")
            
            # Issues and recommendations
            if validation['issues']:
                report_lines.append("  Issues:")
                for issue in validation['issues']:
                    report_lines.append(f"    - {issue}")
            
            if validation['recommendations']:
                report_lines.append("  Recommendations:")
                for rec in validation['recommendations']:
                    report_lines.append(f"    - {rec}")
            
            report_lines.append("")
        
        # Driver conflict analysis
        conflicts = self.check_driver_conflicts(chipset_details)
        report_lines.append("Driver Conflict Analysis:")
        report_lines.append("-" * 25)
        
        if conflicts['conflicts_found']:
            report_lines.append("⚠️  Conflicts detected:")
            for conflict in conflicts['conflict_details']:
                report_lines.append(f"  - {conflict['description']}")
            
            report_lines.append("Recommendations:")
            for rec in conflicts['recommendations']:
                report_lines.append(f"  - {rec}")
        else:
            report_lines.append("✓ No driver conflicts detected")
        
        report_lines.append("")
        
        # Summary
        supported_count = sum(1 for cs in chipset_details 
                            if f"{cs.vendor_id}:{cs.device_id}" in self.chipset_database)
        
        report_lines.append("Summary:")
        report_lines.append(f"  Total Devices: {len(chipset_details)}")
        report_lines.append(f"  Supported Chipsets: {supported_count}")
        report_lines.append(f"  Driver Conflicts: {'Yes' if conflicts['conflicts_found'] else 'No'}")
        
        report_content = "\n".join(report_lines)
        
        # Save to file if requested
        if output_file:
            try:
                with open(output_file, 'w') as f:
                    f.write(report_content)
                print(f"Compatibility report saved to: {output_file}")
            except Exception as e:
                print(f"Error saving report: {e}")
        
        return report_content
    
    def export_chipset_data(self, format_type: str = "json", output_file: Optional[str] = None) -> str:
        """Export chipset data in various formats"""
        devices = self.detect_wireless_devices()
        chipset_details = [self.get_chipset_details(device) for device in devices]
        
        if format_type.lower() == "json":
            data = {
                "timestamp": time.time(),
                "chipsets": [asdict(chipset) for chipset in chipset_details]
            }
            
            output = json.dumps(data, indent=2, default=str)
        
        elif format_type.lower() == "csv":
            import csv
            import io
            
            output_buffer = io.StringIO()
            writer = csv.writer(output_buffer)
            
            # Write header
            writer.writerow([
                "Bus Info", "Vendor ID", "Device ID", "Chipset Name", 
                "Manufacturer", "Generation", "Driver", "Monitor Mode",
                "Injection", "Mesh Support"
            ])
            
            # Write data
            for chipset in chipset_details:
                writer.writerow([
                    chipset.bus_info, chipset.vendor_id, chipset.device_id,
                    chipset.chipset_name, chipset.manufacturer, chipset.generation,
                    chipset.driver_in_use, chipset.monitor_mode_support,
                    chipset.injection_support, chipset.mesh_support
                ])
            
            output = output_buffer.getvalue()
        
        else:
            raise ValueError(f"Unsupported format: {format_type}")
        
        # Save to file if requested
        if output_file:
            try:
                with open(output_file, 'w') as f:
                    f.write(output)
                print(f"Chipset data exported to: {output_file}")
            except Exception as e:
                print(f"Error exporting data: {e}")
        
        return output

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Chipset Detection and Validation Tool")
    parser.add_argument("--report", "-r", help="Generate compatibility report")
    parser.add_argument("--export", "-e", help="Export chipset data")
    parser.add_argument("--format", "-f", choices=["json", "csv"], default="json", 
                       help="Export format (default: json)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    tool = ChipsetValidationTool()
    
    if args.report:
        report = tool.generate_compatibility_report(args.report)
        if not args.report:
            print(report)
    
    elif args.export:
        data = tool.export_chipset_data(args.format, args.export)
        if not args.export:
            print(data)
    
    else:
        # Default: show detected devices
        devices = tool.detect_wireless_devices()
        
        if devices:
            print(f"Detected {len(devices)} wireless device(s):")
            for device in devices:
                chipset = tool.get_chipset_details(device)
                print(f"  - {chipset.chipset_name} ({chipset.manufacturer})")
                print(f"    Bus: {chipset.bus_info}")
                print(f"    Driver: {chipset.driver_in_use or 'None'}")
                print(f"    Capabilities: Monitor={'✓' if chipset.monitor_mode_support else '✗'}, "
                      f"Injection={'✓' if chipset.injection_support else '✗'}, "
                      f"Mesh={'✓' if chipset.mesh_support else '✗'}")
        else:
            print("No wireless devices detected")

if __name__ == "__main__":
    import time
    main()