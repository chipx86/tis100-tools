#!/usr/bin/env python

import argparse
from itertools import chain

from tis100.compiler import compile_asm
from tis100.loader import Loader
from tis100.logger import Logger
from tis100.node import Node
from tis100.tis import TIS


def main():
    parser = argparse.ArgumentParser(
        description='Run a saved TIS-100 program.')
    parser.add_argument('filename', help='The program to run.')
    parser.add_argument('--input',
                        metavar='NODE_ID:VALUE,...',
                        action='append',
                        dest='inputs',
                        help='The list of input to feed to a given node.')
    parser.add_argument('--output',
                        metavar='OUTPUT_ID:VALUE,...',
                        dest='outputs',
                        action='append',
                        help='The list of expected outputs to a given node.')
    parser.add_argument('--disabled-nodes',
                        metavar='NODE_ID,...',
                        default='',
                        dest='disabled_node_ids',
                        help='The list of node IDs that are disabled.')

    args = parser.parse_args()

    inputs = []
    loggers = []
    expected_outputs = []
    all_outputs_count = 0

    tis = TIS(
        disabled_node_ids=[
            int(node_id)
            for node_id in args.disabled_node_ids.split(',')
            if node_id
        ])
    loader = Loader(tis)
    logger = Logger(tis)

    with open(args.filename, 'r') as fp:
        loader.load(fp.read())

    for inputs in args.inputs:
        node_id, values = inputs.split(':', 1)
        node_id = int(node_id)
        values = [int(value) for value in values.split(',')]

        tis.buffer_input(tis.nodes[node_id], Node.UP, values)

    for i, outputs in enumerate(args.outputs):
        node_id, values = outputs.split(':', 1)
        node_id = int(node_id)
        values = [int(value) for value in values.split(',')]

        expected_outputs.append(values)
        all_outputs_count += len(values)

        logger.attach_to_output(node_id)

    for _ in tis.run():
        if (not tis.has_buffered_inputs() and
            logger.seen_input_count == all_outputs_count):
            break

    print 'Resulting outputs:'
    results = zip(*list(chain.from_iterable([
        [expected_outputs[i], logger.log_nodes[i].seen_inputs]
        for i in xrange(len(logger.log_nodes))
    ])))

    for values in results:
        print '  '.join(
            '%d: [%3d: %3d]'
            % (i / 2, values[i], values[i + 1])
            for i in xrange(0, len(values), 2)
        )


if __name__ == '__main__':
    main()
