#ifndef BACKPORTS_POWER_COMPAT_H
#define BACKPORTS_POWER_COMPAT_H

/*
 * Power Management Compatibility Layer
 * 
 * This header provides power management compatibility for mobile platforms
 * with optimizations for Android kernel 4.19 and battery efficiency.
 */

#include "compat.h"
#include <linux/pm.h>
#include <linux/pm_runtime.h>

#if BACKPORTS_MOBILE_PLATFORM

#include <linux/device.h>
#include <linux/workqueue.h>

/* Power management states */
enum backports_pm_state {
    BACKPORTS_PM_ACTIVE,
    BACKPORTS_PM_IDLE,
    BACKPORTS_PM_SUSPEND,
    BACKPORTS_PM_DEEP_SLEEP
};

/* Power management events */
enum backports_pm_event {
    BACKPORTS_PM_EVENT_SCAN_START,
    BACKPORTS_PM_EVENT_SCAN_COMPLETE,
    BACKPORTS_PM_EVENT_CONNECT,
    BACKPORTS_PM_EVENT_DISCONNECT,
    BACKPORTS_PM_EVENT_TX_ACTIVE,
    BACKPORTS_PM_EVENT_TX_IDLE,
    BACKPORTS_PM_EVENT_RX_ACTIVE,
    BACKPORTS_PM_EVENT_RX_IDLE
};

/* Power management context */
struct backports_pm_context {
    struct device *dev;
    enum backports_pm_state state;
    
    /* Runtime PM */
    bool runtime_enabled;
    int runtime_usage_count;
    
    /* Suspend/Resume */
    bool suspend_enabled;
    bool in_suspend;
    
    /* Battery optimization */
    bool battery_optimization;
    unsigned long last_activity;
    unsigned long idle_timeout;
    
    /* Workqueue for power management */
    struct workqueue_struct *pm_wq;
    struct delayed_work idle_work;
    struct work_struct suspend_work;
    struct work_struct resume_work;
    
    /* Statistics */
    unsigned long suspend_count;
    unsigned long resume_count;
    unsigned long idle_count;
    unsigned long active_count;
    
    /* Callbacks */
    int (*suspend_cb)(struct backports_pm_context *ctx);
    int (*resume_cb)(struct backports_pm_context *ctx);
    int (*idle_cb)(struct backports_pm_context *ctx);
    int (*active_cb)(struct backports_pm_context *ctx);
    
    /* Lock for synchronization */
    struct mutex lock;
};

/* Power management operations */
struct backports_pm_ops {
    int (*init)(struct backports_pm_context *ctx, struct device *dev);
    void (*exit)(struct backports_pm_context *ctx);
    int (*suspend)(struct backports_pm_context *ctx);
    int (*resume)(struct backports_pm_context *ctx);
    int (*runtime_suspend)(struct backports_pm_context *ctx);
    int (*runtime_resume)(struct backports_pm_context *ctx);
    void (*notify_event)(struct backports_pm_context *ctx, enum backports_pm_event event);
};

/* Function declarations */
extern int backports_pm_init(struct backports_pm_context *ctx, struct device *dev);
extern void backports_pm_exit(struct backports_pm_context *ctx);

extern int backports_pm_suspend(struct backports_pm_context *ctx);
extern int backports_pm_resume(struct backports_pm_context *ctx);

extern int backports_pm_runtime_get(struct backports_pm_context *ctx);
extern int backports_pm_runtime_put(struct backports_pm_context *ctx);
extern int backports_pm_runtime_get_sync(struct backports_pm_context *ctx);
extern int backports_pm_runtime_put_sync(struct backports_pm_context *ctx);

extern void backports_pm_notify_event(struct backports_pm_context *ctx, enum backports_pm_event event);
extern void backports_pm_stay_awake(struct backports_pm_context *ctx, const char *reason);
extern void backports_pm_relax(struct backports_pm_context *ctx, const char *reason);

extern int backports_pm_set_callbacks(struct backports_pm_context *ctx,
                                     int (*suspend_cb)(struct backports_pm_context *),
                                     int (*resume_cb)(struct backports_pm_context *),
                                     int (*idle_cb)(struct backports_pm_context *),
                                     int (*active_cb)(struct backports_pm_context *));

extern void backports_pm_enable_battery_optimization(struct backports_pm_context *ctx, bool enable);
extern void backports_pm_set_idle_timeout(struct backports_pm_context *ctx, unsigned long timeout_ms);

extern int backports_pm_get_statistics(struct backports_pm_context *ctx, 
                                      unsigned long *suspend_count,
                                      unsigned long *resume_count,
                                      unsigned long *idle_count,
                                      unsigned long *active_count);

/* Android-specific power management */
#if BACKPORTS_ANDROID_KERNEL

#include "android-compat.h"

/* Android power management context */
struct backports_android_pm_context {
    struct backports_pm_context base;
    struct backports_android_pm android_pm;
    
    /* Android-specific features */
    bool doze_mode_enabled;
    bool app_standby_enabled;
    bool background_scan_enabled;
    
    /* Android power hints */
    int power_hint_handle;
    bool power_hint_active;
};

extern int backports_android_pm_init(struct backports_android_pm_context *ctx, struct device *dev);
extern void backports_android_pm_exit(struct backports_android_pm_context *ctx);

extern void backports_android_pm_set_doze_mode(struct backports_android_pm_context *ctx, bool enable);
extern void backports_android_pm_set_app_standby(struct backports_android_pm_context *ctx, bool enable);
extern void backports_android_pm_set_background_scan(struct backports_android_pm_context *ctx, bool enable);

extern int backports_android_pm_send_power_hint(struct backports_android_pm_context *ctx, int hint);

#endif /* BACKPORTS_ANDROID_KERNEL */

/* Macros for power management */
#define BACKPORTS_PM_IDLE_TIMEOUT_DEFAULT 5000 /* 5 seconds */
#define BACKPORTS_PM_SUSPEND_TIMEOUT_DEFAULT 30000 /* 30 seconds */

#define backports_pm_is_active(ctx) ((ctx)->state == BACKPORTS_PM_ACTIVE)
#define backports_pm_is_idle(ctx) ((ctx)->state == BACKPORTS_PM_IDLE)
#define backports_pm_is_suspended(ctx) ((ctx)->state == BACKPORTS_PM_SUSPEND || (ctx)->state == BACKPORTS_PM_DEEP_SLEEP)

/* Conditional compilation helpers */
#ifdef CONFIG_PM_RUNTIME
#define BACKPORTS_HAS_RUNTIME_PM 1
#else
#define BACKPORTS_HAS_RUNTIME_PM 0
#endif

#ifdef CONFIG_PM_SLEEP
#define BACKPORTS_HAS_SUSPEND_RESUME 1
#else
#define BACKPORTS_HAS_SUSPEND_RESUME 0
#endif

#ifdef CONFIG_PM_AUTOSLEEP
#define BACKPORTS_HAS_AUTOSLEEP 1
#else
#define BACKPORTS_HAS_AUTOSLEEP 0
#endif

#else /* !BACKPORTS_MOBILE_PLATFORM */

/* Stub implementations for non-mobile platforms */
struct backports_pm_context { int dummy; };
struct backports_pm_ops { int dummy; };
struct backports_android_pm_context { int dummy; };

enum backports_pm_state { BACKPORTS_PM_ACTIVE };
enum backports_pm_event { BACKPORTS_PM_EVENT_SCAN_START };

static inline int backports_pm_init(struct backports_pm_context *ctx, struct device *dev) { return 0; }
static inline void backports_pm_exit(struct backports_pm_context *ctx) { }
static inline int backports_pm_suspend(struct backports_pm_context *ctx) { return 0; }
static inline int backports_pm_resume(struct backports_pm_context *ctx) { return 0; }
static inline int backports_pm_runtime_get(struct backports_pm_context *ctx) { return 0; }
static inline int backports_pm_runtime_put(struct backports_pm_context *ctx) { return 0; }
static inline int backports_pm_runtime_get_sync(struct backports_pm_context *ctx) { return 0; }
static inline int backports_pm_runtime_put_sync(struct backports_pm_context *ctx) { return 0; }
static inline void backports_pm_notify_event(struct backports_pm_context *ctx, enum backports_pm_event event) { }
static inline void backports_pm_stay_awake(struct backports_pm_context *ctx, const char *reason) { }
static inline void backports_pm_relax(struct backports_pm_context *ctx, const char *reason) { }
static inline int backports_pm_set_callbacks(struct backports_pm_context *ctx, void *a, void *b, void *c, void *d) { return 0; }
static inline void backports_pm_enable_battery_optimization(struct backports_pm_context *ctx, bool enable) { }
static inline void backports_pm_set_idle_timeout(struct backports_pm_context *ctx, unsigned long timeout_ms) { }
static inline int backports_pm_get_statistics(struct backports_pm_context *ctx, unsigned long *a, unsigned long *b, unsigned long *c, unsigned long *d) { return 0; }

#if BACKPORTS_ANDROID_KERNEL
static inline int backports_android_pm_init(struct backports_android_pm_context *ctx, struct device *dev) { return 0; }
static inline void backports_android_pm_exit(struct backports_android_pm_context *ctx) { }
static inline void backports_android_pm_set_doze_mode(struct backports_android_pm_context *ctx, bool enable) { }
static inline void backports_android_pm_set_app_standby(struct backports_android_pm_context *ctx, bool enable) { }
static inline void backports_android_pm_set_background_scan(struct backports_android_pm_context *ctx, bool enable) { }
static inline int backports_android_pm_send_power_hint(struct backports_android_pm_context *ctx, int hint) { return 0; }
#endif

#define backports_pm_is_active(ctx) true
#define backports_pm_is_idle(ctx) false
#define backports_pm_is_suspended(ctx) false

#endif /* BACKPORTS_MOBILE_PLATFORM */

#endif /* BACKPORTS_POWER_COMPAT_H */