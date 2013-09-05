from mush import Runner, first, last, attr, item
from argparse import ArgumentParser, Namespace

from .example_with_mush_clone import (
    DatabaseHandler, Config, parse_args, parse_config, do,
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
    runner.add(options, ArgumentParser)
    runner.add(parse_args, last(ArgumentParser))
    runner.add(parse_config, first(Namespace))
    runner.add(setup_logging,
               log_path = item(first(Config), 'log'),
               quiet = attr(first(Namespace), 'quiet'),
               verbose = attr(first(Namespace), 'verbose'))
    runner.add(DatabaseHandler, item(Config, 'db'))
    runner.add(do,
               attr(DatabaseHandler, 'conn'),
               attr(Namespace, 'path'))
    return runner

main = make_runner(do)
