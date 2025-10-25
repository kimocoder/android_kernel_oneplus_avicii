# Auto-generated kernel compatibility Makefile
# Kernel version: 6.18.0-061800rc2-generic
# Generated on: Sat Oct 25 12:42:06 CEST 2025

# Kernel version variables
KERNEL_VERSION_MAJOR := 6
KERNEL_VERSION_MINOR := 18
KERNEL_VERSION_PATCH := 0
KERNEL_VERSION_CODE := 397824

# Platform detection
IS_ANDROID_KERNEL := 0
IS_MOBILE_PLATFORM := 0

# Compatibility flags
COMPAT_ANDROID_OPTIMIZED := 0
COMPAT_MOBILE_PLATFORM := 0

# Conditional compilation
ifeq ($(IS_ANDROID_KERNEL),1)
ccflags-y += -DBACKPORTS_ANDROID_KERNEL=1
endif

ifeq ($(IS_MOBILE_PLATFORM),1)
ccflags-y += -DBACKPORTS_MOBILE_PLATFORM=1
endif

# Version-specific flags
ccflags-y += -DKERNEL_VERSION_CODE=397824