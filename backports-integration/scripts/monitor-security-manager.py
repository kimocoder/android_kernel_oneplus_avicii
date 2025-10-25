#!/usr/bin/env python3
"""
Monitor Mode and Security Manager

This module provides comprehensive monitor mode and security capabilities
including packet capture, injection, channel switching, and regulatory compliance.
"""

import os
import sys
import subprocess
import json
import struct
import socket
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import warnings

class MonitorMode(Enum):
    """Monitor mode types"""
    PASSIVE = "passive"
    ACTIVE = "active"
    INJECTION = "injection"
    ANALYSIS = "analysis"

class ChannelWidth(Enum):
    """Channel width options"""
    HT20 = "HT20"
    HT40_PLUS = "HT40+"
    HT40_MINUS = "HT40-"
    VHT80 = "VHT80"
    VHT160 = "VHT160"

class InjectionMode(Enum):
    """Packet injection modes"""
    RAW = "raw"
    BEACON = "beacon"
    PROBE = "probe"
    DATA = "data"
    MANAGEMENT = "management"

@dataclass
class ChannelConfig:
    """Channel configuration"""
    frequency: int
    channel: int
    width: ChannelWidth
    center_freq1: Optional[int] = None
    center_freq2: Optional[int] = None
    regulatory_domain: str = "US"

@dataclass
class MonitorConfig:
    """Monitor mode configuration"""
    interface: str
    mode: MonitorMode
    channel_config: ChannelConfig
    capture_filter: Optional[str] = None
    radiotap_enabled: bool = True
    fcs_enabled: bool = True
    retry_count: int = 3

@dataclass
class InjectionConfig:
    """Packet injection configuration"""
    interface: str
    mode: InjectionMode
    rate_mbps: float = 1.0
    power_dbm: int = 15
    retry_count: int = 3
    sequence_control: bool = True
    timestamp_correction: bool = True

class MonitorSecurityManager:
    """Monitor mode and security manager"""
    
    def __init__(self, kernel_root: str = "."):
        """Initialize monitor security manager"""
        self.kernel_root = Path(kernel_root).resolve()
        self.backports_dir = self.kernel_root / "backports-integration"
        
        # Regulatory domains and their restrictions
        self.regulatory_domains = {
            "US": {
                "channels_2ghz": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
                "channels_5ghz": [36, 40, 44, 48, 149, 153, 157, 161, 165],
                "max_power_dbm": 30,
                "dfs_required": [52, 56, 60, 64, 100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140],
                "monitor_allowed": True,
                "injection_allowed": True
            },
            "EU": {
                "channels_2ghz": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
                "channels_5ghz": [36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140],
                "max_power_dbm": 20,
                "dfs_required": [52, 56, 60, 64, 100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140],
                "monitor_allowed": True,
                "injection_allowed": False
            },
            "JP": {
                "channels_2ghz": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
                "channels_5ghz": [36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140],
                "max_power_dbm": 20,
                "dfs_required": [52, 56, 60, 64, 100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140],
                "monitor_allowed": True,
                "injection_allowed": False
            }
        }
        
        # Supported drivers and their capabilities
        self.driver_capabilities = {
            "ath10k": {
                "monitor_mode": True,
                "packet_injection": True,
                "channel_switching": True,
                "radiotap": True,
                "spectral_scan": True,
                "rate_control": True,
                "power_control": True
            },
            "ath11k": {
                "monitor_mode": True,
                "packet_injection": True,
                "channel_switching": True,
                "radiotap": True,
                "spectral_scan": True,
                "rate_control": True,
                "power_control": True
            },
            "iwlwifi": {
                "monitor_mode": True,
                "packet_injection": False,
                "channel_switching": True,
                "radiotap": True,
                "spectral_scan": False,
                "rate_control": False,
                "power_control": True
            },
            "rt2x00": {
                "monitor_mode": True,
                "packet_injection": True,
                "channel_switching": True,
                "radiotap": True,
                "spectral_scan": False,
                "rate_control": True,
                "power_control": True
            }
        }
    
    def _run_command(self, cmd: List[str]) -> Tuple[int, str, str]:
        """Run a system command"""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return -1, "", str(e)
    
    def detect_wireless_interfaces(self) -> List[Dict[str, str]]:
        """Detect available wireless interfaces"""
        interfaces = []
        
        # Check for wireless interfaces
        exit_code, stdout, stderr = self._run_command(["iw", "dev"])
        
        if exit_code == 0:
            current_interface = None
            current_driver = None
            
            for line in stdout.split('\n'):
                line = line.strip()
                if line.startswith('Interface'):
                    current_interface = line.split()[1]
                elif line.startswith('type') and current_interface:
                    interface_type = line.split()[1]
                    
                    # Get driver information
                    exit_code2, stdout2, stderr2 = self._run_command([
                        "readlink", "-f", f"/sys/class/net/{current_interface}/device/driver"
                    ])
                    
                    if exit_code2 == 0:
                        current_driver = Path(stdout2.strip()).name
                    
                    interfaces.append({
                        "interface": current_interface,
                        "type": interface_type,
                        "driver": current_driver or "unknown",
                        "capabilities": self.driver_capabilities.get(current_driver, {})
                    })
                    
                    current_interface = None
                    current_driver = None
        
        return interfaces
    
    def validate_regulatory_compliance(self, config: Union[MonitorConfig, InjectionConfig], 
                                     regulatory_domain: str = "US") -> Dict[str, any]:
        """Enhanced regulatory compliance validation with comprehensive security warnings"""
        validation = {
            "compliant": True,
            "warnings": [],
            "errors": [],
            "recommendations": [],
            "security_alerts": [],
            "compliance_level": "UNKNOWN",
            "risk_assessment": "LOW"
        }
        
        if regulatory_domain not in self.regulatory_domains:
            validation["errors"].append(f"Unknown regulatory domain: {regulatory_domain}")
            validation["compliant"] = False
            validation["compliance_level"] = "INVALID"
            validation["risk_assessment"] = "HIGH"
            return validation
        
        domain_rules = self.regulatory_domains[regulatory_domain]
        
        # Check channel compliance
        if isinstance(config, MonitorConfig):
            channel = config.channel_config.channel
            frequency = config.channel_config.frequency
            channel_width = config.channel_config.width
        else:
            # For injection config, we'd need to get channel from interface
            channel = None
            frequency = None
            channel_width = None
        
        if channel:
            # Check 2.4GHz channels
            if 1 <= channel <= 14:
                if channel not in domain_rules["channels_2ghz"]:
                    validation["errors"].append(f"Channel {channel} not allowed in {regulatory_domain}")
                    validation["security_alerts"].append(f"REGULATORY VIOLATION: Using prohibited channel {channel}")
                    validation["compliant"] = False
                    validation["risk_assessment"] = "HIGH"
                
                # Special warnings for specific channels
                if channel == 14 and regulatory_domain != "JP":
                    validation["warnings"].append("Channel 14 is only allowed in Japan")
                    validation["security_alerts"].append("POTENTIAL VIOLATION: Channel 14 usage outside Japan")
                
                if channel in [12, 13] and regulatory_domain == "US":
                    validation["warnings"].append("Channels 12-13 have restricted use in US")
                    validation["security_alerts"].append("RESTRICTED CHANNEL: Limited power/indoor use only")
                    
            # Check 5GHz channels
            elif channel >= 36:
                if channel not in domain_rules["channels_5ghz"]:
                    validation["errors"].append(f"Channel {channel} not allowed in {regulatory_domain}")
                    validation["security_alerts"].append(f"REGULATORY VIOLATION: Using prohibited 5GHz channel {channel}")
                    validation["compliant"] = False
                    validation["risk_assessment"] = "HIGH"
                
                # Check DFS requirements
                if channel in domain_rules["dfs_required"]:
                    validation["warnings"].append(f"Channel {channel} requires DFS compliance and radar detection")
                    validation["security_alerts"].append(f"DFS REQUIRED: Channel {channel} needs radar detection capability")
                    validation["recommendations"].append("Ensure DFS radar detection is enabled and functional")
                
                # Weather radar channels (extra caution)
                weather_radar_channels = [120, 124, 128]
                if channel in weather_radar_channels:
                    validation["warnings"].append(f"Channel {channel} may interfere with weather radar")
                    validation["security_alerts"].append(f"WEATHER RADAR RISK: Channel {channel} interference possible")
                    validation["risk_assessment"] = "MEDIUM"
        
        # Check injection compliance with enhanced security warnings
        if isinstance(config, InjectionConfig):
            if not domain_rules["injection_allowed"]:
                validation["errors"].append(f"Packet injection not allowed in {regulatory_domain}")
                validation["security_alerts"].append(f"INJECTION PROHIBITED: Regulatory domain {regulatory_domain} forbids packet injection")
                validation["compliant"] = False
                validation["risk_assessment"] = "HIGH"
            
            if config.power_dbm > domain_rules["max_power_dbm"]:
                validation["errors"].append(
                    f"Power {config.power_dbm}dBm exceeds limit {domain_rules['max_power_dbm']}dBm"
                )
                validation["security_alerts"].append(
                    f"POWER VIOLATION: {config.power_dbm}dBm exceeds regulatory limit of {domain_rules['max_power_dbm']}dBm"
                )
                validation["compliant"] = False
                validation["risk_assessment"] = "HIGH"
            
            # Security warnings for injection
            if config.mode == InjectionMode.BEACON:
                validation["security_alerts"].append("BEACON INJECTION: Can create rogue access points")
                validation["recommendations"].append("Beacon injection should only be used in controlled environments")
            
            if config.mode == InjectionMode.PROBE:
                validation["security_alerts"].append("PROBE INJECTION: Can trigger network responses")
                validation["recommendations"].append("Probe injection may reveal network information")
            
            if config.mode == InjectionMode.MANAGEMENT:
                validation["security_alerts"].append("MANAGEMENT FRAME INJECTION: Can disrupt network operations")
                validation["recommendations"].append("Management frame injection requires extreme caution")
                validation["risk_assessment"] = "HIGH" if validation["risk_assessment"] != "HIGH" else "HIGH"
            
            # Rate and power warnings
            if config.rate_mbps > 54:
                validation["warnings"].append("High data rates may not be supported on all channels")
            
            if config.power_dbm > 20:
                validation["warnings"].append("High power levels may cause interference")
                validation["security_alerts"].append("HIGH POWER: Increased interference risk")
        
        # Check monitor mode compliance with security considerations
        if isinstance(config, MonitorConfig):
            if not domain_rules["monitor_allowed"]:
                validation["errors"].append(f"Monitor mode not allowed in {regulatory_domain}")
                validation["security_alerts"].append(f"MONITOR PROHIBITED: Regulatory domain {regulatory_domain} forbids monitor mode")
                validation["compliant"] = False
                validation["risk_assessment"] = "HIGH"
            
            # Security warnings for monitor mode
            if config.mode == MonitorMode.ACTIVE:
                validation["security_alerts"].append("ACTIVE MONITORING: May transmit probe requests")
                validation["recommendations"].append("Active monitoring can reveal your presence to networks")
            
            if config.mode == MonitorMode.INJECTION:
                validation["security_alerts"].append("INJECTION MODE: Combines monitoring with transmission capabilities")
                validation["recommendations"].append("Injection mode requires careful regulatory compliance")
                validation["risk_assessment"] = "MEDIUM" if validation["risk_assessment"] == "LOW" else validation["risk_assessment"]
        
        # Determine compliance level
        if validation["compliant"]:
            if validation["warnings"] or validation["security_alerts"]:
                validation["compliance_level"] = "CONDITIONAL"
            else:
                validation["compliance_level"] = "FULL"
        else:
            validation["compliance_level"] = "NON_COMPLIANT"
        
        # Add comprehensive recommendations
        if validation["compliant"]:
            validation["recommendations"].extend([
                "Verify local regulations before operation",
                "Use minimum necessary power levels",
                "Monitor for regulatory updates and changes",
                "Maintain logs of regulatory compliance checks"
            ])
            
            if isinstance(config, InjectionConfig):
                validation["recommendations"].extend([
                    "Use packet injection only in authorized environments",
                    "Implement proper access controls for injection capabilities",
                    "Monitor for unintended interference or disruption"
                ])
            
            if isinstance(config, MonitorConfig):
                validation["recommendations"].extend([
                    "Ensure monitor mode usage complies with privacy laws",
                    "Implement appropriate data handling procedures",
                    "Consider notification requirements for monitoring activities"
                ])
        else:
            validation["recommendations"].extend([
                "Modify configuration to achieve regulatory compliance",
                "Consult local regulatory authorities for guidance",
                "Consider alternative channels or power levels",
                "Implement additional safeguards and controls"
            ])
        
        # Add security-specific recommendations
        if validation["security_alerts"]:
            validation["recommendations"].extend([
                "Review security implications of current configuration",
                "Implement monitoring and logging for security events",
                "Establish incident response procedures",
                "Regular security audits and compliance reviews"
            ])
        
        return validation
    
    def configure_monitor_mode(self, config: MonitorConfig) -> Dict[str, any]:
        """Configure interface for monitor mode"""
        result = {
            "success": False,
            "interface": config.interface,
            "mode": config.mode.value,
            "channel": config.channel_config.channel,
            "commands_executed": [],
            "errors": []
        }
        
        # Validate regulatory compliance
        compliance = self.validate_regulatory_compliance(config)
        if not compliance["compliant"]:
            result["errors"].extend(compliance["errors"])
            return result
        
        # Check if interface exists
        exit_code, stdout, stderr = self._run_command(["ip", "link", "show", config.interface])
        if exit_code != 0:
            result["errors"].append(f"Interface {config.interface} not found")
            return result
        
        # Bring interface down
        cmd = ["ip", "link", "set", config.interface, "down"]
        exit_code, stdout, stderr = self._run_command(cmd)
        result["commands_executed"].append(" ".join(cmd))
        
        if exit_code != 0:
            result["errors"].append(f"Failed to bring interface down: {stderr}")
            return result
        
        # Set monitor mode
        cmd = ["iw", "dev", config.interface, "set", "type", "monitor"]
        exit_code, stdout, stderr = self._run_command(cmd)
        result["commands_executed"].append(" ".join(cmd))
        
        if exit_code != 0:
            result["errors"].append(f"Failed to set monitor mode: {stderr}")
            return result
        
        # Configure radiotap if enabled
        if config.radiotap_enabled:
            cmd = ["iw", "dev", config.interface, "set", "monitor", "otherbss"]
            exit_code, stdout, stderr = self._run_command(cmd)
            result["commands_executed"].append(" ".join(cmd))
        
        # Bring interface up
        cmd = ["ip", "link", "set", config.interface, "up"]
        exit_code, stdout, stderr = self._run_command(cmd)
        result["commands_executed"].append(" ".join(cmd))
        
        if exit_code != 0:
            result["errors"].append(f"Failed to bring interface up: {stderr}")
            return result
        
        # Set channel
        channel_result = self.set_channel(config.interface, config.channel_config)
        result["commands_executed"].extend(channel_result.get("commands_executed", []))
        
        if not channel_result["success"]:
            result["errors"].extend(channel_result.get("errors", []))
            return result
        
        result["success"] = True
        return result
    
    def set_channel(self, interface: str, channel_config: ChannelConfig) -> Dict[str, any]:
        """Set channel configuration for interface"""
        result = {
            "success": False,
            "interface": interface,
            "channel": channel_config.channel,
            "frequency": channel_config.frequency,
            "commands_executed": [],
            "errors": []
        }
        
        # Build channel command
        cmd = ["iw", "dev", interface, "set", "freq", str(channel_config.frequency)]
        
        # Add channel width
        if channel_config.width != ChannelWidth.HT20:
            cmd.extend([channel_config.width.value])
            
            if channel_config.center_freq1:
                cmd.append(str(channel_config.center_freq1))
            
            if channel_config.center_freq2:
                cmd.append(str(channel_config.center_freq2))
        
        # Execute command
        exit_code, stdout, stderr = self._run_command(cmd)
        result["commands_executed"].append(" ".join(cmd))
        
        if exit_code != 0:
            result["errors"].append(f"Failed to set channel: {stderr}")
            return result
        
        result["success"] = True
        return result
    
    def generate_radiotap_header(self, flags: int = 0, rate: int = 0, 
                                channel: int = 0, fhss: int = 0, 
                                antenna_signal: int = 0, antenna_noise: int = 0,
                                tx_power: int = 0, mcs_info: Dict[str, int] = None,
                                vht_info: Dict[str, int] = None, timestamp: int = 0) -> bytes:
        """Generate enhanced radiotap header for packet injection with advanced features"""
        # Radiotap header structure
        # it_version (1 byte) + it_pad (1 byte) + it_len (2 bytes) + it_present (4 bytes)
        
        header = bytearray()
        
        # Version (0)
        header.append(0)
        
        # Padding
        header.append(0)
        
        # Length (will be updated)
        length_pos = len(header)
        header.extend([0, 0])
        
        # Present flags
        present = 0
        present_pos = len(header)
        header.extend([0, 0, 0, 0])
        
        # Add timestamp if provided (bit 0)
        if timestamp:
            present |= (1 << 0)  # Timestamp field present
            header.extend(struct.pack('<Q', timestamp))
        
        # Add fields based on flags
        if flags:
            present |= (1 << 1)  # Flags field present
            header.append(flags)
        
        if rate:
            present |= (1 << 2)  # Rate field present
            header.append(rate)
        
        if channel:
            present |= (1 << 3)  # Channel field present
            header.extend(struct.pack('<H', channel))  # Frequency
            header.extend([0, 0])  # Channel flags
        
        if fhss:
            present |= (1 << 4)  # FHSS field present
            header.extend(struct.pack('<H', fhss))
        
        if antenna_signal:
            present |= (1 << 5)  # Antenna signal field present
            header.append(antenna_signal & 0xFF)
        
        if antenna_noise:
            present |= (1 << 6)  # Antenna noise field present
            header.append(antenna_noise & 0xFF)
        
        if tx_power:
            present |= (1 << 10)  # dBm TX power field present
            header.append(tx_power & 0xFF)
        
        # Add MCS information (bit 19)
        if mcs_info:
            present |= (1 << 19)  # MCS field present
            header.append(mcs_info.get('known', 0))
            header.append(mcs_info.get('flags', 0))
            header.append(mcs_info.get('mcs', 0))
        
        # Add VHT information (bit 21)
        if vht_info:
            present |= (1 << 21)  # VHT field present
            header.extend(struct.pack('<H', vht_info.get('known', 0)))
            header.append(vht_info.get('flags', 0))
            header.append(vht_info.get('bandwidth', 0))
            # MCS/NSS for up to 4 users
            mcs_nss = vht_info.get('mcs_nss', [0, 0, 0, 0])
            for i in range(4):
                header.append(mcs_nss[i] if i < len(mcs_nss) else 0)
            header.append(vht_info.get('coding', 0))
            header.append(vht_info.get('group_id', 0))
            partial_aid = vht_info.get('partial_aid', 0)
            header.extend(struct.pack('<H', partial_aid))
        
        # Update length
        total_length = len(header)
        struct.pack_into('<H', header, length_pos, total_length)
        
        # Update present flags
        struct.pack_into('<L', header, present_pos, present)
        
        return bytes(header)
    
    def inject_packet(self, config: InjectionConfig, packet_data: bytes, 
                     radiotap_header: Optional[bytes] = None, 
                     rate_control: bool = True, timing_control: bool = False) -> Dict[str, any]:
        """Enhanced packet injection with advanced rate control and timing"""
        result = {
            "success": False,
            "interface": config.interface,
            "mode": config.mode.value,
            "packet_size": len(packet_data),
            "injection_attempts": 0,
            "successful_injections": 0,
            "rate_adaptations": 0,
            "timing_info": {},
            "errors": [],
            "warnings": []
        }
        
        injection_start_time = time.time()
        
        # Validate regulatory compliance
        compliance = self.validate_regulatory_compliance(config)
        if not compliance["compliant"]:
            result["errors"].extend(compliance["errors"])
            result["warnings"].extend(compliance["security_alerts"])
            return result
        
        # Add compliance warnings to result
        result["warnings"].extend(compliance["warnings"])
        result["warnings"].extend(compliance["security_alerts"])
        
        # Check interface is in monitor mode
        exit_code, stdout, stderr = self._run_command(["iw", "dev", config.interface, "info"])
        
        if exit_code != 0 or "type monitor" not in stdout:
            result["errors"].append(f"Interface {config.interface} not in monitor mode")
            return result
        
        # Rate control parameters
        current_rate = config.rate_mbps
        rate_fallback_levels = [54, 48, 36, 24, 18, 12, 9, 6, 1]  # Common rates in Mbps
        rate_attempts = {}
        
        try:
            # Create raw socket
            sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0003))
            
            # Get interface index
            exit_code, stdout, stderr = self._run_command(["cat", f"/sys/class/net/{config.interface}/ifindex"])
            
            if exit_code != 0:
                result["errors"].append(f"Could not get interface index for {config.interface}")
                return result
            
            if_index = int(stdout.strip())
            
            # Bind to interface
            sock.bind((config.interface, 0))
            
            # Injection loop with rate control
            for attempt in range(config.retry_count):
                result["injection_attempts"] += 1
                attempt_start_time = time.time()
                
                # Select rate for this attempt
                if rate_control and attempt > 0:
                    # Implement rate fallback
                    available_rates = [r for r in rate_fallback_levels if r <= config.rate_mbps]
                    if available_rates and attempt < len(available_rates):
                        current_rate = available_rates[min(attempt, len(available_rates) - 1)]
                        result["rate_adaptations"] += 1
                
                # Prepare packet with current rate
                if radiotap_header:
                    full_packet = radiotap_header + packet_data
                else:
                    # Generate enhanced radiotap header with current settings
                    radiotap_flags = 0x00  # Default flags
                    
                    # Add timing information if enabled
                    timestamp = int(time.time() * 1000000) if timing_control else 0
                    
                    # Determine MCS information for higher rates
                    mcs_info = None
                    if current_rate >= 6.5:  # MCS rates
                        mcs_info = {
                            "known": 0x07,  # MCS index, bandwidth, guard interval known
                            "flags": 0x00,  # 20MHz, long GI
                            "mcs": min(int((current_rate - 6.5) / 6.5), 7)  # Approximate MCS mapping
                        }
                    
                    radiotap_header = self.generate_radiotap_header(
                        flags=radiotap_flags,
                        rate=int(current_rate * 2) if current_rate <= 54 else 0,  # Legacy rates in 500kbps units
                        tx_power=config.power_dbm,
                        mcs_info=mcs_info,
                        timestamp=timestamp
                    )
                    full_packet = radiotap_header + packet_data
                
                # Record rate attempt
                rate_key = f"{current_rate}Mbps"
                rate_attempts[rate_key] = rate_attempts.get(rate_key, 0) + 1
                
                try:
                    # Timing control - precise inter-frame spacing
                    if timing_control and attempt > 0:
                        # Standard inter-frame spacing (SIFS = 16μs for 5GHz, 10μs for 2.4GHz)
                        sifs_delay = 0.000016  # 16 microseconds
                        time.sleep(sifs_delay)
                    
                    # Send packet
                    bytes_sent = sock.send(full_packet)
                    attempt_time = time.time() - attempt_start_time
                    
                    if bytes_sent == len(full_packet):
                        result["successful_injections"] += 1
                        result["success"] = True
                        result["bytes_sent"] = bytes_sent
                        result["final_rate_mbps"] = current_rate
                        result["timing_info"][f"attempt_{attempt + 1}"] = {
                            "duration_ms": round(attempt_time * 1000, 3),
                            "rate_mbps": current_rate,
                            "bytes_sent": bytes_sent
                        }
                        break
                    else:
                        result["errors"].append(f"Partial send: {bytes_sent}/{len(full_packet)} bytes")
                        result["timing_info"][f"attempt_{attempt + 1}"] = {
                            "duration_ms": round(attempt_time * 1000, 3),
                            "rate_mbps": current_rate,
                            "bytes_sent": bytes_sent,
                            "status": "partial"
                        }
                
                except Exception as e:
                    attempt_time = time.time() - attempt_start_time
                    result["errors"].append(f"Send attempt {attempt + 1} failed: {e}")
                    result["timing_info"][f"attempt_{attempt + 1}"] = {
                        "duration_ms": round(attempt_time * 1000, 3),
                        "rate_mbps": current_rate,
                        "status": "failed",
                        "error": str(e)
                    }
                
                # Adaptive delay between retries
                if attempt < config.retry_count - 1:
                    retry_delay = 0.01 * (attempt + 1)  # Increasing delay
                    time.sleep(retry_delay)
            
            sock.close()
            
            # Calculate overall timing statistics
            total_injection_time = time.time() - injection_start_time
            result["timing_info"]["total_duration_ms"] = round(total_injection_time * 1000, 3)
            result["timing_info"]["average_attempt_ms"] = round(
                (total_injection_time / result["injection_attempts"]) * 1000, 3
            ) if result["injection_attempts"] > 0 else 0
            
            # Add rate control statistics
            result["rate_control_stats"] = {
                "initial_rate_mbps": config.rate_mbps,
                "final_rate_mbps": current_rate,
                "rate_attempts": rate_attempts,
                "rate_adaptations": result["rate_adaptations"],
                "rate_control_enabled": rate_control
            }
            
            # Performance assessment
            success_rate = (result["successful_injections"] / result["injection_attempts"]) * 100
            result["performance_assessment"] = {
                "success_rate_percent": round(success_rate, 1),
                "efficiency": "HIGH" if success_rate >= 90 else "MEDIUM" if success_rate >= 70 else "LOW",
                "rate_stability": "STABLE" if result["rate_adaptations"] == 0 else "ADAPTIVE"
            }
            
        except Exception as e:
            result["errors"].append(f"Socket error: {e}")
        
        return result    

    def create_beacon_frame(self, ssid: str, channel: int, 
                           capabilities: int = 0x1104) -> bytes:
        """Create a basic beacon frame for injection testing"""
        # 802.11 Beacon frame structure
        frame = bytearray()
        
        # Frame Control (2 bytes) - Beacon frame
        frame.extend([0x80, 0x00])
        
        # Duration (2 bytes)
        frame.extend([0x00, 0x00])
        
        # Destination Address (6 bytes) - Broadcast
        frame.extend([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])
        
        # Source Address (6 bytes) - Example MAC
        frame.extend([0x02, 0x00, 0x00, 0x00, 0x00, 0x01])
        
        # BSSID (6 bytes) - Same as source
        frame.extend([0x02, 0x00, 0x00, 0x00, 0x00, 0x01])
        
        # Sequence Control (2 bytes)
        frame.extend([0x00, 0x00])
        
        # Fixed parameters (12 bytes)
        # Timestamp (8 bytes)
        timestamp = int(time.time() * 1000000) & 0xFFFFFFFFFFFFFFFF
        frame.extend(struct.pack('<Q', timestamp))
        
        # Beacon Interval (2 bytes) - 100 TU
        frame.extend([0x64, 0x00])
        
        # Capability Information (2 bytes)
        frame.extend(struct.pack('<H', capabilities))
        
        # Information Elements
        # SSID Element
        frame.append(0x00)  # Element ID
        frame.append(len(ssid))  # Length
        frame.extend(ssid.encode('utf-8'))
        
        # Supported Rates Element
        frame.append(0x01)  # Element ID
        frame.append(0x08)  # Length
        frame.extend([0x82, 0x84, 0x8B, 0x96, 0x0C, 0x12, 0x18, 0x24])
        
        # DS Parameter Set Element
        frame.append(0x03)  # Element ID
        frame.append(0x01)  # Length
        frame.append(channel)
        
        return bytes(frame)
    
    def create_probe_request(self, ssid: str = "") -> bytes:
        """Create a probe request frame for injection testing"""
        frame = bytearray()
        
        # Frame Control (2 bytes) - Probe Request
        frame.extend([0x40, 0x00])
        
        # Duration (2 bytes)
        frame.extend([0x00, 0x00])
        
        # Destination Address (6 bytes) - Broadcast
        frame.extend([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])
        
        # Source Address (6 bytes) - Example MAC
        frame.extend([0x02, 0x00, 0x00, 0x00, 0x00, 0x02])
        
        # BSSID (6 bytes) - Broadcast
        frame.extend([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])
        
        # Sequence Control (2 bytes)
        frame.extend([0x00, 0x00])
        
        # Information Elements
        # SSID Element
        frame.append(0x00)  # Element ID
        frame.append(len(ssid))  # Length
        if ssid:
            frame.extend(ssid.encode('utf-8'))
        
        # Supported Rates Element
        frame.append(0x01)  # Element ID
        frame.append(0x08)  # Length
        frame.extend([0x82, 0x84, 0x8B, 0x96, 0x0C, 0x12, 0x18, 0x24])
        
        return bytes(frame)
    
    def scan_channels(self, interface: str, channels: List[int], 
                     dwell_time: float = 0.1, channel_width: ChannelWidth = ChannelWidth.HT20,
                     regulatory_domain: str = "US") -> Dict[str, any]:
        """Enhanced channel scanning with regulatory compliance and advanced features"""
        result = {
            "success": False,
            "interface": interface,
            "channels_scanned": [],
            "channel_results": {},
            "regulatory_violations": [],
            "performance_metrics": {},
            "errors": []
        }
        
        # Check if interface is in monitor mode
        exit_code, stdout, stderr = self._run_command(["iw", "dev", interface, "info"])
        
        if exit_code != 0 or "type monitor" not in stdout:
            result["errors"].append(f"Interface {interface} not in monitor mode")
            return result
        
        # Validate regulatory compliance for all channels
        domain_rules = self.regulatory_domains.get(regulatory_domain, {})
        if not domain_rules:
            result["errors"].append(f"Unknown regulatory domain: {regulatory_domain}")
            return result
        
        start_time = time.time()
        successful_switches = 0
        
        try:
            for channel in channels:
                channel_start_time = time.time()
                
                # Calculate frequency from channel
                if 1 <= channel <= 14:
                    # 2.4 GHz
                    if channel == 14:
                        frequency = 2484
                    else:
                        frequency = 2407 + (channel * 5)
                    
                    # Check 2.4GHz regulatory compliance
                    if channel not in domain_rules.get("channels_2ghz", []):
                        result["regulatory_violations"].append(f"Channel {channel} not allowed in {regulatory_domain}")
                        result["channel_results"][channel] = {
                            "frequency": frequency,
                            "success": False,
                            "errors": [f"Regulatory violation: Channel {channel} not allowed"],
                            "regulatory_compliant": False
                        }
                        continue
                        
                elif channel >= 36:
                    # 5 GHz
                    frequency = 5000 + (channel * 5)
                    
                    # Check 5GHz regulatory compliance
                    if channel not in domain_rules.get("channels_5ghz", []):
                        result["regulatory_violations"].append(f"Channel {channel} not allowed in {regulatory_domain}")
                        result["channel_results"][channel] = {
                            "frequency": frequency,
                            "success": False,
                            "errors": [f"Regulatory violation: Channel {channel} not allowed"],
                            "regulatory_compliant": False
                        }
                        continue
                    
                    # Check DFS requirements
                    if channel in domain_rules.get("dfs_required", []):
                        result["channel_results"][channel] = result.get("channel_results", {}).get(channel, {})
                        result["channel_results"][channel]["dfs_required"] = True
                else:
                    result["errors"].append(f"Invalid channel: {channel}")
                    continue
                
                # Create channel config with enhanced features
                channel_config = ChannelConfig(
                    frequency=frequency,
                    channel=channel,
                    width=channel_width,
                    regulatory_domain=regulatory_domain
                )
                
                # Set channel with timing measurement
                channel_result = self.set_channel(interface, channel_config)
                channel_switch_time = time.time() - channel_start_time
                
                if channel_result["success"]:
                    result["channels_scanned"].append(channel)
                    result["channel_results"][channel] = {
                        "frequency": frequency,
                        "success": True,
                        "dwell_time": dwell_time,
                        "switch_time_ms": round(channel_switch_time * 1000, 2),
                        "regulatory_compliant": True,
                        "channel_width": channel_width.value,
                        "band": "2.4GHz" if channel <= 14 else "5GHz"
                    }
                    
                    successful_switches += 1
                    
                    # Dwell on channel
                    time.sleep(dwell_time)
                    
                    # Measure channel quality (simplified)
                    quality_metrics = self._measure_channel_quality(interface, channel)
                    result["channel_results"][channel].update(quality_metrics)
                    
                else:
                    result["channel_results"][channel] = {
                        "frequency": frequency,
                        "success": False,
                        "errors": channel_result.get("errors", []),
                        "switch_time_ms": round(channel_switch_time * 1000, 2),
                        "regulatory_compliant": True
                    }
                    result["errors"].extend(channel_result.get("errors", []))
            
            # Calculate performance metrics
            total_time = time.time() - start_time
            result["performance_metrics"] = {
                "total_scan_time_ms": round(total_time * 1000, 2),
                "successful_switches": successful_switches,
                "failed_switches": len(channels) - successful_switches,
                "average_switch_time_ms": round((total_time / len(channels)) * 1000, 2) if channels else 0,
                "channels_per_second": round(len(channels) / total_time, 2) if total_time > 0 else 0
            }
            
            result["success"] = len(result["channels_scanned"]) > 0
            
        except Exception as e:
            result["errors"].append(f"Channel scanning error: {e}")
        
        return result
    
    def _measure_channel_quality(self, interface: str, channel: int) -> Dict[str, any]:
        """Measure basic channel quality metrics"""
        quality = {
            "noise_floor_dbm": None,
            "channel_utilization": None,
            "interference_detected": False
        }
        
        try:
            # Try to get noise floor from driver (if supported)
            exit_code, stdout, stderr = self._run_command(["iw", "dev", interface, "survey", "dump"])
            
            if exit_code == 0:
                # Parse survey data for current channel
                lines = stdout.split('\n')
                in_channel = False
                
                for line in lines:
                    if f"frequency: {self._channel_to_frequency(channel)}" in line:
                        in_channel = True
                    elif line.startswith("Survey data from") and in_channel:
                        break
                    elif in_channel and "noise:" in line:
                        try:
                            noise_str = line.split("noise:")[1].strip().split()[0]
                            quality["noise_floor_dbm"] = int(noise_str)
                        except:
                            pass
                    elif in_channel and "channel active time:" in line:
                        # Could calculate utilization from active time
                        pass
            
        except Exception:
            pass  # Quality measurement is optional
        
        return quality
    
    def _channel_to_frequency(self, channel: int) -> int:
        """Convert channel number to frequency in MHz"""
        if 1 <= channel <= 14:
            if channel == 14:
                return 2484
            else:
                return 2407 + (channel * 5)
        elif channel >= 36:
            return 5000 + (channel * 5)
        else:
            return 0
    
    def generate_monitor_config(self, interface: str, channel: int, 
                              mode: MonitorMode = MonitorMode.PASSIVE,
                              regulatory_domain: str = "US") -> MonitorConfig:
        """Generate monitor configuration with regulatory compliance"""
        
        # Calculate frequency from channel
        if 1 <= channel <= 14:
            if channel == 14:
                frequency = 2484
            else:
                frequency = 2407 + (channel * 5)
        else:
            frequency = 5000 + (channel * 5)
        
        channel_config = ChannelConfig(
            frequency=frequency,
            channel=channel,
            width=ChannelWidth.HT20,
            regulatory_domain=regulatory_domain
        )
        
        return MonitorConfig(
            interface=interface,
            mode=mode,
            channel_config=channel_config,
            radiotap_enabled=True,
            fcs_enabled=True
        )
    
    def generate_injection_config(self, interface: str, mode: InjectionMode = InjectionMode.BEACON,
                                rate_mbps: float = 1.0, power_dbm: int = 15) -> InjectionConfig:
        """Generate injection configuration with safety limits"""
        
        # Apply safety limits
        safe_power = min(power_dbm, 20)  # Limit to 20dBm for safety
        safe_rate = max(0.5, min(rate_mbps, 54.0))  # Limit rate range
        
        return InjectionConfig(
            interface=interface,
            mode=mode,
            rate_mbps=safe_rate,
            power_dbm=safe_power,
            retry_count=3,
            sequence_control=True,
            timestamp_correction=True
        )
    
    def validate_driver_capabilities(self, interface: str, 
                                   required_capabilities: List[str]) -> Dict[str, any]:
        """Validate driver capabilities for monitor/injection operations"""
        result = {
            "interface": interface,
            "driver": "unknown",
            "supported_capabilities": {},
            "missing_capabilities": [],
            "warnings": [],
            "compatible": True
        }
        
        # Get driver information
        exit_code, stdout, stderr = self._run_command([
            "readlink", "-f", f"/sys/class/net/{interface}/device/driver"
        ])
        
        if exit_code == 0:
            driver_name = Path(stdout.strip()).name
            result["driver"] = driver_name
            
            if driver_name in self.driver_capabilities:
                driver_caps = self.driver_capabilities[driver_name]
                result["supported_capabilities"] = driver_caps.copy()
                
                # Check required capabilities
                for capability in required_capabilities:
                    if capability not in driver_caps or not driver_caps[capability]:
                        result["missing_capabilities"].append(capability)
                        result["compatible"] = False
                
                # Add driver-specific warnings
                if driver_name == "iwlwifi" and "packet_injection" in required_capabilities:
                    result["warnings"].append("iwlwifi has limited packet injection support")
                
                if driver_name == "rt2x00" and "spectral_scan" in required_capabilities:
                    result["warnings"].append("rt2x00 does not support spectral scanning")
            else:
                result["warnings"].append(f"Unknown driver: {driver_name}")
                result["compatible"] = False
        else:
            result["warnings"].append("Could not determine driver")
            result["compatible"] = False
        
        return result
    
    def create_security_report(self, interfaces: List[str]) -> Dict[str, any]:
        """Create comprehensive security and capability report"""
        report = {
            "timestamp": time.time(),
            "interfaces": {},
            "regulatory_compliance": {},
            "security_warnings": [],
            "recommendations": []
        }
        
        for interface in interfaces:
            # Get interface information
            interface_info = {
                "exists": False,
                "type": "unknown",
                "driver": "unknown",
                "capabilities": {},
                "monitor_ready": False,
                "injection_ready": False
            }
            
            # Check if interface exists
            exit_code, stdout, stderr = self._run_command(["ip", "link", "show", interface])
            
            if exit_code == 0:
                interface_info["exists"] = True
                
                # Get interface type
                exit_code2, stdout2, stderr2 = self._run_command(["iw", "dev", interface, "info"])
                
                if exit_code2 == 0:
                    for line in stdout2.split('\n'):
                        if 'type' in line:
                            interface_info["type"] = line.split()[-1]
                            break
                
                # Validate capabilities
                monitor_caps = self.validate_driver_capabilities(interface, ["monitor_mode", "radiotap"])
                injection_caps = self.validate_driver_capabilities(interface, ["packet_injection", "rate_control"])
                
                interface_info["driver"] = monitor_caps["driver"]
                interface_info["capabilities"] = monitor_caps["supported_capabilities"]
                interface_info["monitor_ready"] = monitor_caps["compatible"]
                interface_info["injection_ready"] = injection_caps["compatible"]
                
                # Add warnings
                report["security_warnings"].extend(monitor_caps.get("warnings", []))
                report["security_warnings"].extend(injection_caps.get("warnings", []))
            
            report["interfaces"][interface] = interface_info
        
        # Check regulatory compliance for common domains
        for domain in ["US", "EU", "JP"]:
            test_config = self.generate_monitor_config("test", 6, regulatory_domain=domain)
            compliance = self.validate_regulatory_compliance(test_config, domain)
            
            report["regulatory_compliance"][domain] = {
                "monitor_allowed": compliance["compliant"],
                "warnings": compliance.get("warnings", []),
                "restrictions": self.regulatory_domains.get(domain, {})
            }
        
        # Generate recommendations
        monitor_ready_count = sum(1 for info in report["interfaces"].values() if info["monitor_ready"])
        injection_ready_count = sum(1 for info in report["interfaces"].values() if info["injection_ready"])
        
        if monitor_ready_count == 0:
            report["recommendations"].append("No interfaces ready for monitor mode - check driver support")
        
        if injection_ready_count == 0:
            report["recommendations"].append("No interfaces ready for packet injection - consider ath10k or rt2x00")
        
        report["recommendations"].append("Always comply with local regulatory requirements")
        report["recommendations"].append("Use minimum necessary power levels")
        report["recommendations"].append("Monitor mode and injection should be used responsibly")
        
        return report
    
    def generate_kconfig_options(self) -> Dict[str, str]:
        """Generate kernel configuration options for monitor and security features"""
        config = {
            # Core monitor mode support
            "CONFIG_BACKPORTS_MONITOR_MODE": "y",
            "CONFIG_BACKPORTS_MONITOR_RADIOTAP": "y",
            "CONFIG_BACKPORTS_MONITOR_COOKED": "y",
            "CONFIG_BACKPORTS_MONITOR_TX_STATUS": "y",
            "CONFIG_BACKPORTS_MONITOR_CHANNEL_SWITCH": "y",
            
            # Packet injection support
            "CONFIG_BACKPORTS_FRAME_INJECTION": "y",
            "CONFIG_BACKPORTS_INJECTION_RATE_CONTROL": "y",
            "CONFIG_BACKPORTS_INJECTION_POWER_CONTROL": "y",
            "CONFIG_BACKPORTS_INJECTION_SEQUENCE_CONTROL": "y",
            "CONFIG_BACKPORTS_INJECTION_TIMESTAMP": "y",
            
            # Security and analysis features
            "CONFIG_BACKPORTS_WIRELESS_SECURITY_ENHANCED": "y",
            "CONFIG_BACKPORTS_WIRELESS_ANALYSIS": "y",
            "CONFIG_BACKPORTS_WIRELESS_FORENSICS": "y",
            "CONFIG_BACKPORTS_REGULATORY_COMPLIANCE": "y",
            "CONFIG_BACKPORTS_SECURITY_WARNINGS": "y",
            
            # Radiotap support
            "CONFIG_BACKPORTS_RADIOTAP_ENHANCED": "y",
            "CONFIG_BACKPORTS_RADIOTAP_VENDOR": "y",
            "CONFIG_BACKPORTS_RADIOTAP_MCS": "y",
            "CONFIG_BACKPORTS_RADIOTAP_VHT": "y",
            "CONFIG_BACKPORTS_RADIOTAP_HE": "y",
            
            # Channel switching and scanning
            "CONFIG_BACKPORTS_CHANNEL_SWITCH_ENHANCED": "y",
            "CONFIG_BACKPORTS_CHANNEL_SCAN_PASSIVE": "y",
            "CONFIG_BACKPORTS_CHANNEL_SCAN_ACTIVE": "y",
            "CONFIG_BACKPORTS_FREQUENCY_HOPPING": "y",
            
            # Driver-specific enhancements
            "CONFIG_BACKPORTS_ATH10K_MONITOR_ENHANCED": "y",
            "CONFIG_BACKPORTS_ATH11K_MONITOR_ENHANCED": "y",
            "CONFIG_BACKPORTS_RT2X00_MONITOR_ENHANCED": "y",
            "CONFIG_BACKPORTS_IWLWIFI_MONITOR_ENHANCED": "y",
            
            # Spectral scanning (where supported)
            "CONFIG_BACKPORTS_SPECTRAL_SCAN": "y",
            "CONFIG_BACKPORTS_ATH_SPECTRAL_ENHANCED": "y",
            
            # Debugging and diagnostics
            "CONFIG_BACKPORTS_MONITOR_DEBUG": "y",
            "CONFIG_BACKPORTS_INJECTION_DEBUG": "y",
            "CONFIG_BACKPORTS_SECURITY_DEBUG": "y",
            "CONFIG_BACKPORTS_REGULATORY_DEBUG": "y"
        }
        
        return config

def main():
    """Main function for testing"""
    manager = MonitorSecurityManager()
    
    print("Monitor Mode and Security Manager")
    print("=" * 50)
    
    # Detect wireless interfaces
    print("\\nDetecting wireless interfaces...")
    interfaces = manager.detect_wireless_interfaces()
    
    if interfaces:
        for iface in interfaces:
            print(f"  {iface['interface']}: {iface['type']} ({iface['driver']})")
            caps = iface['capabilities']
            if caps:
                print(f"    Monitor: {'✓' if caps.get('monitor_mode') else '✗'}")
                print(f"    Injection: {'✓' if caps.get('packet_injection') else '✗'}")
                print(f"    Channel Switch: {'✓' if caps.get('channel_switching') else '✗'}")
                print(f"    Radiotap: {'✓' if caps.get('radiotap') else '✗'}")
    else:
        print("  No wireless interfaces detected")
    
    # Test regulatory compliance
    print("\\nTesting regulatory compliance...")
    test_interface = interfaces[0]['interface'] if interfaces else "wlan0"
    
    # Test monitor config
    monitor_config = manager.generate_monitor_config(test_interface, 6, MonitorMode.PASSIVE)
    compliance = manager.validate_regulatory_compliance(monitor_config, "US")
    
    print(f"  Monitor mode (US): {'✓' if compliance['compliant'] else '✗'}")
    if compliance['warnings']:
        for warning in compliance['warnings']:
            print(f"    Warning: {warning}")
    
    # Test injection config
    injection_config = manager.generate_injection_config(test_interface, InjectionMode.BEACON)
    compliance = manager.validate_regulatory_compliance(injection_config, "EU")
    
    print(f"  Packet injection (EU): {'✓' if compliance['compliant'] else '✗'}")
    if compliance['errors']:
        for error in compliance['errors']:
            print(f"    Error: {error}")
    
    # Generate security report
    print("\\nGenerating security report...")
    if interfaces:
        interface_names = [iface['interface'] for iface in interfaces[:2]]  # Test first 2 interfaces
        security_report = manager.create_security_report(interface_names)
        
        print(f"  Interfaces analyzed: {len(security_report['interfaces'])}")
        print(f"  Security warnings: {len(security_report['security_warnings'])}")
        print(f"  Recommendations: {len(security_report['recommendations'])}")
        
        if security_report['recommendations']:
            print("\\n  Key recommendations:")
            for rec in security_report['recommendations'][:3]:
                print(f"    - {rec}")
    
    # Show configuration options
    print("\\nKernel configuration options:")
    config_options = manager.generate_kconfig_options()
    
    # Show first few options
    monitor_options = {k: v for k, v in config_options.items() if 'MONITOR' in k}
    for option, value in list(monitor_options.items())[:5]:
        print(f"  {option}={value}")
    
    if len(monitor_options) > 5:
        print(f"  ... and {len(monitor_options) - 5} more monitor options")
    
    injection_options = {k: v for k, v in config_options.items() if 'INJECTION' in k}
    for option, value in list(injection_options.items())[:3]:
        print(f"  {option}={value}")
    
    if len(injection_options) > 3:
        print(f"  ... and {len(injection_options) - 3} more injection options")

if __name__ == "__main__":
    main()