"""
Notes:
- Apple API for his "Fav tracks of 2023" playlist?
    - https://developer.apple.com/documentation/applemusicapi/generating_developer_tokens
    - https://music.apple.com/us/playlist/my-fav-singles-of-2023/pl.u-mJjJTyKgxEy
"""
import requests
import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import base64


load_dotenv()

auth_manager = SpotifyOAuth(scope='playlist-modify-public ugc-image-upload')
sp = spotipy.Spotify(auth_manager=auth_manager)


def get_videos() -> dict:
    channel_params = {
        'key': os.environ['YOUTUBE_API_KEY'],
        'part': "contentDetails",
        'forUsername': "theneedledrop"
    }
    channel_request = requests.get("https://www.googleapis.com/youtube/v3/channels", params=channel_params).json()
    channel_id = channel_request['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    playlist_params = {
        'key': os.environ['YOUTUBE_API_KEY'],
        'part': "snippet",
        'playlistId': channel_id,
        'maxResults': 50
    }
    playlist_request = requests.get("https://www.googleapis.com/youtube/v3/playlistItems", params=playlist_params).json()
    videos = playlist_request['items']

    return videos


def get_songs() -> dict:
    all_videos = get_videos()

    songs = dict()
    for video in all_videos:
        video_title = str(video['snippet']['title']).split("| ")[-1]

        if "Weekly Track Roundup" not in video_title:
            continue

        description = str(video['snippet']['description'])
        description = description.split("BEST TRACKS")[1].split("\n", 1)[1].split("===")[0]
        
        songs[video_title] = list()
        for line in description.split("\n"):
            if "-" not in line or any(check in line for check in ["http", "meh", "WORST TRACKS", "Review:"]):
                continue

            try:
                track_artist, track_title = line.split(" - ", 1)
            except Exception:
                track_artist, track_title = line, ""

            
            for title in track_title.split(" / "):
                songs[video_title].append((track_artist, title))

    return songs


def get_track_uri(track: tuple[str, str]) -> int:
    title_words = ['ft. ', 'feat. ']

    import pdb
    pdb.set_trace()

    artist, title = track
    search = sp.search(q='artist:' + artist + ' track:' + title, type='track', limit=3)

    results = search['tracks']['items']

    if len(results) == 0:
        for word in title_words:
            if word in title:
                title = title.replace(word, '')
        
        search = sp.search(q='artist:' + artist + ' track:' + title, type='track', limit=3)
    return results[0]['uri']
    # If no results stil, need to skip to next and log, or try to search again with different parameters


def upload_songs(songs: dict):   
    user_id = sp.current_user()['id']
    user_playlists = [playlist['name'] for playlist in sp.user_playlists(user_id)['items']]

    with open("./assets/fantano.jpg", "rb") as img:
        img_64_encode = base64.b64encode(img.read())

    for video, tracks in songs.items():
        # if video in user_playlists:
        #     continue
        
        playlist = sp.user_playlist_create(user_id, video, description="Anthony Fantano's music highlights of the week.")

        sp.playlist_upload_cover_image(playlist['id'], img_64_encode)

        for track in tracks:            
            track_uri = get_track_uri(track)
            return
    return


if __name__ == "__main__":
    songs = get_songs()
    upload_songs(songs)
