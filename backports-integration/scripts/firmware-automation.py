#!/usr/bin/env python3
"""
Firmware Download and Installation Automation

This script provides automated firmware download, validation, and installation
for wireless drivers with comprehensive error handling and retry mechanisms.
"""

import os
import sys
import subprocess
import json
import hashlib
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import tempfile
import shutil

@dataclass
class FirmwareFile:
    """Firmware file information"""
    name: str
    url: str
    checksum_md5: Optional[str] = None
    checksum_sha256: Optional[str] = None
    size: Optional[int] = None
    required: bool = True

@dataclass
class DownloadResult:
    """Download result information"""
    success: bool
    file_path: str
    size: int
    download_time: float
    checksum_valid: bool
    error: Optional[str] = None

class FirmwareAutomation:
    """Automated firmware management system"""
    
    def __init__(self, kernel_root: str = "."):
        """Initialize firmware automation"""
        self.kernel_root = Path(kernel_root).resolve()
        self.backports_dir = self.kernel_root / "backports-integration"
        self.firmware_dir = Path("/lib/firmware")
        self.temp_dir = Path(tempfile.gettempdir()) / "wireless-firmware"
        
        # Load configuration
        self.config = self._load_config()
        
        # Firmware database
        self.firmware_db = self._load_firmware_database()
    
    def _load_config(self) -> Dict:
        """Load automation configuration"""
        config_file = self.backports_dir / "configs" / "firmware-automation.json"
        
        default_config = {
            "download_timeout": 300,
            "retry_attempts": 3,
            "retry_delay": 5,
            "validate_checksums": True,
            "backup_existing": True,
            "parallel_downloads": 4,
            "base_urls": [
                "https://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git/plain/",
                "https://github.com/kvalo/ath11k-firmware/raw/master/",
                "https://github.com/kvalo/ath10k-firmware/raw/master/"
            ],
            "user_agent": "WirelessFirmwareAutomation/1.0"
        }
        
        try:
            if config_file.exists():
                with open(config_file, 'r') as f:
                    loaded_config = json.load(f)
                default_config.update(loaded_config)
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
        
        return default_config
    
    def _load_firmware_database(self) -> Dict:
        """Load firmware database"""
        return {
            "ath11k": {
                "QCA6390": [
                    FirmwareFile("ath11k/QCA6390/hw2.0/amss.bin", 
                               "ath11k/QCA6390/hw2.0/amss.bin", required=True),
                    FirmwareFile("ath11k/QCA6390/hw2.0/m3.bin",
                               "ath11k/QCA6390/hw2.0/m3.bin", required=True),
                    FirmwareFile("ath11k/QCA6390/hw2.0/board-2.bin",
                               "ath11k/QCA6390/hw2.0/board-2.bin", required=False)
                ],
                "QCA6490": [
                    FirmwareFile("ath11k/QCA6490/hw2.0/amss.bin",
                               "ath11k/QCA6490/hw2.0/amss.bin", required=True),
                    FirmwareFile("ath11k/QCA6490/hw2.0/m3.bin", 
                               "ath11k/QCA6490/hw2.0/m3.bin", required=True)
                ],
                "WCN6855": [
                    FirmwareFile("ath11k/WCN6855/hw2.0/amss.bin",
                               "ath11k/WCN6855/hw2.0/amss.bin", required=True),
                    FirmwareFile("ath11k/WCN6855/hw2.0/m3.bin",
                               "ath11k/WCN6855/hw2.0/m3.bin", required=True)
                ]
            },
            "ath10k": {
                "QCA988X": [
                    FirmwareFile("ath10k/QCA988X/hw2.0/firmware-5.bin",
                               "ath10k/QCA988X/hw2.0/firmware-5.bin", required=True),
                    FirmwareFile("ath10k/QCA988X/hw2.0/board.bin",
                               "ath10k/QCA988X/hw2.0/board.bin", required=False)
                ],
                "QCA6174": [
                    FirmwareFile("ath10k/QCA6174/hw3.0/firmware-6.bin",
                               "ath10k/QCA6174/hw3.0/firmware-6.bin", required=True),
                    FirmwareFile("ath10k/QCA6174/hw3.0/board.bin", 
                               "ath10k/QCA6174/hw3.0/board.bin", required=False)
                ]
            },
            "iwlwifi": {
                "AX200": [
                    FirmwareFile("iwlwifi-cc-a0-63.ucode",
                               "iwlwifi-cc-a0-63.ucode", required=True)
                ],
                "AX210": [
                    FirmwareFile("iwlwifi-ty-a0-gf-a0-63.ucode",
                               "iwlwifi-ty-a0-gf-a0-63.ucode", required=True)
                ]
            },
            "rt2x00": {
                "RT3070": [
                    FirmwareFile("rt2870.bin", "rt2870.bin", required=True)
                ]
            },
            "rtw88": {
                "RTL8822B": [
                    FirmwareFile("rtw88/rtw8822b_fw.bin", "rtw88/rtw8822b_fw.bin", required=True),
                    FirmwareFile("rtw88/rtw8822b_wow_fw.bin", "rtw88/rtw8822b_wow_fw.bin", required=False)
                ],
                "RTL8822C": [
                    FirmwareFile("rtw88/rtw8822c_fw.bin", "rtw88/rtw8822c_fw.bin", required=True),
                    FirmwareFile("rtw88/rtw8822c_wow_fw.bin", "rtw88/rtw8822c_wow_fw.bin", required=False)
                ],
                "RTL8821C": [
                    FirmwareFile("rtw88/rtw8821c_fw.bin", "rtw88/rtw8821c_fw.bin", required=True),
                    FirmwareFile("rtw88/rtw8821c_wow_fw.bin", "rtw88/rtw8821c_wow_fw.bin", required=False)
                ],
                "RTL8723D": [
                    FirmwareFile("rtw88/rtw8723d_fw.bin", "rtw88/rtw8723d_fw.bin", required=True),
                    FirmwareFile("rtw88/rtw8723d_wow_fw.bin", "rtw88/rtw8723d_wow_fw.bin", required=False)
                ]
            },
            "mt76": {
                "MT7601U": [
                    FirmwareFile("mt7601u.bin", "mt7601u.bin", required=True)
                ],
                "MT7610U": [
                    FirmwareFile("mediatek/mt7610u.bin", "mediatek/mt7610u.bin", required=True)
                ],
                "MT7612U": [
                    FirmwareFile("mediatek/mt7612u.bin", "mediatek/mt7612u.bin", required=True)
                ],
                "MT7663U": [
                    FirmwareFile("mediatek/mt7663_usb_sdio_n9_rebb.bin", "mediatek/mt7663_usb_sdio_n9_rebb.bin", required=True),
                    FirmwareFile("mediatek/mt7663_usb_sdio_cr4_rebb.bin", "mediatek/mt7663_usb_sdio_cr4_rebb.bin", required=True)
                ],
                "MT7921U": [
                    FirmwareFile("mediatek/WIFI_RAM_CODE_MT7961_1.bin", "mediatek/WIFI_RAM_CODE_MT7961_1.bin", required=True),
                    FirmwareFile("mediatek/WIFI_MT7961_patch_mcu_1_2_hdr.bin", "mediatek/WIFI_MT7961_patch_mcu_1_2_hdr.bin", required=True)
                ]
            },
            "rtw88": {
                "RTL8822B": [
                    FirmwareFile("rtw88/rtw8822b_fw.bin", "rtw88/rtw8822b_fw.bin", required=True)
                ],
                "RTL8822C": [
                    FirmwareFile("rtw88/rtw8822c_fw.bin", "rtw88/rtw8822c_fw.bin", required=True)
                ],
                "RTL8821C": [
                    FirmwareFile("rtw88/rtw8821c_fw.bin", "rtw88/rtw8821c_fw.bin", required=True)
                ],
                "RTL8723D": [
                    FirmwareFile("rtw88/rtw8723d_fw.bin", "rtw88/rtw8723d_fw.bin", required=True)
                ]
            },
            "mt76": {
                "MT7601U": [
                    FirmwareFile("mt7601u.bin", "mt7601u.bin", required=True)
                ],
                "MT7610U": [
                    FirmwareFile("mediatek/mt7610u.bin", "mediatek/mt7610u.bin", required=True)
                ],
                "MT7612U": [
                    FirmwareFile("mediatek/mt7612u.bin", "mediatek/mt7612u.bin", required=True)
                ],
                "MT7663U": [
                    FirmwareFile("mediatek/mt7663_usb_sdio_n9_rebb.bin", "mediatek/mt7663_usb_sdio_n9_rebb.bin", required=True),
                    FirmwareFile("mediatek/mt7663_usb_sdio_cr4_rebb.bin", "mediatek/mt7663_usb_sdio_cr4_rebb.bin", required=True)
                ],
                "MT7921U": [
                    FirmwareFile("mediatek/WIFI_RAM_CODE_MT7961_1.bin", "mediatek/WIFI_RAM_CODE_MT7961_1.bin", required=True),
                    FirmwareFile("mediatek/WIFI_MT7961_patch_mcu_1_2_hdr.bin", "mediatek/WIFI_MT7961_patch_mcu_1_2_hdr.bin", required=True)
                ]
            }
        }
    
    def download_firmware(self, driver: str, chipset: str, 
                         target_dir: Optional[str] = None) -> Dict[str, any]:
        """Download firmware for specific driver and chipset"""
        result = {
            "success": False,
            "driver": driver,
            "chipset": chipset,
            "downloaded_files": [],
            "failed_files": [],
            "total_size": 0,
            "total_time": 0,
            "errors": []
        }
        
        if driver not in self.firmware_db:
            result["errors"].append(f"Unknown driver: {driver}")
            return result
        
        if chipset not in self.firmware_db[driver]:
            result["errors"].append(f"Unknown chipset: {chipset}")
            return result
        
        firmware_files = self.firmware_db[driver][chipset]
        target_path = Path(target_dir) if target_dir else self.firmware_dir
        
        # Create temporary download directory
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        start_time = time.time()
        
        for firmware_file in firmware_files:
            download_result = self._download_single_file(firmware_file, target_path)
            
            if download_result.success:
                result["downloaded_files"].append(download_result.file_path)
                result["total_size"] += download_result.size
            else:
                result["failed_files"].append(firmware_file.name)
                if firmware_file.required:
                    result["errors"].append(f"Failed to download required file: {firmware_file.name}")
        
        result["total_time"] = time.time() - start_time
        
        # Check if all required files were downloaded
        required_files = [f for f in firmware_files if f.required]
        downloaded_required = [f for f in required_files 
                             if any(f.name in path for path in result["downloaded_files"])]
        
        result["success"] = len(downloaded_required) == len(required_files)
        
        return result
    
    def _download_single_file(self, firmware_file: FirmwareFile, 
                            target_dir: Path) -> DownloadResult:
        """Download a single firmware file"""
        start_time = time.time()
        
        # Try each base URL
        for base_url in self.config["base_urls"]:
            download_url = base_url + firmware_file.url
            
            for attempt in range(self.config["retry_attempts"]):
                try:
                    result = self._attempt_download(download_url, firmware_file, target_dir)
                    
                    if result.success:
                        result.download_time = time.time() - start_time
                        return result
                    
                    # Wait before retry
                    if attempt < self.config["retry_attempts"] - 1:
                        time.sleep(self.config["retry_delay"])
                
                except Exception as e:
                    if attempt == self.config["retry_attempts"] - 1:
                        return DownloadResult(
                            success=False,
                            file_path="",
                            size=0,
                            download_time=time.time() - start_time,
                            checksum_valid=False,
                            error=str(e)
                        )
        
        return DownloadResult(
            success=False,
            file_path="",
            size=0,
            download_time=time.time() - start_time,
            checksum_valid=False,
            error="All download attempts failed"
        )
    
    def _attempt_download(self, url: str, firmware_file: FirmwareFile, 
                         target_dir: Path) -> DownloadResult:
        """Attempt to download a file from URL"""
        temp_file = self.temp_dir / firmware_file.name
        temp_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create request with user agent
        request = urllib.request.Request(url)
        request.add_header('User-Agent', self.config["user_agent"])
        
        # Download to temporary file
        with urllib.request.urlopen(request, timeout=self.config["download_timeout"]) as response:
            with open(temp_file, 'wb') as f:
                shutil.copyfileobj(response, f)
        
        # Validate file
        file_size = temp_file.stat().st_size
        checksum_valid = True
        
        if self.config["validate_checksums"] and firmware_file.checksum_sha256:
            calculated_checksum = self._calculate_sha256(temp_file)
            checksum_valid = calculated_checksum == firmware_file.checksum_sha256
        
        if not checksum_valid:
            temp_file.unlink()
            return DownloadResult(
                success=False,
                file_path="",
                size=file_size,
                download_time=0,
                checksum_valid=False,
                error="Checksum validation failed"
            )
        
        # Move to target location
        target_file = target_dir / firmware_file.name
        target_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Backup existing file if configured
        if target_file.exists() and self.config["backup_existing"]:
            backup_file = target_file.with_suffix(target_file.suffix + ".backup")
            shutil.copy2(target_file, backup_file)
        
        shutil.move(temp_file, target_file)
        
        return DownloadResult(
            success=True,
            file_path=str(target_file),
            size=file_size,
            download_time=0,  # Will be set by caller
            checksum_valid=checksum_valid
        )
    
    def _calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def install_firmware(self, driver: str, chipset: str) -> Dict[str, any]:
        """Download and install firmware"""
        result = {
            "success": False,
            "driver": driver,
            "chipset": chipset,
            "actions": [],
            "warnings": [],
            "errors": []
        }
        
        # Download firmware
        download_result = self.download_firmware(driver, chipset)
        
        if not download_result["success"]:
            result["errors"].extend(download_result["errors"])
            return result
        
        result["actions"].extend([
            f"Downloaded {len(download_result['downloaded_files'])} firmware files",
            f"Total size: {download_result['total_size']} bytes",
            f"Download time: {download_result['total_time']:.2f} seconds"
        ])
        
        # Validate installation
        validation_result = self.validate_firmware(driver, chipset)
        
        if validation_result["valid"]:
            result["success"] = True
            result["actions"].append("Firmware installation validated")
        else:
            result["warnings"].extend(validation_result["warnings"])
            result["errors"].extend(validation_result["errors"])
        
        return result
    
    def validate_firmware(self, driver: str, chipset: str) -> Dict[str, any]:
        """Validate installed firmware"""
        result = {
            "valid": True,
            "driver": driver,
            "chipset": chipset,
            "found_files": [],
            "missing_files": [],
            "warnings": [],
            "errors": []
        }
        
        if driver not in self.firmware_db or chipset not in self.firmware_db[driver]:
            result["errors"].append("Unknown driver/chipset combination")
            result["valid"] = False
            return result
        
        firmware_files = self.firmware_db[driver][chipset]
        
        for firmware_file in firmware_files:
            firmware_path = self.firmware_dir / firmware_file.name
            
            if firmware_path.exists():
                result["found_files"].append(str(firmware_path))
                
                # Validate checksum if available
                if (self.config["validate_checksums"] and 
                    firmware_file.checksum_sha256):
                    
                    calculated = self._calculate_sha256(firmware_path)
                    if calculated != firmware_file.checksum_sha256:
                        result["warnings"].append(f"Checksum mismatch: {firmware_file.name}")
            else:
                result["missing_files"].append(firmware_file.name)
                
                if firmware_file.required:
                    result["errors"].append(f"Required firmware missing: {firmware_file.name}")
                    result["valid"] = False
        
        return result
    
    def cleanup_firmware(self, driver: str, chipset: str) -> Dict[str, any]:
        """Remove firmware files for driver/chipset"""
        result = {
            "success": False,
            "removed_files": [],
            "errors": []
        }
        
        if driver not in self.firmware_db or chipset not in self.firmware_db[driver]:
            result["errors"].append("Unknown driver/chipset combination")
            return result
        
        firmware_files = self.firmware_db[driver][chipset]
        
        for firmware_file in firmware_files:
            firmware_path = self.firmware_dir / firmware_file.name
            
            if firmware_path.exists():
                try:
                    firmware_path.unlink()
                    result["removed_files"].append(str(firmware_path))
                except Exception as e:
                    result["errors"].append(f"Could not remove {firmware_path}: {e}")
        
        result["success"] = len(result["errors"]) == 0
        return result
    
    def generate_firmware_report(self, output_file: Optional[str] = None) -> str:
        """Generate comprehensive firmware report"""
        report_lines = []
        report_lines.append("Firmware Automation Report")
        report_lines.append("=" * 40)
        report_lines.append(f"Generated: {time.ctime()}")
        report_lines.append("")
        
        # Configuration summary
        report_lines.append("Configuration:")
        report_lines.append(f"  Firmware directory: {self.firmware_dir}")
        report_lines.append(f"  Validation enabled: {self.config['validate_checksums']}")
        report_lines.append(f"  Backup enabled: {self.config['backup_existing']}")
        report_lines.append(f"  Retry attempts: {self.config['retry_attempts']}")
        report_lines.append("")
        
        # Firmware status for each driver/chipset
        report_lines.append("Firmware Status:")
        
        for driver, chipsets in self.firmware_db.items():
            report_lines.append(f"  {driver}:")
            
            for chipset, firmware_files in chipsets.items():
                validation = self.validate_firmware(driver, chipset)
                
                status_icon = "✅" if validation["valid"] else "❌"
                report_lines.append(f"    {status_icon} {chipset}")
                
                if validation["found_files"]:
                    report_lines.append(f"      Found: {len(validation['found_files'])} files")
                
                if validation["missing_files"]:
                    report_lines.append(f"      Missing: {len(validation['missing_files'])} files")
                    for missing in validation["missing_files"]:
                        report_lines.append(f"        - {missing}")
        
        report_lines.append("")
        
        # Download sources
        report_lines.append("Download Sources:")
        for i, url in enumerate(self.config["base_urls"], 1):
            report_lines.append(f"  {i}. {url}")
        
        report_content = "\n".join(report_lines)
        
        # Save to file if requested
        if output_file:
            try:
                with open(output_file, 'w') as f:
                    f.write(report_content)
                print(f"Firmware report saved to: {output_file}")
            except Exception as e:
                print(f"Error saving report: {e}")
        
        return report_content

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Firmware Download and Installation Automation")
    parser.add_argument("command", choices=[
        "download", "install", "validate", "cleanup", "report"
    ], help="Automation command")
    
    parser.add_argument("driver", nargs="?", help="Driver name")
    parser.add_argument("chipset", nargs="?", help="Chipset name")
    parser.add_argument("--target-dir", help="Target directory for firmware")
    parser.add_argument("--output", "-o", help="Output file for report")
    parser.add_argument("--no-validate", action="store_true", help="Skip checksum validation")
    parser.add_argument("--no-backup", action="store_true", help="Skip backup of existing files")
    
    args = parser.parse_args()
    
    # Initialize automation
    automation = FirmwareAutomation()
    
    # Update configuration based on arguments
    if args.no_validate:
        automation.config["validate_checksums"] = False
    if args.no_backup:
        automation.config["backup_existing"] = False
    
    # Execute command
    if args.command == "download":
        if not args.driver or not args.chipset:
            print("Error: Driver and chipset required for download command")
            return 1
        
        result = automation.download_firmware(args.driver, args.chipset, args.target_dir)
        
        if result["success"]:
            print(f"✅ Successfully downloaded firmware for {args.driver}/{args.chipset}")
            print(f"  Files: {len(result['downloaded_files'])}")
            print(f"  Size: {result['total_size']} bytes")
            print(f"  Time: {result['total_time']:.2f} seconds")
        else:
            print(f"❌ Failed to download firmware for {args.driver}/{args.chipset}")
            for error in result["errors"]:
                print(f"  Error: {error}")
    
    elif args.command == "install":
        if not args.driver or not args.chipset:
            print("Error: Driver and chipset required for install command")
            return 1
        
        result = automation.install_firmware(args.driver, args.chipset)
        
        if result["success"]:
            print(f"✅ Successfully installed firmware for {args.driver}/{args.chipset}")
            for action in result["actions"]:
                print(f"  - {action}")
        else:
            print(f"❌ Failed to install firmware for {args.driver}/{args.chipset}")
            for error in result["errors"]:
                print(f"  Error: {error}")
        
        for warning in result["warnings"]:
            print(f"  Warning: {warning}")
    
    elif args.command == "validate":
        if not args.driver or not args.chipset:
            print("Error: Driver and chipset required for validate command")
            return 1
        
        result = automation.validate_firmware(args.driver, args.chipset)
        
        if result["valid"]:
            print(f"✅ Firmware validation passed for {args.driver}/{args.chipset}")
            print(f"  Found files: {len(result['found_files'])}")
        else:
            print(f"❌ Firmware validation failed for {args.driver}/{args.chipset}")
            for error in result["errors"]:
                print(f"  Error: {error}")
        
        for warning in result["warnings"]:
            print(f"  Warning: {warning}")
    
    elif args.command == "cleanup":
        if not args.driver or not args.chipset:
            print("Error: Driver and chipset required for cleanup command")
            return 1
        
        result = automation.cleanup_firmware(args.driver, args.chipset)
        
        if result["success"]:
            print(f"✅ Successfully cleaned up firmware for {args.driver}/{args.chipset}")
            print(f"  Removed files: {len(result['removed_files'])}")
        else:
            print(f"❌ Failed to cleanup firmware for {args.driver}/{args.chipset}")
            for error in result["errors"]:
                print(f"  Error: {error}")
    
    elif args.command == "report":
        report = automation.generate_firmware_report(args.output)
        if not args.output:
            print(report)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())