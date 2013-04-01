import functools
import logging
import os
import time
import sys
import urllib2
from fuelweb_test.settings import LOGS_DIR


def save_logs(ip, filename):
    logging.info('Saving logs to "%s" file' % filename)
    with open(filename, 'w') as f:
        f.write(
            urllib2.urlopen("http://%s:8000/api/logs/package" % ip).read()
        )


def fetch_logs():
    """ Decorator to fetch logs to file.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwagrs):
            # noinspection PyBroadException
            try:
                func(*args, **kwagrs)
                status = "ok"
            except:
                status = "error"
            if LOGS_DIR:
                save_logs(args[0].get_admin_node_ip(),
                          os.path.join(LOGS_DIR,
                                       "{0:s}-{1:s}-{2:s}".format(
                                           status,
                                           func.__name__,
                                           time.time())))

        return wrapper

    return decorator


def snapshot_errors():
    """ Decorator to snapshot environment when error occurred in test.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwagrs):
            try:
                func(*args, **kwagrs)
            except Exception, e:
                name = 'error-%s' % time.time()
                description = "Failed in method '%s'" % func.__name__
                if args[0].ci() is not None:
                    args[0].ci().environment().suspend(verbose=False)
                    args[0].ci().environment().snapshot(name, description)
                raise e, None, sys.exc_info()[2]

        return wrapper

    return decorator


def debug_(loggername):
    logger = logging.getLogger(loggername)

    def log_(enter_message, exit_message=None):
        def wrapper(f):
            def wrapped(*args, **kargs):
                logger.debug(enter_message)
                r = f(*args, **kargs)
                if exit_message:
                    logger.debug(exit_message)
                return r

            return wrapped

        return wrapper

    return log_


def debug(logger):
    def wrapper(func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            logger.debug(
                "Calling: %s with args: %s %s" % (func.__name__, args, kwargs))
            result = func(*args, **kwargs)
            logger.debug("Done: %s with result: %s" % (func.__name__, result))
            return result

        return wrapped

    return wrapper
