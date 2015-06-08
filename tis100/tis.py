from __future__ import unicode_literals

from tis100.node import Node


class TIS(object):
    """An implementation of ths TIS-100 computer.

    This handles the management of nodes and their execution, along with
    buffering data to stream to one or more nodes.
    """

    MAX_NODES_X = 4
    MAX_NODES_Y = 3

    def __init__(self, nodes=[], disabled_node_ids=[]):
        self.disabled_node_ids = set(disabled_node_ids)

        if not nodes:
            self.nodes = [
                Node(unicode(self.MAX_NODES_X * y + x))
                for y in xrange(self.MAX_NODES_Y)
                for x in xrange(self.MAX_NODES_X)
            ]

            for y in xrange(self.MAX_NODES_Y):
                for x in xrange(self.MAX_NODES_X):
                    node = self.nodes[self.MAX_NODES_X * y + x]

                    if 0 < y < self.MAX_NODES_Y:
                        node.attach_node(
                            self.nodes[self.MAX_NODES_X * (y - 1) + x],
                            Node.UP)

                    if 0 < x < self.MAX_NODES_X:
                        node.attach_node(
                            self.nodes[self.MAX_NODES_X * y + x - 1],
                            Node.LEFT)

        self.buffered_input = {}
        self.num_buffered_inputs = 0

    def buffer_input(self, node, direction, values):
        """Buffer some data to a stream to a node's input.

        Whenever the node is available to read a value from the matching
        input, this will send the next value.
        """
        self.num_buffered_inputs += len(values)
        self.buffered_input.setdefault(node, {}).setdefault(direction,
                                                            []).extend(values)

    def has_buffered_inputs(self):
        """Return whether there are any buffered inputs remaining."""


    def run(self):
        """Run the TIS-100.

        This will run in a loop, indefinitely, until the caller shuts it
        down.
        """
        node_runs = [
            (node, node.run())
            for node in self.nodes
            if node.loaded
        ]

        while True:
            for node, node_run in node_runs:
                if node in self.buffered_input and node.mode == Node.READ:
                    for d, values in self.buffered_input[node].iteritems():
                        if values and not node.has_inputs(d):
                            node.write_input(d, values.pop(0))
                            self.num_buffered_inputs -= 1
                            break

                yield next(node_run)
