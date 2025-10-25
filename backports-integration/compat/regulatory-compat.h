#ifndef BACKPORTS_REGULATORY_COMPAT_H
#define BACKPORTS_REGULATORY_COMPAT_H

/*
 * Regulatory Compliance Compatibility Layer
 * 
 * This header provides regulatory compliance enforcement across different
 * kernel versions with special focus on Android kernel 4.19 requirements.
 */

#include "compat.h"
#include <net/cfg80211.h>
#include <net/regulatory.h>

/* Regulatory enforcement levels */
enum backports_regulatory_mode {
    BACKPORTS_REG_PERMISSIVE,    /* Minimal enforcement */
    BACKPORTS_REG_STANDARD,      /* Standard enforcement */
    BACKPORTS_REG_STRICT,        /* Strict enforcement */
    BACKPORTS_REG_ANDROID        /* Android-specific enforcement */
};

/* Regulatory compliance context */
struct backports_regulatory_context {
    enum backports_regulatory_mode mode;
    char alpha2[3];              /* Current regulatory domain */
    bool enforcement_enabled;
    bool monitor_mode_allowed;
    bool packet_injection_allowed;
    bool mesh_networking_allowed;
    
    /* Frequency restrictions */
    struct {
        bool enabled;
        u32 min_freq_khz;
        u32 max_freq_khz;
        u32 max_power_dbm;
    } freq_restrictions;
    
    /* Channel restrictions */
    struct {
        bool enabled;
        u8 allowed_channels_2ghz[14];  /* Channels 1-14 */
        u8 allowed_channels_5ghz[64];  /* 5GHz channels */
        u8 num_2ghz_channels;
        u8 num_5ghz_channels;
    } channel_restrictions;
    
    /* Feature restrictions */
    struct {
        bool dfs_required;
        bool indoor_only;
        bool no_outdoor;
        bool passive_scan_only;
        bool no_ibss;
        bool radar_detection_required;
    } feature_restrictions;
    
    /* Android-specific restrictions */
#if BACKPORTS_ANDROID_KERNEL
    struct {
        bool location_permission_required;
        bool background_scan_restricted;
        bool hotspot_restricted;
        uid_t allowed_uids[16];
        int num_allowed_uids;
    } android_restrictions;
#endif
    
    /* Statistics */
    unsigned long violations_detected;
    unsigned long violations_blocked;
    unsigned long feature_denials;
    
    struct mutex lock;
};

/* Regulatory violation types */
enum backports_regulatory_violation {
    BACKPORTS_REG_VIOLATION_FREQUENCY,
    BACKPORTS_REG_VIOLATION_POWER,
    BACKPORTS_REG_VIOLATION_CHANNEL,
    BACKPORTS_REG_VIOLATION_FEATURE,
    BACKPORTS_REG_VIOLATION_PERMISSION,
    BACKPORTS_REG_VIOLATION_DFS
};

/* Regulatory check result */
struct backports_regulatory_result {
    bool allowed;
    enum backports_regulatory_violation violation_type;
    char violation_reason[128];
    u32 suggested_frequency;
    u32 suggested_power;
    u8 suggested_channel;
};

/* Function declarations */
extern int backports_regulatory_init(struct backports_regulatory_context *ctx);
extern void backports_regulatory_exit(struct backports_regulatory_context *ctx);

extern int backports_regulatory_set_domain(struct backports_regulatory_context *ctx, const char *alpha2);
extern int backports_regulatory_get_domain(struct backports_regulatory_context *ctx, char *alpha2);

extern int backports_regulatory_set_mode(struct backports_regulatory_context *ctx, enum backports_regulatory_mode mode);
extern enum backports_regulatory_mode backports_regulatory_get_mode(struct backports_regulatory_context *ctx);

extern int backports_regulatory_check_frequency(struct backports_regulatory_context *ctx,
                                               u32 freq_khz, u32 power_dbm,
                                               struct backports_regulatory_result *result);

extern int backports_regulatory_check_channel(struct backports_regulatory_context *ctx,
                                            u8 channel, enum nl80211_band band,
                                            struct backports_regulatory_result *result);

extern int backports_regulatory_check_feature(struct backports_regulatory_context *ctx,
                                            enum nl80211_iftype iftype,
                                            u32 feature_flags,
                                            struct backports_regulatory_result *result);

extern bool backports_regulatory_is_monitor_allowed(struct backports_regulatory_context *ctx);
extern bool backports_regulatory_is_injection_allowed(struct backports_regulatory_context *ctx);
extern bool backports_regulatory_is_mesh_allowed(struct backports_regulatory_context *ctx);

extern int backports_regulatory_enforce_restrictions(struct backports_regulatory_context *ctx,
                                                   struct wiphy *wiphy);

extern int backports_regulatory_get_statistics(struct backports_regulatory_context *ctx,
                                              unsigned long *violations_detected,
                                              unsigned long *violations_blocked,
                                              unsigned long *feature_denials);

/* Android-specific functions */
#if BACKPORTS_ANDROID_KERNEL
extern int backports_regulatory_android_init(struct backports_regulatory_context *ctx);
extern bool backports_regulatory_android_check_permission(struct backports_regulatory_context *ctx,
                                                         enum backports_regulatory_violation violation);
extern int backports_regulatory_android_add_allowed_uid(struct backports_regulatory_context *ctx, uid_t uid);
extern int backports_regulatory_android_remove_allowed_uid(struct backports_regulatory_context *ctx, uid_t uid);
extern bool backports_regulatory_android_is_location_required(struct backports_regulatory_context *ctx);
#endif

/* Kernel version compatibility */
#if BACKPORTS_NEW_REGULATORY_API
#define backports_regulatory_set_wiphy_regd(wiphy, rd) regulatory_set_wiphy_regd_sync_rtnl(wiphy, rd)
#else
#define backports_regulatory_set_wiphy_regd(wiphy, rd) regulatory_set_wiphy_regd(wiphy, rd)
#endif

/* Feature flags for regulatory checking */
#define BACKPORTS_REG_FEATURE_MONITOR_MODE    BIT(0)
#define BACKPORTS_REG_FEATURE_PACKET_INJECTION BIT(1)
#define BACKPORTS_REG_FEATURE_MESH_NETWORKING  BIT(2)
#define BACKPORTS_REG_FEATURE_IBSS            BIT(3)
#define BACKPORTS_REG_FEATURE_AP_MODE         BIT(4)
#define BACKPORTS_REG_FEATURE_P2P             BIT(5)
#define BACKPORTS_REG_FEATURE_DFS             BIT(6)

/* Regulatory domain definitions */
#define BACKPORTS_REG_DOMAIN_WORLD    "00"
#define BACKPORTS_REG_DOMAIN_US       "US"
#define BACKPORTS_REG_DOMAIN_EU       "EU"
#define BACKPORTS_REG_DOMAIN_JP       "JP"
#define BACKPORTS_REG_DOMAIN_CN       "CN"
#define BACKPORTS_REG_DOMAIN_CA       "CA"
#define BACKPORTS_REG_DOMAIN_AU       "AU"

/* Frequency band definitions */
#define BACKPORTS_REG_FREQ_2GHZ_START 2412000  /* 2.412 GHz in kHz */
#define BACKPORTS_REG_FREQ_2GHZ_END   2484000  /* 2.484 GHz in kHz */
#define BACKPORTS_REG_FREQ_5GHZ_START 5170000  /* 5.170 GHz in kHz */
#define BACKPORTS_REG_FREQ_5GHZ_END   5835000  /* 5.835 GHz in kHz */
#define BACKPORTS_REG_FREQ_6GHZ_START 5925000  /* 5.925 GHz in kHz */
#define BACKPORTS_REG_FREQ_6GHZ_END   7125000  /* 7.125 GHz in kHz */

/* Power limits (in dBm) */
#define BACKPORTS_REG_POWER_MAX_2GHZ  30
#define BACKPORTS_REG_POWER_MAX_5GHZ  30
#define BACKPORTS_REG_POWER_MAX_6GHZ  30

/* Channel definitions */
#define BACKPORTS_REG_CHANNEL_2GHZ_MIN  1
#define BACKPORTS_REG_CHANNEL_2GHZ_MAX  14
#define BACKPORTS_REG_CHANNEL_5GHZ_MIN  36
#define BACKPORTS_REG_CHANNEL_5GHZ_MAX  165

/* Macros for regulatory checking */
#define backports_regulatory_is_2ghz_freq(freq) \
    ((freq) >= BACKPORTS_REG_FREQ_2GHZ_START && (freq) <= BACKPORTS_REG_FREQ_2GHZ_END)

#define backports_regulatory_is_5ghz_freq(freq) \
    ((freq) >= BACKPORTS_REG_FREQ_5GHZ_START && (freq) <= BACKPORTS_REG_FREQ_5GHZ_END)

#define backports_regulatory_is_6ghz_freq(freq) \
    ((freq) >= BACKPORTS_REG_FREQ_6GHZ_START && (freq) <= BACKPORTS_REG_FREQ_6GHZ_END)

#define backports_regulatory_freq_to_channel_2ghz(freq) \
    (((freq) - BACKPORTS_REG_FREQ_2GHZ_START) / 5000 + 1)

#define backports_regulatory_channel_to_freq_2ghz(channel) \
    (BACKPORTS_REG_FREQ_2GHZ_START + ((channel) - 1) * 5000)

/* Conditional compilation helpers */
#ifdef CONFIG_CFG80211_CERTIFICATION_ONUS
#define BACKPORTS_HAS_CERTIFICATION_ONUS 1
#else
#define BACKPORTS_HAS_CERTIFICATION_ONUS 0
#endif

#ifdef CONFIG_CFG80211_REG_CELLULAR_HINTS
#define BACKPORTS_HAS_CELLULAR_HINTS 1
#else
#define BACKPORTS_HAS_CELLULAR_HINTS 0
#endif

#ifdef CONFIG_CFG80211_REG_RELAX_NO_IR
#define BACKPORTS_HAS_REG_RELAX_NO_IR 1
#else
#define BACKPORTS_HAS_REG_RELAX_NO_IR 0
#endif

/* Global regulatory context */
extern struct backports_regulatory_context *backports_global_regulatory_ctx;

/* Initialization and cleanup */
extern int backports_regulatory_global_init(void);
extern void backports_regulatory_global_exit(void);

#endif /* BACKPORTS_REGULATORY_COMPAT_H */