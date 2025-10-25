#
# Build Integration Makefile
#
# This file provides build integration utilities and consistency checking
# for the backports build system.
#

# Build integration version
BUILD_INTEGRATION_VERSION := 1.0

# Consistency checking
define check_backports_consistency
	@echo "Checking backports consistency..."
	@if [ "$(CONFIG_BACKPORTS)" = "y" ] && [ "$(CONFIG_CFG80211)" = "y" ]; then \
		echo "ERROR: CONFIG_BACKPORTS and CONFIG_CFG80211 cannot both be enabled"; \
		exit 1; \
	fi
	@if [ "$(CONFIG_BACKPORTS)" = "y" ] && [ "$(CONFIG_MAC80211)" = "y" ]; then \
		echo "ERROR: CONFIG_BACKPORTS and CONFIG_MAC80211 cannot both be enabled"; \
		exit 1; \
	fi
	@echo "Backports consistency check passed"
endef

# Wireless driver consistency checking
define check_wireless_consistency
	@echo "Checking wireless driver consistency..."
	@if [ "$(CONFIG_BACKPORTS_WIRELESS_DRIVERS)" = "y" ] && [ "$(CONFIG_BACKPORTS_CFG80211)" != "y" ]; then \
		echo "WARNING: Wireless drivers enabled but CONFIG_BACKPORTS_CFG80211 not set"; \
	fi
	@if [ "$(CONFIG_BACKPORTS_ATH11K)" = "y" ] && [ "$(CONFIG_BACKPORTS_MAC80211)" != "y" ]; then \
		echo "WARNING: ath11k enabled but CONFIG_BACKPORTS_MAC80211 not set"; \
	fi
	@echo "Wireless consistency check passed"
endef

# Build environment validation
define validate_build_env
	@echo "Validating build environment..."
	@if [ -z "$(KERNELDIR)" ]; then \
		echo "ERROR: KERNELDIR not set"; \
		exit 1; \
	fi
	@if [ -z "$(KLIB_BUILD)" ]; then \
		echo "ERROR: KLIB_BUILD not set"; \
		exit 1; \
	fi
	@echo "Build environment validation passed"
endef

# Integration targets
backports_consistency_check:
	$(call check_backports_consistency)
	$(call check_wireless_consistency)

backports_env_validate:
	$(call validate_build_env)

# Phony targets
.PHONY: backports_consistency_check backports_env_validate