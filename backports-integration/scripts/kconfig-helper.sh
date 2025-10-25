#!/bin/bash
#
# Kconfig Helper Script
#
# Provides utilities for automated configuration changes and fixes.
#

set -e

KERNEL_ROOT="${1:-.}"
CONFIG_FILE="$KERNEL_ROOT/.config"
BACKUP_DIR="$KERNEL_ROOT/.config.backups"

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

# Backup configuration
backup_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        log_error "Configuration file not found: $CONFIG_FILE"
        return 1
    fi
    
    mkdir -p "$BACKUP_DIR"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/config_$timestamp"
    
    cp "$CONFIG_FILE" "$backup_file"
    log_info "Configuration backed up to: $backup_file"
}

# Enable a configuration option
enable_option() {
    local option="$1"
    local value="${2:-y}"
    
    if [ -z "$option" ]; then
        log_error "Option name required"
        return 1
    fi
    
    log_info "Enabling $option=$value"
    
    # Remove existing option if present
    sed -i "/^$option=/d" "$CONFIG_FILE" 2>/dev/null || true
    sed -i "/^# $option is not set/d" "$CONFIG_FILE" 2>/dev/null || true
    
    # Add the option
    echo "$option=$value" >> "$CONFIG_FILE"
    
    log_success "Enabled $option=$value"
}

# Disable a configuration option
disable_option() {
    local option="$1"
    
    if [ -z "$option" ]; then
        log_error "Option name required"
        return 1
    fi
    
    log_info "Disabling $option"
    
    # Remove existing option if present
    sed -i "/^$option=/d" "$CONFIG_FILE" 2>/dev/null || true
    sed -i "/^# $option is not set/d" "$CONFIG_FILE" 2>/dev/null || true
    
    # Add disabled marker
    echo "# $option is not set" >> "$CONFIG_FILE"
    
    log_success "Disabled $option"
}

# Check if option is enabled
is_enabled() {
    local option="$1"
    
    if [ -z "$option" ]; then
        return 1
    fi
    
    grep -q "^$option=[ym]" "$CONFIG_FILE" 2>/dev/null
}

# Get option value
get_option_value() {
    local option="$1"
    
    if [ -z "$option" ]; then
        return 1
    fi
    
    grep "^$option=" "$CONFIG_FILE" 2>/dev/null | cut -d'=' -f2
}

# Apply configuration template
apply_template() {
    local template="$1"
    
    case "$template" in
        "basic")
            log_info "Applying basic backports configuration"
            backup_config
            
            # Disable kernel wireless
            disable_option "CONFIG_CFG80211"
            disable_option "CONFIG_MAC80211"
            
            # Enable backports
            enable_option "CONFIG_BACKPORTS" "y"
            enable_option "CONFIG_BACKPORTS_CFG80211" "m"
            enable_option "CONFIG_BACKPORTS_MAC80211" "m"
            ;;
            
        "monitor")
            log_info "Applying monitor mode configuration"
            backup_config
            
            # Disable kernel wireless
            disable_option "CONFIG_CFG80211"
            disable_option "CONFIG_MAC80211"
            
            # Enable backports with monitor mode
            enable_option "CONFIG_BACKPORTS" "y"
            enable_option "CONFIG_BACKPORTS_CFG80211" "m"
            enable_option "CONFIG_BACKPORTS_MAC80211" "m"
            enable_option "CONFIG_BACKPORTS_MONITOR_MODE" "y"
            enable_option "CONFIG_PACKET" "y"
            ;;
            
        "injection")
            log_info "Applying frame injection configuration"
            log_warning "Frame injection has security implications!"
            backup_config
            
            # Disable kernel wireless
            disable_option "CONFIG_CFG80211"
            disable_option "CONFIG_MAC80211"
            
            # Enable backports with frame injection
            enable_option "CONFIG_BACKPORTS" "y"
            enable_option "CONFIG_BACKPORTS_CFG80211" "m"
            enable_option "CONFIG_BACKPORTS_MAC80211" "m"
            enable_option "CONFIG_BACKPORTS_MONITOR_MODE" "y"
            enable_option "CONFIG_BACKPORTS_FRAME_INJECTION" "y"
            enable_option "CONFIG_PACKET" "y"
            enable_option "CONFIG_PACKET_MMAP" "y"
            ;;
            
        "android")
            log_info "Applying Android-compatible configuration"
            backup_config
            
            # Disable conflicting drivers
            disable_option "CONFIG_CFG80211"
            disable_option "CONFIG_MAC80211"
            disable_option "CONFIG_QCACLD"
            disable_option "CONFIG_PRIMA_WLAN"
            
            # Enable Android backports
            enable_option "CONFIG_BACKPORTS" "y"
            enable_option "CONFIG_BACKPORTS_CFG80211" "m"
            enable_option "CONFIG_BACKPORTS_MAC80211" "m"
            enable_option "CONFIG_BACKPORTS_ANDROID" "y"
            ;;
            
        "android-complete")
            log_info "Applying complete Android backports configuration"
            log_info "This includes full Android integration and security features"
            backup_config
            
            # Apply complete Android configuration
            local config_template="$SCRIPT_DIR/../configs/android-complete.config"
            if [ -f "$config_template" ]; then
                log_info "Applying complete Android configuration from template"
                # Extract CONFIG_ lines and apply them
                grep "^CONFIG_" "$config_template" | while read -r line; do
                    if [[ $line == *"=y" ]]; then
                        option=$(echo "$line" | cut -d'=' -f1)
                        enable_option "$option" "y"
                    elif [[ $line == *"=m" ]]; then
                        option=$(echo "$line" | cut -d'=' -f1)
                        enable_option "$option" "m"
                    fi
                done
            else
                log_error "Complete Android configuration template not found"
                return 1
            fi
            ;;
            
        "advanced")
            log_info "Applying advanced monitor mode configuration"
            log_warning "This includes security-sensitive features!"
            backup_config
            
            # Apply advanced monitor configuration
            local config_template="$SCRIPT_DIR/../configs/advanced-monitor.config"
            if [ -f "$config_template" ]; then
                log_info "Applying configuration from template"
                # Extract CONFIG_ lines and apply them
                grep "^CONFIG_" "$config_template" | while read -r line; do
                    if [[ $line == *"=y" ]]; then
                        option=$(echo "$line" | cut -d'=' -f1)
                        enable_option "$option" "y"
                    elif [[ $line == *"=m" ]]; then
                        option=$(echo "$line" | cut -d'=' -f1)
                        enable_option "$option" "m"
                    fi
                done
            else
                log_error "Advanced configuration template not found"
                return 1
            fi
            ;;
            
        "security")
            log_info "Applying security research configuration"
            log_warning "*** SECURITY WARNING ***"
            log_warning "This enables frame injection and other security-sensitive features!"
            log_warning "Only use in controlled environments!"
            backup_config
            
            # Apply security research configuration
            local config_template="$SCRIPT_DIR/../configs/security-research.config"
            if [ -f "$config_template" ]; then
                log_info "Applying security research configuration from template"
                # Extract CONFIG_ lines and apply them
                grep "^CONFIG_" "$config_template" | while read -r line; do
                    if [[ $line == *"=y" ]]; then
                        option=$(echo "$line" | cut -d'=' -f1)
                        enable_option "$option" "y"
                    elif [[ $line == *"=m" ]]; then
                        option=$(echo "$line" | cut -d'=' -f1)
                        enable_option "$option" "m"
                    fi
                done
            else
                log_error "Security research configuration template not found"
                return 1
            fi
            ;;
            
        *)
            log_error "Unknown template: $template"
            log_info "Available templates: basic, monitor, injection, android, android-complete, advanced, security"
            return 1
            ;;
    esac
    
    log_success "Template '$template' applied successfully"
    log_info "Run 'make olddefconfig' to resolve dependencies"
}

# Validate configuration
validate_config() {
    log_info "Validating backports configuration"
    
    local script_dir="$(dirname "$0")"
    local validator="$script_dir/enhanced-validator.py"
    
    if [ -f "$validator" ]; then
        python3 "$validator" --kernel-root "$KERNEL_ROOT"
    else
        log_warning "Enhanced validator not found, using basic validation"
        
        # Basic validation
        local errors=0
        
        # Check for conflicting wireless stacks
        if is_enabled "CONFIG_BACKPORTS" && (is_enabled "CONFIG_CFG80211" || is_enabled "CONFIG_MAC80211"); then
            log_error "Conflicting wireless stacks detected"
            errors=$((errors + 1))
        fi
        
        # Check dependencies
        if is_enabled "CONFIG_BACKPORTS_MAC80211" && ! is_enabled "CONFIG_BACKPORTS_CFG80211"; then
            log_error "MAC80211 requires CFG80211"
            errors=$((errors + 1))
        fi
        
        if is_enabled "CONFIG_BACKPORTS_FRAME_INJECTION" && ! is_enabled "CONFIG_BACKPORTS_MONITOR_MODE"; then
            log_error "Frame injection requires monitor mode"
            errors=$((errors + 1))
        fi
        
        if [ $errors -eq 0 ]; then
            log_success "Basic validation passed"
        else
            log_error "Validation failed with $errors errors"
            return 1
        fi
    fi
}

# Fix common configuration issues
auto_fix() {
    log_info "Attempting to auto-fix configuration issues"
    backup_config
    
    local fixed=0
    
    # Fix conflicting wireless stacks
    if is_enabled "CONFIG_BACKPORTS" && (is_enabled "CONFIG_CFG80211" || is_enabled "CONFIG_MAC80211"); then
        log_info "Fixing conflicting wireless stacks"
        disable_option "CONFIG_CFG80211"
        disable_option "CONFIG_MAC80211"
        fixed=$((fixed + 1))
    fi
    
    # Fix missing dependencies
    if is_enabled "CONFIG_BACKPORTS_MAC80211" && ! is_enabled "CONFIG_BACKPORTS_CFG80211"; then
        log_info "Enabling missing CFG80211 dependency"
        enable_option "CONFIG_BACKPORTS_CFG80211" "m"
        fixed=$((fixed + 1))
    fi
    
    if is_enabled "CONFIG_BACKPORTS_MONITOR_MODE" && ! is_enabled "CONFIG_PACKET"; then
        log_info "Enabling missing PACKET dependency"
        enable_option "CONFIG_PACKET" "y"
        fixed=$((fixed + 1))
    fi
    
    if is_enabled "CONFIG_BACKPORTS_FRAME_INJECTION" && ! is_enabled "CONFIG_PACKET_MMAP"; then
        log_info "Enabling missing PACKET_MMAP dependency"
        enable_option "CONFIG_PACKET_MMAP" "y"
        fixed=$((fixed + 1))
    fi
    
    if [ $fixed -gt 0 ]; then
        log_success "Auto-fixed $fixed configuration issues"
        log_info "Run 'make olddefconfig' to resolve remaining dependencies"
    else
        log_info "No auto-fixable issues found"
    fi
}

# Show configuration status
show_status() {
    log_info "Backports configuration status:"
    echo
    
    local options=(
        "CONFIG_BACKPORTS"
        "CONFIG_BACKPORTS_CFG80211"
        "CONFIG_BACKPORTS_MAC80211"
        "CONFIG_BACKPORTS_MONITOR_MODE"
        "CONFIG_BACKPORTS_FRAME_INJECTION"
        "CONFIG_BACKPORTS_ANDROID"
        "CONFIG_BACKPORTS_DEBUG"
    )
    
    for option in "${options[@]}"; do
        if is_enabled "$option"; then
            local value=$(get_option_value "$option")
            echo -e "  ✅ $option=$value"
        else
            echo -e "  ❌ $option (disabled)"
        fi
    done
    
    echo
    
    # Check for conflicts
    local conflicts=()
    if is_enabled "CONFIG_BACKPORTS" && is_enabled "CONFIG_CFG80211"; then
        conflicts+=("CONFIG_CFG80211 conflicts with backports")
    fi
    if is_enabled "CONFIG_BACKPORTS" && is_enabled "CONFIG_MAC80211"; then
        conflicts+=("CONFIG_MAC80211 conflicts with backports")
    fi
    
    if [ ${#conflicts[@]} -gt 0 ]; then
        log_warning "Configuration conflicts detected:"
        for conflict in "${conflicts[@]}"; do
            echo -e "  ⚠️  $conflict"
        done
    else
        log_success "No conflicts detected"
    fi
}

# Main function
main() {
    local command="$1"
    shift
    
    case "$command" in
        "enable")
            enable_option "$@"
            ;;
        "disable")
            disable_option "$@"
            ;;
        "template")
            apply_template "$1"
            ;;
        "validate")
            validate_config
            ;;
        "fix")
            auto_fix
            ;;
        "status")
            show_status
            ;;
        "backup")
            backup_config
            ;;
        *)
            echo "Usage: $0 <command> [options]"
            echo
            echo "Commands:"
            echo "  enable <option> [value]  - Enable configuration option"
            echo "  disable <option>         - Disable configuration option"
            echo "  template <name>          - Apply configuration template"
            echo "  validate                 - Validate configuration"
            echo "  fix                      - Auto-fix common issues"
            echo "  status                   - Show configuration status"
            echo "  backup                   - Backup current configuration"
            echo
            echo "Templates:"
            echo "  basic     - Basic backports configuration"
            echo "  monitor   - Enable monitor mode"
            echo "  injection - Enable frame injection (security sensitive)"
            echo "  android   - Android-compatible configuration"
            echo "  android-complete - Complete Android integration with security"
            echo "  advanced  - Advanced monitor mode with full debugging"
            echo "  security  - Security research configuration (RESTRICTED)"
            echo
            echo "Examples:"
            echo "  $0 template basic"
            echo "  $0 enable CONFIG_BACKPORTS_MONITOR_MODE"
            echo "  $0 validate"
            echo "  $0 fix"
            return 1
            ;;
    esac
}

# Run main function if script is executed directly
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi