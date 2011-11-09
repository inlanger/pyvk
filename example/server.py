# -*- coding: utf-8 -*-
from bottle import *
import json
import vkontakte
from vkontakte import http

app = Bottle()
vk = vkontakte.API('YOUR_APP_ID', 'YOUR_APP_SECRET')

@app.route('/')
def home():
	return '<a href="http://api.vkontakte.ru/oauth/authorize?client_id=YOUR_APP_ID&scope=PERMISSIONS&redirect_uri=YOUR_RETURN_URL&response_type=code">Authorize me!</a>'

@app.route('/success/')
def test():
	code = request.GET.get('code')
	response.set_cookie("code", code)
	get = http.get('https://api.vkontakte.ru/oauth/access_token?client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&code=' + code,  1)
	json_obj = json.loads(get)
	access_token = json_obj['access_token']
	response.set_cookie("access_token", access_token)
	photos = vk.get('photos.getAlbums', uid='4563348', access_token = access_token)
	return '<h1>This is a test URL!</h1>' + photos

run(app, server='gunicorn')