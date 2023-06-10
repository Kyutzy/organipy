import flask
import uuid
import requests
from datetime import timedelta

app = flask.Flask(__name__)
secret = str(uuid.uuid4())
app.secret_key = secret
spotifyURL = "https://accounts.spotify.com/authorize?client_id=6ffd741239e94c8ca74873a728bbeb90&response_type=code&redirect_uri=http://localhost:8000/authorize&scope=user-library-read user-read-private user-read-email playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private"

def isAuthenticated(f):
    def _internalUse(*args, **kwargs):
        if 'token' in flask.session:
            return f(*args, **kwargs)
        else:
            flask.session['beforeRedirect'] = flask.request.path
            flask.session['baseURL'] = flask.request.base_url
            return flask.redirect(f'/auth')
    _internalUse.__name__ = f.__name__
    return _internalUse

@app.before_request
def make_session_permanent():
    flask.session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=60)

@app.route('/')
def index():
    flask.session['id'] = str(uuid.uuid4())
    return flask.render_template('index.html')

@app.route('/auth')
def auth():
    return flask.redirect(spotifyURL)

@app.route('/authorize')
def authorize():
    requestCode = flask.request.args.get('code')
    flask.session['code'] = requestCode
    print(requestCode)

    postData = {
      "grant_type":"authorization_code",
      "code" : flask.session['code'],
      "redirect_uri":  "http://localhost:8000/authorize",
      "client_secret": '09085b43741240c0ac40326ba6163253',
      "client_id":     '6ffd741239e94c8ca74873a728bbeb90',
    }

    response = requests.post("https://accounts.spotify.com/api/token", data=postData)
    flask.session['token'] = response.json()['access_token']
    return flask.redirect(f'/home' if 'beforeRedirect' not in flask.session else flask.session['beforeRedirect'])

@app.route('/home')
@isAuthenticated
def home():
    headers = {'Authorization': 'Bearer ' + flask.session['token']}
    dados_usuario = requests.get('https://api.spotify.com/v1/me', headers=getHeader())
    dados_playlists = requests.get('https://api.spotify.com/v1/me/playlists', headers=getHeader())
    print(dados_playlists.json())
    return flask.render_template('home.html', dados=[dados_usuario.json(),dados_playlists.json()['items']])

@app.route('/organizar')
@isAuthenticated
def organizar():
    headers = {'Authorization': 'Bearer ' + flask.session['token']}
    dados_playlists = requests.get('https://api.spotify.com/v1/me/playlists', headers=headers)
    return flask.render_template('organizar.html', dados=dados_playlists.json()['items'])

@app.route('/organizar/playlist')
@isAuthenticated
def organizarPlaylist():
    urlPlaylistEscolhida = flask.request.args.get('playlistLink')
    flask.session['urlPlaylistEscolhida'] = urlPlaylistEscolhida
    return flask.render_template('telaOrganizacao.html')

@app.route('/organizar/playlist/filtrado')
@isAuthenticated
def organizarPlaylistFiltrado():
    tipoFiltro = flask.request.args.get('Filtro')
    print(tipoFiltro)
    correspondencia = {'artista' : 'artists', 'album' : 'album', 'genero' : 'genre'}
    url = flask.session['urlPlaylistEscolhida']
    playlist = requests.get(url, headers=getHeader())
    playlist = playlist.json()
    tracks = playlist['tracks']['items']
    tracks = [track['track'] for track in tracks]
    chaveCorrespondente = correspondencia[tipoFiltro]
    organizado = {}
    for track in tracks:
        if chaveCorrespondente in track:
            if track[chaveCorrespondente] not in organizado:
                organizado[track[chaveCorrespondente]] = []
            organizado[track[0][chaveCorrespondente]].append(track)

    return tracks

@isAuthenticated
def getHeader():
    return {'Authorization': 'Bearer ' + flask.session['token']}



if __name__ == '__main__':
    app.run(debug=True, port=8000)