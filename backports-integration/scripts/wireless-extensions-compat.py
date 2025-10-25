#!/usr/bin/env python3
"""
Wireless Extensions Compatibility Layer

This module provides compatibility with legacy wireless extensions (WEXT)
while using the modern cfg80211/nl80211 stack.
"""

import os
import sys
import subprocess
import struct
import socket
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

class WextCommand(Enum):
    """Wireless Extensions commands"""
    SIOCGIWNAME = 0x8B01    # Get name
    SIOCSIWNWID = 0x8B02    # Set network ID
    SIOCGIWNWID = 0x8B03    # Get network ID
    SIOCSIWFREQ = 0x8B04    # Set frequency/channel
    SIOCGIWFREQ = 0x8B05    # Get frequency/channel
    SIOCSIWMODE = 0x8B06    # Set operation mode
    SIOCGIWMODE = 0x8B07    # Get operation mode
    SIOCSIWSENS = 0x8B08    # Set sensitivity
    SIOCGIWSENS = 0x8B09    # Get sensitivity
    SIOCSIWRANGE = 0x8B0A   # Set range
    SIOCGIWRANGE = 0x8B0B   # Get range
    SIOCSIWPRIV = 0x8B0C    # Set private
    SIOCGIWPRIV = 0x8B0D    # Get private
    SIOCSIWSTATS = 0x8B0E   # Set statistics
    SIOCGIWSTATS = 0x8B0F   # Get statistics
    SIOCSIWSPY = 0x8B10     # Set spy addresses
    SIOCGIWSPY = 0x8B11     # Get spy info
    SIOCSIWTHRSPY = 0x8B12  # Set spy threshold
    SIOCGIWTHRSPY = 0x8B13  # Get spy threshold
    SIOCSIWAP = 0x8B14      # Set access point MAC
    SIOCGIWAP = 0x8B15      # Get access point MAC
    SIOCSIWSCAN = 0x8B18    # Trigger scanning
    SIOCGIWSCAN = 0x8B19    # Get scanning results
    SIOCSIWESSID = 0x8B1A   # Set ESSID
    SIOCGIWESSID = 0x8B1B   # Get ESSID
    SIOCSIWNICKN = 0x8B1C   # Set nickname
    SIOCGIWNICKN = 0x8B1D   # Get nickname
    SIOCSIWRATE = 0x8B20    # Set default bit rate
    SIOCGIWRATE = 0x8B21    # Get default bit rate
    SIOCSIWRTS = 0x8B22     # Set RTS/CTS threshold
    SIOCGIWRTS = 0x8B23     # Get RTS/CTS threshold
    SIOCSIWFRAG = 0x8B24    # Set fragmentation threshold
    SIOCGIWFRAG = 0x8B25    # Get fragmentation threshold
    SIOCSIWTXPOW = 0x8B26   # Set transmit power
    SIOCGIWTXPOW = 0x8B27   # Get transmit power
    SIOCSIWRETRY = 0x8B28   # Set retry limits
    SIOCGIWRETRY = 0x8B29   # Get retry limits
    SIOCSIWENCODE = 0x8B2A  # Set encoding token
    SIOCGIWENCODE = 0x8B2B  # Get encoding token
    SIOCSIWPOWER = 0x8B2C   # Set power management
    SIOCGIWPOWER = 0x8B2D   # Get power management

@dataclass
class WirelessInterface:
    """Information about a wireless interface"""
    name: str
    driver: str
    chipset: str
    supports_wext: bool
    supports_nl80211: bool
    current_mode: str
    capabilities: List[str]

class WirelessExtensionsCompat:
    """Wireless Extensions compatibility layer"""
    
    def __init__(self):
        """Initialize WEXT compatibility layer"""
        self.interfaces = {}
        self.wext_tools = ["iwconfig", "iwlist", "iwspy", "iwpriv"]
        self.nl80211_tools = ["iw"]
        
        # Mode mappings between WEXT and nl80211
        self.mode_mappings = {
            "managed": "station",
            "master": "ap",
            "ad-hoc": "adhoc",
            "monitor": "monitor",
            "repeater": "wds",
            "secondary": "wds",
            "auto": "station"
        }
        
        # Scan for available interfaces
        self._scan_interfaces()
    
    def _run_command(self, cmd: List[str]) -> Tuple[int, str, str]:
        """Run a system command"""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return -1, "", str(e)
    
    def _scan_interfaces(self):
        """Scan for available wireless interfaces"""
        self.interfaces = {}
        
        # Get interfaces from /proc/net/wireless (WEXT)
        wext_interfaces = self._get_wext_interfaces()
        
        # Get interfaces from iw (nl80211)
        nl80211_interfaces = self._get_nl80211_interfaces()
        
        # Combine information
        all_interface_names = set(wext_interfaces.keys()) | set(nl80211_interfaces.keys())
        
        for iface_name in all_interface_names:
            wext_info = wext_interfaces.get(iface_name, {})
            nl80211_info = nl80211_interfaces.get(iface_name, {})
            
            self.interfaces[iface_name] = WirelessInterface(
                name=iface_name,
                driver=nl80211_info.get("driver", "unknown"),
                chipset=nl80211_info.get("chipset", "unknown"),
                supports_wext=iface_name in wext_interfaces,
                supports_nl80211=iface_name in nl80211_interfaces,
                current_mode=nl80211_info.get("mode", "unknown"),
                capabilities=nl80211_info.get("capabilities", [])
            )
    
    def _get_wext_interfaces(self) -> Dict[str, Dict[str, Any]]:
        """Get wireless interfaces from /proc/net/wireless"""
        interfaces = {}
        
        try:
            with open("/proc/net/wireless", "r") as f:
                lines = f.readlines()
                
            # Skip header lines
            for line in lines[2:]:
                if line.strip():
                    parts = line.split()
                    if parts:
                        iface_name = parts[0].rstrip(":")
                        interfaces[iface_name] = {
                            "link_quality": parts[2] if len(parts) > 2 else "0",
                            "signal_level": parts[3] if len(parts) > 3 else "0",
                            "noise_level": parts[4] if len(parts) > 4 else "0"
                        }
        except FileNotFoundError:
            pass  # WEXT not available
        
        return interfaces
    
    def _get_nl80211_interfaces(self) -> Dict[str, Dict[str, Any]]:
        """Get wireless interfaces from iw"""
        interfaces = {}
        
        exit_code, stdout, stderr = self._run_command(["iw", "dev"])
        if exit_code != 0:
            return interfaces
        
        current_interface = None
        for line in stdout.split('\n'):
            line = line.strip()
            
            if line.startswith("Interface "):
                current_interface = line.split()[1]
                interfaces[current_interface] = {
                    "driver": "unknown",
                    "chipset": "unknown",
                    "mode": "unknown",
                    "capabilities": []
                }
            elif current_interface and line.startswith("type "):
                interfaces[current_interface]["mode"] = line.split()[1]
        
        return interfaces
    
    def check_wext_compatibility(self) -> Dict[str, Any]:
        """Check wireless extensions compatibility"""
        compatibility = {
            "wext_available": False,
            "nl80211_available": False,
            "tools_available": {},
            "interfaces": {},
            "compatibility_issues": []
        }
        
        # Check if WEXT is available
        compatibility["wext_available"] = os.path.exists("/proc/net/wireless")
        
        # Check if nl80211 is available
        exit_code, stdout, stderr = self._run_command(["iw", "list"])
        compatibility["nl80211_available"] = exit_code == 0
        
        # Check tool availability
        for tool in self.wext_tools + self.nl80211_tools:
            exit_code, stdout, stderr = self._run_command(["which", tool])
            compatibility["tools_available"][tool] = exit_code == 0
        
        # Check interface compatibility
        for iface_name, iface_info in self.interfaces.items():
            compatibility["interfaces"][iface_name] = {
                "supports_wext": iface_info.supports_wext,
                "supports_nl80211": iface_info.supports_nl80211,
                "driver": iface_info.driver,
                "mode": iface_info.current_mode
            }
            
            # Check for compatibility issues
            if iface_info.supports_wext and not iface_info.supports_nl80211:
                compatibility["compatibility_issues"].append(
                    f"Interface {iface_name} only supports WEXT (legacy)"
                )
            elif iface_info.supports_nl80211 and not iface_info.supports_wext:
                compatibility["compatibility_issues"].append(
                    f"Interface {iface_name} only supports nl80211 (may have WEXT compatibility issues)"
                )
        
        return compatibility
    
    def translate_wext_to_nl80211(self, wext_command: str, interface: str, *args) -> Optional[List[str]]:
        """Translate WEXT command to equivalent nl80211 command"""
        translations = {
            "iwconfig": {
                "essid": lambda iface, essid: ["iw", "dev", iface, "connect", essid],
                "mode": lambda iface, mode: ["iw", "dev", iface, "set", "type", self.mode_mappings.get(mode, mode)],
                "freq": lambda iface, freq: ["iw", "dev", iface, "set", "freq", freq],
                "channel": lambda iface, ch: ["iw", "dev", iface, "set", "channel", ch],
                "txpower": lambda iface, power: ["iw", "dev", iface, "set", "txpower", "fixed", power],
                "power": lambda iface, state: ["iw", "dev", iface, "set", "power_save", "on" if state == "on" else "off"]
            },
            "iwlist": {
                "scan": lambda iface: ["iw", "dev", iface, "scan"],
                "frequency": lambda iface: ["iw", "dev", iface, "info"],
                "rate": lambda iface: ["iw", "dev", iface, "info"],
                "power": lambda iface: ["iw", "dev", iface, "info"]
            },
            "iwspy": {
                "": lambda iface: ["iw", "dev", iface, "station", "dump"]
            }
        }
        
        if wext_command in translations:
            if args and args[0] in translations[wext_command]:
                return translations[wext_command][args[0]](interface, *args[1:])
            elif "" in translations[wext_command]:
                return translations[wext_command][""](interface)
        
        return None
    
    def execute_wext_command(self, command: List[str]) -> Tuple[int, str, str]:
        """Execute WEXT command with nl80211 fallback"""
        if not command:
            return -1, "", "Empty command"
        
        tool = command[0]
        
        # Try original WEXT command first
        if tool in self.wext_tools:
            exit_code, stdout, stderr = self._run_command(command)
            if exit_code == 0:
                return exit_code, stdout, stderr
            
            # If WEXT command failed, try nl80211 translation
            if len(command) >= 2:
                interface = command[1]
                if interface in self.interfaces:
                    nl80211_cmd = self.translate_wext_to_nl80211(tool, interface, *command[2:])
                    if nl80211_cmd:
                        return self._run_command(nl80211_cmd)
        
        # Execute as-is if no translation available
        return self._run_command(command)
    
    def create_wext_wrapper_scripts(self, output_dir: str) -> Dict[str, bool]:
        """Create wrapper scripts for WEXT tools"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        for tool in self.wext_tools:
            script_path = output_path / f"{tool}-compat"
            
            script_content = f'''#!/bin/bash
#
# Wireless Extensions Compatibility Wrapper for {tool}
# Automatically falls back to nl80211 commands when WEXT fails
#

# Check if original tool exists
if command -v {tool} >/dev/null 2>&1; then
    # Try original WEXT tool first
    if {tool} "$@" 2>/dev/null; then
        exit 0
    fi
fi

# WEXT failed or not available, try nl80211 equivalent
case "$1" in
    */*)
        # Interface specified, try to translate command
        interface="$1"
        shift
        
        case "{tool}" in
            "iwconfig")
                case "$1" in
                    "essid")
                        exec iw dev "$interface" connect "$2"
                        ;;
                    "mode")
                        case "$2" in
                            "managed") exec iw dev "$interface" set type station ;;
                            "master") exec iw dev "$interface" set type ap ;;
                            "ad-hoc") exec iw dev "$interface" set type adhoc ;;
                            "monitor") exec iw dev "$interface" set type monitor ;;
                            *) exec iw dev "$interface" set type "$2" ;;
                        esac
                        ;;
                    "freq")
                        exec iw dev "$interface" set freq "$2"
                        ;;
                    "channel")
                        exec iw dev "$interface" set channel "$2"
                        ;;
                    *)
                        echo "No nl80211 equivalent for: {tool} $interface $*" >&2
                        exit 1
                        ;;
                esac
                ;;
            "iwlist")
                case "$1" in
                    "scan")
                        exec iw dev "$interface" scan
                        ;;
                    "frequency"|"freq")
                        exec iw dev "$interface" info
                        ;;
                    *)
                        echo "No nl80211 equivalent for: {tool} $interface $*" >&2
                        exit 1
                        ;;
                esac
                ;;
            *)
                echo "No nl80211 equivalent for: {tool} $*" >&2
                exit 1
                ;;
        esac
        ;;
    *)
        echo "Usage: {tool}-compat <interface> [options]" >&2
        echo "This is a compatibility wrapper that falls back to nl80211 commands" >&2
        exit 1
        ;;
esac
'''
            
            try:
                with open(script_path, 'w') as f:
                    f.write(script_content)
                os.chmod(script_path, 0o755)
                results[tool] = True
            except Exception as e:
                print(f"Error creating wrapper for {tool}: {e}")
                results[tool] = False
        
        return results
    
    def generate_compatibility_report(self) -> Dict[str, Any]:
        """Generate comprehensive compatibility report"""
        report = {
            "compatibility_status": self.check_wext_compatibility(),
            "interfaces": {},
            "recommendations": []
        }
        
        # Add detailed interface information
        for iface_name, iface_info in self.interfaces.items():
            report["interfaces"][iface_name] = {
                "name": iface_info.name,
                "driver": iface_info.driver,
                "chipset": iface_info.chipset,
                "supports_wext": iface_info.supports_wext,
                "supports_nl80211": iface_info.supports_nl80211,
                "current_mode": iface_info.current_mode,
                "capabilities": iface_info.capabilities
            }
        
        # Generate recommendations
        compat_status = report["compatibility_status"]
        
        if not compat_status["wext_available"]:
            report["recommendations"].append("WEXT support not available - use nl80211 tools")
        
        if not compat_status["nl80211_available"]:
            report["recommendations"].append("nl80211 support not available - limited functionality")
        
        missing_tools = [tool for tool, available in compat_status["tools_available"].items() if not available]
        if missing_tools:
            report["recommendations"].append(f"Install missing tools: {', '.join(missing_tools)}")
        
        if compat_status["compatibility_issues"]:
            report["recommendations"].append("Address interface compatibility issues")
        
        return report

def main():
    """Main function for testing"""
    compat = WirelessExtensionsCompat()
    
    print("Wireless Extensions Compatibility Layer")
    print("=" * 50)
    
    # Check compatibility
    compatibility = compat.check_wext_compatibility()
    
    print("System Compatibility:")
    wext_status = "✓" if compatibility["wext_available"] else "✗"
    nl80211_status = "✓" if compatibility["nl80211_available"] else "✗"
    print(f"  WEXT Support: {wext_status}")
    print(f"  nl80211 Support: {nl80211_status}")
    
    print(f"\nTool Availability:")
    for tool, available in compatibility["tools_available"].items():
        status = "✓" if available else "✗"
        print(f"  {status} {tool}")
    
    print(f"\nWireless Interfaces:")
    if not compat.interfaces:
        print("  No wireless interfaces found")
    else:
        for iface_name, iface_info in compat.interfaces.items():
            wext_support = "✓" if iface_info.supports_wext else "✗"
            nl80211_support = "✓" if iface_info.supports_nl80211 else "✗"
            print(f"  {iface_name}:")
            print(f"    Driver: {iface_info.driver}")
            print(f"    Mode: {iface_info.current_mode}")
            print(f"    WEXT: {wext_support}, nl80211: {nl80211_support}")
    
    if compatibility["compatibility_issues"]:
        print(f"\nCompatibility Issues:")
        for issue in compatibility["compatibility_issues"]:
            print(f"  ⚠️  {issue}")
    
    # Generate report
    report = compat.generate_compatibility_report()
    if report["recommendations"]:
        print(f"\nRecommendations:")
        for rec in report["recommendations"]:
            print(f"  - {rec}")

if __name__ == "__main__":
    main()