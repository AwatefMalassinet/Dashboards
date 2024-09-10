from dotenv import load_dotenv
import os
import base64
from requests import post, get
import pandas as pd
import json

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
country_code = os.getenv("COUNTRY_CODE")
artist_names = os.getenv('ARTIST_NAMES')

# Vérification que ARTIST_NAMES n'est pas None
if artist_names is None:
    raise ValueError("ARTIST_NAMES is not defined in the .env file.")

artist_names = artist_names.split(",")

def get_token():
    auth_string = f"{client_id}:{client_secret}"
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": f"Basic {auth_base64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {"grant_type": "client_credentials"}
    result = post(url, headers=headers, data=data)
    token = result.json()["access_token"]
    return token

def get_auth_header(token):
    return {"Authorization": f"Bearer {token}"}

def search_for_artist(token, artist_name):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f"?q={artist_name}&type=artist&limit=1"

    result = get(url + query, headers=headers)
    artists = result.json()["artists"]["items"]
    if not artists:
        print(f"No artist with the name '{artist_name}' exists...")
        return None
    return artists[0]

def get_albums_by_artist(token, artist_id, country_code):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/albums?market={country_code}&include_groups=album,single&limit=50"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    return result.json().get('items', [])

def get_tracks_by_album(token, album_id, country_code):
    url = f"https://api.spotify.com/v1/albums/{album_id}/tracks?market={country_code}&limit=50"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    return result.json().get('items', [])

def get_track_details(token, track_id, country_code):
    url = f"https://api.spotify.com/v1/tracks/{track_id}?market={country_code}"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    return result.json()

def get_audio_features(token, track_id):
    url = f"https://api.spotify.com/v1/audio-features/{track_id}"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    return result.json()

def get_songs_by_artist(token, artist_id, country_code):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?country={country_code}"
    headers = get_auth_header(token)
    results = get(url, headers=headers)
    return results.json().get("tracks", [])

# Obtenir le token d'accès
token = get_token()

# Créer une liste pour contenir les détails de toutes les pistes
all_track_details = []

# Parcourir chaque artiste dans la liste
for artist_name in artist_names:
    artist_name = artist_name.strip()  # Enlever les espaces en début et fin de nom

    # Recherche de l'artiste
    artist = search_for_artist(token, artist_name)
    if artist:
        artist_id = artist["id"]

        # Récupération des albums
        albums = get_albums_by_artist(token, artist_id, country_code)

        # Pour chaque album, récupérer les pistes
        for album in albums:
            album_id = album["id"]
            tracks = get_tracks_by_album(token, album_id, country_code)

            for track in tracks:
                track_id = track["id"]
                track_details = get_track_details(token, track_id, country_code)
                audio_features = get_audio_features(token, track_id)

                # Collecte des caractéristiques d'intérêt
                track_data = {
                    "artist_name": track_details["artists"][0]["name"] if track_details["artists"] else "N/A",
                    "track_id": track_details["id"],
                    "track_name": track_details["name"],
                    "album_id": track_details["album"]["id"],
                    "album_name": track_details["album"]["name"],
                    "track_number": track_details["track_number"],
                    "duration_ms": track_details["duration_ms"],
                    "explicit": track_details.get("explicit", False),
                    "popularity": track_details.get("popularity", "N/A"),
                    "disc_number": track_details.get("disc_number", "N/A"),
                    "release_date": track_details["album"]["release_date"],
                    "preview_url": track_details.get("preview_url", "N/A"),
                    "acousticness": audio_features.get("acousticness", "N/A"),
                    "danceability": audio_features.get("danceability", "N/A"),
                    "energy": audio_features.get("energy", "N/A"),
                    "instrumentalness": audio_features.get("instrumentalness", "N/A"),
                    "key": audio_features.get("key", "N/A"),
                    "liveness": audio_features.get("liveness", "N/A"),
                    "loudness": audio_features.get("loudness", "N/A"),
                    "mode": audio_features.get("mode", "N/A"),
                    "speechiness": audio_features.get("speechiness", "N/A"),
                    "tempo": audio_features.get("tempo", "N/A"),
                    "time_signature": audio_features.get("time_signature", "N/A"),
                    "valence": audio_features.get("valence", "N/A"),
                    # Ajout des nouvelles informations
                    "artist_uri": track_details["artists"][0]["uri"] if track_details["artists"] else "N/A",
                    "album_image_url": track_details["album"]["images"][0]["url"] if track_details["album"]["images"] else "N/A",
                    "album_total_tracks": track_details["album"]["total_tracks"] if track_details["album"] else "N/A",
                }

                all_track_details.append(track_data)

        # Intégration des chansons top tracks
        top_tracks = get_songs_by_artist(token, artist_id, country_code)
        for song in top_tracks:
            song_data = {
                "artist_name": song["artists"][0]["name"] if song["artists"] else "N/A",
                "track_id": song["id"],
                "track_name": song["name"],
                "album_id": song["album"]["id"],
                "album_type": song["album"]["album_type"],
                "album_name": song["album"]["name"],
                "track_number": song.get("track_number", "N/A"),
                "duration_ms": song["duration_ms"],
                "explicit": song.get("explicit", False),
                "genres": song.get("genres", "N/A"),
                "popularity": song.get("popularity", "N/A"),
                "disc_number": song.get("disc_number", "N/A"),
                "isrc": song["external_ids"].get("isrc", "N/A"),
                "release_date": song["album"]["release_date"],
                "preview_url": song.get("preview_url", "N/A"),
                "acousticness": "N/A",  # Si non disponible, laisser vide
                "danceability": "N/A",
                "energy": "N/A",
                "instrumentalness": "N/A",
                "key": "N/A",
                "liveness": "N/A",
                "loudness": "N/A",
                "mode": "N/A",
                "speechiness": "N/A",
                "tempo": "N/A",
                "time_signature": "N/A",
                "valence": "N/A",
                "artist_uri": song["artists"][0]["uri"] if song["artists"] else "N/A",
                "album_image_url": song["album"]["images"][0]["url"] if song["album"]["images"] else "N/A",
                "album_total_tracks": song["album"]["total_tracks"] if song["album"] else "N/A",
            }
            all_track_details.append(song_data)

    else:
        print(f"Artist {artist_name} not found.")

# Création du DataFrame
df = pd.DataFrame(all_track_details)

# Exportation en fichier CSV unique
df.to_csv(f"data/Artists_List_Track_Details.csv", index=False)

print("Unified CSV file with track details and audio features has been created successfully!")
