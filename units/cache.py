
# https://github.com/python/cpython/issues/90780

from async_lru import alru_cache


async_cache = alru_cache(maxsize=None)

