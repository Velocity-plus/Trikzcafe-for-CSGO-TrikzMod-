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
from listeners import OnEntitySpawned, OnEntityDeleted, OnPlayerRunCommand
from engines.server import server
from memory.hooks import PreHook, PostHook
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
from trikzcafe.tcore.instances import HITBOX_FROM_ADDRESS
from trikzcafe.tcore.instances import shared_path
from trikzcafe.tcore.instances import remove_hitbox_from_player
from trikzcafe.tcore.instances import create_player_hitbox
from trikzcafe.tcore.instances import remove_all_hitbox
from .tcore.instances import PLAYER
from .model_glow import enable_glow, create_player_glow, update_model_glow
from entities.hooks import EntityCondition
from entities.hooks import EntityPreHook
from core import PLATFORM
from core import SOURCE_ENGINE
from memory import Convention, DataType
from cvars import ConVar
from engines.trace import ContentMasks
from engines.trace import GameTrace
from engines.trace import Ray
from engines.trace import TraceFilterSimple, TraceFilter
from engines.trace import engine_trace
from listeners import OnPlayerRunCommand
from mathlib import Vector
from engines.precache import Model
from engines.server import engine_server
from listeners import OnEntityTransmit

# ======================================================
# => Constants
# ======================================================

SETTINGS = ConfigObj(shared_path + 'settings.ini')

MimicSound_Flashbang = [
    Sound(SETTINGS["Sound_On_Flashbang_Hit"]["sound"], attenuation=Attenuation.GUNFIRE, volume=0.25)]

MimicSound_Falldamage = [Sound(SETTINGS["Sound_On_Falldamage"]["sound_1"], attenuation=Attenuation.NORMAL, volume=0.15),
                         Sound(SETTINGS["Sound_On_Falldamage"]["sound_2"], attenuation=Attenuation.NORMAL, volume=0.15),
                         Sound(SETTINGS["Sound_On_Falldamage"]["sound_2"], attenuation=Attenuation.NORMAL, volume=0.15)]

TARGET_CLASSNAME = 'flashbang_projectile'

"""
server1 = find_binary('server', srv_check=False)

PassServerEntityFilter = server1[b'\x55\xB8\x01\x00\x00\x00\x89\xE5\x83\xEC\x38\x89\x5D\xF4'].make_function(
    Convention.CDECL,
    [DataType.ULONG, DataType.ULONG],
    DataType.BOOL
)
"""

DEBUG = 0


# ============================================================================
# >> ENTITY PRE-HOOKS
# ============================================================================
@EntityPreHook(EntityCondition.equals_entity_classname('flashbang_projectile'), 'detonate')
def _pre_flashbang_detonate(stack_data):
    return False


from listeners import OnEntityCollision, OnPlayerTransmit


@OnEntityCollision
def on_entity_collision(entity, other):
    entity_index = entity.index
    other_index = other.index
    if entity_index not in ENTITY:
        return
    if other_index not in HITBOX:
        return

    flash = ENTITY[entity_index]
    hitbox = ENTITY[other_index]
    flash_owner = flash.owner.index
    hitbox_owner = hitbox.parent.index
    if flash_owner == hitbox_owner:
        return False


@OnPlayerGrenadeTouchUnder
def _on_player_grenade_touch_under(hitbox, entity, self_touch, multiple):
    if hitbox.index in HITBOX:
        player = PLAYER[hitbox.parent.index]
    else:
        player = PLAYER[hitbox.index]

    if self_touch:
        return

    if player.boost_step == 0 and not player.is_grounded:
        if player.jump_touch_velocity != NULL_VECTOR:
            # SayText2('\x05 Touch boost').send()
            player.playerVel = player.jump_touch_velocity
        else:
            player.playerVel = player.velocity

        player.flashVel = entity.velocity

        if DEBUG: SayText2('\x06[FB JUMP/F] -> \x08 Flash Vel: %s | Player Vel: %s | P: %s' % (
            round(player.flashVel.length, 2), round(player.playerVel.length, 2),
            round(player.origin.z - entity.origin.z, 2))).send()

        if entity.nj:
            player.flashVel = Vector(player.flashVel.x * 1.15, player.flashVel.y * 1.15, player.flashVel.z * 1.12)

        if player.playerVel.z <= -700:
            fall_sound = random.choice(MimicSound_Falldamage)
            fall_sound.index = player.index
            fall_sound.play()

        if player.velocity.length  > player.playerVelLastTick.length:
            player.playerVelLastTick = player.velocity

        if player.jump_touch_velocity != NULL_VECTOR:
            #SayText2('\x05 Touch boost %s' % str(player.jump_touch_velocity)).send()
            player.teleport(player.origin, None, player.jump_touch_velocity)
        else:
            #SayText2('\x05 Touch boost %s' % str(player.jump_touch_velocity)).send()
            player.teleport(player.origin, None, player.playerVelLastTick)

        if player.flashVel.length <= 300:
            player.flashVel.z = player.flashVel.z * 3.5
        player.boost_step = 1

        # if self_touch:
        #    player.flashVel.z = 750 + (abs(player.flashVel.z) * 0.1) + (abs(player.playerVel.z) * 0.12)
        #
        #    normal = player.flashVel.normalized() * -1
        #    player.flashVel.x = (normal.x * 500 * abs(player.playerVel.z) * 0.005) - player.flashVel.x * 0.1
        #    player.flashVel.y = (normal.y * 500 * abs(player.playerVel.z) * 0.005) - player.flashVel.y * 0.1

    entity.delay(0.25, entity.remove, cancel_on_level_end=True)


def reset_jump_touch_velocity(player):
    player.jump_touch_velocity = NULL_VECTOR


@OnPlayerOnTop
def on_player_on_top(up, down):
    if up.jump_touch_velocity == NULL_VECTOR:
        up.jump_touch_velocity = up.velocity
        up.delay(0.50, reset_jump_touch_velocity, args=(up,))

    if up.skyboost and up.boost_step > 0 and up.jumping and down.ducking:
        if up.repeater_runboost:
            up.repeater_runboost.stop()
        up.speed = 1
        return

    if up.jumped:
        up.repeater_runboost_tick = 200
        up.speed = 0.64
        if not up.repeater_runboost:
            up.repeater_runboost = Repeat(runboost_slow, args=(up, down), cancel_on_level_end=True)
            up.repeater_runboost.start(0.001)

        elif up.repeater_runboost.status & RepeatStatus.STOPPED:
            up.repeater_runboost = Repeat(runboost_slow, args=(up, down), cancel_on_level_end=True)
            up.repeater_runboost.start(0.001)
    up.jumped = False


@OnPlayerSky
def on_player_sky(up, down):
    if up.skyboost == 0:
        up.skyVelBooster = down.velocity
        up.skyVelFlyer = up.velocity
        up.ticks = 0
        up.speed = 1.0

        if up.skyVelBooster.z <= 0:
            return

        if down.is_crouched:
            up.skyVelBooster.z -= 50
        up.skyboost = 1


def runboost_slow(player, target):
    if player.skyboost or not player.boost_step == 0 or not target.flags & PlayerStates.ONGROUND:
        player.repeater_runboost_tick = 0
        player.speed = 1
        player.repeater_runboost.stop()

    player.repeater_runboost_tick -= 1
    height_diff = (player.origin.z - target.origin.z - player.maxs.z)

    if not (height_diff > 0.0) or not (height_diff < 20):
        player.speed = 1
        player.repeater_runboost.stop()

    if player.speed < 1.0:
        if target.velocity.length >= 245:
            player.speed = 1
            player.repeater_runboost.stop()
        else:
            player.speed += 0.008 * (player.speed / 4)

    if player.speed >= 1:
        player.speed = 1
        player.repeater_runboost.stop()

    if player.repeater_runboost_tick <= 0:
        player.speed = 1
        player.repeater_runboost.stop()


@EntityPostHook(EntityCondition.is_player, 'post_think')
def pre_post_think(stack_data, a):
    player = PLAYER[index_from_pointer(stack_data[0])]
    # Is the player dead or a spectator?
    if player.is_dead:
        return

    if player.on_ground:
        if not player.is_grounded and not player.is_grounded_timer:
            player.delay(1, change_state_grounded, args=(player, True), cancel_on_level_end=True)
            player.is_grounded_timer = True

    else:
        player.is_grounded = False
        player.is_grounded_timer = False

    if player.ducking:
        player.delay(0.06, change_state_crouched, args=(player, True), cancel_on_level_end=True)
        player.is_crouched = True

    if player.boost_step == 1:
        boost_vec = Vector(player.flashVel.x * 0.135, player.flashVel.y * 0.135, player.flashVel.z * -0.135)
        player.boost_step = 2

    if player.skyboost == 1:
        player.skyboost = 2


def change_state_grounded(player, state):
    player.is_grounded = player.on_ground


def change_state_crouched(player, state):
    player.is_crouched = player.ducking


from memory.manager import manager
from paths import ADDONS_PATH

CBaseGrenade = manager.create_type_from_file(
    'CBaseGrenade', ADDONS_PATH + '/source-python/data/plugins/CBaseGrenade.ini'
)


@EntityPreHook(
    EntityCondition.equals_entity_classname('flashbang_projectile'),
    lambda entity: CBaseGrenade._obj(entity.pointer).bounce_sound)
def bounce_sound_pre(stack_data):
    index = index_from_pointer(stack_data[0])
    if index not in ENTITY:
        return
    flash = ENTITY[index]
    if flash.touches > 3:
        return False


class BoostThreading:
    def __init__(self):
        self.index = None
        self.repeater = None
        self.thread = None

    def _threader(self):
        pass

    def repeat_thread(self):
        self.repeater = Repeat(self._threader, cancel_on_level_end=True)
        self.repeater.start(0.1)

    def start_thread(self):
        # Creates the thread
        self.thread = GameThread(target=self.repeat_thread)
        self.thread.daemon = True
        self.thread.start()


boost_thread = BoostThreading()


def closeplayer(player, radius):
    for other in PLAYER.values():
        if not player.index == other.index and not other.is_dead:
            dist = player.origin.get_distance(other.origin)
            if dist <= radius:
                return dist, other

    return 10000, None


TICK = 102.4

from players.constants import PlayerButtons


def set_jump(player):
    player.jumped3 = False


@OnPlayerRunCommand
def player_run_command(player, cmd):
    player = PLAYER[player.index]
    if not player.is_dead:
        # Get the player's view model.
        view_model = Entity.from_inthandle(player.get_property_int('m_hViewModel'))
        # Get the current view model animation sequence.
        sequence = view_model.get_network_property_uchar('m_nSequence')

        if cmd.buttons & PlayerButtons.JUMP and sequence == 2 and not player.jumped3 and player.on_ground:
            player.delay(0.5, set_jump, args=(player,))
            # SayText2('\x06 %s Did jump' % player.name).send()
            player.jumped3 = True

        if cmd.buttons & PlayerButtons.ATTACK:
            player.threw_ready = True

        playerFlags = player.flags

        if playerFlags & PlayerStates.ONGROUND and player.friction_jump and not player.skyboost and not player.boost_step:
            if not cmd.buttons & PlayerButtons.JUMP:
                if player.friction_tick >= 8:
                    if playerFlags & PlayerStates.DUCKING:
                        player.teleport(None, None, player.velocity * 0.84)
                    else:
                        player.teleport(None, None, player.velocity * 0.88)
                    # SayText2('\x02%s Stop' % player.name).send()
                if player.friction_tick >= 0:

                    player.set_property_float('cslocaldata.m_flStamina', player.friction_tick)
                    player.friction_tick -= 1
                else:
                    player.friction_jump = False
        else:
            player.friction_tick = 14

        if player.boost_step == 0 and player.skyboost == 2:
            bVel = player.skyVelBooster
            fVel = player.skyVelFlyer
            if DEBUG: SayText2('\x06 [SKYBOOST]: \x08 Booster Vel: %s | Flyer Vel: %s' % (
                round(bVel.z, 2), round(((fVel.z * -1) * 0.128) * 0.128, 2))).send()

            if bVel.z <= 0:
                bVel.z = 148

            # SayText2(f'B: {round(bVel.z, 2)} F: {round(fVel.z, 2)}').send()
            boost_z = pow(bVel.z, 1.164) + (abs(fVel.z) * 0.2)

            if 150 >= bVel.z >= 20 and boost_z <= 450:
                boost_z = pow(bVel.z, 1.24)

            if boost_z >= 865:
                boost_z = 865
            boost_vec = Vector(fVel.x - bVel.x, fVel.y - bVel.y, boost_z)

            player.teleport(None, None, boost_vec)
            player.skyboost = 3
            player.delay(0.1, reset_skyboost, args=(player,))

        if player.boost_step == 2:
            flashVel = player.flashVel
            playerVel = player.velocity
            if flashVel.z > 1000:
                reducer = 0.9928
            else:
                reducer = 0.9628
            boost_vec = Vector(playerVel.x - flashVel.x, playerVel.y - flashVel.y, flashVel.z * reducer)
            player.teleport(None, None, boost_vec)
            player.boost_step = 3

        elif player.boost_step == 3:
            flashVel = player.flashVel
            playerVel = player.velocity

            boost_vec = Vector(playerVel.x + (flashVel.x * 0.1528), playerVel.y + (flashVel.y * 0.1528), playerVel.z)
            player.teleport(None, None, boost_vec)
            player.boost_step = 0

        player.playerVelLastTick = player.velocity
        player.playerGroundLastTick = player.flags & PlayerStates.ONGROUND


def reset_skyboost(player):
    player.skyboost = 0


@OnLevelEnd
def on_level_end():
    remove_all_hitbox()


@OnLevelInit
def on_level_start(map_name):
    engine_server.precache_model('models/weapons/w_eq_smokegrenade_thrown.mdl')
    print('New map has started!')
    boost_thread.start_thread()


import math


def create_flashbang(player):
    # Don't render the 'trigger_multiple'.
    # Without this the players' consoles will get spammed with this error:
    # ERROR:  Can't draw studio model models/props/cs_assault/money.mdl
    # because CBaseTrigger is not derived from C_BaseAnimating
    # hitbox.effects |= EntityEffects.NODRAW
    ###
    degree = (2 * math.pi) / 4
    x, y, z = player.get_eye_location()
    x2, y2, z2 = Vector(x + 20, y - 20, z)
    x3 = (x2 - x) * math.cos(degree) - (y2 - y) * math.sin(degree)
    y3 = (y2 - y) * math.cos(degree) + (x2 - x) * math.sin(degree)
    z3 = z2
    flashbang = Entity.create('flashbang_projectile')

    # flashbang.model = Model(flashbangModel)
    flashbang.spawn()
    flashbang.set_network_property_int('m_hThrower', player.inthandle)
    flashbang.set_network_property_int('m_hOwnerEntity', player.inthandle)
    px, py, pz = player.origin
    flashbang.origin = Vector(px, py, pz + 64) + (player.view_vector)

    flashbang.avelocity = Vector(1000, 0, 600)

    vx, vy, vz = player.view_vector
    # format_vec(player.view_vector)
    new_view = Vector(vx, vy, vz * 1.15).normalized()
    vx, vy, vz = new_view
    SayText2("100 ms" + str(player.velocity)).send()
    direction = Vector(675 * vx, 675 * vy, 675 * vz) + player.velocity
    # SayText2(str(player.view_vector)).send()
    flashbang.teleport(None, None, direction)
    ent = ENTITY[flashbang.index]
    flashbang.delay(1.6, flashbang.remove)
    # flashbang.delay(0, speed_of_flash, args=(flashbang,), cancel_on_level_end=True)
    player.threw = True
    player.delay(1, throw_again, args=(player,))


def throw_again(player):
    player.threw = False


@OnEntitySpawned
def spawned(base_entity):
    if base_entity.classname.endswith("projectile"):
        owner_handle = base_entity.owner_handle
        # No owner? (invalid inthandle)
        if owner_handle == -1:
            return

        flash_index = base_entity.index
        ent = ENTITY[flash_index]
        # s.add(base_entity)

    if base_entity.classname == "flashbang_projectile":
        owner_handle = base_entity.owner_handle
        # No owner? (invalid inthandle)
        if owner_handle == -1:
            return

        flash_index = base_entity.index
        ent = ENTITY[flash_index]

        player = PLAYER[ent.owner.index]
        # if player.flash_skin_enabled:
        #    ent.model = Model('models/weapons/w_eq_smokegrenade_thrown.mdl')
        if player.on_ground:
            ent.nj = True
        # ent.delay(0, calculate_efficiency, args=(player, ent), cancel_on_level_end=True)
        # ent.delay(0, speed_of_flash, args=(ent, player), cancel_on_level_end=True)
        ex, ey, ez = ent.origin
        quick_spawn = Vector(ex, ey, ez + 3)
        ent.teleport(quick_spawn, None, None)
        ent.delay(1.4, ent.remove, cancel_on_level_end=True)


from entities.constants import RenderEffects, RenderMode, DissolveType


def format_vec(v):
    x, y, z = v
    SayText2("X: %s Y: %s Z: %s | Len %s" % (round(x, 2), round(y, 2), round(z, 2), round(v.length, 2))).send()


def speed_of_flash(entity, player):
    evx, evy, evz = entity.velocity
    nx, ny, nz = entity.velocity.normalized()
    normal = Vector(evx, evy, evz + 365)
    ex, ey, ez = entity.origin

    quick_spawn = Vector(ex + (nx * 8), ey + (ny * 8), ez + (nz * 8))

    if player.jumped3 and entity.velocity.length <= 680:
        for players in PLAYER.values():
            if players.steamid == "STEAM_1:0:21252369":
                # SayText2('\x06 Bug -> Self-fix %s ' % round(entity.velocity.length,2)).send(players.index)
                break
        entity.fake_jump = True
    entity.teleport(quick_spawn, None, None)

    # if player.jumped3:
    #   SayText2('Flash %s nj: %s' % (player.jump_velocity, entity.nj)).send()

    # ent_org = entity.origin
    # SayText2("X: %s Y: %s Z: %s" % (round(normal.x * 8, 2), round(normal.y * 8, 2), round((1 - normal.z) * 8, 2))).send()


def calculate_efficiency(player, flash):
    efficiency = 0.34129692832
    efficiency_result = round(player.velocity.z * efficiency, 1)
    if efficiency_result < 60:
        player.boost_stats['efficiency'] = "-.--"
    else:
        if efficiency_result > 100:
            efficiency_result = 100
        player.boost_stats['efficiency'] = efficiency_result


@Event('player_death', 'player_team', 'player_disconnect')
def events_for_removal(event):
    userid = event['userid']
    try:
        player = PLAYER.from_userid(userid)
        # Does the player have a custom bounding box?
        remove_hitbox_from_player(player)
    except ValueError:
        return


@Event("player_spawn")
def OnSpawn(game_event):
    try:
        userid = game_event['userid']
        player = PLAYER.from_userid(userid)
        if not player.is_player() or player.is_dead:
            return
        remove_hitbox_from_player(player)
        create_player_hitbox(player)
    except ValueError:
        pass


@Event("player_jump")
def OnJump(game_event):
    userid = game_event['userid']
    player = PLAYER[index_from_userid(userid)]
    base_vel = player.base_velocity
    player.jumped_height = player.origin.z
    target_info = closeplayer(player, radius=156)
    player.jumped2 = True
    if target_info[0] <= 156:
        target = target_info[1]
        if target.flags & PlayerStates.DUCKING:
            if abs(target.origin.z - player.origin.z) <= 1:
                player.base_velocity = Vector(base_vel.x, base_vel.y, base_vel.z + 16)
                player.jump_velocity = player.velocity
                player.jumped = True

        else:
            if abs(player.origin.z - target.origin.z) <= 10:
                player.base_velocity = Vector(base_vel.x, base_vel.y, base_vel.z + 24)
            player.jumped = True
        player.speed = 1.0
    player.friction_jump = True


def get_trace_attack_function(entity):
    offset = {
        'orangebox': {'windows': 60, 'linux': 61},
        'csgo': {'windows': 66, 'linux': 67}
    }[SOURCE_ENGINE][PLATFORM]
    return entity.pointer.make_virtual_function(
        offset,
        Convention.THISCALL,
        # this, CTakeDamageInfo, Vector, trace_t, CDmgAccumulator
        (DataType.POINTER, DataType.POINTER, DataType.POINTER,
         DataType.POINTER, DataType.POINTER),
        DataType.VOID
    )


@EntityPreHook(EntityCondition.is_player, get_trace_attack_function)
def pre_trace_attack(stack_data):
    victim_index = index_from_pointer(stack_data[0])
    if victim_index not in PLAYER:
        return
    victim = PLAYER[victim_index]

    damage_info = make_object(TakeDamageInfo, stack_data[1])
    if damage_info.attacker not in PLAYER:
        return
    attacker = PLAYER[damage_info.attacker]
    attacker_weapon = attacker.active_weapon.classname
    damage = damage_info.damage
    xvv, yvv, zvv = victim.velocity
    xva, yva, zva = attacker.velocity
    if victim.partner != attacker.partner:
        return
    xa, ya, za = attacker.view_angle
    xnv, ynv, znv = Vector(xva, yva, 0).normalized()
    default_boost_knife = Vector((525 * xnv), (525 * ynv), 350) + Vector(xva * 1.325, yva * 1.325, 0)
    z_boost = 400
    if xa * -1 > 0:
        # SayText2(str(( xa * -1 * 100/89))).send()
        z_boost = ((175 * ((xa * -1) / 89)) + zva) + z_boost

    if attacker_weapon == "weapon_knife":
        if damage in (65, 180):
            z_boost = z_boost * 1.10
        boost = Vector(xvv - default_boost_knife.x, yvv - default_boost_knife.y, z_boost)
        x, y, z = boost
        # SayText2("Player: " + str(round(xva,2))+  " "+ str(round(yva,2)) +  " "+ str(round(zva, 2))).send()
        # SayText2("Boost: " + str(round(x,2)) +  " "+ str(round(y,2)) +  " "+ str(round(z, 2))).send()
        # SayText2("Knife Z Boost: " + str(boost[2])).send()
        if not victim.is_grounded:
            victim.teleport(None, None, boost)

    else:
        if (victim.flags & PlayerStates.ONGROUND):
            boost = Vector(xvv - (xva * 0.667), yvv - (yva * 0.667), 500)
            victim.teleport(None, None, boost)
            switch(PLAYER[attacker.index], "weapon_flashbang")
            WeaponSwitch(PLAYER[attacker.index], "weapon_flashbang")


def switch(player, weapon):
    if not player.is_dead:
        player.client_command('use %s' % weapon, server_side=True)


def WeaponSwitch(player, weapon):
    if not player.is_dead:
        if weapon == 'weapon_flashbang':
            player.set_property_float('m_flNextAttack', 1.0)
            player.set_property_bool('m_bWaitForNoAttack', False)


sv_maxvelocity = ConVar("sv_maxvelocity")

from entities.constants import RenderMode


def create_player_glow(entity, color):
    player_model = Entity(entity.index)
    player_model.render_mode = RenderMode.GLOW
    # turn the glow on
    # player_model.get_property_bool('m_bShouldGlow')

    # set the glow color
    # gotta use long color codes for this one
    # http://www.pbdr.com/pbtips/ps/rgblong.htm
    player_model.set_property_int('m_clrGlow', rgb_to_long(color[0], color[1], color[2], color[3]))
    player_model.set_property_int('m_GlowStyle', 2)
    # set the distance from which you can see the glow
    # NOTE: without this, the glow won't show
    player_model.set_property_float('m_flGlowMaxDist', 10000000.0)


from colors import Color
from commands.say import SayCommand


@SayCommand(['!glow'])
def change_model(say, index, team_only=None):
    """Changes the player's world and warms model."""
    player = PLAYER[index]
    # create_player_glow(player, Color(255,0,0, 255))
    if say.command_string.startswith('/'):
        return CommandReturn.BLOCK


class MyTraceFilter(TraceFilterSimple):
    def __init__(self, player, hitboxes):
        super().__init__([])
        self.hitboxes = hitboxes
        self.player = player

    def should_hit_entity(self, entity, contents_mask):
        if entity in self.hitboxes or entity == self.player:
            return False
        return super().should_hit_entity(entity, contents_mask)


def is_player_surfing(player):
    origin = Vector(player.origin.x, player.origin.y, player.origin.z - 100)
    destination = Vector(origin.x, origin.y, origin.z - sv_maxvelocity.get_int())

    trace = GameTrace()

    ignore = tuple([player] + [BaseEntity(hit.index) for hit in HITBOX.values()])
    filter = TraceFilterSimple(ignore)

    engine_trace.trace_ray(
        Ray(origin, destination, player.mins, player.maxs),
        ContentMasks.PLAYER_SOLID_BRUSH_ONLY,
        filter,
        trace,
    )

    is_surfing = False
    if trace.did_hit():
        # Sometimes I'm getting 0.00048828125, mostly 0.0
        destination_distance = trace.end_position.get_distance(origin)
        SayText2(str(round(trace.plane.normal.z, 3)) + " - " + str(round(destination_distance, 3))).send()
        if (destination_distance <= 1 and trace.plane.normal.z >= 0.7 and trace.plane.normal.z < 1.0):
            is_surfing = True

    return is_surfing, trace.plane.normal