#
# Backports Integration Makefile
#
# This Makefile integrates the backports build system with the kernel build process.
# It provides conditional compilation based on Kconfig selections and handles
# module installation and dependency resolution.
#

# Check if backports are enabled
ifdef CONFIG_BACKPORTS

# Include consistency checking integration
include backports-integration/scripts/build-integration.mk

# Backports configuration
BACKPORTS_DIR := backports-generated-6.1
BACKPORTS_BUILD_FLAGS := -j$(shell nproc)
BACKPORTS_VERSION := $(CONFIG_BACKPORTS_VERSION)

# Set build environment for backports
export KLIB_BUILD := $(objtree)
export KLIB := $(objtree)
export KERNELDIR := $(srctree)
export BACKPORT_DIR := $(srctree)/$(BACKPORTS_DIR)

# Conditional backports components based on Kconfig
backports-components-y :=
backports-components-$(CONFIG_BACKPORTS_CFG80211) += cfg80211
backports-components-$(CONFIG_BACKPORTS_MAC80211) += mac80211
backports-components-$(CONFIG_BACKPORTS_MONITOR_MODE) += monitor
backports-components-$(CONFIG_BACKPORTS_FRAME_INJECTION) += injection

# Compatibility layer components
compat-layer-y :=
compat-layer-$(CONFIG_BACKPORTS_KERNEL_COMPAT) += compat/
compat-layer-$(CONFIG_BACKPORTS_ANDROID_COMPAT) += compat/android-compat.o
compat-layer-$(CONFIG_BACKPORTS_MOBILE_PLATFORM_COMPAT) += compat/power-compat.o
compat-layer-$(CONFIG_BACKPORTS_REGULATORY_ENFORCEMENT) += compat/regulatory-compat.o

# Wireless driver components
wireless-drivers-y := $(compat-layer-y)
wireless-drivers-$(CONFIG_BACKPORTS_WIRELESS_DRIVERS) += wireless-core
wireless-drivers-$(CONFIG_BACKPORTS_ATH_DRIVERS) += ath-drivers
wireless-drivers-$(CONFIG_BACKPORTS_ATH11K) += ath11k
wireless-drivers-$(CONFIG_BACKPORTS_ATH10K) += ath10k
wireless-drivers-$(CONFIG_BACKPORTS_ATH9K) += ath9k
wireless-drivers-$(CONFIG_BACKPORTS_IWLWIFI) += iwlwifi
wireless-drivers-$(CONFIG_BACKPORTS_RT2X00) += rt2x00
wireless-drivers-$(CONFIG_BACKPORTS_RTW88) += rtw88
wireless-drivers-$(CONFIG_BACKPORTS_MT76) += mt76
wireless-drivers-$(CONFIG_BACKPORTS_RTW88) += rtw88
wireless-drivers-$(CONFIG_BACKPORTS_MT76) += mt76

# Security and monitor mode components
security-components-y :=
security-components-$(CONFIG_BACKPORTS_SECURITY_ENHANCED) += security-enhanced
security-components-$(CONFIG_BACKPORTS_MONITOR_ENHANCED) += monitor-enhanced
security-components-$(CONFIG_BACKPORTS_INJECTION_ENHANCED) += injection-enhanced
security-components-$(CONFIG_BACKPORTS_REGULATORY_ENHANCED) += regulatory-enhanced

# Combine all components
backports-all-components := $(backports-components-y) $(wireless-drivers-y) $(security-components-y)

# Main backports build target
obj-$(CONFIG_BACKPORTS) += $(BACKPORTS_DIR)/

# Wireless driver build configuration
WIRELESS_BUILD_FLAGS := $(BACKPORTS_BUILD_FLAGS)
WIRELESS_INSTALL_PATH := $(INSTALL_MOD_PATH)/lib/modules/$(KERNELRELEASE)
FIRMWARE_INSTALL_PATH := $(INSTALL_MOD_PATH)/lib/firmware

# Wireless driver source directories
ATH11K_SRC_DIR := $(src)/$(BACKPORTS_DIR)/drivers/net/wireless/ath/ath11k
ATH10K_SRC_DIR := $(src)/$(BACKPORTS_DIR)/drivers/net/wireless/ath/ath10k
ATH9K_SRC_DIR := $(src)/$(BACKPORTS_DIR)/drivers/net/wireless/ath/ath9k
IWLWIFI_SRC_DIR := $(src)/$(BACKPORTS_DIR)/drivers/net/wireless/intel/iwlwifi
RT2X00_SRC_DIR := $(src)/$(BACKPORTS_DIR)/drivers/net/wireless/ralink/rt2x00

# Firmware directories
FIRMWARE_SRC_DIR := $(src)/backports-integration/firmware
ATH11K_FW_DIR := $(FIRMWARE_SRC_DIR)/ath11k
ATH10K_FW_DIR := $(FIRMWARE_SRC_DIR)/ath10k
IWLWIFI_FW_DIR := $(FIRMWARE_SRC_DIR)/iwlwifi
RT2X00_FW_DIR := $(FIRMWARE_SRC_DIR)/rt2x00

# Build rules for backports
$(obj)/$(BACKPORTS_DIR)/:
	@echo "Building backports components: $(backports-components-y)"
	@echo "  Kernel build dir: $(KLIB_BUILD)"
	@echo "  Kernel source dir: $(KERNELDIR)"
	@echo "  Backports version: $(BACKPORTS_VERSION)"
	$(Q)if [ ! -d "$(src)/$(BACKPORTS_DIR)" ]; then \
		echo "ERROR: Backports directory $(BACKPORTS_DIR) not found"; \
		exit 1; \
	fi
	$(Q)if [ ! -f "$(src)/$(BACKPORTS_DIR)/Makefile" ]; then \
		echo "ERROR: Backports Makefile not found"; \
		exit 1; \
	fi
	$(Q)$(MAKE) -C $(src)/$(BACKPORTS_DIR) \
		KLIB_BUILD=$(KLIB_BUILD) \
		KLIB=$(KLIB) \
		KERNELDIR=$(KERNELDIR) \
		$(BACKPORTS_BUILD_FLAGS) \
		modules || { \
		echo "ERROR: Backports build failed"; \
		echo "Check $(src)/$(BACKPORTS_DIR) for build issues"; \
		exit 1; \
	}
	@echo "Backports build completed successfully"

# Wireless driver specific build targets
wireless_drivers: $(obj)/$(BACKPORTS_DIR)/
	@echo "Building wireless drivers: $(wireless-drivers-y)"
	$(Q)if [ "$(CONFIG_BACKPORTS_WIRELESS_DRIVERS)" = "y" ]; then \
		echo "Building wireless stack components..."; \
		$(MAKE) -C $(src)/$(BACKPORTS_DIR) \
			KLIB_BUILD=$(KLIB_BUILD) \
			KLIB=$(KLIB) \
			KERNELDIR=$(KERNELDIR) \
			$(WIRELESS_BUILD_FLAGS) \
			M=net/wireless modules || { \
			echo "ERROR: Wireless stack build failed"; \
			exit 1; \
		}; \
	fi
	$(Q)if [ "$(CONFIG_BACKPORTS_ATH11K)" = "y" ] && [ -d "$(ATH11K_SRC_DIR)" ]; then \
		echo "Building ath11k driver..."; \
		$(MAKE) -C $(src)/$(BACKPORTS_DIR) \
			KLIB_BUILD=$(KLIB_BUILD) \
			KLIB=$(KLIB) \
			KERNELDIR=$(KERNELDIR) \
			$(WIRELESS_BUILD_FLAGS) \
			M=drivers/net/wireless/ath/ath11k modules || { \
			echo "ERROR: ath11k build failed"; \
			exit 1; \
		}; \
	fi
	$(Q)if [ "$(CONFIG_BACKPORTS_ATH10K)" = "y" ] && [ -d "$(ATH10K_SRC_DIR)" ]; then \
		echo "Building ath10k driver..."; \
		$(MAKE) -C $(src)/$(BACKPORTS_DIR) \
			KLIB_BUILD=$(KLIB_BUILD) \
			KLIB=$(KLIB) \
			KERNELDIR=$(KERNELDIR) \
			$(WIRELESS_BUILD_FLAGS) \
			M=drivers/net/wireless/ath/ath10k modules || { \
			echo "ERROR: ath10k build failed"; \
			exit 1; \
		}; \
	fi
	$(Q)if [ "$(CONFIG_BACKPORTS_IWLWIFI)" = "y" ] && [ -d "$(IWLWIFI_SRC_DIR)" ]; then \
		echo "Building iwlwifi driver..."; \
		$(MAKE) -C $(src)/$(BACKPORTS_DIR) \
			KLIB_BUILD=$(KLIB_BUILD) \
			KLIB=$(KLIB) \
			KERNELDIR=$(KERNELDIR) \
			$(WIRELESS_BUILD_FLAGS) \
			M=drivers/net/wireless/intel/iwlwifi modules || { \
			echo "ERROR: iwlwifi build failed"; \
			exit 1; \
		}; \
	fi
	$(Q)if [ "$(CONFIG_BACKPORTS_RT2X00)" = "y" ] && [ -d "$(RT2X00_SRC_DIR)" ]; then \
		echo "Building rt2x00 driver..."; \
		$(MAKE) -C $(src)/$(BACKPORTS_DIR) \
			KLIB_BUILD=$(KLIB_BUILD) \
			KLIB=$(KLIB) \
			KERNELDIR=$(KERNELDIR) \
			$(WIRELESS_BUILD_FLAGS) \
			M=drivers/net/wireless/ralink/rt2x00 modules || { \
			echo "ERROR: rt2x00 build failed"; \
			exit 1; \
		}; \
	fi
	@echo "Wireless drivers build completed successfully"

# Installation rules
backports_install: $(obj)/$(BACKPORTS_DIR)/
	@echo "Installing backports modules..."
	@echo "  INSTALL_MOD_PATH: $(INSTALL_MOD_PATH)"
	@echo "  Module directory: $(INSTALL_MOD_PATH)/lib/modules/$(KERNELRELEASE)/backports"
	$(Q)mkdir -p $(INSTALL_MOD_PATH)/lib/modules/$(KERNELRELEASE)/backports
	$(Q)$(MAKE) -C $(src)/$(BACKPORTS_DIR) \
		KLIB_BUILD=$(KLIB_BUILD) \
		KLIB=$(KLIB) \
		INSTALL_MOD_PATH=$(INSTALL_MOD_PATH) \
		KMODDIR=backports \
		modules_install || { \
		echo "ERROR: Backports installation failed"; \
		exit 1; \
	}
	@echo "Backports modules installed successfully"

# Firmware installation rules
firmware_install:
	@echo "Installing wireless firmware..."
	@echo "  Firmware install path: $(FIRMWARE_INSTALL_PATH)"
	$(Q)mkdir -p $(FIRMWARE_INSTALL_PATH)
	$(Q)if [ "$(CONFIG_BACKPORTS_ATH11K)" = "y" ] && [ -d "$(ATH11K_FW_DIR)" ]; then \
		echo "Installing ath11k firmware..."; \
		mkdir -p $(FIRMWARE_INSTALL_PATH)/ath11k; \
		if [ -d "$(ATH11K_FW_DIR)" ]; then \
			cp -r $(ATH11K_FW_DIR)/* $(FIRMWARE_INSTALL_PATH)/ath11k/ 2>/dev/null || \
			echo "Warning: No ath11k firmware files found in $(ATH11K_FW_DIR)"; \
		fi; \
	fi
	$(Q)if [ "$(CONFIG_BACKPORTS_ATH10K)" = "y" ] && [ -d "$(ATH10K_FW_DIR)" ]; then \
		echo "Installing ath10k firmware..."; \
		mkdir -p $(FIRMWARE_INSTALL_PATH)/ath10k; \
		if [ -d "$(ATH10K_FW_DIR)" ]; then \
			cp -r $(ATH10K_FW_DIR)/* $(FIRMWARE_INSTALL_PATH)/ath10k/ 2>/dev/null || \
			echo "Warning: No ath10k firmware files found in $(ATH10K_FW_DIR)"; \
		fi; \
	fi
	$(Q)if [ "$(CONFIG_BACKPORTS_IWLWIFI)" = "y" ] && [ -d "$(IWLWIFI_FW_DIR)" ]; then \
		echo "Installing iwlwifi firmware..."; \
		if [ -d "$(IWLWIFI_FW_DIR)" ]; then \
			cp $(IWLWIFI_FW_DIR)/*.ucode $(FIRMWARE_INSTALL_PATH)/ 2>/dev/null || \
			echo "Warning: No iwlwifi firmware files found in $(IWLWIFI_FW_DIR)"; \
		fi; \
	fi
	$(Q)if [ "$(CONFIG_BACKPORTS_RT2X00)" = "y" ] && [ -d "$(RT2X00_FW_DIR)" ]; then \
		echo "Installing rt2x00 firmware..."; \
		if [ -d "$(RT2X00_FW_DIR)" ]; then \
			cp $(RT2X00_FW_DIR)/*.bin $(FIRMWARE_INSTALL_PATH)/ 2>/dev/null || \
			echo "Warning: No rt2x00 firmware files found in $(RT2X00_FW_DIR)"; \
		fi; \
	fi
	@echo "Firmware installation completed"

# Firmware download and management
firmware_download:
	@echo "Downloading wireless firmware..."
	$(Q)$(src)/backports-integration/scripts/firmware-validation-tool.py --download ath11k QCA6390 --target-dir $(FIRMWARE_SRC_DIR) || \
		echo "Warning: Failed to download ath11k QCA6390 firmware"
	$(Q)$(src)/backports-integration/scripts/firmware-validation-tool.py --download ath11k QCA6490 --target-dir $(FIRMWARE_SRC_DIR) || \
		echo "Warning: Failed to download ath11k QCA6490 firmware"
	$(Q)$(src)/backports-integration/scripts/firmware-validation-tool.py --download ath10k QCA988X --target-dir $(FIRMWARE_SRC_DIR) || \
		echo "Warning: Failed to download ath10k QCA988X firmware"
	$(Q)$(src)/backports-integration/scripts/firmware-validation-tool.py --download iwlwifi AX200 --target-dir $(FIRMWARE_SRC_DIR) || \
		echo "Warning: Failed to download iwlwifi AX200 firmware"
	@echo "Firmware download completed"

# Firmware validation
firmware_validate:
	@echo "Validating wireless firmware..."
	$(Q)if [ -f "$(src)/backports-integration/scripts/firmware-validation-tool.py" ]; then \
		python3 $(src)/backports-integration/scripts/firmware-validation-tool.py --scan || \
		echo "Warning: Firmware validation failed"; \
	else \
		echo "Warning: Firmware validation tool not found"; \
	fi

# Wireless driver installation (includes firmware)
wireless_install: backports_install firmware_install
	@echo "Installing wireless drivers..."
	$(Q)if [ "$(CONFIG_BACKPORTS_WIRELESS_DRIVERS)" = "y" ]; then \
		echo "Installing wireless stack modules..."; \
		mkdir -p $(WIRELESS_INSTALL_PATH)/backports/net/wireless; \
		find $(src)/$(BACKPORTS_DIR)/net/wireless -name "*.ko" -exec cp {} $(WIRELESS_INSTALL_PATH)/backports/net/wireless/ \; 2>/dev/null || \
		echo "Warning: No wireless stack modules found"; \
	fi
	$(Q)if [ "$(CONFIG_BACKPORTS_ATH11K)" = "y" ]; then \
		echo "Installing ath11k modules..."; \
		mkdir -p $(WIRELESS_INSTALL_PATH)/backports/drivers/net/wireless/ath/ath11k; \
		find $(ATH11K_SRC_DIR) -name "*.ko" -exec cp {} $(WIRELESS_INSTALL_PATH)/backports/drivers/net/wireless/ath/ath11k/ \; 2>/dev/null || \
		echo "Warning: No ath11k modules found"; \
	fi
	$(Q)if [ "$(CONFIG_BACKPORTS_ATH10K)" = "y" ]; then \
		echo "Installing ath10k modules..."; \
		mkdir -p $(WIRELESS_INSTALL_PATH)/backports/drivers/net/wireless/ath/ath10k; \
		find $(ATH10K_SRC_DIR) -name "*.ko" -exec cp {} $(WIRELESS_INSTALL_PATH)/backports/drivers/net/wireless/ath/ath10k/ \; 2>/dev/null || \
		echo "Warning: No ath10k modules found"; \
	fi
	$(Q)if [ "$(CONFIG_BACKPORTS_IWLWIFI)" = "y" ]; then \
		echo "Installing iwlwifi modules..."; \
		mkdir -p $(WIRELESS_INSTALL_PATH)/backports/drivers/net/wireless/intel/iwlwifi; \
		find $(IWLWIFI_SRC_DIR) -name "*.ko" -exec cp {} $(WIRELESS_INSTALL_PATH)/backports/drivers/net/wireless/intel/iwlwifi/ \; 2>/dev/null || \
		echo "Warning: No iwlwifi modules found"; \
	fi
	$(Q)if [ "$(CONFIG_BACKPORTS_RT2X00)" = "y" ]; then \
		echo "Installing rt2x00 modules..."; \
		mkdir -p $(WIRELESS_INSTALL_PATH)/backports/drivers/net/wireless/ralink/rt2x00; \
		find $(RT2X00_SRC_DIR) -name "*.ko" -exec cp {} $(WIRELESS_INSTALL_PATH)/backports/drivers/net/wireless/ralink/rt2x00/ \; 2>/dev/null || \
		echo "Warning: No rt2x00 modules found"; \
	fi
	@echo "Wireless drivers installation completed"

# Uninstallation rules
backports_uninstall:
	@echo "Uninstalling backports modules..."
	@if [ -d "$(INSTALL_MOD_PATH)/lib/modules/$(KERNELRELEASE)/backports" ]; then \
		rm -rf $(INSTALL_MOD_PATH)/lib/modules/$(KERNELRELEASE)/backports; \
		echo "Backports modules uninstalled"; \
	else \
		echo "No backports modules found to uninstall"; \
	fi

# Wireless-specific uninstallation
wireless_uninstall: backports_uninstall firmware_uninstall
	@echo "Uninstalling wireless drivers..."
	@if [ -d "$(WIRELESS_INSTALL_PATH)/backports/drivers/net/wireless" ]; then \
		rm -rf $(WIRELESS_INSTALL_PATH)/backports/drivers/net/wireless; \
		echo "Wireless driver modules uninstalled"; \
	fi
	@if [ -d "$(WIRELESS_INSTALL_PATH)/backports/net/wireless" ]; then \
		rm -rf $(WIRELESS_INSTALL_PATH)/backports/net/wireless; \
		echo "Wireless stack modules uninstalled"; \
	fi

# Firmware uninstallation
firmware_uninstall:
	@echo "Uninstalling wireless firmware..."
	@if [ -d "$(FIRMWARE_INSTALL_PATH)/ath11k" ]; then \
		rm -rf $(FIRMWARE_INSTALL_PATH)/ath11k; \
		echo "ath11k firmware uninstalled"; \
	fi
	@if [ -d "$(FIRMWARE_INSTALL_PATH)/ath10k" ]; then \
		rm -rf $(FIRMWARE_INSTALL_PATH)/ath10k; \
		echo "ath10k firmware uninstalled"; \
	fi
	@find $(FIRMWARE_INSTALL_PATH) -name "iwlwifi-*.ucode" -delete 2>/dev/null || true
	@find $(FIRMWARE_INSTALL_PATH) -name "rt*.bin" -delete 2>/dev/null || true
	@echo "Firmware uninstallation completed"

# Module dependency handling
backports_depmod: backports_install
	@echo "Updating module dependencies for backports..."
	$(Q)if [ -r System.map ]; then \
		depmod -ae -F System.map $(KERNELRELEASE); \
	elif [ -r $(objtree)/System.map ]; then \
		depmod -ae -F $(objtree)/System.map $(KERNELRELEASE); \
	else \
		depmod -A $(KERNELRELEASE); \
	fi
	@echo "Module dependencies updated"

# Clean rules
backports_clean:
	@echo "Cleaning backports..."
	$(Q)if [ -d "$(src)/$(BACKPORTS_DIR)" ]; then \
		$(MAKE) -C $(src)/$(BACKPORTS_DIR) clean; \
	else \
		echo "Backports directory not found, skipping clean"; \
	fi

# Wireless-specific clean targets
wireless_clean: backports_clean
	@echo "Cleaning wireless drivers..."
	$(Q)if [ "$(CONFIG_BACKPORTS_ATH11K)" = "y" ] && [ -d "$(ATH11K_SRC_DIR)" ]; then \
		$(MAKE) -C $(src)/$(BACKPORTS_DIR) M=drivers/net/wireless/ath/ath11k clean; \
	fi
	$(Q)if [ "$(CONFIG_BACKPORTS_ATH10K)" = "y" ] && [ -d "$(ATH10K_SRC_DIR)" ]; then \
		$(MAKE) -C $(src)/$(BACKPORTS_DIR) M=drivers/net/wireless/ath/ath10k clean; \
	fi
	$(Q)if [ "$(CONFIG_BACKPORTS_IWLWIFI)" = "y" ] && [ -d "$(IWLWIFI_SRC_DIR)" ]; then \
		$(MAKE) -C $(src)/$(BACKPORTS_DIR) M=drivers/net/wireless/intel/iwlwifi clean; \
	fi
	$(Q)if [ "$(CONFIG_BACKPORTS_RT2X00)" = "y" ] && [ -d "$(RT2X00_SRC_DIR)" ]; then \
		$(MAKE) -C $(src)/$(BACKPORTS_DIR) M=drivers/net/wireless/ralink/rt2x00 clean; \
	fi
	@echo "Wireless drivers clean completed"

# Firmware clean
firmware_clean:
	@echo "Cleaning firmware build artifacts..."
	$(Q)find $(FIRMWARE_SRC_DIR) -name "*.tmp" -delete 2>/dev/null || true
	$(Q)find $(FIRMWARE_SRC_DIR) -name "*.log" -delete 2>/dev/null || true
	@echo "Firmware clean completed"

backports_distclean: wireless_clean firmware_clean
	@echo "Dist-cleaning backports..."
	$(Q)if [ -d "$(src)/$(BACKPORTS_DIR)" ]; then \
		$(MAKE) -C $(src)/$(BACKPORTS_DIR) mrproper; \
	else \
		echo "Backports directory not found, skipping distclean"; \
	fi
	@echo "Removing backports configuration cache..."
	$(Q)rm -f $(src)/backports-integration/.config.cache
	$(Q)rm -f $(src)/backports-integration/.build.log
	$(Q)rm -f $(src)/backports-integration/.wireless.cache
	$(Q)rm -f $(src)/backports-integration/.firmware.cache

# Configuration validation
backports_validate:
	@echo "Validating backports configuration..."
	@if [ "$(CONFIG_BACKPORTS)" = "y" ] && [ "$(CONFIG_CFG80211)" = "y" ]; then \
		echo "ERROR: Cannot enable both CONFIG_BACKPORTS and CONFIG_CFG80211"; \
		exit 1; \
	fi
	@if [ "$(CONFIG_BACKPORTS)" = "y" ] && [ "$(CONFIG_MAC80211)" = "y" ]; then \
		echo "ERROR: Cannot enable both CONFIG_BACKPORTS and CONFIG_MAC80211"; \
		exit 1; \
	fi
	@echo "Backports configuration validation passed"

# Wireless-specific configuration validation
wireless_validate: backports_validate
	@echo "Validating wireless driver configuration..."
	@if [ "$(CONFIG_BACKPORTS_WIRELESS_DRIVERS)" = "y" ] && [ "$(CONFIG_BACKPORTS_CFG80211)" != "y" ]; then \
		echo "ERROR: Wireless drivers require CONFIG_BACKPORTS_CFG80211"; \
		exit 1; \
	fi
	@if [ "$(CONFIG_BACKPORTS_ATH11K)" = "y" ] && [ "$(CONFIG_BACKPORTS_MAC80211)" != "y" ]; then \
		echo "ERROR: ath11k driver requires CONFIG_BACKPORTS_MAC80211"; \
		exit 1; \
	fi
	@if [ "$(CONFIG_BACKPORTS_ATH10K)" = "y" ] && [ "$(CONFIG_BACKPORTS_MAC80211)" != "y" ]; then \
		echo "ERROR: ath10k driver requires CONFIG_BACKPORTS_MAC80211"; \
		exit 1; \
	fi
	@if [ "$(CONFIG_BACKPORTS_IWLWIFI)" = "y" ] && [ "$(CONFIG_BACKPORTS_MAC80211)" != "y" ]; then \
		echo "ERROR: iwlwifi driver requires CONFIG_BACKPORTS_MAC80211"; \
		exit 1; \
	fi
	@if [ "$(CONFIG_BACKPORTS_FRAME_INJECTION)" = "y" ] && [ "$(CONFIG_BACKPORTS_MONITOR_MODE)" != "y" ]; then \
		echo "ERROR: Frame injection requires CONFIG_BACKPORTS_MONITOR_MODE"; \
		exit 1; \
	fi
	@if [ "$(CONFIG_BACKPORTS_INJECTION_ENHANCED)" = "y" ] && [ "$(CONFIG_BACKPORTS_FRAME_INJECTION)" != "y" ]; then \
		echo "ERROR: Enhanced injection requires CONFIG_BACKPORTS_FRAME_INJECTION"; \
		exit 1; \
	fi
	@echo "Wireless configuration validation passed"

# Dependency checking
backports_deps:
	@echo "Checking backports dependencies..."
	@if [ ! -d "$(src)/$(BACKPORTS_DIR)" ]; then \
		echo "WARNING: Backports directory $(BACKPORTS_DIR) not found"; \
		echo "This is expected if backports are not yet generated"; \
	else \
		if [ ! -f "$(src)/$(BACKPORTS_DIR)/Makefile" ]; then \
			echo "ERROR: Backports Makefile not found in $(BACKPORTS_DIR)"; \
			exit 1; \
		fi; \
		echo "Backports dependencies check passed"; \
	fi

# Status reporting
backports_status:
	@echo "Backports Integration Status"
	@echo "============================"
	@echo "Configuration:"
	@echo "  CONFIG_BACKPORTS: $(CONFIG_BACKPORTS)"
	@echo "  CONFIG_BACKPORTS_CFG80211: $(CONFIG_BACKPORTS_CFG80211)"
	@echo "  CONFIG_BACKPORTS_MAC80211: $(CONFIG_BACKPORTS_MAC80211)"
	@echo "  CONFIG_BACKPORTS_MONITOR_MODE: $(CONFIG_BACKPORTS_MONITOR_MODE)"
	@echo "  CONFIG_BACKPORTS_FRAME_INJECTION: $(CONFIG_BACKPORTS_FRAME_INJECTION)"
	@echo ""
	@echo "Wireless Drivers:"
	@echo "  CONFIG_BACKPORTS_WIRELESS_DRIVERS: $(CONFIG_BACKPORTS_WIRELESS_DRIVERS)"
	@echo "  CONFIG_BACKPORTS_ATH_DRIVERS: $(CONFIG_BACKPORTS_ATH_DRIVERS)"
	@echo "  CONFIG_BACKPORTS_ATH11K: $(CONFIG_BACKPORTS_ATH11K)"
	@echo "  CONFIG_BACKPORTS_ATH10K: $(CONFIG_BACKPORTS_ATH10K)"
	@echo "  CONFIG_BACKPORTS_ATH9K: $(CONFIG_BACKPORTS_ATH9K)"
	@echo "  CONFIG_BACKPORTS_IWLWIFI: $(CONFIG_BACKPORTS_IWLWIFI)"
	@echo "  CONFIG_BACKPORTS_RT2X00: $(CONFIG_BACKPORTS_RT2X00)"
	@echo ""
	@echo "Security Features:"
	@echo "  CONFIG_BACKPORTS_SECURITY_ENHANCED: $(CONFIG_BACKPORTS_SECURITY_ENHANCED)"
	@echo "  CONFIG_BACKPORTS_MONITOR_ENHANCED: $(CONFIG_BACKPORTS_MONITOR_ENHANCED)"
	@echo "  CONFIG_BACKPORTS_INJECTION_ENHANCED: $(CONFIG_BACKPORTS_INJECTION_ENHANCED)"
	@echo "  CONFIG_BACKPORTS_REGULATORY_ENHANCED: $(CONFIG_BACKPORTS_REGULATORY_ENHANCED)"
	@echo ""
	@echo "Build Environment:"
	@echo "  KLIB_BUILD: $(KLIB_BUILD)"
	@echo "  KERNELDIR: $(KERNELDIR)"
	@echo "  BACKPORTS_DIR: $(BACKPORTS_DIR)"
	@echo "  BACKPORTS_VERSION: $(BACKPORTS_VERSION)"
	@echo "  WIRELESS_INSTALL_PATH: $(WIRELESS_INSTALL_PATH)"
	@echo "  FIRMWARE_INSTALL_PATH: $(FIRMWARE_INSTALL_PATH)"
	@echo ""
	@echo "Components:"
	@echo "  Backports: $(backports-components-y)"
	@echo "  Wireless Drivers: $(wireless-drivers-y)"
	@echo "  Security: $(security-components-y)"
	@echo "  All Components: $(backports-all-components)"

# Wireless-specific status
wireless_status: backports_status
	@echo ""
	@echo "Wireless Driver Status"
	@echo "======================"
	@if [ "$(CONFIG_BACKPORTS_ATH11K)" = "y" ]; then \
		echo "ath11k driver: ENABLED"; \
		if [ -d "$(ATH11K_SRC_DIR)" ]; then \
			echo "  Source directory: $(ATH11K_SRC_DIR) [EXISTS]"; \
		else \
			echo "  Source directory: $(ATH11K_SRC_DIR) [MISSING]"; \
		fi; \
		if [ -d "$(ATH11K_FW_DIR)" ]; then \
			echo "  Firmware directory: $(ATH11K_FW_DIR) [EXISTS]"; \
		else \
			echo "  Firmware directory: $(ATH11K_FW_DIR) [MISSING]"; \
		fi; \
	else \
		echo "ath11k driver: DISABLED"; \
	fi
	@if [ "$(CONFIG_BACKPORTS_ATH10K)" = "y" ]; then \
		echo "ath10k driver: ENABLED"; \
		if [ -d "$(ATH10K_SRC_DIR)" ]; then \
			echo "  Source directory: $(ATH10K_SRC_DIR) [EXISTS]"; \
		else \
			echo "  Source directory: $(ATH10K_SRC_DIR) [MISSING]"; \
		fi; \
		if [ -d "$(ATH10K_FW_DIR)" ]; then \
			echo "  Firmware directory: $(ATH10K_FW_DIR) [EXISTS]"; \
		else \
			echo "  Firmware directory: $(ATH10K_FW_DIR) [MISSING]"; \
		fi; \
	else \
		echo "ath10k driver: DISABLED"; \
	fi
	@if [ "$(CONFIG_BACKPORTS_IWLWIFI)" = "y" ]; then \
		echo "iwlwifi driver: ENABLED"; \
		if [ -d "$(IWLWIFI_SRC_DIR)" ]; then \
			echo "  Source directory: $(IWLWIFI_SRC_DIR) [EXISTS]"; \
		else \
			echo "  Source directory: $(IWLWIFI_SRC_DIR) [MISSING]"; \
		fi; \
		if [ -d "$(IWLWIFI_FW_DIR)" ]; then \
			echo "  Firmware directory: $(IWLWIFI_FW_DIR) [EXISTS]"; \
		else \
			echo "  Firmware directory: $(IWLWIFI_FW_DIR) [MISSING]"; \
		fi; \
	else \
		echo "iwlwifi driver: DISABLED"; \
	fi
	@if [ "$(CONFIG_BACKPORTS_RT2X00)" = "y" ]; then \
		echo "rt2x00 driver: ENABLED"; \
		if [ -d "$(RT2X00_SRC_DIR)" ]; then \
			echo "  Source directory: $(RT2X00_SRC_DIR) [EXISTS]"; \
		else \
			echo "  Source directory: $(RT2X00_SRC_DIR) [MISSING]"; \
		fi; \
		if [ -d "$(RT2X00_FW_DIR)" ]; then \
			echo "  Firmware directory: $(RT2X00_FW_DIR) [EXISTS]"; \
		else \
			echo "  Firmware directory: $(RT2X00_FW_DIR) [MISSING]"; \
		fi; \
	else \
		echo "rt2x00 driver: DISABLED"; \
	fi

# Help target
backports_help:
	@echo "Backports Integration Makefile"
	@echo "=============================="
	@echo ""
	@echo "Core backports targets:"
	@echo "  backports_install   - Install backports modules"
	@echo "  backports_uninstall - Uninstall backports modules"
	@echo "  backports_depmod    - Update module dependencies"
	@echo "  backports_clean     - Clean backports build"
	@echo "  backports_distclean - Clean backports completely"
	@echo "  backports_validate  - Validate backports configuration"
	@echo "  backports_deps      - Check backports dependencies"
	@echo "  backports_status    - Show backports status"
	@echo "  backports_help      - Show this help"
	@echo ""
	@echo "Wireless driver targets:"
	@echo "  wireless_drivers    - Build wireless drivers"
	@echo "  wireless_install    - Install wireless drivers and firmware"
	@echo "  wireless_uninstall  - Uninstall wireless drivers and firmware"
	@echo "  wireless_clean      - Clean wireless driver builds"
	@echo "  wireless_validate   - Validate wireless configuration"
	@echo "  wireless_status     - Show wireless driver status"
	@echo ""
	@echo "Firmware management targets:"
	@echo "  firmware_install    - Install wireless firmware"
	@echo "  firmware_uninstall  - Uninstall wireless firmware"
	@echo "  firmware_download   - Download missing firmware"
	@echo "  firmware_validate   - Validate firmware requirements"
	@echo "  firmware_clean      - Clean firmware build artifacts"
	@echo ""
	@echo "Integration targets (called by kernel build):"
	@echo "  modules             - Build backports modules"
	@echo "  modules_install     - Install backports modules"
	@echo "  clean               - Clean backports"
	@echo "  mrproper            - Dist-clean backports"
	@echo ""
	@echo "Configuration variables:"
	@echo "  CONFIG_BACKPORTS_WIRELESS_DRIVERS - Enable wireless drivers"
	@echo "  CONFIG_BACKPORTS_ATH11K           - Enable ath11k driver"
	@echo "  CONFIG_BACKPORTS_ATH10K           - Enable ath10k driver"
	@echo "  CONFIG_BACKPORTS_IWLWIFI          - Enable iwlwifi driver"
	@echo "  CONFIG_BACKPORTS_RT2X00           - Enable rt2x00 driver"
	@echo "  FIRMWARE_INSTALL_PATH             - Firmware installation path"
	@echo "  WIRELESS_INSTALL_PATH             - Module installation path"

# Phony targets
.PHONY: backports_install backports_uninstall backports_depmod
.PHONY: backports_clean backports_distclean backports_validate
.PHONY: backports_deps backports_status backports_help
.PHONY: wireless_drivers wireless_install wireless_uninstall wireless_clean
.PHONY: wireless_validate wireless_status
.PHONY: firmware_install firmware_uninstall firmware_download firmware_validate firmware_clean

else
# Backports not enabled - provide stub targets
backports_install backports_uninstall backports_depmod:
	@echo "Backports not enabled in configuration"

backports_clean backports_distclean:
	@echo "Backports not enabled in configuration"

backports_validate backports_deps backports_status backports_help:
	@echo "Backports not enabled in configuration"

# Wireless driver stub targets
wireless_drivers wireless_install wireless_uninstall wireless_clean:
	@echo "Backports not enabled in configuration"

wireless_validate wireless_status:
	@echo "Backports not enabled in configuration"

# Firmware stub targets
firmware_install firmware_uninstall firmware_download firmware_validate firmware_clean:
	@echo "Backports not enabled in configuration"

.PHONY: backports_install backports_uninstall backports_depmod
.PHONY: backports_clean backports_distclean backports_validate
.PHONY: backports_deps backports_status backports_help
.PHONY: wireless_drivers wireless_install wireless_uninstall wireless_clean
.PHONY: wireless_validate wireless_status
.PHONY: firmware_install firmware_uninstall firmware_download firmware_validate firmware_clean

endif # CONFIG_BACKPORTS