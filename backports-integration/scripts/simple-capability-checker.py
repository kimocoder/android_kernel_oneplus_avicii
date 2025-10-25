#!/usr/bin/env python3
"""
Simple Wireless Driver Capability Checker

This module provides basic functionality to check wireless driver capabilities.
"""

import os
import subprocess
import re
from typing import Dict, List, Tuple

class SimpleCapabilityChecker:
    """Simple checker for wireless driver capabilities"""
    
    def __init__(self):
        """Initialize the capability checker"""
        self.capabilities = {
            "monitor_mode": False,
            "packet_injection": False,
            "mesh_networking": False,
            "wpa3_support": False,
            "spectral_scan": False
        }
    
    def _run_command(self, cmd: List[str]) -> Tuple[int, str, str]:
        """Run a system command"""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.returncode, result.stdout, result.stderr
        except Exception:
            return -1, "", "Command failed"
    
    def check_monitor_mode(self) -> bool:
        """Check if monitor mode is supported"""
        # Check if iw is available
        exit_code, stdout, stderr = self._run_command(["which", "iw"])
        if exit_code != 0:
            return False
        
        # Check if mac80211 is loaded
        exit_code, stdout, stderr = self._run_command(["lsmod"])
        if exit_code == 0 and "mac80211" in stdout:
            return True
        
        return False
    
    def check_packet_injection(self) -> bool:
        """Check if packet injection is supported"""
        # Requires monitor mode
        if not self.check_monitor_mode():
            return False
        
        # Check for packet socket support
        if os.path.exists("/proc/net/packet"):
            return True
        
        return False
    
    def check_mesh_networking(self) -> bool:
        """Check if mesh networking is supported"""
        # Check iw mesh support
        exit_code, stdout, stderr = self._run_command(["iw", "list"])
        if exit_code == 0 and "mesh point" in stdout.lower():
            return True
        
        return False
    
    def check_wpa3_support(self) -> bool:
        """Check if WPA3 is supported"""
        # Check wpa_supplicant version
        exit_code, stdout, stderr = self._run_command(["wpa_supplicant", "-v"])
        if exit_code == 0:
            version_match = re.search(r'v(\d+\.\d+)', stdout)
            if version_match:
                version = float(version_match.group(1))
                return version >= 2.6
        
        return False
    
    def check_spectral_scan(self) -> bool:
        """Check if spectral scan is supported"""
        # Check for debugfs spectral interfaces
        import glob
        patterns = [
            "/sys/kernel/debug/ieee80211/*/ath*/spectral_scan_ctl",
            "/sys/kernel/debug/ieee80211/*/ath10k/spectral_scan_ctl"
        ]
        
        for pattern in patterns:
            if glob.glob(pattern):
                return True
        
        return False
    
    def check_all_capabilities(self) -> Dict[str, bool]:
        """Check all capabilities"""
        self.capabilities["monitor_mode"] = self.check_monitor_mode()
        self.capabilities["packet_injection"] = self.check_packet_injection()
        self.capabilities["mesh_networking"] = self.check_mesh_networking()
        self.capabilities["wpa3_support"] = self.check_wpa3_support()
        self.capabilities["spectral_scan"] = self.check_spectral_scan()
        
        return self.capabilities

def main():
    """Main function"""
    checker = SimpleCapabilityChecker()
    results = checker.check_all_capabilities()
    
    print("Wireless Capability Check Results:")
    print("=" * 40)
    
    for capability, supported in results.items():
        status = "✓ Supported" if supported else "✗ Not Supported"
        print(f"{capability.replace('_', ' ').title()}: {status}")

if __name__ == "__main__":
    main()