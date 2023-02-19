from events import Event
from entities.helpers import index_from_pointer
from messages import SayText2
from players.helpers import index_from_userid
import active_menus
from entities.constants import SolidType, SolidFlags, EntityEffects, CollisionGroup, EntityFlags, RenderMode, \
    RenderEffects
from .tcore.instances import PLAYER, HITBOX
from entities.dictionary import EntityDictionary
from players.dictionary import PlayerDictionary
import memory
from memory import Convention
from memory import DataType
from entities.hooks import EntityCondition, EntityPreHook, EntityPostHook
from memory.manager import TypeManager
from path import Path
from listeners import OnEntitySpawned, OnLevelInit, OnLevelEnd, OnEntityOutput, OnEntityPreSpawned, OnEntityDeleted, \
    OnClientFullyConnect, OnClientDisconnect, OnNetworkedEntityCreated, OnNetworkedEntitySpawned
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
from filters.entities import EntityIter
from trikzcafe.tcore.instances import HITBOX
from trikzcafe.tcore.instances import ENTITY
from trikzcafe.tcore.instances import PLAYER, MODEL_GLOW, FLASH_GLOW
from trikzcafe.tcore.instances import ENTITY_REALM, Trigger
from trikzcafe.tcore.instances import ENTITY_FROM_ADDRESS
from trikzcafe.tcore.instances import HITBOX_FROM_ADDRESS
from listeners import OnEntityCollision, OnPlayerTransmit, OnPlayerCollision, OnNetworkedEntityCreated
from entities.transmit import TransmitSet
from entities.collisions import CollisionHook, CollisionHash
from listeners import OnEntityTransmit
from memory.manager import manager
from paths import ADDONS_PATH
from .tcore.instances import TEAMS

CBaseEntity = manager.create_type_from_file(
    'CBaseEntity', ADDONS_PATH + '/source-python/data/plugins/CBaseEntity.ini'
)


tracked_inputs = ('Break', 'Toggle', 'Open', 'Enable', 'Disable')
tracked_triggers = ('func_button', 'trigger_multiple')

# Hide flashes
@OnEntityTransmit
def on_transmit_player_entity(player, entity):
    entity_index = entity.index

    player_index = player.index
    if player_index not in PLAYER:
        return

    if entity_index in ENTITY:
        flash = ENTITY[entity_index]
        flash_owner = flash.owner.index
        other = PLAYER[flash_owner]
        player = PLAYER[player_index]
        if player.partner != other.partner:
            return False
        return



# Hide players
@OnPlayerTransmit
def on_transmit_player_other(player, other):
    player_index = player.index
    if player_index not in PLAYER:
        return
    other_index = other.index
    if other_index not in PLAYER:
        return
    other = PLAYER[other_index]
    player = PLAYER[player_index]
    if player.partner != other.partner:
        return False

# Ignore flash ignore hitboxes
@OnEntityCollision
def on_entity_collision(entity, other):
    entity_index = entity.index
    if entity_index not in ENTITY:
        return

    other_index = other.index
    if other_index in HITBOX:

        flash = ENTITY[entity_index]
        hitbox = HITBOX[other_index]
        flash_owner = flash.owner.index
        hitbox_owner = hitbox.parent.index
        player = PLAYER[hitbox_owner]
        other = PLAYER[flash_owner]
        if player.partner != other.partner:
            return False
        return

    if other_index in PLAYER:
        flash = ENTITY[entity_index]
        player = PLAYER[other_index]
        flash_owner = flash.owner.index
        other = PLAYER[flash_owner]
        if player.partner != other.partner:
            return False
        return

@OnPlayerCollision
def on_entity_collision(player, other):
    player_index = player.index
    other_index = other.index
    if player_index not in PLAYER:
        return

    if other_index in PLAYER:
        other = PLAYER[other_index]
        player = PLAYER[player_index]
        if player.partner != other.partner:
            return False
        return

    if other_index in ENTITY:
        flash = ENTITY[other_index]
        flash_owner = flash.owner.index
        other = PLAYER[flash_owner]
        player = PLAYER[player_index]
        if player.partner != other.partner:
            return False
        return

# For realm
@CollisionHook
def on_collision_hook(entity, other, trace, mask):
    entity_index = entity.index

    if entity_index not in PLAYER:
        return

    other_index = other.index
    if other_index not in ENTITY_REALM:
        return

    entity1 = ENTITY_REALM[other_index]
    player = PLAYER[entity_index]

    partner = player.partner
    if partner in entity1.completed:
        return entity1.default_is_hidden

    return not entity1.default_is_hidden


DEBUG = 0

@OnNetworkedEntityCreated
def on_entity_created(ent):
    if ent.classname.endswith('projectile'):
        entity = Entity(ent.index)
        owner = entity.owner
        if owner:
            player = PLAYER[owner.index]
            TEAMS.join_team_entity(player.partner, entity)

@EntityPreHook(EntityCondition.is_player, lambda entity: CBaseEntity._obj(entity.pointer).accept_input)
def accept_input(stack_data):
    input_name = stack_data[1]
    # Don't go further if this isn't an input we're tracking.
    if input_name not in tracked_inputs:
        return

    try:
        activator_index = index_from_pointer(stack_data[2])
        entity_index = index_from_pointer(stack_data[0])
    except ValueError:
        return

    player = PLAYER[activator_index]

    if entity_index not in ENTITY_REALM:
        entity = Entity(entity_index)
        if DEBUG:
            SayText2('\x08 Entity: %s not supported! Log this.' % entity.classname).send()
        return
    entity = ENTITY_REALM[entity_index]

    if entity.classname == 'trigger_multiple':
        return

    name = input_name + " " + Entity(entity_index).classname
    team = player.partner
    # SayText(entity.classname).send()
    # Button Pressed
    if input_name in ('Enable', 'Break', 'Open'):
        if player.press == Trigger.BUTTON:
            entity.complete_level(team, 'func_button', "Enable")
            if DEBUG:
                SayText2('\06%s => Complete | Button | Hidden: %s' % (name, entity.default_is_hidden)).send()
        elif player.press == Trigger.MULTIPLE:
            entity.complete_level(team, 'trigger', "Enable")
            if DEBUG:
                SayText2('\06%s => Complete | Multiple | Hidden: %s' % (name, entity.default_is_hidden)).send()
        else:
            entity.complete_level(team, 'trigger', "Enable")
            if DEBUG:
                SayText2('\06%s => Complete | Default | Hidden: %s' % (name, entity.default_is_hidden)).send()

    if input_name in ('Toggle'):
        if player.press == Trigger.BUTTON:
            entity.complete_level(team, 'func_button', "Toggle")
            if DEBUG:
                SayText2('\06%s => Complete | Default | Hidden: %s' % (name, entity.default_is_hidden)).send()
        elif player.press == Trigger.MULTIPLE:
            entity.complete_level(team, 'trigger', "Toggle")
            if DEBUG:
                SayText2('\06%s => Complete | Multiple | Hidden: %s' % (name, entity.default_is_hidden)).send()
        else:
            entity.complete_level(team, 'unknown', "Toggle")
            if DEBUG:
                SayText2('\06%s => Complete | Multiple | Hidden: %s' % (name, entity.default_is_hidden)).send()
    if input_name in ("Disable", "Close"):
        if player.press == Trigger.BUTTON:
            entity.complete_level(team, 'func_button', "Disable")
            if DEBUG:
                SayText2('\06%s => Complete | Button | Hidden: %s' % (name, entity.default_is_hidden)).send()
        else:
            entity.complete_level(team, 'trigger', 'Disable')
            if DEBUG:
                SayText2('\06%s => Disable | Default | Hidden: %s' % (name, entity.default_is_hidden)).send()

    return False


Entity_Outputs = ("trigger_multiple", 'func_button', 'func_wall_toggle', 'trigger_teleport')


@OnEntityOutput
def on_entity_output(output, activator, caller, value, delay):
    # Don't go further if the entity output isn't OnStartTouch.
    if caller.classname not in Entity_Outputs:
        return

    try:
        if not activator.is_player():
            return

        player = PLAYER[activator.index]
        if output == "OnPressed":
            entity = ENTITY_REALM[caller.index]
            if entity.wait is None:
                entity.wait = entity.get_property_float('m_flWait')
            caller.set_property_float('m_flWait', 0.1)
            caller.set_property_float('m_fStayPushed', 0.0)
            player.set_press(Trigger.BUTTON)
        elif output not in ('OnIn', 'OnOut'):
            player.set_press(Trigger.MULTIPLE)
    except:
        pass


from trikzcafe.tcore.instances import remove_hitbox_from_player, create_player_hitbox
from mathlib import Vector


@SayCommand(['!point', '/point'])
def find_entity(say, index, team_only=None):
    '''
    Called whenever a player says something.
    '''
    player = PLAYER[index]
    entity = player.get_view_entity()
    SayText2("Entity: %s" % (player.get_view_entity().classname)).send()
    TEAMS.teams['default']['hash'].add_pair(player, entity)
    SayText2("Entity: %s Should Collide: %s | Paired: %s" % (entity.classname,
                                                            TEAMS.teams['default']['hash'].should_collide(player, entity),
                                                            TEAMS.teams['default']['hash'].has_pair(player, entity))).send()
    """
    for ent in ENTITY_REALM.values():
        if ent.classname == "func_brush":
            org = Vector(-864, 6336, 2614)
            if ent.origin.get_distance(org) < 10:
                # ent.move_type = SolidFlags.NOT_SOLID
                SayText2('Hidden: %s' % ent.default_is_hidden).send()
                SayText2('Startdisabled: %s' % ent.get_key_value_bool("StartDisabled")).send()
                SayText2('solid type %s' % ent.solid_type).send()
                SayText2('Solid flags %s' % ent.solid_flags).send()
                SayText2('solid %s' % ent.physics_object.collision_enabled).send()
                SayText2('collision %s' % ent.collision_group).send()
                SayText2('spawnflags %s' % ent.spawn_flags).send()
            # entity.physics_object.collision_enabled = True
            # ent.set_key_value_bool("solidbsp", True)
            # ent.set_key_value_int("solid", 6)
            # ent.call_input("Enable")
    """

def is_brush_hidden(brush):
    return EntityEffects.NODRAW in EntityEffects(brush.effects)


FL_EDICT_ALWAYS = 1 << 3

@OnNetworkedEntitySpawned
def on_spawned(base_entity):
    if base_entity.classname in ['func_wall_toggle']:
        entity = ENTITY_REALM[base_entity.index]
        entity.default_is_hidden = bool(entity.spawn_flags)
        entity.edict.clear_transmit_state()
        entity.physics_object.collision_enabled = True
        entity.solid_flags &= ~SolidFlags.NOT_SOLID
        entity.effects &= ~EntityEffects.NODRAW

    elif base_entity.classname in ('func_door', 'func_door_rotating'):
        entity = ENTITY_REALM[base_entity.index]
        entity.edict.clear_transmit_state()

    elif base_entity.classname == "func_brush":
        entity = ENTITY_REALM[base_entity.index]
        entity.default_is_hidden = bool(entity.effects & EntityEffects.NODRAW) or entity.get_property_bool(
            "m_bSolidBsp")
        entity.edict.clear_transmit_state()
        entity.call_input("Enable")

    elif base_entity.classname == 'trigger_teleport':
        entity = ENTITY_REALM[base_entity.index]
        entity.delay(5, toggle_teleports, args=(entity,))


def contradict():
    SayText2('Entity is visible, but are startdisabled').send()


def toggle_teleports(entity):
    if entity.get_key_value_bool("StartDisabled"):
        entity.default_is_hidden = True
        entity.call_input("Enable")
    else:
        entity.default_is_hidden = False
    #entity.edict.clear_transmit_state()
    #entity.edict.state_changed()

is_teleport = EntityCondition.equals_entity_classname('trigger_teleport')
is_trigger = EntityCondition.equals_entity_classname('trigger_multiple')

@EntityPreHook(is_trigger, 'touch')
@EntityPreHook(is_teleport, 'touch')
def pre_touch_teleport(stack_data):
    index0 = index_from_pointer(stack_data[0])
    index1 = index_from_pointer(stack_data[1])
    if index0 not in ENTITY_REALM:
        return
    if index1 not in PLAYER:
        return
    player = PLAYER[index1]

    if player.is_dead:
        return

    entity = ENTITY_REALM[index0]

    pair = player.partner
    if pair in entity.completed:
        if entity.default_is_hidden:
            return
        else:
            return False
    else:
        if not entity.default_is_hidden:
            return
        else:
            return False

"""
@EntityPreHook(is_teleport, 'start_touch')
def teleport_touch(stack_data):
    index0 = index_from_pointer(stack_data[0])
    index1 = index_from_pointer(stack_data[1])
    return False
    if index0 not in ENTITY_REALM:
        return
    if index1 not in PLAYER:
        return
"""
"""
is_teleport = EntityCondition.equals_entity_classname('trigger_multiple')
@EntityPreHook(is_teleport, 'touch')
def pre_touch_multiple(stack_data):
    index0 = index_from_pointer(stack_data[0])
    index1 = index_from_pointer(stack_data[1])
    if index0 not in ENTITY_REALM:
        return
    if index1 not in PLAYER:
        return
    player = PLAYER[index1]

    if player.is_dead:
        return

    entity = ENTITY_REALM[index0]

    if entity.classname == "trigger_multiple":
        return False

    pair = (player.index, player.partner)
    pair2 = (player.partner, player.index)
    if pair in entity.completed or pair2 in entity.completed:
        if entity.default_is_hidden:
            return
        else:
            return False
    else:
        if not entity.default_is_hidden:
            return
        else:
            return False
"""
