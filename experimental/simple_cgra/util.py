import inspect
import magma as m


def wrap(inner, outer):
    for name in inner.interface.ports:
        m.wire(getattr(inner, name), getattr(outer, name))


def subgenerator(fn):
    def wrapped(*args, **kwargs):
        return fn(*args, **kwargs)
    return wrapped
