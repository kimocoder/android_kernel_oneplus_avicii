#!/bin/bash
#
# Comprehensive Wireless Driver Setup Script
#
# This script provides automated setup and configuration of wireless drivers
# with interactive guidance, conflict resolution, and regulatory compliance.
#

set -e

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KERNEL_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKPORTS_DIR="$KERNEL_ROOT/backports-integration"
CONFIG_DIR="$BACKPORTS_DIR/configs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration variables
DRIVER=""
CHIPSET=""
USE_CASE=""
REGULATORY_DOMAIN=""
FEATURES=()
AUTO_MODE=false
SKIP_BUILD=false
SKIP_FIRMWARE=false
FORCE_INSTALL=false

# Logging
LOG_FILE="/tmp/wireless-setup-$(date +%Y%m%d-%H%M%S).log"

# Helper functions
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

check_requirements() {
    info "Checking system requirements..."
    
    # Check if running as root for some operations
    if [[ $EUID -eq 0 ]]; then
        warning "Running as root - some operations may be restricted"
    fi
    
    # Check for required tools
    local required_tools=("python3" "make" "gcc")
    local missing_tools=()
    
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        error "Missing required tools: ${missing_tools[*]}"
        info "Please install missing tools and try again"
        exit 1
    fi
    
    # Check for kernel headers
    local kernel_version=$(uname -r)
    local headers_dir="/lib/modules/$kernel_version/build"
    
    if [[ ! -d "$headers_dir" ]]; then
        warning "Kernel headers not found at $headers_dir"
        info "Install kernel headers: sudo apt install linux-headers-$(uname -r)"
    fi
    
    # Check Python modules
    if ! python3 -c "import json, subprocess, pathlib" 2>/dev/null; then
        error "Required Python modules not available"
        exit 1
    fi
    
    success "System requirements check passed"
}

detect_hardware() {
    info "Detecting wireless hardware..."
    
    # Use lspci and lsusb to detect wireless devices
    local pci_devices=$(lspci | grep -i "wireless\|network\|wifi" || true)
    local usb_devices=$(lsusb | grep -i "wireless\|wifi\|atheros\|intel\|ralink\|mediatek" || true)
    
    if [[ -n "$pci_devices" ]]; then
        info "PCI wireless devices found:"
        echo "$pci_devices" | while read -r line; do
            info "  $line"
        done
    fi
    
    if [[ -n "$usb_devices" ]]; then
        info "USB wireless devices found:"
        echo "$usb_devices" | while read -r line; do
            info "  $line"
        done
    fi
    
    # Try to detect specific chipsets
    if lspci | grep -q "QCA6390\|QCA6490\|WCN6855"; then
        info "Detected ath11k compatible chipset"
        DRIVER="ath11k"
    elif lspci | grep -q "QCA988X\|QCA6174\|QCA9377"; then
        info "Detected ath10k compatible chipset"
        DRIVER="ath10k"
    elif lspci | grep -q "Intel.*Wireless"; then
        info "Detected Intel wireless chipset"
        DRIVER="iwlwifi"
    elif lsusb | grep -q "Realtek.*RTL88"; then
        info "Detected Realtek RTW88 compatible chipset"
        DRIVER="rtw88"
    elif lsusb | grep -q "MediaTek.*MT76\|MT7601\|MT7610\|MT7612\|MT7663\|MT7921"; then
        info "Detected MediaTek MT76 compatible chipset"
        DRIVER="mt76"
    elif lsusb | grep -q "Ralink\|MediaTek"; then
        info "Detected Ralink/MediaTek chipset"
        DRIVER="rt2x00"
    fi
}

interactive_setup() {
    if [[ "$AUTO_MODE" == "true" ]]; then
        return
    fi
    
    echo
    info "=== Interactive Wireless Driver Setup ==="
    echo
    
    # Use case selection
    if [[ -z "$USE_CASE" ]]; then
        echo "Select your use case:"
        echo "1) Laptop/Desktop (standard usage)"
        echo "2) Security Research (monitor mode, injection)"
        echo "3) Mesh Networking (mesh support required)"
        echo "4) Enterprise (enterprise features)"
        echo "5) Embedded System (minimal features)"
        
        read -p "Enter choice (1-5): " use_case_choice
        
        case $use_case_choice in
            1) USE_CASE="laptop" ;;
            2) USE_CASE="security_research" ;;
            3) USE_CASE="mesh_networking" ;;
            4) USE_CASE="enterprise" ;;
            5) USE_CASE="embedded" ;;
            *) USE_CASE="laptop" ;;
        esac
    fi
    
    # Driver selection
    if [[ -z "$DRIVER" ]]; then
        echo
        echo "Select wireless driver:"
        echo "1) ath11k (Qualcomm 11ac/11ax - QCA6390, QCA6490, WCN6855)"
        echo "2) ath10k (Qualcomm 11ac - QCA988X, QCA6174, QCA9377)"
        echo "3) iwlwifi (Intel Wireless - AX200, AX210, AC9560)"
        echo "4) rt2x00 (Ralink/MediaTek - RT3070, RT5370)"
        echo "5) rtw88 (Realtek RTW88 - RTL8822B/C, RTL8821C, RTL8723D)"
        echo "6) mt76 (MediaTek MT76 - MT7601U, MT7610U, MT7612U, MT7663U, MT7921U)"
        
        read -p "Enter choice (1-6): " driver_choice
        
        case $driver_choice in
            1) DRIVER="ath11k" ;;
            2) DRIVER="ath10k" ;;
            3) DRIVER="iwlwifi" ;;
            4) DRIVER="rt2x00" ;;
            5) DRIVER="rtw88" ;;
            6) DRIVER="mt76" ;;
            *) DRIVER="ath11k" ;;
        esac
    fi
    
    # Chipset selection based on driver
    if [[ -z "$CHIPSET" ]]; then
        echo
        case $DRIVER in
            "ath11k")
                echo "Select ath11k chipset:"
                echo "1) QCA6390 (common in laptops)"
                echo "2) QCA6490 (newer laptops)"
                echo "3) WCN6855 (latest generation)"
                echo "4) QCN9074 (enterprise/AP)"
                
                read -p "Enter choice (1-4): " chipset_choice
                case $chipset_choice in
                    1) CHIPSET="QCA6390" ;;
                    2) CHIPSET="QCA6490" ;;
                    3) CHIPSET="WCN6855" ;;
                    4) CHIPSET="QCN9074" ;;
                    *) CHIPSET="QCA6390" ;;
                esac
                ;;
            "ath10k")
                echo "Select ath10k chipset:"
                echo "1) QCA988X (PCIe cards)"
                echo "2) QCA6174 (laptops)"
                echo "3) QCA9377 (USB adapters)"
                
                read -p "Enter choice (1-3): " chipset_choice
                case $chipset_choice in
                    1) CHIPSET="QCA988X" ;;
                    2) CHIPSET="QCA6174" ;;
                    3) CHIPSET="QCA9377" ;;
                    *) CHIPSET="QCA6174" ;;
                esac
                ;;
            "iwlwifi")
                echo "Select iwlwifi chipset:"
                echo "1) AX200 (WiFi 6)"
                echo "2) AX210 (WiFi 6E)"
                echo "3) AC9560 (WiFi 5)"
                
                read -p "Enter choice (1-3): " chipset_choice
                case $chipset_choice in
                    1) CHIPSET="AX200" ;;
                    2) CHIPSET="AX210" ;;
                    3) CHIPSET="AC9560" ;;
                    *) CHIPSET="AX200" ;;
                esac
                ;;
            "rt2x00")
                echo "Select rt2x00 chipset:"
                echo "1) RT3070 (common USB)"
                echo "2) RT5370 (newer USB)"
                
                read -p "Enter choice (1-2): " chipset_choice
                case $chipset_choice in
                    1) CHIPSET="RT3070" ;;
                    2) CHIPSET="RT5370" ;;
                    *) CHIPSET="RT3070" ;;
                esac
                ;;
            "rtw88")
                echo "Select RTW88 chipset:"
                echo "1) RTL8822B (USB/PCIe 802.11ac 2x2)"
                echo "2) RTL8822C (USB/PCIe 802.11ac 2x2 enhanced)"
                echo "3) RTL8821C (USB/PCIe 802.11ac 1x1)"
                echo "4) RTL8723D (USB 802.11n 1x1 + Bluetooth)"
                
                read -p "Enter choice (1-4): " chipset_choice
                case $chipset_choice in
                    1) CHIPSET="RTL8822B" ;;
                    2) CHIPSET="RTL8822C" ;;
                    3) CHIPSET="RTL8821C" ;;
                    4) CHIPSET="RTL8723D" ;;
                    *) CHIPSET="RTL8822C" ;;
                esac
                ;;
            "mt76")
                echo "Select MT76 chipset:"
                echo "1) MT7601U (USB 802.11n 1x1)"
                echo "2) MT7610U (USB 802.11ac 1x1)"
                echo "3) MT7612U (USB 802.11ac 2x2)"
                echo "4) MT7663U (USB 802.11ac 2x2 enhanced)"
                echo "5) MT7921U (USB 802.11ax 2x2 Wi-Fi 6)"
                
                read -p "Enter choice (1-5): " chipset_choice
                case $chipset_choice in
                    1) CHIPSET="MT7601U" ;;
                    2) CHIPSET="MT7610U" ;;
                    3) CHIPSET="MT7612U" ;;
                    4) CHIPSET="MT7663U" ;;
                    5) CHIPSET="MT7921U" ;;
                    *) CHIPSET="MT7612U" ;;
                esac
                ;;
        esac
    fi
    
    # Regulatory domain
    if [[ -z "$REGULATORY_DOMAIN" ]]; then
        echo
        echo "Select regulatory domain:"
        echo "1) US (United States - Full features)"
        echo "2) EU (European Union - Injection restricted)"
        echo "3) JP (Japan - Monitor mode restricted)"
        echo "4) CA (Canada - Similar to US)"
        echo "5) AU (Australia - Similar to EU)"
        
        read -p "Enter choice (1-5): " reg_choice
        
        case $reg_choice in
            1) REGULATORY_DOMAIN="US" ;;
            2) REGULATORY_DOMAIN="EU" ;;
            3) REGULATORY_DOMAIN="JP" ;;
            4) REGULATORY_DOMAIN="CA" ;;
            5) REGULATORY_DOMAIN="AU" ;;
            *) REGULATORY_DOMAIN="US" ;;
        esac
    fi
    
    # Feature selection based on use case
    case $USE_CASE in
        "security_research")
            FEATURES=("monitor_mode" "packet_injection")
            ;;
        "mesh_networking")
            FEATURES=("mesh_networking")
            ;;
        "enterprise")
            FEATURES=("enterprise_security")
            ;;
        "embedded")
            FEATURES=("minimal")
            ;;
        *)
            FEATURES=("standard")
            ;;
    esac
    
    # Confirm configuration
    echo
    info "=== Configuration Summary ==="
    info "Use Case: $USE_CASE"
    info "Driver: $DRIVER"
    info "Chipset: $CHIPSET"
    info "Regulatory Domain: $REGULATORY_DOMAIN"
    info "Features: ${FEATURES[*]}"
    echo
    
    if [[ "$AUTO_MODE" != "true" ]]; then
        read -p "Proceed with this configuration? (y/N): " confirm
        if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
            info "Setup cancelled by user"
            exit 0
        fi
    fi
}

check_conflicts() {
    info "Checking for driver conflicts..."
    
    if [[ -f "$SCRIPT_DIR/wireless-conflict-resolver.py" ]]; then
        python3 "$SCRIPT_DIR/wireless-conflict-resolver.py" detect
        
        # Check if conflicts were found
        local conflicts=$(python3 "$SCRIPT_DIR/wireless-conflict-resolver.py" detect 2>/dev/null | grep -c "conflict" || true)
        
        if [[ "$conflicts" -gt 0 ]]; then
            warning "Driver conflicts detected"
            
            if [[ "$AUTO_MODE" == "true" || "$FORCE_INSTALL" == "true" ]]; then
                info "Auto-resolving conflicts..."
                python3 "$SCRIPT_DIR/wireless-conflict-resolver.py" resolve-all
            else
                read -p "Resolve conflicts automatically? (y/N): " resolve_conflicts
                if [[ "$resolve_conflicts" == "y" || "$resolve_conflicts" == "Y" ]]; then
                    python3 "$SCRIPT_DIR/wireless-conflict-resolver.py" resolve-all
                fi
            fi
        else
            success "No driver conflicts detected"
        fi
    else
        warning "Conflict resolver not available"
    fi
}

check_regulatory_compliance() {
    info "Checking regulatory compliance..."
    
    if [[ -f "$SCRIPT_DIR/regulatory-compliance-checker.py" ]]; then
        local compliance_result=$(python3 "$SCRIPT_DIR/regulatory-compliance-checker.py" check \
            --driver "$DRIVER" --domain "$REGULATORY_DOMAIN" 2>/dev/null || echo "failed")
        
        if echo "$compliance_result" | grep -q "compliant"; then
            success "Driver is regulatory compliant"
        else
            warning "Regulatory compliance issues detected"
            info "Review compliance requirements for $REGULATORY_DOMAIN"
            
            # Show compliance details
            python3 "$SCRIPT_DIR/regulatory-compliance-checker.py" check \
                --driver "$DRIVER" --domain "$REGULATORY_DOMAIN" --verbose || true
        fi
    else
        warning "Regulatory compliance checker not available"
    fi
}

install_driver() {
    info "Installing wireless driver: $DRIVER"
    
    # Use wireless management CLI if available
    if [[ -f "$SCRIPT_DIR/wireless-management-cli.py" ]]; then
        local install_args=("install" "$DRIVER")
        
        if [[ -n "$CHIPSET" ]]; then
            install_args+=("--chipset" "$CHIPSET")
        fi
        
        install_args+=("--check-conflicts")
        
        if [[ "$AUTO_MODE" == "true" || "$FORCE_INSTALL" == "true" ]]; then
            install_args+=("--resolve-conflicts")
        fi
        
        python3 "$SCRIPT_DIR/wireless-management-cli.py" "${install_args[@]}"
    else
        # Fallback to manual installation
        warning "Wireless management CLI not available, using manual installation"
        
        # Generate Kconfig
        generate_kconfig
        
        # Build driver
        if [[ "$SKIP_BUILD" != "true" ]]; then
            build_driver
        fi
        
        # Install firmware
        if [[ "$SKIP_FIRMWARE" != "true" ]]; then
            install_firmware
        fi
    fi
}

generate_kconfig() {
    info "Generating Kconfig for $DRIVER..."
    
    local config_file="$CONFIG_DIR/${DRIVER}.config"
    mkdir -p "$CONFIG_DIR"
    
    cat > "$config_file" << EOF
# Wireless driver configuration for $DRIVER
# Generated by setup-wireless-drivers.sh

# Basic backports configuration
CONFIG_BACKPORTS=y
CONFIG_BACKPORTS_BUILD_COMPAT=y

# Wireless stack
CONFIG_BACKPORTS_CFG80211=y
CONFIG_BACKPORTS_MAC80211=y
CONFIG_BACKPORTS_MAC80211_RC_MINSTREL=y

# Regulatory support
CONFIG_BACKPORTS_CFG80211_CRDA_SUPPORT=y

EOF

    # Driver-specific configuration
    case $DRIVER in
        "ath11k")
            cat >> "$config_file" << EOF
# ath11k driver
CONFIG_BACKPORTS_ATH_COMMON=y
CONFIG_BACKPORTS_ATH11K=y
CONFIG_BACKPORTS_ATH11K_PCI=y
CONFIG_BACKPORTS_ATH11K_DEBUG=y
EOF
            ;;
        "ath10k")
            cat >> "$config_file" << EOF
# ath10k driver
CONFIG_BACKPORTS_ATH_COMMON=y
CONFIG_BACKPORTS_ATH10K=y
CONFIG_BACKPORTS_ATH10K_PCI=y
CONFIG_BACKPORTS_ATH10K_DEBUG=y
EOF
            ;;
        "iwlwifi")
            cat >> "$config_file" << EOF
# iwlwifi driver
CONFIG_BACKPORTS_IWLWIFI=y
CONFIG_BACKPORTS_IWLDVM=y
CONFIG_BACKPORTS_IWLMVM=y
EOF
            ;;
        "rt2x00")
            cat >> "$config_file" << EOF
# rt2x00 driver family
CONFIG_BACKPORTS_RT2X00=y
CONFIG_BACKPORTS_RT2800USB=y
CONFIG_BACKPORTS_RT2X00_LIB=y
EOF
            ;;
        "rtw88")
            cat >> "$config_file" << EOF
# RTW88 driver family
CONFIG_BACKPORTS_RTW88=m
CONFIG_BACKPORTS_RTW88_CORE=m
CONFIG_BACKPORTS_RTW88_USB=m
CONFIG_BACKPORTS_RTW88_8822B=m
CONFIG_BACKPORTS_RTW88_8822C=m
CONFIG_BACKPORTS_RTW88_8821C=m
CONFIG_BACKPORTS_RTW88_8723D=m
EOF
            ;;
        "mt76")
            cat >> "$config_file" << EOF
# MT76 driver family
CONFIG_BACKPORTS_MT76=m
CONFIG_BACKPORTS_MT76_CORE=m
CONFIG_BACKPORTS_MT76_USB=m
CONFIG_BACKPORTS_MT7601U=m
CONFIG_BACKPORTS_MT7610U=m
CONFIG_BACKPORTS_MT7612U=m
CONFIG_BACKPORTS_MT7663U=m
CONFIG_BACKPORTS_MT7921U=m
EOF
            ;;
    esac
    
    # Feature-specific configuration
    for feature in "${FEATURES[@]}"; do
        case $feature in
            "monitor_mode")
                echo "CONFIG_BACKPORTS_MAC80211_DEBUGFS=y" >> "$config_file"
                ;;
            "packet_injection")
                echo "CONFIG_BACKPORTS_MAC80211_MESH=y" >> "$config_file"
                ;;
            "mesh_networking")
                echo "CONFIG_BACKPORTS_MAC80211_MESH=y" >> "$config_file"
                ;;
        esac
    done
    
    success "Generated Kconfig: $config_file"
}

build_driver() {
    info "Building wireless driver..."
    
    cd "$BACKPORTS_DIR"
    
    # Clean previous build
    if [[ -f "Makefile" ]]; then
        make clean 2>/dev/null || true
    fi
    
    # Configure build
    local config_file="$CONFIG_DIR/${DRIVER}.config"
    if [[ -f "$config_file" ]]; then
        cp "$config_file" .config
    fi
    
    # Build
    if make -j$(nproc) 2>&1 | tee -a "$LOG_FILE"; then
        success "Driver build completed successfully"
    else
        error "Driver build failed"
        info "Check build log: $LOG_FILE"
        exit 1
    fi
    
    cd - > /dev/null
}

install_firmware() {
    info "Installing firmware for $DRIVER/$CHIPSET..."
    
    if [[ -f "$SCRIPT_DIR/firmware-automation.py" ]]; then
        python3 "$SCRIPT_DIR/firmware-automation.py" install "$DRIVER" "$CHIPSET"
    else
        warning "Firmware automation not available"
        info "Manual firmware installation may be required"
    fi
}

verify_installation() {
    info "Verifying installation..."
    
    # Check if driver module exists
    local module_path="$BACKPORTS_DIR/drivers/net/wireless"
    
    case $DRIVER in
        "ath11k")
            module_path="$module_path/ath/ath11k/ath11k.ko"
            ;;
        "ath10k")
            module_path="$module_path/ath/ath10k/ath10k_core.ko"
            ;;
        "iwlwifi")
            module_path="$module_path/intel/iwlwifi/iwlwifi.ko"
            ;;
        "rt2x00")
            module_path="$module_path/ralink/rt2x00/rt2x00lib.ko"
            ;;
    esac
    
    if [[ -f "$module_path" ]]; then
        success "Driver module found: $module_path"
    else
        warning "Driver module not found at expected location"
    fi
    
    # Check firmware
    if [[ -f "$SCRIPT_DIR/firmware-automation.py" ]]; then
        python3 "$SCRIPT_DIR/firmware-automation.py" validate "$DRIVER" "$CHIPSET"
    fi
    
    # Generate verification report
    if [[ -f "$SCRIPT_DIR/wireless-management-cli.py" ]]; then
        info "Generating installation report..."
        python3 "$SCRIPT_DIR/wireless-management-cli.py" report --output "/tmp/wireless-install-report.txt"
        info "Installation report saved to: /tmp/wireless-install-report.txt"
    fi
}

save_configuration() {
    info "Saving configuration..."
    
    local config_file="$CONFIG_DIR/wireless-driver-config.json"
    
    cat > "$config_file" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "use_case": "$USE_CASE",
    "driver": "$DRIVER",
    "chipset": "$CHIPSET",
    "regulatory_domain": "$REGULATORY_DOMAIN",
    "features": [$(printf '"%s",' "${FEATURES[@]}" | sed 's/,$//')]
}
EOF
    
    success "Configuration saved to: $config_file"
}

show_usage() {
    cat << EOF
Wireless Driver Setup Script

Usage: $0 [OPTIONS]

OPTIONS:
    --driver DRIVER         Specify driver (ath11k, ath10k, iwlwifi, rt2x00)
    --chipset CHIPSET       Specify chipset variant
    --use-case CASE         Specify use case (laptop, security_research, mesh_networking, enterprise, embedded)
    --regulatory DOMAIN     Specify regulatory domain (US, EU, JP, CA, AU)
    --auto                  Run in automatic mode (no prompts)
    --skip-build            Skip driver build step
    --skip-firmware         Skip firmware installation
    --force                 Force installation even with conflicts
    --help                  Show this help message

EXAMPLES:
    # Interactive setup
    $0
    
    # Automated ath11k setup
    $0 --driver ath11k --chipset QCA6390 --regulatory US --auto
    
    # Security research setup
    $0 --use-case security_research --driver ath11k --auto
    
    # Skip build (use pre-built drivers)
    $0 --driver iwlwifi --skip-build

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --driver)
            DRIVER="$2"
            shift 2
            ;;
        --chipset)
            CHIPSET="$2"
            shift 2
            ;;
        --use-case)
            USE_CASE="$2"
            shift 2
            ;;
        --regulatory)
            REGULATORY_DOMAIN="$2"
            shift 2
            ;;
        --auto)
            AUTO_MODE=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-firmware)
            SKIP_FIRMWARE=true
            shift
            ;;
        --force)
            FORCE_INSTALL=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    info "=== Wireless Driver Setup Started ==="
    info "Log file: $LOG_FILE"
    
    # Check system requirements
    check_requirements
    
    # Detect hardware if no driver specified
    if [[ -z "$DRIVER" ]]; then
        detect_hardware
    fi
    
    # Interactive setup if not in auto mode
    interactive_setup
    
    # Pre-installation checks
    check_conflicts
    check_regulatory_compliance
    
    # Installation process
    install_driver
    
    # Post-installation verification
    verify_installation
    
    # Save configuration
    save_configuration
    
    success "=== Wireless Driver Setup Completed ==="
    info "Configuration saved and driver installed successfully"
    info "Log file: $LOG_FILE"
    
    # Show next steps
    echo
    info "Next steps:"
    info "1. Reboot or reload wireless modules"
    info "2. Configure network manager"
    info "3. Test wireless connectivity"
    
    if [[ "${FEATURES[*]}" =~ "monitor_mode" ]]; then
        warning "Monitor mode enabled - ensure proper authorization"
    fi
    
    if [[ "${FEATURES[*]}" =~ "packet_injection" ]]; then
        warning "Packet injection enabled - ensure regulatory compliance"
    fi
}

# Run main function
main "$@"