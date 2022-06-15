import os
import glob
from pathlib import Path

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import dotenv_values

from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

# Read client details from .env file
ENV_DIRECTORY = "{}\client_info.env".format(Path().absolute())
config = dotenv_values(ENV_DIRECTORY)

cid = config["SPOTIPY_CLIENT_ID"]
secret = config["SPOTIPY_CLIENT_SECRET"]

# Spotipy Client Credentials Flow
auth_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
sp = spotipy.Spotify(auth_manager=auth_manager)

def get_album_folder(artist_folder, artist_name, album_name):
    """ Get album folder path from format 'album' or 'artist - album' """
    album_folder = artist_folder / album_name
    # combined artist - album name
    artist_alb_name = artist_name + ' - ' + album_name
    artist_album_folder = artist_folder / artist_alb_name

    # Check album folder exists
    song_parent_folder = None
    if os.path.isdir(album_folder):
        song_parent_folder = album_folder
    elif os.path.isdir(artist_album_folder):
        song_parent_folder = artist_album_folder

    return song_parent_folder

def song_dir_search(folder_path, track_name):
    """
        Linear search for song in the album or artist folder based on the ID3
        track title tag for .mp3 files
    """
    filenames = glob.glob(folder_path + "/*.mp3")
    track_info = None
    new_path = None
    for song_file in filenames:
        audio = EasyID3(song_file)
        if "artist" not in audio or "title" not in audio:
            continue

        if track_name == audio["title"][0]:
            song_length = None
            if "length" not in audio:
                audio_MP3 = MP3(song_file)
                song_length = round(audio_MP3.info.length * 1000)
            else:
                song_length = audio["length"][0]

            track_info = "#EXTINF:{},{} - {}".format(song_length, audio["artist"][0], audio["title"][0])
            new_path = song_file.replace(os.sep, '/')

            break
    return track_info, new_path

def song_dict_search(track_list, track_name, artist_name):
    """ Search for a song from a list of track dictionaries """
    track_info = None
    new_path = None
    for track_dict in track_list:
        if track_name == track_dict["title"]:
            track_info = "#EXTINF:{},{} - {}".format(track_dict["length"], artist_name, track_name)
            new_path = track_dict["location"].replace(os.sep, '/')
            break
    return track_info, new_path

def create_m3u(playlist_name, m3u_lines):
    """ Create the final m3u file """
    if len(m3u_lines) == 1:
        return
    # join m3u data with new line
    playlist_output = '\n'.join([line for line in m3u_lines])

    m3u_file_name = playlist_name + ".m3u"
    with open(m3u_file_name, 'w', encoding="utf-8") as out_file:
        out_file.write(playlist_output)

def construct_artist_song_dict(search_dir):
    """
        Create a dictionary where artist is the key and the value is a list of dictionaries
        for the artist's songs and other song information
    """
    filenames = glob.glob(str(search_dir) + "/*.mp3")

    # Artist is a unique key
    artist_song_dict = {}
    # directory is empty of music files
    if not filenames:
        return artist_song_dict

    # Linear search for the track
    for song_file in filenames:
        audio = EasyID3(song_file)
        if "artist" not in audio or "title" not in audio:
            continue
        song_length = None
        if "length" not in audio:
            audio_MP3 = MP3(song_file)
            song_length = round(audio_MP3.info.length * 1000)
        else:
            song_length = audio["length"][0]

        track_dict = {
            "title": audio["title"][0],
            "length": song_length,
            "location": song_file
        }
        # artist key already exists
        if audio["artist"][0] in artist_song_dict:
            song_list = artist_song_dict[audio["artist"][0]]
            # append track and location to songs list
            song_list.append(track_dict)
        else: 
            # insert new artist and track
            artist_pair = {
                audio["artist"][0]: [ track_dict ],
            }
            artist_song_dict.update(artist_pair)
    return artist_song_dict

def convert_playlist(playlist_link, root_search_dir):
    """
        Create m3u file from a Spotify playlist link and
        search matching music files from a local root folder
    """
    # Call spotify web api
    playlist_URI = playlist_link.split("/")[-1].split("?")[0]
    try:
        # get playlist tracks
        spotify_tracks = sp.playlist_tracks(playlist_URI)["items"]
    except spotipy.exceptions.SpotifyException as e:
        print("Error: Playlist link inaccessible")
        return
    # get playlist name
    playlist_name = sp.user_playlist(user=None, playlist_id=playlist_URI, fields="name")["name"]

    # absolute local pathname
    root_search_dir = Path(root_search_dir)
    m3u_lines = ["#EXTM3U"]

    fail_output = "The following tracks could not be found: \n"

    # Construct hash table of mp3 files in the root directory excluding sub folders
    artist_song_dict = construct_artist_song_dict(root_search_dir)

    index = 0
    for track in spotify_tracks:
        index += 1
        artist_name = track["track"]["artists"][0]["name"]
        track_name = track["track"]["name"]
        album_name = track["track"]["album"]["name"]

        # Check Artist folder exists
        artist_folder = root_search_dir / artist_name
        if not os.path.isdir(artist_folder):
            # Else search hash table of root folder
            if artist_name in artist_song_dict:
                track_list = artist_song_dict[artist_name]
                track_info, new_path = song_dict_search(track_list, track_name, artist_name)
                if track_info:
                    m3u_lines.append(track_info)
                    m3u_lines.append(new_path)
                else:
                    fail_output += "{} - {}\n".format(str(index), track_name)
            else:
                fail_output += "{} - {}\n".format(str(index), track_name)
            continue

        album_folder = get_album_folder(artist_folder, artist_name, album_name)
        # Album folder does not exist
        if not album_folder:
            # Else search in Artist directory
            track_info, new_path = song_dir_search(str(artist_folder), track_name)
            if track_info:
                m3u_lines.append(track_info)
                m3u_lines.append(new_path)
            else:
                fail_output += "{} - {}\n".format(str(index), track_name)
            continue

        # Search in Album directory
        track_info, new_path = song_dir_search(str(album_folder), track_name)
        if track_info:
            m3u_lines.append(track_info)
            m3u_lines.append(new_path)
        else:
            fail_output += "{} - {}\n".format(str(index), track_name)

    create_m3u(playlist_name, m3u_lines)

    print(fail_output)

if __name__ == "__main__":
    spotify_link = input('Enter Spotify playlist link: ')
    root_path = input('Enter the path to your songs folder: ')
    print('\n')

    convert_playlist(spotify_link, root_path)
