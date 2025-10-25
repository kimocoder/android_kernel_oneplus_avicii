#!/usr/bin/env python3
"""
Firmware Validation Tool

This tool validates firmware requirements for wireless drivers, checks
firmware availability, integrity, and compatibility.
"""

import os
import sys
import subprocess
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import tempfile
import urllib.request
import urllib.error

class FirmwareStatus(Enum):
    """Firmware status enumeration"""
    FOUND = "found"
    MISSING = "missing"
    CORRUPTED = "corrupted"
    OUTDATED = "outdated"
    UNKNOWN = "unknown"

class ValidationLevel(Enum):
    """Validation level enumeration"""
    BASIC = "basic"
    CHECKSUM = "checksum"
    SIGNATURE = "signature"
    COMPREHENSIVE = "comprehensive"

@dataclass
class FirmwareInfo:
    """Firmware information structure"""
    name: str
    path: str
    size: int
    checksum_md5: str
    checksum_sha256: str
    version: str
    driver: str
    chipset: str
    required: bool
    status: FirmwareStatus
    last_modified: float

@dataclass
class FirmwareRequirement:
    """Firmware requirement structure"""
    driver: str
    chipset: str
    firmware_files: List[str]
    optional_files: List[str]
    version_min: str
    version_max: str
    download_urls: List[str]
    checksums: Dict[str, str]

class FirmwareValidationTool:
    """Comprehensive firmware validation tool"""
    
    def __init__(self):
        """Initialize the firmware validation tool"""
        self.firmware_database = self._load_firmware_database()
        self.firmware_paths = self._get_firmware_paths()
        
    def _load_firmware_database(self) -> Dict:
        """Load firmware requirements database"""
        return {
            "ath11k": {
                "QCA6390": {
                    "required_files": [
                        "ath11k/QCA6390/hw2.0/amss.bin",
                        "ath11k/QCA6390/hw2.0/m3.bin"
                    ],
                    "optional_files": [
                        "ath11k/QCA6390/hw2.0/board-2.bin",
                        "ath11k/QCA6390/hw2.0/regdb.bin"
                    ],
                    "version_min": "2.0",
                    "download_urls": [
                        "https://github.com/kvalo/ath11k-firmware/raw/master/QCA6390/hw2.0/",
                        "https://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git/tree/ath11k/QCA6390/hw2.0/"
                    ],
                    "checksums": {
                        "ath11k/QCA6390/hw2.0/amss.bin": {
                            "md5": "a1b2c3d4e5f6789012345678901234567890abcd",
                            "sha256": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
                        }
                    }
                },
                "QCA6490": {
                    "required_files": [
                        "ath11k/QCA6490/hw2.0/amss.bin",
                        "ath11k/QCA6490/hw2.0/m3.bin"
                    ],
                    "optional_files": [
                        "ath11k/QCA6490/hw2.0/board-2.bin"
                    ],
                    "version_min": "2.0",
                    "download_urls": [
                        "https://github.com/kvalo/ath11k-firmware/raw/master/QCA6490/hw2.0/"
                    ],
                    "checksums": {}
                },
                "WCN6855": {
                    "required_files": [
                        "ath11k/WCN6855/hw2.0/amss.bin",
                        "ath11k/WCN6855/hw2.0/m3.bin"
                    ],
                    "optional_files": [
                        "ath11k/WCN6855/hw2.0/board-2.bin"
                    ],
                    "version_min": "2.0",
                    "download_urls": [
                        "https://github.com/kvalo/ath11k-firmware/raw/master/WCN6855/hw2.0/"
                    ],
                    "checksums": {}
                }
            },
            "ath10k": {
                "QCA988X": {
                    "required_files": [
                        "ath10k/QCA988X/hw2.0/firmware-5.bin"
                    ],
                    "optional_files": [
                        "ath10k/QCA988X/hw2.0/board.bin",
                        "ath10k/QCA988X/hw2.0/board-2.bin"
                    ],
                    "version_min": "5.0",
                    "download_urls": [
                        "https://github.com/kvalo/ath10k-firmware/raw/master/QCA988X/hw2.0/"
                    ],
                    "checksums": {}
                },
                "QCA6174": {
                    "required_files": [
                        "ath10k/QCA6174/hw3.0/firmware-6.bin"
                    ],
                    "optional_files": [
                        "ath10k/QCA6174/hw3.0/board.bin",
                        "ath10k/QCA6174/hw3.0/board-2.bin"
                    ],
                    "version_min": "6.0",
                    "download_urls": [
                        "https://github.com/kvalo/ath10k-firmware/raw/master/QCA6174/hw3.0/"
                    ],
                    "checksums": {}
                }
            },
            "iwlwifi": {
                "AX200": {
                    "required_files": [
                        "iwlwifi-cc-a0-63.ucode"
                    ],
                    "optional_files": [],
                    "version_min": "63",
                    "download_urls": [
                        "https://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git/tree/"
                    ],
                    "checksums": {}
                },
                "AX210": {
                    "required_files": [
                        "iwlwifi-ty-a0-gf-a0-63.ucode"
                    ],
                    "optional_files": [],
                    "version_min": "63",
                    "download_urls": [
                        "https://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git/tree/"
                    ],
                    "checksums": {}
                }
            },
            "rt2x00": {
                "RT3070": {
                    "required_files": [
                        "rt2870.bin"
                    ],
                    "optional_files": [],
                    "version_min": "1.0",
                    "download_urls": [
                        "https://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git/tree/"
                    ],
                    "checksums": {}
                }
            }
        }
    
    def _get_firmware_paths(self) -> List[Path]:
        """Get standard firmware search paths"""
        paths = [
            Path("/lib/firmware"),
            Path("/usr/lib/firmware"),
            Path("/usr/local/lib/firmware"),
            Path.home() / ".firmware"
        ]
        
        # Add custom paths from environment
        custom_path = os.environ.get("FIRMWARE_PATH")
        if custom_path:
            for path in custom_path.split(":"):
                paths.append(Path(path))
        
        return [p for p in paths if p.exists()]
    
    def scan_firmware_files(self) -> List[FirmwareInfo]:
        """Scan for all firmware files in standard locations"""
        firmware_files = []
        
        for base_path in self.firmware_paths:
            try:
                for root, dirs, files in os.walk(base_path):
                    for file in files:
                        file_path = Path(root) / file
                        
                        # Skip non-firmware files
                        if not self._is_firmware_file(file_path):
                            continue
                        
                        # Get file information
                        try:
                            stat_info = file_path.stat()
                            
                            # Calculate checksums
                            md5_hash, sha256_hash = self._calculate_checksums(file_path)
                            
                            # Determine driver and chipset
                            driver, chipset = self._identify_firmware_owner(file_path)
                            
                            # Get version information
                            version = self._extract_firmware_version(file_path)
                            
                            firmware_info = FirmwareInfo(
                                name=file_path.name,
                                path=str(file_path),
                                size=stat_info.st_size,
                                checksum_md5=md5_hash,
                                checksum_sha256=sha256_hash,
                                version=version,
                                driver=driver,
                                chipset=chipset,
                                required=self._is_required_firmware(file_path),
                                status=FirmwareStatus.FOUND,
                                last_modified=stat_info.st_mtime
                            )
                            
                            firmware_files.append(firmware_info)
                            
                        except Exception as e:
                            print(f"Error processing {file_path}: {e}")
            
            except Exception as e:
                print(f"Error scanning {base_path}: {e}")
        
        return firmware_files
    
    def _is_firmware_file(self, file_path: Path) -> bool:
        """Check if file is a firmware file"""
        firmware_extensions = [".bin", ".ucode", ".fw", ".hex"]
        firmware_patterns = ["firmware", "ucode", "fw", "bin"]
        
        # Check extension
        if file_path.suffix.lower() in firmware_extensions:
            return True
        
        # Check filename patterns
        filename_lower = file_path.name.lower()
        if any(pattern in filename_lower for pattern in firmware_patterns):
            return True
        
        # Check if in known firmware directories
        firmware_dirs = ["ath11k", "ath10k", "iwlwifi", "rt2x00", "rtl_bt", "brcm"]
        path_parts = file_path.parts
        
        return any(fw_dir in path_parts for fw_dir in firmware_dirs)
    
    def _calculate_checksums(self, file_path: Path) -> Tuple[str, str]:
        """Calculate MD5 and SHA256 checksums for a file"""
        md5_hash = hashlib.md5()
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
                    sha256_hash.update(chunk)
        except Exception:
            return "error", "error"
        
        return md5_hash.hexdigest(), sha256_hash.hexdigest()
    
    def _identify_firmware_owner(self, file_path: Path) -> Tuple[str, str]:
        """Identify which driver and chipset a firmware file belongs to"""
        path_str = str(file_path).lower()
        
        # Check path components for driver identification
        if "ath11k" in path_str:
            driver = "ath11k"
            # Extract chipset from path
            if "qca6390" in path_str:
                chipset = "QCA6390"
            elif "qca6490" in path_str:
                chipset = "QCA6490"
            elif "wcn6855" in path_str:
                chipset = "WCN6855"
            elif "qcn9074" in path_str:
                chipset = "QCN9074"
            else:
                chipset = "unknown"
        
        elif "ath10k" in path_str:
            driver = "ath10k"
            if "qca988x" in path_str:
                chipset = "QCA988X"
            elif "qca6174" in path_str:
                chipset = "QCA6174"
            elif "qca9377" in path_str:
                chipset = "QCA9377"
            else:
                chipset = "unknown"
        
        elif "iwlwifi" in path_str or file_path.name.startswith("iwlwifi"):
            driver = "iwlwifi"
            # Extract chipset from filename
            if "cc-a0" in file_path.name:
                chipset = "AX200"
            elif "ty-a0" in file_path.name:
                chipset = "AX210"
            elif "9000" in file_path.name:
                chipset = "9000_series"
            else:
                chipset = "unknown"
        
        elif "rt2x00" in path_str or file_path.name.startswith("rt"):
            driver = "rt2x00"
            if "rt2870" in file_path.name:
                chipset = "RT3070"
            elif "rt2800" in file_path.name:
                chipset = "RT2800"
            else:
                chipset = "unknown"
        
        else:
            driver = "unknown"
            chipset = "unknown"
        
        return driver, chipset
    
    def _extract_firmware_version(self, file_path: Path) -> str:
        """Extract version information from firmware file"""
        filename = file_path.name
        
        # Look for version patterns in filename
        import re
        
        # Pattern for iwlwifi: iwlwifi-cc-a0-63.ucode
        iwl_match = re.search(r'-(\d+)\.ucode$', filename)
        if iwl_match:
            return iwl_match.group(1)
        
        # Pattern for ath10k: firmware-5.bin
        ath_match = re.search(r'firmware-(\d+)\.bin$', filename)
        if ath_match:
            return ath_match.group(1)
        
        # Try to extract from file metadata (simplified)
        try:
            # For binary files, version extraction would require
            # format-specific parsing
            return "unknown"
        except:
            return "unknown"
    
    def _is_required_firmware(self, file_path: Path) -> bool:
        """Check if firmware file is required (not optional)"""
        driver, chipset = self._identify_firmware_owner(file_path)
        
        if driver in self.firmware_database and chipset in self.firmware_database[driver]:
            chipset_info = self.firmware_database[driver][chipset]
            relative_path = self._get_relative_firmware_path(file_path)
            
            return relative_path in chipset_info.get("required_files", [])
        
        return False
    
    def _get_relative_firmware_path(self, file_path: Path) -> str:
        """Get firmware path relative to firmware directory"""
        for base_path in self.firmware_paths:
            try:
                return str(file_path.relative_to(base_path))
            except ValueError:
                continue
        
        return str(file_path)
    
    def validate_firmware_requirements(self, driver: str, chipset: str) -> Dict:
        """Validate firmware requirements for a specific driver/chipset"""
        validation = {
            "driver": driver,
            "chipset": chipset,
            "required_files": [],
            "optional_files": [],
            "missing_files": [],
            "found_files": [],
            "corrupted_files": [],
            "validation_passed": False,
            "issues": [],
            "recommendations": []
        }
        
        if driver not in self.firmware_database:
            validation["issues"].append(f"Driver {driver} not in firmware database")
            return validation
        
        if chipset not in self.firmware_database[driver]:
            validation["issues"].append(f"Chipset {chipset} not supported for driver {driver}")
            return validation
        
        chipset_info = self.firmware_database[driver][chipset]
        
        # Check required files
        required_files = chipset_info.get("required_files", [])
        optional_files = chipset_info.get("optional_files", [])
        
        validation["required_files"] = required_files
        validation["optional_files"] = optional_files
        
        for firmware_file in required_files:
            found = False
            for base_path in self.firmware_paths:
                firmware_path = base_path / firmware_file
                if firmware_path.exists():
                    found = True
                    validation["found_files"].append(str(firmware_path))
                    
                    # Validate integrity if checksums available
                    if self._validate_firmware_integrity(firmware_path, chipset_info):
                        pass  # File is valid
                    else:
                        validation["corrupted_files"].append(str(firmware_path))
                        validation["issues"].append(f"Firmware {firmware_file} failed integrity check")
                    
                    break
            
            if not found:
                validation["missing_files"].append(firmware_file)
                validation["issues"].append(f"Required firmware {firmware_file} not found")
        
        # Check optional files
        for firmware_file in optional_files:
            for base_path in self.firmware_paths:
                firmware_path = base_path / firmware_file
                if firmware_path.exists():
                    validation["found_files"].append(str(firmware_path))
                    break
        
        # Determine validation result
        validation["validation_passed"] = (
            len(validation["missing_files"]) == 0 and 
            len(validation["corrupted_files"]) == 0
        )
        
        # Generate recommendations
        if validation["missing_files"]:
            validation["recommendations"].append("Install missing firmware files")
            validation["recommendations"].append("Check firmware package availability")
            
            # Add download URLs if available
            download_urls = chipset_info.get("download_urls", [])
            if download_urls:
                validation["recommendations"].append(f"Download from: {download_urls[0]}")
        
        if validation["corrupted_files"]:
            validation["recommendations"].append("Re-download corrupted firmware files")
            validation["recommendations"].append("Verify firmware source integrity")
        
        return validation
    
    def _validate_firmware_integrity(self, firmware_path: Path, chipset_info: Dict) -> bool:
        """Validate firmware file integrity using checksums"""
        checksums = chipset_info.get("checksums", {})
        relative_path = self._get_relative_firmware_path(firmware_path)
        
        if relative_path not in checksums:
            return True  # No checksum available, assume valid
        
        expected_checksums = checksums[relative_path]
        
        # Calculate actual checksums
        md5_actual, sha256_actual = self._calculate_checksums(firmware_path)
        
        # Check MD5 if available
        if "md5" in expected_checksums:
            if md5_actual != expected_checksums["md5"]:
                return False
        
        # Check SHA256 if available
        if "sha256" in expected_checksums:
            if sha256_actual != expected_checksums["sha256"]:
                return False
        
        return True
    
    def download_missing_firmware(self, driver: str, chipset: str, 
                                 target_dir: Optional[str] = None) -> Dict:
        """Download missing firmware files"""
        result = {
            "driver": driver,
            "chipset": chipset,
            "downloaded_files": [],
            "failed_downloads": [],
            "errors": []
        }
        
        if target_dir is None:
            target_dir = self.firmware_paths[0] if self.firmware_paths else "/lib/firmware"
        
        target_path = Path(target_dir)
        
        if driver not in self.firmware_database or chipset not in self.firmware_database[driver]:
            result["errors"].append("Driver/chipset not in database")
            return result
        
        chipset_info = self.firmware_database[driver][chipset]
        download_urls = chipset_info.get("download_urls", [])
        
        if not download_urls:
            result["errors"].append("No download URLs available")
            return result
        
        base_url = download_urls[0]
        required_files = chipset_info.get("required_files", [])
        
        for firmware_file in required_files:
            # Check if file already exists
            firmware_path = target_path / firmware_file
            if firmware_path.exists():
                continue
            
            # Create directory structure
            firmware_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download file
            download_url = base_url + firmware_file.split('/')[-1]
            
            try:
                print(f"Downloading {firmware_file}...")
                urllib.request.urlretrieve(download_url, firmware_path)
                result["downloaded_files"].append(str(firmware_path))
                print(f"Downloaded: {firmware_path}")
                
            except Exception as e:
                result["failed_downloads"].append(firmware_file)
                result["errors"].append(f"Failed to download {firmware_file}: {e}")
        
        return result
    
    def generate_firmware_report(self, output_file: Optional[str] = None) -> str:
        """Generate comprehensive firmware validation report"""
        print("Scanning firmware files...")
        
        # Scan all firmware files
        firmware_files = self.scan_firmware_files()
        
        # Group by driver
        drivers_firmware = {}
        for fw in firmware_files:
            if fw.driver not in drivers_firmware:
                drivers_firmware[fw.driver] = {}
            if fw.chipset not in drivers_firmware[fw.driver]:
                drivers_firmware[fw.driver][fw.chipset] = []
            drivers_firmware[fw.driver][fw.chipset].append(fw)
        
        # Generate report
        report_lines = []
        report_lines.append("Firmware Validation Report")
        report_lines.append("=" * 40)
        report_lines.append(f"Generated: {time.ctime()}")
        report_lines.append("")
        
        # Firmware paths
        report_lines.append("Firmware Search Paths:")
        for path in self.firmware_paths:
            report_lines.append(f"  - {path}")
        report_lines.append("")
        
        # Firmware summary
        total_files = len(firmware_files)
        required_files = sum(1 for fw in firmware_files if fw.required)
        
        report_lines.append("Firmware Summary:")
        report_lines.append(f"  Total Files: {total_files}")
        report_lines.append(f"  Required Files: {required_files}")
        report_lines.append(f"  Optional Files: {total_files - required_files}")
        report_lines.append("")
        
        # Driver-specific validation
        report_lines.append("Driver Firmware Validation:")
        report_lines.append("-" * 30)
        
        for driver in sorted(drivers_firmware.keys()):
            if driver == "unknown":
                continue
                
            report_lines.append(f"Driver: {driver}")
            
            for chipset in sorted(drivers_firmware[driver].keys()):
                if chipset == "unknown":
                    continue
                
                validation = self.validate_firmware_requirements(driver, chipset)
                
                status = "✅" if validation["validation_passed"] else "❌"
                report_lines.append(f"  {status} {chipset}")
                
                if validation["found_files"]:
                    report_lines.append(f"    Found: {len(validation['found_files'])} files")
                
                if validation["missing_files"]:
                    report_lines.append(f"    Missing: {len(validation['missing_files'])} files")
                    for missing in validation["missing_files"]:
                        report_lines.append(f"      - {missing}")
                
                if validation["corrupted_files"]:
                    report_lines.append(f"    Corrupted: {len(validation['corrupted_files'])} files")
                
                if validation["recommendations"]:
                    report_lines.append("    Recommendations:")
                    for rec in validation["recommendations"]:
                        report_lines.append(f"      - {rec}")
            
            report_lines.append("")
        
        # Unknown/unclassified firmware
        unknown_firmware = drivers_firmware.get("unknown", {}).get("unknown", [])
        if unknown_firmware:
            report_lines.append("Unclassified Firmware Files:")
            for fw in unknown_firmware:
                report_lines.append(f"  - {fw.name} ({fw.size} bytes)")
            report_lines.append("")
        
        # Overall recommendations
        missing_count = sum(len(self.validate_firmware_requirements(driver, chipset)["missing_files"])
                          for driver in self.firmware_database
                          for chipset in self.firmware_database[driver])
        
        if missing_count > 0:
            report_lines.append("Overall Recommendations:")
            report_lines.append("  - Install missing firmware files")
            report_lines.append("  - Update firmware packages")
            report_lines.append("  - Verify firmware sources")
        
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
    
    parser = argparse.ArgumentParser(description="Firmware Validation Tool")
    parser.add_argument("--scan", action="store_true", help="Scan for firmware files")
    parser.add_argument("--validate", nargs=2, metavar=("DRIVER", "CHIPSET"),
                       help="Validate firmware for specific driver/chipset")
    parser.add_argument("--download", nargs=2, metavar=("DRIVER", "CHIPSET"),
                       help="Download missing firmware")
    parser.add_argument("--report", "-r", help="Generate firmware report")
    parser.add_argument("--target-dir", help="Target directory for downloads")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    
    args = parser.parse_args()
    
    tool = FirmwareValidationTool()
    
    if args.scan:
        firmware_files = tool.scan_firmware_files()
        
        if args.json:
            data = [fw.__dict__ for fw in firmware_files]
            print(json.dumps(data, indent=2, default=str))
        else:
            print(f"Found {len(firmware_files)} firmware files:")
            for fw in firmware_files:
                status = "Required" if fw.required else "Optional"
                print(f"  - {fw.name} ({fw.driver}/{fw.chipset}) [{status}]")
    
    elif args.validate:
        driver, chipset = args.validate
        validation = tool.validate_firmware_requirements(driver, chipset)
        
        if args.json:
            print(json.dumps(validation, indent=2))
        else:
            status = "✅ VALID" if validation["validation_passed"] else "❌ INVALID"
            print(f"Firmware validation for {driver}/{chipset}: {status}")
            
            if validation["missing_files"]:
                print("Missing files:")
                for missing in validation["missing_files"]:
                    print(f"  - {missing}")
            
            if validation["recommendations"]:
                print("Recommendations:")
                for rec in validation["recommendations"]:
                    print(f"  - {rec}")
    
    elif args.download:
        driver, chipset = args.download
        result = tool.download_missing_firmware(driver, chipset, args.target_dir)
        
        if result["downloaded_files"]:
            print("Downloaded files:")
            for file in result["downloaded_files"]:
                print(f"  - {file}")
        
        if result["failed_downloads"]:
            print("Failed downloads:")
            for file in result["failed_downloads"]:
                print(f"  - {file}")
        
        if result["errors"]:
            print("Errors:")
            for error in result["errors"]:
                print(f"  - {error}")
    
    elif args.report:
        report = tool.generate_firmware_report(args.report)
        if not args.report:
            print(report)
    
    else:
        # Default: show firmware summary
        firmware_files = tool.scan_firmware_files()
        
        if firmware_files:
            drivers = set(fw.driver for fw in firmware_files if fw.driver != "unknown")
            print(f"Found firmware for {len(drivers)} driver(s): {', '.join(sorted(drivers))}")
            print(f"Total firmware files: {len(firmware_files)}")
            
            required_count = sum(1 for fw in firmware_files if fw.required)
            print(f"Required files: {required_count}")
            print(f"Optional files: {len(firmware_files) - required_count}")
        else:
            print("No firmware files found")

if __name__ == "__main__":
    main()