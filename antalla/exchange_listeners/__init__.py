from os import path
import pkgutil
import sys


def load_listeners():
    for _, module_name, _ in pkgutil.iter_modules(__path__, prefix=__name__ + "."):
        __import__(module_name)

# force to load all listeners so they get registered to the factory
load_listeners()

