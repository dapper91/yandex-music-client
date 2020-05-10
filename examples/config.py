"""
Service login example.
"""

import configparser
import getpass
import pathlib
import sys

from yamusic import exceptions, YaMusicClient, OAuthCred

config = configparser.ConfigParser()
config_file = pathlib.Path.home() / '.yamusic'

try:
    if config_file.exists():
        config.read(config_file)
        username = config['OAUTH']['username']
        access_token = config['OAUTH']['access_token']
        user_id = config['OAUTH']['user_id']

        ym_client = YaMusicClient(username, oauth_cred=OAuthCred(access_token, user_id))
    else:
        username = getpass.getuser()
        username = input(f"Login ({username}): ") or username
        password = getpass.getpass("Password: ")

        ym_client = YaMusicClient(username, password)

        config['OAUTH'] = {
            'username': username,
            'access_token': ym_client.oauth_cred.access_token,
            'user_id': ym_client.oauth_cred.user_id,
        }

        with config_file.open('w') as fp:
            config.write(fp)

except exceptions.AuthenticationError:
    print("Authentication error: username or password is incorrect")
    sys.exit(1)


print("User's playlists:")
for playlist in ym_client.get_playlists():
    print("{title} ({track_count})".format(
        title=playlist.title,
        track_count=playlist.track_count)
    )
