from events import Event
from entities.helpers import index_from_pointer
from messages import SayText2
from players.helpers import index_from_userid
import active_menus
from entities.constants import SolidType, SolidFlags, EntityEffects, CollisionGroup, EntityFlags, RenderMode, \
    RenderEffects
from .data import player_instances
from entities.dictionary import EntityDictionary
import memory
from memory import Convention
from memory import DataType
from entities.hooks import EntityCondition, EntityPreHook, EntityPostHook
from memory.manager import TypeManager
from path import Path
from listeners import OnEntitySpawned, OnLevelInit, OnLevelEnd, OnEntityOutput, OnEntityPreSpawned, OnEntityDeleted, \
    OnClientFullyConnect, OnClientDisconnect
from entities.entity import Entity
from entities.constants import EntityEffects
from entities import CheckTransmitInfo
from entities.entity import BaseEntity
from memory import make_object
from memory.hooks import PreHook
from memory import Function
from entities.helpers import index_from_edict
from memory.hooks import HookType
from memory import get_virtual_function
from time import time
from commands.say import SayCommand
from .region_address import cast_address

# This is used to get the offset from a custom data file. This way you don't
# have to add the offset to the SP data file after every update.
manager = TypeManager()
CBaseEntity = manager.create_type_from_file('CBaseEntity', Path(__file__).parent / 'CBaseEntity.ini')

server = memory.find_binary('server', srv_check=False)

PassServerEntityFilter = server[b'\x55\xB8\x01\x00\x00\x00\x89\xE5\x83\xEC\x38\x89\x5D\xF4'].make_function(
    Convention.CDECL,
    [DataType.POINTER, DataType.POINTER],
    DataType.BOOL
)


def realm_get_players(realm):
    players = []
    for player in player_instances.values():
        if player.realm == realm:
            players.append(player.index)
    return players


from effects import box
from filters.recipients import RecipientFilter
from engines.precache import Model
from events import Event
from players.entity import Player

model = Model('sprites/laser.vmt')


def drawbox(origin, size, time):
    box(
        RecipientFilter(),
        origin,
        size,
        alpha=255,
        blue=0,
        green=0,
        red=255,
        amplitude=0,
        end_width=1,
        life_time=time,
        start_width=1,
        fade_length=0,
        flags=0,
        frame_rate=255,
        halo=model,
        model=model,
        start_frame=0
    )


def create_player_glow(entity, color):
    player_model = entity

    # turn the glow on
    player_model.set_property_bool('m_bShouldGlow', True)

    # set the glow color
    # gotta use long color codes for this one
    # http://www.pbdr.com/pbtips/ps/rgblong.htm
    player_model.set_property_int('m_clrGlow', rgb_to_long(color[0], color[1], color[2]))

    # set the distance from which you can see the glow
    # NOTE: without this, the glow won't show
    player_model.set_property_float('m_flGlowMaxDist', 1000000.0)


# =============================================================================
# >> UTIL
# =============================================================================
def rgb_to_long(r, g, b):
    return b * 65536 + g * 256 + r


class LevelHandler(Entity):
    def __init__(self, index):
        super().__init__(index)
        # Instance of the 'trigger_multiple' used for the custom bounding box.
        self.finished = []
        self.cooldown = False
        self.has_pointer = False
        self.trigger_once = False

    def add_player(self, indexs, timer=True):
        if isinstance(indexs, int):
            if indexs not in self.finished:
                self.finished.append(indexs)
                if timer:
                    self.delay(self.cooldown, self.remove_player, args=(indexs,), cancel_on_level_end=True)
            else:
                self.notify_already_open(indexs)
                return False

        else:
            for object in indexs:
                if object not in self.finished:
                    self.finished.append(object)
                    if timer:
                        self.delay(self.cooldown, self.remove_player, args=(object,), cancel_on_level_end=True)
                else:
                    self.notify_already_open(object)
                    break

    def remove_player(self, indexs):
        if isinstance(indexs, int):
            player = player_instances[indexs]
            if player:
                for object in realm_get_players(player.realm):
                    if object in self.finished:
                        self.finished.remove(object)

        else:
            for object in indexs:
                if object in self.finished:
                    self.finished.remove(object)

    def notify_already_open(self, indexs):
        if not self.cooldown:
            player = player_instances[indexs]
            for object in realm_get_players(player.realm):
                if object in self.finished:
                    self.finished.remove(object)


def reset_buttons():
    for ent in button_instances.values():
        ent.set_property_float('m_flWait', func_properties[ent.index]['cooldown'])


class ButtonHandler(Entity):
    def __init__(self, index):
        super().__init__(index)
        # Instance of the 'trigger_multiple' used for the custom bounding box.
        self.finished = []
        if self.index in func_properties:
            self.cooldown = func_properties[self.index]['cooldown']
        else:
            self.cooldown = 6.5
        self.is_pointer = False
        self.trigger_once = False


level_instances = EntityDictionary(LevelHandler)
button_instances = EntityDictionary(ButtonHandler)

from filters.entities import EntityIter

for entity in EntityIter("func_button", exact_match=True):
    entity.set_property_float("m_flWait", 0)

test_entities = set()


@PreHook(PassServerEntityFilter)
def _pre_pass_server_entity_filter(args):
    try:
        base_entity1 = cast_address(args[1].address)

        if not base_entity1:
            return

        index1 = base_entity1.index

    except AttributeError:
        return

    try:
        base_entity0 = cast_address(args[0].address)
        if not base_entity0:
            return

        index0 = base_entity0.index

        if index0 == index1:
            return

    except AttributeError:
        return

    #SayText2(str(base_entity1.classname) + " | " + str(base_entity0.classname)).send()
    if base_entity1.classname == "flashbang_projectile":
        owner_index = Entity(base_entity1.index).owner.index
        if base_entity0.is_player():
            player = player_instances[owner_index]
            other = player_instances[index0]
            if player.realm != other.realm:
                return False

            return

        level = level_instances[index0]
        if owner_index in level.finished:
            return func_properties[index0]['collision']

        if index0 in func_properties:
            return func_properties[index0]['default']

        return

    if base_entity0.is_player() and base_entity1.is_player():

        player = player_instances[index0]
        other = player_instances[index1]
        if player.realm == other.realm:
            return True

        return False

    if not base_entity1.is_player():
        return

    if index0 not in func_properties:
        return
    player = player_instances[index1]
    level = level_instances[index0]

    if player.index in level.finished:
        return func_properties[index0]['collision']
    return func_properties[index0]['default']


tracked_inputs = ('Break', 'Toggle', 'Open', 'Enable', 'Disable')
tracked_triggers = ('func_button', 'trigger_multiple')


@EntityPreHook(EntityCondition.is_player, "accept_input")
def pre_accept_input(stack_data):
    input_name = stack_data[1]
    # Don't go further if this isn't an input we're tracking.
    if input_name not in tracked_inputs:
        return

    try:
        activator = make_object(BaseEntity, stack_data[2])
        if not activator.is_player:
            return
    except ValueError:
        return

    # Get the BaseEntity on which the input was called.
    # (func_door, func_breakable, func_wall_toggle, etc.)
    base_entity = make_object(Entity, stack_data[0])
    player = player_instances[activator.index]

    if player.is_dead:
        return

    level = level_instances[base_entity.index]

    timer = True
    special_conditions = False
    button_entity = make_object(Entity, stack_data[3])

    if level.classname == "trigger_push":
        return

    if level.classname == "trigger_multiple":
        for action in level.get_output("OnStartTouch").event_actions:
            #SayText2("%s Target: %s %s" % (action.target, action.target_input, action.parameter)).send()
            if action.target_input == "AddOutput" and action.target:
                # SayText2("Special Conditions apply to this level").send()
                special_conditions = True


    #SayText2("Level: %s" % level.classname).send()
    delay = 0

    if button_entity:

        if button_entity.classname == "trigger_push":
            return

        if button_entity.classname == 'trigger_multiple' or button_entity.classname == "trigger_once":

            if button_entity.classname == "trigger_once":
                level.trigger_once = True

            delay = 0

            for action in button_entity.get_output("OnStartTouch").event_actions:
                #SayText2("Target: %s" % action.target_input).send()
                if action.target_input == "AddOutput" and action.target:
                    # SayText2("Special Conditions apply to this level").send()
                    special_conditions = True

                if action.delay != 0:
                    delay = action.delay

                if delay <= 2.0:
                    delay = 0

            if level.cooldown == False:
                level.cooldown = delay
                if delay <= 0:
                    timer = False

            #SayText2("Level: %s | Button: %s | Delay: %s, Timer: %s" % (level.classname, button_entity.classname, delay, timer)).send()

        else:
            button = button_instances[button_entity.index]
            if button.classname == 'func_button':
                delay = 0
                for action in button.get_output("OnPressed").event_actions:
                    if action.delay != 0:
                        if action.delay >= delay:
                            delay = action.delay

                if delay > 0:
                    if not level.cooldown:
                        level.cooldown = delay
                else:
                    if not level.cooldown:
                        level.cooldown = button.cooldown
                        delay = button.cooldown

                #SayText2("Level: %s | Button: %s | Delay: %s, Timer: %s" % (level.classname, button_entity.classname, delay, timer)).send()

            if button.cooldown == -1:
                return

        level.add_player(realm_get_players(player.realm), timer=timer)

        if level.classname == 'trigger_teleport':
            return

    # SayText2('After: %s' % level.classname).send()

    if special_conditions:
        SayText2("Special %s" % special_conditions).send()
        return

    return False


is_teleport = EntityCondition.equals_entity_classname('trigger_teleport')


@EntityPreHook(is_teleport, 'touch')
def pre_touch_teleport(stack_data):
    if crash_handler['safe']:
        base_entity = make_object(BaseEntity, stack_data[0])
        if 'trigger_teleport' == base_entity.classname:
            activator = make_object(BaseEntity, stack_data[1])
            if not activator.is_player():
                return

            player = player_instances[activator.index]
            if player.is_dead:
                return

            try:
                level = level_instances[base_entity.index]
                if player.index in level.finished or func_properties[level.index]['default']:
                    return
            except:
                return

            return False


"""
Entity_Outputs = ("trigger_multiple")
@OnEntityOutput
def on_entity_output(output, activator, caller, value, delay):
    # Don't go further if the entity output isn't OnStartTouch.
    if caller.classname not in Entity_Outputs:
        return

    if not activator.is_player():
        return

    player = player_instances[activator.index]

    if caller.classname == "trigger_multiple":
        SayText2("%s" % output).send()
"""

# We can use the worldspawn entity, because it's using
# CBaseEntity::SetTransmit just like all triggers

global_tick = {'tick': 100, 'entity': None}
crash_handler = {'safe': True}


@SayCommand(['!a', '/a'])
def giveWeaponText(say, index, team_only=None):
    '''
    Called whenever a player says something.
    '''
    player = player_instances[index]
    entity = player.get_view_entity()
    SayText2(str(entity.classname)).send()
    SayText2(str(entity.get_property_bool('m_bDisabled'))).send()


def server_respond(entity):
    print('------ CRASHED REPORT ----------')
    print(entity.classname)
    print(entity.global_name)
    print(entity.target_name)


crash_entities = ('env_fire',
                  '_firesmoke',
                  'env_laser',
                  'func_rotating',
                  'env_spritetrail',
                  'point_spotlight')

ENTITIES = {"func_door",
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


def crash_exceptions(classname):
    if classname not in normal_ui and "projectile" not in classname and "weapon" not in classname and classname not in ENTITIES:
        return True
    return False


def transmit_filter(entity, player, classname, ent_index):
    level = level_instances[ent_index]
    if level.trigger_once:
        level.add_player(realm_get_players(player.realm), timer=False)

    if player.index in level.finished:
        return func_properties[ent_index]['toggle']

    return func_properties[ent_index]['default']


@PreHook(Entity(0).set_transmit)
def pre_set_transmit_player(args):
    entity = BaseEntity._obj(args[0])
    entity_classname = entity.classname

    if crash_exceptions(entity_classname) or entity_classname in crash_entities:
        return True
    if not crash_handler['safe']:
        return

    entity_index = entity.index
    # For projectiles
    if "projectile" in entity_classname:
        edict = CheckTransmitInfo._obj(args[1]).client

        player = player_instances[index_from_edict(edict)]
        if player.index == entity_index:
            return None

        entity = Entity(entity_index)
        other = player_instances[entity.owner.index]
        if player.realm != other.realm:
            return False

        return None

    if "player" == entity_classname:
        edict = CheckTransmitInfo._obj(args[1]).client

        player = player_instances[index_from_edict(edict)]

        if player.index == entity_index:
            return None

        other = player_instances[entity_index]

        if not player.realm == other.realm:
            return False

        return None

    if entity_classname == "trigger_teleport" or entity_classname == 'trigger_multiple':
        return None

    if entity_index not in func_properties:
        return None

    edict = CheckTransmitInfo._obj(args[1]).client

    player = player_instances[index_from_edict(edict)]

    if player.index == entity_index:
        return None
    return None if transmit_filter(entity_index, player, entity_classname, entity_index) else False


func_properties = {}
fitler_transmit = {}


class Filter_Transmit(Entity):
    def __init__(self, index):
        super().__init__(index)
        # Instance of the 'trigger_multiple' used for the custom bounding box.
        self.has_pointer = self.pointer


created_entities = EntityDictionary(Filter_Transmit)


@OnLevelEnd
def on_level_end():
    # Remove all custom bounding boxes when changing map
    func_properties.clear()
    crash_handler['safe'] = False


@OnLevelInit
def on_level_start(map):
    crash_handler['safe'] = True


def is_func_visible(brush):
    return EntityEffects.NODRAW not in EntityEffects(brush.effects)


def is_func_brush_visible(brush):
    return EntityEffects.NODRAW not in EntityEffects(brush.effects)


from listeners.tick import Delay


@OnEntitySpawned
def on_entity_spawned(base_entity):
    classname = base_entity.classname
    if classname in ENTITIES:
        index = base_entity.index
        register_entity(Entity(index), classname, index)


def register_entity(entity, classname, index, reset=False):
    entity.edict.clear_transmit_state()

    hidden = is_func_brush_visible(entity)

    if classname == 'func_wall_toggle':
        entity.solid_flags = SolidFlags.NOT_MOVEABLE
        entity.effects &= ~EntityEffects.NODRAW
        #entity.call_input("Enable")

    if classname == "trigger_teleport":
        disabled = not entity.get_property_bool('m_bDisabled')
        hidden = disabled

    if classname == 'func_brush':
        # if entity.get_key_value_int("Solidity") != 1:
        #entity.solid_flags = SolidFlags(entity.solid_flags | ~SolidFlags.NOT_SOLID)
        #if entity.get_key_value_int("Solidity") != 1:
        #    entity.solid_flags = SolidFlags.NOT_MOVEABLE
        entity.effects &= ~EntityEffects.NODRAW
        if entity.get_key_value_int("Solidity") != 1:
            entity.solid_flags = SolidFlags(entity.solid_flags & ~SolidFlags.NOT_SOLID)
        entity.call_input("Enable")


    wait = False
    if classname == "func_button":
        wait = entity.get_property_float('m_flWait')
        entity.set_property_float('m_flWait', 0)

    func_properties[index] = {'default': hidden,
                              'toggle': not hidden,
                              'collision': not hidden,
                              'cooldown': wait}

    fitler_transmit[entity.pointer] = entity


func_properties.clear()
fitler_transmit.clear()
