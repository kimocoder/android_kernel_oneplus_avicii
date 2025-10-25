# Wireless Driver Management Scripts

This directory contains comprehensive wireless driver management tools for the backports integration system. These scripts provide automated driver selection, configuration, firmware management, conflict resolution, and regulatory compliance checking.

## Overview

The wireless management system consists of several interconnected components:

1. **Driver Management** - Selection, installation, and configuration of wireless drivers
2. **Firmware Automation** - Automated firmware download, validation, and installation
3. **Conflict Resolution** - Detection and resolution of driver conflicts
4. **Regulatory Compliance** - Compliance checking and regulatory domain management
5. **Configuration Management** - Interactive driver configuration and setup

## Main Scripts

### 1. Wireless Management CLI (`wireless-management-cli.py`)

The main command-line interface for all wireless driver management operations.

```bash
# List available drivers
./wireless-management-cli.py list

# Install a specific driver
./wireless-management-cli.py install ath11k --chipset QCA6390

# Manage firmware
./wireless-management-cli.py firmware ath11k download --chipset QCA6390

# Check for conflicts
./wireless-management-cli.py conflicts detect

# Check regulatory compliance
./wireless-management-cli.py regulatory check ath11k --country US

# Generate comprehensive report
./wireless-management-cli.py report --output wireless-report.txt
```

### 2. Driver Configurator (`wireless-driver-configurator.py`)

Interactive driver configuration wizard for guided setup.

```bash
# Run interactive setup
./wireless-driver-configurator.py setup

# Load existing configuration
./wireless-driver-configurator.py load --config driver-config.json

# List available configurations
./wireless-driver-configurator.py list
```

### 3. Setup Script (`setup-wireless-drivers.sh`)

Comprehensive automated setup script for complete wireless driver installation with interactive guidance.

```bash
# Interactive setup with hardware detection
./setup-wireless-drivers.sh

# Automated setup for specific driver
./setup-wireless-drivers.sh --driver ath11k --chipset QCA6390 --regulatory US --auto

# Security research setup
./setup-wireless-drivers.sh --use-case security_research --driver ath11k --auto

# Skip build step (use pre-built drivers)
./setup-wireless-drivers.sh --driver iwlwifi --skip-build

# Force installation even with conflicts
./setup-wireless-drivers.sh --driver ath11k --force --auto
```

### 4. Regulatory Compliance Checker (`regulatory-compliance-checker.py`)

Comprehensive regulatory compliance validation.

```bash
# Check driver compliance
./regulatory-compliance-checker.py check --driver ath11k --domain US

# Validate frequency and power
./regulatory-compliance-checker.py frequency --domain EU --frequency 5180 --power 23

# Generate compliance report
./regulatory-compliance-checker.py report --output compliance-report.json

# Validate current setup
./regulatory-compliance-checker.py validate
```

### 5. Regulatory Manager (`regulatory-manager.py`)

Advanced regulatory database and domain management.

```bash
# Check regulatory database status
./regulatory-manager.py status

# Download regulatory database
sudo ./regulatory-manager.py download

# Set regulatory domain
sudo ./regulatory-manager.py set --domain US

# List available channels
./regulatory-manager.py channels --domain US --band 5

# Validate frequency/power combination
./regulatory-manager.py validate --domain EU --frequency 5180 --power 23

# Generate regulatory report
./regulatory-manager.py report --output regulatory-report.txt
```

## Component Scripts

### Driver Management (`wireless-driver-manager.py`)

Core driver management functionality including:
- Driver detection and status checking
- Driver installation and configuration
- Dependency resolution
- Conflict detection
- Regulatory compliance checking

### Firmware Automation (`firmware-automation.py`)

Automated firmware management including:
- Firmware download from multiple sources
- Checksum validation
- Installation and verification
- Cleanup and maintenance

### Conflict Resolution (`wireless-conflict-resolver.py`)

Driver conflict detection and resolution including:
- Symbol conflict detection
- Resource conflict analysis
- Automatic conflict resolution
- Resolution strategy implementation

### Regulatory Manager (`regulatory-manager.py`)

Regulatory database and compliance management including:
- Regulatory database management
- Country-specific rules
- Frequency and power validation
- Channel availability checking

## Usage Examples

### Basic Driver Installation

```bash
# 1. Run interactive setup
./setup-wireless-drivers.sh

# 2. Or use CLI for specific driver
./wireless-management-cli.py install ath11k --chipset QCA6390 --check-conflicts

# 3. Verify installation
./wireless-management-cli.py list --status loaded
```

### Firmware Management

```bash
# Download firmware for ath11k
./wireless-management-cli.py firmware ath11k download --chipset QCA6390

# Validate firmware installation
./wireless-management-cli.py firmware ath11k validate --chipset QCA6390

# Install firmware if missing
./wireless-management-cli.py firmware ath11k install --chipset QCA6390
```

### Conflict Resolution

```bash
# Detect conflicts
./wireless-management-cli.py conflicts detect

# Resolve conflicts automatically
./wireless-management-cli.py conflicts resolve

# Generate conflict report
./wireless-management-cli.py conflicts report --output conflicts.txt
```

### Regulatory Compliance

```bash
# Check compliance for US domain
./regulatory-compliance-checker.py check --driver ath11k --domain US

# Validate current setup
./regulatory-compliance-checker.py validate

# Check available channels
./wireless-management-cli.py regulatory channels --country US --band 5
```

## Configuration Files and Templates

### Configuration Templates (`configs/*.config`)

Pre-built configuration templates for common wireless use cases:

#### Standard Use Cases
- **`laptop-standard.config`** - Standard laptop/desktop configuration
- **`android-mobile.config`** - Android mobile device optimization
- **`embedded-iot.config`** - Minimal IoT device configuration
- **`enterprise-wireless.config`** - Enterprise-grade wireless setup

#### Specialized Use Cases
- **`security-research-advanced.config`** - Advanced security research with monitor mode and injection
- **`monitor-only.config`** - Passive monitoring without transmission capabilities
- **`mesh-networking.config`** - 802.11s mesh networking configuration

#### Template Management
```bash
# List available templates
./config-template-manager.py list

# Show template details
./config-template-manager.py show laptop-standard

# Apply a template
./config-template-manager.py apply laptop-standard --output .config

# Customize a template
./config-template-manager.py customize laptop-standard --customize '{"BACKPORTS_DEBUG": "y"}'

# Validate a template
./config-template-manager.py validate laptop-standard.config
```

### Driver Configuration (`configs/wireless-driver-config.json`)

Main driver configuration file created by the configurator:

```json
{
  "use_case": "laptop",
  "driver": "ath11k",
  "chipset": "QCA6390",
  "features": ["monitor_mode", "mesh_networking"],
  "regulatory_domain": "US"
}
```

### Kconfig Settings (`configs/<driver>.config`)

Generated Kconfig settings for each driver:

```
CONFIG_BACKPORTS=y
CONFIG_BACKPORTS_CFG80211=y
CONFIG_BACKPORTS_MAC80211=y
CONFIG_BACKPORTS_ATH11K=y
CONFIG_BACKPORTS_ATH11K_PCI=y
```

## Supported Drivers

### ath11k (Qualcomm Atheros 11ac/11ax)
- **Chipsets**: QCA6390, QCA6490, WCN6855, QCN9074
- **Features**: Monitor mode, packet injection, mesh networking, WiFi 6/6E
- **Use Cases**: Modern laptops, desktops, research

### ath10k (Qualcomm Atheros 11ac)
- **Chipsets**: QCA988X, QCA6174, QCA9377, QCA4019
- **Features**: Monitor mode, packet injection, mesh networking
- **Use Cases**: Older laptops, desktops, embedded systems

### iwlwifi (Intel Wireless)
- **Chipsets**: AX200, AX210, AC9560, AC8265
- **Features**: Power management, enterprise security
- **Use Cases**: Intel-based laptops, enterprise environments

### rt2x00 (Ralink/MediaTek Legacy)
- **Chipsets**: RT3070, RT5370, RT2800
- **Features**: Monitor mode, packet injection
- **Use Cases**: USB adapters, research, embedded systems

### rtw88 (Realtek RTW88)
- **Chipsets**: RTL8822B, RTL8822C, RTL8821C, RTL8723D
- **Features**: Monitor mode, packet injection, 802.11ac support
- **Use Cases**: USB/PCIe adapters, laptops, research

### mt76 (MediaTek MT76)
- **Chipsets**: MT7601U, MT7610U, MT7612U, MT7663U, MT7921U
- **Features**: Monitor mode, packet injection, Wi-Fi 6 support (MT7921U)
- **Use Cases**: USB adapters, modern devices, research

## Regulatory Domains

### Supported Domains
- **US**: United States (FCC) - Full feature support
- **EU**: European Union (ETSI) - Packet injection restricted
- **JP**: Japan (MKK) - Monitor mode requires authorization
- **CN**: China - Limited frequency bands, restricted features
- **CA**: Canada - Similar to US with some restrictions
- **AU**: Australia - Similar to EU regulations

### Compliance Features
- Frequency band validation
- Power limit enforcement
- Feature restriction checking
- DFS (radar detection) requirements
- Regulatory database management

## Troubleshooting

### Common Issues

1. **Driver not loading**
   ```bash
   # Check for conflicts
   ./wireless-management-cli.py conflicts detect
   
   # Verify firmware
   ./wireless-management-cli.py firmware <driver> validate
   
   # Check dependencies
   lsmod | grep cfg80211
   ```

2. **Firmware missing**
   ```bash
   # Download firmware
   ./wireless-management-cli.py firmware <driver> download
   
   # Install firmware package
   sudo apt install linux-firmware  # Ubuntu/Debian
   sudo dnf install linux-firmware  # Fedora
   ```

3. **Regulatory issues**
   ```bash
   # Check current domain
   iw reg get
   
   # Set regulatory domain
   sudo iw reg set US
   
   # Validate compliance
   ./regulatory-compliance-checker.py validate
   ```

4. **Build failures**
   ```bash
   # Check requirements
   ./setup-wireless-drivers.sh --help
   
   # Install kernel headers
   sudo apt install linux-headers-$(uname -r)
   
   # Clean and rebuild
   make -C backports-integration clean
   make -C backports-integration wireless_drivers
   ```

### Debug Mode

Enable verbose output for debugging:

```bash
# Verbose driver listing
./wireless-management-cli.py list --verbose

# Detailed compliance check
./regulatory-compliance-checker.py check --driver ath11k --domain US --verbose

# Comprehensive report
./wireless-management-cli.py report --output debug-report.txt
```

## Integration with Build System

The wireless management scripts integrate with the existing Makefile:

```makefile
# Build wireless drivers
make wireless_drivers

# Install wireless drivers
make wireless_install

# Clean wireless drivers
make wireless_clean

# Run wireless tests
make wireless_test
```

## Security Considerations

### Monitor Mode and Packet Injection
- Ensure proper authorization before enabling monitor mode
- Packet injection must comply with local regulations
- Use only in authorized environments (labs, test networks)
- Respect privacy laws and regulations

### Regulatory Compliance
- Always set correct regulatory domain
- Verify power limits and channel restrictions
- Obtain necessary authorizations for restricted features
- Regular compliance validation recommended

### Firmware Security
- Verify firmware checksums when available
- Use official firmware sources only
- Keep firmware updated for security patches
- Monitor for firmware-related security advisories

## Contributing

When adding new drivers or features:

1. Update driver database in `wireless-driver-manager.py`
2. Add regulatory rules in `regulatory-compliance-checker.py`
3. Update conflict resolution rules in `wireless-conflict-resolver.py`
4. Add firmware information in `firmware-automation.py`
5. Update this documentation

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Generate a comprehensive report: `./wireless-management-cli.py report`
3. Review logs in `/var/log/kern.log` for driver issues
4. Check regulatory compliance: `./regulatory-compliance-checker.py validate`

## License

These scripts are part of the backports integration system and follow the same licensing terms as the main project.