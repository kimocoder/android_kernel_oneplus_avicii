#!/usr/bin/env python3
"""
Wireless Regulatory Manager

This script provides comprehensive regulatory database management,
compliance checking, and regulatory domain configuration for wireless drivers.
"""

import os
import sys
import subprocess
import json
import urllib.request
import urllib.error
import hashlib
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import time

@dataclass
class ChannelInfo:
    """Wireless channel information"""
    channel: int
    frequency: int
    max_power: int
    flags: List[str]
    band: str

@dataclass
class RegulatoryDomain:
    """Regulatory domain information"""
    code: str
    name: str
    dfs_region: str
    channels: List[ChannelInfo]
    restrictions: List[str]

class WirelessRegulatoryManager:
    """Comprehensive wireless regulatory management"""
    
    def __init__(self):
        """Initialize regulatory manager"""
        self.regulatory_db_path = Path("/lib/firmware/regulatory.db")
        self.regulatory_sig_path = Path("/lib/firmware/regulatory.db.p7s")
        self.temp_dir = Path(tempfile.gettempdir()) / "regulatory-manager"
        
        # Regulatory database URLs
        self.db_urls = [
            "https://git.kernel.org/pub/scm/linux/kernel/git/sforshee/wireless-regdb.git/plain/regulatory.db",
            "https://wireless.wiki.kernel.org/attachments/en/developers/regulatory/regulatory.db"
        ]
        
        self.sig_urls = [
            "https://git.kernel.org/pub/scm/linux/kernel/git/sforshee/wireless-regdb.git/plain/regulatory.db.p7s",
            "https://wireless.wiki.kernel.org/attachments/en/developers/regulatory/regulatory.db.p7s"
        ]
        
        # Load regulatory domain definitions
        self.regulatory_domains = self._load_regulatory_domains()
    
    def _load_regulatory_domains(self) -> Dict[str, RegulatoryDomain]:
        """Load regulatory domain definitions"""
        domains = {}
        
        # United States (FCC)
        us_channels = []
        # 2.4 GHz channels
        for ch in range(1, 12):  # Channels 1-11
            freq = 2412 + (ch - 1) * 5
            us_channels.append(ChannelInfo(ch, freq, 30, [], "2.4GHz"))
        
        # 5 GHz channels
        us_5ghz = [
            (36, 5180, 23, []), (40, 5200, 23, []), (44, 5220, 23, []), (48, 5240, 23, []),
            (52, 5260, 23, ["DFS"]), (56, 5280, 23, ["DFS"]), (60, 5300, 23, ["DFS"]), (64, 5320, 23, ["DFS"]),
            (100, 5500, 23, ["DFS"]), (104, 5520, 23, ["DFS"]), (108, 5540, 23, ["DFS"]), (112, 5560, 23, ["DFS"]),
            (116, 5580, 23, ["DFS"]), (120, 5600, 23, ["DFS"]), (124, 5620, 23, ["DFS"]), (128, 5640, 23, ["DFS"]),
            (132, 5660, 23, ["DFS"]), (136, 5680, 23, ["DFS"]), (140, 5700, 23, ["DFS"]),
            (149, 5745, 30, []), (153, 5765, 30, []), (157, 5785, 30, []), (161, 5805, 30, []), (165, 5825, 30, [])
        ]
        
        for ch, freq, power, flags in us_5ghz:
            us_channels.append(ChannelInfo(ch, freq, power, flags, "5GHz"))
        
        domains["US"] = RegulatoryDomain(
            code="US",
            name="United States (FCC)",
            dfs_region="FCC",
            channels=us_channels,
            restrictions=[
                "Monitor mode requires proper authorization for commercial use",
                "Packet injection must comply with Part 15 regulations",
                "DFS channels require radar detection"
            ]
        )
        
        # European Union (ETSI)
        eu_channels = []
        # 2.4 GHz channels (1-13)
        for ch in range(1, 14):
            freq = 2412 + (ch - 1) * 5
            eu_channels.append(ChannelInfo(ch, freq, 20, [], "2.4GHz"))
        
        # 5 GHz channels (more restrictive)
        eu_5ghz = [
            (36, 5180, 23, []), (40, 5200, 23, []), (44, 5220, 23, []), (48, 5240, 23, []),
            (52, 5260, 23, ["DFS"]), (56, 5280, 23, ["DFS"]), (60, 5300, 23, ["DFS"]), (64, 5320, 23, ["DFS"]),
            (100, 5500, 23, ["DFS"]), (104, 5520, 23, ["DFS"]), (108, 5540, 23, ["DFS"]), (112, 5560, 23, ["DFS"]),
            (116, 5580, 23, ["DFS"]), (120, 5600, 23, ["DFS"]), (124, 5620, 23, ["DFS"]), (128, 5640, 23, ["DFS"]),
            (132, 5660, 23, ["DFS"]), (136, 5680, 23, ["DFS"]), (140, 5700, 23, ["DFS"])
        ]
        
        for ch, freq, power, flags in eu_5ghz:
            eu_channels.append(ChannelInfo(ch, freq, power, flags, "5GHz"))
        
        domains["EU"] = RegulatoryDomain(
            code="EU",
            name="European Union (ETSI)",
            dfs_region="ETSI",
            channels=eu_channels,
            restrictions=[
                "Packet injection is generally prohibited",
                "Monitor mode may require authorization in some countries",
                "DFS channels require radar detection",
                "Power limits are strictly enforced"
            ]
        )
        
        # Japan (MKK)
        jp_channels = []
        # 2.4 GHz channels (1-14, including channel 14)
        for ch in range(1, 15):
            freq = 2412 + (ch - 1) * 5 if ch < 14 else 2484
            jp_channels.append(ChannelInfo(ch, freq, 20, [], "2.4GHz"))
        
        # 5 GHz channels (limited)
        jp_5ghz = [
            (36, 5180, 23, []), (40, 5200, 23, []), (44, 5220, 23, []), (48, 5240, 23, []),
            (52, 5260, 23, ["DFS"]), (56, 5280, 23, ["DFS"]), (60, 5300, 23, ["DFS"]), (64, 5320, 23, ["DFS"]),
            (100, 5500, 23, ["DFS"]), (104, 5520, 23, ["DFS"]), (108, 5540, 23, ["DFS"]), (112, 5560, 23, ["DFS"]),
            (116, 5580, 23, ["DFS"]), (120, 5600, 23, ["DFS"]), (124, 5620, 23, ["DFS"]), (128, 5640, 23, ["DFS"]),
            (132, 5660, 23, ["DFS"]), (136, 5680, 23, ["DFS"]), (140, 5700, 23, ["DFS"])
        ]
        
        for ch, freq, power, flags in jp_5ghz:
            jp_channels.append(ChannelInfo(ch, freq, power, flags, "5GHz"))
        
        domains["JP"] = RegulatoryDomain(
            code="JP",
            name="Japan (MKK)",
            dfs_region="JP",
            channels=jp_channels,
            restrictions=[
                "Monitor mode requires special authorization",
                "Packet injection is prohibited",
                "Strict power limits enforced",
                "Channel 14 (2.4 GHz) available"
            ]
        )
        
        # China
        cn_channels = []
        # 2.4 GHz channels (1-13)
        for ch in range(1, 14):
            freq = 2412 + (ch - 1) * 5
            cn_channels.append(ChannelInfo(ch, freq, 20, [], "2.4GHz"))
        
        # 5 GHz ISM band only
        cn_5ghz = [
            (149, 5745, 30, []), (153, 5765, 30, []), (157, 5785, 30, []), 
            (161, 5805, 30, []), (165, 5825, 30, [])
        ]
        
        for ch, freq, power, flags in cn_5ghz:
            cn_channels.append(ChannelInfo(ch, freq, power, flags, "5GHz"))
        
        domains["CN"] = RegulatoryDomain(
            code="CN",
            name="China",
            dfs_region="FCC",
            channels=cn_channels,
            restrictions=[
                "Monitor mode is prohibited",
                "Packet injection is prohibited",
                "Limited frequency bands available",
                "Strict government regulations"
            ]
        )
        
        return domains
    
    def check_regulatory_database(self) -> Dict[str, any]:
        """Check regulatory database status"""
        result = {
            "db_exists": self.regulatory_db_path.exists(),
            "sig_exists": self.regulatory_sig_path.exists(),
            "db_size": 0,
            "sig_size": 0,
            "db_modified": None,
            "sig_modified": None
        }
        
        if result["db_exists"]:
            stat = self.regulatory_db_path.stat()
            result["db_size"] = stat.st_size
            result["db_modified"] = time.ctime(stat.st_mtime)
        
        if result["sig_exists"]:
            stat = self.regulatory_sig_path.stat()
            result["sig_size"] = stat.st_size
            result["sig_modified"] = time.ctime(stat.st_mtime)
        
        return result
    
    def download_regulatory_database(self, force: bool = False) -> bool:
        """Download regulatory database and signature"""
        # Check if already exists and not forcing
        if not force:
            status = self.check_regulatory_database()
            if status["db_exists"] and status["sig_exists"]:
                print("Regulatory database already exists (use --force to update)")
                return True
        
        # Create temporary directory
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Download regulatory.db
            db_success = False
            for url in self.db_urls:
                try:
                    print(f"Downloading regulatory.db from {url}")
                    temp_db = self.temp_dir / "regulatory.db"
                    
                    urllib.request.urlretrieve(url, temp_db)
                    
                    # Verify file is not empty
                    if temp_db.stat().st_size > 0:
                        db_success = True
                        break
                    else:
                        print(f"Downloaded file is empty, trying next URL")
                
                except Exception as e:
                    print(f"Failed to download from {url}: {e}")
            
            if not db_success:
                print("Failed to download regulatory.db from all sources")
                return False
            
            # Download regulatory.db.p7s
            sig_success = False
            for url in self.sig_urls:
                try:
                    print(f"Downloading regulatory.db.p7s from {url}")
                    temp_sig = self.temp_dir / "regulatory.db.p7s"
                    
                    urllib.request.urlretrieve(url, temp_sig)
                    
                    # Verify file is not empty
                    if temp_sig.stat().st_size > 0:
                        sig_success = True
                        break
                    else:
                        print(f"Downloaded signature file is empty, trying next URL")
                
                except Exception as e:
                    print(f"Failed to download signature from {url}: {e}")
            
            if not sig_success:
                print("Failed to download regulatory.db.p7s from all sources")
                return False
            
            # Install files
            print("Installing regulatory database...")
            
            # Backup existing files
            if self.regulatory_db_path.exists():
                backup_db = self.regulatory_db_path.with_suffix(".db.backup")
                shutil.copy2(self.regulatory_db_path, backup_db)
                print(f"Backed up existing database to {backup_db}")
            
            if self.regulatory_sig_path.exists():
                backup_sig = self.regulatory_sig_path.with_suffix(".p7s.backup")
                shutil.copy2(self.regulatory_sig_path, backup_sig)
                print(f"Backed up existing signature to {backup_sig}")
            
            # Install new files
            shutil.move(temp_db, self.regulatory_db_path)
            shutil.move(temp_sig, self.regulatory_sig_path)
            
            print("✅ Regulatory database installed successfully")
            return True
        
        except Exception as e:
            print(f"Error downloading regulatory database: {e}")
            return False
        
        finally:
            # Cleanup temporary directory
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def get_current_regulatory_domain(self) -> Optional[str]:
        """Get current regulatory domain"""
        try:
            result = subprocess.run(["iw", "reg", "get"], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith("country"):
                        return line.split()[1].rstrip(':')
            
        except FileNotFoundError:
            print("iw command not available")
        except Exception as e:
            print(f"Error getting regulatory domain: {e}")
        
        return None
    
    def set_regulatory_domain(self, domain: str) -> bool:
        """Set regulatory domain"""
        if domain not in self.regulatory_domains:
            print(f"Unknown regulatory domain: {domain}")
            return False
        
        try:
            result = subprocess.run(["iw", "reg", "set", domain], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Regulatory domain set to {domain}")
                return True
            else:
                print(f"Failed to set regulatory domain: {result.stderr}")
                return False
        
        except FileNotFoundError:
            print("iw command not available")
            return False
        except Exception as e:
            print(f"Error setting regulatory domain: {e}")
            return False
    
    def get_channel_list(self, domain: str, band: str = "both") -> List[ChannelInfo]:
        """Get available channels for regulatory domain"""
        if domain not in self.regulatory_domains:
            return []
        
        domain_info = self.regulatory_domains[domain]
        channels = domain_info.channels
        
        if band == "2.4":
            channels = [ch for ch in channels if ch.band == "2.4GHz"]
        elif band == "5":
            channels = [ch for ch in channels if ch.band == "5GHz"]
        
        return channels
    
    def validate_frequency_power(self, domain: str, frequency: int, power: int) -> Dict[str, any]:
        """Validate frequency and power for regulatory domain"""
        result = {
            "valid": False,
            "frequency": frequency,
            "power": power,
            "domain": domain,
            "max_allowed_power": 0,
            "channel": None,
            "band": None,
            "flags": [],
            "issues": [],
            "warnings": []
        }
        
        if domain not in self.regulatory_domains:
            result["issues"].append(f"Unknown regulatory domain: {domain}")
            return result
        
        domain_info = self.regulatory_domains[domain]
        
        # Find matching channel
        for channel in domain_info.channels:
            if channel.frequency == frequency:
                result["channel"] = channel.channel
                result["band"] = channel.band
                result["max_allowed_power"] = channel.max_power
                result["flags"] = channel.flags
                
                if power <= channel.max_power:
                    result["valid"] = True
                else:
                    result["issues"].append(f"Power {power} dBm exceeds maximum {channel.max_power} dBm")
                
                if "DFS" in channel.flags:
                    result["warnings"].append("DFS (radar detection) required for this frequency")
                
                break
        
        if not result["channel"]:
            result["issues"].append(f"Frequency {frequency} MHz not allowed in {domain}")
        
        return result
    
    def generate_regulatory_report(self, domains: Optional[List[str]] = None) -> str:
        """Generate comprehensive regulatory report"""
        if not domains:
            domains = list(self.regulatory_domains.keys())
        
        report_lines = []
        report_lines.append("Wireless Regulatory Report")
        report_lines.append("=" * 40)
        report_lines.append(f"Generated: {time.ctime()}")
        report_lines.append("")
        
        # Current regulatory status
        current_domain = self.get_current_regulatory_domain()
        if current_domain:
            report_lines.append(f"Current Domain: {current_domain}")
        else:
            report_lines.append("Current Domain: Not set or unknown")
        
        # Database status
        db_status = self.check_regulatory_database()
        db_icon = "✅" if db_status["db_exists"] else "❌"
        sig_icon = "✅" if db_status["sig_exists"] else "❌"
        
        report_lines.append(f"Database Status: {db_icon} regulatory.db ({db_status['db_size']} bytes)")
        report_lines.append(f"Signature Status: {sig_icon} regulatory.db.p7s ({db_status['sig_size']} bytes)")
        report_lines.append("")
        
        # Domain information
        for domain in domains:
            if domain not in self.regulatory_domains:
                continue
            
            domain_info = self.regulatory_domains[domain]
            report_lines.append(f"{domain}: {domain_info.name}")
            report_lines.append(f"  DFS Region: {domain_info.dfs_region}")
            
            # Channel summary
            channels_2_4 = [ch for ch in domain_info.channels if ch.band == "2.4GHz"]
            channels_5 = [ch for ch in domain_info.channels if ch.band == "5GHz"]
            
            report_lines.append(f"  2.4 GHz Channels: {len(channels_2_4)}")
            if channels_2_4:
                ch_range = f"{channels_2_4[0].channel}-{channels_2_4[-1].channel}"
                max_power = max(ch.max_power for ch in channels_2_4)
                report_lines.append(f"    Range: {ch_range}, Max Power: {max_power} dBm")
            
            report_lines.append(f"  5 GHz Channels: {len(channels_5)}")
            if channels_5:
                dfs_channels = [ch for ch in channels_5 if "DFS" in ch.flags]
                non_dfs_channels = [ch for ch in channels_5 if "DFS" not in ch.flags]
                report_lines.append(f"    Non-DFS: {len(non_dfs_channels)}, DFS: {len(dfs_channels)}")
            
            # Restrictions
            if domain_info.restrictions:
                report_lines.append("  Restrictions:")
                for restriction in domain_info.restrictions:
                    report_lines.append(f"    - {restriction}")
            
            report_lines.append("")
        
        return "\n".join(report_lines)
    
    def check_driver_compliance(self, driver: str, domain: str) -> Dict[str, any]:
        """Check driver compliance with regulatory domain"""
        # Driver capabilities (simplified)
        driver_capabilities = {
            "ath11k": {"monitor_mode": True, "packet_injection": True},
            "ath10k": {"monitor_mode": True, "packet_injection": True},
            "iwlwifi": {"monitor_mode": True, "packet_injection": False},
            "rt2x00": {"monitor_mode": True, "packet_injection": True},
            "rtw88": {"monitor_mode": True, "packet_injection": True},
            "mt76": {"monitor_mode": True, "packet_injection": True}
        }
        
        # Domain restrictions
        domain_restrictions = {
            "US": {"monitor_mode": True, "packet_injection": True},
            "EU": {"monitor_mode": True, "packet_injection": False},
            "JP": {"monitor_mode": False, "packet_injection": False},
            "CN": {"monitor_mode": False, "packet_injection": False}
        }
        
        result = {
            "compliant": True,
            "driver": driver,
            "domain": domain,
            "issues": [],
            "warnings": [],
            "recommendations": []
        }
        
        if driver not in driver_capabilities:
            result["issues"].append(f"Unknown driver: {driver}")
            result["compliant"] = False
            return result
        
        if domain not in domain_restrictions:
            result["issues"].append(f"Unknown domain: {domain}")
            result["compliant"] = False
            return result
        
        driver_caps = driver_capabilities[driver]
        domain_rules = domain_restrictions[domain]
        
        # Check monitor mode
        if driver_caps["monitor_mode"] and not domain_rules["monitor_mode"]:
            result["issues"].append("Monitor mode capability conflicts with domain restrictions")
            result["compliant"] = False
        
        # Check packet injection
        if driver_caps["packet_injection"] and not domain_rules["packet_injection"]:
            result["issues"].append("Packet injection capability conflicts with domain restrictions")
            result["compliant"] = False
        
        # Add domain-specific recommendations
        if domain in self.regulatory_domains:
            result["recommendations"].extend(self.regulatory_domains[domain].restrictions)
        
        return result

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Wireless Regulatory Manager")
    parser.add_argument("command", choices=[
        "status", "download", "set", "get", "channels", "validate", "report", "compliance"
    ], help="Regulatory command")
    
    parser.add_argument("--domain", help="Regulatory domain code")
    parser.add_argument("--frequency", type=int, help="Frequency in MHz")
    parser.add_argument("--power", type=int, help="Power in dBm")
    parser.add_argument("--band", choices=["2.4", "5", "both"], help="Frequency band")
    parser.add_argument("--driver", help="Driver name for compliance check")
    parser.add_argument("--force", action="store_true", help="Force download")
    parser.add_argument("--output", "-o", help="Output file")
    
    args = parser.parse_args()
    
    manager = WirelessRegulatoryManager()
    
    if args.command == "status":
        status = manager.check_regulatory_database()
        current_domain = manager.get_current_regulatory_domain()
        
        print("Regulatory Database Status:")
        print(f"Current Domain: {current_domain or 'Not set'}")
        
        db_status = "✅" if status["db_exists"] else "❌"
        sig_status = "✅" if status["sig_exists"] else "❌"
        
        print(f"{db_status} regulatory.db ({status['db_size']} bytes)")
        if status["db_modified"]:
            print(f"   Modified: {status['db_modified']}")
        
        print(f"{sig_status} regulatory.db.p7s ({status['sig_size']} bytes)")
        if status["sig_modified"]:
            print(f"   Modified: {status['sig_modified']}")
        
        if not status["db_exists"] or not status["sig_exists"]:
            print("\nTo download regulatory database:")
            print("  sudo python3 regulatory-manager.py download")
    
    elif args.command == "download":
        success = manager.download_regulatory_database(force=args.force)
        if not success:
            return 1
    
    elif args.command == "set":
        if not args.domain:
            print("Error: Domain required")
            return 1
        
        success = manager.set_regulatory_domain(args.domain)
        if not success:
            return 1
    
    elif args.command == "get":
        domain = manager.get_current_regulatory_domain()
        if domain:
            print(f"Current regulatory domain: {domain}")
        else:
            print("Regulatory domain not set or unknown")
    
    elif args.command == "channels":
        if not args.domain:
            print("Error: Domain required")
            return 1
        
        channels = manager.get_channel_list(args.domain, args.band or "both")
        
        if channels:
            print(f"Available channels in {args.domain}:")
            
            current_band = None
            for channel in channels:
                if channel.band != current_band:
                    current_band = channel.band
                    print(f"\n{current_band}:")
                
                flags_str = f" ({', '.join(channel.flags)})" if channel.flags else ""
                print(f"  Channel {channel.channel:3d}: {channel.frequency} MHz, "
                      f"Max {channel.max_power} dBm{flags_str}")
        else:
            print(f"No channels available for {args.domain}")
    
    elif args.command == "validate":
        if not args.domain or not args.frequency or not args.power:
            print("Error: Domain, frequency, and power required")
            return 1
        
        result = manager.validate_frequency_power(args.domain, args.frequency, args.power)
        
        if result["valid"]:
            print(f"✅ {args.frequency} MHz @ {args.power} dBm is valid in {args.domain}")
        else:
            print(f"❌ {args.frequency} MHz @ {args.power} dBm is NOT valid in {args.domain}")
        
        if result["channel"]:
            print(f"Channel: {result['channel']} ({result['band']})")
            print(f"Max allowed power: {result['max_allowed_power']} dBm")
        
        for issue in result["issues"]:
            print(f"Issue: {issue}")
        
        for warning in result["warnings"]:
            print(f"Warning: {warning}")
    
    elif args.command == "report":
        domains = [args.domain] if args.domain else None
        report = manager.generate_regulatory_report(domains)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(report)
            print(f"Report saved to: {args.output}")
        else:
            print(report)
    
    elif args.command == "compliance":
        if not args.driver or not args.domain:
            print("Error: Driver and domain required")
            return 1
        
        result = manager.check_driver_compliance(args.driver, args.domain)
        
        if result["compliant"]:
            print(f"✅ {args.driver} is compliant in {args.domain}")
        else:
            print(f"❌ {args.driver} is NOT compliant in {args.domain}")
        
        for issue in result["issues"]:
            print(f"Issue: {issue}")
        
        for warning in result["warnings"]:
            print(f"Warning: {warning}")
        
        if result["recommendations"]:
            print("\nRecommendations:")
            for rec in result["recommendations"]:
                print(f"  - {rec}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())