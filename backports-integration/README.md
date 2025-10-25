# Backports Kconfig Integration

This directory contains the complete integration of Linux kernel backports into the OnePlus Avicii kernel's Kconfig system.

## Overview

The backports integration provides modern wireless stack functionality (cfg80211/mac80211 from kernel 6.1) to the older kernel 4.19 base through the standard kernel configuration system.

## Directory Structure

```
backports-integration/
├── Kconfig                 # Main backports Kconfig file
├── Makefile               # Build system integration
├── scripts/               # Validation and helper scripts
├── configs/               # Configuration templates
├── patches/               # Integration patches
└── README.md             # This file
```

## Features

- **Seamless Integration**: Configure backports through menuconfig/xconfig
- **Dependency Management**: Automatic resolution of dependencies and conflicts
- **Build System Integration**: Automatic building as part of kernel compilation
- **Android Compatibility**: Support for Android kernel 4.19 environment
- **Security Features**: Monitor mode and frame injection capabilities
- **Validation**: Comprehensive configuration validation and error handling

## Quick Start

1. **Enable backports in kernel configuration:**
   ```bash
   make menuconfig
   # Navigate to: Networking support -> Wireless -> Enable Linux Kernel Backports
   ```

2. **Configure desired features:**
   - cfg80211 wireless configuration API
   - mac80211 networking stack
   - Monitor mode support (optional)
   - Frame injection support (optional)

3. **Build the kernel:**
   ```bash
   make -j$(nproc)
   ```

4. **Install modules:**
   ```bash
   make modules_install
   ```

## Configuration Options

### Core Components
- `CONFIG_BACKPORTS` - Enable backports system
- `CONFIG_BACKPORTS_CFG80211` - cfg80211 wireless configuration API
- `CONFIG_BACKPORTS_MAC80211` - mac80211 networking stack

### Advanced Features
- `CONFIG_BACKPORTS_MONITOR_MODE` - Monitor mode support
- `CONFIG_BACKPORTS_FRAME_INJECTION` - Frame injection capabilities
- `CONFIG_BACKPORTS_DEBUG` - Debugging and diagnostic features

### Android Support
- `CONFIG_BACKPORTS_ANDROID` - Android-specific adaptations
- `CONFIG_BACKPORTS_VENDOR_COMPAT` - Vendor driver compatibility
- `CONFIG_BACKPORTS_SECURITY_ANDROID` - Android security integration

## Requirements

- Linux kernel 4.19 or newer
- Existing backports-generated-6.1 directory
- Standard kernel build environment
- For Android: Android kernel build system

## Troubleshooting

See `scripts/` directory for validation and troubleshooting tools:
- Run `scripts/validate-backports-config.py` to check configuration
- Use `scripts/check-wireless-conflicts.sh` to detect driver conflicts
- Check `scripts/backports-error-recovery.sh` for error recovery

## Security Considerations

When enabling frame injection and monitor mode:
- Ensure proper security measures are in place
- Understand the security implications
- Follow responsible disclosure practices
- Comply with local regulations and laws

## Support

For issues and questions:
1. Check the troubleshooting scripts in `scripts/`
2. Review configuration templates in `configs/`
3. Examine integration patches in `patches/`
4. Consult the main backports documentation