from re import search
from flask import Flask, jsonify, request
import pprint
import sys
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from flask_cors import CORS

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
   

if __name__ == '__main__':  
   app.run(host='0.0.0.0', debug=True)
 
