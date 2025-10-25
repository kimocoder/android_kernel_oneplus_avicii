#ifndef BACKPORTS_COMPAT_H
#define BACKPORTS_COMPAT_H

/*
 * Wireless Driver Compatibility Layer
 * 
 * This header provides compatibility shims for wireless drivers across
 * different kernel versions, with special focus on Android kernel 4.19
 * and mobile platform integration.
 */

#include <linux/version.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/netdevice.h>
#include <linux/wireless.h>
#include <net/cfg80211.h>

/* Kernel version compatibility macros */
#define KERNEL_VERSION_CODE LINUX_VERSION_CODE

/* Android kernel detection */
#ifdef CONFIG_ANDROID
#define BACKPORTS_ANDROID_KERNEL 1
#else
#define BACKPORTS_ANDROID_KERNEL 0
#endif

/* Android kernel 4.19 specific detection */
#if KERNEL_VERSION_CODE >= KERNEL_VERSION(4,19,0) && \
    KERNEL_VERSION_CODE < KERNEL_VERSION(4,20,0) && \
    BACKPORTS_ANDROID_KERNEL
#define BACKPORTS_ANDROID_4_19 1
#else
#define BACKPORTS_ANDROID_4_19 0
#endif

/* Mobile platform detection */
#if defined(CONFIG_ARM) || defined(CONFIG_ARM64) || defined(CONFIG_ANDROID)
#define BACKPORTS_MOBILE_PLATFORM 1
#else
#define BACKPORTS_MOBILE_PLATFORM 0
#endif

/* Power management compatibility */
#if BACKPORTS_MOBILE_PLATFORM
#define BACKPORTS_PM_RUNTIME_SUPPORT 1
#define BACKPORTS_WAKELOCK_SUPPORT 1
#else
#define BACKPORTS_PM_RUNTIME_SUPPORT 0
#define BACKPORTS_WAKELOCK_SUPPORT 0
#endif

/* Regulatory compatibility */
#if KERNEL_VERSION_CODE >= KERNEL_VERSION(4,19,0)
#define BACKPORTS_NEW_REGULATORY_API 1
#else
#define BACKPORTS_NEW_REGULATORY_API 0
#endif

/* cfg80211 API compatibility */
#if KERNEL_VERSION_CODE >= KERNEL_VERSION(4,19,0)
#define BACKPORTS_CFG80211_SCAN_INFO_V2 1
#define BACKPORTS_CFG80211_CONNECT_TIMEOUT 1
#else
#define BACKPORTS_CFG80211_SCAN_INFO_V2 0
#define BACKPORTS_CFG80211_CONNECT_TIMEOUT 0
#endif

/* mac80211 API compatibility */
#if KERNEL_VERSION_CODE >= KERNEL_VERSION(4,19,0)
#define BACKPORTS_MAC80211_TXQ_SUPPORT 1
#define BACKPORTS_MAC80211_AIRTIME_FAIRNESS 1
#else
#define BACKPORTS_MAC80211_TXQ_SUPPORT 0
#define BACKPORTS_MAC80211_AIRTIME_FAIRNESS 0
#endif

/* Netlink API compatibility */
#if KERNEL_VERSION_CODE >= KERNEL_VERSION(4,19,0)
#define BACKPORTS_NETLINK_EXT_ACK 1
#else
#define BACKPORTS_NETLINK_EXT_ACK 0
#endif

/* SKB API compatibility */
#if KERNEL_VERSION_CODE >= KERNEL_VERSION(4,19,0)
#define BACKPORTS_SKB_PUT_ZERO 1
#define BACKPORTS_SKB_PUT_DATA 1
#else
#define BACKPORTS_SKB_PUT_ZERO 0
#define BACKPORTS_SKB_PUT_DATA 0
#endif

/* Timer API compatibility */
#if KERNEL_VERSION_CODE >= KERNEL_VERSION(4,15,0)
#define BACKPORTS_TIMER_SETUP 1
#else
#define BACKPORTS_TIMER_SETUP 0
#endif

/* Workqueue API compatibility */
#if KERNEL_VERSION_CODE >= KERNEL_VERSION(4,19,0)
#define BACKPORTS_WQ_HIGHPRI 1
#else
#define BACKPORTS_WQ_HIGHPRI 0
#endif

/* Android-specific compatibility */
#if BACKPORTS_ANDROID_KERNEL

/* Android wakelock compatibility */
#ifdef CONFIG_ANDROID_WAKELOCK
#include <linux/wakelock.h>
#define backports_wake_lock(lock) wake_lock(lock)
#define backports_wake_unlock(lock) wake_unlock(lock)
#define backports_wake_lock_init(lock, type, name) wake_lock_init(lock, type, name)
#define backports_wake_lock_destroy(lock) wake_lock_destroy(lock)
#else
/* Stub implementations for kernels without wakelock */
struct backports_wake_lock { int dummy; };
#define backports_wake_lock(lock) do { } while (0)
#define backports_wake_unlock(lock) do { } while (0)
#define backports_wake_lock_init(lock, type, name) do { } while (0)
#define backports_wake_lock_destroy(lock) do { } while (0)
#endif

/* Android power management */
#ifdef CONFIG_ANDROID_POWER
#include <linux/android_power.h>
#define backports_android_register_early_suspend(handler) android_register_early_suspend(handler)
#define backports_android_unregister_early_suspend(handler) android_unregister_early_suspend(handler)
#else
#define backports_android_register_early_suspend(handler) do { } while (0)
#define backports_android_unregister_early_suspend(handler) do { } while (0)
#endif

/* Android property system */
#ifdef CONFIG_ANDROID_PROPERTY
extern int backports_android_property_set(const char *key, const char *val);
extern int backports_android_property_get(const char *key, char *val, const char *default_val);
#else
static inline int backports_android_property_set(const char *key, const char *val) { return -ENOSYS; }
static inline int backports_android_property_get(const char *key, char *val, const char *default_val) { return -ENOSYS; }
#endif

#endif /* BACKPORTS_ANDROID_KERNEL */

/* Function compatibility shims */

/* SKB compatibility functions */
#if !BACKPORTS_SKB_PUT_ZERO
static inline void *skb_put_zero(struct sk_buff *skb, unsigned int len)
{
    void *tmp = skb_put(skb, len);
    memset(tmp, 0, len);
    return tmp;
}
#endif

#if !BACKPORTS_SKB_PUT_DATA
static inline void *skb_put_data(struct sk_buff *skb, const void *data, unsigned int len)
{
    void *tmp = skb_put(skb, len);
    memcpy(tmp, data, len);
    return tmp;
}
#endif

/* Timer compatibility */
#if !BACKPORTS_TIMER_SETUP
#define timer_setup(timer, callback, flags) \
    setup_timer(timer, (void (*)(unsigned long))callback, (unsigned long)timer)

#define from_timer(var, callback_timer, timer_fieldname) \
    container_of(callback_timer, typeof(*var), timer_fieldname)
#endif

/* cfg80211 compatibility functions */
#if !BACKPORTS_CFG80211_SCAN_INFO_V2
struct backports_cfg80211_scan_info {
    bool aborted;
};

static inline void cfg80211_scan_done(struct cfg80211_scan_request *request,
                                    struct backports_cfg80211_scan_info *info)
{
    cfg80211_scan_done(request, info->aborted);
}
#endif

/* Netlink compatibility */
#if !BACKPORTS_NETLINK_EXT_ACK
struct netlink_ext_ack {
    const char *_msg;
};
#define NL_SET_ERR_MSG(extack, msg) do { if (extack) (extack)->_msg = msg; } while (0)
#else
#define NL_SET_ERR_MSG(extack, msg) NL_SET_ERR_MSG(extack, msg)
#endif

/* Workqueue compatibility */
#if !BACKPORTS_WQ_HIGHPRI
#define WQ_HIGHPRI 0
#endif

/* Regulatory compatibility */
#if !BACKPORTS_NEW_REGULATORY_API
/* Provide compatibility for older regulatory API */
static inline int regulatory_set_wiphy_regd_sync_rtnl(struct wiphy *wiphy,
                                                    struct ieee80211_regdomain *rd)
{
    return regulatory_set_wiphy_regd(wiphy, rd);
}
#endif

/* Power management compatibility for mobile platforms */
#if BACKPORTS_MOBILE_PLATFORM

/* Runtime PM helpers */
static inline int backports_pm_runtime_get_sync(struct device *dev)
{
#ifdef CONFIG_PM_RUNTIME
    return pm_runtime_get_sync(dev);
#else
    return 0;
#endif
}

static inline int backports_pm_runtime_put_sync(struct device *dev)
{
#ifdef CONFIG_PM_RUNTIME
    return pm_runtime_put_sync(dev);
#else
    return 0;
#endif
}

static inline void backports_pm_runtime_enable(struct device *dev)
{
#ifdef CONFIG_PM_RUNTIME
    pm_runtime_enable(dev);
#endif
}

static inline void backports_pm_runtime_disable(struct device *dev)
{
#ifdef CONFIG_PM_RUNTIME
    pm_runtime_disable(dev);
#endif
}

/* Battery optimization helpers */
static inline void backports_pm_stay_awake(struct device *dev)
{
#ifdef CONFIG_PM_SLEEP
    pm_stay_awake(dev);
#endif
}

static inline void backports_pm_relax(struct device *dev)
{
#ifdef CONFIG_PM_SLEEP
    pm_relax(dev);
#endif
}

#else /* !BACKPORTS_MOBILE_PLATFORM */

/* Stub implementations for non-mobile platforms */
static inline int backports_pm_runtime_get_sync(struct device *dev) { return 0; }
static inline int backports_pm_runtime_put_sync(struct device *dev) { return 0; }
static inline void backports_pm_runtime_enable(struct device *dev) { }
static inline void backports_pm_runtime_disable(struct device *dev) { }
static inline void backports_pm_stay_awake(struct device *dev) { }
static inline void backports_pm_relax(struct device *dev) { }

#endif /* BACKPORTS_MOBILE_PLATFORM */

/* Vendor driver compatibility helpers */
#ifdef CONFIG_BACKPORTS_VENDOR_COMPAT

/* Interface naming compatibility */
extern int backports_register_netdev_compat(struct net_device *dev, const char *vendor_prefix);
extern void backports_unregister_netdev_compat(struct net_device *dev);

/* Resource sharing compatibility */
extern int backports_request_firmware_compat(const struct firmware **fw, const char *name, struct device *device);
extern void backports_release_firmware_compat(const struct firmware *fw);

/* Regulatory domain sharing */
extern int backports_set_regulatory_compat(const char *alpha2);
extern int backports_get_regulatory_compat(char *alpha2, size_t len);

#else

/* Direct implementations when vendor compatibility is disabled */
#define backports_register_netdev_compat(dev, prefix) register_netdev(dev)
#define backports_unregister_netdev_compat(dev) unregister_netdev(dev)
#define backports_request_firmware_compat(fw, name, device) request_firmware(fw, name, device)
#define backports_release_firmware_compat(fw) release_firmware(fw)
#define backports_set_regulatory_compat(alpha2) (-ENOSYS)
#define backports_get_regulatory_compat(alpha2, len) (-ENOSYS)

#endif /* CONFIG_BACKPORTS_VENDOR_COMPAT */

/* Debug and logging compatibility */
#if BACKPORTS_ANDROID_KERNEL
#define backports_pr_info(fmt, ...) pr_info("backports: " fmt, ##__VA_ARGS__)
#define backports_pr_warn(fmt, ...) pr_warn("backports: " fmt, ##__VA_ARGS__)
#define backports_pr_err(fmt, ...) pr_err("backports: " fmt, ##__VA_ARGS__)
#define backports_pr_debug(fmt, ...) pr_debug("backports: " fmt, ##__VA_ARGS__)
#else
#define backports_pr_info(fmt, ...) pr_info(fmt, ##__VA_ARGS__)
#define backports_pr_warn(fmt, ...) pr_warn(fmt, ##__VA_ARGS__)
#define backports_pr_err(fmt, ...) pr_err(fmt, ##__VA_ARGS__)
#define backports_pr_debug(fmt, ...) pr_debug(fmt, ##__VA_ARGS__)
#endif

/* Memory allocation compatibility for mobile platforms */
#if BACKPORTS_MOBILE_PLATFORM
static inline void *backports_kmalloc(size_t size, gfp_t flags)
{
    /* Use GFP_ATOMIC for mobile platforms to avoid blocking */
    if (flags & GFP_KERNEL)
        flags = (flags & ~GFP_KERNEL) | GFP_ATOMIC;
    return kmalloc(size, flags);
}

static inline void *backports_kzalloc(size_t size, gfp_t flags)
{
    if (flags & GFP_KERNEL)
        flags = (flags & ~GFP_KERNEL) | GFP_ATOMIC;
    return kzalloc(size, flags);
}
#else
#define backports_kmalloc(size, flags) kmalloc(size, flags)
#define backports_kzalloc(size, flags) kzalloc(size, flags)
#endif

/* Version information */
#define BACKPORTS_COMPAT_VERSION "1.0.0"
#define BACKPORTS_COMPAT_BUILD_DATE __DATE__ " " __TIME__

/* Feature detection macros for drivers */
#define BACKPORTS_HAS_FEATURE(feature) (BACKPORTS_##feature)

/* Initialization and cleanup helpers */
extern int backports_compat_init(void);
extern void backports_compat_exit(void);

#endif /* BACKPORTS_COMPAT_H */