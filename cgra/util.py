import os

if os.getenv('WHICH_SOC') == "amber":
    from .util_amber import *
else:
    from .util_onyx import *
