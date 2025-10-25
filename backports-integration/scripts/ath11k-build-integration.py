#!/usr/bin/env python3
"""
ath11k Build System Integration

This script integrates ath11k driver build rules into the backports build system
including Makefile rules, firmware management, and conditional compilation.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

class Ath11kBuildIntegration:
    """ath11k build system integration"""
    
    def __init__(self, kernel_root: str = "."):
        """Initialize build integration"""
        self.kernel_root = Path(kernel_root).resolve()
        self.backports_dir = self.kernel_root / "backports-integration"
        self.makefile_path = self.backports_dir / "Makefile"
    
    def generate_makefile_rules(self) -> str:
        """Generate Makefile rules for ath11k"""
        rules = """
#
# ath11k Driver Build Rules
# Integrated into backports build system
#

# ath11k driver configuration
ifdef CONFIG_BACKPORTS_ATH11K
    # Core ath11k driver
    obj-$(CONFIG_BACKPORTS_ATH11K) += ath11k/
    
    # Chipset-specific compilation flags
    ifdef CONFIG_BACKPORTS_ATH11K_QCA6390
        CFLAGS_ath11k-y += -DCONFIG_ATH11K_QCA6390
        ath11k-chipsets += qca6390
    endif
    
    ifdef CONFIG_BACKPORTS_ATH11K_QCA6490
        CFLAGS_ath11k-y += -DCONFIG_ATH11K_QCA6490
        ath11k-chipsets += qca6490
    endif
    
    ifdef CONFIG_BACKPORTS_ATH11K_WCN6855
        CFLAGS_ath11k-y += -DCONFIG_ATH11K_WCN6855
        ath11k-chipsets += wcn6855
    endif
    
    ifdef CONFIG_BACKPORTS_ATH11K_QCN9074
        CFLAGS_ath11k-y += -DCONFIG_ATH11K_QCN9074
        ath11k-chipsets += qcn9074
    endif
    
    # Feature-specific compilation flags
    ifdef CONFIG_BACKPORTS_MONITOR_MODE
        CFLAGS_ath11k-y += -DCONFIG_ATH11K_MONITOR_MODE
    endif
    
    ifdef CONFIG_BACKPORTS_FRAME_INJECTION
        CFLAGS_ath11k-y += -DCONFIG_ATH11K_FRAME_INJECTION
    endif
    
    ifdef CONFIG_BACKPORTS_ATH11K_SPECTRAL
        CFLAGS_ath11k-y += -DCONFIG_ATH11K_SPECTRAL_SCAN
    endif
    
    ifdef CONFIG_BACKPORTS_ATH11K_DEBUG
        CFLAGS_ath11k-y += -DCONFIG_ATH11K_DEBUG -DDEBUG
    endif
    
    ifdef CONFIG_BACKPORTS_ATH11K_TRACING
        CFLAGS_ath11k-y += -DCONFIG_ATH11K_TRACING
    endif
    
    ifdef CONFIG_BACKPORTS_ATH11K_DEBUGFS
        CFLAGS_ath11k-y += -DCONFIG_ATH11K_DEBUGFS
    endif
endif

# ath11k firmware installation
install-ath11k-firmware: $(if $(CONFIG_BACKPORTS_ATH11K),install-ath11k-firmware-real)

install-ath11k-firmware-real:
	@echo "Installing ath11k firmware files..."
	$(Q)mkdir -p $(DESTDIR)/lib/firmware/ath11k
	$(Q)for chipset in $(ath11k-chipsets); do \\
		if [ -d firmware/ath11k/$$chipset ]; then \\
			echo "  Installing firmware for $$chipset"; \\
			cp -r firmware/ath11k/$$chipset $(DESTDIR)/lib/firmware/ath11k/; \\
		fi; \\
	done
	@echo "ath11k firmware installation complete"

# ath11k module installation
install-ath11k-modules: $(if $(CONFIG_BACKPORTS_ATH11K),install-ath11k-modules-real)

install-ath11k-modules-real:
	@echo "Installing ath11k kernel modules..."
	$(Q)$(MAKE) -C $(KLIB_BUILD) M=$(PWD)/ath11k modules_install INSTALL_MOD_PATH=$(DESTDIR)
	@echo "ath11k modules installation complete"

# ath11k clean rules
clean-ath11k:
	$(Q)$(MAKE) -C ath11k clean 2>/dev/null || true
	$(Q)rm -f ath11k/*.o ath11k/*.ko ath11k/.*.cmd
	$(Q)rm -rf ath11k/.tmp_versions

# ath11k configuration validation
validate-ath11k-config:
	@echo "Validating ath11k configuration..."
	$(Q)if [ "$(CONFIG_BACKPORTS_ATH11K)" = "y" ] || [ "$(CONFIG_BACKPORTS_ATH11K)" = "m" ]; then \\
		echo "  ath11k driver: enabled"; \\
		if [ -z "$(ath11k-chipsets)" ]; then \\
			echo "  WARNING: No chipsets selected for ath11k"; \\
		else \\
			echo "  Selected chipsets: $(ath11k-chipsets)"; \\
		fi; \\
	else \\
		echo "  ath11k driver: disabled"; \\
	fi

# Add to main targets
.PHONY: install-ath11k-firmware install-ath11k-modules clean-ath11k validate-ath11k-config

# Integration with main build targets
install-firmware: install-ath11k-firmware
install-modules: install-ath11k-modules
clean: clean-ath11k
validate-config: validate-ath11k-config
"""
        return rules
    
    def create_firmware_makefile(self) -> str:
        """Create firmware-specific Makefile"""
        firmware_makefile = """
#
# ath11k Firmware Makefile
# Manages firmware files for different chipsets
#

FIRMWARE_DIR := /lib/firmware
ATH11K_FIRMWARE_DIR := $(FIRMWARE_DIR)/ath11k

# Chipset firmware mappings
QCA6390_FIRMWARE := QCA6390/hw2.0/amss.bin QCA6390/hw2.0/m3.bin
QCA6490_FIRMWARE := QCA6490/hw2.0/amss.bin QCA6490/hw2.0/m3.bin
WCN6855_FIRMWARE := WCN6855/hw2.0/amss.bin WCN6855/hw2.0/m3.bin
QCN9074_FIRMWARE := QCN9074/hw1.0/amss.bin QCN9074/hw1.0/m3.bin

# Installation targets
install-qca6390-firmware:
	@echo "Installing QCA6390 firmware..."
	$(Q)mkdir -p $(DESTDIR)$(ATH11K_FIRMWARE_DIR)/QCA6390/hw2.0
	$(Q)for fw in $(QCA6390_FIRMWARE); do \\
		if [ -f firmware/ath11k/$$fw ]; then \\
			cp firmware/ath11k/$$fw $(DESTDIR)$(ATH11K_FIRMWARE_DIR)/$$fw; \\
			echo "  Installed $$fw"; \\
		else \\
			echo "  WARNING: $$fw not found"; \\
		fi; \\
	done

install-qca6490-firmware:
	@echo "Installing QCA6490 firmware..."
	$(Q)mkdir -p $(DESTDIR)$(ATH11K_FIRMWARE_DIR)/QCA6490/hw2.0
	$(Q)for fw in $(QCA6490_FIRMWARE); do \\
		if [ -f firmware/ath11k/$$fw ]; then \\
			cp firmware/ath11k/$$fw $(DESTDIR)$(ATH11K_FIRMWARE_DIR)/$$fw; \\
			echo "  Installed $$fw"; \\
		else \\
			echo "  WARNING: $$fw not found"; \\
		fi; \\
	done

install-wcn6855-firmware:
	@echo "Installing WCN6855 firmware..."
	$(Q)mkdir -p $(DESTDIR)$(ATH11K_FIRMWARE_DIR)/WCN6855/hw2.0
	$(Q)for fw in $(WCN6855_FIRMWARE); do \\
		if [ -f firmware/ath11k/$$fw ]; then \\
			cp firmware/ath11k/$$fw $(DESTDIR)$(ATH11K_FIRMWARE_DIR)/$$fw; \\
			echo "  Installed $$fw"; \\
		else \\
			echo "  WARNING: $$fw not found"; \\
		fi; \\
	done

install-qcn9074-firmware:
	@echo "Installing QCN9074 firmware..."
	$(Q)mkdir -p $(DESTDIR)$(ATH11K_FIRMWARE_DIR)/QCN9074/hw1.0
	$(Q)for fw in $(QCN9074_FIRMWARE); do \\
		if [ -f firmware/ath11k/$$fw ]; then \\
			cp firmware/ath11k/$$fw $(DESTDIR)$(ATH11K_FIRMWARE_DIR)/$$fw; \\
			echo "  Installed $$fw"; \\
		else \\
			echo "  WARNING: $$fw not found"; \\
		fi; \\
	done

# Conditional firmware installation based on configuration
install-ath11k-firmware-conditional:
ifdef CONFIG_BACKPORTS_ATH11K_QCA6390
	$(MAKE) install-qca6390-firmware
endif
ifdef CONFIG_BACKPORTS_ATH11K_QCA6490
	$(MAKE) install-qca6490-firmware
endif
ifdef CONFIG_BACKPORTS_ATH11K_WCN6855
	$(MAKE) install-wcn6855-firmware
endif
ifdef CONFIG_BACKPORTS_ATH11K_QCN9074
	$(MAKE) install-qcn9074-firmware
endif

# Firmware validation
validate-ath11k-firmware:
	@echo "Validating ath11k firmware..."
	$(Q)for chipset in qca6390 qca6490 wcn6855 qcn9074; do \\
		if [ -d $(DESTDIR)$(ATH11K_FIRMWARE_DIR)/$$chipset ]; then \\
			echo "  $$chipset firmware: present"; \\
		else \\
			echo "  $$chipset firmware: missing"; \\
		fi; \\
	done

.PHONY: install-qca6390-firmware install-qca6490-firmware install-wcn6855-firmware install-qcn9074-firmware
.PHONY: install-ath11k-firmware-conditional validate-ath11k-firmware
"""
        return firmware_makefile
    
    def integrate_with_main_makefile(self) -> bool:
        """Integrate ath11k rules with main Makefile"""
        try:
            # Check if main Makefile exists
            if not self.makefile_path.exists():
                print(f"Main Makefile not found at {self.makefile_path}")
                return False
            
            # Read current Makefile
            with open(self.makefile_path, 'r') as f:
                makefile_content = f.read()
            
            # Check if ath11k integration already exists
            if "# ath11k Driver Build Rules" in makefile_content:
                print("ath11k integration already present in Makefile")
                return True
            
            # Add ath11k rules
            ath11k_rules = self.generate_makefile_rules()
            
            # Append to Makefile
            with open(self.makefile_path, 'a') as f:
                f.write("\n")
                f.write(ath11k_rules)
            
            print(f"ath11k build rules integrated into {self.makefile_path}")
            return True
            
        except Exception as e:
            print(f"Error integrating with Makefile: {e}")
            return False
    
    def create_build_scripts(self) -> Dict[str, bool]:
        """Create build helper scripts"""
        scripts_dir = self.backports_dir / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        # ath11k build script
        build_script = scripts_dir / "build-ath11k.sh"
        build_script_content = """#!/bin/bash
#
# ath11k Build Helper Script
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKPORTS_DIR="$(dirname "$SCRIPT_DIR")"
KERNEL_ROOT="$(dirname "$BACKPORTS_DIR")"

# Colors
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m'

print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Check configuration
check_ath11k_config() {
    print_status "$YELLOW" "Checking ath11k configuration..."
    
    if [ ! -f "$KERNEL_ROOT/.config" ]; then
        print_status "$RED" "ERROR: Kernel configuration not found"
        return 1
    fi
    
    if grep -q "CONFIG_BACKPORTS_ATH11K=m\\|CONFIG_BACKPORTS_ATH11K=y" "$KERNEL_ROOT/.config"; then
        print_status "$GREEN" "  ath11k driver: enabled"
    else
        print_status "$RED" "  ath11k driver: disabled"
        return 1
    fi
    
    # Check chipset configurations
    local chipsets_found=0
    for chipset in QCA6390 QCA6490 WCN6855 QCN9074; do
        if grep -q "CONFIG_BACKPORTS_ATH11K_$chipset=y" "$KERNEL_ROOT/.config"; then
            print_status "$GREEN" "  $chipset: enabled"
            chipsets_found=$((chipsets_found + 1))
        fi
    done
    
    if [ $chipsets_found -eq 0 ]; then
        print_status "$YELLOW" "  WARNING: No chipsets enabled"
    fi
    
    return 0
}

# Build ath11k
build_ath11k() {
    print_status "$YELLOW" "Building ath11k driver..."
    
    cd "$KERNEL_ROOT"
    
    # Build the driver
    if make -C "$BACKPORTS_DIR" ath11k/; then
        print_status "$GREEN" "ath11k build successful"
    else
        print_status "$RED" "ath11k build failed"
        return 1
    fi
    
    return 0
}

# Install ath11k
install_ath11k() {
    print_status "$YELLOW" "Installing ath11k driver..."
    
    cd "$KERNEL_ROOT"
    
    # Install modules
    if make -C "$BACKPORTS_DIR" install-ath11k-modules; then
        print_status "$GREEN" "ath11k modules installed"
    else
        print_status "$RED" "ath11k module installation failed"
        return 1
    fi
    
    # Install firmware
    if make -C "$BACKPORTS_DIR" install-ath11k-firmware; then
        print_status "$GREEN" "ath11k firmware installed"
    else
        print_status "$YELLOW" "ath11k firmware installation failed (may not be available)"
    fi
    
    return 0
}

# Main function
main() {
    case "$1" in
        "check")
            check_ath11k_config
            ;;
        "build")
            check_ath11k_config && build_ath11k
            ;;
        "install")
            check_ath11k_config && build_ath11k && install_ath11k
            ;;
        "clean")
            print_status "$YELLOW" "Cleaning ath11k build..."
            cd "$KERNEL_ROOT"
            make -C "$BACKPORTS_DIR" clean-ath11k
            print_status "$GREEN" "ath11k clean complete"
            ;;
        *)
            echo "Usage: $0 {check|build|install|clean}"
            echo "  check   - Check ath11k configuration"
            echo "  build   - Build ath11k driver"
            echo "  install - Build and install ath11k driver"
            echo "  clean   - Clean ath11k build files"
            exit 1
            ;;
    esac
}

main "$@"
"""
        
        try:
            with open(build_script, 'w') as f:
                f.write(build_script_content)
            build_script.chmod(0o755)
            results["build_script"] = True
            print(f"Created build script: {build_script}")
        except Exception as e:
            print(f"Error creating build script: {e}")
            results["build_script"] = False
        
        return results
    
    def validate_integration(self) -> Dict[str, any]:
        """Validate ath11k build integration"""
        validation = {
            "makefile_integrated": False,
            "build_scripts_present": False,
            "configuration_valid": True,
            "issues": [],
            "recommendations": []
        }
        
        # Check Makefile integration
        if self.makefile_path.exists():
            with open(self.makefile_path, 'r') as f:
                makefile_content = f.read()
            validation["makefile_integrated"] = "# ath11k Driver Build Rules" in makefile_content
        
        # Check build scripts
        build_script = self.backports_dir / "scripts" / "build-ath11k.sh"
        validation["build_scripts_present"] = build_script.exists()
        
        # Generate recommendations
        if not validation["makefile_integrated"]:
            validation["issues"].append("ath11k build rules not integrated into Makefile")
            validation["recommendations"].append("Run integrate_with_main_makefile()")
        
        if not validation["build_scripts_present"]:
            validation["issues"].append("ath11k build scripts not present")
            validation["recommendations"].append("Run create_build_scripts()")
        
        validation["configuration_valid"] = len(validation["issues"]) == 0
        
        return validation

def main():
    """Main function for testing"""
    integration = Ath11kBuildIntegration()
    
    print("ath11k Build System Integration")
    print("=" * 50)
    
    # Validate current integration
    validation = integration.validate_integration()
    
    print("Integration Status:")
    makefile_status = "✓" if validation["makefile_integrated"] else "✗"
    scripts_status = "✓" if validation["build_scripts_present"] else "✗"
    
    print(f"  Makefile Integration: {makefile_status}")
    print(f"  Build Scripts: {scripts_status}")
    
    if validation["issues"]:
        print(f"\nIssues:")
        for issue in validation["issues"]:
            print(f"  - {issue}")
    
    if validation["recommendations"]:
        print(f"\nRecommendations:")
        for rec in validation["recommendations"]:
            print(f"  - {rec}")
    
    # Show sample Makefile rules
    print(f"\nSample Makefile Rules:")
    rules = integration.generate_makefile_rules()
    print(rules[:500] + "..." if len(rules) > 500 else rules)

if __name__ == "__main__":
    main()