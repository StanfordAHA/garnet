#=========================================================================
# easysteps.py
#=========================================================================
# Author : S. Richardson
# Date   : February, 2021

import os
import sys

# from parse import ParseNodes
from mflowgen.components.step import Step

# Private data structure for nodes
class _Node:
    # def __init__(self, name, step, successors):
    def __init__(self, stepdir, successors):
        # self.name = name
        self.stepdir = stepdir
        self.successors = successors

    def __repr__(self):
        s=f"({self.step})"
        w=16
        return(f"{self.name:{w}} {s:25} -> {self.successors}")


# Persistent storage for todo list
_todo    = {}   ;# Connections waiting to be made, used only by easysteps
_extnodes= []   ;# List of extension nodes, used only by easysteps

#   rtl = CStep(g, '/../common/rtl', 'synth')
def CStep(graph, stepdir, successors, DBG=1):
    step = _add_step_with_handle(graph, stepdir, successors, 'custom', DBG=DBG)
    return step

def DStep(graph, stepdir, successors, DBG=1):
    step = _add_step_with_handle(graph, stepdir, successors, 'default', DBG=DBG)
    return step

def EStep(graph, stepdir, successors, DBG=1):
    step = _add_step_with_handle(graph, stepdir, successors, 'extension', DBG=DBG)
    _extnodes.append(step)  ;# Mark this step as an "extend" step
    return step

def _add_step_with_handle(graph, stepdir, successors, which, DBG=0):
      '''
      # Given a node with a stepname and associated dir, build the
      # step and make a handle for the step in the calling frame
      # Nota bene: the handle will be a GLOBAL variable!
      #
      # Example:
      #     frame = sys._getframe(1)
      #     g.add_step_with_handle( 'rtl',  '/../common/rtl' )
      #
      # Does this:
      #     rtl = Step( this_dir + '/../common/rtl' )
      #     g.add_step( rtl )
      #
      # Also: after step is built, add successors to todo list for later processing
      '''
      assert which in ['custom','default','extension']
      if DBG: print(f"Adding {which} step '{stepdir}' -> {successors}")

      if which == 'default':
          is_default = True
      else:
          is_default = False

      # Build the step and assign the handle
      if not is_default:
          frame = sys._getframe(2)
          this_file = os.path.abspath( frame.f_globals['__file__'] )
          this_dir  = os.path.dirname( this_file )
          stepdir   = this_dir + '/' + stepdir

      step = Step( stepdir, default=is_default)

      stepname = step
      _todo[stepname] = [] ; # Initialize todo list

      # Add step to graph
      graph.add_step(step)

      # Add successors to todo list
      # for succ_name in node.successors:
      for succ_name in successors:
        if DBG: print(f"    Adding {stepname}->{succ_name} to todo list")
        _todo[stepname].append(succ_name)

      if DBG: print('')
      return step

def connect_outstanding_nodes(graph, DBG=0):
    '''
    # construct.py should call this method after all steps have been built,
    # to clear out the todo list.
    '''
    print("PROCESSING CONNECTIONS IN TODO LIST")
    frame = sys._getframe(1)
    for from_name in _todo:

        try:
            # Only global vars end up on the todo list, so 'from' node must be global
            from_node = frame.f_globals[from_name]
            from_key = from_name
        except:
            # Huh. not global. Must be that new thing
            for lname in frame.f_locals:
                lval = frame.f_locals[lname]
                print(f'LOCAL {lname} = {lval}; =? {from_name} ?')
                if lval == from_name: break

            assert lval == from_name, "OOOOPS"
            print("FOUNDIT")

            from_key  = from_name
            from_name = lname
            from_node = lval

        # Must make shallow copy b/c we may be deleting elements in situ
        to_list = _todo[from_key].copy() ;

        for to_name in to_list:
            if DBG: print(f"  CONNECTING {from_name} -> {to_name}")

            # Don't know (yet) whether to_node is local or global to calling frame (construct.py)
            to_node = _findvar(frame, to_name, DBG)

            # If "from" is an "extension" node, connect all "from" outputs as "to" inputs
            if from_key in list(_extnodes):
              if DBG: print('    Extnode: connecting all outputs to dest node')
              to_node.extend_inputs( from_node.all_outputs() )

            # Connect "from" -> "to" nodes
            graph.connect_by_name(from_node, to_node)
            # if DBG: print(f'    CONNECTED {from_key} -> {to_name}')
            if DBG: print('')
            _todo[from_key].remove(to_name)

            # if DBG: print(f'    REMOVED from todo list: {from_key} -> {to_name}\n')

def _findvar(frame, varname, DBG=0):
    "Search given frame for local or global var 'varname'"

    # print(f"Look for varname '{varname}' among list of frame's locals")
    try:
        value = frame.f_locals[varname] ;# This will fail if local not exists
        if DBG: print(f"    Found local var '{varname}'")
        return value
    except: pass

    # print(f"    {varname} not local, is it global perchance? ", end='')
    try:
        value = frame.f_globals[varname] ;# This will fail if global not exists
        if DBG: print(f"    Found global var '{varname}'")
        return value
    except: pass

    # Give up
    print(f"**ERROR Could not find '{varname}'"); assert False
