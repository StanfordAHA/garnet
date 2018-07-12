import os


def make_relative(file):
    """
    Helper function to make file paths relative to test file directory rather
    than where `pytest` is run
    """
    return os.path.join(os.path.dirname(__file__), file)
