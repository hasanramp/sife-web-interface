import sqlite3
from sife.encryption import encrypt_file, decrypt_file

class sql_handler:
    def __init__(self, database, password):
        self.password = password
        self.database_filename = 'sife/data/passwords.db'
        self.database = database.split('/')[-1]
        self.database_name = self.database.replace('.db', '')

    def get_result(self):
        try:
            result = self.execute('SELECT * FROM passwords;')
        except sqlite3.OperationalError:
            self.execute('CREATE TABLE passwords (website text, password text, username text);')
            result = []
        return result

    def commit(self):
        self.password_database.commit()

    def execute(self, query, commit=False):
        decrypt_file(self.database_filename + '.enc', self.password)
        self.password_database = sqlite3.connect(self.database_filename)
        self.cursor = self.password_database.cursor()
        self.cursor.execute(query)
        result =  self.cursor.fetchall()
        if commit:
            self.commit()
        self.password_database.close()
        encrypt_file(self.database_filename, self.password)
        return result

    def insert_password(self, website, password, username):
        if username is None:
            username = 'NULL'
        try:
            query = f'INSERT INTO {self.database_name} VALUES ("{website}", "{password}", "{username}");'
            self.execute(query, commit=True)
        except sqlite3.OperationalError:
            self.insert_password_single_quotes(website, password, username)

    def delete_password(self, website, username):
        query = f'DELETE FROM {self.database_name} WHERE website = "{website}" AND username = "{username}"'
        self.execute(query, commit=True)
        
    def insert_password_single_quotes(self, website, password, username):
        """
        When inserting password and website, if either of them have double quotes, mysql throws an error.
        Therefore, this function is designed to counter that and execute query successfully
        """
        query = f"INSERT INTO {self.database_name} VALUES ('{website}', '{password}', '{username}')"
        self.execute(query, commit=True)

    def replace_password(self, website, password, username):
        if username == None:
            username = 'NULL'
        elif username == 'None':
            username = 'NULL'
        query = f"UPDATE {self.database_name} SET password='{password}' WHERE website='{website}' AND username='{username}'"
        self.execute(query, commit=True)

    def delete_table(self):
        self.execute('DELETE FROM ' + self.database_name + ';', commit=True)
