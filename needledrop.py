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
from difflib import SequenceMatcher

from urllib.parse import quote


load_dotenv()

auth_manager = SpotifyOAuth(scope='playlist-modify-public ugc-image-upload')
sp = spotipy.Spotify(auth_manager=auth_manager)

user_id = sp.current_user()['id']


def get_videos() -> list[dict]:
    channel_params = {
        'key': os.environ['YOUTUBE_API_KEY'],
        'part': "contentDetails",
        'forUsername': "theneedledrop"
    }
    channel_request = requests.get("https://www.googleapis.com/youtube/v3/channels", params=channel_params).json()
    channel_id = channel_request['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    user_playlists = [playlist['name'] for playlist in sp.user_playlists(user_id)['items']]

    playlist_params = {
        'key': os.environ['YOUTUBE_API_KEY'],
        'part': "snippet",
        'playlistId': channel_id,
        'maxResults': 50
    }

    roundup_videos = list()
    while len(roundup_videos) < 5:
        try:
            playlist_params['pageToken'] = playlist_request['nextPageToken']
        except NameError:
            pass

        playlist_request = requests.get("https://www.googleapis.com/youtube/v3/playlistItems", params=playlist_params).json()

        roundup_videos.extend([video for video in playlist_request['items'] if "Weekly Track Roundup" in str(video['snippet']['title']).split("| ")[-1]])
        # TODO: Do this outside of loop? Just return all results from roundup_videos that match conditional

    return [video for video in roundup_videos if str(video['snippet']['title']).split("| ")[-1] not in user_playlists]


count = 0
def get_track_uri(artist: str, title: str, rerun: bool = False) -> str:
    global count
    if rerun:
        problem_words = ["ft. ", "feat. ", "& ", "(", ")"]

        for word in problem_words:
            if word in title:
                title = title.replace(word, "")
            if word in artist:
                artist = artist.replace(word, "")

    # TODO: Use urllib to create actual query using quote(). Might actually work despite previous testing.
    search = sp.search(q=f'artist:{artist} track:{title}', type='track', market="US", limit=3)
    # search = sp.search(q=quote(f'artist:{artist} track:{title}'), type='track', market="US", limit=3)

    results = search['tracks']['items']

    # Good result
    if len(results) > 0:
        if SequenceMatcher(None, title.lower(), results[0]['name'].lower()).ratio() > 0.7 or results[0]['name'].lower().split()[0] == title.lower().split()[0]:
            return results[0]['uri']
        else:
            print(f"track:{title}   result:{results[0]['name']}")
        
    if rerun:
        # import pdb
        # pdb.set_trace()
        print(count, f"artist:{artist} track:{title}")
        count += 1
        return ""
    
    return get_track_uri(artist, title, rerun=True)
    
    


def get_new_tracks() -> dict[str: list[tuple[str, str, str]]] | None:
    all_videos = get_videos()

    if not all_videos:
        return None

    songs = dict()
    for video in all_videos:

        video_title = str(video['snippet']['title']).split("| ")[-1]

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
                track_uri = get_track_uri(track_artist, title)
                if not track_uri:
                    track_uri = f"NOT FOUND: {track_artist} - {title}"

                # TODO Make this work
                # if track_uri not in [song[2] for song in songs[video_title]]:
                songs[video_title].append((track_artist, title, track_uri))

    return songs


def create_playlists(songs: dict[str: list[tuple[str, str, str]]]) -> list[str]:
    with open("./assets/fantano.jpg", "rb") as img:
        img_64_encode = base64.b64encode(img.read())

    uploaded_playlists = list()
    for video, tracks in songs.items():
        track_uris = list()
        description = "Anthony Fantano's music highlights of the week."
        for track in tracks:
            if "NOT FOUND: " in track[2]:
                if "COULD NOT ADD THE FOLLOWING: " not in description:
                    description += f" COULD NOT ADD THE FOLLOWING: {track[2].split('NOT FOUND: ')[1]}"
                else:
                    description += f" || {track[2].split('NOT FOUND: ')[1]}"
            else:
                track_uris.append(track[2])

        playlist = sp.user_playlist_create(user_id, video, description=description)
        sp.playlist_upload_cover_image(playlist['id'], img_64_encode)

        sp.playlist_add_items(playlist['id'], track_uris)

        uploaded_playlists.append(video)
            
    return uploaded_playlists


if __name__ == "__main__":
    new_tracks = get_new_tracks()
    
    if new_tracks:
        uploaded_playlists = create_playlists(new_tracks)
