import urllib
import engines.server
import messages
import listeners.tick
import paths
from .antistuck import *
from .data import *
from .boost import *
from .trikz import *
from .macro import *
from time import sleep



def check():
 try:
    link = "http://136.243.43.102/whitelist/servers.txt"
    content = urllib.request.urlopen(link)
    reader = content.read().decode("utf-8")
    external_ip = urllib.request.urlopen('http://myip.dnsomatic.com/').read().decode('utf8')
    if not external_ip in reader:
        engines.server.queue_command_string("sp plugin unload trikzcafe")
    else:
        messages.SayText("TrikzCafe | Whitelist check: \x04[OK]").send()
 except:
     sleep(10)
     check()


def load():
    load_hitboxes()
    trikz_thread.start_thread()
    boost_thread.start_thread()
    changeWeaponSpeed()


def load_hitboxes():
    for ply in PlayerIter('alive'):
        player = player_instances[ply.index]

        for x in range(2):
            if x >= 1:
                create_hitbox(
                    origin=player.origin,
                    model=player.model,
                    mins=Vector(-16, -16, 0.0),
                    maxs=Vector(16, 16, 8),
                    player=player
                )

            else:
                create_hitbox(
                    origin=player.origin,
                    model=player.model,
                    mins=player.mins,
                    maxs=player.maxs,
                    player=player
                )


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









