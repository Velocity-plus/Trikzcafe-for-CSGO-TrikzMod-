from events import Event
from entities.helpers import index_from_pointer
from messages import SayText2
from players.helpers import index_from_userid
import active_menus
from entities.constants import SolidType, SolidFlags, EntityEffects, CollisionGroup, EntityFlags, RenderMode, \
    RenderEffects
from entities.dictionary import EntityDictionary
import memory
from memory import Convention
from memory import DataType
from entities.hooks import EntityCondition, EntityPreHook, EntityPostHook
from memory.manager import TypeManager
from path import Path
from listeners import OnEntitySpawned, OnLevelInit, OnLevelEnd, OnEntityOutput, OnEntityDeleted, OnClientPutInServer, OnClientDisconnect
from entities.entity import Entity
from players.entity import Player
from entities.entity import BaseEntity
from filters.entities import EntityIter
from filters.players import PlayerIter
from .tcore.instances import PLAYER, HITBOX
from listeners.tick import Delay



crash_entities = ('env_fire',
                  '_firesmoke',
                  'env_laser',
                  'func_rotating',
                  'env_spritetrail',
                  'point_spotlight')

entities_to_log = {"func_door",
                   "func_wall_toggle",
                   "func_breakable",
                   "func_door",
                   "func_button",
                   "func_brush",
                   "func_door_rotating",
                   "func_tanktrain",
                   "trigger_teleport"}

normal_ui = {"ai_hint",
             "ai_network",
             "cs_gamerules",
             "cs_player_manager",
             "cs_team_manager",
             "env_cascade_light",
             "env_fog_controller",
             "env_soundscape",
             "env_soundscape_proxy",
             "env_soundscape_triggerable",
             "env_spritetrail",
             "env_wind",
             "func_breakable",
             "func_brush",
             "func_button",
             "func_buyzone",
             "func_door",
             "func_illusionary",
             "func_movelinear",
             "func_rotating",
             "func_tanktrainenv_sun",
             "func_wall",
             "func_wall_toggle",
             "hl2mp_gamerules",
             "info_ladder",
             "info_map_parameters",
             "info_node",
             "info_node_hint",
             "info_player_combine",
             "info_player_deathmatch",
             "info_player_rebel",
             "info_projecteddecal",
             "info_target",
             "infodecal",
             "keyframe_rope",
             "logic_auto",
             "move_rope",
             "player",
             "player_manager",
             "point_devshot_camera",
             "point_viewcontrol",
             "predicted_viewmodel",
             "scene_manager",
             "shadow_control",
             "sky_camera",
             "soundent",
             "team_manager",
             "trigger_soundscape",
             "viewmodel",
             "vote_controller",
             "water_lod_control",
             "weapon_knife",
             "weaponworldmodel",
             "worldspawn"}

@OnLevelEnd
def on_level_end():
    # Remove all custom bounding boxes when changing map
    address_players.clear()
    address_players_entity.clear()
    address_entities_entity.clear()
    address_entities.clear()


@OnEntitySpawned
def on_entity_spawned(base_entity):
    classname = base_entity.classname
    if classname in entities_to_log or "projectile" in classname:
        index = base_entity.index
        entity = Entity(index)
        address = entity.pointer.address
        address_entities.add(address)
        address_entities_entity[address] = entity


@OnEntityDeleted
def on_entity_deleted(base_entity):
    address = base_entity.pointer.address
    if address in address_entities:
        address_entities.remove(address)
        del address_entities_entity[address]


@OnClientDisconnect
def on_client_disconnect(index):
    address = BaseEntity(index).pointer.address
    if address in address_players:
        address_players.remove(address)
        del address_players_entity[address]


address_entities = set()
address_entities_entity = {}
address_players = set()
address_players_entity = {}
address_hitbox = set()
address_hitbox_entity = {}


def cast_address(address):
    if address in address_entities:
        return address_entities_entity[address]

    if address in address_players:
        return address_players_entity[address]

    if address in address_hitbox:
        return address_hitbox_entity[address]

    return False

for classname in entities_to_log:
    for entity in EntityIter(classname, exact_match=True):
        address = entity.pointer.address
        address_entities.add(address)
        address_entities_entity[address] = entity


def addplayers():
    for player in PLAYER.values():
        SayText2(player.name).send()
        address = player.pointer.address
        if address not in address_players:
            address_players.add(address)
            address_players_entity[address] = player
        for hitbox in player.hitbox_prop.values():
            address = hitbox.pointer.address
            if address not in address_hitbox:
                address_hitbox.add(address)
                address_hitbox_entity[address] = hitbox

    SayText2("\x09 Entity memory addresses: \x02 %s\n\x09Player memory addresses: \x02 %s \n \x09 Hitbox memory addresses:\x02 %s"  % (len(address_entities), len(address_players), len(address_hitbox))).send()


Delay(3, addplayers)
