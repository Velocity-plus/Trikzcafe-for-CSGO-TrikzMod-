from mathlib import Vector, QAngle, NULL_VECTOR
from math import sqrt, pow
from decimal import Decimal
from events import Event
from entities.entity import BaseEntity
from players.entity import Player
from entities.entity import Entity
from entities.helpers import index_from_pointer
from entities.hooks import EntityPreHook
from entities.hooks import EntityPostHook
from entities.hooks import EntityCondition
from entities.constants import SolidType
from entities.constants import EntityEffects
from entities.dictionary import EntityDictionary
from entities.constants import CollisionGroup
from entities import TakeDamageInfo
from entities.constants import EntityStates
from players.constants import PlayerStates
from listeners import OnEntitySpawned, OnEntityDeleted
from engines.server import server
from memory.hooks import PreHook
from listeners import OnLevelEnd
from listeners import OnLevelInit
from listeners.tick import Repeat
from listeners.tick import GameThread
from listeners.tick import RepeatStatus
from listeners import OnTick
from memory import make_object
from memory import find_binary
from messages import SayText2, SayText
from messages import HintText
from engines.sound import Attenuation
from engines.sound import Sound
from core import echo_console
from engines.precache import Model
from players import UserCmd
from players.constants import PlayerButtons
from players.helpers import index_from_userid
from time import time
from configobj import ConfigObj
import random
import string
from .tlisteners.grenadetouch import OnPlayerGrenadeTouchUnder
from .tlisteners.grenadetouch import OnPlayerGrenadeTouch
from .tlisteners.playertouch import OnPlayerOnTop
from .tlisteners.playertouch import OnPlayerSky
from trikzcafe.tcore.instances import HITBOX
from trikzcafe.tcore.instances import ENTITY
from trikzcafe.tcore.instances import PLAYER
from trikzcafe.tcore.instances import ENTITY_FROM_ADDRESS
from trikzcafe.tcore.instances import HITBOX_FROM_ADDRESS
from trikzcafe.tcore.instances import shared_path
from trikzcafe.tcore.instances import remove_hitbox_from_player
from trikzcafe.tcore.instances import create_player_hitbox
from entities.hooks import EntityCondition
from entities.hooks import EntityPreHook
from core import PLATFORM
from core import SOURCE_ENGINE
from memory import Convention, DataType
from cvars import ConVar
from engines.trace import ContentMasks, ContentFlags, SurfaceFlags
from engines.trace import GameTrace, TraceType
from engines.trace import Ray
from engines.trace import TraceFilterSimple
from engines.trace import engine_trace
from listeners import OnPlayerRunCommand
from mathlib import Vector
from engines.precache import Model
from engines.server import engine_server
from commands.say import SayCommand
from menus import PagedMenu
from menus import PagedOption
import active_menus
from engines.server import server, queue_command_string
from paths import ADDONS_PATH
import datetime


stripper_path = ADDONS_PATH + '/stripper/maps/'
@SayCommand(['!modmap'])
def change_model(say, index, team_only=None):
    player = PLAYER[index]
    if player.check_auth(['Peace']):
        if not player.mod_map:
            player.mod_map = True
            SayText2("\x02Map modifier toggled, menu will appear when you touch triggers!").send(player.index)
        else:
            player.mod_map = False
            SayText2("\x02Map modifier disabled!").send(player.index)

@SayCommand(['!a', '/a'])
def find_trigger(say, index, team_only=None):
    '''
    Called whenever a player says something.
    '''
    player = PLAYER[index]
    origin = player.origin

    destination = Vector(origin.x, origin.y, origin.z) + (player.view_vector * 1000)
    SayText2(str(player.view_vector)).send()
    #player.teleport(destination, None, None)
    trace = GameTrace()

    filters = (player,) + tuple([hit for hit in player.hitbox_prop.values()] + [hit for hit in player.glow_prop.values()])

    engine_trace.trace_ray(
        Ray(origin, destination, Vector(-2,-2, 0), Vector(2,2,2)),
        ContentMasks.ALL,
        TraceFilterSimple((filters), TraceType.EVERYTHING),
        trace,
    )

    is_surfing = False

    if trace.did_hit():
        SayText2(str(trace.entity.classname)).send()
        # Sometimes I'm getting 0.00048828125, mostly 0.0
        destination_distance = trace.end_position.get_distance(origin)
        # SayText2(str(trace.plane.normal.z)).send()
        if (destination_distance <= 1 and trace.plane.normal.z >= 0.7 and trace.plane.normal.z < 1.0):
            is_surfing = True



@EntityPreHook(EntityCondition.equals_entity_classname('trigger_teleport'), 'touch')
def touch_trigger_multiple(args):
    index2 = index_from_pointer(args[0])
    index1 = index_from_pointer(args[1])

    if index1 not in PLAYER:
        return

    if index2 in PLAYER:
        return
    entity = ENTITY[index2]
    player = PLAYER[index1]
    if not player.mod_map and not player.is_dead:
        return

    return False


@EntityPreHook(EntityCondition.equals_entity_classname('trigger_multiple'), 'start_touch')
@EntityPreHook(EntityCondition.equals_entity_classname('trigger_teleport'), 'start_touch')
def touch_trigger_multiple(args):
    index2 = index_from_pointer(args[0])
    index1 = index_from_pointer(args[1])

    if index1 not in PLAYER:
        return

    if index2 in PLAYER:
        return

    entity = ENTITY[index2]
    player = PLAYER[index1]
    if not player.mod_map:
        return

    player.current_trigger = entity
    send.map_fix(player.index)



from menus.base import Text

class Menus:
    def __init__(self):
        self.menu = None

    def map_fix(self, index):
        player = PLAYER[index]
        steamid = player.steamid
        adjusted =  player.current_trigger.origin - player.current_trigger.first_origin
        adjusted_str = "Adjusted X: %s Y: %s Z: %s" % (round(adjusted.x,1), round(adjusted.y,1), round(adjusted.z,1))
        cx, cy, cz = player.current_trigger.first_origin
        original_pos = "Default: X: %s Y: %s Z: %s" % (round(cx,1),round(cy,1),round(cz,1))
        self.menu = PagedMenu(
            title='ModMap => ID %s' % player.current_trigger.hammerid,
            top_separator=("Trigger: %s\n%s\n%s\nName: '%s'\nTarget: '%s'" % (player.current_trigger.classname,
                                                        original_pos,
                                                        adjusted_str,
                                                        player.current_trigger.global_name,
                                                        player.current_trigger.target_name)),
            bottom_separator=' ',
            select_callback=self.map_fix_callback
        )
        self.menu.append(PagedOption('Z: + 1', 'z+'))
        self.menu.append(PagedOption('Z: -  1', 'z-'))
        self.menu.append(PagedOption('Y: + 1', 'y+'))
        self.menu.append(PagedOption('Y: -  1', 'y-'))
        self.menu.append(PagedOption('X: + 1', 'x+'))
        self.menu.append(PagedOption('X: -  1', 'x-'))
        self.menu.append(PagedOption('Save current trigger', "save"))
        self.menu.append(PagedOption('Generate empty map cfg', "generate"))
        self.menu.append(PagedOption('Show triggers', "trigger"))
        self.menu.append(PagedOption('Reset Trigger', "reset"))
        self.menu.append(PagedOption('Perm delete trigger', "delete"))
        self.menu.send(index)
        active_menus.am.addMenu(index, self.menu)

    def map_fix_callback(self, menu, index, option):
        player = PLAYER[index]
        steamid = player.steamid
        torigin = player.current_trigger.origin
        if option.value == "z+":
            torigin.z += 1
            player.current_trigger.teleport(torigin, None, None)

        if option.value == "z-":
            torigin.z -= 1
            player.current_trigger.teleport(torigin, None, None)

        if option.value == "y+":
            torigin.y += 1
            player.current_trigger.teleport(torigin, None, None)

        if option.value == "y-":
            torigin.y -= 1
            player.current_trigger.teleport(torigin, None, None)

        if option.value == "x+":
            torigin.x += 1
            player.current_trigger.teleport(torigin, None, None)

        if option.value == "x-":
            torigin.x -= 1
            player.current_trigger.teleport(torigin, None, None)

        if option.value == "reset":
            player.current_trigger.teleport(player.current_trigger.first_origin, None, None)
            SayText2("\x06Trigger has been resetted").send(player.index)

        if option.value == "trigger":
            queue_command_string("showtriggers_toggle")
            SayText2("\x06Trigger toggle").send(player.index)

        if option.value == "generate":
            f = open(stripper_path+server.map_name+".cfg", "a")
            f.write("")
            f.close()
            SayText2("\x06Empty CFG has been created for map: %s!!!" % server.map_name).send(player.index)

        if option.value == "save":
            ox, oy, oz  = roundAndFormat(player.current_trigger.first_origin)

            ax, ay, az =  roundAndFormat(player.current_trigger.origin)
            tname = player.current_trigger.classname
            text = \
"""
; PLUGIN MODIFICATION BY %s
;ID %s TIME: %s
modify:
{
    match:
    {
    "hammerid" "%s"
    "classname" "%s"
    }

    replace:
    {
    "origin" "%s %s %s"
    }
}
""" % (player.name, player.current_trigger.hammerid, datetime.datetime.now(), player.current_trigger.hammerid, tname, ax, ay,az)
            f = open(stripper_path+server.map_name+".cfg", "a")
            f.write(text)
            f.close()
            SayText2("\x02!!!SETTINGS SAVED for map: %s!!! \x06 Please reload map to check if it saved succesfully!" % server.map_name).send(player.index)
        if option.value != "delete":
            send.map_fix(player.index)

        if option.value == "delete":
            if player.confirm_delete < 3:
                player.confirm_delete += 1
                SayText2('!! Please press the button a few times to confirm %s/3' % player.confirm_delete).send(player.index)
                send.map_fix(player.index)
            else:
                player.confirm_delete = 0
                ox, oy, oz  = roundAndFormat(player.current_trigger.first_origin)

                tname = player.current_trigger.classname
                text = \
"""
; PLUGIN MODIFICATION BY %s
;ID %s TIME: %s
remove:
{
    "hammerid" "%s"
    "classname" "%s"
}
    """ % (player.name, player.current_trigger.hammerid, datetime.datetime.now(), player.current_trigger.hammerid, tname)
                f = open(stripper_path+server.map_name+".cfg", "a")
                f.write(text)
                f.close()
                SayText2("\x02!!!TRIGGER DELETED for map: %s!!! \x06 Please reload map to check if it saved succesfully!" % server.map_name).send(player.index)
                player.current_trigger.remove()

send = Menus()


def roundAndFormat(origin):
    ox, oy, oz = origin
    ox = round(ox, 1)
    oy = round(oy, 1)
    oz = round(oz, 1)
    if ox == int(ox):
        ox = int(ox)
    if oy == int(oy):
        oy = int(oy)
    if oz == int(oz):
        oz = int(oz)
    return ox, oy, oz