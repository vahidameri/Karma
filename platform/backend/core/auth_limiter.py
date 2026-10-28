import hashlib

from django.core.cache import cache


def key_for(request, username):
    identity = request.META.get("REMOTE_ADDR", "") + "\0" + username
    return "login-user:" + hashlib.sha256(identity.encode()).hexdigest()


def increment(key):
    cache.add(key, 0, 300)
    try:
        return cache.incr(key)
    except ValueError:
        cache.add(key, 0, 300)
        return cache.incr(key)


def allowed(request, username):
    ip = "login-ip:" + hashlib.sha256(request.META.get("REMOTE_ADDR", "").encode()).hexdigest()
    return increment(ip) <= 100 and increment(key_for(request, username)) <= 10


def clear(request, username):
    cache.delete(key_for(request, username))
