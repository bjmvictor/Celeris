from django.core.cache import cache


NAVIGATION_CACHE_KEY = "celeris:navigation:v3"
SYSTEM_ICONS_CACHE_KEY = "celeris:system-icons:v1"
NAVIGATION_CACHE_TIMEOUT = 300


def invalidate_navigation_cache():
    cache.delete_many((NAVIGATION_CACHE_KEY, SYSTEM_ICONS_CACHE_KEY))
