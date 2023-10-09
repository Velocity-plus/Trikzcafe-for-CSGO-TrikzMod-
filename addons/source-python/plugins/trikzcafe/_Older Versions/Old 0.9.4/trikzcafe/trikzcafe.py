import urllib
import engines.server
import messages
import listeners.tick
import paths
from trikzcafe.tcore.instances import HITBOX
from trikzcafe.tcore.instances import ENTITY
from trikzcafe.tcore.instances import PLAYER
from trikzcafe.tcore.instances import remove_all_hitbox
from trikzcafe.tcore.instances import create_player_hitbox
from .antistuck import *
from .data import *
from .boost import *
from .trikz import *
from .macro import *
from .weapon_drop import *
from time import sleep
from listeners.tick import Delay


def unload():
    remove_all_hitbox()
    SayText2('Plugin Trikz has been unloaded').send()


def load():
    load_hitboxes()
    trikz_thread.start_thread()
    boost_thread.start_thread()
    SayText2('Plugin Trikz has been reloaded').send()
    changeWeaponSpeed()


def load_hitboxes():
    for player in PlayerIter('alive'):
        create_player_hitbox(player)


def changeWeaponSpeed():
    f = open(paths.GAME_PATH + "/scripts/items/items_game.txt", "r")
    data = []
    x = 0
    for line in f:
        if not line.isspace():
            if x > 18332:
                checker = line.strip()
                if checker.startswith('"max player speed"'):
                    line = '         "max player speed"        "250"\n'
            data.append(line)
        x += 1
    f.close()
    fw = open(paths.GAME_PATH + "/scripts/items/items_game.txt", "w")
    content = "".join(data)
    fw.write(content)
    fw.close()
