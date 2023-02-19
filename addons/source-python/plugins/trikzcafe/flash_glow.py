# wallhack_test.py
import memory

from colors import Color
from events import Event

from entities import CheckTransmitInfo
from entities.entity import Entity
from entities.hooks import EntityPreHook, EntityCondition
from entities.constants import EntityEffects, RenderMode
from entities.helpers import index_from_pointer, index_from_edict

from players.entity import Player
from players.helpers import index_from_userid, userid_from_edict, userid_from_index

from commands import CommandReturn
from commands.client import ClientCommand
from commands.say import SayCommand

from listeners import OnLevelEnd
from listeners.tick import Delay

from filters.players import PlayerIter
from .tcore.instances import PLAYER, FLASH_GLOW, ENTITY
from listeners import OnEntitySpawned, OnEntityDeleted
from messages import SayText2
from listeners import OnEntityTransmit


# sv_force_transmit_players
# has to be set to 1 in order for the wallhack to work correctly
# if set to 0, player glows that are too far will appear at map's origin
# NOTE: enabling this makes actual wallhacks more effective


@OnEntitySpawned
def spawned(base_entity):
    if base_entity.classname.endswith("projectile"):
        owner_handle = base_entity.owner_handle
        # No owner? (invalid inthandle)
        if owner_handle == -1:
            return
        flash_index = base_entity.index
        flash = ENTITY[flash_index]
        flash.delay(0.01, create_flash_model_prop, args=(flash, flash.owner.index), cancel_on_level_end=True)


@OnEntityTransmit
def on_entity_transmit(player, entity):
    ent_index = entity.index
    if ent_index not in FLASH_GLOW:
        return

    ent_owner = PLAYER[ENTITY[FLASH_GLOW[ent_index].parent.index].owner.index]
    player_index = player.index
    player = PLAYER[player_index]
    if not player.glow_flash_enabled or ent_owner.partner != player.partner:
        return False
    return True

@OnEntityDeleted
def deleted(base_entity):
    try:
        if base_entity.classname == "flashbang_projectile":
            index = base_entity.index
            flash = ENTITY[index]
            flash_prop = flash.glow_entity
            remove_flash_model(flash_prop.index)
    except:
        pass

# =============================================================================
# >> COMMANDS
# =============================================================================

# toggle_wallhack           - toggles wallhack on the player that used the command
# toggle_wallhack <userid>  - toggles wallhack on the specified userid
def enable_flash_glow(index):
    player = PLAYER[index]
    if player.glow_flash_enabled:
        player.glow_flash_enabled = False
    else:
        player.glow_flash_enabled = True
    FLASH_GLOW.change_state()

def remove_all_flash_models():
    for model in list(FLASH_GLOW.values()):
        model.remove()

def remove_flash_model(index):
    flash = FLASH_GLOW[index]
    flash.remove()


def create_flash_model_prop(flash, index2):
    player = PLAYER[index2]
    skin = Entity.create('prop_dynamic_override')
    skin.model = flash.model

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
    skin.set_parent(flash, -1)

    # make the player model prop invisible
    skin.render_color = Color(255, 255, 255, 0)
    skin.render_mode = RenderMode.TRANS_ALPHA

    # save the player model prop reference in a dictionary(userid:model prop reference)
    model_glow_player = player.glow_flash_prop[skin.index]
    model_glow = FLASH_GLOW[skin.index]
    flash.glow_entity = model_glow
    create_flash_glow(model_glow, player.glow_flash_color, player.glow_flash_style)
    return skin


def create_flash_glow(player_model, color, style):
    player_model.set_property_bool('m_bShouldGlow', True)

    # set the glow color
    # gotta use long color codes for this one
    # http://www.pbdr.com/pbtips/ps/rgblong.htm
    player_model.set_property_int('m_clrGlow', rgb_to_long(color[0], color[1], color[2]))

    player_model.set_property_int('m_nGlowStyle', style)

    # set the distance from which you can see the glow
    # NOTE: without this, the glow won't show
    player_model.set_property_float('m_flGlowMaxDist', 10000000.0)


# =============================================================================
# >> UTIL
# =============================================================================
def rgb_to_long(r, g, b):
    return b * 65536 + g * 256 + r
