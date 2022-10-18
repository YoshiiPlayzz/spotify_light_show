import math
import os
import random
import time

import requests

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv


def setup(sp):
    playback = sp.current_playback()
    uri = playback['item']['id']
    current_time = playback['progress_ms'] / 1000

    timestamp = playback['timestamp']
    analysis = sp.audio_analysis(uri)
    # analysis['track']['codestring'] = ""
    # analysis['track']['echoprintstring'] = ""
    # analysis['track']['synchstring'] = ""
    # analysis['track']['rhythmstring'] = ""
    highs = []
    test = []

    for val in analysis['segments']:
        # Append to highs if confidence is over 0.137
        if val['confidence'] >= 0.137:
            highs.append(round(val['start'], 2))
            test.append(val['loudness_max'])

    print(f"Now playing: {playback['item']['name']} by {playback['item']['artists'][0]['name']}")
    mil = int(round(time.time() * 1000))
    time_lost = (mil - timestamp)
    current_time += round(time_lost / 1000000, 2)

    return mil, time_lost, current_time, highs, test, uri


def random_rgb() -> any:
    rgb = [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)]
    return rgb


if __name__ == '__main__':

    load_dotenv()

    # Hassio client token
    client_token = os.getenv("CLIENT_TOKEN")
    entity_id = os.getenv("ENTITY_ID")
    hass_url = os.getenv("HASS_URL")

    # Spotify client id, client secret, scope and redirect uri
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    scope = "user-read-playback-state,user-modify-playback-state"
    redirect_uri = os.getenv("REDIRECT_URI")

    sp = spotipy.Spotify(
        client_credentials_manager=SpotifyOAuth(client_id=client_id, client_secret=client_secret, scope=scope,
                                                redirect_uri=redirect_uri))

    s = setup(sp)

    milliseconds = s[0]
    time_lost = s[1]
    current_time = s[2]
    highs = s[3]
    test = s[4]
    uri = s[5]

    # Home assistant post headers
    headers = {
        'Authorization': 'Bearer ' + client_token,
        # Already added when you pass json= but not when you pass data=
        # 'Content-Type': 'application/json',
    }

    while True:
        current_time += 0.01

        time_rounded = int(current_time * 100) / 100

        if time_rounded % 4 == 0:
            playback = sp.current_playback()
            if not playback['is_playing']:
                current_time -= 0.1
            if playback['item']['id'] != uri:
                uri = setup(sp)[5]

        if time_rounded in highs:
            json_data = {
                'entity_id': entity_id,
                'rgb_color': random_rgb(),
            }
            response = requests.request('post', hass_url + '/api/services/light/turn_on',
                                        headers=headers, json=json_data)

        time.sleep(0.01)
