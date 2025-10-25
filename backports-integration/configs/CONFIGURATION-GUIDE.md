# Wireless Configuration Templates Guide

This guide provides comprehensive information about wireless configuration templates for different use cases and deployment scenarios.

## Overview

The backports wireless system includes pre-configured templates optimized for specific use cases. Each template is carefully designed to provide the optimal balance of features, performance, and compliance for its intended scenario.

## Available Templates

### 1. Laptop/Desktop Standard (`laptop-standard.config`)

**Use Case**: Everyday wireless usage on laptops and desktop systems

**Features**:
- Standard wireless connectivity with modern drivers
- Power management optimization for battery life
- Enterprise security support (WPA2/WPA3)
- Multiple driver support (ath11k, ath10k, iwlwifi)
- Regulatory compliance enforcement
- No monitor mode or injection (security policy)

**Recommended For**:
- Personal laptops and desktops
- Business workstations
- General-purpose wireless connectivity
- Users who need reliable, standard wireless functionality

**Regulatory Notes**:
- Complies with standard regulatory requirements
- Safe for use in all jurisdictions
- No special authorizations required

### 2. Advanced Security Research (`security-research-advanced.config`)

**Use Case**: Wireless security research, penetration testing, and protocol analysis

**Features**:
- Monitor mode with radiotap headers
- Packet injection with full control (rate, sequence, power, timing)
- Multiple driver support optimized for research
- Spectral scan capabilities for interference analysis
- Advanced debugging and tracing
- Mesh networking support
- Enhanced monitoring features

**⚠️ SECURITY WARNINGS**:
- Enables security-sensitive features
- Only use in isolated test environments
- Requires proper authorization and legal compliance
- Not suitable for production environments

**⚠️ REGULATORY WARNINGS**:
- Monitor mode and injection may be restricted or prohibited
- Requires authorization in many jurisdictions
- Ensure compliance with local regulations
- Use only in authorized test environments

**Recommended For**:
- Security researchers and penetration testers
- Wireless protocol analysis
- Academic research institutions
- Authorized security testing

### 3. Mesh Networking (`mesh-networking.config`)

**Use Case**: 802.11s mesh networking deployments

**Features**:
- 802.11s mesh networking with advanced features
- Multi-hop routing optimization
- Mesh security with SAE authentication
- Power save mechanisms for mesh nodes
- Quality of Service support
- Advanced path selection algorithms
- Enhanced mesh forwarding

**Recommended For**:
- IoT mesh networks
- Smart city deployments
- Distributed sensor networks
- Community wireless networks
- Disaster recovery networks

**Regulatory Notes**:
- Mesh networking generally allowed in most regions
- Standard power limits and channel restrictions apply
- Check local regulations for outdoor deployments

### 4. Enterprise Wireless (`enterprise-wireless.config`)

**Use Case**: Corporate and enterprise wireless deployments

**Features**:
- WPA3 Enterprise support
- 802.1X authentication integration
- Advanced security features and policies
- Enterprise power management
- SNMP monitoring support
- Quality of Service (QoS) management
- VLAN support for network segmentation
- Strict regulatory compliance

**Security Policy**:
- Monitor mode and injection disabled for security
- Enterprise-grade security enforcement
- Compliance with corporate security policies

**Recommended For**:
- Corporate networks
- Enterprise environments
- Managed wireless deployments
- Organizations with strict security requirements

**Requirements**:
- Enterprise wireless infrastructure
- 802.1X authentication server
- Network management system
- Quality of Service support

### 5. Android Mobile (`android-mobile.config`)

**Use Case**: Android mobile devices and tablets

**Features**:
- Android framework integration
- Mobile power optimization and battery management
- Android security model integration
- Vendor driver compatibility (Qualcomm, Broadcom)
- Android wakelock support
- Android property system integration
- Location permission integration

**Android-Specific**:
- Integrates with Android power management
- Supports Android security policies
- Compatible with Android kernel 4.19+
- Vendor driver coexistence

**Security Policy**:
- Monitor mode and injection disabled (Android security policy)
- Android permission system enforcement
- SELinux policy compliance

**Recommended For**:
- Android smartphones and tablets
- Android-based embedded devices
- Mobile platforms with Android kernel

### 6. Embedded IoT (`embedded-iot.config`)

**Use Case**: Resource-constrained embedded IoT devices

**Features**:
- Minimal resource usage and memory footprint
- Ultra-low power consumption
- Essential wireless features only
- Optimized for constrained devices
- Basic security features
- No debugging or advanced features (resource saving)

**Optimization**:
- Aggressive power management
- Minimal kernel configuration
- Reduced feature set
- Memory and CPU optimization

**Recommended For**:
- IoT sensors and devices
- Embedded systems with limited resources
- Battery-powered devices
- Microcontroller-based systems

**Limitations**:
- Limited feature set for resource constraints
- No debugging or monitoring capabilities
- Basic security features only

### 7. Monitor Mode Only (`monitor-only.config`)

**Use Case**: Passive wireless monitoring and packet capture

**Features**:
- Monitor mode with radiotap headers
- Passive packet capture capabilities
- Channel switching support
- Spectral scan capabilities
- Enhanced monitoring features
- **No transmission capabilities** (receive only)

**⚠️ REGULATORY NOTES**:
- Monitor mode may require authorization in some jurisdictions
- Passive monitoring generally more permissive than injection
- No transmission reduces regulatory concerns
- Check local regulations for monitoring activities

**Recommended For**:
- Network monitoring and analysis
- Passive wireless surveys
- Spectrum analysis
- Compliance monitoring
- Educational purposes

### 8. USB Wireless Adapters (`usb-adapters.config`)

**Use Case**: External USB wireless adapters with modern chipsets

**Features**:
- RTW88 Realtek USB adapter support (RTL8822B/C, RTL8821C, RTL8723D)
- MT76 MediaTek USB adapter support (MT7601U, MT7610U, MT7612U, MT7663U, MT7921U)
- Legacy RT2X00 USB adapter support for older devices
- Monitor mode and packet injection capabilities
- Mesh networking support
- Advanced debugging and analysis tools
- Multi-chipset firmware management

**⚠️ SECURITY WARNINGS**:
- Enables monitor mode and packet injection
- USB adapter performance may vary by chipset and USB version
- Some features may require specific firmware versions

**⚠️ REGULATORY WARNINGS**:
- USB adapters subject to same regulatory restrictions as internal cards
- Monitor mode and injection authorization may be required
- Check adapter certification for your region
- External antennas may have additional restrictions

**Recommended For**:
- Security research with USB adapters
- Wireless testing and development
- Systems without internal wireless cards
- Multi-adapter setups for research
- USB adapter compatibility testing

**Requirements**:
- USB wireless adapter with supported chipset (RTW88, MT76, or RT2X00)
- USB 2.0 or USB 3.0 port (USB 3.0 recommended for performance)
- Compatible firmware files for the specific chipset
- Root privileges for monitor mode operations

## Template Selection Guide

### By Use Case

| Use Case | Recommended Template | Alternative |
|----------|---------------------|-------------|
| Personal laptop/desktop | `laptop-standard` | `enterprise-wireless` |
| Security research | `security-research-advanced` | `monitor-only` |
| Mesh networking | `mesh-networking` | `laptop-standard` |
| Corporate environment | `enterprise-wireless` | `laptop-standard` |
| Android device | `android-mobile` | `embedded-iot` |
| IoT device | `embedded-iot` | `android-mobile` |
| Passive monitoring | `monitor-only` | `security-research-advanced` |
| USB wireless adapters | `usb-adapters` | `security-research-advanced` |

### By Regulatory Environment

| Regulatory Environment | Suitable Templates |
|----------------------|-------------------|
| Strict (e.g., Japan, China) | `laptop-standard`, `enterprise-wireless`, `android-mobile`, `embedded-iot` |
| Standard (e.g., US, Canada) | All templates (with proper authorization for research) |
| Permissive research environment | `security-research-advanced`, `monitor-only` |
| Enterprise/Corporate | `enterprise-wireless`, `laptop-standard` |

### By Hardware Platform

| Platform Type | Recommended Templates |
|---------------|---------------------|
| x86/x64 Laptop | `laptop-standard`, `enterprise-wireless` |
| ARM Mobile | `android-mobile`, `embedded-iot` |
| Embedded ARM | `embedded-iot`, `mesh-networking` |
| Research Hardware | `security-research-advanced`, `monitor-only` |

## Using Templates

### Quick Start

1. **List available templates**:
   ```bash
   ./config-template-manager.py list
   ```

2. **Show template details**:
   ```bash
   ./config-template-manager.py show laptop-standard
   ```

3. **Apply a template**:
   ```bash
   ./config-template-manager.py apply laptop-standard
   ```

### Advanced Usage

1. **Apply to specific file**:
   ```bash
   ./config-template-manager.py apply laptop-standard --output my-config.config
   ```

2. **Customize a template**:
   ```bash
   ./config-template-manager.py customize laptop-standard --customize '{"BACKPORTS_DEBUG": "y", "BACKPORTS_MONITOR_MODE": "y"}'
   ```

3. **Validate a template**:
   ```bash
   ./config-template-manager.py validate laptop-standard.config --verbose
   ```

### Integration with Build System

Templates can be used with the existing build system:

```bash
# Apply template and build
./config-template-manager.py apply laptop-standard
make wireless_drivers

# Use with kconfig helper
./kconfig-helper.sh laptop-standard
```

## Customization Guidelines

### Safe Customizations

These options can generally be safely modified:

- `CONFIG_BACKPORTS_DEBUG` - Enable/disable debugging
- `CONFIG_BACKPORTS_STATISTICS` - Enable/disable statistics
- Driver-specific options (e.g., `CONFIG_BACKPORTS_ATH11K_DEBUGFS`)
- Power management options

### Dangerous Customizations

⚠️ **Be careful when modifying these options**:

- `CONFIG_BACKPORTS_MONITOR_MODE` - May have regulatory implications
- `CONFIG_BACKPORTS_FRAME_INJECTION` - May be prohibited in some regions
- `CONFIG_BACKPORTS_REGULATORY_ENFORCEMENT` - Disabling may violate regulations
- Core wireless stack options (`CONFIG_BACKPORTS_CFG80211`, `CONFIG_BACKPORTS_MAC80211`)

### Regulatory Considerations

When customizing templates:

1. **Always maintain regulatory compliance**
2. **Check local regulations** before enabling monitor mode or injection
3. **Obtain proper authorization** for security research features
4. **Use appropriate templates** for your jurisdiction
5. **Document any modifications** for compliance auditing

## Troubleshooting

### Common Issues

1. **Template not found**:
   - Check template name with `./config-template-manager.py list`
   - Ensure template file exists in `configs/` directory

2. **Validation errors**:
   - Use `./config-template-manager.py validate <template>` to check
   - Review error messages and fix configuration conflicts

3. **Build failures**:
   - Ensure all required kernel options are enabled
   - Check for missing dependencies
   - Validate template before building

4. **Regulatory compliance issues**:
   - Review template regulatory notes
   - Ensure proper authorization for restricted features
   - Consider using more restrictive template

### Getting Help

1. **Check template details**: `./config-template-manager.py show <template>`
2. **Validate configuration**: `./config-template-manager.py validate <file>`
3. **Generate report**: `./config-template-manager.py report`
4. **Review documentation**: Check README files and regulatory guides

## Contributing

When creating new templates:

1. **Follow naming convention**: `use-case-variant.config`
2. **Include comprehensive comments** in the template file
3. **Add template to manager database** in `config-template-manager.py`
4. **Test thoroughly** on target platform
5. **Document regulatory considerations**
6. **Validate template** before submission

## Legal and Regulatory Disclaimer

⚠️ **Important Legal Notice**:

- **Monitor mode and packet injection** may be restricted or prohibited in your jurisdiction
- **Obtain proper authorization** before using security research features
- **Ensure compliance** with local regulations and laws
- **Use only in authorized environments** for security testing
- **The authors are not responsible** for misuse of these templates
- **Check local regulations** before deployment

Always consult with legal counsel and regulatory authorities when deploying wireless systems with advanced capabilities.