import pathlib


def ip_available(filename, paths):
    for path in paths:
        fullpath = pathlib.Path(path) / pathlib.Path(filename)
        if fullpath.is_file():
            return True
    return False


# TODO(rsetaluri): Add a version which just emits a warning. For now, our only
# use case is to error for such functions.
def deprecated(message):
    def deprecated_decorator(func):
        def deprecated_func(*args, **kwargs):
            msg = f"Function {func.__name__} is deprecated: {message}"
            raise RuntimeError(msg)
        return deprecated_func
    return deprecated_decorator
