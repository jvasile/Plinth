from menu import Menu
import os
import StringIO

from ConfigParser import SafeConfigParser
parser = SafeConfigParser(
    defaults={
        'root':os.path.dirname(os.path.realpath(__file__)),
        'product_name':"Plinth",
        'box_name':"FreedomBox",
        'file_root': os.getcwd(),
        'data_dir':'%(file_root)s/data',
        'store_file':'%(data_dir)s/store.sqlite3',
        'user_db':'%(data_dir)s/users',
        'status_log_file':'%(data_dir)s/status.log',
        'access_log_file':'%(data_dir)s/access.log',
        'users_dir':'%(data_dir)s/users',
        'pidfile':'%(data_dir)s/pidfile.pid',
        'host':"127.0.0.1",
        'port':"8000",
        })

# populate empty sections in case file isn't found
parser.readfp(StringIO.StringIO("[Name]\n[Path]\n[Network]"))

parser.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'plinth.config'))

product_name = parser.get('Name', 'product_name')
box_name = parser.get('Name', 'box_name')
root = parser.get('Path', 'root')
file_root = parser.get('Path', 'file_root')
data_dir = parser.get('Path', 'data_dir')
store_file = parser.get('Path', 'store_file')
user_db = parser.get('Path', 'user_db')
status_log_file = parser.get('Path', 'status_log_file')
access_log_file = parser.get('Path', 'access_log_file')
users_dir = parser.get('Path', 'users_dir')
pidfile = parser.get('Path', 'pidfile')
host = parser.get('Network', 'host')
port = parser.get('Network', 'port')
if port:
    try:
        port = int(port)
    except ValueError:
        port = int(parser.get('DEFAULT', 'port'))

html_root = None
main_menu = Menu()
base_href = ""

if store_file.endswith(".sqlite3"):
    store_file = os.path.splitext(store_file)[0]
