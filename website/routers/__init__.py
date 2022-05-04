from starlette.config import Config
from authlib.integrations.starlette_client import OAuth

config = Config('../../.env')
oauth = OAuth(config)
CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'

oauth.register(
    name='google',
    server_metadata_url=CONF_URL,
    client_kwargs={
        'scope': 'openid email profile'
    }
)
