from __future__ import unicode_literals

from tis100.node import Node


class LogNode(Node):
    """A special node that simply logs data sent to its inputs."""

    def __init__(self, logger, node_id):
        super(LogNode, self).__init__(node_id)

        self.logger = logger
        self.seen_inputs = []

    def write_input(self, direction, i):
        self._log('Got input: %s' % i)
        self.seen_inputs.append(i)
        self.logger.seen_input_count += 1


class Logger(object):
    """Logs output coming from one or more nodes."""

    def __init__(self, tis):
        self.tis = tis
        self.log_nodes = []
        self.seen_input_count = 0

    def attach_to_output(self, node_id):
        """Attach a logger to the output of a node."""
        log_node = LogNode(self, 'Out %s' % len(self.log_nodes))
        self.log_nodes.append(log_node)

        self.tis.nodes[node_id].attach_node(log_node, Node.DOWN, bidi=False)
