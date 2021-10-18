from re import search
from flask import Flask, jsonify, request
import pprint
import sys
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from flask_cors import CORS
from pymongo import MongoClient
import bcrypt

client = MongoClient('localhost', 27017)
db = client.mytopster

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
cid = "79b0fc127f5a49978ea0045844685dcf"
secret = "05cb5b72719d435f8b02df73658b44a6"
sp = spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=cid, client_secret=secret))

""" if len(sys.argv) > 1:
    search_str = sys.argv[1]
else:
    search_str = '박소은'

res = sp.search(search_str, limit="20",type='album', market='KR') """

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
    """ pprint.pprint(result) """
    return result

@app.route('/api/upload', methods=['POST'])
def post_topster():
    data = request.data
    print(data)
    return jsonify({'msg':"data received"})

#---------회원가입---------
@app.route('/api/join', methods=['POST'])
def post_join():
    data = request.get_json()
    findID = db.user.find_one({"join_email":data['join_email']})
    if findID:
        return jsonify({'msg':"invalid"})
    
    password = data['join_password']
    bpw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    str_bpw = bpw.decode('utf-8')
    data['join_password'] = str_bpw
    print(data)
    db.user.insert_one(data)
    return jsonify({'msg':"join data received"})

#---------로그인---------
@app.route('/api/login', methods=['POST'])
def post_login():
    data = request.get_json()
    password = data['login_password']
    

    findID = db.user.find_one({"join_email":data['login_email']},{'_id': False})
    if findID:
        db_bpw = findID['join_password']
        checkpw = bcrypt.checkpw(password.encode('utf-8'), db_bpw.encode('utf-8'))
        print(checkpw)
        if checkpw:
            return jsonify({'msg':"allowed"})
    print(data)
    return jsonify({'msg':"tryagain"})




if __name__ == '__main__':  
   app.run(host='0.0.0.0', debug=True)