import os

def global_setup:
    print("Hello woild I am global setup howdja do")
    print("Hey I wonder where does this script live?")
    print("I think it is here maybe:")

    # Maybe this fails if script is run interactively i.e. __file__ no exists then maybe
    print(os.path.dirname(os.path.realpath(__file__)))    
