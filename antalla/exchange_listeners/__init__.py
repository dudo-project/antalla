from os import path
import pkgutil
import sys


def load_listeners():
    for importer, module_name, _ in pkgutil.iter_modules(__path__, prefix=__name__ + "."):
        if module_name not in sys.modules:
            importer.find_module(module_name).load_module(module_name)

# force to load all listeners so they get registered to the factory
load_listeners()

