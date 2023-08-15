
# https://github.com/python/cpython/issues/90780

from aiocache import cached  # type: ignore
# https://github.com/aio-libs/aiocache/issues/512
# https://github.com/aio-libs/aiocache/issues/667
from async_lru import alru_cache


def async_cache(function = None, *, ignore_kwargs = None):
    if callable(function):
        return alru_cache(maxsize = None)(function)
    elif ignore_kwargs:
        return cached(
            key_builder = custom_key_builder(ignore_kwargs = ignore_kwargs)
        )
    else:
        return alru_cache(maxsize = None)


def custom_key_builder(ignore_kwargs = ()):
    if isinstance(ignore_kwargs, str):
        ignore_kwargs = (ignore_kwargs,)

    def key_builder(func, *args, **kwargs):
        for ignore_kwarg in ignore_kwargs:
            kwargs.pop(ignore_kwarg, None)

        # aiocache.cached default
        ordered_kwargs = sorted(kwargs.items())
        return (
            (func.__module__ or "")
            + func.__name__
            + str(args)  # noself = False
            + str(ordered_kwargs)
        )

    return key_builder

