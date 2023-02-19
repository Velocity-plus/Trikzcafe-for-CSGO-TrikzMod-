# wallhack_test.py
import memory

from colors import Color
from events import Event

from entities import CheckTransmitInfo
from entities.entity import Entity
from entities.hooks import EntityPreHook, EntityCondition
from entities.constants import EntityEffects, RenderMode
from entities.helpers import index_from_pointer, index_from_edict
from listeners import OnEntityDeleted
from players.entity import Player
from players.helpers import index_from_userid, userid_from_edict, userid_from_index

from commands import CommandReturn
from commands.client import ClientCommand
from commands.say import SayCommand

from listeners import OnLevelEnd
from listeners.tick import Delay

from filters.players import PlayerIter
from .tcore.instances import PLAYER, MODEL_GLOW

from messages import SayText2

# sv_force_transmit_players
# has to be set to 1 in order for the wallhack to work correctly
# if set to 0, player glows that are too far will appear at map's origin
# NOTE: enabling this makes actual wallhacks more effective

# =============================================================================
# >> COMMANDS
# =============================================================================


# toggle_wallhack           - toggles wallhack on the player that used the command
# toggle_wallhack <userid>  - toggles wallhack on the specified userid
def enable_glow(index):
    player = PLAYER[index]
    if player.glow_enabled:
        player.glow_enabled = False
        remove_and_create_all_models()
    else:
        player.glow_enabled = True
        for other in PLAYER.values():
            create_player_model_prop(other.index)

def update_model_glow():
    remove_and_create_all_models()

def remove_all_models():
    for model in list(MODEL_GLOW.values()):
        model.remove()

def remove_and_create_all_models():
    for model in list(MODEL_GLOW.values()):
        model.remove()
    for other in PLAYER.values():
        create_player_model_prop(other.index)

def remove_player_model(index):
    player = PLAYER[index]
    for index in list(player.glow_prop):
        model = player.glow_prop[index]
        model.remove()

# >> EVENTS
# =============================================================================
@Event('player_spawn')
def player_spawned(event):
    userid = event['userid']
    index = index_from_userid(userid)
    # is there at least 1 player using wallhack?
    player = PLAYER[index]
    #player.delay(0.01, late_spawn_check, (index,), cancel_on_level_end=True)


@Event('player_death', 'player_team')
def player_death(event):
    userid = event['userid']
    index = index_from_userid(userid)
    player = PLAYER[index]
    remove_player_model(player.index)


def late_spawn_check(index):
    create_player_model_prop(index)


@Event('player_disconnect')
def player_left(event):
    try:
        userid = event['userid']
        index = index_from_userid(userid)
        remove_player_model(index)
    except ValueError:
        pass


from listeners import *
from entities.transmit import *


@OnEntityTransmit
def on_entity_transmit(player, entity):
    ent_index = entity.index
    if ent_index not in MODEL_GLOW:
        return

    model_glow = MODEL_GLOW[ent_index]
    model_glow_owner = model_glow.parent.index
    other = PLAYER[model_glow_owner]

    player_index = player.index
    player = PLAYER[player_index]
    if not player.glow_enabled:
        return False

    if other.index == player.index:
        if player.glow_enabled_self:
            return False

    return


def create_player_model_prop(index):
    player = PLAYER[index]
    if len(player.glow_prop) > 0:
        for glow_model in player.glow_prop.values():
            glow_model.model = player.model
            glow_model.edict.state_changed()
        return None

    skin = Entity.create('prop_dynamic_override')
    skin.model = player.model

    # spawn with collisions disabled
    skin.spawn_flags = 256

    skin.set_property_uchar('m_CollisionGroup', 11)
    skin.spawn()

    # BONEMERGE         merge child(player model prop) and parent(player) bones with the same name
    # more info:        https://developer.valvesoftware.com/wiki/EF_BONEMERGE

    # NOSHADOW          disable shadows from this model
    # NORECEIVESHADOW   disable receiving of shadows on this model

    # PARENT_ANIMATES   make sure the model is always properly aligned with the parent(player)
    # more info:        https://developer.valvesoftware.com/wiki/EF_PARENT_ANIMATES
    skin.effects = EntityEffects.BONEMERGE | EntityEffects.NOSHADOW | EntityEffects.NORECEIVESHADOW | EntityEffects.PARENT_ANIMATES

    # parent player model prop to the player
    skin.set_parent(player, -1)
    skin.set_parent_attachment('primary')

    # make the player model prop invisible
    skin.render_color = Color(255, 255, 255, 0)
    skin.render_mode = RenderMode.TRANS_ALPHA

    # save the player model prop reference in a dictionary(userid:model prop reference)

    model_glow_player = player.glow_prop[skin.index]
    model_glow = MODEL_GLOW[skin.index]
    create_player_glow(model_glow, player.glow_color)
    model_glow.edict.state_changed()
    return model_glow


def create_player_glow(player_model, color, yes=True):
    player_model.set_property_bool('m_bShouldGlow', yes)

    # set the glow color
    # gotta use long color codes for this one
    # http://www.pbdr.com/pbtips/ps/rgblong.htm
    player_model.set_property_int('m_clrGlow', rgb_to_long(color[0], color[1], color[2]))
    # set the distance from which you can see the glow
    # NOTE: without this, the glow won't show
    player_model.set_property_float('m_flGlowMaxDist', 10000000.0)


# =============================================================================
# >> UTIL
# =============================================================================
def rgb_to_long(r, g, b):
    return b * 65536 + g * 256 + r
