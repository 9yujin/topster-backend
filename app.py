from logging import currentframe
from re import search
from flask import Flask, json, jsonify, request
import pprint
import sys
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from flask_cors import CORS
from pymongo import MongoClient
import bcrypt
import jwt
import base64
import os
from datetime import datetime, timedelta

client = MongoClient('localhost', 27017)
db = client.mytopster

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
cid = "79b0fc127f5a49978ea0045844685dcf"
secret = "05cb5b72719d435f8b02df73658b44a6"
sp = spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=cid, client_secret=secret))

@app.route('/')
def enter_page():
    print("req")
    return jsonify({'msg':"data received"})


#---------앨범아트----------
@app.route('/api/albums')
def get_arts():
    search_str = request.args.get('search')
    print(search_str)

    test = sp.search(search_str, limit="50",type='album', market='KR')['albums']['items']
    pprint.pprint(test)
    response = sp.search(search_str, limit="50",type='album', market='KR')['albums']['items']
    images=[]
    titles=[]
    artists=[]
    ids=[]
    for i in response:
        images.append(i['images'][0]['url'])
        titles.append(i['name'])
        artists.append(i['artists'][0]['name'])
        ids.append(i['id'])
    result = {}
    result_tmp = []
    for i in range(len(images)):
        result_tmp.append({"image": images[i], "title": titles[i], "artist": artists[i], "id": ids[i]})
    result["res"] = {"albums": result_tmp}
    return result



#---------업로드---------
@app.route('/api/upload', methods=['POST'])
def post_topster():
    now = datetime.now()
    now2 = now.strftime("%D_%H%M_%S")
    date = now2.replace('/', '-')
    
    try:
        data = request.get_json()
        userid = request.args.get('user')

        absolute_path = os.path.abspath(__file__)
        path = os.path.dirname(absolute_path)
        path_root = os.path.dirname(path)
        path_user = path_root + '/images/' + userid

        if not os.path.exists(path_user):
            os.makedirs(path_user)

        dataValue = str(data['topsterimage'])
        dataBin=dataValue.split(',')[1]
        imgdata = base64.b64decode(dataBin)
    
        filename = path_user + '/' + date +'.png' 
        data = {"userid":userid, "filename":filename, "like": 0, "date":now}
        db.posts.insert_one(data)
        with open(filename, 'wb') as f:
            f.write(imgdata)
        
        return jsonify({'msg':"upload succeeded"})
    except:
        return jsonify({'msg':"error"})



#-------피드 가져오기-------
@app.route('/api/feed', methods=['GET'])
def get_feed():
    search_user = request.args.get('search')
    if search_user == "all":
        data = list(db.posts.find({}, {'_id': False}))
        data.reverse()
        newdata = list()
        for i in data:
            with open(i['filename'], "rb") as f:
                filedata = f.read()
                encoded = base64.b64encode(filedata)
                topsterimage = "data:image/png;base64," + encoded.decode('utf-8')
            doc = {'userid':i['userid'], 'topsterImage':topsterimage, 'like':i['like'], 'date':i['date']}
            newdata.append(doc)
        return jsonify({"feedData":newdata})        
    return jsonify({'msg':"received"})



#---------회원가입---------
@app.route('/api/join', methods=['POST'])
def post_join():
    data = request.get_json()
    findID = db.user.find_one({"join_id":data['join_id']})
    if findID:
        return jsonify({'msg':"invalid"})
    
    password = data['join_password']
    bpw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    str_bpw = bpw.decode('utf-8')
    data['join_password'] = str_bpw
    print(data)
    db.user.insert_one(data)
    return jsonify({'msg':"registered"})



app.config['JWT_SECRET_KEY'] = 'your_secret_key_for_jwt'
algorithm = 'HS256'
#---------로그인---------
@app.route('/api/login', methods=['POST'])
def post_login():
    data = request.get_json()
    password = data['login_password']
    
    findID = db.user.find_one({"join_id":data['login_id']},{'_id': False})
    if findID:
        db_bpw = findID['join_password']
        db_id = findID["join_id"]
        checkpw = bcrypt.checkpw(password.encode('utf-8'), db_bpw.encode('utf-8'))
        print(checkpw)
        if checkpw:
            jwt_token = jwt.encode({"id":db_id, 'exp':datetime.utcnow() + timedelta(weeks=5)}, app.config['JWT_SECRET_KEY'], algorithm)
            db.user.update({'join_id':db_id}, {'$set':{'jwt':jwt_token}})
            return jsonify({'msg':"allowed", "name":db_id, "access_token":jwt_token})
    print(data)
    return jsonify({'msg':"tryagain"})



#---------jwt인증---------
@app.route('/api/auth', methods=['GET'])
def get_auth():
    cli_jwt = request.headers.get("Authorization")
    if cli_jwt:
        payload = jwt.decode(cli_jwt, app.config["JWT_SECRET_KEY"], algorithm)
        findID = db.user.find_one({"join_id":payload['id']}, {'_id':False})
        if findID:
            return jsonify({'msg':"allowed", 'name':findID["join_name"], 'id':payload['id']})
    else:
        return jsonify({'msg':"not allowed"})

#---------로그아웃(jwt삭제)---------
@app.route('/api/logout', methods=['GET'])
def get_logout():
    cli_jwt = request.headers.get("Authorization")
    if cli_jwt:
        payload = jwt.decode(cli_jwt, app.config["JWT_SECRET_KEY"], algorithm)
        findID = db.user.find_one({"join_id":payload['id']}, {'_id':False})
        if findID:
            db.user.update_one({'join_id':payload['id']},{'$set':{'jwt':""}})
            return jsonify({'msg':"succeeded"})
    else:
        return jsonify({'msg':"no jwt"})


if __name__ == '__main__':  
   app.run(host='0.0.0.0', debug=True)