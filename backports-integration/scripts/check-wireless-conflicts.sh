#!/bin/bash
#
# Wireless Driver Conflict Detection Script
#
# This script detects and prevents conflicts between backports and vendor
# wireless drivers, providing automatic conflict resolution suggestions.
#

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KERNEL_ROOT="${SCRIPT_DIR}/../.."
CONFIG_FILE="${KERNEL_ROOT}/.config"
BACKPORTS_DIR="${KERNEL_ROOT}/backports-generated-6.1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_conflict() {
    echo -e "${CYAN}[CONFLICT]${NC} $1"
}

# Conflict definitions
declare -A WIRELESS_CONFLICTS=(
    # Core wireless conflicts
    ["CONFIG_BACKPORTS_CFG80211"]="CONFIG_CFG80211"
    ["CONFIG_BACKPORTS_MAC80211"]="CONFIG_MAC80211"
    
    # Vendor driver conflicts
    ["CONFIG_BACKPORTS"]="CONFIG_QCACLD CONFIG_PRIMA_WLAN CONFIG_ATH_CARDS CONFIG_IWLWIFI"
    
    # Specific driver conflicts
    ["CONFIG_BACKPORTS_CFG80211"]="CONFIG_QCACLD_WLAN_LFR3 CONFIG_PRIMA_WLAN_LFR"
    ["CONFIG_BACKPORTS_MAC80211"]="CONFIG_QCOM_WLAN CONFIG_BROADCOM_WLAN"
)

# Vendor driver patterns
VENDOR_DRIVERS=(
    "CONFIG_QCACLD"
    "CONFIG_PRIMA_WLAN"
    "CONFIG_ATH_CARDS"
    "CONFIG_IWLWIFI"
    "CONFIG_BROADCOM_WLAN"
    "CONFIG_QCOM_WLAN"
    "CONFIG_REALTEK_WLAN"
    "CONFIG_MARVELL_WLAN"
)

# Read kernel configuration
read_config() {
    local config_file="$1"
    local -A config
    
    if [ ! -f "$config_file" ]; then
        log_warning "Configuration file not found: $config_file"
        return 1
    fi
    
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ $key =~ ^#.*$ ]] && continue
        [[ -z $key ]] && continue
        
        # Store configuration
        config["$key"]="$value"
    done < "$config_file"
    
    # Export config as global associative array
    for key in "${!config[@]}"; do
        declare -g "KERNEL_CONFIG_$key"="${config[$key]}"
    done
}

# Check if a config option is enabled
is_enabled() {
    local option="$1"
    local var_name="KERNEL_CONFIG_$option"
    local value="${!var_name}"
    
    [[ "$value" == "y" ]] || [[ "$value" == "m" ]]
}

# Get config value
get_config_value() {
    local option="$1"
    local var_name="KERNEL_CONFIG_$option"
    echo "${!var_name:-n}"
}

# Detect direct conflicts
detect_direct_conflicts() {
    log_info "Checking for direct wireless driver conflicts..."
    
    local conflicts_found=0
    
    for backports_option in "${!WIRELESS_CONFLICTS[@]}"; do
        if is_enabled "$backports_option"; then
            local conflicting_options="${WIRELESS_CONFLICTS[$backports_option]}"
            
            for conflict in $conflicting_options; do
                if is_enabled "$conflict"; then
                    log_conflict "Direct conflict: $backports_option conflicts with $conflict"
                    log_error "Both $backports_option=$(get_config_value "$backports_option") and $conflict=$(get_config_value "$conflict") are enabled"
                    conflicts_found=$((conflicts_found + 1))
                fi
            done
        fi
    done
    
    return $conflicts_found
}

# Detect vendor driver conflicts
detect_vendor_conflicts() {
    log_info "Checking for vendor driver conflicts..."
    
    local conflicts_found=0
    local backports_enabled=false
    
    # Check if any backports are enabled
    for option in CONFIG_BACKPORTS CONFIG_BACKPORTS_CFG80211 CONFIG_BACKPORTS_MAC80211; do
        if is_enabled "$option"; then
            backports_enabled=true
            break
        fi
    done
    
    if [ "$backports_enabled" = true ]; then
        for vendor_driver in "${VENDOR_DRIVERS[@]}"; do
            if is_enabled "$vendor_driver"; then
                log_conflict "Vendor driver conflict: $vendor_driver may conflict with backports"
                log_warning "$vendor_driver=$(get_config_value "$vendor_driver") is enabled alongside backports"
                conflicts_found=$((conflicts_found + 1))
            fi
        done
    fi
    
    return $conflicts_found
}

# Detect module loading conflicts
detect_module_conflicts() {
    log_info "Checking for potential module loading conflicts..."
    
    local conflicts_found=0
    
    # Check if both backports and kernel wireless are built as modules
    if [[ "$(get_config_value "CONFIG_BACKPORTS_CFG80211")" == "m" ]] && [[ "$(get_config_value "CONFIG_CFG80211")" == "m" ]]; then
        log_conflict "Module conflict: Both backports cfg80211 and kernel cfg80211 are built as modules"
        log_warning "This may cause module loading conflicts at runtime"
        conflicts_found=$((conflicts_found + 1))
    fi
    
    if [[ "$(get_config_value "CONFIG_BACKPORTS_MAC80211")" == "m" ]] && [[ "$(get_config_value "CONFIG_MAC80211")" == "m" ]]; then
        log_conflict "Module conflict: Both backports mac80211 and kernel mac80211 are built as modules"
        log_warning "This may cause module loading conflicts at runtime"
        conflicts_found=$((conflicts_found + 1))
    fi
    
    return $conflicts_found
}

# Check for Android-specific conflicts
detect_android_conflicts() {
    log_info "Checking for Android-specific conflicts..."
    
    local conflicts_found=0
    
    # Check for Android wireless framework conflicts
    if is_enabled "CONFIG_BACKPORTS" && is_enabled "CONFIG_ANDROID"; then
        # Check for common Android wireless conflicts
        local android_wireless_options=(
            "CONFIG_ANDROID_PARANOID_NETWORK"
            "CONFIG_QCOM_WLAN_FEATURE_11W"
            "CONFIG_QCACLD_FEATURE_WLAN_WAPI"
        )
        
        for option in "${android_wireless_options[@]}"; do
            if is_enabled "$option"; then
                log_warning "Android wireless option $option may need special handling with backports"
            fi
        done
        
        # Check for vendor-specific Android drivers
        if is_enabled "CONFIG_QCACLD"; then
            log_conflict "Android vendor driver conflict: QCACLD driver conflicts with backports"
            log_error "CONFIG_QCACLD and CONFIG_BACKPORTS cannot be enabled simultaneously"
            conflicts_found=$((conflicts_found + 1))
        fi
    fi
    
    return $conflicts_found
}

# Generate conflict resolution suggestions
generate_resolution_suggestions() {
    local total_conflicts="$1"
    
    if [ "$total_conflicts" -eq 0 ]; then
        return 0
    fi
    
    echo
    log_info "Conflict Resolution Suggestions:"
    echo "================================="
    
    # Direct conflict resolutions
    if is_enabled "CONFIG_BACKPORTS" && is_enabled "CONFIG_CFG80211"; then
        echo "1. Disable kernel cfg80211:"
        echo "   sed -i 's/CONFIG_CFG80211=.*/# CONFIG_CFG80211 is not set/' .config"
    fi
    
    if is_enabled "CONFIG_BACKPORTS" && is_enabled "CONFIG_MAC80211"; then
        echo "2. Disable kernel mac80211:"
        echo "   sed -i 's/CONFIG_MAC80211=.*/# CONFIG_MAC80211 is not set/' .config"
    fi
    
    # Vendor driver resolutions
    for vendor_driver in "${VENDOR_DRIVERS[@]}"; do
        if is_enabled "CONFIG_BACKPORTS" && is_enabled "$vendor_driver"; then
            echo "3. Disable vendor driver $vendor_driver:"
            echo "   sed -i 's/$vendor_driver=.*/# $vendor_driver is not set/' .config"
        fi
    done
    
    # Module blacklisting suggestions
    echo
    echo "4. Consider blacklisting conflicting modules:"
    echo "   echo 'blacklist cfg80211' >> /etc/modprobe.d/backports-blacklist.conf"
    echo "   echo 'blacklist mac80211' >> /etc/modprobe.d/backports-blacklist.conf"
    
    # Configuration regeneration
    echo
    echo "5. Regenerate configuration after changes:"
    echo "   make olddefconfig"
    echo "   make menuconfig  # Optional: review changes"
    
    return 0
}

# Create conflict resolution script
create_resolution_script() {
    local script_file="${KERNEL_ROOT}/resolve-wireless-conflicts.sh"
    
    log_info "Creating automatic conflict resolution script..."
    
    cat > "$script_file" << 'EOF'
#!/bin/bash
#
# Automatic Wireless Conflict Resolution Script
# Generated by check-wireless-conflicts.sh
#

set -e

CONFIG_FILE=".config"
BACKUP_FILE=".config.backup.$(date +%Y%m%d_%H%M%S)"

echo "Creating backup: $BACKUP_FILE"
cp "$CONFIG_FILE" "$BACKUP_FILE"

echo "Resolving wireless conflicts..."

# Disable conflicting kernel wireless drivers
sed -i 's/CONFIG_CFG80211=.*/# CONFIG_CFG80211 is not set/' "$CONFIG_FILE"
sed -i 's/CONFIG_MAC80211=.*/# CONFIG_MAC80211 is not set/' "$CONFIG_FILE"

# Disable common vendor drivers that conflict with backports
sed -i 's/CONFIG_QCACLD=.*/# CONFIG_QCACLD is not set/' "$CONFIG_FILE"
sed -i 's/CONFIG_PRIMA_WLAN=.*/# CONFIG_PRIMA_WLAN is not set/' "$CONFIG_FILE"
sed -i 's/CONFIG_ATH_CARDS=.*/# CONFIG_ATH_CARDS is not set/' "$CONFIG_FILE"

echo "Regenerating configuration..."
make olddefconfig

echo "Conflict resolution completed!"
echo "Backup saved as: $BACKUP_FILE"
echo "Run 'make menuconfig' to review changes if needed."
EOF
    
    chmod +x "$script_file"
    log_success "Resolution script created: $script_file"
}

# Generate detailed conflict report
generate_conflict_report() {
    local total_conflicts="$1"
    local report_file="${KERNEL_ROOT}/wireless-conflicts-report.txt"
    
    log_info "Generating detailed conflict report..."
    
    cat > "$report_file" << EOF
Wireless Driver Conflict Detection Report
==========================================

Generated: $(date)
Kernel Root: $KERNEL_ROOT
Configuration: $CONFIG_FILE

Summary:
--------
Total Conflicts Found: $total_conflicts

Backports Configuration:
------------------------
CONFIG_BACKPORTS: $(get_config_value "CONFIG_BACKPORTS")
CONFIG_BACKPORTS_CFG80211: $(get_config_value "CONFIG_BACKPORTS_CFG80211")
CONFIG_BACKPORTS_MAC80211: $(get_config_value "CONFIG_BACKPORTS_MAC80211")
CONFIG_BACKPORTS_MONITOR_MODE: $(get_config_value "CONFIG_BACKPORTS_MONITOR_MODE")
CONFIG_BACKPORTS_FRAME_INJECTION: $(get_config_value "CONFIG_BACKPORTS_FRAME_INJECTION")

Kernel Wireless Configuration:
------------------------------
CONFIG_CFG80211: $(get_config_value "CONFIG_CFG80211")
CONFIG_MAC80211: $(get_config_value "CONFIG_MAC80211")
CONFIG_WIRELESS_EXT: $(get_config_value "CONFIG_WIRELESS_EXT")

Vendor Drivers:
---------------
EOF
    
    for vendor_driver in "${VENDOR_DRIVERS[@]}"; do
        echo "$vendor_driver: $(get_config_value "$vendor_driver")" >> "$report_file"
    done
    
    cat >> "$report_file" << EOF

Detected Conflicts:
-------------------
EOF
    
    # Add conflict details to report
    if [ "$total_conflicts" -gt 0 ]; then
        echo "See console output above for detailed conflict information." >> "$report_file"
    else
        echo "No conflicts detected." >> "$report_file"
    fi
    
    cat >> "$report_file" << EOF

Recommendations:
----------------
1. If conflicts are found, run the generated resolution script:
   ./resolve-wireless-conflicts.sh

2. Review configuration changes:
   make menuconfig

3. Rebuild kernel with resolved configuration:
   make -j\$(nproc)

4. Test wireless functionality after installation.

For more information, consult the backports documentation.
EOF
    
    log_success "Conflict report saved: $report_file"
}

# Main conflict detection function
main() {
    echo "Wireless Driver Conflict Detection"
    echo "=================================="
    echo
    
    # Read kernel configuration
    if ! read_config "$CONFIG_FILE"; then
        log_error "Failed to read kernel configuration"
        exit 1
    fi
    
    # Run conflict detection
    local total_conflicts=0
    
    detect_direct_conflicts
    total_conflicts=$((total_conflicts + $?))
    
    detect_vendor_conflicts
    total_conflicts=$((total_conflicts + $?))
    
    detect_module_conflicts
    total_conflicts=$((total_conflicts + $?))
    
    detect_android_conflicts
    total_conflicts=$((total_conflicts + $?))
    
    echo
    echo "Conflict Detection Summary:"
    echo "=========================="
    echo "Total conflicts found: $total_conflicts"
    
    if [ "$total_conflicts" -eq 0 ]; then
        log_success "No wireless driver conflicts detected!"
        echo
        log_info "Your configuration appears to be conflict-free."
        log_info "You can proceed with building backports."
    else
        log_error "Wireless driver conflicts detected!"
        echo
        generate_resolution_suggestions "$total_conflicts"
        create_resolution_script
        generate_conflict_report "$total_conflicts"
        echo
        log_info "Run './resolve-wireless-conflicts.sh' to automatically resolve conflicts"
    fi
    
    return $total_conflicts
}

# Handle command line arguments
case "${1:-check}" in
    check)
        main
        ;;
    resolve)
        if [ -f "${KERNEL_ROOT}/resolve-wireless-conflicts.sh" ]; then
            "${KERNEL_ROOT}/resolve-wireless-conflicts.sh"
        else
            log_error "Resolution script not found. Run 'check' first to generate it."
            exit 1
        fi
        ;;
    report)
        read_config "$CONFIG_FILE"
        generate_conflict_report 0
        ;;
    *)
        echo "Usage: $0 [check|resolve|report]"
        echo "  check   - Check for conflicts (default)"
        echo "  resolve - Run automatic conflict resolution"
        echo "  report  - Generate conflict report only"
        exit 1
        ;;
esac