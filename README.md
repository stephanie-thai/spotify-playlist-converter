# Spotify Playlist Converter
A python application to convert a Spotify playlist to an M3U file.

## Pre-requisites
- The spotify playlist must be public.
- Music files must be in .mp3 format.
- Your music folder structure must be in the form: Artist/Album/Song OR Artist/Song.
  - Album folder can also be named as 'Artist - Album'.
- Folder names or song title tags must be an exact match to Spotify's naming scheme.

## Setup
If you have an existing Spotify account, you also need to sign up for a Spotify developer account and create an app. Once you have your client id and key, create a `client_info.env` file like the example `client_info.example.env`

## Dependencies
You must have python 3.6+ installed.

The following dependencies are required:
- pip install python-dotenv
- pip install spotipy --upgrade
- pip install mutagen

## Usage
Enter the Spotify playlist link: 
`https://open.spotify.com/playlist/37i9dQZF1DXafCT9DHTijq?si=aa70b201f5704aba`

Enter the absolute path: 
`C:/Users/username/Music/classical`

Your .m3u will be output to the folder your python script is located in.