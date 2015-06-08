from __future__ import unicode_literals

import re


OP_RE = re.compile(
    r'(?P<name>[A-Z]+)'
    r'(\s*(?P<arg1>[0-9A-Z_]+)(,?\s*(?P<arg2>[0-9A-Z_]+))?)?')
COMMENT_RE = re.compile('#.*$')


def compile_asm(lines):
    """Compile lines of assembly into a list of opcodes.

    These opcodes can be loaded into a Node.
    """
    ops = []
    labels = {}
    i = 0

    for line in lines:
        line = COMMENT_RE.sub('', line).strip()

        if line:
            if ':' in line:
                label, line = line.split(':', 1)
                line = line.strip()
                labels[label] = i

            m = OP_RE.match(line)

            if m:
                ops.append((m.group('name'), m.group('arg1'),
                            m.group('arg2')))
                i += 1

    return ops, labels
