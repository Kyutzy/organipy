import flask
from flask import url_for
import uuid
import requests
from datetime import timedelta
import random
import hashlib
import database
import base64
import secretsHandling

app = flask.Flask(__name__)
secret = str(uuid.uuid4())
app.secret_key = secret
spotifyURL = f"https://accounts.spotify.com/authorize?client_id={secretsHandling.F('client_id')}&response_type=code&redirect_uri=http://localhost:8000/authorize&scope=user-library-read user-read-private user-read-email playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private"
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def isAuthenticated(f):
    def _internalUse(*args, **kwargs):
        if 'token' in flask.session:
            return f(*args, **kwargs)
        else:
            flask.session['beforeRedirect'] = flask.request.path
            flask.session['baseURL'] = flask.request.base_url
            return flask.redirect(f'/login')
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

@app.route('/register')
def register():
    return flask.render_template('registrar.html')

@app.route('/handleRegister', methods=['POST'])
def handleRegister():
    usuario = flask.request.form['username']
    senha = flask.request.form['password']
    foto = flask.request.files['foto']
    senha = f"{usuario};{senha}"
    foto.filename = str(uuid.uuid4())
    foto.save(f'static/uploads/{foto.filename}.jpg')
    senha = hashlib.sha256(senha.encode()).hexdigest()
    database.createData(usuario, senha, foto.filename)
    return flask.redirect('/home')

@app.route('/login')
def login():
    return flask.render_template('login.html')

@app.route('/handleLogin', methods=['POST'])
def handleLogin():
    usuario = flask.request.form['username']
    senha = flask.request.form['password']
    senha = f"{usuario};{senha}"
    senha = hashlib.sha256(senha.encode()).hexdigest()
    print(senha)
    data = database.getData(senha)
    print(data)
    if data:
        flask.session['autenticado'] = True
        flask.session['nome'] = data[1]
        flask.session['foto'] = data[2]
        return flask.redirect('/auth')
    else:
        return flask.redirect('/login')


@app.route('/auth')
def auth():
    return flask.redirect(spotifyURL)

@app.route('/authorize')
def authorize():
    requestCode = flask.request.args.get('code')
    flask.session['code'] = requestCode

    postData = {
      "grant_type":"authorization_code",
      "code" : flask.session['code'],
      "redirect_uri":  "http://localhost:8000/authorize",
      "client_secret": f"{secretsHandling.F('client_secret')}",
      "client_id":     f"{secretsHandling.F('client_id')}",
    }

    response = requests.post("https://accounts.spotify.com/api/token", data=postData)
    flask.session['token'] = response.json()['access_token']
    return flask.redirect(f'/home' if 'beforeRedirect' not in flask.session else flask.session['beforeRedirect'])

@app.route('/home')
@isAuthenticated
def home():
    dados_usuario = requests.get('https://api.spotify.com/v1/me', headers=getHeader())
    dados_playlists = requests.get('https://api.spotify.com/v1/me/playlists', headers=getHeader())
    return flask.render_template('home.html', dados=[flask.session['foto'], dados_usuario.json(),dados_playlists.json()['items']])

@app.route('/organizar')
@isAuthenticated
def organizar():
    dados_playlists = requests.get('https://api.spotify.com/v1/me/playlists', headers=getHeader())
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
    correspondencia = {'artista' : 'artists', 'album' : 'album', 'genero' : 'genre'}
    url = flask.session['urlPlaylistEscolhida']
    playlist = requests.get(url, headers=getHeader())
    playlist = playlist.json()
    tracks = playlist['tracks']['items']
    tracks = [track['track'] for track in tracks]
    chaveCorrespondente = correspondencia[tipoFiltro]
    organizado = {'nome' : playlist['name']}
    if chaveCorrespondente == 'genre':
        for track in tracks:
            dadosArtista = requests.get(f"https://api.spotify.com/v1/artists/{track['artists'][0]['id']}", headers=getHeader())
            try:
                generos = {
                    'nome': track['name'],
                    'id' : track['id'],
                    'uri' : track['uri'],
                    'foto' : track['album']['images'][0]['url'],
                    'genero' : dadosArtista.json()['genres'][0]
                    }
            except:
                    generos = {
                    'nome': track['name'],
                    'id' : track['id'],
                    'uri' : track['uri'],
                    'foto' : track['album']['images'][0]['url'],
                    'genero' : "Genero não encontrado"
                    }
            if generos['genero'] not in organizado:
                organizado[generos['genero']] = []
            organizado[generos['genero']].append(generos)
    else:
        for track in tracks:
            if chaveCorrespondente in track:
                chaveFinal = track[chaveCorrespondente]['name'] if chaveCorrespondente != 'artists' else track[chaveCorrespondente][0]['name']
                if chaveFinal not in organizado:
                    organizado[chaveFinal] = []
                organizado[chaveFinal].append({
                    'nome': track['name'],
                    'id' : track['id'],
                    'uri' : track['uri'],
                    'foto' : track['album']['images'][0]['url']
                    })
    flask.session['organizado'] = organizado
    return flask.render_template('previa.html', dados=organizado)

@app.route('/organizar/playlist/filtrado/organizado')
@isAuthenticated
def realizarOrganizacaoSpotify():
    if 'organizado' not in flask.session:
        return flask.redirect('/home')
    organizado = flask.session['organizado']
    usuario = requests.get('https://api.spotify.com/v1/me', headers=getHeader())
    usuario_id = usuario.json()['id']
    nome = organizado['nome']
    for key in organizado:
        if key == 'nome':
            continue
        detalhesPlaylist = {
            'name' : f"{nome} - {key}",
            'public' : False,
            'description' : f"Playlist gerada pelo Organizador de Playlists do Spotify, com base no filtro {key}"
        }
        response = requests.post(f"https://api.spotify.com/v1/users/{usuario_id}/playlists", headers=getHeader(), json=detalhesPlaylist)
        print(response)
        id = response.json()['id']
        uris = [track['uri'] for track in organizado[key]]
        requests.post(f"https://api.spotify.com/v1/playlists/{id}/tracks", headers=getHeader(), json={'uris' : uris})
    return flask.redirect('/home')

@app.route('/randomizar')
@isAuthenticated
def randomizar():
    dados_playlists = requests.get('https://api.spotify.com/v1/me/playlists', headers=getHeader())
    return flask.render_template('aleatorizar.html', dados=dados_playlists.json()['items'])

@app.route('/randomizar/playlist')
@isAuthenticated
def fazerAleatorizacao():
    playlistEscolhida = flask.request.args.get('playlistLink')
    print(playlistEscolhida)
    playlist = requests.get(playlistEscolhida, headers=getHeader())
    tracks = playlist.json()['tracks']
    nome = playlist.json()['name']
    usuario = requests.get('https://api.spotify.com/v1/me', headers=getHeader())
    usuario_id = usuario.json()['id']
    tracks = [track['track'] for track in tracks['items']]
    print(tracks)
    uri = [track['uri'] for track in tracks]
    random.shuffle(uri)
    detalhesPlaylist = {
            'name' : f"{nome} - Aleatória",
            'public' : False,
            'description' : f"Playlist gerada pelo Organizador de Playlists do Spotify, aleatorizada"}
    response = requests.post(f"https://api.spotify.com/v1/users/{usuario_id}/playlists", headers=getHeader(), json=detalhesPlaylist)
    id = response.json()['id']
    requests.post(f"https://api.spotify.com/v1/playlists/{id}/tracks", headers=getHeader(), json={'uris' : uri})
    return flask.redirect('/home')

@isAuthenticated
def getHeader():
    return {'Authorization': 'Bearer ' + flask.session['token']}

if __name__ == '__main__':
    app.run(debug=True, port=8000)