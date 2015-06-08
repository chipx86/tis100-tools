from __future__ import unicode_literals


class Node(object):
    """An independent node in a TIS-100 computer.

    Each node can be loaded with its own assembly program, which may act
    independently of other nodes. These nodes can communicate by sending
    data to each others inputs through their outputs.
    """

    # A node's state.
    IDLE = 0
    RUN = 1
    READ = 2
    WRITE = 3

    # A neighboring node direction.
    UP = 0
    DOWN = 1
    RIGHT = 2
    LEFT = 3

    DIRECTIONS = (UP, DOWN, LEFT, RIGHT)

    _mode_labels = {
        IDLE: 'IDLE',
        RUN: 'RUN',
        READ: 'READ',
        WRITE: 'WRITE',
    }

    _direction_labels = {
        UP: 'UP',
        DOWN: 'DOWN',
        LEFT: 'LEFT',
        RIGHT: 'RIGHT',
    }

    _label_to_direction = {
        'UP': UP,
        'DOWN': DOWN,
        'LEFT': LEFT,
        'RIGHT': RIGHT,
    }

    _opposite_directions = {
        UP: DOWN,
        DOWN: UP,
        LEFT: RIGHT,
        RIGHT: LEFT,
    }

    def __init__(self, node_id, compiled=(None, None)):
        self.node_id = node_id
        self.ops, self.labels = compiled

        self.acc = 0
        self.bak = 0
        self.iptr = 0
        self.next_iptr = 0
        self.cur_op = None
        self._mode = [self.IDLE]

        self._last_port_dir = None

        self.inputs = {}

        self.attached_nodes = {}

        self.op_table = {
            'NOP': self._nop,
            'MOV': self._mov,
            'SWP': self._swp,
            'SAV': self._sav,
            'ADD': self._add,
            'SUB': self._sub,
            'NEG': self._neg,
            'JMP': self._jmp,
            'JEZ': self._jez,
            'JNZ': self._jnz,
            'JGZ': self._jgz,
            'JLZ': self._jlz,
            'JRO': self._jro,
        }

    @property
    def loaded(self):
        """Whether or not the node has a program loaded."""
        return bool(self.ops)

    @property
    def mode(self):
        """The node's current mode."""
        return self._mode[-1]

    def push_mode(self, mode):
        """Push a node mode onto the stack."""
        self._mode.append(mode)

    def pop_mode(self):
        """Pop the last mode off the stack."""
        self._mode.pop()

    def load_bytecode(self, compiled):
        """Load compiled bytecode into the node."""
        self.ops, self.labels = compiled

    def get_next_op(self):
        """Return the next opcode to process."""
        if self.next_iptr >= len(self.ops):
            self.next_iptr = 0

        op = self.ops[self.next_iptr]
        self.iptr = self.next_iptr

        return op

    def attach_node(self, node, direction, bidi=True):
        """Attach another node to this node.

        The node will be attached at the given direction. By default, the
        nodes will be attached bidirectionally, but this can be changed
        by modifying the bidi argument.
        """
        assert direction in self.DIRECTIONS

        self.attached_nodes[direction] = node

        if bidi:
            node.attached_nodes[self._opposite_directions[direction]] = self

    def get_attached_node(self, direction):
        """Return the node attached at the given direction."""
        assert direction in self.DIRECTIONS

        return self.attached_nodes.get(direction)

    def write_input(self, direction, value):
        """Write a value to one of this node's inputs."""
        self._log('<<< %s written from %s'
                  % (value, self._direction_labels[direction]))
        self.inputs.setdefault(direction, []).append(value)

    def read_input(self, direction):
        """Read and pop a value from one of this node's inputs."""
        self._log('<<< Reading from %s' % (self._direction_labels[direction]))
        return self.inputs.setdefault(direction, []).pop(0)

    def has_inputs(self, direction):
        """Return whether this node has any data at a given input."""
        return len(self.inputs.get(direction, [])) > 0

    def run(self):
        """Run the node's program.

        The program will run in a loop, indefinitely. It will block when
        waiting to read or write data.

        Callers should treat this as a generator, running it within a loop.
        """
        while True:
            self.push_mode(self.RUN)

            op, arg1, arg2 = self.get_next_op()
            self.next_iptr = self.iptr + 1

            assert op in self.op_table
            self._log('%s %s, %s' % (op, arg1, arg2))

            for _ in self.op_table[op](arg1, arg2):
                yield

            self._log('DONE: %s %s, %s <ACC = %s, BAK = %s, MODE = %s, '
                      'INPUTS = %r>'
                      % (op, arg1, arg2, self.acc, self.bak,
                         self._mode_labels[self.mode], self.inputs))

            self.pop_mode()

    def _log(self, s):
        """Log data from this node."""
        print '[Node %s] %s' % (self.node_id, s)

    def _nop(self, *args):
        """No-op instruction."""
        yield

    def _mov(self, src, dest):
        """Move data from a source value/location to a destination location."""
        value = None

        for value in self._read_src(src):
            yield

        for _ in self._write_dest(dest, value):
            yield

    def _swp(self, *args):
        """Swap ACC and BAK."""
        self.bak, self.acc = self.acc, self.bak
        yield

    def _sav(self, *args):
        """Save ACC to BAK."""
        self.bak = self.acc
        yield

    def _add(self, src, *args):
        """Add the given value/location's value to ACC."""
        for value in self._read_src(src):
            yield

        self.acc += value

    def _sub(self, src, *args):
        """Subtract the given value/location's value to ACC."""
        for value in self._read_src(src):
            yield

        self.acc -= value

    def _neg(self, src, *args):
        """Negate the value in ACC."""
        self.acc = -self.acc
        yield

    def _jmp(self, label, *args):
        """Jump to the given label."""
        assert label in self.labels
        self.next_iptr = self.labels[label]
        yield

    def _jez(self, label, *args):
        """Jump to the given label if ACC == 0."""
        if self.acc == 0:
            for _ in self._jmp(label):
                yield

    def _jnz(self, label, *args):
        """Jump to the given label if ACC != 0."""
        if self.acc != 0:
            for _ in self._jmp(label):
                yield

    def _jgz(self, label, *args):
        """Jump to the given label if ACC > 0."""
        if self.acc > 0:
            for _ in self._jmp(label):
                yield

    def _jlz(self, label, *args):
        """Jump to the given label if ACC < 0."""
        if self.acc < 0:
            for _ in self._jmp(label):
                yield

    def _jro(self, src, *args):
        """Jump to the given offset.

        The offset may be a value or the result of a source location.
        """
        for value in self._read_src(src):
            yield

        new_iptr = self.next_iptr + value

        self.next_iptr = max(0, min(new_iptr, len(self.ops)))

    def _read_src(self, src):
        """Read data from a source.

        If the data is an input port, this may block while waiting on data
        from that port.
        """
        assert src != 'BAK'

        if src == 'ACC':
            yield self.acc
        elif src == 'NIL':
            yield NIL
        elif src in ('UP', 'DOWN', 'LEFT', 'RIGHT'):
            for src in self._read_input(self._label_to_direction[src]):
                yield src
        elif src == 'ANY':
            self.push_mode(self.READ)

            while True:
                for direction in self.DIRECTIONS:
                    for src in self._read_input(direction, blocking=False):
                        yield src

                        if src is not None:
                            self.pop_mode()
                            return

                yield
        elif src == 'LAST':
            for src in self._read_input(self._last_port_dir):
                yield src
        else:
            # Assume it's a normal value.
            yield int(src)

    def _write_dest(self, dest, value):
        """Write data to a destination.

        If the destination is an output, this may block while waiting to
        write data to the output.
        """
        assert dest in ('ACC', 'NIL', 'UP', 'DOWN', 'LEFT', 'RIGHT', 'ANY',
                        'LAST')

        if dest == 'ACC':
            self.acc = value
        elif dest == 'NIL':
            pass
        elif dest in ('UP', 'DOWN', 'LEFT', 'RIGHT'):
            for _ in self._write_output(self._label_to_direction[dest], value):
                yield
        elif dest == 'ANY':
            self.push_mode(self.WRITE)

            while True:
                for direction in self.DIRECTIONS:
                    for result in self._write_output(direction, value,
                                                     blocking=False):
                        if result:
                            self.pop_mode()
                            return

                        yield

                yield
        elif dest == 'LAST':
            for _ in self._write_output(self._last_port_dir, value):
                yield

    def _read_input(self, direction, blocking=True):
        """Read data from an input port.

        By default, this blocks while waiting on data from the port.
        While waiting, the node's mode will be READ.
        """
        self.push_mode(self.READ)
        node = self.get_attached_node(direction)
        opposite_dir = self._opposite_directions[direction]

        while not self.has_inputs(direction):
            if blocking:
                yield
            else:
                self.pop_mode()
                return

        result = self.read_input(direction)
        self._last_port_dir = direction
        self.pop_mode()

        assert result is not None

        yield result

    def _write_output(self, direction, value, blocking=True):
        """Write data to an output port.

        By default, this blocks while waiting to write data to the port.
        While waiting, the node's value will be WRITE.
        """
        self.push_mode(self.WRITE)

        node = self.get_attached_node(direction)
        opposite_dir = self._opposite_directions[direction]

        if not node:
            if blocking:
                # Deadlock.
                pass
            else:
                self.pop_mode()

            return

        node.write_input(self._opposite_directions[direction], value)
        self._last_port_dir = direction

        while node.has_inputs(opposite_dir):
            if blocking:
                yield
            else:
                self.pop_mode()
                return

        self.pop_mode()

        yield True
