from argparse import ArgumentParser
from .configparser import RawConfigParser
import logging, os, sqlite3, sys

log = logging.getLogger()

def main():
    parser = ArgumentParser()
    parser.add_argument('config', help='Path to .ini file')
    parser.add_argument('--quiet', action='store_true',
                        help='Log less to the console')
    parser.add_argument('--verbose', action='store_true',
                        help='Log more to the console')
    parser.add_argument('path', help='Path to the file to process')

    args = parser.parse_args()
    
    config = RawConfigParser()
    config.read(args.config)
    
    handler = logging.FileHandler(config.get('main', 'log'))
    handler.setLevel(logging.DEBUG)
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)

    if not args.quiet:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(logging.DEBUG if args.verbose else logging.INFO)
        log.addHandler(handler)

    conn = sqlite3.connect(config.get('main', 'db'))

    try:
        filename = os.path.basename(args.path)
        with open(args.path) as source:
            conn.execute('insert into notes values (?, ?)',
                         (filename, source.read()))
        conn.commit()
        log.info('Successfully added %r', filename)
    except:
        log.exception('Something went wrong')

if __name__ == '__main__':
    main()
