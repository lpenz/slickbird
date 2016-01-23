'''Slickbird options importer'''

from tornado.options import define

define('config', default=None, help='Configuration file')
define('database', default='./db', help='Database file')
define('home', default='.', help='Home directory of colletions')
