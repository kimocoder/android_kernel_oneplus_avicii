#!/usr/bin/env python3
"""
Build System Integration Test Suite

This test suite validates the build system integration for wireless drivers
including Makefile targets, conditional compilation, and firmware management.
"""

import os
import sys
import subprocess
import unittest
import tempfile
from pathlib import Path

class TestBuildSystemIntegration(unittest.TestCase):
    """Test suite for build system integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.kernel_root = Path(__file__).parent.parent.parent
        self.backports_dir = self.kernel_root / "backports-integration"
        self.makefile = self.backports_dir / "Makefile"
        
    def test_makefile_exists(self):
        """Test that Makefile exists and is readable"""
        self.assertTrue(self.makefile.exists(), "Makefile should exist")
        self.assertTrue(self.makefile.is_file(), "Makefile should be a file")
        
        # Test that Makefile is readable
        content = self.makefile.read_text()
        self.assertGreater(len(content), 0, "Makefile should have content")
    
    def test_makefile_help_target(self):
        """Test Makefile help target"""
        result = subprocess.run([
            "make", "-f", str(self.makefile), "backports_help"
        ], capture_output=True, text=True, env={"CONFIG_BACKPORTS": "y"})
        
        self.assertEqual(result.returncode, 0, "Help target should succeed")
        self.assertIn("Backports Integration Makefile", result.stdout)
        self.assertIn("wireless_drivers", result.stdout)
        self.assertIn("firmware_install", result.stdout)
    
    def test_wireless_status_target(self):
        """Test wireless status target"""
        env = {
            "CONFIG_BACKPORTS": "y",
            "CONFIG_BACKPORTS_ATH11K": "y"
        }
        
        result = subprocess.run([
            "make", "-f", str(self.makefile), "wireless_status"
        ], capture_output=True, text=True, env=env)
        
        self.assertEqual(result.returncode, 0, "Wireless status should succeed")
        self.assertIn("Wireless Driver Status", result.stdout)
        self.assertIn("ath11k driver: ENABLED", result.stdout)
    
    def test_backports_validate_target(self):
        """Test backports validation target"""
        result = subprocess.run([
            "make", "-f", str(self.makefile), "backports_validate"
        ], capture_output=True, text=True, env={"CONFIG_BACKPORTS": "y"})
        
        self.assertEqual(result.returncode, 0, "Validation should succeed")
        self.assertIn("validation passed", result.stdout)
    
    def test_wireless_validate_target(self):
        """Test wireless validation target"""
        env = {
            "CONFIG_BACKPORTS": "y",
            "CONFIG_BACKPORTS_WIRELESS_DRIVERS": "y",
            "CONFIG_BACKPORTS_CFG80211": "y"
        }
        
        result = subprocess.run([
            "make", "-f", str(self.makefile), "wireless_validate"
        ], capture_output=True, text=True, env=env)
        
        self.assertEqual(result.returncode, 0, "Wireless validation should succeed")
    
    def test_conditional_compilation(self):
        """Test conditional compilation based on Kconfig"""
        # Test with no drivers enabled
        result = subprocess.run([
            "make", "-f", str(self.makefile), "backports_status"
        ], capture_output=True, text=True, env={"CONFIG_BACKPORTS": "y"})
        
        self.assertEqual(result.returncode, 0)
        self.assertIn("Wireless Drivers:", result.stdout)
        
        # Test with ath11k enabled
        env = {
            "CONFIG_BACKPORTS": "y",
            "CONFIG_BACKPORTS_ATH11K": "y"
        }
        
        result = subprocess.run([
            "make", "-f", str(self.makefile), "backports_status"
        ], capture_output=True, text=True, env=env)
        
        self.assertEqual(result.returncode, 0)
        self.assertIn("ath11k", result.stdout)
    
    def test_build_integration_script(self):
        """Test wireless build integration script"""
        script = self.backports_dir / "scripts" / "wireless-build-integration.py"
        
        if script.exists():
            result = subprocess.run([
                "python3", str(script), "--validate"
            ], capture_output=True, text=True)
            
            self.assertEqual(result.returncode, 0, "Build integration script should work")
            self.assertIn("Build environment validation", result.stdout)
    
    def test_build_configuration_file(self):
        """Test build configuration file"""
        config_file = self.backports_dir / "configs" / "build.json"
        
        self.assertTrue(config_file.exists(), "Build config should exist")
        
        # Test that it's valid JSON
        import json
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Check required sections
            self.assertIn("wireless_drivers", config)
            self.assertIn("build_options", config)
            self.assertIn("firmware_options", config)
            
            # Check wireless drivers section
            drivers = config["wireless_drivers"]
            self.assertIn("ath11k", drivers)
            self.assertIn("ath10k", drivers)
            self.assertIn("iwlwifi", drivers)
            
        except json.JSONDecodeError:
            self.fail("Build config should be valid JSON")
    
    def test_firmware_management_targets(self):
        """Test firmware management targets"""
        # Test firmware validation target
        result = subprocess.run([
            "make", "-f", str(self.makefile), "firmware_validate"
        ], capture_output=True, text=True, env={"CONFIG_BACKPORTS": "y"})
        
        # Should complete without critical errors
        self.assertEqual(result.returncode, 0, "Firmware validation should complete")
    
    def test_clean_targets(self):
        """Test clean targets"""
        # Test backports clean
        result = subprocess.run([
            "make", "-f", str(self.makefile), "backports_clean"
        ], capture_output=True, text=True, env={"CONFIG_BACKPORTS": "y"})
        
        self.assertEqual(result.returncode, 0, "Clean should succeed")
        
        # Test wireless clean
        result = subprocess.run([
            "make", "-f", str(self.makefile), "wireless_clean"
        ], capture_output=True, text=True, env={"CONFIG_BACKPORTS": "y"})
        
        self.assertEqual(result.returncode, 0, "Wireless clean should succeed")
    
    def test_dependency_checking(self):
        """Test dependency checking"""
        result = subprocess.run([
            "make", "-f", str(self.makefile), "backports_deps"
        ], capture_output=True, text=True, env={"CONFIG_BACKPORTS": "y"})
        
        # Should complete dependency check
        self.assertEqual(result.returncode, 0, "Dependency check should complete")
    
    def test_makefile_syntax(self):
        """Test Makefile syntax"""
        # Test that Makefile has valid syntax by running a simple target
        result = subprocess.run([
            "make", "-f", str(self.makefile), "-n", "backports_help"
        ], capture_output=True, text=True, env={"CONFIG_BACKPORTS": "y"})
        
        # -n flag means dry run, should succeed if syntax is valid
        self.assertEqual(result.returncode, 0, "Makefile should have valid syntax")

class TestBuildIntegrationScript(unittest.TestCase):
    """Test suite for build integration script"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.script_path = Path(__file__).parent / "wireless-build-integration.py"
    
    def test_script_exists(self):
        """Test that build integration script exists"""
        self.assertTrue(self.script_path.exists(), "Build integration script should exist")
    
    def test_script_help(self):
        """Test script help"""
        if self.script_path.exists():
            result = subprocess.run([
                "python3", str(self.script_path), "--help"
            ], capture_output=True, text=True)
            
            self.assertEqual(result.returncode, 0, "Script help should work")
            self.assertIn("Wireless Build Integration", result.stdout)
    
    def test_script_validation(self):
        """Test script validation"""
        if self.script_path.exists():
            result = subprocess.run([
                "python3", str(self.script_path), "--validate"
            ], capture_output=True, text=True)
            
            self.assertEqual(result.returncode, 0, "Script validation should work")
    
    def test_script_report_generation(self):
        """Test script report generation"""
        if self.script_path.exists():
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                report_file = f.name
            
            try:
                result = subprocess.run([
                    "python3", str(self.script_path), "--report", report_file
                ], capture_output=True, text=True)
                
                self.assertEqual(result.returncode, 0, "Report generation should work")
                
                # Check report file was created
                report_path = Path(report_file)
                self.assertTrue(report_path.exists(), "Report file should be created")
                
                if report_path.exists():
                    content = report_path.read_text()
                    self.assertIn("Wireless Build Integration Report", content)
            
            finally:
                # Clean up
                if Path(report_file).exists():
                    Path(report_file).unlink()

class TestFirmwareIntegration(unittest.TestCase):
    """Test suite for firmware integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.firmware_tool = Path(__file__).parent / "firmware-validation-tool.py"
    
    def test_firmware_validation_tool(self):
        """Test firmware validation tool integration"""
        if self.firmware_tool.exists():
            result = subprocess.run([
                "python3", str(self.firmware_tool), "--help"
            ], capture_output=True, text=True)
            
            self.assertEqual(result.returncode, 0, "Firmware tool should work")
            self.assertIn("Firmware Validation Tool", result.stdout)

def create_test_suite():
    """Create comprehensive test suite"""
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestBuildSystemIntegration,
        TestBuildIntegrationScript,
        TestFirmwareIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    return suite

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build System Integration Tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--failfast", "-f", action="store_true", help="Stop on first failure")
    
    args = parser.parse_args()
    
    # Configure test runner
    verbosity = 2 if args.verbose else 1
    
    suite = create_test_suite()
    runner = unittest.TextTestRunner(
        verbosity=verbosity,
        failfast=args.failfast,
        buffer=True
    )
    
    print("Build System Integration Tests")
    print("=" * 50)
    
    result = runner.run(suite)
    
    # Print summary
    print(f"\nTests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / 
                   max(result.testsRun, 1)) * 100
    print(f"Success rate: {success_rate:.1f}%")
    
    if result.wasSuccessful():
        print("\n✅ All build system integration tests passed!")
        return 0
    else:
        print(f"\n❌ {len(result.failures) + len(result.errors)} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())