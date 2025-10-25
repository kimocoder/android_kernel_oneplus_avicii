/*
 * Wireless Driver Compatibility Layer Implementation
 * 
 * This file implements compatibility functions for wireless drivers across
 * different kernel versions, with special focus on Android kernel 4.19
 * and mobile platform integration.
 */

#include "compat.h"
#include <linux/firmware.h>
#include <linux/slab.h>
#include <linux/string.h>
#include <linux/mutex.h>
#include <linux/list.h>

/* Global compatibility state */
static struct {
    bool initialized;
    struct mutex lock;
    struct list_head vendor_devices;
    char regulatory_alpha2[3];
} backports_compat_state = {
    .initialized = false,
    .lock = __MUTEX_INITIALIZER(backports_compat_state.lock),
    .vendor_devices = LIST_HEAD_INIT(backports_compat_state.vendor_devices),
    .regulatory_alpha2 = "00",
};

/* Vendor device tracking for compatibility */
struct vendor_device_entry {
    struct list_head list;
    struct net_device *dev;
    char vendor_name[32];
    char original_name[IFNAMSIZ];
    bool active;
};

#ifdef CONFIG_BACKPORTS_VENDOR_COMPAT

/**
 * backports_register_netdev_compat - Register network device with vendor compatibility
 * @dev: Network device to register
 * @vendor_prefix: Vendor prefix for interface naming
 * 
 * This function registers a network device while maintaining compatibility
 * with existing vendor drivers by using appropriate interface naming.
 */
int backports_register_netdev_compat(struct net_device *dev, const char *vendor_prefix)
{
    struct vendor_device_entry *entry;
    char new_name[IFNAMSIZ];
    int ret;

    if (!dev || !vendor_prefix)
        return -EINVAL;

    /* Allocate tracking entry */
    entry = kzalloc(sizeof(*entry), GFP_KERNEL);
    if (!entry)
        return -ENOMEM;

    /* Store original name */
    strncpy(entry->original_name, dev->name, IFNAMSIZ - 1);
    strncpy(entry->vendor_name, vendor_prefix, sizeof(entry->vendor_name) - 1);

    /* Generate vendor-compatible name */
    snprintf(new_name, sizeof(new_name), "%s%s", vendor_prefix, dev->name);
    
    /* Check if name is already in use */
    if (dev_get_by_name(&init_net, new_name)) {
        /* Try with numeric suffix */
        int i;
        for (i = 0; i < 100; i++) {
            snprintf(new_name, sizeof(new_name), "%s%s%d", 
                    vendor_prefix, dev->name, i);
            if (!dev_get_by_name(&init_net, new_name))
                break;
        }
        if (i >= 100) {
            kfree(entry);
            return -EEXIST;
        }
    }

    /* Update device name */
    strncpy(dev->name, new_name, IFNAMSIZ - 1);

    /* Register the device */
    ret = register_netdev(dev);
    if (ret) {
        kfree(entry);
        return ret;
    }

    /* Add to tracking list */
    entry->dev = dev;
    entry->active = true;

    mutex_lock(&backports_compat_state.lock);
    list_add(&entry->list, &backports_compat_state.vendor_devices);
    mutex_unlock(&backports_compat_state.lock);

    backports_pr_info("Registered device %s (original: %s) with vendor compatibility\n",
                     dev->name, entry->original_name);

    return 0;
}
EXPORT_SYMBOL_GPL(backports_register_netdev_compat);

/**
 * backports_unregister_netdev_compat - Unregister network device with vendor compatibility
 * @dev: Network device to unregister
 */
void backports_unregister_netdev_compat(struct net_device *dev)
{
    struct vendor_device_entry *entry, *tmp;

    if (!dev)
        return;

    /* Find and remove from tracking list */
    mutex_lock(&backports_compat_state.lock);
    list_for_each_entry_safe(entry, tmp, &backports_compat_state.vendor_devices, list) {
        if (entry->dev == dev) {
            list_del(&entry->list);
            backports_pr_info("Unregistered device %s (original: %s)\n",
                             dev->name, entry->original_name);
            kfree(entry);
            break;
        }
    }
    mutex_unlock(&backports_compat_state.lock);

    /* Unregister the device */
    unregister_netdev(dev);
}
EXPORT_SYMBOL_GPL(backports_unregister_netdev_compat);

/**
 * backports_request_firmware_compat - Request firmware with vendor compatibility
 * @fw: Pointer to firmware pointer
 * @name: Firmware file name
 * @device: Device requesting firmware
 * 
 * This function requests firmware while handling vendor-specific paths
 * and fallback mechanisms.
 */
int backports_request_firmware_compat(const struct firmware **fw, 
                                    const char *name, struct device *device)
{
    char vendor_path[256];
    int ret;

    if (!fw || !name || !device)
        return -EINVAL;

    /* Try vendor-specific path first */
    snprintf(vendor_path, sizeof(vendor_path), "vendor/%s", name);
    ret = request_firmware(fw, vendor_path, device);
    if (ret == 0) {
        backports_pr_debug("Loaded firmware from vendor path: %s\n", vendor_path);
        return 0;
    }

    /* Try backports-specific path */
    snprintf(vendor_path, sizeof(vendor_path), "backports/%s", name);
    ret = request_firmware(fw, vendor_path, device);
    if (ret == 0) {
        backports_pr_debug("Loaded firmware from backports path: %s\n", vendor_path);
        return 0;
    }

    /* Fall back to standard path */
    ret = request_firmware(fw, name, device);
    if (ret == 0) {
        backports_pr_debug("Loaded firmware from standard path: %s\n", name);
        return 0;
    }

    backports_pr_warn("Failed to load firmware: %s\n", name);
    return ret;
}
EXPORT_SYMBOL_GPL(backports_request_firmware_compat);

/**
 * backports_release_firmware_compat - Release firmware with vendor compatibility
 * @fw: Firmware to release
 */
void backports_release_firmware_compat(const struct firmware *fw)
{
    if (fw) {
        release_firmware(fw);
    }
}
EXPORT_SYMBOL_GPL(backports_release_firmware_compat);

/**
 * backports_set_regulatory_compat - Set regulatory domain with vendor compatibility
 * @alpha2: Two-character country code
 */
int backports_set_regulatory_compat(const char *alpha2)
{
    if (!alpha2 || strlen(alpha2) != 2)
        return -EINVAL;

    mutex_lock(&backports_compat_state.lock);
    strncpy(backports_compat_state.regulatory_alpha2, alpha2, 2);
    backports_compat_state.regulatory_alpha2[2] = '\0';
    mutex_unlock(&backports_compat_state.lock);

    backports_pr_info("Set regulatory domain to: %s\n", alpha2);
    return 0;
}
EXPORT_SYMBOL_GPL(backports_set_regulatory_compat);

/**
 * backports_get_regulatory_compat - Get current regulatory domain
 * @alpha2: Buffer to store country code
 * @len: Buffer length
 */
int backports_get_regulatory_compat(char *alpha2, size_t len)
{
    if (!alpha2 || len < 3)
        return -EINVAL;

    mutex_lock(&backports_compat_state.lock);
    strncpy(alpha2, backports_compat_state.regulatory_alpha2, len - 1);
    alpha2[len - 1] = '\0';
    mutex_unlock(&backports_compat_state.lock);

    return 0;
}
EXPORT_SYMBOL_GPL(backports_get_regulatory_compat);

#endif /* CONFIG_BACKPORTS_VENDOR_COMPAT */

#if BACKPORTS_ANDROID_KERNEL

#ifdef CONFIG_ANDROID_PROPERTY
/**
 * backports_android_property_set - Set Android system property
 * @key: Property key
 * @val: Property value
 */
int backports_android_property_set(const char *key, const char *val)
{
    /* This would interface with Android's property system */
    backports_pr_debug("Setting Android property: %s=%s\n", key, val);
    return 0; /* Stub implementation */
}
EXPORT_SYMBOL_GPL(backports_android_property_set);

/**
 * backports_android_property_get - Get Android system property
 * @key: Property key
 * @val: Buffer for property value
 * @default_val: Default value if property not found
 */
int backports_android_property_get(const char *key, char *val, const char *default_val)
{
    /* This would interface with Android's property system */
    if (default_val) {
        strncpy(val, default_val, PROP_VALUE_MAX - 1);
        val[PROP_VALUE_MAX - 1] = '\0';
    } else {
        val[0] = '\0';
    }
    backports_pr_debug("Getting Android property: %s (default: %s)\n", key, default_val);
    return 0; /* Stub implementation */
}
EXPORT_SYMBOL_GPL(backports_android_property_get);
#endif /* CONFIG_ANDROID_PROPERTY */

#endif /* BACKPORTS_ANDROID_KERNEL */

/**
 * backports_compat_init - Initialize compatibility layer
 */
int backports_compat_init(void)
{
    if (backports_compat_state.initialized)
        return 0;

    mutex_lock(&backports_compat_state.lock);
    
    if (!backports_compat_state.initialized) {
        INIT_LIST_HEAD(&backports_compat_state.vendor_devices);
        
        backports_pr_info("Compatibility layer initialized\n");
        backports_pr_info("Version: %s\n", BACKPORTS_COMPAT_VERSION);
        backports_pr_info("Build: %s\n", BACKPORTS_COMPAT_BUILD_DATE);
        backports_pr_info("Kernel: %d.%d.%d\n", 
                         KERNEL_VERSION_CODE >> 16,
                         (KERNEL_VERSION_CODE >> 8) & 0xFF,
                         KERNEL_VERSION_CODE & 0xFF);
        
#if BACKPORTS_ANDROID_KERNEL
        backports_pr_info("Android kernel support: enabled\n");
#if BACKPORTS_ANDROID_4_19
        backports_pr_info("Android 4.19 optimizations: enabled\n");
#endif
#endif

#if BACKPORTS_MOBILE_PLATFORM
        backports_pr_info("Mobile platform optimizations: enabled\n");
#endif

#ifdef CONFIG_BACKPORTS_VENDOR_COMPAT
        backports_pr_info("Vendor driver compatibility: enabled\n");
#endif

        backports_compat_state.initialized = true;
    }
    
    mutex_unlock(&backports_compat_state.lock);
    return 0;
}
EXPORT_SYMBOL_GPL(backports_compat_init);

/**
 * backports_compat_exit - Cleanup compatibility layer
 */
void backports_compat_exit(void)
{
    struct vendor_device_entry *entry, *tmp;

    if (!backports_compat_state.initialized)
        return;

    mutex_lock(&backports_compat_state.lock);
    
    /* Clean up vendor device tracking */
    list_for_each_entry_safe(entry, tmp, &backports_compat_state.vendor_devices, list) {
        list_del(&entry->list);
        backports_pr_warn("Cleaning up tracked device: %s\n", entry->original_name);
        kfree(entry);
    }
    
    backports_compat_state.initialized = false;
    
    mutex_unlock(&backports_compat_state.lock);
    
    backports_pr_info("Compatibility layer cleanup completed\n");
}
EXPORT_SYMBOL_GPL(backports_compat_exit);

/* Module information */
MODULE_DESCRIPTION("Backports Wireless Driver Compatibility Layer");
MODULE_AUTHOR("Backports Integration Team");
MODULE_LICENSE("GPL v2");
MODULE_VERSION(BACKPORTS_COMPAT_VERSION);