# Backports Compatibility Layer Makefile

# Compatibility layer objects
backports-compat-y := compat.o

# Android compatibility (conditional)
ifeq ($(CONFIG_BACKPORTS_ANDROID),y)
backports-compat-y += android-compat.o
endif

# Power management compatibility (conditional)
ifeq ($(CONFIG_BACKPORTS_MOBILE_PLATFORM),y)
backports-compat-y += power-compat.o
endif

# Regulatory compatibility (always included)
backports-compat-y += regulatory-compat.o

# Build as module or built-in
obj-$(CONFIG_BACKPORTS) += backports-compat.o

# Compiler flags
ccflags-y += -I$(src)/../include
ccflags-y += -DBACKPORTS_COMPAT_BUILD

# Android-specific flags
ifeq ($(CONFIG_ANDROID),y)
ccflags-y += -DCONFIG_ANDROID
endif

# Mobile platform detection
ifeq ($(CONFIG_ARM),y)
ccflags-y += -DCONFIG_ARM
endif

ifeq ($(CONFIG_ARM64),y)
ccflags-y += -DCONFIG_ARM64
endif

# Debug flags
ifeq ($(CONFIG_BACKPORTS_DEBUG),y)
ccflags-y += -DDEBUG
endif

# Version information
BACKPORTS_COMPAT_VERSION := $(shell date +%Y%m%d)
ccflags-y += -DBACKPORTS_COMPAT_VERSION_CODE=$(BACKPORTS_COMPAT_VERSION)

# Clean targets
clean-files := *.o *.ko *.mod.c *.mod.o *.symvers modules.order

# Help target
help:
	@echo "Backports Compatibility Layer Build Targets:"
	@echo "  all          - Build compatibility layer"
	@echo "  clean        - Clean build artifacts"
	@echo "  install      - Install compatibility layer"
	@echo ""
	@echo "Configuration Options:"
	@echo "  CONFIG_BACKPORTS_ANDROID=y        - Enable Android compatibility"
	@echo "  CONFIG_BACKPORTS_MOBILE_PLATFORM=y - Enable mobile platform optimizations"
	@echo "  CONFIG_BACKPORTS_DEBUG=y          - Enable debug output"

.PHONY: help clean