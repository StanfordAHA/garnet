import os
import sys

from mflowgen.components import Graph, Step
from enum import Enum


class NodeType(Enum):
    INIT = 0
    POWER = 1
    PLACE = 2
    CTS = 3
    POSTCTS_HOLD = 4
    ROUTE = 5
    POSTROUTE = 5
    POSTROUTE_HOLD = 6
    SIGNOFF = 7


class NodeTest:
    # flow_node: the feature node we are testing
    # test_node: the node that actually contains the test
    # test_points: list of NodeTypes where we attach test_node and run the test
    def __init__(self, flow_node: Step, test_node: Step, test_points: list):
        self.flow_node = flow_node
        self.test_node = test_node
        self.test_points = test_points

    def attach_test(self, g):
        step_types = {
            NodeType.INIT: 'cadence-innovus-init',
            NodeType.POWER: 'cadence-innovus-power',
            NodeType.PLACE: 'cadence-innovus-place',
            NodeType.CTS: 'cadence-innovus-cts',
            NodeType.POSTCTS_HOLD: 'cadence-innovus-postcts-hold',
            NodeType.ROUTE: 'cadence-innovus-route',
            NodeType.POSTROUTE: 'cadence-innovus-postroute',
            NodeType.POSTROUTE_HOLD: 'cadence-innovus-postroute-hold',
            NodeType.SIGNOFF: 'cadence-innovus-signoff'
        }

        clone = False
        adk = g.get_adk_step()
        for test_point in self.test_points:
            flow_step = g.get_step(step_types[test_point])
            # Create as many clones of the test node as needed
            # to connect to all test points
            if clone == True:
                test_step = self.test_node.clone()
            else:
                test_step = self.test_node
                clone = True
            test_step.set_name(f"TEST-{self.flow_node.get_name()}-AT-{flow_step.get_name()}")
            g.add_step(test_step)
            # Connect adk to test
            g.connect_by_name(adk, test_step)
            # Connect every specified flow step to a test
            g.connect_by_name(flow_step, test_step)

        return g



def add_power_strategy_test(g: Graph, adk, *test_steps):
    # Define the test node(s)
    static_pa    = Step( 'cadence-voltus-static-power-analysis', default=True )
    static_ra    = Step( 'cadence-voltus-static-rail-analysis', default=True )
    
    # Create enough clones of the test nodes to attach to each test point
    static_pa_nodes = [static_pa]
    static_ra_nodes = [static_ra]
    pa_name = static_pa.get_name()
    ra_name = static_ra.get_name()
    for i in range(len(test_steps) - 1):
        pa_clone = static_pa.clone()
        ra_clone = static_ra.clone()
        pa_clone.set_name(pa_name + f"{i}") 
        ra_clone.set_name(ra_name + f"{i}") 
        static_pa_nodes += [pa_clone]
        static_ra_nodes += [ra_clone]

    # Connect each test node to each test point
    test_conns = zip(test_steps, static_pa_nodes, static_ra_nodes)

    for (test_step, pa_node, ra_node) in test_conns:
        g.add_step(pa_node)
        g.add_step(ra_node)
        g.connect_by_name(adk, pa_node)
        g.connect_by_name(adk, ra_node)
        g.connect_by_name(test_step, pa_node)
        g.connect_by_name(test_step, ra_node)
        g.connect_by_name(pa_node, ra_node)
  
    return g
