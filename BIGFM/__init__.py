from BIGFM.core.bot import Aviax
from BIGFM.core.dir import dirr
from BIGFM.core.git import git
from BIGFM.core.userbot import Userbot
from BIGFM.misc import dbb, heroku

from .logging import LOGGER

dirr()
git()
dbb()
heroku()

app = Aviax()
userbot = Userbot()


from .platforms import *

Apple = AppleAPI()
Carbon = CarbonAPI()
SoundCloud = SoundAPI()
Spotify = SpotifyAPI()
Resso = RessoAPI()
Telegram = TeleAPI()
YouTube = YouTubeAPI()
