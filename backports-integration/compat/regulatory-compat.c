/*
 * Regulatory Compliance Compatibility Layer Implementation
 * 
 * This file implements regulatory compliance enforcement across different
 * kernel versions with special focus on Android kernel 4.19 requirements.
 */

#include "regulatory-compat.h"
#include <linux/slab.h>
#include <linux/string.h>

/* Global regulatory context */
struct backports_regulatory_context *backports_global_regulatory_ctx = NULL;

/* Regulatory domain configurations */
static const struct {
    const char *alpha2;
    enum backports_regulatory_mode default_mode;
    bool monitor_allowed;
    bool injection_allowed;
    bool mesh_allowed;
    u32 max_power_2ghz;
    u32 max_power_5ghz;
} regulatory_domains[] = {
    { "US", BACKPORTS_REG_STANDARD, true,  true,  true,  30, 30 },
    { "EU", BACKPORTS_REG_STRICT,   true,  false, true,  20, 23 },
    { "JP", BACKPORTS_REG_STRICT,   false, false, true,  20, 23 },
    { "CN", BACKPORTS_REG_STRICT,   false, false, false, 20, 30 },
    { "CA", BACKPORTS_REG_STANDARD, true,  true,  true,  30, 30 },
    { "AU", BACKPORTS_REG_STANDARD, true,  false, true,  20, 23 },
    { "00", BACKPORTS_REG_PERMISSIVE, true, true,  true,  20, 20 }, /* World domain */
};

/**
 * backports_regulatory_init - Initialize regulatory context
 * @ctx: Regulatory context
 */
int backports_regulatory_init(struct backports_regulatory_context *ctx)
{
    if (!ctx)
        return -EINVAL;

    memset(ctx, 0, sizeof(*ctx));
    
    /* Initialize default values */
    ctx->mode = BACKPORTS_REG_STANDARD;
    strncpy(ctx->alpha2, "00", sizeof(ctx->alpha2)); /* World domain */
    ctx->enforcement_enabled = true;
    ctx->monitor_mode_allowed = true;
    ctx->packet_injection_allowed = true;
    ctx->mesh_networking_allowed = true;
    
    /* Initialize frequency restrictions */
    ctx->freq_restrictions.enabled = false;
    ctx->freq_restrictions.min_freq_khz = BACKPORTS_REG_FREQ_2GHZ_START;
    ctx->freq_restrictions.max_freq_khz = BACKPORTS_REG_FREQ_5GHZ_END;
    ctx->freq_restrictions.max_power_dbm = 30;
    
    /* Initialize channel restrictions */
    ctx->channel_restrictions.enabled = false;
    ctx->channel_restrictions.num_2ghz_channels = 0;
    ctx->channel_restrictions.num_5ghz_channels = 0;
    
    /* Initialize feature restrictions */
    ctx->feature_restrictions.dfs_required = false;
    ctx->feature_restrictions.indoor_only = false;
    ctx->feature_restrictions.no_outdoor = false;
    ctx->feature_restrictions.passive_scan_only = false;
    ctx->feature_restrictions.no_ibss = false;
    ctx->feature_restrictions.radar_detection_required = false;
    
#if BACKPORTS_ANDROID_KERNEL
    /* Initialize Android-specific restrictions */
    backports_regulatory_android_init(ctx);
#endif
    
    mutex_init(&ctx->lock);
    
    backports_pr_info("Regulatory compliance initialized (domain: %s, mode: %d)\n",
                     ctx->alpha2, ctx->mode);
    return 0;
}

/**
 * backports_regulatory_exit - Cleanup regulatory context
 * @ctx: Regulatory context
 */
void backports_regulatory_exit(struct backports_regulatory_context *ctx)
{
    if (!ctx)
        return;

    mutex_lock(&ctx->lock);
    
    backports_pr_info("Regulatory compliance cleanup (violations: %lu, blocked: %lu)\n",
                     ctx->violations_detected, ctx->violations_blocked);
    
    mutex_unlock(&ctx->lock);
}

/**
 * backports_regulatory_set_domain - Set regulatory domain
 * @ctx: Regulatory context
 * @alpha2: Two-character country code
 */
int backports_regulatory_set_domain(struct backports_regulatory_context *ctx, const char *alpha2)
{
    int i;
    
    if (!ctx || !alpha2 || strlen(alpha2) != 2)
        return -EINVAL;

    mutex_lock(&ctx->lock);
    
    /* Find domain configuration */
    for (i = 0; i < ARRAY_SIZE(regulatory_domains); i++) {
        if (strncmp(regulatory_domains[i].alpha2, alpha2, 2) == 0) {
            strncpy(ctx->alpha2, alpha2, sizeof(ctx->alpha2));
            ctx->mode = regulatory_domains[i].default_mode;
            ctx->monitor_mode_allowed = regulatory_domains[i].monitor_allowed;
            ctx->packet_injection_allowed = regulatory_domains[i].injection_allowed;
            ctx->mesh_networking_allowed = regulatory_domains[i].mesh_allowed;
            
            /* Update power limits */
            ctx->freq_restrictions.max_power_dbm = regulatory_domains[i].max_power_2ghz;
            
            backports_pr_info("Regulatory domain set to %s (mode: %d)\n", alpha2, ctx->mode);
            mutex_unlock(&ctx->lock);
            return 0;
        }
    }
    
    /* Unknown domain - use world domain settings */
    strncpy(ctx->alpha2, alpha2, sizeof(ctx->alpha2));
    ctx->mode = BACKPORTS_REG_PERMISSIVE;
    ctx->monitor_mode_allowed = false;
    ctx->packet_injection_allowed = false;
    ctx->mesh_networking_allowed = false;
    
    backports_pr_warn("Unknown regulatory domain %s, using restrictive settings\n", alpha2);
    
    mutex_unlock(&ctx->lock);
    return 0;
}

/**
 * backports_regulatory_get_domain - Get current regulatory domain
 * @ctx: Regulatory context
 * @alpha2: Buffer for country code
 */
int backports_regulatory_get_domain(struct backports_regulatory_context *ctx, char *alpha2)
{
    if (!ctx || !alpha2)
        return -EINVAL;

    mutex_lock(&ctx->lock);
    strncpy(alpha2, ctx->alpha2, 3);
    mutex_unlock(&ctx->lock);
    
    return 0;
}

/**
 * backports_regulatory_set_mode - Set regulatory enforcement mode
 * @ctx: Regulatory context
 * @mode: Enforcement mode
 */
int backports_regulatory_set_mode(struct backports_regulatory_context *ctx, enum backports_regulatory_mode mode)
{
    if (!ctx)
        return -EINVAL;

    mutex_lock(&ctx->lock);
    ctx->mode = mode;
    
    /* Adjust enforcement based on mode */
    switch (mode) {
    case BACKPORTS_REG_PERMISSIVE:
        ctx->enforcement_enabled = false;
        break;
    case BACKPORTS_REG_STANDARD:
        ctx->enforcement_enabled = true;
        break;
    case BACKPORTS_REG_STRICT:
        ctx->enforcement_enabled = true;
        ctx->feature_restrictions.dfs_required = true;
        break;
    case BACKPORTS_REG_ANDROID:
        ctx->enforcement_enabled = true;
#if BACKPORTS_ANDROID_KERNEL
        ctx->android_restrictions.location_permission_required = true;
        ctx->android_restrictions.background_scan_restricted = true;
#endif
        break;
    }
    
    mutex_unlock(&ctx->lock);
    
    backports_pr_info("Regulatory mode set to %d\n", mode);
    return 0;
}

/**
 * backports_regulatory_get_mode - Get current regulatory enforcement mode
 * @ctx: Regulatory context
 */
enum backports_regulatory_mode backports_regulatory_get_mode(struct backports_regulatory_context *ctx)
{
    enum backports_regulatory_mode mode;
    
    if (!ctx)
        return BACKPORTS_REG_PERMISSIVE;

    mutex_lock(&ctx->lock);
    mode = ctx->mode;
    mutex_unlock(&ctx->lock);
    
    return mode;
}

/**
 * backports_regulatory_check_frequency - Check frequency compliance
 * @ctx: Regulatory context
 * @freq_khz: Frequency in kHz
 * @power_dbm: Power in dBm
 * @result: Check result
 */
int backports_regulatory_check_frequency(struct backports_regulatory_context *ctx,
                                        u32 freq_khz, u32 power_dbm,
                                        struct backports_regulatory_result *result)
{
    if (!ctx || !result)
        return -EINVAL;

    memset(result, 0, sizeof(*result));
    result->allowed = true;
    
    mutex_lock(&ctx->lock);
    
    if (!ctx->enforcement_enabled) {
        mutex_unlock(&ctx->lock);
        return 0;
    }
    
    /* Check frequency range */
    if (ctx->freq_restrictions.enabled) {
        if (freq_khz < ctx->freq_restrictions.min_freq_khz ||
            freq_khz > ctx->freq_restrictions.max_freq_khz) {
            result->allowed = false;
            result->violation_type = BACKPORTS_REG_VIOLATION_FREQUENCY;
            snprintf(result->violation_reason, sizeof(result->violation_reason),
                    "Frequency %u kHz outside allowed range %u-%u kHz",
                    freq_khz, ctx->freq_restrictions.min_freq_khz,
                    ctx->freq_restrictions.max_freq_khz);
            
            /* Suggest closest allowed frequency */
            if (freq_khz < ctx->freq_restrictions.min_freq_khz)
                result->suggested_frequency = ctx->freq_restrictions.min_freq_khz;
            else
                result->suggested_frequency = ctx->freq_restrictions.max_freq_khz;
            
            ctx->violations_detected++;
            goto out;
        }
    }
    
    /* Check power limits */
    if (power_dbm > ctx->freq_restrictions.max_power_dbm) {
        result->allowed = false;
        result->violation_type = BACKPORTS_REG_VIOLATION_POWER;
        snprintf(result->violation_reason, sizeof(result->violation_reason),
                "Power %u dBm exceeds maximum %u dBm",
                power_dbm, ctx->freq_restrictions.max_power_dbm);
        result->suggested_power = ctx->freq_restrictions.max_power_dbm;
        
        ctx->violations_detected++;
        goto out;
    }
    
    /* Domain-specific checks */
    if (strncmp(ctx->alpha2, "CN", 2) == 0) {
        /* China: Only allow ISM bands */
        if (backports_regulatory_is_5ghz_freq(freq_khz) &&
            (freq_khz < 5725000 || freq_khz > 5850000)) {
            result->allowed = false;
            result->violation_type = BACKPORTS_REG_VIOLATION_FREQUENCY;
            snprintf(result->violation_reason, sizeof(result->violation_reason),
                    "5GHz frequency %u kHz not allowed in China (only 5.725-5.850 GHz)",
                    freq_khz);
            result->suggested_frequency = 5745000; /* Channel 149 */
            ctx->violations_detected++;
            goto out;
        }
    }
    
out:
    if (!result->allowed && ctx->mode >= BACKPORTS_REG_STANDARD) {
        ctx->violations_blocked++;
    }
    
    mutex_unlock(&ctx->lock);
    return 0;
}

/**
 * backports_regulatory_check_channel - Check channel compliance
 * @ctx: Regulatory context
 * @channel: Channel number
 * @band: Frequency band
 * @result: Check result
 */
int backports_regulatory_check_channel(struct backports_regulatory_context *ctx,
                                      u8 channel, enum nl80211_band band,
                                      struct backports_regulatory_result *result)
{
    u32 freq_khz;
    
    if (!ctx || !result)
        return -EINVAL;

    /* Convert channel to frequency */
    switch (band) {
    case NL80211_BAND_2GHZ:
        if (channel < 1 || channel > 14) {
            result->allowed = false;
            result->violation_type = BACKPORTS_REG_VIOLATION_CHANNEL;
            snprintf(result->violation_reason, sizeof(result->violation_reason),
                    "Invalid 2.4GHz channel %u (valid: 1-14)", channel);
            return 0;
        }
        
        if (channel == 14)
            freq_khz = 2484000; /* Channel 14 */
        else
            freq_khz = backports_regulatory_channel_to_freq_2ghz(channel);
        break;
        
    case NL80211_BAND_5GHZ:
        /* Simplified 5GHz channel to frequency conversion */
        if (channel >= 36 && channel <= 64)
            freq_khz = 5000000 + channel * 5000;
        else if (channel >= 100 && channel <= 144)
            freq_khz = 5000000 + channel * 5000;
        else if (channel >= 149 && channel <= 165)
            freq_khz = 5000000 + channel * 5000;
        else {
            result->allowed = false;
            result->violation_type = BACKPORTS_REG_VIOLATION_CHANNEL;
            snprintf(result->violation_reason, sizeof(result->violation_reason),
                    "Invalid 5GHz channel %u", channel);
            return 0;
        }
        break;
        
    default:
        result->allowed = false;
        result->violation_type = BACKPORTS_REG_VIOLATION_CHANNEL;
        snprintf(result->violation_reason, sizeof(result->violation_reason),
                "Unsupported band %d", band);
        return 0;
    }
    
    /* Check frequency compliance */
    return backports_regulatory_check_frequency(ctx, freq_khz, 20, result);
}

/**
 * backports_regulatory_check_feature - Check feature compliance
 * @ctx: Regulatory context
 * @iftype: Interface type
 * @feature_flags: Feature flags
 * @result: Check result
 */
int backports_regulatory_check_feature(struct backports_regulatory_context *ctx,
                                      enum nl80211_iftype iftype,
                                      u32 feature_flags,
                                      struct backports_regulatory_result *result)
{
    if (!ctx || !result)
        return -EINVAL;

    memset(result, 0, sizeof(*result));
    result->allowed = true;
    
    mutex_lock(&ctx->lock);
    
    if (!ctx->enforcement_enabled) {
        mutex_unlock(&ctx->lock);
        return 0;
    }
    
    /* Check monitor mode */
    if ((iftype == NL80211_IFTYPE_MONITOR || 
         (feature_flags & BACKPORTS_REG_FEATURE_MONITOR_MODE)) &&
        !ctx->monitor_mode_allowed) {
        result->allowed = false;
        result->violation_type = BACKPORTS_REG_VIOLATION_FEATURE;
        snprintf(result->violation_reason, sizeof(result->violation_reason),
                "Monitor mode not allowed in domain %s", ctx->alpha2);
        ctx->feature_denials++;
        goto out;
    }
    
    /* Check packet injection */
    if ((feature_flags & BACKPORTS_REG_FEATURE_PACKET_INJECTION) &&
        !ctx->packet_injection_allowed) {
        result->allowed = false;
        result->violation_type = BACKPORTS_REG_VIOLATION_FEATURE;
        snprintf(result->violation_reason, sizeof(result->violation_reason),
                "Packet injection not allowed in domain %s", ctx->alpha2);
        ctx->feature_denials++;
        goto out;
    }
    
    /* Check mesh networking */
    if ((iftype == NL80211_IFTYPE_MESH_POINT ||
         (feature_flags & BACKPORTS_REG_FEATURE_MESH_NETWORKING)) &&
        !ctx->mesh_networking_allowed) {
        result->allowed = false;
        result->violation_type = BACKPORTS_REG_VIOLATION_FEATURE;
        snprintf(result->violation_reason, sizeof(result->violation_reason),
                "Mesh networking not allowed in domain %s", ctx->alpha2);
        ctx->feature_denials++;
        goto out;
    }
    
    /* Check IBSS restrictions */
    if (iftype == NL80211_IFTYPE_ADHOC && ctx->feature_restrictions.no_ibss) {
        result->allowed = false;
        result->violation_type = BACKPORTS_REG_VIOLATION_FEATURE;
        snprintf(result->violation_reason, sizeof(result->violation_reason),
                "IBSS/Ad-hoc mode restricted");
        ctx->feature_denials++;
        goto out;
    }
    
#if BACKPORTS_ANDROID_KERNEL
    /* Android-specific permission checks */
    if (ctx->mode == BACKPORTS_REG_ANDROID) {
        if (!backports_regulatory_android_check_permission(ctx, BACKPORTS_REG_VIOLATION_PERMISSION)) {
            result->allowed = false;
            result->violation_type = BACKPORTS_REG_VIOLATION_PERMISSION;
            snprintf(result->violation_reason, sizeof(result->violation_reason),
                    "Android permission denied");
            ctx->feature_denials++;
            goto out;
        }
    }
#endif
    
out:
    mutex_unlock(&ctx->lock);
    return 0;
}

/**
 * backports_regulatory_is_monitor_allowed - Check if monitor mode is allowed
 * @ctx: Regulatory context
 */
bool backports_regulatory_is_monitor_allowed(struct backports_regulatory_context *ctx)
{
    bool allowed;
    
    if (!ctx)
        return false;

    mutex_lock(&ctx->lock);
    allowed = ctx->monitor_mode_allowed && ctx->enforcement_enabled;
    mutex_unlock(&ctx->lock);
    
    return allowed;
}

/**
 * backports_regulatory_is_injection_allowed - Check if packet injection is allowed
 * @ctx: Regulatory context
 */
bool backports_regulatory_is_injection_allowed(struct backports_regulatory_context *ctx)
{
    bool allowed;
    
    if (!ctx)
        return false;

    mutex_lock(&ctx->lock);
    allowed = ctx->packet_injection_allowed && ctx->enforcement_enabled;
    mutex_unlock(&ctx->lock);
    
    return allowed;
}

/**
 * backports_regulatory_is_mesh_allowed - Check if mesh networking is allowed
 * @ctx: Regulatory context
 */
bool backports_regulatory_is_mesh_allowed(struct backports_regulatory_context *ctx)
{
    bool allowed;
    
    if (!ctx)
        return false;

    mutex_lock(&ctx->lock);
    allowed = ctx->mesh_networking_allowed && ctx->enforcement_enabled;
    mutex_unlock(&ctx->lock);
    
    return allowed;
}

/**
 * backports_regulatory_enforce_restrictions - Enforce restrictions on wiphy
 * @ctx: Regulatory context
 * @wiphy: Wireless hardware description
 */
int backports_regulatory_enforce_restrictions(struct backports_regulatory_context *ctx,
                                            struct wiphy *wiphy)
{
    if (!ctx || !wiphy)
        return -EINVAL;

    mutex_lock(&ctx->lock);
    
    if (!ctx->enforcement_enabled) {
        mutex_unlock(&ctx->lock);
        return 0;
    }
    
    /* Disable features based on regulatory restrictions */
    if (!ctx->monitor_mode_allowed) {
        wiphy->interface_modes &= ~BIT(NL80211_IFTYPE_MONITOR);
    }
    
    if (!ctx->mesh_networking_allowed) {
        wiphy->interface_modes &= ~BIT(NL80211_IFTYPE_MESH_POINT);
    }
    
    if (ctx->feature_restrictions.no_ibss) {
        wiphy->interface_modes &= ~BIT(NL80211_IFTYPE_ADHOC);
    }
    
    mutex_unlock(&ctx->lock);
    
    backports_pr_debug("Regulatory restrictions enforced on wiphy\n");
    return 0;
}

/**
 * backports_regulatory_get_statistics - Get regulatory statistics
 */
int backports_regulatory_get_statistics(struct backports_regulatory_context *ctx,
                                       unsigned long *violations_detected,
                                       unsigned long *violations_blocked,
                                       unsigned long *feature_denials)
{
    if (!ctx)
        return -EINVAL;

    mutex_lock(&ctx->lock);
    if (violations_detected) *violations_detected = ctx->violations_detected;
    if (violations_blocked) *violations_blocked = ctx->violations_blocked;
    if (feature_denials) *feature_denials = ctx->feature_denials;
    mutex_unlock(&ctx->lock);
    
    return 0;
}

#if BACKPORTS_ANDROID_KERNEL

/**
 * backports_regulatory_android_init - Initialize Android regulatory restrictions
 */
int backports_regulatory_android_init(struct backports_regulatory_context *ctx)
{
    if (!ctx)
        return -EINVAL;

    ctx->android_restrictions.location_permission_required = false;
    ctx->android_restrictions.background_scan_restricted = false;
    ctx->android_restrictions.hotspot_restricted = false;
    ctx->android_restrictions.num_allowed_uids = 0;
    
    /* Add default allowed UIDs */
    backports_regulatory_android_add_allowed_uid(ctx, 0);    /* root */
    backports_regulatory_android_add_allowed_uid(ctx, 1010); /* wifi */
    backports_regulatory_android_add_allowed_uid(ctx, 3005); /* net_admin */
    
    backports_pr_debug("Android regulatory restrictions initialized\n");
    return 0;
}

/**
 * backports_regulatory_android_check_permission - Check Android permission
 */
bool backports_regulatory_android_check_permission(struct backports_regulatory_context *ctx,
                                                  enum backports_regulatory_violation violation)
{
    uid_t current_uid;
    int i;
    
    if (!ctx)
        return false;

    current_uid = current_uid().val;
    
    /* Check if UID is in allowed list */
    for (i = 0; i < ctx->android_restrictions.num_allowed_uids; i++) {
        if (ctx->android_restrictions.allowed_uids[i] == current_uid)
            return true;
    }
    
    /* Check specific permissions based on violation type */
    switch (violation) {
    case BACKPORTS_REG_VIOLATION_FEATURE:
        /* Feature access requires NET_RAW or NET_ADMIN capability */
        return capable(CAP_NET_RAW) || capable(CAP_NET_ADMIN);
        
    case BACKPORTS_REG_VIOLATION_PERMISSION:
        /* General permission check */
        return capable(CAP_NET_ADMIN);
        
    default:
        return false;
    }
}

/**
 * backports_regulatory_android_add_allowed_uid - Add allowed UID
 */
int backports_regulatory_android_add_allowed_uid(struct backports_regulatory_context *ctx, uid_t uid)
{
    if (!ctx || ctx->android_restrictions.num_allowed_uids >= 16)
        return -EINVAL;

    ctx->android_restrictions.allowed_uids[ctx->android_restrictions.num_allowed_uids++] = uid;
    backports_pr_debug("Added allowed UID: %u\n", uid);
    return 0;
}

/**
 * backports_regulatory_android_remove_allowed_uid - Remove allowed UID
 */
int backports_regulatory_android_remove_allowed_uid(struct backports_regulatory_context *ctx, uid_t uid)
{
    int i, j;
    
    if (!ctx)
        return -EINVAL;

    for (i = 0; i < ctx->android_restrictions.num_allowed_uids; i++) {
        if (ctx->android_restrictions.allowed_uids[i] == uid) {
            /* Shift remaining UIDs */
            for (j = i; j < ctx->android_restrictions.num_allowed_uids - 1; j++) {
                ctx->android_restrictions.allowed_uids[j] = 
                    ctx->android_restrictions.allowed_uids[j + 1];
            }
            ctx->android_restrictions.num_allowed_uids--;
            backports_pr_debug("Removed allowed UID: %u\n", uid);
            return 0;
        }
    }
    
    return -ENOENT;
}

/**
 * backports_regulatory_android_is_location_required - Check if location permission is required
 */
bool backports_regulatory_android_is_location_required(struct backports_regulatory_context *ctx)
{
    if (!ctx)
        return false;

    return ctx->android_restrictions.location_permission_required;
}

#endif /* BACKPORTS_ANDROID_KERNEL */

/**
 * backports_regulatory_global_init - Initialize global regulatory context
 */
int backports_regulatory_global_init(void)
{
    if (backports_global_regulatory_ctx)
        return 0; /* Already initialized */

    backports_global_regulatory_ctx = kzalloc(sizeof(*backports_global_regulatory_ctx), GFP_KERNEL);
    if (!backports_global_regulatory_ctx)
        return -ENOMEM;

    return backports_regulatory_init(backports_global_regulatory_ctx);
}

/**
 * backports_regulatory_global_exit - Cleanup global regulatory context
 */
void backports_regulatory_global_exit(void)
{
    if (backports_global_regulatory_ctx) {
        backports_regulatory_exit(backports_global_regulatory_ctx);
        kfree(backports_global_regulatory_ctx);
        backports_global_regulatory_ctx = NULL;
    }
}