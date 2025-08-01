from sife.utils import compress_file
import openpyexcel as xl
# from password_managing_app.sql_handler import sql_handler
from sife.__init__ import get_username_and_password
from sife.utils import transfer_from_excel_to_mysql
import time
from sife.hdn import Parser
from sife.cloud.cloud import CloudStorageHandler
from sife.cloud.cloud import GithubCLoud
import os
import shutil
from sife.__init__ import get_db_engine
from sife.encryption import encrypt_file, decrypt_file
import hashlib

def get_github_config():
    destination_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/github.json')
    if os.path.exists(destination_file):
        pass
    else:
        with open(destination_file, 'w') as f:
            default_str = '{"token":"", "repo":""}'
            f.write(default_str)

        print('a default github credential file has been created sife/data. Enter access token and repository name.')
        input('press enter to continue...') 
    import json
    github_json = json.load(open(destination_file, 'r'))
    return github_json['token'], github_json['repo']


class Backup:
    def __init__(self, password, compress_file_type='gz', cloud=False, access_token=None, cloud_client='github', repo='None'):
        # self.username, self.password = get_username_and_password()
        self.cmp_format = compress_file_type
        self.password = password
        db_engine = get_db_engine()
        self.repo = repo
        self.db_engine = db_engine
        if db_engine == 'sqlite3':
            from sife.db.sqlite3_handler import sql_handler
            self.sqh = sql_handler(database='sife/data/passwords.db', password=password)
        else:
            from sife.db.sql_handler import sql_handler
            user, password = get_username_and_password()
            self.sqh = sql_handler(user, password, 'passwords')
        self.cloud = cloud
        if self.cloud is True:
            if cloud_client == 'dropbox':
                self.csh = CloudStorageHandler(access_token)
            else:
                token, repo = get_github_config()
                if self.repo is not None:
                    repo = self.repo
                if access_token is not None:
                    token = access_token
                self.csh = GithubCLoud(token, repo)
            
    def create_backup(self, default_path, default_dir=''):
        if default_path is None:
            default_path = os.path.join('sife/data', 'password_backup.xlsx')
        else:
            default_path = os.path.join(default_path, 'password_backup.xlsx')
        try:
            wb = xl.load_workbook(backup_file)
        except FileNotFoundError:
            wb = xl.Workbook()
            wb.create_sheet('Sheet1')
            wb.save(backup_file)
        result = self.sqh.get_result()
        if self.cloud is False:
            index = 1
            sheet = wb['Sheet1']
            for r in result:
                website_data = r[0]
                password_data = r[1]
                username_data = r[2]
                website_cell = sheet.cell(index, 1)
                password_cell = sheet.cell(index, 2)
                username_cell = sheet.cell(index, 3)
                website_cell.value = website_data
                password_cell.value = password_data
                username_cell.value = username_data
                index += 1
            wb.save(backup_file)
            encrypt_file(backup_file, self.password)
            if type(self.cmp_format) == str:
                compressed_backup_filename = compress_file(backup_file, self.cmp_format)
                return
        else:
            index = 1
            sheet = wb['Sheet1']
            for r in result:
                website_data = r[0]
                password_data = r[1]
                username_data = r[2]
                website_cell = sheet.cell(index, 1)
                password_cell = sheet.cell(index, 2)
                username_cell = sheet.cell(index, 3)
                website_cell.value = website_data
                password_cell.value = password_data
                username_cell.value = username_data
                index += 1
            wb.save(backup_file)
            encrypt_file(backup_file, self.password)
            if type(self.cmp_format) == str:
                compressed_backup_filename = compress_file(backup_file, self.cmp_format)
                self.csh.update(compressed_backup_filename, dir=default_dir)
                return
            self.csh.update(backup_file, dir=default_dir)

    def transfer_backup(self):
        to_transfer_from = 'data/password_backup.xlsx'
        to_transfer = '/media/kevin/Windows/Users/Kevin/py_projects/pma-windows/password_backup.xlsx'

        to_transfer_from_file = open(to_transfer_from, 'rb')
        to_transfer_file = open(to_transfer, 'wb')
        data = to_transfer_from_file.read()
        to_transfer_file.write(data)

    def load_backup(self, default_dir=''):
        to_transfer_from = '/usr/share/sife/data/password_backup.xlsx'
        if self.cloud is True:
            if type(self.cmp_format) == str:
                self.csh.download('sife/data/password_backup.xlsx.' + '.enc' + self.cmp_format, dir=default_dir)
                from utils import decompress_file
                decompress_file('sife/data/password_backup.xlsx.' + '.enc' + self.cmp_format, self.cmp_format)
                to_transfer_from = 'sife/data/password_backup.xlsx'
            else:
                self.csh.download('sife/data/password_backup.xlsx.enc', dir=default_dir)
                to_transfer_from = 'sife/data/password_backup.xlsx'
        else:
            # print("didn't readch")
            if type(self.cmp_format) == str:
                decompress_file('sife/data/password_backup.xlsx.enc' + self.cmp_format, self.cmp_format)
                to_transfer_from = 'sife/data/password_backup.xlsx'
        decrypt_file('sife/data/password_backup.xlsx.enc', self.password)
        print('[DELETING INFO TABLE OF EXISTING DATABASE]......')
        self.sqh.execute('DELETE FROM passwords;')
        time.sleep(5)
        print('[WRITING INTO DATABASE]....')
        if self.db_engine == 'mysql':
            from utils import transfer_from_excel_to_mysql
            transfer_from_excel_to_mysql(to_transfer_from)
        else:
            from utils import transfer_from_excel_to_sqlite3
            transfer_from_excel_to_sqlite3(to_transfer_from)
        encrypt_file('sife/data/password_backup.xlsx', password)
        
    def upload(self, default_dir=''):
        self.csh.upload('password_backup.xlsx', dir=default_dir)

class Backup_hdn:
    def __init__(self, password, compress_file_type=None, cloud=False, access_token=None, cloud_client='github', repo=None):
        # self.username, self.password = get_username_and_password()
        self.cmp_format = compress_file_type
        self.password = password
        # self.compressed = compressed
        db_engine = get_db_engine()
        self.repo = repo
        if db_engine == 'sqlite3':
            from sife.db.sqlite3_handler import sql_handler
            self.sqh = sql_handler(database='sife/data/passwords.db', password=password)
        else:
            from sife.db.sql_handler import sql_handler
            user, password = get_username_and_password()
            self.sqh = sql_handler(user, password, 'passwords')
        self.hdn_parser = Parser('sife/data/backup.hdn')
        self.cloud = cloud
        self.file = 'sife/data/backup.hdn'
        if self.cloud is True:
            if cloud_client == 'dropbox':
                self.csh = CloudStorageHandler(access_token)
            else:
                token, repo = get_github_config()
                if self.repo is not None:
                    repo = self.repo
                if access_token is not None:
                    token = access_token
                self.csh = GithubCLoud(token, repo)
        
        
    def create_backup(self, default_path, default_dir=''):
        if default_path is None:
            default_path = os.path.join('sife/data', 'backup.hdn')
        else:
            default_path = os.path.join(default_path, 'backup.hdn')
        if self.cloud is False:
            lines = self.sqh.get_result()
            hdn_parser = self.hdn_parser
            hdn_str = hdn_parser.write_in_hdn(lines)
            hdn_parser.dump(hdn_str, default_path)
            encrypt_file(default_path, self.password)
            if type(self.cmp_format) == str:
                compressed_backup_filename = compress_file(default_path + '.enc', self.cmp_format)
                return
        else:
            lines = self.sqh.get_result()
            hdn_parser = self.hdn_parser
            hdn_str = hdn_parser.write_in_hdn(lines)
            hdn_parser.dump(hdn_str, 'sife/data/backup.hdn')
            encrypt_file(default_path, self.password)
            if type(self.cmp_format) == str:
                compressed_backup_filename = compress_file('sife/data/backup.hdn.enc', self.cmp_format)
                self.csh.update(f'backup.hdn.enc.{self.cmp_format}', compressed_backup_filename)
                return
            self.csh.update('backup.hdn.enc', 'sife/data/backup.hdn.enc')
    def load_backup(self, file='sife/data/backup.hdn', default_dir='', rows=None):
        if self.cloud is True:
            if type(self.cmp_format) == str:
                filename = 'backup.hdn' + '.' + self.cmp_format
                self.csh.download(filename, f'sife/data/{filename}')
                from utils import decompress_file
                decompress_file('sife/data/backup.hdn.enc' + self.cmp_format, self.cmp_format)
                decrypt_file('sife/data/backup.hdn.enc', self.password)
            else:
                self.csh.download('backup.hdn.enc', file + '.enc')
                decrypt_file(file + '.enc', self.password)
            # self.csh.download(file, dir=default_dir)
            shutil.move(file, self.file)
        else:
            if type(self.cmp_format) == str:
                from utils import decompress_file
                decompress_file('sife/data/backup.hdn.enc' + self.cmp_format, self.cmp_format)

            decrypt_file('sife/data/backup.hdn.enc', self.password)
        
        if rows is None:
            rows = self.hdn_parser.parse()
        
        print('[DELETING INFO TABLE OF EXISTING DATABASE]......')
        self.sqh.delete_table()
        print('[LOADING INFO IN DATABASE].....')
        query = f"INSERT INTO {self.sqh.database_name} (website, password, username) VALUES "        
        for row in rows:
            website = row[0]
            password = row[1]
            username = row[2]

            query += f"('{website}', '{password}', '{username}'), "

        # All characters except the last two characters
        query = query[:-2]
        query += ';'
        self.sqh.execute(query, commit=True)
        print('Done!')
        encrypt_file(self.file, self.password)
    
    def upload(self, file, default_dir=''):
        self.csh.upload(file, dir=default_dir)
    
    def sync(self, filename):

        if not self.csh.check_for_file(filename):
            return "File doesn't exist"
        
        self.cloud = False
        self.create_backup(default_dir='sife/', default_path='sife/data/')
        decrypt_file('sife/data/backup.hdn.enc', self.password)
        sha1 = hashlib.sha1()
        BUF_SIZE = 65536
        with open("sife/data/backup.hdn", "rb") as f:
            while True:
                data = f.read(BUF_SIZE)
                if not data:
                    break
                sha1.update(data)
        old_rows = self.hdn_parser.parse()
        encrypt_file('sife/data/backup.hdn', self.password)
        keys = set()
        for row in old_rows:
            key = row[0] + '|' + row[1] + '|' + row[2]
            keys.add(key)
        self.csh.download(filename, f'sife/data/{filename}')
        decrypt_file('sife/data/backup.hdn.enc', self.password)
        sha2 = hashlib.sha1()
        with open("sife/data/backup.hdn", "rb") as f:
            while True:
                data = f.read(BUF_SIZE)
                if not data:
                    break
                sha2.update(data)
        
        if sha1.hexdigest() == sha2.hexdigest:
            return "Files are the same"
        
        rows = self.hdn_parser.parse()

        new_rows = []
        query = f"INSERT INTO {self.sqh.database_name} (website, password, username) VALUES "        
        changed = False
        for row in rows:
            
            key = row[0] + '|' + row[1] + '|' + row[2]
            if key not in keys: 
                changed = True
                website, password, username = row
                print(row)
                query += f"('{website}', '{password}', '{username}'), "

        # All characters except the last two characters
        query = query[:-2]
        query += ';'
        if changed:
            print("Changes made")
            self.sqh.execute(query, commit=True)
            old_rows = old_rows + new_rows
            self.hdn_parser.dump(self.hdn_parser.write_in_hdn(old_rows), 'sife/data/backup.hdn')
        else:
            print("no changes")
        
        encrypt_file('sife/data/backup.hdn', self.password)
        self.cloud = True
        self.create_backup(default_dir='sife/', default_path='sife/data/')
        return "File synced"

class BackupSqlite(Backup_hdn):
    def __init__(self, cloud=False, access_token=None):
        Backup_hdn.__init__(self, cloud, access_token)
        self.file = 'sife/data/passwords.db.enc'

    def create_backup(self, default_dir=''):
        file_exists = self.check_if_file_exists()
        if file_exists:
            self.csh.update(self.file, dir=default_dir)
        else:
            self.upload(file='passwords.db.enc', default_dir=default_dir)

    def load_backup(self, file='passwords.db.enc', default_dir=''):
        self.csh.download(file, dir=default_dir)
        shutil.move(file, self.file)

    def check_if_file_exists(self):
        try:
            dbx.files_get_metadata('/passwords/passwords.db.enc')
            return True
        except:
            return False

# media/kevin/Windows/Users/Kevin/py_projects/pma-windows
