from .example_with_mush_clone import DatabaseHandler, main, do, setup_logging
from unittest import TestCase
from testfixtures import TempDirectory
from testfixtures import Replacer
from testfixtures import LogCapture
from testfixtures import ShouldRaise
import sqlite3

class Tests(TestCase):

    def test_main(self):
        with TempDirectory() as d:
            # setup db
            db_path = d.getpath('sqlite.db')
            conn = sqlite3.connect(db_path)
            conn.execute('create table notes (filename varchar, text varchar)')
            conn.commit()
            # setup config
            config = d.write('config.ini', '''
[main]
db = %s
log = %s
''' % (db_path, d.getpath('script.log')), 'ascii')
            # setup file to read
            source = d.write('test.txt', 'some text', 'ascii')
            with Replacer() as r:
                r.replace('sys.argv', ['script.py', config, source, '--quiet'])
                main()
            # check results
            self.assertEqual(
                conn.execute('select * from notes').fetchall(),
                [('test.txt', 'some text')]
                )

    # coverage.py says no test of branch to log.check call!
    def test_do(self):
        # setup db
        conn = sqlite3.connect(':memory:')
        conn.execute('create table notes (filename varchar, text varchar)')
        conn.commit()
        with TempDirectory() as d:
            # setup file to read
            source = d.write('test.txt', 'some text', 'ascii')
            with LogCapture() as log:
                # call the function under test
                do(conn, source) # pragma: no branch (coverage.py bug)
            # check results
            self.assertEqual(
                conn.execute('select * from notes').fetchall(),
                [('test.txt', 'some text')]
                )
            # check logging
            log.check(('root', 'INFO', "Successfully added 'test.txt'"))

    def test_setup_logging(self):
        with TempDirectory() as dir:
            with LogCapture():
                setup_logging(dir.getpath('test.log'), verbose=True)
                
class DatabaseHandlerTests(TestCase):

    def setUp(self):
        self.dir = TempDirectory()
        self.addCleanup(self.dir.cleanup)
        self.db_path = self.dir.getpath('test.db')
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute('create table notes '
                          '(filename varchar, text varchar)')
        self.conn.commit()
        self.log = LogCapture()
        self.addCleanup(self.log.uninstall)

    def test_normal(self):
        with DatabaseHandler(self.db_path) as handler:
            handler.conn.execute('insert into notes values (?, ?)',
                                 ('test.txt', 'a note'))
            handler.conn.commit()
        # check the row was inserted and committed
        curs = self.conn.cursor()
        curs.execute('select * from notes')
        self.assertEqual(curs.fetchall(), [('test.txt', 'a note')])
        # check there was no logging
        self.log.check()

    def test_exception(self):
        with ShouldRaise(Exception('foo')):
            with DatabaseHandler(self.db_path) as handler:
                handler.conn.execute('insert into notes values (?, ?)',
                                     ('test.txt', 'a note'))
                raise Exception('foo')
        # check the row not inserted and the transaction was rolled back
        curs = handler.conn.cursor()
        curs.execute('select * from notes')
        self.assertEqual(curs.fetchall(), [])
        # check the error was logged
        self.log.check(('root', 'ERROR', 'Something went wrong'))
