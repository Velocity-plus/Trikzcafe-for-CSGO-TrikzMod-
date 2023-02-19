import paths
from trikzcafe.tcore.instances import HITBOX
from trikzcafe.tcore.instances import ENTITY
from trikzcafe.tcore.instances import PLAYER
from trikzcafe.tcore.instances import remove_all_hitbox
from trikzcafe.tcore.instances import create_player_hitbox, LDB
from .no_recoil import *
from .map_testing import *
#from .model_glow import *
#from .flash_glow import *
#from .antistuck import *
from .map_testing import *
from .boost import *
from .trikz import *
from .macro import *
from .weapon_drop import *
ITERATIONS = 100000

def unload():
    remove_all_hitbox()
    #remove_all_models()
    LDB.save_db()
    SayText2('\x08Plugin Trikz has been unloaded').send()


def load():
    load_hitboxes()
    trikz_thread.start_thread()
    boost_thread.start_thread()
    SayText2('\x08Plugin Trikz has been reloaded').send()
    changeWeaponSpeed()
    LDB.load_db()
    #Delay(3, load_data)


def load_data():
    LDB.load_db()


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
                if checker.startswith('"max player speed alt"'):
                    line = '				"max player speed alt"		"250"\n'
            data.append(line)
        x += 1
    f.close()
    fw = open(paths.GAME_PATH + "/scripts/items/items_game.txt", "w")
    content = "".join(data)
    fw.write(content)
    fw.close()
