from .example_with_mush_factory import main
from unittest import TestCase
from testfixtures import TempDirectory, Replacer
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
''' % (db_path, d.getpath('script.log')))
            # setup file to read
            source = d.write('test.txt', 'some text')
            with Replacer() as r:
                r.replace('sys.argv', ['script.py', config, source, '--quiet'])
                main()
            # check results
            self.assertEqual(
                conn.execute('select * from notes').fetchall(),
                [(u'test.txt', u'some text')]
                )