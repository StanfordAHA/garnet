import os

if os.getenv('WHICH_SOC') == "amber":
    from .wiring_amber import *

else:
    from .wiring_onyx import *
