#!/usr/bin/env python3
"""
Security and Monitor Mode Configurator

This script provides a comprehensive interface for configuring and managing
security and monitor mode capabilities including regulatory compliance,
packet injection, and advanced monitoring features.
"""

import os
import sys
import json
import argparse
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add the scripts directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from monitor_security_manager import (
        MonitorSecurityManager, MonitorConfig, InjectionConfig, 
        ChannelConfig, MonitorMode, InjectionMode, ChannelWidth
    )
    from packet_analysis_manager import PacketAnalysisManager
except ImportError as e:
    print(f"Error: Could not import required modules: {e}")
    print("Please ensure monitor_security_manager.py and packet_analysis_manager.py are available")
    sys.exit(1)

class SecurityMonitorConfigurator:
    """Comprehensive security and monitor mode configurator"""
    
    def __init__(self):
        """Initialize the configurator"""
        self.monitor_manager = MonitorSecurityManager()
        self.packet_analyzer = PacketAnalysisManager()
        self.config_file = Path(__file__).parent.parent / "configs" / "security-monitor-runtime.json"
        
        # Default configuration
        self.default_config = {
            "regulatory_domain": "US",
            "monitor_mode": {
                "enabled": True,
                "mode": "passive",
                "radiotap": True,
                "channel_switching": True
            },
            "packet_injection": {
                "enabled": False,
                "rate_control": True,
                "power_control": True,
                "regulatory_check": True
            },
            "security_monitoring": {
                "threat_detection": True,
                "compliance_checking": True,
                "logging": True
            },
            "channels": {
                "2ghz": [1, 6, 11],
                "5ghz": [36, 40, 44, 48, 149, 153, 157, 161]
            }
        }
    
    def load_configuration(self) -> Dict:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load configuration: {e}")
        
        return self.default_config.copy()
    
    def save_configuration(self, config: Dict) -> bool:
        """Save configuration to file"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error: Could not save configuration: {e}")
            return False
    
    def detect_interfaces(self) -> List[Dict]:
        """Detect and analyze wireless interfaces"""
        print("Detecting wireless interfaces...")
        interfaces = self.monitor_manager.detect_wireless_interfaces()
        
        if not interfaces:
            print("No wireless interfaces detected")
            return []
        
        print(f"Found {len(interfaces)} wireless interface(s):")
        for i, iface in enumerate(interfaces, 1):
            print(f"  {i}. {iface['interface']} ({iface['driver']}) - {iface['type']}")
            
            caps = iface.get('capabilities', {})
            if caps:
                print(f"     Monitor: {'✓' if caps.get('monitor_mode') else '✗'}")
                print(f"     Injection: {'✓' if caps.get('packet_injection') else '✗'}")
                print(f"     Channel Switch: {'✓' if caps.get('channel_switching') else '✗'}")
                print(f"     Radiotap: {'✓' if caps.get('radiotap') else '✗'}")
        
        return interfaces
    
    def configure_monitor_mode(self, interface: str, channel: int, 
                             regulatory_domain: str = "US") -> Dict:
        """Configure monitor mode for an interface"""
        print(f"Configuring monitor mode on {interface}, channel {channel}...")
        
        # Generate monitor configuration
        monitor_config = self.monitor_manager.generate_monitor_config(
            interface, channel, MonitorMode.PASSIVE, regulatory_domain
        )
        
        # Validate regulatory compliance
        compliance = self.monitor_manager.validate_regulatory_compliance(
            monitor_config, regulatory_domain
        )
        
        if not compliance["compliant"]:
            print("❌ Regulatory compliance check failed:")
            for error in compliance["errors"]:
                print(f"   Error: {error}")
            for alert in compliance.get("security_alerts", []):
                print(f"   Alert: {alert}")
            return {"success": False, "compliance": compliance}
        
        # Show warnings if any
        if compliance["warnings"] or compliance.get("security_alerts"):
            print("⚠️  Compliance warnings:")
            for warning in compliance["warnings"]:
                print(f"   Warning: {warning}")
            for alert in compliance.get("security_alerts", []):
                print(f"   Alert: {alert}")
        
        # Configure monitor mode
        result = self.monitor_manager.configure_monitor_mode(monitor_config)
        
        if result["success"]:
            print("✅ Monitor mode configured successfully")
            print(f"   Interface: {result['interface']}")
            print(f"   Mode: {result['mode']}")
            print(f"   Channel: {result['channel']}")
        else:
            print("❌ Monitor mode configuration failed:")
            for error in result["errors"]:
                print(f"   Error: {error}")
        
        result["compliance"] = compliance
        return result
    
    def test_packet_injection(self, interface: str, regulatory_domain: str = "US") -> Dict:
        """Test packet injection capabilities"""
        print(f"Testing packet injection on {interface}...")
        
        # Generate injection configuration
        injection_config = self.monitor_manager.generate_injection_config(
            interface, InjectionMode.BEACON, rate_mbps=1.0, power_dbm=15
        )
        
        # Validate regulatory compliance
        compliance = self.monitor_manager.validate_regulatory_compliance(
            injection_config, regulatory_domain
        )
        
        if not compliance["compliant"]:
            print("❌ Packet injection not allowed:")
            for error in compliance["errors"]:
                print(f"   Error: {error}")
            return {"success": False, "compliance": compliance}
        
        # Show warnings
        if compliance["warnings"] or compliance.get("security_alerts"):
            print("⚠️  Injection warnings:")
            for warning in compliance["warnings"]:
                print(f"   Warning: {warning}")
            for alert in compliance.get("security_alerts", []):
                print(f"   Alert: {alert}")
        
        # Create test beacon frame
        test_beacon = self.monitor_manager.create_beacon_frame("TEST_SSID", 6)
        
        # Inject test packet
        result = self.monitor_manager.inject_packet(
            injection_config, test_beacon, rate_control=True
        )
        
        if result["success"]:
            print("✅ Packet injection test successful")
            print(f"   Attempts: {result['injection_attempts']}")
            print(f"   Success Rate: {result['performance_assessment']['success_rate_percent']}%")
            print(f"   Final Rate: {result.get('final_rate_mbps', 'N/A')} Mbps")
        else:
            print("❌ Packet injection test failed:")
            for error in result["errors"]:
                print(f"   Error: {error}")
        
        result["compliance"] = compliance
        return result
    
    def scan_channels(self, interface: str, channels: List[int], 
                     regulatory_domain: str = "US") -> Dict:
        """Perform channel scanning"""
        print(f"Scanning channels {channels} on {interface}...")
        
        result = self.monitor_manager.scan_channels(
            interface, channels, dwell_time=0.1, regulatory_domain=regulatory_domain
        )
        
        if result["success"]:
            print("✅ Channel scan completed")
            print(f"   Channels scanned: {len(result['channels_scanned'])}/{len(channels)}")
            print(f"   Scan time: {result['performance_metrics']['total_scan_time_ms']:.1f}ms")
            print(f"   Average switch time: {result['performance_metrics']['average_switch_time_ms']:.1f}ms")
            
            if result["regulatory_violations"]:
                print("⚠️  Regulatory violations detected:")
                for violation in result["regulatory_violations"]:
                    print(f"   {violation}")
        else:
            print("❌ Channel scan failed:")
            for error in result["errors"]:
                print(f"   Error: {error}")
        
        return result
    
    def generate_security_report(self, interfaces: List[str]) -> Dict:
        """Generate comprehensive security report"""
        print("Generating security report...")
        
        # Generate monitor security report
        monitor_report = self.monitor_manager.create_security_report(interfaces)
        
        # Generate packet analysis report
        packet_report = self.packet_analyzer.generate_security_report()
        
        # Combine reports
        combined_report = {
            "timestamp": time.time(),
            "monitor_security": monitor_report,
            "packet_analysis": packet_report,
            "overall_assessment": self._assess_overall_security(monitor_report, packet_report)
        }
        
        # Display summary
        print("✅ Security report generated")
        print(f"   Interfaces analyzed: {len(monitor_report.get('interfaces', {}))}")
        print(f"   Security warnings: {len(monitor_report.get('security_warnings', []))}")
        print(f"   Threat indicators: {len(packet_report.get('threat_indicators', []))}")
        print(f"   Risk level: {packet_report.get('risk_level', 'UNKNOWN')}")
        
        return combined_report
    
    def _assess_overall_security(self, monitor_report: Dict, packet_report: Dict) -> Dict:
        """Assess overall security posture"""
        assessment = {
            "risk_level": "LOW",
            "compliance_status": "COMPLIANT",
            "recommendations": [],
            "critical_issues": []
        }
        
        # Analyze monitor security
        if monitor_report.get("security_warnings"):
            assessment["risk_level"] = "MEDIUM"
            assessment["recommendations"].append("Address monitor security warnings")
        
        # Analyze packet security
        packet_risk = packet_report.get("risk_level", "LOW")
        if packet_risk == "HIGH":
            assessment["risk_level"] = "HIGH"
            assessment["critical_issues"].extend(packet_report.get("threat_indicators", []))
        elif packet_risk == "MEDIUM" and assessment["risk_level"] == "LOW":
            assessment["risk_level"] = "MEDIUM"
        
        # Check compliance
        regulatory_compliance = packet_report.get("regulatory_compliance", {})
        if regulatory_compliance.get("regulatory_warnings"):
            assessment["compliance_status"] = "WARNINGS"
            assessment["recommendations"].append("Review regulatory compliance warnings")
        
        # Add general recommendations
        assessment["recommendations"].extend([
            "Regular security monitoring and assessment",
            "Maintain compliance with local regulations",
            "Implement proper access controls"
        ])
        
        return assessment
    
    def interactive_setup(self):
        """Interactive setup wizard"""
        print("Security and Monitor Mode Configuration Wizard")
        print("=" * 50)
        
        # Load current configuration
        config = self.load_configuration()
        
        # Detect interfaces
        interfaces = self.detect_interfaces()
        if not interfaces:
            print("No wireless interfaces available. Exiting.")
            return
        
        # Select interface
        print("\nSelect wireless interface:")
        for i, iface in enumerate(interfaces, 1):
            print(f"  {i}. {iface['interface']} ({iface['driver']})")
        
        try:
            choice = int(input("Enter choice (1-{}): ".format(len(interfaces))))
            selected_interface = interfaces[choice - 1]["interface"]
        except (ValueError, IndexError):
            print("Invalid choice. Using first interface.")
            selected_interface = interfaces[0]["interface"]
        
        print(f"Selected interface: {selected_interface}")
        
        # Select regulatory domain
        print("\nSelect regulatory domain:")
        domains = ["US", "EU", "JP"]
        for i, domain in enumerate(domains, 1):
            print(f"  {i}. {domain}")
        
        try:
            choice = int(input("Enter choice (1-3): "))
            regulatory_domain = domains[choice - 1]
        except (ValueError, IndexError):
            regulatory_domain = "US"
        
        print(f"Selected regulatory domain: {regulatory_domain}")
        
        # Configure monitor mode
        print("\nConfiguring monitor mode...")
        monitor_result = self.configure_monitor_mode(selected_interface, 6, regulatory_domain)
        
        if not monitor_result["success"]:
            print("Monitor mode configuration failed. Cannot continue.")
            return
        
        # Test packet injection (optional)
        test_injection = input("\nTest packet injection? (y/N): ").lower().startswith('y')
        if test_injection:
            injection_result = self.test_packet_injection(selected_interface, regulatory_domain)
        
        # Test channel scanning
        test_channels = [1, 6, 11, 36, 40, 44, 48]
        print(f"\nTesting channel scanning on channels: {test_channels}")
        scan_result = self.scan_channels(selected_interface, test_channels, regulatory_domain)
        
        # Generate security report
        print("\nGenerating security report...")
        security_report = self.generate_security_report([selected_interface])
        
        # Save configuration
        config["last_interface"] = selected_interface
        config["regulatory_domain"] = regulatory_domain
        config["last_setup"] = time.time()
        
        if self.save_configuration(config):
            print("✅ Configuration saved")
        
        print("\n" + "=" * 50)
        print("Setup completed successfully!")
        print(f"Monitor mode configured on {selected_interface}")
        print(f"Regulatory domain: {regulatory_domain}")
        print(f"Risk level: {security_report['packet_analysis']['risk_level']}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Security and Monitor Mode Configurator")
    parser.add_argument("--interface", help="Wireless interface to configure")
    parser.add_argument("--channel", type=int, default=6, help="Channel to use (default: 6)")
    parser.add_argument("--domain", default="US", help="Regulatory domain (default: US)")
    parser.add_argument("--interactive", action="store_true", help="Run interactive setup")
    parser.add_argument("--scan-channels", nargs="+", type=int, help="Channels to scan")
    parser.add_argument("--test-injection", action="store_true", help="Test packet injection")
    parser.add_argument("--security-report", action="store_true", help="Generate security report")
    
    args = parser.parse_args()
    
    configurator = SecurityMonitorConfigurator()
    
    if args.interactive:
        configurator.interactive_setup()
        return
    
    # Detect interfaces if none specified
    if not args.interface:
        interfaces = configurator.detect_interfaces()
        if not interfaces:
            print("No wireless interfaces detected")
            return
        args.interface = interfaces[0]["interface"]
        print(f"Using interface: {args.interface}")
    
    # Configure monitor mode
    monitor_result = configurator.configure_monitor_mode(
        args.interface, args.channel, args.domain
    )
    
    if not monitor_result["success"]:
        print("Monitor mode configuration failed")
        return
    
    # Test packet injection if requested
    if args.test_injection:
        configurator.test_packet_injection(args.interface, args.domain)
    
    # Scan channels if requested
    if args.scan_channels:
        configurator.scan_channels(args.interface, args.scan_channels, args.domain)
    
    # Generate security report if requested
    if args.security_report:
        configurator.generate_security_report([args.interface])

if __name__ == "__main__":
    main()