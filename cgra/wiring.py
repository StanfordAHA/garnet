import os

if os.getenv('WHICH_SOC') == "amber":
    from .wiring_amber import *

elif "INCLUDE_E64_HW" in os.environ and os.environ.get("INCLUDE_E64_HW") == "1":
    from .wiring_zircon import *

else:
    from .wiring_onyx import *
