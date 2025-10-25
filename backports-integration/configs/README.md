# Backports Configuration Templates

This directory contains configuration templates for common backports use cases.

## Templates

- `basic.config` - Basic backports configuration with cfg80211 and mac80211
- `monitor.config` - Configuration with monitor mode support
- `injection.config` - Full configuration with frame injection capabilities
- `android.config` - Android-specific configuration template
- `debug.config` - Development configuration with debugging enabled

## Usage

These templates can be used as starting points for backports configuration:

```bash
# Copy a template to your kernel configuration
cp backports-integration/configs/monitor.config .config-backports

# Merge with existing kernel configuration
scripts/kconfig/merge_config.sh .config .config-backports
```