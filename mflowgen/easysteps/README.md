# EASYSTEPS - Simpler step  creation

This easysteps package is designed to simplify the way we build `construct.py` scripts for new flows...it aims to reduce duplicated/unnecessary extra effort involved for various simple tasks.

Without easysteps, adding a node/step involves modifying your `construct.py` script in three separate places, once to define the node, once to add the node to the graph, and once to connect it to the other nodes in the graph. For example, adding a couple of default nodes `iflow` and `init` currently looks like the code below (all "before" examples are taken from [Tile_PE/construct.py](https://github.com/StanfordAHA/garnet/blob/69c3971586defcc41b71d29ec9f09eea41e2c270/mflowgen/Tile_PE/construct.py) in StanfordAHA's `garnet` repo).

```
    # Adding default nodes BEFORE:

    init   = Step( 'cadence-innovus-init',      default=True )
    power  = Step( 'cadence-innovus-power',     default=True )
    iflow  = Step( 'cadence-innovus-flowsetup', default=True )
    ...
    g.add_step( init  )
    g.add_step( power )
    g.add_step( iflow )
    ...
    g.connect_by_name( init,     power        )
    g.connect_by_name( power,    place        )
    g.connect_by_name( iflow,    init         )
    g.connect_by_name( iflow,    power        )
    g.connect_by_name( iflow,    place        )
    g.connect_by_name( iflow,    cts          )
    g.connect_by_name( iflow,    postcts_hold )
    g.connect_by_name( iflow,    route        )
    g.connect_by_name( iflow,    postroute    )
    g.connect_by_name( iflow,    signoff      )
    ...
```

Easysteps combines all these steps in a single place in the script, e.g.
```
    # Adding default nodes AFTER:
 
    add_default_steps(g, '''
      init  - cadence-innovus-init  -> power
      power - cadence-innovus-power -> place
      iflow - cadence-innovus-flowsetup -> init power place cts postcts_hold
              route postroute signoff debugcalibre
    ''')
```
The string passed to this new method, yaml-like in simplicity, would be parsed and expanded, invisibly to the user, into the full `Step()/add_step()/connect_by_name()` sequence.

An identical `add_custom_steps()` method is provided for custom steps; and for convenience, I included an `extend_steps()` method for the common case where a custom step's sole purpose is to provide new inputs for an existing default step.
```
    add_custom_steps(g, '''
              rtl         - ../common/rtl -> synth
              constraints - constraints   -> synth iflow
    ''')
    extend_steps(g, '''
              custom_init  - custom-init                 -> init
              custom_power - ../common/custom-power-leaf -> power
    ''')
---
    # Can optionally be done as separate per-line calls e.g.
 
    extend_steps(g, 'custom-init                 - custom_init  -> init')
    extend_steps(g, '../common/custom-power-leaf - custom_power -> power')
```

After all `easysteps` have been added, there *must* be at least one final connect-everything call to put it all together
```
  # Complete all easysteps connections
  connect_outstanding_nodes(g, DBG=1)
```
