from mathlib import Vector, QAngle, NULL_VECTOR
from math import sqrt,pow
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
from listeners import OnEntitySpawned
from engines.server import server
from listeners import OnLevelEnd
from listeners import OnLevelInit
from listeners.tick import Repeat
from listeners.tick import GameThread
from listeners.tick import RepeatStatus
from listeners import OnTick
from memory import make_object
from messages import SayText2, SayText
from messages import HintText
from engines.sound import Attenuation
from engines.sound import Sound
from core import echo_console
from .data import PLAYER
from .data import HITBOX
from .data import shared_path
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
from trikzcafe.tcore.instances import remove_hitbox_from_player
from trikzcafe.tcore.instances import create_player_hitbox
from entities.hooks import EntityCondition
from entities.hooks import EntityPreHook
from core import PLATFORM
from core import SOURCE_ENGINE
from memory import Convention, DataType
from cvars import ConVar
from engines.trace import ContentMasks
from engines.trace import GameTrace
from engines.trace import Ray
from engines.trace import TraceFilterSimple
from engines.trace import engine_trace
from listeners import OnPlayerRunCommand
from mathlib import Vector

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


@OnPlayerGrenadeTouch
def _on_player_grenade_touch(hitbox, entity, self_touch, multiple):
    if hitbox.index in HITBOX:
        player = PLAYER[hitbox.parent.index]
    else:
        player = PLAYER[hitbox.index]

    if entity.owner.index == player.index:
        return

    if (entity.origin.z - hitbox.origin.z) < 1:
        return

    #SayText2('This maybe?').send()
    pVel = player.velocity.normalized()
    fVel = entity.velocity.normalized()

    check_x = 0
    check_y = 0
    if pVel[0] > 0 and fVel[0] < 0 or pVel[0] < 0 and fVel[0] > 0:
        check_y = 1

    if pVel[1] > 0 and fVel[1] < 0 or pVel[1] < 0 and fVel[1] > 0:
        check_x = 1

    if check_x and check_y:
        #player.teleport(None, None, Vector(0, 0, player.velocity[2]))
        pass

    if hitbox.classname != 'trigger_multiple':
        return

    flash_sound = random.choice(MimicSound_Flashbang)
    flash_sound.index = player.index

    flash_sound.play()
    normal = entity.origin - player.origin
    normal.normalize()
    # Second and final pass at calculating the normal, this one should work.
    # Subtract the normalized projectile velocity from the normal to get
    # more pronounced values. Maybe I'm overthinking this?
    final_normal = get_box_normal(normal - entity.velocity.normalized())
    # Calculate the direction / velocity of the bouncing projectile.
    bounce_direction = final_normal * final_normal.dot(entity.velocity) * 2
    bounce_velocity = entity.velocity - bounce_direction
    # Decrease the velocity of the projectile by 45%.
    bounce_velocity.length = entity.velocity.length * 0.34
    # Add the new velocity to the projectile.
    entity.teleport(None, None, bounce_velocity)
    entity.delay(0.25, entity.remove, cancel_on_level_end=True)


@OnPlayerGrenadeTouchUnder
def _on_player_grenade_touch_under(hitbox, entity, self_touch, multiple):
    if hitbox.index in HITBOX:
        player = PLAYER[hitbox.parent.index]
    else:
        player = PLAYER[hitbox.index]

    if hitbox.classname != "prop_dynamic" or hitbox.identifier != "UNDER":
        return

    if self_touch:
        return

    if player.boost_step == 0 and not player.is_grounded:
        #SayText2('Boost').send()
        player.test['flash'] = 1
        player.playerVel = player.velocity
        player.flashVel = entity.velocity
        player.boost_step = 1

        if player.playerVel.z <= -700:
            fall_sound = random.choice(MimicSound_Falldamage)
            fall_sound.index = player.index
            fall_sound.play()
        if player.flashVel.length < 300:
            player.flashVel.z = player.flashVel.z * 3.35

    entity.delay(0.25, entity.remove, cancel_on_level_end=True)


@OnPlayerOnTop
def on_player_on_top(up, down):
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
        if down.is_crouched:
            #SayText2('True').send()
            up.skyVelBooster.z -= 75

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
        if target.velocity.length >= 240:
            player.speed = 1
            player.repeater_runboost.stop()
        else:
            player.speed += 0.009 * (player.speed / 3.125)

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
            player.delay(0.48, change_state_grounded, args=(player, True), cancel_on_level_end=True)
            player.is_grounded_timer = True

    else:
        player.is_grounded = False
        player.is_grounded_timer = False

    if player.ducking:
        player.delay(0.1, change_state_crouched, args=(player, True), cancel_on_level_end=True)
        player.is_crouched = True



    if player.boost_step == 1:
        # boost_vec = Vector(player.flashVel.x * 0.135, player.flashVel.y * 0.135, player.flashVel.z * -0.135)
        player.boost_step = 2

    if player.skyboost == 1:
        player.skyboost = 2

def change_state_grounded(player, state):
    player.is_grounded = player.on_ground

def change_state_crouched(player, state):
    player.is_crouched = player.ducking

class BoostThreading:
    def __init__(self):
        self.index = None
        self.repeater = None
        self.thread = None

    def _threader(self):
        for player in PLAYER.values():
            if not player.is_dead and player.boost_stats['enabled']:
                efficiency = player.boost_stats['efficiency']
                speed = round(player.velocity.length_2D, 1)

                spectators = player.get_spectators(PLAYER.values())
                spectators_len = 0
                for _ in player.get_spectators(PLAYER.values()):
                    spectators_len += 1
                for spec in player.get_spectators(PLAYER.values()):
                    HintText('Efficiency: {0}%\nSpeed: {1}\nSpecs: {2}'.format(efficiency, speed, spectators_len)).send(spec.index)

                HintText('Efficiency: {0}%\nSpeed: {1}\nSpecs: {2}'.format(efficiency, speed, spectators_len)).send(player.index)
            else:
                pass
                #target_index = player.observer_target
                #SayText2('Target: %s' % target_index).send()
                #if target_index:
                #    player2 = PLAYER[target_index]
                #    efficiency = player2.boost_stats['efficiency']
                #    speed = round(player2.velocity.length_2D, 1)
                #    HintText('Efficiency: {0}%\n Speed: {1}\n'.format(efficiency, speed)).send(player.index)


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


test = 1


def calculate_sky_boost(x):
    if x > 300:
        x = 300
    boost = 0.383139126937465e-4 * x ** 3 - 0.105106488752637e-1 * x ** 2 + 1.26257372918474 * x + 397.842857797988

    return boost

TICK = 102.4
@EntityPreHook(EntityCondition.is_player, 'run_command')
def player_run_command(args):
    player = PLAYER[index_from_pointer(args[0])]
    if not player.is_dead:

        cmd = make_object(UserCmd, args[1])

        if test:
            ox, oy, oz = player.test['origin']
            nx, ny, nz = player.origin

            if player.flags & PlayerStates.ONGROUND:
                if player.test['msg'] == 0 and (player.test['height'] > 63 or player.test['distance'] >= 240):
                    player.test['msg'] = 1
                    if player.test['display']:
                        if player.test['flash']:
                            SayText2('<Flash> Name: %s > Height: %s, Dist: %s' % (
                                player.name, round(player.test['height'], 1), round(player.test['distance'], 1))).send()
                        else:
                            SayText2('<Normal> Name: %s > Height: %s, Dist: %s' % (
                                player.name, round(player.test['height'], 1), round(player.test['distance'], 1))).send()
                player.test['height'] = 0
                player.test['flash'] = 0
                player.test['origin'] = player.origin
            else:
                player.test['msg'] = 0
                player.test['air'] = 1
                height = Vector(0, 0, oz).get_distance(Vector(0, 0, nz))
                # SayText2('Name: %s > Height: %s, Dist: %s' % (
                # player.name, round(player.test['height'], 1), round(player.test['distance'], 1))).send()
                if height > player.test['height']:
                    player.test['height'] = height
                # player.test['height'] = height
                player.test['distance'] = Vector(ox, oy, 0).get_distance(Vector(nx, ny, 0)) + 32

        if player.boost_step == 0 and not player.skyboost:
            is_surfing, plane_normal = is_player_surfing(player)
            if is_surfing and player.flags & PlayerStates.ONGROUND and not player.playerGroundLastTick:

                # SayText2("Slope fix").send()
                vLast = player.playerVelLastTick
                vLast[2] -= float(ConVar("sv_gravity")) * 0.128

                fBackOff = vLast.dot(plane_normal)

                change = 0
                vVel = Vector(0, 0, 0)
                for i in range(2):
                    change = plane_normal[i] * fBackOff
                    vVel[i] = vLast[i] - change

                fAdjust = vVel.dot(plane_normal)

                if fAdjust < 0.0:
                    for i in range(2):
                        vVel[i] -= (plane_normal[i] * fAdjust)

                vVel[2] = 0
                vLast[2] = 0
                if vVel.length > vLast.length:
                    if player.flags & EntityStates.BASEVELOCITY:
                        vVel += player.base_velocity
                    #SayText2('Slope fix').send()
                    player.teleport(None, None, vVel)

        if player.boost_step == 0 and player.skyboost == 2:
            bVel = player.skyVelBooster
            fVel = player.skyVelFlyer
            #SayText2('Booster vel: %s flyer vel: %s' % (round(bVel.z,2), round(abs(fVel.z) * 0.128,2))).send()
            if bVel.z <= 0:
                bVel.z = 1

            boost_z = pow(bVel.z, 1.168) + (abs(fVel.z) * 0.128)
            if boost_z >= 865:
                boost_z = 865
            boost_vec = Vector(fVel.x, fVel.y, boost_z)

            player.teleport(None, None, boost_vec)
            player.skyboost = 0

        if player.boost_step == 2:
            flashVel = player.flashVel
            playerVel = player.playerVel
            boost_vec = Vector(playerVel.x - flashVel.x, playerVel.y - flashVel.y, flashVel.z)
            player.teleport(None, None, boost_vec)
            player.boost_step = 3

        elif player.boost_step == 3:
            flashVel = player.flashVel
            playerVel = player.playerVelLastTick

            boost_vec = Vector(playerVel.x + (flashVel.x * 0.1728), playerVel.y + (flashVel.y * 0.1728), playerVel.z)
            player.teleport(None, None, boost_vec)
            player.boost_step = 0

        playerFlags = player.flags
        if playerFlags & PlayerStates.ONGROUND:
            player.flash_x = 1
            if player.get_property_float('m_flDuckSpeed') < 7.0:
                player.set_property_float('m_flDuckSpeed', 7.0)

        if playerFlags & PlayerStates.ONGROUND and playerFlags & PlayerStates.DUCKING and player.friction_jump:
            if not cmd.buttons & PlayerButtons.JUMP:

                if player.friction_tick >= 8:
                    player.teleport(None, None, player.velocity)
                if player.friction_tick >= 0:
                    player.set_property_float('cslocaldata.m_flStamina', player.friction_tick)

                    player.friction_tick -= 1
                else:
                    player.friction_jump = False
        else:
            player.friction_tick = 14

        player.playerVelLastTick = player.velocity
        player.playerGroundLastTick = player.flags & PlayerStates.ONGROUND



@OnLevelEnd
def on_level_end():
    pass


@OnLevelInit
def on_level_start(map_name):
    print('New map has started!')
    boost_thread.start_thread()




def get_box_normal(normal):
    # If a projectile hits near the bottom of the custom bounding box, it
    # might freak out and go through the ground or the player.
    # Decrease the z axis of the normal to avoid this (mostly).
    normal.z *= 0.5
    # Get the largest normal value to determine which side of the box got hit.
    primary_side = max(map(abs, normal))

    # Go through all the normal axes.
    for axis, value in enumerate(normal):
        # Is this the side that got hit?
        # Subtracting 0.04 here allows for bouncing off of edges.
        if abs(value) >= primary_side - 0.04:
            normal[axis] = round(value)
        else:
            normal[axis] = 0

    return normal


@OnEntitySpawned
def spawned(base_entity):
    if base_entity.classname == "flashbang_projectile":
        flash_index = base_entity.index
        ent = ENTITY[flash_index]
        player = PLAYER[ent.owner.index]
        for hitbox_index in player.hitbox_prop:
            hitbox = HITBOX[hitbox_index]
            if hitbox.identifier == "OVER":
                if hitbox.ghost_quick_over_delay:
                    hitbox.ghost_quick_over_delay.cancel()

                hitbox.collision_group = CollisionGroup.DEBRIS
                hitbox.ghost_quick_over_delay = hitbox.delay(1.41, change_collision_over, args=(hitbox, None), cancel_on_level_end=True)

            angle = player.get_view_angle().x >= 70
            if hitbox.identifier == "UNDER" and angle and not player.is_grounded:
                if hitbox.ghost_delay:
                    hitbox.ghost_delay.cancel()
                hitbox.collision_group = CollisionGroup.DEBRIS
                hitbox.ghost = True
                hitbox.ghost_delay = hitbox.delay(0.2, change_collision, args=(hitbox, None), cancel_on_level_end=True)

        ent.delay(0, calculate_efficiency, args=(player, ent), cancel_on_level_end=True)
        ent.delay(1.4, ent.remove, cancel_on_level_end=True)


def change_collision(hitbox, player):
    hitbox.ghost_delay = None
    hitbox.collision_group = CollisionGroup.DEBRIS_BLOCK_PROJECTILE
    hitbox.ghost = False

def change_collision_over(hitbox, player):
    hitbox.ghost_quick_over_delay = None
    hitbox.collision_group = CollisionGroup.DEBRIS_BLOCK_PROJECTILE



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
    userid = game_event['userid']
    try:
        player = PLAYER[index_from_userid(userid)]
    except ValueError:
        return

    if not player.is_player() and not player.is_dead:
        return
    remove_hitbox_from_player(player)
    create_player_hitbox(player)


@Event("player_jump")
def OnJump(game_event):
    userid = game_event['userid']
    player = PLAYER[index_from_userid(userid)]
    base_vel = player.base_velocity
    player.jumped_height = player.origin.z
    target_info = closeplayer(player, radius=156)
    if target_info[0] <= 156:
        target = target_info[1]
        if target.flags & PlayerStates.DUCKING:
            if target.origin.z <= player.jumped_height:
                player.base_velocity = Vector(base_vel.x, base_vel.y, base_vel.z + 8)
                player.jumped = True

        else:
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
        if not (victim.flags & PlayerStates.ONGROUND):
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


def is_player_surfing(player):
    origin = player.origin

    destination = Vector(origin.x, origin.y, origin.z - sv_maxvelocity.get_int())

    trace = GameTrace()


    filters = (player,) + tuple([hit for hit in player.hitbox_prop.values()])

    engine_trace.trace_ray(
        Ray(origin, destination, player.mins, player.maxs),
        ContentMasks.PLAYER_SOLID_BRUSH_ONLY,
        TraceFilterSimple((filters)),
        trace,
    )

    is_surfing = False

    if trace.did_hit():
        # Sometimes I'm getting 0.00048828125, mostly 0.0
        destination_distance = trace.end_position.get_distance(origin)
        # SayText2(str(trace.plane.normal.z)).send()
        if (destination_distance <= 1 and trace.plane.normal.z >= 0.7 and trace.plane.normal.z < 1.0):
            is_surfing = True

    return is_surfing, trace.plane.normal
