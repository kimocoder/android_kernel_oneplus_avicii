#!/bin/bash
#
# Comprehensive Backports Validation Script
#
# This script runs all validation checks in sequence and provides
# a unified interface for backports configuration validation.
#

set -e

# Configuration
SCRIPT_DIR="$(dirname "$0")"
KERNEL_ROOT="${1:-.}"
MODE="${2:-full}"

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

# Check if required scripts exist
check_dependencies() {
    local missing=0
    
    if [ ! -f "$SCRIPT_DIR/validate-backports-config.py" ]; then
        log_error "validate-backports-config.py not found"
        missing=$((missing + 1))
    fi
    
    if [ ! -f "$SCRIPT_DIR/consistency-checker.py" ]; then
        log_error "consistency-checker.py not found"
        missing=$((missing + 1))
    fi
    
    if [ ! -f "$SCRIPT_DIR/kconfig-helper.sh" ]; then
        log_error "kconfig-helper.sh not found"
        missing=$((missing + 1))
    fi
    
    if [ $missing -gt 0 ]; then
        log_error "$missing required scripts missing"
        return 1
    fi
    
    return 0
}

# Run configuration validation
run_config_validation() {
    log_info "Running configuration validation..."
    
    if python3 "$SCRIPT_DIR/validate-backports-config.py" --kernel-root "$KERNEL_ROOT"; then
        log_success "Configuration validation passed"
        return 0
    else
        log_error "Configuration validation failed"
        return 1
    fi
}

# Run consistency checking
run_consistency_check() {
    log_info "Running consistency checking..."
    
    if python3 "$SCRIPT_DIR/consistency-checker.py" --kernel-root "$KERNEL_ROOT"; then
        log_success "Consistency checking passed"
        return 0
    else
        log_error "Consistency checking failed"
        return 1
    fi
}

# Run pre-build validation
run_pre_build_validation() {
    log_info "Running pre-build validation..."
    
    if python3 "$SCRIPT_DIR/consistency-checker.py" --kernel-root "$KERNEL_ROOT" --pre-build; then
        log_success "Pre-build validation passed"
        return 0
    else
        log_error "Pre-build validation failed"
        return 1
    fi
}

# Apply automated fixes
apply_fixes() {
    log_info "Applying automated fixes..."
    
    local fixes_applied=0
    
    # Try consistency checker auto-fix
    if python3 "$SCRIPT_DIR/consistency-checker.py" --kernel-root "$KERNEL_ROOT" --auto-fix; then
        log_success "Consistency checker fixes applied"
        fixes_applied=$((fixes_applied + 1))
    fi
    
    # Try kconfig helper auto-fix
    if [ -f "$SCRIPT_DIR/kconfig-helper.sh" ]; then
        if "$SCRIPT_DIR/kconfig-helper.sh" fix; then
            log_success "Kconfig helper fixes applied"
            fixes_applied=$((fixes_applied + 1))
        fi
    fi
    
    if [ $fixes_applied -gt 0 ]; then
        log_success "Applied $fixes_applied automated fixes"
        return 0
    else
        log_warning "No automated fixes were applied"
        return 1
    fi
}

# Show configuration status
show_status() {
    log_info "Backports configuration status:"
    
    if [ -f "$SCRIPT_DIR/kconfig-helper.sh" ]; then
        "$SCRIPT_DIR/kconfig-helper.sh" status
    else
        log_warning "Kconfig helper not available for status display"
    fi
}

# Generate comprehensive report
generate_report() {
    local report_file="$1"
    
    log_info "Generating comprehensive validation report..."
    
    {
        echo "Backports Configuration Validation Report"
        echo "========================================"
        echo "Generated: $(date)"
        echo "Kernel Root: $KERNEL_ROOT"
        echo ""
        
        echo "Configuration Validation:"
        echo "------------------------"
        if python3 "$SCRIPT_DIR/validate-backports-config.py" --kernel-root "$KERNEL_ROOT" --json 2>/dev/null; then
            echo "Status: PASSED"
        else
            echo "Status: FAILED"
        fi
        echo ""
        
        echo "Consistency Checking:"
        echo "--------------------"
        if python3 "$SCRIPT_DIR/consistency-checker.py" --kernel-root "$KERNEL_ROOT" --json 2>/dev/null; then
            echo "Status: PASSED"
        else
            echo "Status: FAILED"
        fi
        echo ""
        
        echo "Configuration Status:"
        echo "--------------------"
        if [ -f "$SCRIPT_DIR/kconfig-helper.sh" ]; then
            "$SCRIPT_DIR/kconfig-helper.sh" status
        fi
        
    } > "$report_file"
    
    log_success "Report generated: $report_file"
}

# Main validation function
run_full_validation() {
    log_info "Starting comprehensive backports validation"
    echo "=============================================="
    
    local overall_success=true
    
    # 1. Configuration validation
    echo ""
    echo "1️⃣  Configuration Validation"
    echo "----------------------------"
    if ! run_config_validation; then
        overall_success=false
    fi
    
    # 2. Consistency checking
    echo ""
    echo "2️⃣  Consistency Checking"
    echo "------------------------"
    if ! run_consistency_check; then
        overall_success=false
    fi
    
    # 3. Show status
    echo ""
    echo "3️⃣  Configuration Status"
    echo "------------------------"
    show_status
    
    # Summary
    echo ""
    echo "📊 VALIDATION SUMMARY"
    echo "===================="
    if [ "$overall_success" = true ]; then
        log_success "All validations passed - configuration is ready"
        return 0
    else
        log_error "Some validations failed - review issues above"
        log_info "Run with 'fix' mode to apply automated fixes"
        return 1
    fi
}

# Usage information
show_usage() {
    echo "Usage: $0 [kernel_root] [mode]"
    echo ""
    echo "Modes:"
    echo "  full      - Run complete validation suite (default)"
    echo "  pre-build - Run pre-build validation only"
    echo "  config    - Run configuration validation only"
    echo "  consistency - Run consistency checking only"
    echo "  fix       - Apply automated fixes"
    echo "  status    - Show configuration status"
    echo "  report    - Generate validation report"
    echo "  help      - Show this help"
    echo ""
    echo "Examples:"
    echo "  $0                    # Full validation in current directory"
    echo "  $0 /path/to/kernel    # Full validation in specified directory"
    echo "  $0 . pre-build       # Pre-build validation only"
    echo "  $0 . fix             # Apply automated fixes"
    echo "  $0 . status          # Show configuration status"
}

# Main execution
main() {
    # Check dependencies
    if ! check_dependencies; then
        exit 1
    fi
    
    # Execute based on mode
    case "$MODE" in
        "full")
            run_full_validation
            ;;
        "pre-build")
            run_pre_build_validation
            ;;
        "config")
            run_config_validation
            ;;
        "consistency")
            run_consistency_check
            ;;
        "fix")
            apply_fixes
            ;;
        "status")
            show_status
            ;;
        "report")
            generate_report "backports-validation-report.txt"
            ;;
        "help"|"--help"|"-h")
            show_usage
            ;;
        *)
            log_error "Unknown mode: $MODE"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"