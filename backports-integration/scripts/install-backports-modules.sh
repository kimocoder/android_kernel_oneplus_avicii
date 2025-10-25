#!/bin/bash
#
# Backports Module Installation Script
#
# This script handles the installation of backports modules with proper
# dependency resolution and conflict management.
#

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKPORTS_DIR="${SCRIPT_DIR}/../.."
KERNEL_VERSION="${KERNELRELEASE:-$(uname -r)}"
INSTALL_ROOT="${INSTALL_MOD_PATH:-}"
MODULE_DIR="${INSTALL_ROOT}/lib/modules/${KERNEL_VERSION}"
BACKPORTS_MODULE_DIR="${MODULE_DIR}/backports"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Check if running as root for system installation
check_permissions() {
    if [ -z "$INSTALL_ROOT" ] && [ "$EUID" -ne 0 ]; then
        log_warning "Not running as root. System module installation may fail."
        log_info "Consider running with sudo or setting INSTALL_MOD_PATH"
    fi
}

# Validate environment
validate_environment() {
    log_info "Validating installation environment..."
    
    if [ ! -d "$BACKPORTS_DIR/backports-generated-6.1" ]; then
        log_error "Backports directory not found: $BACKPORTS_DIR/backports-generated-6.1"
        exit 1
    fi
    
    if [ ! -f "$BACKPORTS_DIR/backports-generated-6.1/Makefile" ]; then
        log_error "Backports Makefile not found"
        exit 1
    fi
    
    log_success "Environment validation passed"
}

# Check for conflicting modules
check_conflicts() {
    log_info "Checking for conflicting modules..."
    
    local conflicts_found=0
    
    # Check for existing cfg80211
    if [ -f "${MODULE_DIR}/kernel/net/wireless/cfg80211.ko" ]; then
        log_warning "Existing cfg80211 module found in kernel tree"
        conflicts_found=1
    fi
    
    # Check for existing mac80211
    if [ -f "${MODULE_DIR}/kernel/net/mac80211/mac80211.ko" ]; then
        log_warning "Existing mac80211 module found in kernel tree"
        conflicts_found=1
    fi
    
    if [ $conflicts_found -eq 1 ]; then
        log_warning "Conflicting modules detected. Backports modules will take precedence."
        log_info "Consider blacklisting conflicting modules if needed"
    else
        log_success "No conflicting modules found"
    fi
}

# Create module directories
create_directories() {
    log_info "Creating module directories..."
    
    mkdir -p "$BACKPORTS_MODULE_DIR"
    mkdir -p "$BACKPORTS_MODULE_DIR/net/wireless"
    mkdir -p "$BACKPORTS_MODULE_DIR/net/mac80211"
    mkdir -p "$BACKPORTS_MODULE_DIR/drivers/net/wireless"
    
    log_success "Module directories created"
}

# Install backports modules
install_modules() {
    log_info "Installing backports modules..."
    
    cd "$BACKPORTS_DIR/backports-generated-6.1"
    
    # Set environment variables
    export KLIB_BUILD="${KLIB_BUILD:-/lib/modules/${KERNEL_VERSION}/build}"
    export KLIB="${KLIB:-/lib/modules/${KERNEL_VERSION}}"
    export INSTALL_MOD_PATH="${INSTALL_ROOT}"
    export KMODDIR="backports"
    
    # Run the installation
    if make modules_install; then
        log_success "Backports modules installed successfully"
    else
        log_error "Failed to install backports modules"
        exit 1
    fi
}

# Update module dependencies
update_dependencies() {
    log_info "Updating module dependencies..."
    
    local depmod_args=()
    
    # Add System.map if available
    if [ -f "/boot/System.map-${KERNEL_VERSION}" ]; then
        depmod_args+=("-F" "/boot/System.map-${KERNEL_VERSION}")
    elif [ -f "${KLIB_BUILD}/System.map" ]; then
        depmod_args+=("-F" "${KLIB_BUILD}/System.map")
    fi
    
    # Run depmod
    if [ -n "$INSTALL_ROOT" ]; then
        depmod_args+=("-b" "$INSTALL_ROOT")
    fi
    
    depmod_args+=("$KERNEL_VERSION")
    
    if depmod "${depmod_args[@]}"; then
        log_success "Module dependencies updated"
    else
        log_warning "Failed to update module dependencies"
    fi
}

# Create module loading configuration
create_module_config() {
    log_info "Creating module loading configuration..."
    
    local modprobe_dir="${INSTALL_ROOT}/etc/modprobe.d"
    local config_file="${modprobe_dir}/backports.conf"
    
    mkdir -p "$modprobe_dir"
    
    cat > "$config_file" << 'EOF'
# Backports module configuration
# This file configures the backports wireless modules

# Prefer backports modules over kernel modules
install cfg80211 /sbin/modprobe --ignore-install cfg80211 $CMDLINE_OPTS && { /sbin/modprobe --quiet --ignore-install backports-cfg80211; }
install mac80211 /sbin/modprobe --ignore-install mac80211 $CMDLINE_OPTS && { /sbin/modprobe --quiet --ignore-install backports-mac80211; }

# Blacklist conflicting kernel modules if needed
# Uncomment the following lines if you experience conflicts:
# blacklist cfg80211
# blacklist mac80211
EOF
    
    log_success "Module configuration created: $config_file"
}

# Generate installation report
generate_report() {
    log_info "Generating installation report..."
    
    local report_file="${BACKPORTS_MODULE_DIR}/INSTALLATION_REPORT.txt"
    
    cat > "$report_file" << EOF
Backports Module Installation Report
====================================

Installation Date: $(date)
Kernel Version: $KERNEL_VERSION
Installation Path: $BACKPORTS_MODULE_DIR

Installed Modules:
EOF
    
    if [ -d "$BACKPORTS_MODULE_DIR" ]; then
        find "$BACKPORTS_MODULE_DIR" -name "*.ko" | sort >> "$report_file"
    fi
    
    cat >> "$report_file" << EOF

Configuration:
- Module configuration: ${INSTALL_ROOT}/etc/modprobe.d/backports.conf
- Module dependencies updated: $(date)

Usage:
- Load cfg80211: modprobe cfg80211
- Load mac80211: modprobe mac80211
- Check status: lsmod | grep -E "(cfg80211|mac80211)"

For more information, see the backports documentation.
EOF
    
    log_success "Installation report created: $report_file"
}

# Main installation function
main() {
    echo "Backports Module Installation"
    echo "============================="
    echo
    
    check_permissions
    validate_environment
    check_conflicts
    create_directories
    install_modules
    update_dependencies
    create_module_config
    generate_report
    
    echo
    log_success "Backports module installation completed successfully!"
    echo
    log_info "Next steps:"
    log_info "1. Load modules: modprobe cfg80211 && modprobe mac80211"
    log_info "2. Check status: lsmod | grep -E '(cfg80211|mac80211)'"
    log_info "3. Test functionality: iw dev"
    echo
}

# Handle command line arguments
case "${1:-install}" in
    install)
        main
        ;;
    uninstall)
        log_info "Uninstalling backports modules..."
        rm -rf "$BACKPORTS_MODULE_DIR"
        rm -f "${INSTALL_ROOT}/etc/modprobe.d/backports.conf"
        update_dependencies
        log_success "Backports modules uninstalled"
        ;;
    status)
        log_info "Backports installation status:"
        if [ -d "$BACKPORTS_MODULE_DIR" ]; then
            log_success "Backports modules are installed"
            log_info "Module count: $(find "$BACKPORTS_MODULE_DIR" -name "*.ko" | wc -l)"
        else
            log_warning "Backports modules are not installed"
        fi
        ;;
    *)
        echo "Usage: $0 [install|uninstall|status]"
        exit 1
        ;;
esac