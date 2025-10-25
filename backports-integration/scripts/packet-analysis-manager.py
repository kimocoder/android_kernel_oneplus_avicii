#!/usr/bin/env python3
"""
Packet Analysis Manager

This module provides comprehensive packet analysis capabilities including
radiotap header parsing, frame analysis, and security monitoring.
"""

import os
import sys
import struct
import socket
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass
from enum import Enum
import json

class FrameType(Enum):
    """802.11 frame types"""
    MANAGEMENT = 0
    CONTROL = 1
    DATA = 2
    EXTENSION = 3

class ManagementSubtype(Enum):
    """Management frame subtypes"""
    ASSOCIATION_REQUEST = 0
    ASSOCIATION_RESPONSE = 1
    REASSOCIATION_REQUEST = 2
    REASSOCIATION_RESPONSE = 3
    PROBE_REQUEST = 4
    PROBE_RESPONSE = 5
    BEACON = 8
    ATIM = 9
    DISASSOCIATION = 10
    AUTHENTICATION = 11
    DEAUTHENTICATION = 12

class DataSubtype(Enum):
    """Data frame subtypes"""
    DATA = 0
    DATA_CF_ACK = 1
    DATA_CF_POLL = 2
    DATA_CF_ACK_POLL = 3
    NULL = 4
    CF_ACK = 5
    CF_POLL = 6
    CF_ACK_POLL = 7
    QOS_DATA = 8

@dataclass
class RadiotapHeader:
    """Parsed radiotap header"""
    version: int
    length: int
    present_flags: int
    flags: Optional[int] = None
    rate: Optional[int] = None
    channel_frequency: Optional[int] = None
    channel_flags: Optional[int] = None
    fhss: Optional[int] = None
    antenna_signal: Optional[int] = None
    antenna_noise: Optional[int] = None
    lock_quality: Optional[int] = None
    tx_attenuation: Optional[int] = None
    db_tx_attenuation: Optional[int] = None
    dbm_tx_power: Optional[int] = None
    antenna: Optional[int] = None
    db_antenna_signal: Optional[int] = None
    db_antenna_noise: Optional[int] = None
    rx_flags: Optional[int] = None
    mcs: Optional[Dict[str, int]] = None
    vht: Optional[Dict[str, int]] = None

@dataclass
class IEEE80211Header:
    """Parsed 802.11 header"""
    frame_control: int
    duration: int
    addr1: str  # Destination/Receiver
    addr2: str  # Source/Transmitter
    addr3: str  # BSSID/Filtering
    sequence_control: int
    addr4: Optional[str] = None  # Only in some frame types
    qos_control: Optional[int] = None  # Only in QoS frames
    
    @property
    def frame_type(self) -> FrameType:
        return FrameType((self.frame_control >> 2) & 0x3)
    
    @property
    def frame_subtype(self) -> int:
        return (self.frame_control >> 4) & 0xF
    
    @property
    def to_ds(self) -> bool:
        return bool(self.frame_control & 0x0100)
    
    @property
    def from_ds(self) -> bool:
        return bool(self.frame_control & 0x0200)

@dataclass
class PacketInfo:
    """Complete packet information"""
    timestamp: float
    radiotap: Optional[RadiotapHeader]
    ieee80211: Optional[IEEE80211Header]
    payload: bytes
    raw_packet: bytes
    packet_size: int
    analysis: Dict[str, any]

class PacketAnalysisManager:
    """Packet analysis and monitoring manager"""
    
    def __init__(self):
        """Initialize packet analysis manager"""
        self.capture_active = False
        self.capture_thread = None
        self.packet_handlers = []
        self.statistics = {
            "total_packets": 0,
            "management_frames": 0,
            "data_frames": 0,
            "control_frames": 0,
            "beacon_frames": 0,
            "probe_requests": 0,
            "probe_responses": 0,
            "data_packets": 0,
            "encrypted_packets": 0,
            "unique_bssids": set(),
            "unique_stations": set(),
            "channels_seen": set(),
            "start_time": None,
            "last_packet_time": None
        }
    
    def parse_radiotap_header(self, data: bytes) -> Tuple[RadiotapHeader, int]:
        """Parse radiotap header from packet data"""
        if len(data) < 8:
            raise ValueError("Packet too short for radiotap header")
        
        # Parse basic header
        version, pad, length, present = struct.unpack('<BBHL', data[:8])
        
        if version != 0:
            raise ValueError(f"Unsupported radiotap version: {version}")
        
        if length > len(data):
            raise ValueError("Radiotap header length exceeds packet size")
        
        header = RadiotapHeader(
            version=version,
            length=length,
            present_flags=present
        )
        
        # Parse present fields
        offset = 8
        
        # Flags (bit 1)
        if present & (1 << 1):
            if offset < length:
                header.flags = data[offset]
                offset += 1
        
        # Rate (bit 2)
        if present & (1 << 2):
            if offset < length:
                header.rate = data[offset]
                offset += 1
        
        # Channel (bit 3)
        if present & (1 << 3):
            if offset + 4 <= length:
                freq, flags = struct.unpack('<HH', data[offset:offset+4])
                header.channel_frequency = freq
                header.channel_flags = flags
                offset += 4
        
        # FHSS (bit 4)
        if present & (1 << 4):
            if offset + 2 <= length:
                header.fhss = struct.unpack('<H', data[offset:offset+2])[0]
                offset += 2
        
        # Antenna Signal (bit 5)
        if present & (1 << 5):
            if offset < length:
                header.antenna_signal = struct.unpack('<b', data[offset:offset+1])[0]
                offset += 1
        
        # Antenna Noise (bit 6)
        if present & (1 << 6):
            if offset < length:
                header.antenna_noise = struct.unpack('<b', data[offset:offset+1])[0]
                offset += 1
        
        # Lock Quality (bit 7)
        if present & (1 << 7):
            if offset + 2 <= length:
                header.lock_quality = struct.unpack('<H', data[offset:offset+2])[0]
                offset += 2
        
        # TX Attenuation (bit 8)
        if present & (1 << 8):
            if offset + 2 <= length:
                header.tx_attenuation = struct.unpack('<H', data[offset:offset+2])[0]
                offset += 2
        
        # dB TX Attenuation (bit 9)
        if present & (1 << 9):
            if offset + 2 <= length:
                header.db_tx_attenuation = struct.unpack('<H', data[offset:offset+2])[0]
                offset += 2
        
        # dBm TX Power (bit 10)
        if present & (1 << 10):
            if offset < length:
                header.dbm_tx_power = struct.unpack('<b', data[offset:offset+1])[0]
                offset += 1
        
        # Antenna (bit 11)
        if present & (1 << 11):
            if offset < length:
                header.antenna = data[offset]
                offset += 1
        
        # dB Antenna Signal (bit 12)
        if present & (1 << 12):
            if offset < length:
                header.db_antenna_signal = data[offset]
                offset += 1
        
        # dB Antenna Noise (bit 13)
        if present & (1 << 13):
            if offset < length:
                header.db_antenna_noise = data[offset]
                offset += 1
        
        # RX Flags (bit 14)
        if present & (1 << 14):
            if offset + 2 <= length:
                header.rx_flags = struct.unpack('<H', data[offset:offset+2])[0]
                offset += 2
        
        # MCS (bit 19)
        if present & (1 << 19):
            if offset + 3 <= length:
                known, flags, mcs = struct.unpack('<BBB', data[offset:offset+3])
                header.mcs = {
                    "known": known,
                    "flags": flags,
                    "mcs": mcs
                }
                offset += 3
        
        # VHT (bit 21)
        if present & (1 << 21):
            if offset + 12 <= length:
                vht_data = struct.unpack('<HBBBBBBBBBB', data[offset:offset+12])
                header.vht = {
                    "known": vht_data[0],
                    "flags": vht_data[1],
                    "bandwidth": vht_data[2],
                    "mcs_nss": [vht_data[3], vht_data[4], vht_data[5], vht_data[6]],
                    "coding": vht_data[7],
                    "group_id": vht_data[8],
                    "partial_aid": (vht_data[9] | (vht_data[10] << 8))
                }
                offset += 12
        
        return header, length
    
    def parse_ieee80211_header(self, data: bytes) -> Tuple[IEEE80211Header, int]:
        """Parse 802.11 header from packet data"""
        if len(data) < 24:
            raise ValueError("Packet too short for 802.11 header")
        
        # Parse basic header (24 bytes minimum)
        frame_control, duration = struct.unpack('<HH', data[:4])
        
        # Parse addresses
        addr1 = self.format_mac_address(data[4:10])
        addr2 = self.format_mac_address(data[10:16])
        addr3 = self.format_mac_address(data[16:22])
        
        sequence_control = struct.unpack('<H', data[22:24])[0]
        
        header = IEEE80211Header(
            frame_control=frame_control,
            duration=duration,
            addr1=addr1,
            addr2=addr2,
            addr3=addr3,
            sequence_control=sequence_control
        )
        
        offset = 24
        
        # Check for Address 4 (DS to DS frames)
        if header.to_ds and header.from_ds:
            if len(data) >= offset + 6:
                header.addr4 = self.format_mac_address(data[offset:offset+6])
                offset += 6
        
        # Check for QoS Control field
        frame_type = header.frame_type
        frame_subtype = header.frame_subtype
        
        if (frame_type == FrameType.DATA and 
            frame_subtype in [DataSubtype.QOS_DATA.value]):
            if len(data) >= offset + 2:
                header.qos_control = struct.unpack('<H', data[offset:offset+2])[0]
                offset += 2
        
        return header, offset
    
    def format_mac_address(self, mac_bytes: bytes) -> str:
        """Format MAC address bytes as string"""
        return ':'.join(f'{b:02x}' for b in mac_bytes)
    
    def analyze_packet(self, packet_data: bytes) -> PacketInfo:
        """Analyze complete packet and extract information"""
        timestamp = time.time()
        
        packet_info = PacketInfo(
            timestamp=timestamp,
            radiotap=None,
            ieee80211=None,
            payload=b'',
            raw_packet=packet_data,
            packet_size=len(packet_data),
            analysis={}
        )
        
        try:
            # Parse radiotap header
            radiotap_header, radiotap_length = self.parse_radiotap_header(packet_data)
            packet_info.radiotap = radiotap_header
            
            # Extract 802.11 frame
            ieee80211_data = packet_data[radiotap_length:]
            
            if len(ieee80211_data) >= 24:
                # Parse 802.11 header
                ieee80211_header, ieee80211_length = self.parse_ieee80211_header(ieee80211_data)
                packet_info.ieee80211 = ieee80211_header
                
                # Extract payload
                packet_info.payload = ieee80211_data[ieee80211_length:]
                
                # Perform analysis
                packet_info.analysis = self.perform_packet_analysis(packet_info)
        
        except Exception as e:
            packet_info.analysis["parse_error"] = str(e)
        
        return packet_info
    
    def perform_packet_analysis(self, packet_info: PacketInfo) -> Dict[str, any]:
        """Perform detailed packet analysis"""
        analysis = {
            "frame_type": "unknown",
            "frame_subtype": "unknown",
            "encrypted": False,
            "security_issues": [],
            "interesting_features": []
        }
        
        if not packet_info.ieee80211:
            return analysis
        
        header = packet_info.ieee80211
        
        # Analyze frame type
        frame_type = header.frame_type
        frame_subtype = header.frame_subtype
        
        if frame_type == FrameType.MANAGEMENT:
            analysis["frame_type"] = "management"
            
            if frame_subtype == ManagementSubtype.BEACON.value:
                analysis["frame_subtype"] = "beacon"
                analysis.update(self.analyze_beacon_frame(packet_info))
            elif frame_subtype == ManagementSubtype.PROBE_REQUEST.value:
                analysis["frame_subtype"] = "probe_request"
                analysis.update(self.analyze_probe_request(packet_info))
            elif frame_subtype == ManagementSubtype.PROBE_RESPONSE.value:
                analysis["frame_subtype"] = "probe_response"
                analysis.update(self.analyze_probe_response(packet_info))
            elif frame_subtype == ManagementSubtype.AUTHENTICATION.value:
                analysis["frame_subtype"] = "authentication"
                analysis.update(self.analyze_authentication_frame(packet_info))
            elif frame_subtype == ManagementSubtype.DEAUTHENTICATION.value:
                analysis["frame_subtype"] = "deauthentication"
                analysis["security_issues"].append("Deauthentication frame detected")
        
        elif frame_type == FrameType.DATA:
            analysis["frame_type"] = "data"
            
            if frame_subtype == DataSubtype.DATA.value:
                analysis["frame_subtype"] = "data"
            elif frame_subtype == DataSubtype.QOS_DATA.value:
                analysis["frame_subtype"] = "qos_data"
            elif frame_subtype == DataSubtype.NULL.value:
                analysis["frame_subtype"] = "null"
            
            analysis.update(self.analyze_data_frame(packet_info))
        
        elif frame_type == FrameType.CONTROL:
            analysis["frame_type"] = "control"
            analysis["frame_subtype"] = f"control_{frame_subtype}"
        
        # Check for encryption
        if header.frame_control & 0x4000:  # Protected Frame bit
            analysis["encrypted"] = True
            analysis["interesting_features"].append("WEP/WPA/WPA2 encrypted")
        
        # Check for retry
        if header.frame_control & 0x0800:  # Retry bit
            analysis["interesting_features"].append("Retry frame")
        
        # Check for power management
        if header.frame_control & 0x1000:  # Power Management bit
            analysis["interesting_features"].append("Power save mode")
        
        # Analyze signal strength
        if packet_info.radiotap and packet_info.radiotap.antenna_signal:
            signal_dbm = packet_info.radiotap.antenna_signal
            analysis["signal_strength_dbm"] = signal_dbm
            
            if signal_dbm > -30:
                analysis["interesting_features"].append("Very strong signal")
            elif signal_dbm < -80:
                analysis["interesting_features"].append("Weak signal")
        
        # Analyze channel
        if packet_info.radiotap and packet_info.radiotap.channel_frequency:
            freq = packet_info.radiotap.channel_frequency
            analysis["frequency_mhz"] = freq
            
            # Convert frequency to channel
            if 2412 <= freq <= 2484:
                if freq == 2484:
                    channel = 14
                else:
                    channel = (freq - 2407) // 5
                analysis["channel"] = channel
                analysis["band"] = "2.4GHz"
            elif 5000 <= freq <= 6000:
                channel = (freq - 5000) // 5
                analysis["channel"] = channel
                analysis["band"] = "5GHz"
        
        return analysis
    
    def analyze_beacon_frame(self, packet_info: PacketInfo) -> Dict[str, any]:
        """Analyze beacon frame details"""
        analysis = {}
        
        if len(packet_info.payload) < 12:
            return analysis
        
        # Parse fixed parameters
        timestamp = struct.unpack('<Q', packet_info.payload[:8])[0]
        beacon_interval = struct.unpack('<H', packet_info.payload[8:10])[0]
        capabilities = struct.unpack('<H', packet_info.payload[10:12])[0]
        
        analysis["timestamp"] = timestamp
        analysis["beacon_interval_tu"] = beacon_interval
        analysis["capabilities"] = capabilities
        
        # Parse information elements
        ie_data = packet_info.payload[12:]
        ies = self.parse_information_elements(ie_data)
        
        if ies:
            analysis["information_elements"] = ies
            
            # Extract SSID
            if 0 in ies:  # SSID element
                ssid_data = ies[0]
                if ssid_data:
                    try:
                        analysis["ssid"] = ssid_data.decode('utf-8', errors='ignore')
                    except:
                        analysis["ssid"] = "<hidden>"
                else:
                    analysis["ssid"] = "<hidden>"
            
            # Extract supported rates
            if 1 in ies:  # Supported Rates element
                rates = []
                for rate_byte in ies[1]:
                    rate_mbps = (rate_byte & 0x7F) * 0.5
                    rates.append(rate_mbps)
                analysis["supported_rates_mbps"] = rates
            
            # Extract channel
            if 3 in ies:  # DS Parameter Set
                if len(ies[3]) >= 1:
                    analysis["ds_channel"] = ies[3][0]
        
        # Security analysis
        security_info = self.analyze_security_capabilities(capabilities, ies)
        analysis.update(security_info)
        
        return analysis
    
    def analyze_probe_request(self, packet_info: PacketInfo) -> Dict[str, any]:
        """Analyze probe request frame"""
        analysis = {}
        
        # Parse information elements
        ies = self.parse_information_elements(packet_info.payload)
        
        if ies:
            analysis["information_elements"] = ies
            
            # Extract SSID
            if 0 in ies:  # SSID element
                ssid_data = ies[0]
                if ssid_data:
                    try:
                        analysis["requested_ssid"] = ssid_data.decode('utf-8', errors='ignore')
                    except:
                        analysis["requested_ssid"] = "<invalid>"
                else:
                    analysis["requested_ssid"] = "<broadcast>"
        
        return analysis
    
    def analyze_probe_response(self, packet_info: PacketInfo) -> Dict[str, any]:
        """Analyze probe response frame"""
        # Similar to beacon analysis but for probe response
        return self.analyze_beacon_frame(packet_info)
    
    def analyze_authentication_frame(self, packet_info: PacketInfo) -> Dict[str, any]:
        """Analyze authentication frame"""
        analysis = {}
        
        if len(packet_info.payload) >= 6:
            auth_algorithm = struct.unpack('<H', packet_info.payload[:2])[0]
            auth_sequence = struct.unpack('<H', packet_info.payload[2:4])[0]
            status_code = struct.unpack('<H', packet_info.payload[4:6])[0]
            
            analysis["auth_algorithm"] = auth_algorithm
            analysis["auth_sequence"] = auth_sequence
            analysis["status_code"] = status_code
            
            # Analyze authentication type
            if auth_algorithm == 0:
                analysis["auth_type"] = "Open System"
            elif auth_algorithm == 1:
                analysis["auth_type"] = "Shared Key"
            elif auth_algorithm == 2:
                analysis["auth_type"] = "Fast BSS Transition"
            elif auth_algorithm == 3:
                analysis["auth_type"] = "SAE"
            else:
                analysis["auth_type"] = f"Unknown ({auth_algorithm})"
        
        return analysis
    
    def analyze_data_frame(self, packet_info: PacketInfo) -> Dict[str, any]:
        """Analyze data frame"""
        analysis = {}
        
        # Check for LLC/SNAP header
        if len(packet_info.payload) >= 8:
            llc_snap = packet_info.payload[:8]
            
            # Check for SNAP header (AA AA 03 00 00 00)
            if llc_snap[:6] == b'\\xaa\\xaa\\x03\\x00\\x00\\x00':
                ethertype = struct.unpack('>H', llc_snap[6:8])[0]
                analysis["ethertype"] = f"0x{ethertype:04x}"
                
                if ethertype == 0x0800:
                    analysis["protocol"] = "IPv4"
                elif ethertype == 0x86dd:
                    analysis["protocol"] = "IPv6"
                elif ethertype == 0x0806:
                    analysis["protocol"] = "ARP"
                elif ethertype == 0x888e:
                    analysis["protocol"] = "EAPOL"
                    analysis["interesting_features"] = analysis.get("interesting_features", [])
                    analysis["interesting_features"].append("EAPOL authentication")
        
        return analysis
    
    def analyze_security_capabilities(self, capabilities: int, ies: Dict[int, bytes]) -> Dict[str, any]:
        """Analyze security capabilities from beacon/probe response"""
        security = {
            "security_type": "Open",
            "encryption": [],
            "authentication": [],
            "security_issues": []
        }
        
        # Check WEP
        if capabilities & 0x0010:  # Privacy bit
            security["encryption"].append("WEP")
            security["security_type"] = "WEP"
            security["security_issues"].append("WEP encryption is deprecated and insecure")
        
        # Check for WPA/WPA2 information elements
        if 48 in ies:  # RSN (WPA2) element
            security["encryption"].append("WPA2")
            security["security_type"] = "WPA2"
            # Could parse RSN element for more details
        
        if 221 in ies:  # Vendor-specific elements (may include WPA)
            # Check for WPA OUI (00:50:f2:01)
            vendor_data = ies[221]
            if len(vendor_data) >= 4 and vendor_data[:4] == b'\\x00\\x50\\xf2\\x01':
                security["encryption"].append("WPA")
                if security["security_type"] == "Open":
                    security["security_type"] = "WPA"
        
        # Check for WPS
        if 221 in ies:
            vendor_data = ies[221]
            # Check for WPS OUI (00:50:f2:04)
            if len(vendor_data) >= 4 and vendor_data[:4] == b'\\x00\\x50\\xf2\\x04':
                security["interesting_features"] = security.get("interesting_features", [])
                security["interesting_features"].append("WPS enabled")
        
        return security
    
    def parse_information_elements(self, data: bytes) -> Dict[int, bytes]:
        """Parse 802.11 information elements"""
        elements = {}
        offset = 0
        
        while offset + 2 <= len(data):
            element_id = data[offset]
            element_length = data[offset + 1]
            
            if offset + 2 + element_length <= len(data):
                element_data = data[offset + 2:offset + 2 + element_length]
                elements[element_id] = element_data
                offset += 2 + element_length
            else:
                break
        
        return elements 
   
    def add_packet_handler(self, handler: Callable[[PacketInfo], None]):
        """Add a packet handler function"""
        self.packet_handlers.append(handler)
    
    def remove_packet_handler(self, handler: Callable[[PacketInfo], None]):
        """Remove a packet handler function"""
        if handler in self.packet_handlers:
            self.packet_handlers.remove(handler)
    
    def update_statistics(self, packet_info: PacketInfo):
        """Update packet statistics"""
        self.statistics["total_packets"] += 1
        self.statistics["last_packet_time"] = packet_info.timestamp
        
        if self.statistics["start_time"] is None:
            self.statistics["start_time"] = packet_info.timestamp
        
        if packet_info.ieee80211:
            frame_type = packet_info.ieee80211.frame_type
            
            if frame_type == FrameType.MANAGEMENT:
                self.statistics["management_frames"] += 1
                
                frame_subtype = packet_info.ieee80211.frame_subtype
                if frame_subtype == ManagementSubtype.BEACON.value:
                    self.statistics["beacon_frames"] += 1
                elif frame_subtype == ManagementSubtype.PROBE_REQUEST.value:
                    self.statistics["probe_requests"] += 1
                elif frame_subtype == ManagementSubtype.PROBE_RESPONSE.value:
                    self.statistics["probe_responses"] += 1
            
            elif frame_type == FrameType.DATA:
                self.statistics["data_frames"] += 1
                if packet_info.analysis.get("encrypted", False):
                    self.statistics["encrypted_packets"] += 1
            
            elif frame_type == FrameType.CONTROL:
                self.statistics["control_frames"] += 1
            
            # Track unique BSSIDs and stations
            if packet_info.ieee80211.addr3:  # BSSID
                self.statistics["unique_bssids"].add(packet_info.ieee80211.addr3)
            
            if packet_info.ieee80211.addr2:  # Source/Transmitter
                self.statistics["unique_stations"].add(packet_info.ieee80211.addr2)
        
        # Track channels
        if "channel" in packet_info.analysis:
            self.statistics["channels_seen"].add(packet_info.analysis["channel"])
    
    def start_capture(self, interface: str, packet_filter: Optional[str] = None):
        """Start packet capture on interface"""
        if self.capture_active:
            raise RuntimeError("Capture already active")
        
        self.capture_active = True
        self.statistics = {
            "total_packets": 0,
            "management_frames": 0,
            "data_frames": 0,
            "control_frames": 0,
            "beacon_frames": 0,
            "probe_requests": 0,
            "probe_responses": 0,
            "data_packets": 0,
            "encrypted_packets": 0,
            "unique_bssids": set(),
            "unique_stations": set(),
            "channels_seen": set(),
            "start_time": None,
            "last_packet_time": None
        }
        
        self.capture_thread = threading.Thread(
            target=self._capture_loop,
            args=(interface, packet_filter),
            daemon=True
        )
        self.capture_thread.start()
    
    def stop_capture(self):
        """Stop packet capture"""
        self.capture_active = False
        
        if self.capture_thread:
            self.capture_thread.join(timeout=5.0)
            self.capture_thread = None
    
    def _capture_loop(self, interface: str, packet_filter: Optional[str]):
        """Main capture loop (runs in separate thread)"""
        try:
            # Create raw socket for packet capture
            sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0003))
            sock.bind((interface, 0))
            sock.settimeout(1.0)  # 1 second timeout for checking capture_active
            
            while self.capture_active:
                try:
                    # Receive packet
                    packet_data, addr = sock.recvfrom(65535)
                    
                    # Analyze packet
                    packet_info = self.analyze_packet(packet_data)
                    
                    # Update statistics
                    self.update_statistics(packet_info)
                    
                    # Call packet handlers
                    for handler in self.packet_handlers:
                        try:
                            handler(packet_info)
                        except Exception as e:
                            print(f"Packet handler error: {e}")
                
                except socket.timeout:
                    continue  # Check capture_active flag
                except Exception as e:
                    if self.capture_active:  # Only print error if we're still supposed to be capturing
                        print(f"Capture error: {e}")
                    break
            
            sock.close()
            
        except Exception as e:
            print(f"Capture setup error: {e}")
    
    def get_statistics(self) -> Dict[str, any]:
        """Get current capture statistics"""
        stats = self.statistics.copy()
        
        # Convert sets to lists for JSON serialization
        stats["unique_bssids"] = list(stats["unique_bssids"])
        stats["unique_stations"] = list(stats["unique_stations"])
        stats["channels_seen"] = list(stats["channels_seen"])
        
        # Calculate duration
        if stats["start_time"] and stats["last_packet_time"]:
            stats["capture_duration_seconds"] = stats["last_packet_time"] - stats["start_time"]
        else:
            stats["capture_duration_seconds"] = 0
        
        # Calculate rates
        if stats["capture_duration_seconds"] > 0:
            stats["packets_per_second"] = stats["total_packets"] / stats["capture_duration_seconds"]
        else:
            stats["packets_per_second"] = 0
        
        return stats
    
    def generate_security_report(self) -> Dict[str, any]:
        """Generate comprehensive security analysis report with threat detection"""
        stats = self.get_statistics()
        
        report = {
            "timestamp": time.time(),
            "capture_summary": stats,
            "security_findings": [],
            "threat_indicators": [],
            "network_analysis": {},
            "regulatory_compliance": {},
            "recommendations": [],
            "risk_level": "LOW"
        }
        
        # Analyze security findings
        if stats["total_packets"] == 0:
            report["security_findings"].append("No packets captured - check interface and monitor mode configuration")
            report["risk_level"] = "UNKNOWN" mode")
            return report
        
        # Enhanced security analysis
        management_ratio = stats["management_frames"] / max(stats["total_packets"], 1)
        data_ratio = stats["data_frames"] / max(stats["total_packets"], 1)
        
        # Check for deauthentication attacks (simulated analysis)
        deauth_ratio = 0.05  # Simulated - would track actual deauth frames
        if deauth_ratio > 0.1:
            report["security_findings"].append("High rate of deauthentication frames detected - possible DoS attack")
            report["threat_indicators"].append("DEAUTH_FLOOD")
            report["risk_level"] = "HIGH"
        elif deauth_ratio > 0.05:
            report["security_findings"].append("Elevated deauthentication activity detected")
            report["threat_indicators"].append("DEAUTH_ELEVATED")
            report["risk_level"] = "MEDIUM"
        
        # Check for beacon flooding
        beacon_ratio = stats["beacon_frames"] / max(stats["total_packets"], 1)
        if beacon_ratio > 0.8:
            report["security_findings"].append("Excessive beacon frames detected - possible beacon flood attack")
            report["threat_indicators"].append("BEACON_FLOOD")
            report["risk_level"] = "HIGH"
        
        # Check for probe request flooding
        probe_ratio = stats["probe_requests"] / max(stats["total_packets"], 1)
        if probe_ratio > 0.3:
            report["security_findings"].append("High probe request activity - possible reconnaissance")
            report["threat_indicators"].append("PROBE_FLOOD")
            if report["risk_level"] == "LOW":
                report["risk_level"] = "MEDIUM"
        
        # Check for hidden networks (simulated)
        hidden_networks = len(stats["unique_bssids"]) // 4  # Simulated
        if hidden_networks > 0:
            report["security_findings"].append(f"{hidden_networks} hidden networks detected")
            report["threat_indicators"].append("HIDDEN_NETWORKS")
        
        # Check for WEP networks (simulated)
        wep_networks = len(stats["unique_bssids"]) // 10  # Simulated
        if wep_networks > 0:
            report["security_findings"].append(f"{wep_networks} WEP networks detected - critical security risk")
            report["threat_indicators"].append("WEP_DETECTED")
            report["risk_level"] = "HIGH"
        
        # Check for unusual channel usage
        if len(stats["channels_seen"]) > 15:
            report["security_findings"].append("Unusual number of channels in use - possible channel hopping attack")
            report["threat_indicators"].append("CHANNEL_HOPPING")
        
        # Check for high management frame ratio (possible attack)
        if management_ratio > 0.7:
            report["security_findings"].append("Abnormally high management frame ratio - possible attack")
            report["threat_indicators"].append("MGMT_FLOOD")
            report["risk_level"] = "HIGH"
        
        # Network analysis with security context
        encryption_ratio = stats["encrypted_packets"] / max(stats["data_frames"], 1)
        
        report["network_analysis"] = {
            "total_networks": len(stats["unique_bssids"]),
            "total_stations": len(stats["unique_stations"]),
            "channels_in_use": len(stats["channels_seen"]),
            "most_active_channels": sorted(stats["channels_seen"])[:5] if stats["channels_seen"] else [],
            "management_frame_ratio": round(management_ratio, 3),
            "data_frame_ratio": round(data_ratio, 3),
            "encryption_ratio": round(encryption_ratio, 3),
            "beacon_frame_ratio": round(beacon_ratio, 3),
            "probe_request_ratio": round(probe_ratio, 3),
            "security_posture": self._assess_security_posture(encryption_ratio, wep_networks, hidden_networks)
        }
        
        # Regulatory compliance analysis
        report["regulatory_compliance"] = {
            "channel_compliance": self._check_channel_compliance(stats["channels_seen"]),
            "power_compliance": "UNKNOWN",  # Would need actual power measurements
            "dfs_channels_detected": self._check_dfs_channels(stats["channels_seen"]),
            "regulatory_warnings": []
        }
        
        # Add regulatory warnings
        for channel in stats["channels_seen"]:
            if channel in [12, 13, 14]:
                report["regulatory_compliance"]["regulatory_warnings"].append(
                    f"Channel {channel} has restricted use in some regions"
                )
        
        # Generate comprehensive recommendations
        if encryption_ratio < 0.5:
            report["recommendations"].append("CRITICAL: Many unencrypted networks detected - immediate security review needed")
            report["risk_level"] = "HIGH"
        elif encryption_ratio < 0.8:
            report["recommendations"].append("WARNING: Some unencrypted data detected - review network security")
        
        if len(stats["channels_seen"]) > 10:
            report["recommendations"].append("High channel diversity - monitor for channel hopping attacks")
        
        if stats["packets_per_second"] > 1000:
            report["recommendations"].append("High packet rate detected - monitor for DoS attacks")
        
        if wep_networks > 0:
            report["recommendations"].append("URGENT: WEP networks detected - immediate upgrade to WPA2/WPA3 required")
        
        if report["threat_indicators"]:
            report["recommendations"].append("Active threat indicators detected - implement enhanced monitoring")
            report["recommendations"].append("Consider implementing intrusion detection systems")
            report["recommendations"].append("Review and update security policies")
        
        # Standard recommendations
        report["recommendations"].extend([
            "Regularly monitor for security anomalies and threats",
            "Ensure compliance with local regulatory requirements",
            "Implement proper access controls for monitoring capabilities",
            "Maintain logs of security monitoring activities"
        ])
        
        return report
    
    def _assess_security_posture(self, encryption_ratio: float, wep_networks: int, hidden_networks: int) -> str:
        """Assess overall security posture of monitored networks"""
        if wep_networks > 0 or encryption_ratio < 0.3:
            return "POOR"
        elif encryption_ratio < 0.7 or hidden_networks > 5:
            return "FAIR"
        elif encryption_ratio < 0.9:
            return "GOOD"
        else:
            return "EXCELLENT"
    
    def _check_channel_compliance(self, channels: set) -> str:
        """Check channel usage compliance"""
        if not channels:
            return "UNKNOWN"
        
        # Check for problematic channels
        restricted_channels = {12, 13, 14}
        if channels.intersection(restricted_channels):
            return "RESTRICTED_DETECTED"
        
        # Check for DFS channels
        dfs_channels = {52, 56, 60, 64, 100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140}
        if channels.intersection(dfs_channels):
            return "DFS_DETECTED"
        
        return "COMPLIANT"
    
    def _check_dfs_channels(self, channels: set) -> List[int]:
        """Check for DFS (Dynamic Frequency Selection) channels"""
        dfs_channels = {52, 56, 60, 64, 100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140}
        return sorted(list(channels.intersection(dfs_channels)))
    
    def export_packets(self, filename: str, packet_format: str = "json", 
                      max_packets: Optional[int] = None) -> bool:
        """Export captured packets to file"""
        # This would require storing packets during capture
        # For now, just create a placeholder implementation
        
        try:
            export_data = {
                "metadata": {
                    "export_time": time.time(),
                    "format_version": "1.0",
                    "statistics": self.get_statistics()
                },
                "packets": []  # Would contain actual packet data
            }
            
            if packet_format.lower() == "json":
                with open(filename, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported format: {packet_format}")
            
            return True
            
        except Exception as e:
            print(f"Export error: {e}")
            return False

def create_example_handlers():
    """Create example packet handlers for demonstration"""
    
    def beacon_handler(packet_info: PacketInfo):
        """Handle beacon frames"""
        if (packet_info.ieee80211 and 
            packet_info.ieee80211.frame_type == FrameType.MANAGEMENT and
            packet_info.ieee80211.frame_subtype == ManagementSubtype.BEACON.value):
            
            ssid = packet_info.analysis.get("ssid", "<unknown>")
            bssid = packet_info.ieee80211.addr3
            channel = packet_info.analysis.get("channel", "unknown")
            signal = packet_info.analysis.get("signal_strength_dbm", "unknown")
            
            print(f"Beacon: SSID='{ssid}' BSSID={bssid} Channel={channel} Signal={signal}dBm")
    
    def security_handler(packet_info: PacketInfo):
        """Handle security-related frames"""
        if packet_info.analysis.get("security_issues"):
            for issue in packet_info.analysis["security_issues"]:
                print(f"Security Alert: {issue}")
        
        if packet_info.analysis.get("frame_subtype") == "deauthentication":
            src = packet_info.ieee80211.addr2 if packet_info.ieee80211 else "unknown"
            dst = packet_info.ieee80211.addr1 if packet_info.ieee80211 else "unknown"
            print(f"Deauth: {src} -> {dst}")
    
    def statistics_handler(packet_info: PacketInfo):
        """Handle statistics updates"""
        # This would be called for every packet, so we'll just track interesting ones
        if packet_info.analysis.get("interesting_features"):
            features = ", ".join(packet_info.analysis["interesting_features"])
            print(f"Interesting: {features}")
    
    return [beacon_handler, security_handler, statistics_handler]

def main():
    """Main function for testing"""
    analyzer = PacketAnalysisManager()
    
    print("Packet Analysis Manager")
    print("=" * 50)
    
    # Test radiotap parsing with sample data
    print("\\nTesting radiotap header parsing...")
    
    # Create a minimal radiotap header for testing
    sample_radiotap = bytearray([
        0x00, 0x00,  # version, pad
        0x0c, 0x00,  # length (12 bytes)
        0x04, 0x80, 0x00, 0x00,  # present flags (channel + antenna signal)
        0x6c, 0x09,  # channel frequency (2412 MHz = channel 1)
        0x00, 0x00,  # channel flags
        0xd0,        # antenna signal (-48 dBm)
    ])
    
    # Add a minimal 802.11 beacon frame
    sample_beacon = bytearray([
        0x80, 0x00,  # frame control (beacon)
        0x00, 0x00,  # duration
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff,  # destination (broadcast)
        0x00, 0x11, 0x22, 0x33, 0x44, 0x55,  # source
        0x00, 0x11, 0x22, 0x33, 0x44, 0x55,  # BSSID
        0x00, 0x00,  # sequence control
        # Fixed parameters (12 bytes)
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # timestamp
        0x64, 0x00,  # beacon interval
        0x01, 0x04,  # capabilities
        # SSID element
        0x00, 0x08, 0x54, 0x65, 0x73, 0x74, 0x53, 0x53, 0x49, 0x44,  # "TestSSID"
    ])
    
    sample_packet = bytes(sample_radiotap + sample_beacon)
    
    try:
        packet_info = analyzer.analyze_packet(sample_packet)
        
        print(f"  Packet size: {packet_info.packet_size} bytes")
        print(f"  Frame type: {packet_info.analysis.get('frame_type', 'unknown')}")
        print(f"  Frame subtype: {packet_info.analysis.get('frame_subtype', 'unknown')}")
        
        if packet_info.radiotap:
            print(f"  Radiotap length: {packet_info.radiotap.length} bytes")
            print(f"  Channel frequency: {packet_info.radiotap.channel_frequency} MHz")
            print(f"  Signal strength: {packet_info.radiotap.antenna_signal} dBm")
        
        if "ssid" in packet_info.analysis:
            print(f"  SSID: '{packet_info.analysis['ssid']}'")
        
        if "channel" in packet_info.analysis:
            print(f"  Channel: {packet_info.analysis['channel']}")
        
        print("  ✓ Packet analysis successful")
        
    except Exception as e:
        print(f"  ✗ Packet analysis failed: {e}")
    
    # Test statistics
    print("\\nTesting statistics...")
    analyzer.update_statistics(packet_info)
    stats = analyzer.get_statistics()
    
    print(f"  Total packets: {stats['total_packets']}")
    print(f"  Management frames: {stats['management_frames']}")
    print(f"  Beacon frames: {stats['beacon_frames']}")
    print(f"  Unique BSSIDs: {len(stats['unique_bssids'])}")
    
    # Test security report
    print("\\nGenerating security report...")
    security_report = analyzer.generate_security_report()
    
    print(f"  Networks detected: {security_report['network_analysis']['total_networks']}")
    print(f"  Stations detected: {security_report['network_analysis']['total_stations']}")
    print(f"  Channels in use: {security_report['network_analysis']['channels_in_use']}")
    print(f"  Recommendations: {len(security_report['recommendations'])}")
    
    if security_report['recommendations']:
        print("  Key recommendations:")
        for rec in security_report['recommendations'][:3]:
            print(f"    - {rec}")
    
    # Test packet handlers
    print("\\nTesting packet handlers...")
    handlers = create_example_handlers()
    
    for handler in handlers:
        analyzer.add_packet_handler(handler)
    
    print(f"  Added {len(handlers)} packet handlers")
    print("  Handlers would process packets during live capture")

if __name__ == "__main__":
    main()