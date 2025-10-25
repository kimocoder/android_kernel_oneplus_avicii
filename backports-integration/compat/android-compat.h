#ifndef BACKPORTS_ANDROID_COMPAT_H
#define BACKPORTS_ANDROID_COMPAT_H

/*
 * Android-Specific Compatibility Layer
 * 
 * This header provides Android kernel 4.19 specific compatibility
 * and integration with Android's wireless framework.
 */

#include "compat.h"

#if BACKPORTS_ANDROID_KERNEL

#include <linux/android_aid.h>

/* Android property system integration */
#define BACKPORTS_PROP_NAME_MAX 32
#define BACKPORTS_PROP_VALUE_MAX 92

/* Android UID/GID definitions for wireless */
#define BACKPORTS_AID_WIFI      1010
#define BACKPORTS_AID_DHCP      1014
#define BACKPORTS_AID_NET_ADMIN 3005
#define BACKPORTS_AID_NET_RAW   3004

/* Android power management integration */
struct backports_android_pm {
    struct wake_lock wifi_wake_lock;
    struct wake_lock scan_wake_lock;
    bool pm_enabled;
    bool early_suspend_registered;
};

/* Android security context */
struct backports_android_security {
    uid_t wifi_uid;
    gid_t wifi_gid;
    bool permission_checked;
    bool monitor_allowed;
    bool injection_allowed;
};

/* Android wireless framework integration */
struct backports_android_wifi {
    struct backports_android_pm pm;
    struct backports_android_security security;
    char country_code[3];
    bool framework_ready;
};

/* Android-specific function declarations */
extern int backports_android_init(void);
extern void backports_android_exit(void);

/* Power management functions */
extern int backports_android_pm_init(struct backports_android_pm *pm);
extern void backports_android_pm_exit(struct backports_android_pm *pm);
extern void backports_android_pm_stay_awake(struct backports_android_pm *pm, const char *reason);
extern void backports_android_pm_relax(struct backports_android_pm *pm, const char *reason);

/* Security functions */
extern int backports_android_security_init(struct backports_android_security *sec);
extern bool backports_android_check_wifi_permission(void);
extern bool backports_android_check_monitor_permission(void);
extern bool backports_android_check_injection_permission(void);

/* Framework integration */
extern int backports_android_notify_scan_start(void);
extern int backports_android_notify_scan_complete(void);
extern int backports_android_notify_connect(const char *ssid);
extern int backports_android_notify_disconnect(void);

/* Property system helpers */
extern int backports_android_set_wifi_property(const char *key, const char *value);
extern int backports_android_get_wifi_property(const char *key, char *value, const char *default_val);

/* Regulatory integration */
extern int backports_android_set_country_code(const char *alpha2);
extern int backports_android_get_country_code(char *alpha2);

/* Memory optimization for Android */
extern void *backports_android_kmalloc(size_t size, gfp_t flags);
extern void *backports_android_kzalloc(size_t size, gfp_t flags);
extern void backports_android_kfree(const void *ptr);

/* Android logging integration */
#define backports_android_log_info(fmt, ...) \
    pr_info("backports-wifi: " fmt, ##__VA_ARGS__)

#define backports_android_log_warn(fmt, ...) \
    pr_warn("backports-wifi: " fmt, ##__VA_ARGS__)

#define backports_android_log_err(fmt, ...) \
    pr_err("backports-wifi: " fmt, ##__VA_ARGS__)

#define backports_android_log_debug(fmt, ...) \
    pr_debug("backports-wifi: " fmt, ##__VA_ARGS__)

/* Android-specific macros */
#define BACKPORTS_ANDROID_WIFI_SERVICE_NAME "backports-wifi"
#define BACKPORTS_ANDROID_PROP_PREFIX "backports.wifi."

/* Conditional compilation helpers */
#ifdef CONFIG_ANDROID_WAKELOCK
#define BACKPORTS_HAS_ANDROID_WAKELOCK 1
#else
#define BACKPORTS_HAS_ANDROID_WAKELOCK 0
#endif

#ifdef CONFIG_ANDROID_POWER
#define BACKPORTS_HAS_ANDROID_POWER 1
#else
#define BACKPORTS_HAS_ANDROID_POWER 0
#endif

#ifdef CONFIG_ANDROID_PARANOID_NETWORK
#define BACKPORTS_HAS_ANDROID_PARANOID 1
#else
#define BACKPORTS_HAS_ANDROID_PARANOID 0
#endif

/* Android kernel 4.19 specific optimizations */
#if BACKPORTS_ANDROID_4_19

/* Memory management optimizations */
#define BACKPORTS_ANDROID_USE_ATOMIC_ALLOC 1
#define BACKPORTS_ANDROID_OPTIMIZE_POWER 1
#define BACKPORTS_ANDROID_FAST_SUSPEND 1

/* Network namespace compatibility */
#define backports_android_net_ns() (&init_net)

/* Process context helpers */
static inline bool backports_android_in_wifi_context(void)
{
    return (current_uid().val == BACKPORTS_AID_WIFI ||
            in_group_p(KGIDT_INIT(BACKPORTS_AID_WIFI)));
}

static inline bool backports_android_has_net_admin(void)
{
    return (current_uid().val == 0 || /* root */
            in_group_p(KGIDT_INIT(BACKPORTS_AID_NET_ADMIN)));
}

static inline bool backports_android_has_net_raw(void)
{
    return (current_uid().val == 0 || /* root */
            in_group_p(KGIDT_INIT(BACKPORTS_AID_NET_RAW)));
}

#else /* !BACKPORTS_ANDROID_4_19 */

#define BACKPORTS_ANDROID_USE_ATOMIC_ALLOC 0
#define BACKPORTS_ANDROID_OPTIMIZE_POWER 0
#define BACKPORTS_ANDROID_FAST_SUSPEND 0

#define backports_android_net_ns() (&init_net)
static inline bool backports_android_in_wifi_context(void) { return true; }
static inline bool backports_android_has_net_admin(void) { return true; }
static inline bool backports_android_has_net_raw(void) { return true; }

#endif /* BACKPORTS_ANDROID_4_19 */

/* Android vendor integration */
#ifdef CONFIG_BACKPORTS_VENDOR_QCOM
extern int backports_android_qcom_init(void);
extern void backports_android_qcom_exit(void);
extern int backports_android_qcom_coexist_check(void);
#else
static inline int backports_android_qcom_init(void) { return 0; }
static inline void backports_android_qcom_exit(void) { }
static inline int backports_android_qcom_coexist_check(void) { return 0; }
#endif

#ifdef CONFIG_BACKPORTS_VENDOR_BROADCOM
extern int backports_android_broadcom_init(void);
extern void backports_android_broadcom_exit(void);
extern int backports_android_broadcom_coexist_check(void);
#else
static inline int backports_android_broadcom_init(void) { return 0; }
static inline void backports_android_broadcom_exit(void) { }
static inline int backports_android_broadcom_coexist_check(void) { return 0; }
#endif

/* Android framework callbacks */
struct backports_android_callbacks {
    int (*scan_start)(void);
    int (*scan_complete)(void);
    int (*connect)(const char *ssid);
    int (*disconnect)(void);
    int (*country_change)(const char *alpha2);
};

extern int backports_android_register_callbacks(struct backports_android_callbacks *cb);
extern void backports_android_unregister_callbacks(void);

#else /* !BACKPORTS_ANDROID_KERNEL */

/* Stub implementations for non-Android kernels */
struct backports_android_pm { int dummy; };
struct backports_android_security { int dummy; };
struct backports_android_wifi { int dummy; };
struct backports_android_callbacks { int dummy; };

static inline int backports_android_init(void) { return 0; }
static inline void backports_android_exit(void) { }
static inline int backports_android_pm_init(struct backports_android_pm *pm) { return 0; }
static inline void backports_android_pm_exit(struct backports_android_pm *pm) { }
static inline void backports_android_pm_stay_awake(struct backports_android_pm *pm, const char *reason) { }
static inline void backports_android_pm_relax(struct backports_android_pm *pm, const char *reason) { }
static inline int backports_android_security_init(struct backports_android_security *sec) { return 0; }
static inline bool backports_android_check_wifi_permission(void) { return true; }
static inline bool backports_android_check_monitor_permission(void) { return true; }
static inline bool backports_android_check_injection_permission(void) { return true; }
static inline int backports_android_notify_scan_start(void) { return 0; }
static inline int backports_android_notify_scan_complete(void) { return 0; }
static inline int backports_android_notify_connect(const char *ssid) { return 0; }
static inline int backports_android_notify_disconnect(void) { return 0; }
static inline int backports_android_set_wifi_property(const char *key, const char *value) { return -ENOSYS; }
static inline int backports_android_get_wifi_property(const char *key, char *value, const char *default_val) { return -ENOSYS; }
static inline int backports_android_set_country_code(const char *alpha2) { return -ENOSYS; }
static inline int backports_android_get_country_code(char *alpha2) { return -ENOSYS; }
static inline void *backports_android_kmalloc(size_t size, gfp_t flags) { return kmalloc(size, flags); }
static inline void *backports_android_kzalloc(size_t size, gfp_t flags) { return kzalloc(size, flags); }
static inline void backports_android_kfree(const void *ptr) { kfree(ptr); }
static inline int backports_android_qcom_init(void) { return 0; }
static inline void backports_android_qcom_exit(void) { }
static inline int backports_android_qcom_coexist_check(void) { return 0; }
static inline int backports_android_broadcom_init(void) { return 0; }
static inline void backports_android_broadcom_exit(void) { }
static inline int backports_android_broadcom_coexist_check(void) { return 0; }
static inline int backports_android_register_callbacks(struct backports_android_callbacks *cb) { return -ENOSYS; }
static inline void backports_android_unregister_callbacks(void) { }

#define backports_android_log_info(fmt, ...) pr_info(fmt, ##__VA_ARGS__)
#define backports_android_log_warn(fmt, ...) pr_warn(fmt, ##__VA_ARGS__)
#define backports_android_log_err(fmt, ...) pr_err(fmt, ##__VA_ARGS__)
#define backports_android_log_debug(fmt, ...) pr_debug(fmt, ##__VA_ARGS__)

#endif /* BACKPORTS_ANDROID_KERNEL */

#endif /* BACKPORTS_ANDROID_COMPAT_H */