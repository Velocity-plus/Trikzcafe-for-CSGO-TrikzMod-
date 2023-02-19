# ../change_map/change_map.py

# Source.Python
from commands import CommandReturn
from commands.say import SayCommand
from engines.server import queue_command_string
from engines.sound import Sound
from listeners.tick import Delay
from menus import PagedMenu, PagedOption
from messages import SayText2
from messages.colors.saytext2 import GREEN, ORANGE
from paths import GAME_PATH
from menus import PagedMenu
from menus import PagedOption
from commands import CommandReturn
from commands.say import SayCommand
from commands.client import ClientCommand
from entities.constants import CollisionGroup
from entities.constants import SolidType
from entities.hooks import EntityCondition
from entities.hooks import EntityPreHook
from entities.helpers import index_from_pointer
from events import Event
from listeners.tick import Repeat
from listeners.tick import GameThread
from listeners import OnLevelInit
from messages import SayText2
from messages import HudMsg
from mathlib import NULL_VECTOR
from filters.players import PlayerIter
from filters.entities import EntityIter
from colors import Color
from players.entity import Player
from players.helpers import index_from_userid
from memory import make_object
from weapons.entity import Weapon
from operator import itemgetter
from configobj import ConfigObj


# Time (in seconds) until the map changes.
MAP_CHANGE_DELAY = 3


# Get the path to the server's maps folder.
MAPS_PATH = GAME_PATH / 'maps'
# List for storing maps found within the '../cstrike/maps' folder.
maps = [file.namebase for file in MAPS_PATH.files('*.bsp')]


CHAT_SEND_SOUND = Sound('common/talk.wav', volume=1)
# Separator used for the top and bottom part of the menu.
_menu_separator = '-' * 20

class MapChanger:
    def __init__(self):
        self.index = None
        self.repeater = None
        self.repeater_info = None
        self.thread = None
        self.maps = [file.namebase for file in MAPS_PATH.files('*.bsp')]

    def _info(self):
        for file in MAPS_PATH.files('*.bsp'):
            #SayText2(file.namebase).send()
            if file.namebase not in self.maps:
                SayText2("!! NEW MAP UPLOADED %s !! " % file.namebase).send()
                #CHAT_SEND_SOUND.play()
                SayText2("Changing map in 3 seconds..").send()
                Delay(
                    delay=MAP_CHANGE_DELAY,
                    callback=queue_command_string,
                    args=(f'changelevel {file.namebase}',),
                    cancel_on_level_end=True
                )
                break
        self.maps = [file.namebase for file in MAPS_PATH.files('*.bsp')]

    def repeat_thread(self):
        self.repeater = Repeat(self._info, cancel_on_level_end=True)
        self.repeater.start(1)

    def start_thread(self):
        # Creates the thread
        self.thread = GameThread(target=self.repeat_thread)
        self.thread.daemon = True
        self.thread.start()


mapchanger = MapChanger()

def load():
    SayText2("Testing plugin loaded").send()
    mapchanger.start_thread()

@OnLevelInit
def on_level_init(map_name):
    mapchanger.start_thread()
