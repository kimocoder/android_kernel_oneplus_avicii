#!/bin/bash
#
# Backports Dependency Management Script
#
# This script provides a unified interface for managing backports dependencies,
# including validation, conflict detection, and resolution.
#

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KERNEL_ROOT="${SCRIPT_DIR}/../.."

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

log_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# Check if required scripts exist
check_dependencies() {
    local missing_scripts=()
    
    local required_scripts=(
        "validate-backports-deps.py"
        "check-wireless-conflicts.sh"
        "resolve-backports-deps.py"
    )
    
    for script in "${required_scripts[@]}"; do
        if [ ! -f "${SCRIPT_DIR}/${script}" ]; then
            missing_scripts+=("$script")
        fi
    done
    
    if [ ${#missing_scripts[@]} -gt 0 ]; then
        log_error "Missing required scripts: ${missing_scripts[*]}"
        return 1
    fi
    
    return 0
}

# Run full dependency validation
validate_dependencies() {
    log_step "Running dependency validation..."
    
    if python3 "${SCRIPT_DIR}/validate-backports-deps.py" --kernel-root "$KERNEL_ROOT"; then
        log_success "Dependency validation passed"
        return 0
    else
        log_error "Dependency validation failed"
        return 1
    fi
}

# Run conflict detection
detect_conflicts() {
    log_step "Running conflict detection..."
    
    if bash "${SCRIPT_DIR}/check-wireless-conflicts.sh"; then
        log_success "No conflicts detected"
        return 0
    else
        log_warning "Conflicts detected"
        return 1
    fi
}

# Resolve conflicts automatically
resolve_conflicts() {
    log_step "Resolving conflicts automatically..."
    
    if bash "${SCRIPT_DIR}/check-wireless-conflicts.sh" resolve; then
        log_success "Conflicts resolved"
        return 0
    else
        log_error "Failed to resolve conflicts"
        return 1
    fi
}

# Apply configuration template
apply_template() {
    local template_name="$1"
    
    if [ -z "$template_name" ]; then
        log_error "Template name required"
        return 1
    fi
    
    log_step "Applying template: $template_name"
    
    if python3 "${SCRIPT_DIR}/resolve-backports-deps.py" --kernel-root "$KERNEL_ROOT" template "$template_name"; then
        log_success "Template applied successfully"
        return 0
    else
        log_error "Failed to apply template"
        return 1
    fi
}

# Interactive configuration
interactive_config() {
    log_step "Starting interactive configuration..."
    
    if python3 "${SCRIPT_DIR}/resolve-backports-deps.py" --kernel-root "$KERNEL_ROOT" interactive; then
        log_success "Interactive configuration completed"
        return 0
    else
        log_error "Interactive configuration failed"
        return 1
    fi
}

# Generate comprehensive report
generate_report() {
    local report_file="${KERNEL_ROOT}/backports-dependency-report.txt"
    
    log_step "Generating comprehensive dependency report..."
    
    cat > "$report_file" << EOF
Backports Dependency Management Report
======================================

Generated: $(date)
Kernel Root: $KERNEL_ROOT

EOF
    
    # Add dependency validation report
    echo "Dependency Validation:" >> "$report_file"
    echo "=====================" >> "$report_file"
    python3 "${SCRIPT_DIR}/validate-backports-deps.py" --kernel-root "$KERNEL_ROOT" --report >> "$report_file" 2>&1 || true
    echo "" >> "$report_file"
    
    # Add conflict detection report
    echo "Conflict Detection:" >> "$report_file"
    echo "==================" >> "$report_file"
    bash "${SCRIPT_DIR}/check-wireless-conflicts.sh" report >> "$report_file" 2>&1 || true
    echo "" >> "$report_file"
    
    # Add available templates
    echo "Available Templates:" >> "$report_file"
    echo "===================" >> "$report_file"
    python3 "${SCRIPT_DIR}/resolve-backports-deps.py" --kernel-root "$KERNEL_ROOT" list >> "$report_file" 2>&1 || true
    
    log_success "Report generated: $report_file"
}

# Complete setup workflow
complete_setup() {
    local template_name="${1:-basic}"
    
    echo "Backports Complete Setup Workflow"
    echo "================================="
    echo
    
    log_info "Using template: $template_name"
    echo
    
    # Step 1: Validate dependencies
    if ! validate_dependencies; then
        log_error "Dependency validation failed. Please fix issues before continuing."
        return 1
    fi
    
    # Step 2: Apply template
    if ! apply_template "$template_name"; then
        log_error "Failed to apply template. Trying interactive configuration..."
        if ! interactive_config; then
            log_error "Interactive configuration also failed."
            return 1
        fi
    fi
    
    # Step 3: Detect and resolve conflicts
    if ! detect_conflicts; then
        log_warning "Conflicts detected. Attempting automatic resolution..."
        if ! resolve_conflicts; then
            log_error "Automatic conflict resolution failed."
            log_info "Please resolve conflicts manually or use interactive mode."
            return 1
        fi
    fi
    
    # Step 4: Final validation
    log_step "Running final validation..."
    if ! validate_dependencies; then
        log_error "Final validation failed."
        return 1
    fi
    
    # Step 5: Finalize configuration
    log_step "Finalizing kernel configuration..."
    cd "$KERNEL_ROOT"
    if make olddefconfig; then
        log_success "Kernel configuration finalized"
    else
        log_warning "Failed to finalize configuration. You may need to run 'make menuconfig' manually."
    fi
    
    echo
    log_success "Backports setup completed successfully!"
    echo
    log_info "Next steps:"
    log_info "1. Review configuration: make menuconfig"
    log_info "2. Build kernel: make -j\$(nproc)"
    log_info "3. Install modules: make modules_install"
    echo
    
    return 0
}

# Show help
show_help() {
    cat << EOF
Backports Dependency Management Script
======================================

Usage: $0 <command> [options]

Commands:
  validate              - Run dependency validation
  conflicts             - Detect wireless driver conflicts
  resolve               - Resolve conflicts automatically
  template <name>       - Apply configuration template
  interactive           - Interactive configuration
  report                - Generate comprehensive report
  setup [template]      - Complete setup workflow (default: basic)
  list                  - List available templates
  help                  - Show this help

Templates:
  basic                 - Basic cfg80211 and mac80211 support
  monitor               - Monitor mode support
  injection             - Frame injection support
  android               - Android optimized configuration

Examples:
  $0 setup monitor      - Setup with monitor mode template
  $0 template injection - Apply frame injection template
  $0 interactive        - Interactive configuration
  $0 validate           - Validate current configuration
  $0 conflicts          - Check for conflicts

For more information, see the backports documentation.
EOF
}

# Main function
main() {
    # Check if required scripts exist
    if ! check_dependencies; then
        exit 1
    fi
    
    case "${1:-help}" in
        validate)
            validate_dependencies
            ;;
        conflicts)
            detect_conflicts
            ;;
        resolve)
            resolve_conflicts
            ;;
        template)
            if [ -z "$2" ]; then
                log_error "Template name required"
                echo "Available templates:"
                python3 "${SCRIPT_DIR}/resolve-backports-deps.py" --kernel-root "$KERNEL_ROOT" list
                exit 1
            fi
            apply_template "$2"
            ;;
        interactive)
            interactive_config
            ;;
        report)
            generate_report
            ;;
        setup)
            complete_setup "${2:-basic}"
            ;;
        list)
            python3 "${SCRIPT_DIR}/resolve-backports-deps.py" --kernel-root "$KERNEL_ROOT" list
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $1"
            echo
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"