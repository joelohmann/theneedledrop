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


load_dotenv()

auth_manager = SpotifyOAuth(scope='playlist-modify-public')
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
        video_title = str(video['snippet']['title'])

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


def get_track_id(track: tuple) -> int:
    artist, title = track
    search = sp.search(q='artist:' + artist + ' track:' + title, type='track', limit=3)
    return search['tracks']['items'][0]['id']


def upload_songs(songs: dict):
    for video, tracks in songs.items():
        for track in tracks:
            get_track_id(track)
            return
    return


if __name__ == "__main__":
    songs = get_songs()
    upload_songs(songs)
