import pathlib
import difflib
import sys
import filecmp


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


def check_files_equal(file1_name, file2_name):
    """
    Check if file1 == file2
    """
    result = filecmp.cmp(file1_name, file2_name, shallow=False)
    if not result:  # pragma: no cover
        with open(file1_name, "r") as file1:
            with open(file2_name, "r") as file2:
                diff = difflib.unified_diff(
                    file2.readlines(),
                    file1.readlines(),
                    fromfile=file2_name,
                    tofile=file1_name,
                )
                for line in diff:
                    sys.stderr.write(line)
    return result
