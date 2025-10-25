#!/usr/bin/env python3
"""
Wireless Chipset Detection and Validation

This module provides functionality to detect wireless chipsets on the system
and validate their compatibility with available drivers.
"""

import re
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class DetectedChipset:
    """Information about a detected wireless chipset"""
    vendor_id: str
    device_id: str
    subsystem_vendor: str
    subsystem_device: str
    vendor_name: str
    device_name: str
    driver: Optional[str] = None
    interface: str = "Unknown"
    
    @property
    def pci_id(self) -> str:
        """Get the full PCI ID string"""
        return f"{self.vendor_id}:{self.device_id}"
    
    @property
    def full_id(self) -> str:
        """Get the full PCI ID with subsystem"""
        return f"{self.vendor_id}:{self.device_id}:{self.subsystem_vendor}:{self.subsystem_device}"

class ChipsetDetector:
    """Wireless chipset detection and validation system"""
    
    def __init__(self):
        """Initialize the chipset detector"""
        self.pci_database = self._load_pci_database()
        self.wireless_vendors = {
            "168c": "Qualcomm Atheros",
            "8086": "Intel Corporation", 
            "1814": "Ralink Technology",
            "0bda": "Realtek Semiconductor",
            "14e4": "Broadcom Corporation",
            "10ec": "Realtek Semiconductor",
            "1b21": "ASMedia Technology",
            "1033": "NEC Corporation"
        }
        
        # Known wireless chipset mappings
        self.chipset_mappings = {
            # Qualcomm Atheros ath11k
            "168c:1101": "QCA6390",
            "168c:1103": "QCA6490", 
            "168c:1104": "WCN6855",
            "168c:1105": "QCN9074",
            
            # Qualcomm Atheros ath10k
            "168c:003c": "QCA988X",
            "168c:003e": "QCA6174",
            "168c:0041": "QCA9377",
            "168c:0046": "QCA9984",
            "168c:0056": "QCA4019",
            
            # Qualcomm Atheros ath9k
            "168c:0029": "AR9280",
            "168c:002a": "AR9285",
            "168c:002b": "AR9287",
            "168c:0030": "AR9380",
            
            # Intel iwlwifi
            "8086:2723": "AX200",
            "8086:2725": "AX210",
            "8086:271b": "AX201",
            "8086:095a": "7265D",
            "8086:095b": "7265",
            "8086:24f3": "8260",
            "8086:24f4": "8265",
            "8086:2526": "9260",
            "8086:2720": "9560",
            
            # Ralink/MediaTek rt2x00
            "1814:3070": "RT3070",
            "1814:5370": "RT5370",
            "1814:5372": "RT5372",
            "1814:5592": "RT5592",
            "1814:7610": "MT7610U",
            "1814:7612": "MT7612U"
        }
    
    def _load_pci_database(self) -> Dict[str, str]:
        """Load PCI ID database for device name resolution"""
        pci_db = {}
        
        # Try to load from system pci.ids file
        pci_ids_paths = [
            "/usr/share/misc/pci.ids",
            "/usr/share/pci.ids", 
            "/var/lib/pciutils/pci.ids"
        ]
        
        for path in pci_ids_paths:
            if Path(path).exists():
                try:
                    with open(path, 'r') as f:
                        current_vendor = None
                        for line in f:
                            line = line.strip()
                            if not line or line.startswith('#'):
                                continue
                            
                            # Vendor line (no leading tab)
                            if not line.startswith('\t'):
                                match = re.match(r'^([0-9a-f]{4})\s+(.+)', line)
                                if match:
                                    current_vendor = match.group(1)
                                    pci_db[current_vendor] = match.group(2)
                            
                            # Device line (one leading tab)
                            elif line.startswith('\t') and not line.startswith('\t\t'):
                                if current_vendor:
                                    match = re.match(r'^\t([0-9a-f]{4})\s+(.+)', line)
                                    if match:
                                        device_id = match.group(1)
                                        device_name = match.group(2)
                                        pci_db[f"{current_vendor}:{device_id}"] = device_name
                    break
                except Exception as e:
                    print(f"Warning: Could not load PCI database from {path}: {e}")
                    continue
        
        return pci_db
    
    def _run_command(self, cmd: List[str]) -> Tuple[int, str, str]:
        """Run a system command and return exit code, stdout, stderr"""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except FileNotFoundError:
            return -1, "", f"Command not found: {cmd[0]}"
        except Exception as e:
            return -1, "", str(e)
    
    def detect_pci_wireless_devices(self) -> List[DetectedChipset]:
        """Detect wireless devices using lspci"""
        devices = []
        
        # Try lspci with different options
        lspci_commands = [
            ["lspci", "-nn", "-d", "::0280"],  # Network controller class
            ["lspci", "-nn", "-d", "::0200"],  # Ethernet controller class (some wireless)
        ]
        
        for cmd in lspci_commands:
            exit_code, stdout, stderr = self._run_command(cmd)
            if exit_code != 0:
                continue
            
            for line in stdout.strip().split('\n'):
                if not line:
                    continue
                
                device = self._parse_lspci_line(line)
                if device and self._is_wireless_device(device):
                    devices.append(device)
        
        return devices
    
    def _parse_lspci_line(self, line: str) -> Optional[DetectedChipset]:
        """Parse a single lspci output line"""
        # Example: 02:00.0 Network controller [0280]: Qualcomm Atheros QCA6390 [168c:1101] (rev 01)
        pattern = r'^([0-9a-f:\.]+)\s+([^[]+)\[([0-9a-f]{4})\]:\s+([^[]+)\[([0-9a-f]{4}):([0-9a-f]{4})\]'
        match = re.match(pattern, line)
        
        if not match:
            return None
        
        pci_slot = match.group(1)
        device_class = match.group(2).strip()
        class_id = match.group(3)
        vendor_device = match.group(4).strip()
        vendor_id = match.group(5)
        device_id = match.group(6)
        
        # Get subsystem IDs if available
        subsystem_vendor = "0000"
        subsystem_device = "0000"
        
        # Try to get more detailed info with lspci -vvv
        exit_code, stdout, stderr = self._run_command(["lspci", "-vvv", "-s", pci_slot])
        if exit_code == 0:
            for detail_line in stdout.split('\n'):
                if 'Subsystem:' in detail_line:
                    subsys_match = re.search(r'\[([0-9a-f]{4}):([0-9a-f]{4})\]', detail_line)
                    if subsys_match:
                        subsystem_vendor = subsys_match.group(1)
                        subsystem_device = subsys_match.group(2)
                        break
        
        vendor_name = self.wireless_vendors.get(vendor_id, f"Unknown ({vendor_id})")
        device_name = self.pci_database.get(f"{vendor_id}:{device_id}", vendor_device)
        
        return DetectedChipset(
            vendor_id=vendor_id,
            device_id=device_id,
            subsystem_vendor=subsystem_vendor,
            subsystem_device=subsystem_device,
            vendor_name=vendor_name,
            device_name=device_name,
            interface="PCIe"
        )
    
    def _is_wireless_device(self, device: DetectedChipset) -> bool:
        """Check if a device is a wireless network device"""
        # Check if vendor is known wireless vendor
        if device.vendor_id in self.wireless_vendors:
            return True
        
        # Check device name for wireless keywords
        wireless_keywords = [
            "wireless", "wifi", "wlan", "802.11", "atheros", "intel", "ralink", 
            "mediatek", "broadcom", "realtek", "qca", "wcn", "ax200", "ax210"
        ]
        
        device_name_lower = device.device_name.lower()
        return any(keyword in device_name_lower for keyword in wireless_keywords)
    
    def detect_usb_wireless_devices(self) -> List[DetectedChipset]:
        """Detect USB wireless devices using lsusb"""
        devices = []
        
        exit_code, stdout, stderr = self._run_command(["lsusb"])
        if exit_code != 0:
            return devices
        
        for line in stdout.strip().split('\n'):
            if not line:
                continue
            
            device = self._parse_lsusb_line(line)
            if device and self._is_wireless_device(device):
                devices.append(device)
        
        return devices
    
    def _parse_lsusb_line(self, line: str) -> Optional[DetectedChipset]:
        """Parse a single lsusb output line"""
        # Example: Bus 001 Device 003: ID 0bda:8179 Realtek Semiconductor Corp. RTL8188EUS 802.11n Wireless Network Adapter
        pattern = r'^Bus\s+\d+\s+Device\s+\d+:\s+ID\s+([0-9a-f]{4}):([0-9a-f]{4})\s+(.+)'
        match = re.match(pattern, line)
        
        if not match:
            return None
        
        vendor_id = match.group(1)
        device_id = match.group(2)
        device_description = match.group(3)
        
        vendor_name = self.wireless_vendors.get(vendor_id, f"Unknown ({vendor_id})")
        
        return DetectedChipset(
            vendor_id=vendor_id,
            device_id=device_id,
            subsystem_vendor="0000",
            subsystem_device="0000",
            vendor_name=vendor_name,
            device_name=device_description,
            interface="USB"
        )
    
    def identify_chipset_model(self, device: DetectedChipset) -> Optional[str]:
        """Identify the specific chipset model from PCI/USB IDs"""
        pci_id = device.pci_id
        return self.chipset_mappings.get(pci_id)
    
    def detect_current_driver(self, device: DetectedChipset) -> Optional[str]:
        """Detect the currently loaded driver for a device"""
        # Try to find the driver from sysfs
        pci_paths = [
            f"/sys/bus/pci/devices/0000:*",
            f"/sys/class/net/*/device"
        ]
        
        # This is a simplified implementation
        # In practice, you'd need to match the device to its sysfs entry
        try:
            exit_code, stdout, stderr = self._run_command(["lsmod"])
            if exit_code == 0:
                # Look for common wireless drivers
                wireless_drivers = ["ath11k", "ath10k", "ath9k", "iwlwifi", "rt2x00", "rtl8xxxu"]
                loaded_drivers = []
                
                for line in stdout.split('\n'):
                    for driver in wireless_drivers:
                        if line.startswith(driver):
                            loaded_drivers.append(driver)
                
                # Simple heuristic: match vendor to likely driver
                if device.vendor_id == "168c":  # Qualcomm Atheros
                    for driver in ["ath11k", "ath10k", "ath9k"]:
                        if driver in loaded_drivers:
                            return driver
                elif device.vendor_id == "8086":  # Intel
                    if "iwlwifi" in loaded_drivers:
                        return "iwlwifi"
                elif device.vendor_id == "1814":  # Ralink
                    for driver in ["rt2x00", "rt2800usb"]:
                        if driver in loaded_drivers:
                            return driver
        
        except Exception:
            pass
        
        return None
    
    def detect_all_wireless_devices(self) -> List[DetectedChipset]:
        """Detect all wireless devices (PCI and USB)"""
        devices = []
        
        # Detect PCI devices
        pci_devices = self.detect_pci_wireless_devices()
        devices.extend(pci_devices)
        
        # Detect USB devices
        usb_devices = self.detect_usb_wireless_devices()
        devices.extend(usb_devices)
        
        # Enhance device information
        for device in devices:
            chipset_model = self.identify_chipset_model(device)
            if chipset_model:
                device.device_name = f"{device.device_name} ({chipset_model})"
            
            current_driver = self.detect_current_driver(device)
            if current_driver:
                device.driver = current_driver
        
        return devices
    
    def validate_chipset_support(self, device: DetectedChipset) -> Dict[str, bool]:
        """Validate if a chipset is supported by available drivers"""
        chipset_model = self.identify_chipset_model(device)
        
        support_info = {
            "identified": chipset_model is not None,
            "ath11k_supported": False,
            "ath10k_supported": False,
            "iwlwifi_supported": False,
            "rt2x00_supported": False,
            "monitor_mode": False,
            "packet_injection": False
        }
        
        if not chipset_model:
            return support_info
        
        # Check support based on chipset model
        ath11k_chipsets = ["QCA6390", "QCA6490", "WCN6855", "QCN9074"]
        ath10k_chipsets = ["QCA988X", "QCA6174", "QCA9377", "QCA9984", "QCA4019"]
        iwlwifi_chipsets = ["AX200", "AX210", "AX201", "7265D", "7265", "8260", "8265", "9260", "9560"]
        rt2x00_chipsets = ["RT3070", "RT5370", "RT5372", "RT5592", "MT7610U", "MT7612U"]
        
        if chipset_model in ath11k_chipsets:
            support_info["ath11k_supported"] = True
            support_info["monitor_mode"] = True
            support_info["packet_injection"] = True
        elif chipset_model in ath10k_chipsets:
            support_info["ath10k_supported"] = True
            support_info["monitor_mode"] = True
            support_info["packet_injection"] = True
        elif chipset_model in iwlwifi_chipsets:
            support_info["iwlwifi_supported"] = True
            support_info["monitor_mode"] = True  # Limited support
        elif chipset_model in rt2x00_chipsets:
            support_info["rt2x00_supported"] = True
            support_info["monitor_mode"] = True
            support_info["packet_injection"] = True
        
        return support_info

def main():
    """Main function for testing chipset detection"""
    detector = ChipsetDetector()
    
    print("Wireless Chipset Detection")
    print("=" * 50)
    
    devices = detector.detect_all_wireless_devices()
    
    if not devices:
        print("No wireless devices detected.")
        return
    
    for i, device in enumerate(devices, 1):
        print(f"\nDevice {i}:")
        print(f"  Interface: {device.interface}")
        print(f"  Vendor: {device.vendor_name} ({device.vendor_id})")
        print(f"  Device: {device.device_name}")
        print(f"  PCI ID: {device.pci_id}")
        print(f"  Full ID: {device.full_id}")
        
        if device.driver:
            print(f"  Current Driver: {device.driver}")
        
        chipset_model = detector.identify_chipset_model(device)
        if chipset_model:
            print(f"  Chipset Model: {chipset_model}")
        
        support = detector.validate_chipset_support(device)
        print(f"  Support Info:")
        print(f"    Identified: {support['identified']}")
        print(f"    ath11k: {support['ath11k_supported']}")
        print(f"    ath10k: {support['ath10k_supported']}")
        print(f"    iwlwifi: {support['iwlwifi_supported']}")
        print(f"    rt2x00: {support['rt2x00_supported']}")
        print(f"    Monitor Mode: {support['monitor_mode']}")
        print(f"    Packet Injection: {support['packet_injection']}")

if __name__ == "__main__":
    main()