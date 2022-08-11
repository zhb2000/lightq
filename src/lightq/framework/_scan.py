import importlib
from typing import Iterable, Any
from types import ModuleType

from ._handler import MessageHandler, EventHandler, ExceptionHandler


def module_public_members(module: ModuleType) -> Iterable[Any]:
    if hasattr(module, '__all__'):
        for attrname in module.__all__:
            yield getattr(module, attrname)
    else:
        for attrname in dir(module):
            if not attrname.startswith('_'):
                yield getattr(module, attrname)


def scan_handlers(module: ModuleType | str) -> Iterable[MessageHandler | EventHandler | ExceptionHandler]:
    if isinstance(module, str):
        module = importlib.import_module(module)
    return filter(
        lambda x: isinstance(x, MessageHandler | EventHandler | ExceptionHandler),
        module_public_members(module)
    )
