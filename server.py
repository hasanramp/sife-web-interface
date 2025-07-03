from flask import Flask
from flask import render_template
from flask import request
from sife.password_manager import password_manager
import os

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/fn-pwd", methods=['GET', 'POST'])
def fn_pwd():
    if request.method == 'POST':
        website = request.form.get('Website')
        username = request.form.get('Username')
        master_password = request.form.get('master_password')
        pm = password_manager('sife/data/passwords.db', master_password)
    
        if username == '':
            username = None
        password = pm.find_password(website=website, username=username)
        if type(password) == str:
            return render_template("fn-result.html", passwords=[[website, password, username]])
        if type(password) == dict :
            import operator
            sorted_d = dict( sorted(password.items(), key=operator.itemgetter(1),reverse=True))
            matched_arr = []
            website_length = len(website)
            for keys in sorted_d:
                matches = sorted_d[keys]
                if matches >= website_length and len(keys[0]) <= len(website) * 3:
                    website, password_, username = keys
                    matched_arr.append([website, password_, username])
            
            return render_template("fn-result.html", passwords=matched_arr)
        else:
            return render_template("fn-result.html", passwords=password)
        
        

        exit()
        for p in password:
            print(p[1])
        return render_template("fn-result.html", passwords=password)
    

    return render_template("fn-pwd.html")


@app.route("/en-pwd", methods=['GET', 'POST'])
def en_pwd():
    if request.method == 'POST':
        website = request.form.get('Website')
        username = request.form.get('Username')
        password = request.form.get('Password')
        master_password = request.form.get('master_password')
        pm = password_manager('sife/data/passwords.db', master_password)
        res = pm.enter_password(website, password, username)
        if res != None:
            return render_template("en-pwd-invalid-result.html")
        else:
            if website[0] == '@':
                website = website[1:]
            return render_template('single-result.html', passwords=[[website, password, username]])
    # return render_template("en-pwd.html")

@app.route("/gen-pwd", methods=['POST'])
def gen_pwd():

    website = request.form.get("Website")
    master_password = request.form.get('master_password')
    pm = password_manager('sife/data/passwords.db', master_password)

    password = pm.generate(website, 10, username)
    return render_template('single-result.html', passwords=[[website, password, username]])

@app.route("/delete", methods=['POST'])
def delete():
    website = request.form.get('Website')
    username = request.form.get('Username')
    username = 'NULL' if username == '' else username
    master_password = request.form.get('master_password')
    pm = password_manager('sife/data/passwords.db', master_password)
    print(website, username)
    pm.sqh.delete_password(website, username)

    return "Password deleted"

@app.route("/show", methods=['GET', 'POST'])
def show():
    print(request.method)
    master_password = request.form.get('master_password')
    pm = password_manager('sife/data/passwords.db', master_password)

    result = pm.sqh.get_result()
    return render_template("fn-result.html", passwords=result)

@app.route('/backup/', defaults={'function': None}, methods=['GET', 'POST'])
@app.route("/backup/<function>", methods=['GET', 'POST'])
def backup(function):
    if request.method == 'GET':
        return render_template("backup.html")
    else:
        from sife.cloud.backup import Backup, Backup_hdn

        cloud = request.form.get('cloud')
        master_password = request.form.get('master_password')
        compression = request.form.get('compression')
        access_token = request.form.get('access_token')        
        filetype = request.form.get('filetype')
        cloud = True if cloud == 'on' else False

        if cloud and access_token == '':
            pm = password_manager('sife/data/passwords.db', master_password)
            access_token = pm.find_password('githubToken', 'githubToken')
            if type(access_token) != str:
                return 'Invalid access token'


        if filetype == 'hdn':
            backup = Backup_hdn(master_password, cloud=cloud, access_token=access_token, compress_file_type=compression)
        else:
            backup = Backup(master_password, cloud=cloud, access_token=access_token, compress_file_type=compression)
        
        if function == 'create':
            backup.create_backup(default_dir='sife/', default_path='sife/data')
            return "Backup created"
        else:
            backup.load_backup(default_dir='sife/')
            return "backup loaded"
# with app.test_request_context('/fn-pwd', method='POST'):
#     print('reached here')

@app.route("/setup", methods=['GET', 'POST'])
def setup():
    if request.method == 'GET':
        return render_template("setup.html")
    else:
        from sife.encryption import encrypt_file
        from sife.db.sqlite3_handler import sql_handler
        master_password = request.form.get("master_password")
        with open("sife/data/passwords.db", 'w') as f:
            pass
        encrypt_file('sife/data/passwords.db', master_password)
        sqh = sql_handler('sife/data/passwords.db', master_password)
        sqh.execute('CREATE TABLE passwords (website text, password text, username text);')
        return "Setup complete"