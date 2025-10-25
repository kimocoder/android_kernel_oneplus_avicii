#!/usr/bin/env python3
"""
Backports Build Testing Framework

This script provides comprehensive build testing for different Kconfig combinations,
cross-compilation testing for ARM64 architecture, and module loading tests.
"""

import os
import sys
import json
import tempfile
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import argparse
import multiprocessing

class BuildResult(Enum):
    """Build result status"""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    SKIP = "skip"
    ERROR = "error"

@dataclass
class BuildConfiguration:
    """Represents a build configuration to test"""
    name: str
    description: str
    config_options: Dict[str, str]
    arch: str = "x86_64"
    cross_compile: Optional[str] = None
    expected_modules: List[str] = field(default_factory=list)
    build_targets: List[str] = field(default_factory=lambda: ["modules"])
    timeout: int = 300  # 5 minutes default
    priority: int = 1  # 1=high, 2=medium, 3=low

@dataclass
class BuildExecution:
    """Represents a build execution result"""
    config: BuildConfiguration
    result: BuildResult
    execution_time: float
    build_log: str = ""
    error_message: str = ""
    modules_built: List[str] = field(default_factory=list)
    warnings_count: int = 0
    errors_count: int = 0

class BackportsBuildTester:
    """Comprehensive build testing framework"""
    
    def __init__(self, kernel_root: str = "."):
        self.kernel_root = Path(kernel_root).resolve()
        self.build_configs: List[BuildConfiguration] = []
        self.build_results: List[BuildExecution] = []
        
        # Build environment
        self.temp_dir = None
        self.original_config = None
        self.make_jobs = multiprocessing.cpu_count()
        
        # Load build configurations
        self._load_build_configurations()
    
    def _load_build_configurations(self):
        """Load predefined build configurations"""
        
        # Basic build configurations
        self.build_configs.extend([
            BuildConfiguration(
                name="basic_x86_64",
                description="Basic backports build for x86_64",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_CFG80211": "m",
                    "CONFIG_BACKPORTS_MAC80211": "m",
                    "CONFIG_MODULES": "y",
                    "CONFIG_NET": "y"
                },
                arch="x86_64",
                expected_modules=["cfg80211.ko", "mac80211.ko"],
                priority=1
            ),
            
            BuildConfiguration(
                name="basic_arm64",
                description="Basic backports build for ARM64",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_CFG80211": "m",
                    "CONFIG_BACKPORTS_MAC80211": "m",
                    "CONFIG_MODULES": "y",
                    "CONFIG_NET": "y"
                },
                arch="arm64",
                cross_compile="aarch64-linux-gnu-",
                expected_modules=["cfg80211.ko", "mac80211.ko"],
                priority=1
            ),
            
            BuildConfiguration(
                name="monitor_mode_x86_64",
                description="Monitor mode build for x86_64",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_CFG80211": "m",
                    "CONFIG_BACKPORTS_MAC80211": "m",
                    "CONFIG_BACKPORTS_MONITOR_MODE": "y",
                    "CONFIG_MODULES": "y",
                    "CONFIG_NET": "y",
                    "CONFIG_PACKET": "y"
                },
                arch="x86_64",
                expected_modules=["cfg80211.ko", "mac80211.ko"],
                priority=2
            ),
            
            BuildConfiguration(
                name="frame_injection_x86_64",
                description="Frame injection build for x86_64",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_CFG80211": "m",
                    "CONFIG_BACKPORTS_MAC80211": "m",
                    "CONFIG_BACKPORTS_MONITOR_MODE": "y",
                    "CONFIG_BACKPORTS_FRAME_INJECTION": "y",
                    "CONFIG_MODULES": "y",
                    "CONFIG_NET": "y",
                    "CONFIG_PACKET": "y",
                    "CONFIG_PACKET_MMAP": "y"
                },
                arch="x86_64",
                expected_modules=["cfg80211.ko", "mac80211.ko"],
                priority=2
            ),
            
            BuildConfiguration(
                name="android_complete_arm64",
                description="Complete Android build for ARM64",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_CFG80211": "m",
                    "CONFIG_BACKPORTS_MAC80211": "m",
                    "CONFIG_BACKPORTS_ANDROID": "y",
                    "CONFIG_BACKPORTS_ANDROID_WAKELOCK": "y",
                    "CONFIG_BACKPORTS_SECURITY_ANDROID": "y",
                    "CONFIG_MODULES": "y",
                    "CONFIG_NET": "y",
                    "CONFIG_ANDROID": "y",
                    "CONFIG_ANDROID_WAKELOCK": "y"
                },
                arch="arm64",
                cross_compile="aarch64-linux-gnu-",
                expected_modules=["cfg80211.ko", "mac80211.ko"],
                priority=2
            ),
            
            BuildConfiguration(
                name="debug_full_x86_64",
                description="Full debug build for x86_64",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_CFG80211": "m",
                    "CONFIG_BACKPORTS_MAC80211": "m",
                    "CONFIG_BACKPORTS_DEBUG": "y",
                    "CONFIG_BACKPORTS_DEBUG_VERBOSE": "y",
                    "CONFIG_BACKPORTS_TRACING": "y",
                    "CONFIG_BACKPORTS_DIAGNOSTICS": "y",
                    "CONFIG_MODULES": "y",
                    "CONFIG_NET": "y",
                    "CONFIG_TRACING": "y",
                    "CONFIG_DEBUG_FS": "y"
                },
                arch="x86_64",
                expected_modules=["cfg80211.ko", "mac80211.ko"],
                priority=3
            ),
            
            BuildConfiguration(
                name="builtin_x86_64",
                description="Built-in (non-modular) build for x86_64",
                config_options={
                    "CONFIG_BACKPORTS": "y",
                    "CONFIG_BACKPORTS_CFG80211": "y",
                    "CONFIG_BACKPORTS_MAC80211": "y",
                    "CONFIG_MODULES": "y",
                    "CONFIG_NET": "y"
                },
                arch="x86_64",
                expected_modules=[],  # Built-in, no modules expected
                priority=3
            )
        ])
    
    def setup_build_environment(self):
        """Set up build environment"""
        # Create temporary directory for build artifacts
        self.temp_dir = tempfile.mkdtemp(prefix="backports_build_test_")
        
        # Backup original configuration
        config_file = self.kernel_root / ".config"
        if config_file.exists():
            self.original_config = config_file.read_text()
    
    def cleanup_build_environment(self):
        """Clean up build environment"""
        # Restore original configuration
        if self.original_config:
            config_file = self.kernel_root / ".config"
            config_file.write_text(self.original_config)
        
        # Clean build artifacts
        try:
            subprocess.run(["make", "clean"], cwd=self.kernel_root, 
                         capture_output=True, timeout=60)
        except:
            pass
        
        # Remove temporary directory
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def create_build_config(self, config: BuildConfiguration) -> str:
        """Create build configuration file"""
        config_lines = []
        
        # Add architecture-specific options
        if config.arch == "arm64":
            config_lines.extend([
                "CONFIG_ARM64=y",
                "CONFIG_64BIT=y"
            ])
        elif config.arch == "x86_64":
            config_lines.extend([
                "CONFIG_X86_64=y",
                "CONFIG_64BIT=y"
            ])
        
        # Add basic required options
        config_lines.extend([
            "CONFIG_MODULES=y",
            "CONFIG_NET=y",
            "CONFIG_CRYPTO=y",
            "CONFIG_CRC32=y"
        ])
        
        # Add configuration-specific options
        for option, value in config.config_options.items():
            if value == "n":
                config_lines.append(f"# {option} is not set")
            else:
                config_lines.append(f"{option}={value}")
        
        # Create config file
        config_file = Path(self.temp_dir) / f"{config.name}.config"
        config_file.write_text("\n".join(config_lines) + "\n")
        
        return str(config_file)
    
    def prepare_kernel_config(self, config: BuildConfiguration) -> bool:
        """Prepare kernel configuration for build"""
        try:
            # Create and copy configuration
            config_file = self.create_build_config(config)
            kernel_config = self.kernel_root / ".config"
            shutil.copy2(config_file, kernel_config)
            
            # Set up environment variables
            env = os.environ.copy()
            env["ARCH"] = config.arch
            if config.cross_compile:
                env["CROSS_COMPILE"] = config.cross_compile
            
            # Run olddefconfig to resolve dependencies
            result = subprocess.run([
                "make", "olddefconfig"
            ], cwd=self.kernel_root, env=env, capture_output=True, 
               text=True, timeout=60)
            
            if result.returncode != 0:
                print(f"olddefconfig failed: {result.stderr}")
                return False
            
            return True
        
        except Exception as e:
            print(f"Failed to prepare config: {e}")
            return False
    
    def run_build(self, config: BuildConfiguration) -> BuildExecution:
        """Run build for a configuration"""
        start_time = time.time()
        
        try:
            # Prepare configuration
            if not self.prepare_kernel_config(config):
                return BuildExecution(
                    config=config,
                    result=BuildResult.ERROR,
                    execution_time=time.time() - start_time,
                    error_message="Failed to prepare kernel configuration"
                )
            
            # Set up environment
            env = os.environ.copy()
            env["ARCH"] = config.arch
            if config.cross_compile:
                env["CROSS_COMPILE"] = config.cross_compile
            
            # Build command
            build_cmd = ["make", f"-j{self.make_jobs}"] + config.build_targets
            
            # Run build
            result = subprocess.run(
                build_cmd,
                cwd=self.kernel_root,
                env=env,
                capture_output=True,
                text=True,
                timeout=config.timeout
            )
            
            execution_time = time.time() - start_time
            
            # Analyze build output
            build_log = result.stdout + result.stderr
            warnings_count = build_log.count("warning:")
            errors_count = build_log.count("error:")
            
            # Check for built modules
            modules_built = self.find_built_modules()
            
            # Determine result
            if result.returncode == 0:
                # Check if expected modules were built
                missing_modules = []
                for expected_module in config.expected_modules:
                    if not any(expected_module in built for built in modules_built):
                        missing_modules.append(expected_module)
                
                if missing_modules:
                    build_result = BuildResult.FAILURE
                    error_msg = f"Missing expected modules: {missing_modules}"
                else:
                    build_result = BuildResult.SUCCESS
                    error_msg = ""
            else:
                build_result = BuildResult.FAILURE
                error_msg = f"Build failed with exit code {result.returncode}"
            
            return BuildExecution(
                config=config,
                result=build_result,
                execution_time=execution_time,
                build_log=build_log,
                error_message=error_msg,
                modules_built=modules_built,
                warnings_count=warnings_count,
                errors_count=errors_count
            )
        
        except subprocess.TimeoutExpired:
            return BuildExecution(
                config=config,
                result=BuildResult.TIMEOUT,
                execution_time=time.time() - start_time,
                error_message=f"Build timeout after {config.timeout} seconds"
            )
        
        except Exception as e:
            return BuildExecution(
                config=config,
                result=BuildResult.ERROR,
                execution_time=time.time() - start_time,
                error_message=str(e)
            )
    
    def find_built_modules(self) -> List[str]:
        """Find modules that were built"""
        modules = []
        
        # Look for .ko files in common locations
        search_paths = [
            self.kernel_root / "backports-generated-6.1",
            self.kernel_root / "net" / "wireless",
            self.kernel_root / "drivers" / "net" / "wireless"
        ]
        
        for search_path in search_paths:
            if search_path.exists():
                for ko_file in search_path.rglob("*.ko"):
                    modules.append(str(ko_file.relative_to(self.kernel_root)))
        
        return modules
    
    def test_module_loading(self, config: BuildConfiguration, modules: List[str]) -> Dict[str, bool]:
        """Test module loading (requires root privileges)"""
        loading_results = {}
        
        # Skip if no modules to test
        if not modules:
            return loading_results
        
        # Check if we can test module loading
        if os.geteuid() != 0:
            print("Warning: Module loading tests require root privileges")
            return loading_results
        
        for module_path in modules:
            module_file = self.kernel_root / module_path
            if not module_file.exists():
                loading_results[module_path] = False
                continue
            
            try:
                # Try to load module
                result = subprocess.run([
                    "insmod", str(module_file)
                ], capture_output=True, timeout=10)
                
                if result.returncode == 0:
                    loading_results[module_path] = True
                    
                    # Try to unload module
                    module_name = module_file.stem
                    subprocess.run([
                        "rmmod", module_name
                    ], capture_output=True, timeout=10)
                else:
                    loading_results[module_path] = False
            
            except Exception:
                loading_results[module_path] = False
        
        return loading_results
    
    def run_all_builds(self, architectures: Optional[List[str]] = None,
                      priorities: Optional[List[int]] = None) -> List[BuildExecution]:
        """Run all build configurations"""
        
        # Filter configurations
        filtered_configs = self.build_configs
        
        if architectures:
            filtered_configs = [c for c in filtered_configs if c.arch in architectures]
        
        if priorities:
            filtered_configs = [c for c in filtered_configs if c.priority in priorities]
        
        print(f"Running {len(filtered_configs)} build configurations...")
        
        # Set up build environment
        self.setup_build_environment()
        
        try:
            results = []
            for i, config in enumerate(filtered_configs, 1):
                print(f"[{i}/{len(filtered_configs)}] Building: {config.name} ({config.arch})")
                
                # Check cross-compilation tools
                if config.cross_compile:
                    gcc_cmd = f"{config.cross_compile}gcc"
                    if shutil.which(gcc_cmd) is None:
                        print(f"   ⏭️  SKIP - Cross-compiler not found: {gcc_cmd}")
                        execution = BuildExecution(
                            config=config,
                            result=BuildResult.SKIP,
                            execution_time=0,
                            error_message=f"Cross-compiler not found: {gcc_cmd}"
                        )
                        results.append(execution)
                        continue
                
                execution = self.run_build(config)
                results.append(execution)
                
                # Print immediate result
                status_icon = {
                    BuildResult.SUCCESS: "✅",
                    BuildResult.FAILURE: "❌",
                    BuildResult.TIMEOUT: "⏰",
                    BuildResult.SKIP: "⏭️",
                    BuildResult.ERROR: "💥"
                }[execution.result]
                
                print(f"   {status_icon} {execution.result.value.upper()} ({execution.execution_time:.1f}s)")
                if execution.warnings_count > 0:
                    print(f"      Warnings: {execution.warnings_count}")
                if execution.error_message:
                    print(f"      Error: {execution.error_message}")
                if execution.modules_built:
                    print(f"      Modules: {len(execution.modules_built)} built")
            
            self.build_results = results
            return results
        
        finally:
            # Clean up build environment
            self.cleanup_build_environment()
    
    def generate_build_report(self) -> Dict[str, Any]:
        """Generate comprehensive build report"""
        if not self.build_results:
            return {"error": "No build results available"}
        
        # Calculate statistics
        total_builds = len(self.build_results)
        successful = len([r for r in self.build_results if r.result == BuildResult.SUCCESS])
        failed = len([r for r in self.build_results if r.result == BuildResult.FAILURE])
        timeouts = len([r for r in self.build_results if r.result == BuildResult.TIMEOUT])
        errors = len([r for r in self.build_results if r.result == BuildResult.ERROR])
        skipped = len([r for r in self.build_results if r.result == BuildResult.SKIP])
        
        # Calculate by architecture
        architectures = {}
        for result in self.build_results:
            arch = result.config.arch
            if arch not in architectures:
                architectures[arch] = {"total": 0, "successful": 0, "failed": 0}
            
            architectures[arch]["total"] += 1
            if result.result == BuildResult.SUCCESS:
                architectures[arch]["successful"] += 1
            elif result.result == BuildResult.FAILURE:
                architectures[arch]["failed"] += 1
        
        # Calculate execution time
        total_time = sum(r.execution_time for r in self.build_results)
        total_warnings = sum(r.warnings_count for r in self.build_results)
        
        return {
            "summary": {
                "total_builds": total_builds,
                "successful": successful,
                "failed": failed,
                "timeouts": timeouts,
                "errors": errors,
                "skipped": skipped,
                "success_rate": (successful / total_builds * 100) if total_builds > 0 else 0,
                "total_execution_time": total_time,
                "total_warnings": total_warnings
            },
            "architectures": architectures,
            "build_results": [
                {
                    "name": r.config.name,
                    "description": r.config.description,
                    "arch": r.config.arch,
                    "cross_compile": r.config.cross_compile,
                    "result": r.result.value,
                    "execution_time": r.execution_time,
                    "modules_built": len(r.modules_built),
                    "warnings_count": r.warnings_count,
                    "errors_count": r.errors_count,
                    "error_message": r.error_message
                }
                for r in self.build_results
            ]
        }
    
    def print_build_report(self):
        """Print human-readable build report"""
        report = self.generate_build_report()
        
        if "error" in report:
            print(f"Error generating report: {report['error']}")
            return
        
        summary = report["summary"]
        
        print("\n" + "=" * 60)
        print("BACKPORTS BUILD TEST REPORT")
        print("=" * 60)
        
        print(f"\nOverall Results:")
        print(f"  Total Builds: {summary['total_builds']}")
        print(f"  Successful: {summary['successful']} ✅")
        print(f"  Failed: {summary['failed']} ❌")
        print(f"  Timeouts: {summary['timeouts']} ⏰")
        print(f"  Errors: {summary['errors']} 💥")
        print(f"  Skipped: {summary['skipped']} ⏭️")
        print(f"  Success Rate: {summary['success_rate']:.1f}%")
        print(f"  Total Time: {summary['total_execution_time']:.1f}s")
        print(f"  Total Warnings: {summary['total_warnings']}")
        
        # Print architecture breakdown
        print(f"\nResults by Architecture:")
        for arch, stats in report["architectures"].items():
            success_rate = (stats["successful"] / stats["total"] * 100) if stats["total"] > 0 else 0
            print(f"  {arch}: {stats['successful']}/{stats['total']} ({success_rate:.1f}%)")
        
        # Print failed builds
        failed_builds = [r for r in self.build_results 
                        if r.result in [BuildResult.FAILURE, BuildResult.ERROR, BuildResult.TIMEOUT]]
        if failed_builds:
            print(f"\nFailed Builds:")
            for result in failed_builds:
                icon = {"failure": "❌", "error": "💥", "timeout": "⏰"}[result.result.value]
                print(f"  {icon} {result.config.name} ({result.config.arch}): {result.error_message}")
    
    def save_report(self, filename: str):
        """Save build report to file"""
        report = self.generate_build_report()
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Build report saved to: {filename}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Backports build testing framework')
    parser.add_argument('--kernel-root', default='.', help='Path to kernel source root')
    parser.add_argument('--architectures', nargs='+', help='Architectures to test')
    parser.add_argument('--priorities', nargs='+', type=int, help='Build priorities to test')
    parser.add_argument('--jobs', type=int, default=multiprocessing.cpu_count(), help='Number of build jobs')
    parser.add_argument('--report-file', help='Save build report to file')
    parser.add_argument('--json', action='store_true', help='Output JSON report')
    parser.add_argument('--list-configs', action='store_true', help='List available build configurations')
    
    args = parser.parse_args()
    
    # Create tester
    tester = BackportsBuildTester(args.kernel_root)
    tester.make_jobs = args.jobs
    
    if args.list_configs:
        print("Available build configurations:")
        for config in tester.build_configs:
            print(f"  {config.name} ({config.arch}, priority {config.priority})")
            print(f"    {config.description}")
        return 0
    
    # Run builds
    results = tester.run_all_builds(
        architectures=args.architectures,
        priorities=args.priorities
    )
    
    # Generate report
    if args.json:
        report = tester.generate_build_report()
        print(json.dumps(report, indent=2))
    else:
        tester.print_build_report()
    
    # Save report if requested
    if args.report_file:
        tester.save_report(args.report_file)
    
    # Return appropriate exit code
    failed_count = len([r for r in results if r.result in [BuildResult.FAILURE, BuildResult.ERROR]])
    return 1 if failed_count > 0 else 0

if __name__ == "__main__":
    sys.exit(main())