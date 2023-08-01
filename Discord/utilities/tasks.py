
from discord.ext.tasks import Loop
from discord.utils import MISSING

import logging
import sys
import traceback

import sentry_sdk


def loop(
    *, seconds = MISSING, minutes = MISSING, hours = MISSING, time = MISSING,
    count = None, reconnect = True
):
    def decorator(function):
        loop_instance = Loop(
            function, seconds = seconds, minutes = minutes, hours = hours,
            count = count, time = time, reconnect = reconnect
        )

        @loop_instance.error
        async def loop_instance_error(*args):
            error = args[-1]
            sentry_sdk.capture_exception(error)
            print(
                (
                    "Unhandled exception in "
                    f"{loop_instance.coro.__qualname__} task"
                ),
                file = sys.stderr
            )
            traceback.print_exception(
                type(error), error, error.__traceback__, file = sys.stderr
            )
            logging.getLogger("errors").error(
                "Uncaught exception\n",
                exc_info = (type(error), error, error.__traceback__)
            )

        return loop_instance

    return decorator

