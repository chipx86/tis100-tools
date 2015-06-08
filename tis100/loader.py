from __future__ import unicode_literals

from tis100.compiler import compile_asm


class Loader(object):
    """Handles compiling and loading programs into a TIS-100."""

    def __init__(self, tis):
        self.tis = tis

    def load(self, data):
        """Load a new program into the TIS-100."""
        cur_program = []
        cur_node = None
        programs = []

        disabled_node_ids = sorted(self.tis.disabled_node_ids)
        node_id_offset = 0

        for line in data.splitlines():
            if line.startswith('@'):
                node_id = int(line[1:]) + node_id_offset

                while disabled_node_ids and node_id >= disabled_node_ids[0]:
                    node_id += 1
                    node_id_offset += 1
                    disabled_node_ids.pop(0)

                cur_node = self.tis.nodes[node_id]
                cur_program = []
                programs.append((cur_node, cur_program))
            else:
                cur_program.append(line)

        for node, program in programs:
            node.load_bytecode(compile_asm(program))
