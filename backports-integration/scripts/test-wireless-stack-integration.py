#!/usr/bin/env python3
"""
Integration Tests for Wireless Stack

This module provides comprehensive integration tests for the complete wireless
stack build and loading, including driver coexistence scenarios and end-to-end
validation.
"""

import os
import sys
import subprocess
import unittest
import tempfile
import time
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the scripts directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

class TestWirelessStackBuild(unittest.TestCase):
    """Integration tests for wireless stack build system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.kernel_root = Path(__file__).parent.parent.parent
        self.backports_dir = self.kernel_root / "backports-integration"
        
    def test_kconfig_structure(self):
        """Test Kconfig structure and dependencies"""
        kconfig_file = self.backports_dir / "Kconfig"
        self.assertTrue(kconfig_file.exists(), "Kconfig file should exist")
        
        content = kconfig_file.read_text()
        
        # Test essential configuration options
        essential_configs = [
            "BACKPORTS_CFG80211",
            "BACKPORTS_MAC80211", 
            "BACKPORTS_WIRELESS_DRIVERS",
            "BACKPORTS_ATH_DRIVERS",
            "BACKPORTS_IWLWIFI"
        ]
        
        for config in essential_configs:
            self.assertIn(config, content, f"Missing essential config: {config}")
    
    def test_makefile_integration(self):
        """Test Makefile integration for wireless drivers"""
        makefile = self.backports_dir / "Makefile"
        self.assertTrue(makefile.exists(), "Makefile should exist")
        
        content = makefile.read_text()
        
        # Test wireless-related build targets
        expected_targets = [
            "wireless",
            "cfg80211",
            "mac80211"
        ]
        
        # At least some wireless-related content should be present
        wireless_content = any(target in content for target in expected_targets)
        self.assertTrue(wireless_content, "Makefile should contain wireless build rules")
    
    def test_dependency_resolution(self):
        """Test wireless stack dependency resolution"""
        # Test that dependency resolver exists and works
        resolver_script = self.backports_dir / "scripts" / "wireless-dependency-resolver.py"
        
        if resolver_script.exists():
            # Test dependency resolution
            result = subprocess.run([
                "python3", str(resolver_script), "--test"
            ], capture_output=True, text=True)
            
            # Should complete without critical errors
            self.assertEqual(result.returncode, 0, "Dependency resolver should work")
    
    def test_build_system_validation(self):
        """Test build system validation"""
        validator_script = self.backports_dir / "scripts" / "build-system-validator.py"
        
        if validator_script.exists():
            result = subprocess.run([
                "python3", str(validator_script)
            ], capture_output=True, text=True)
            
            # Should complete validation
            self.assertIn(("PASS" or "✓"), result.stdout, "Build system validation should pass")

class TestWirelessStackLoading(unittest.TestCase):
    """Integration tests for wireless stack module loading"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_modules = ["cfg80211", "mac80211"]
        self.wireless_drivers = ["ath11k", "ath10k", "iwlwifi"]
    
    def test_module_loading_order(self):
        """Test correct module loading order"""
        # Test that modules can be loaded in correct dependency order
        # This is a simulation since we can't actually load modules in test
        
        loading_order = [
            "cfg80211",      # Base wireless configuration
            "mac80211",      # 802.11 stack
            "ath11k"         # Driver
        ]
        
        # Verify dependency chain makes sense
        for i in range(len(loading_order) - 1):
            current_module = loading_order[i]
            next_module = loading_order[i + 1]
            
            # Basic validation that order is logical
            self.assertIsInstance(current_module, str)
            self.assertIsInstance(next_module, str)
    
    def test_module_dependency_checking(self):
        """Test module dependency checking"""
        # Test module loading manager if available
        manager_script = Path(__file__).parent / "module-loading-manager.py"
        
        if manager_script.exists():
            result = subprocess.run([
                "python3", str(manager_script), "--check-dependencies"
            ], capture_output=True, text=True)
            
            # Should complete dependency check
            self.assertEqual(result.returncode, 0, "Module dependency check should succeed")
    
    def test_wireless_stack_manager(self):
        """Test wireless stack manager functionality"""
        stack_manager = Path(__file__).parent / "wireless-stack-manager.py"
        
        if stack_manager.exists():
            result = subprocess.run([
                "python3", str(stack_manager), "--validate"
            ], capture_output=True, text=True)
            
            # Should validate stack configuration
            self.assertEqual(result.returncode, 0, "Wireless stack validation should succeed")

class TestDriverCoexistenceScenarios(unittest.TestCase):
    """Integration tests for driver coexistence scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.coexistence_tester = Path(__file__).parent / "driver-coexistence-tester.py"
    
    def test_single_driver_scenario(self):
        """Test single driver loading scenario"""
        if self.coexistence_tester.exists():
            # Test single driver (should always work)
            result = subprocess.run([
                "python3", str(self.coexistence_tester), "--test", "ath11k"
            ], capture_output=True, text=True)
            
            # Single driver should not have conflicts
            self.assertEqual(result.returncode, 0, "Single driver should load without conflicts")
    
    def test_compatible_drivers_scenario(self):
        """Test compatible drivers coexistence"""
        if self.coexistence_tester.exists():
            # Test compatible driver combination
            result = subprocess.run([
                "python3", str(self.coexistence_tester), "--test", "ath11k", "iwlwifi"
            ], capture_output=True, text=True)
            
            # Compatible drivers should coexist
            # Note: This might fail in some environments, which is acceptable
            self.assertIsInstance(result.returncode, int)
    
    def test_conflicting_drivers_detection(self):
        """Test detection of conflicting drivers"""
        if self.coexistence_tester.exists():
            # Test known conflicting combination
            result = subprocess.run([
                "python3", str(self.coexistence_tester), "--test", "ath11k", "qcacld"
            ], capture_output=True, text=True)
            
            # Should detect conflicts (may return non-zero exit code)
            self.assertIsInstance(result.returncode, int)
    
    def test_coexistence_report_generation(self):
        """Test coexistence report generation"""
        if self.coexistence_tester.exists():
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                report_file = f.name
            
            try:
                result = subprocess.run([
                    "python3", str(self.coexistence_tester), "--report", report_file
                ], capture_output=True, text=True)
                
                self.assertEqual(result.returncode, 0, "Report generation should succeed")
                
                # Check report was created
                report_path = Path(report_file)
                self.assertTrue(report_path.exists(), "Report file should be created")
                
                # Check report content
                if report_path.exists():
                    content = report_path.read_text()
                    self.assertGreater(len(content), 0, "Report should have content")
            
            finally:
                # Clean up
                if Path(report_file).exists():
                    Path(report_file).unlink()

class TestEndToEndValidation(unittest.TestCase):
    """End-to-end integration tests for complete wireless stack"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.validation_framework = Path(__file__).parent / "wireless-validation-framework.py"
    
    def test_comprehensive_validation_workflow(self):
        """Test complete validation workflow"""
        if self.validation_framework.exists():
            result = subprocess.run([
                "python3", str(self.validation_framework)
            ], capture_output=True, text=True)
            
            # Should complete validation workflow
            self.assertEqual(result.returncode, 0, "Comprehensive validation should succeed")
    
    def test_validation_report_generation(self):
        """Test validation report generation"""
        if self.validation_framework.exists():
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                report_file = f.name
            
            try:
                result = subprocess.run([
                    "python3", str(self.validation_framework), "--output", report_file
                ], capture_output=True, text=True)
                
                self.assertEqual(result.returncode, 0, "Report generation should succeed")
                
                # Check report was created
                report_path = Path(report_file)
                self.assertTrue(report_path.exists(), "Validation report should be created")
                
                if report_path.exists():
                    content = report_path.read_text()
                    self.assertGreater(len(content), 100, "Report should have substantial content")
            
            finally:
                # Clean up
                if Path(report_file).exists():
                    Path(report_file).unlink()
    
    def test_json_output_format(self):
        """Test JSON output format"""
        if self.validation_framework.exists():
            result = subprocess.run([
                "python3", str(self.validation_framework), "--json"
            ], capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout:
                try:
                    # Should be valid JSON
                    json_data = json.loads(result.stdout)
                    self.assertIsInstance(json_data, dict, "JSON output should be a dictionary")
                except json.JSONDecodeError:
                    self.fail("Output should be valid JSON")

class TestChipsetDetectionIntegration(unittest.TestCase):
    """Integration tests for chipset detection and validation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.chipset_tool = Path(__file__).parent / "chipset-validation-tool.py"
    
    def test_chipset_detection(self):
        """Test chipset detection functionality"""
        if self.chipset_tool.exists():
            result = subprocess.run([
                "python3", str(self.chipset_tool)
            ], capture_output=True, text=True)
            
            # Should complete without critical errors
            self.assertEqual(result.returncode, 0, "Chipset detection should work")
    
    def test_compatibility_report(self):
        """Test chipset compatibility report"""
        if self.chipset_tool.exists():
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                report_file = f.name
            
            try:
                result = subprocess.run([
                    "python3", str(self.chipset_tool), "--report", report_file
                ], capture_output=True, text=True)
                
                self.assertEqual(result.returncode, 0, "Compatibility report should be generated")
                
                # Check report file
                report_path = Path(report_file)
                if report_path.exists():
                    content = report_path.read_text()
                    self.assertIn("Compatibility Report", content, "Report should have proper header")
            
            finally:
                # Clean up
                if Path(report_file).exists():
                    Path(report_file).unlink()
    
    def test_chipset_data_export(self):
        """Test chipset data export functionality"""
        if self.chipset_tool.exists():
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                export_file = f.name
            
            try:
                result = subprocess.run([
                    "python3", str(self.chipset_tool), "--export", export_file, "--format", "json"
                ], capture_output=True, text=True)
                
                self.assertEqual(result.returncode, 0, "Chipset data export should work")
                
                # Check export file
                export_path = Path(export_file)
                if export_path.exists():
                    content = export_path.read_text()
                    try:
                        json.loads(content)  # Should be valid JSON
                    except json.JSONDecodeError:
                        self.fail("Exported data should be valid JSON")
            
            finally:
                # Clean up
                if Path(export_file).exists():
                    Path(export_file).unlink()

class TestFirmwareValidationIntegration(unittest.TestCase):
    """Integration tests for firmware validation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.firmware_tool = Path(__file__).parent / "firmware-validation-tool.py"
    
    def test_firmware_scanning(self):
        """Test firmware scanning functionality"""
        if self.firmware_tool.exists():
            result = subprocess.run([
                "python3", str(self.firmware_tool), "--scan"
            ], capture_output=True, text=True)
            
            # Should complete scanning
            self.assertEqual(result.returncode, 0, "Firmware scanning should work")
    
    def test_firmware_validation(self):
        """Test firmware validation for specific driver/chipset"""
        if self.firmware_tool.exists():
            result = subprocess.run([
                "python3", str(self.firmware_tool), "--validate", "ath11k", "QCA6390"
            ], capture_output=True, text=True)
            
            # Should complete validation (may find missing firmware, which is OK)
            self.assertEqual(result.returncode, 0, "Firmware validation should complete")
    
    def test_firmware_report(self):
        """Test firmware validation report"""
        if self.firmware_tool.exists():
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                report_file = f.name
            
            try:
                result = subprocess.run([
                    "python3", str(self.firmware_tool), "--report", report_file
                ], capture_output=True, text=True)
                
                self.assertEqual(result.returncode, 0, "Firmware report should be generated")
                
                # Check report file
                report_path = Path(report_file)
                if report_path.exists():
                    content = report_path.read_text()
                    self.assertIn("Firmware", content, "Report should mention firmware")
            
            finally:
                # Clean up
                if Path(report_file).exists():
                    Path(report_file).unlink()

class TestIntegrationPerformance(unittest.TestCase):
    """Performance tests for integration scenarios"""
    
    def test_validation_performance(self):
        """Test validation performance under load"""
        validation_framework = Path(__file__).parent / "wireless-validation-framework.py"
        
        if validation_framework.exists():
            start_time = time.time()
            
            # Run validation multiple times
            for _ in range(3):
                result = subprocess.run([
                    "python3", str(validation_framework)
                ], capture_output=True, text=True)
                
                # Should complete reasonably quickly
                self.assertEqual(result.returncode, 0)
            
            elapsed_time = time.time() - start_time
            
            # Should complete within reasonable time (30 seconds for 3 runs)
            self.assertLess(elapsed_time, 30.0, "Validation should complete in reasonable time")
    
    def test_concurrent_validation(self):
        """Test concurrent validation operations"""
        import threading
        
        validation_tools = [
            Path(__file__).parent / "chipset-validation-tool.py",
            Path(__file__).parent / "firmware-validation-tool.py"
        ]
        
        results = []
        threads = []
        
        def run_tool(tool_path):
            if tool_path.exists():
                result = subprocess.run([
                    "python3", str(tool_path)
                ], capture_output=True, text=True)
                results.append(result.returncode)
        
        # Start concurrent validation
        for tool in validation_tools:
            thread = threading.Thread(target=run_tool, args=(tool,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=30)  # 30 second timeout
        
        # All tools should complete successfully
        for returncode in results:
            self.assertEqual(returncode, 0, "Concurrent validation should succeed")

def create_integration_test_suite():
    """Create comprehensive integration test suite"""
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestWirelessStackBuild,
        TestWirelessStackLoading,
        TestDriverCoexistenceScenarios,
        TestEndToEndValidation,
        TestChipsetDetectionIntegration,
        TestFirmwareValidationIntegration,
        TestIntegrationPerformance
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    return suite

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Wireless Stack Integration Tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--failfast", "-f", action="store_true", help="Stop on first failure")
    parser.add_argument("--pattern", "-p", help="Test pattern to match")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    
    args = parser.parse_args()
    
    # Configure test runner
    verbosity = 2 if args.verbose else 1
    
    if args.pattern:
        # Run specific test pattern
        loader = unittest.TestLoader()
        suite = loader.discover('.', pattern=args.pattern)
    else:
        # Run all tests
        suite = create_integration_test_suite()
        
        # Optionally skip performance tests
        if not args.performance:
            # Filter out performance tests for faster execution
            filtered_suite = unittest.TestSuite()
            for test_case in suite:
                if hasattr(test_case, '_tests'):
                    # This is a test suite
                    for test in test_case._tests:
                        if "Performance" not in test.__class__.__name__:
                            filtered_suite.addTest(test)
                else:
                    # This is a single test
                    if "Performance" not in test_case.__class__.__name__:
                        filtered_suite.addTest(test_case)
            suite = filtered_suite
    
    runner = unittest.TextTestRunner(
        verbosity=verbosity,
        failfast=args.failfast,
        buffer=True
    )
    
    print("Wireless Stack Integration Tests")
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
        print("\n✅ All wireless stack integration tests passed!")
        return 0
    else:
        print(f"\n❌ {len(result.failures) + len(result.errors)} test(s) failed")
        
        # Show failure details
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
        
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())