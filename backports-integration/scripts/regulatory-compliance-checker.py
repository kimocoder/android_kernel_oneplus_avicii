#!/usr/bin/env python3
"""
Regulatory Compliance Checker

This script provides comprehensive regulatory compliance checking for
wireless drivers including frequency validation, power limits, and
feature restrictions based on regulatory domains.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class ComplianceResult:
    """Compliance check result"""
    compliant: bool
    driver: str
    domain: str
    issues: List[str]
    warnings: List[str]
    recommendations: List[str]

class RegulatoryComplianceChecker:
    """Comprehensive regulatory compliance checker"""
    
    def __init__(self, kernel_root: str = "."):
        """Initialize compliance checker"""
        self.kernel_root = Path(kernel_root).resolve()
        self.backports_dir = self.kernel_root / "backports-integration"
        
        # Load regulatory rules
        self.regulatory_rules = self._load_regulatory_rules()
        
        # Load driver capabilities
        self.driver_capabilities = self._load_driver_capabilities()
    
    def _load_regulatory_rules(self) -> Dict:
        """Load regulatory rules for different domains"""
        return {
            "US": {
                "name": "United States (FCC)",
                "dfs_region": "FCC",
                "monitor_mode_allowed": True,
                "packet_injection_allowed": True,
                "restrictions": [
                    "Monitor mode requires proper authorization for commercial use",
                    "Packet injection must comply with Part 15 regulations",
                    "DFS channels require radar detection"
                ],
                "frequency_bands": {
                    "2.4GHz": {"start": 2412, "end": 2462, "max_power": 30},
                    "5GHz_lower": {"start": 5170, "end": 5250, "max_power": 23},
                    "5GHz_dfs": {"start": 5250, "end": 5730, "max_power": 23, "dfs_required": True},
                    "5GHz_upper": {"start": 5735, "end": 5835, "max_power": 30}
                }
            },
            "EU": {
                "name": "European Union (ETSI)",
                "dfs_region": "ETSI",
                "monitor_mode_allowed": True,
                "packet_injection_allowed": False,
                "restrictions": [
                    "Packet injection is generally prohibited",
                    "Monitor mode may require authorization in some countries",
                    "DFS channels require radar detection",
                    "Power limits are strictly enforced"
                ],
                "frequency_bands": {
                    "2.4GHz": {"start": 2412, "end": 2472, "max_power": 20},
                    "5GHz_lower": {"start": 5170, "end": 5250, "max_power": 23},
                    "5GHz_dfs": {"start": 5250, "end": 5710, "max_power": 23, "dfs_required": True}
                }
            },
            "JP": {
                "name": "Japan (MKK)",
                "dfs_region": "JP",
                "monitor_mode_allowed": False,
                "packet_injection_allowed": False,
                "restrictions": [
                    "Monitor mode requires special authorization",
                    "Packet injection is prohibited",
                    "Strict power limits enforced",
                    "Limited channel availability"
                ],
                "frequency_bands": {
                    "2.4GHz": {"start": 2412, "end": 2472, "max_power": 20},
                    "5GHz_lower": {"start": 5170, "end": 5250, "max_power": 23},
                    "5GHz_dfs": {"start": 5250, "end": 5710, "max_power": 23, "dfs_required": True}
                }
            },
            "CN": {
                "name": "China",
                "dfs_region": "FCC",
                "monitor_mode_allowed": False,
                "packet_injection_allowed": False,
                "restrictions": [
                    "Monitor mode is prohibited",
                    "Packet injection is prohibited",
                    "Limited frequency bands available",
                    "Strict government regulations"
                ],
                "frequency_bands": {
                    "2.4GHz": {"start": 2412, "end": 2472, "max_power": 20},
                    "5GHz_ism": {"start": 5725, "end": 5850, "max_power": 30}
                }
            }
        }
    
    def _load_driver_capabilities(self) -> Dict:
        """Load driver capability information"""
        return {
            "ath11k": {
                "monitor_mode": True,
                "packet_injection": True,
                "mesh_networking": True,
                "dfs_support": True,
                "power_control": True,
                "regulatory_enforcement": True
            },
            "ath10k": {
                "monitor_mode": True,
                "packet_injection": True,
                "mesh_networking": True,
                "dfs_support": True,
                "power_control": True,
                "regulatory_enforcement": True
            },
            "iwlwifi": {
                "monitor_mode": True,
                "packet_injection": False,
                "mesh_networking": False,
                "dfs_support": True,
                "power_control": True,
                "regulatory_enforcement": True
            },
            "rt2x00": {
                "monitor_mode": True,
                "packet_injection": True,
                "mesh_networking": False,
                "dfs_support": False,
                "power_control": True,
                "regulatory_enforcement": False
            },
            "rtw88": {
                "monitor_mode": True,
                "packet_injection": True,
                "mesh_networking": False,
                "dfs_support": False,
                "power_control": True,
                "regulatory_enforcement": True
            },
            "mt76": {
                "monitor_mode": True,
                "packet_injection": True,
                "mesh_networking": False,
                "dfs_support": True,
                "power_control": True,
                "regulatory_enforcement": True
            }
        }
    
    def check_driver_compliance(self, driver: str, domain: str) -> ComplianceResult:
        """Check regulatory compliance for a driver in a domain"""
        result = ComplianceResult(
            compliant=True,
            driver=driver,
            domain=domain,
            issues=[],
            warnings=[],
            recommendations=[]
        )
        
        # Check if driver and domain are known
        if driver not in self.driver_capabilities:
            result.issues.append(f"Unknown driver: {driver}")
            result.compliant = False
            return result
        
        if domain not in self.regulatory_rules:
            result.issues.append(f"Unknown regulatory domain: {domain}")
            result.compliant = False
            return result
        
        driver_caps = self.driver_capabilities[driver]
        domain_rules = self.regulatory_rules[domain]
        
        # Check monitor mode compliance
        if driver_caps["monitor_mode"] and not domain_rules["monitor_mode_allowed"]:
            result.issues.append("Monitor mode capability conflicts with regulatory restrictions")
            result.compliant = False
        elif driver_caps["monitor_mode"] and domain_rules["monitor_mode_allowed"]:
            result.warnings.append("Monitor mode available - ensure proper authorization")
        
        # Check packet injection compliance
        if driver_caps["packet_injection"] and not domain_rules["packet_injection_allowed"]:
            result.issues.append("Packet injection capability conflicts with regulatory restrictions")
            result.compliant = False
        elif driver_caps["packet_injection"] and domain_rules["packet_injection_allowed"]:
            result.warnings.append("Packet injection available - ensure compliance with regulations")
        
        # Check DFS support
        dfs_bands = [band for band in domain_rules["frequency_bands"].values() 
                    if band.get("dfs_required", False)]
        if dfs_bands and not driver_caps["dfs_support"]:
            result.warnings.append("DFS channels available but driver may not support radar detection")
        
        # Check regulatory enforcement
        if not driver_caps["regulatory_enforcement"]:
            result.warnings.append("Driver may not enforce regulatory limits automatically")
            result.recommendations.append("Manually configure power limits and channel restrictions")
        
        # Add domain-specific recommendations
        result.recommendations.extend(domain_rules["restrictions"])
        
        # Check for specific domain issues
        if domain == "CN" and driver in ["ath11k", "ath10k"]:
            result.warnings.append("Qualcomm drivers may have limited functionality in China")
        
        if domain == "JP" and driver_caps["monitor_mode"]:
            result.recommendations.append("Obtain proper authorization before using monitor mode in Japan")
        
        if domain == "EU" and driver_caps["packet_injection"]:
            result.recommendations.append("Disable packet injection features for EU compliance")
        
        return result
    
    def check_frequency_compliance(self, domain: str, frequency: int, power: int) -> Dict[str, any]:
        """Check if frequency and power are compliant in domain"""
        result = {
            "compliant": False,
            "frequency": frequency,
            "power": power,
            "domain": domain,
            "max_allowed_power": 0,
            "band": None,
            "issues": [],
            "warnings": []
        }
        
        if domain not in self.regulatory_rules:
            result["issues"].append(f"Unknown regulatory domain: {domain}")
            return result
        
        domain_rules = self.regulatory_rules[domain]
        
        # Find applicable frequency band
        for band_name, band_info in domain_rules["frequency_bands"].items():
            if band_info["start"] <= frequency <= band_info["end"]:
                result["band"] = band_name
                result["max_allowed_power"] = band_info["max_power"]
                
                if power <= band_info["max_power"]:
                    result["compliant"] = True
                else:
                    result["issues"].append(f"Power {power} dBm exceeds maximum {band_info['max_power']} dBm")
                
                if band_info.get("dfs_required", False):
                    result["warnings"].append("DFS (radar detection) required for this frequency")
                
                break
        
        if not result["band"]:
            result["issues"].append(f"Frequency {frequency} MHz not allowed in {domain}")
        
        return result
    
    def generate_compliance_report(self, drivers: List[str], domains: List[str]) -> Dict:
        """Generate comprehensive compliance report"""
        report = {
            "drivers": drivers,
            "domains": domains,
            "compliance_matrix": {},
            "summary": {
                "total_checks": 0,
                "compliant": 0,
                "non_compliant": 0,
                "warnings": 0
            },
            "recommendations": []
        }
        
        # Check each driver/domain combination
        for driver in drivers:
            report["compliance_matrix"][driver] = {}
            
            for domain in domains:
                result = self.check_driver_compliance(driver, domain)
                report["compliance_matrix"][driver][domain] = {
                    "compliant": result.compliant,
                    "issues": result.issues,
                    "warnings": result.warnings,
                    "recommendations": result.recommendations
                }
                
                # Update summary
                report["summary"]["total_checks"] += 1
                if result.compliant:
                    report["summary"]["compliant"] += 1
                else:
                    report["summary"]["non_compliant"] += 1
                
                report["summary"]["warnings"] += len(result.warnings)
        
        # Generate overall recommendations
        if report["summary"]["non_compliant"] > 0:
            report["recommendations"].append("Review non-compliant driver/domain combinations")
            report["recommendations"].append("Consider using alternative drivers or domains")
        
        if report["summary"]["warnings"] > 0:
            report["recommendations"].append("Address all regulatory warnings")
            report["recommendations"].append("Ensure proper authorization for restricted features")
        
        # Domain-specific recommendations
        if "CN" in domains:
            report["recommendations"].append("Consider regulatory restrictions in China")
        
        if "JP" in domains:
            report["recommendations"].append("Obtain proper authorization for Japan operations")
        
        if "EU" in domains:
            report["recommendations"].append("Ensure ETSI compliance for EU operations")
        
        return report
    
    def validate_current_setup(self) -> Dict[str, any]:
        """Validate current wireless setup for compliance"""
        result = {
            "regulatory_domain": None,
            "loaded_drivers": [],
            "compliance_status": {},
            "issues": [],
            "recommendations": []
        }
        
        # Get current regulatory domain
        try:
            reg_output = subprocess.run(["iw", "reg", "get"], 
                                      capture_output=True, text=True)
            if reg_output.returncode == 0:
                for line in reg_output.stdout.split('\n'):
                    if line.startswith("country"):
                        result["regulatory_domain"] = line.split()[1].rstrip(':')
                        break
        except FileNotFoundError:
            result["issues"].append("iw command not available")
        
        # Get loaded wireless drivers
        try:
            with open("/proc/modules", "r") as f:
                for line in f:
                    module_name = line.split()[0]
                    if module_name in self.driver_capabilities:
                        result["loaded_drivers"].append(module_name)
        except Exception as e:
            result["issues"].append(f"Could not read loaded modules: {e}")
        
        # Check compliance for loaded drivers
        if result["regulatory_domain"] and result["loaded_drivers"]:
            for driver in result["loaded_drivers"]:
                compliance = self.check_driver_compliance(driver, result["regulatory_domain"])
                result["compliance_status"][driver] = compliance
                
                if not compliance.compliant:
                    result["issues"].extend(compliance.issues)
                
                result["recommendations"].extend(compliance.recommendations)
        
        return result

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Regulatory Compliance Checker")
    parser.add_argument("command", choices=[
        "check", "frequency", "report", "validate", "domains", "drivers"
    ], help="Compliance command")
    
    parser.add_argument("--driver", help="Driver name")
    parser.add_argument("--domain", help="Regulatory domain")
    parser.add_argument("--frequency", type=int, help="Frequency in MHz")
    parser.add_argument("--power", type=int, help="Power in dBm")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    checker = RegulatoryComplianceChecker()
    
    if args.command == "check":
        if not args.driver or not args.domain:
            print("Error: Driver and domain required for compliance check")
            return 1
        
        result = checker.check_driver_compliance(args.driver, args.domain)
        
        if result.compliant:
            print(f"✅ {args.driver} is compliant in {args.domain}")
        else:
            print(f"❌ {args.driver} is NOT compliant in {args.domain}")
            
            if result.issues:
                print("\nIssues:")
                for issue in result.issues:
                    print(f"  - {issue}")
        
        if result.warnings:
            print("\nWarnings:")
            for warning in result.warnings:
                print(f"  ⚠️  {warning}")
        
        if result.recommendations:
            print("\nRecommendations:")
            for rec in result.recommendations:
                print(f"  - {rec}")
    
    elif args.command == "frequency":
        if not args.domain or not args.frequency or not args.power:
            print("Error: Domain, frequency, and power required")
            return 1
        
        result = checker.check_frequency_compliance(args.domain, args.frequency, args.power)
        
        if result["compliant"]:
            print(f"✅ {args.frequency} MHz @ {args.power} dBm is compliant in {args.domain}")
        else:
            print(f"❌ {args.frequency} MHz @ {args.power} dBm is NOT compliant in {args.domain}")
        
        if result["band"]:
            print(f"Band: {result['band']}")
            print(f"Max allowed power: {result['max_allowed_power']} dBm")
        
        for issue in result["issues"]:
            print(f"Issue: {issue}")
        
        for warning in result["warnings"]:
            print(f"Warning: {warning}")
    
    elif args.command == "report":
        drivers = ["ath11k", "ath10k", "iwlwifi", "rt2x00"]
        domains = ["US", "EU", "JP", "CN"]
        
        if args.driver:
            drivers = [args.driver]
        if args.domain:
            domains = [args.domain]
        
        report = checker.generate_compliance_report(drivers, domains)
        
        # Print report
        print("Regulatory Compliance Report")
        print("=" * 40)
        print(f"Drivers: {', '.join(drivers)}")
        print(f"Domains: {', '.join(domains)}")
        print()
        
        print("Summary:")
        print(f"  Total checks: {report['summary']['total_checks']}")
        print(f"  Compliant: {report['summary']['compliant']}")
        print(f"  Non-compliant: {report['summary']['non_compliant']}")
        print(f"  Warnings: {report['summary']['warnings']}")
        print()
        
        # Compliance matrix
        print("Compliance Matrix:")
        for driver in drivers:
            print(f"\n{driver}:")
            for domain in domains:
                compliance = report["compliance_matrix"][driver][domain]
                status = "✅" if compliance["compliant"] else "❌"
                print(f"  {status} {domain}")
                
                if args.verbose:
                    for issue in compliance["issues"]:
                        print(f"    Issue: {issue}")
                    for warning in compliance["warnings"]:
                        print(f"    Warning: {warning}")
        
        if report["recommendations"]:
            print("\nRecommendations:")
            for rec in report["recommendations"]:
                print(f"  - {rec}")
        
        # Save to file if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\nReport saved to: {args.output}")
    
    elif args.command == "validate":
        result = checker.validate_current_setup()
        
        print("Current Setup Validation")
        print("=" * 30)
        
        if result["regulatory_domain"]:
            print(f"Regulatory Domain: {result['regulatory_domain']}")
        else:
            print("Regulatory Domain: Not set or unknown")
        
        if result["loaded_drivers"]:
            print(f"Loaded Drivers: {', '.join(result['loaded_drivers'])}")
        else:
            print("Loaded Drivers: None detected")
        
        if result["compliance_status"]:
            print("\nCompliance Status:")
            for driver, compliance in result["compliance_status"].items():
                status = "✅" if compliance.compliant else "❌"
                print(f"  {status} {driver}")
        
        if result["issues"]:
            print("\nIssues:")
            for issue in result["issues"]:
                print(f"  - {issue}")
        
        if result["recommendations"]:
            print("\nRecommendations:")
            for rec in result["recommendations"]:
                print(f"  - {rec}")
    
    elif args.command == "domains":
        print("Supported Regulatory Domains:")
        for domain, info in checker.regulatory_rules.items():
            print(f"  {domain}: {info['name']}")
            print(f"    Monitor Mode: {'✅' if info['monitor_mode_allowed'] else '❌'}")
            print(f"    Packet Injection: {'✅' if info['packet_injection_allowed'] else '❌'}")
            print(f"    DFS Region: {info['dfs_region']}")
    
    elif args.command == "drivers":
        print("Supported Drivers:")
        for driver, caps in checker.driver_capabilities.items():
            print(f"  {driver}:")
            for cap, supported in caps.items():
                status = "✅" if supported else "❌"
                print(f"    {cap}: {status}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())