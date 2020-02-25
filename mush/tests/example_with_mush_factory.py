from mush import Runner, requires, Value
from argparse import ArgumentParser, Namespace

from .example_with_mush_clone import (
    DatabaseHandler, parse_args, parse_config, do,
    setup_logging
    )


def options(parser):
    parser.add_argument('config', help='Path to .ini file')
    parser.add_argument('--quiet', action='store_true',
                        help='Log less to the console')
    parser.add_argument('--verbose', action='store_true',
                        help='Log more to the console')
    parser.add_argument('path', help='Path to the file to process')

def make_runner(do):
    runner = Runner(ArgumentParser)
    runner.add(options, requires=ArgumentParser)
    runner.add(parse_args, requires=ArgumentParser)
    runner.add(parse_config, requires=Namespace)
    runner.add(setup_logging, requires(
        log_path=Value('config')['log'],
        quiet=Value(Namespace).quiet,
        verbose=Value(Namespace).verbose,
    ))
    runner.add(DatabaseHandler, requires=Value('config')['db'])
    runner.add(
        do,
        requires(Value(DatabaseHandler).conn, Value(Namespace).path)
    )
    return runner

main = make_runner(do)
