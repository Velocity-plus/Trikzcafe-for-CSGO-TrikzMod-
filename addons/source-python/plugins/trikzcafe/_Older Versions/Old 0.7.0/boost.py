from mathlib import Vector, QAngle, NULL_VECTOR
from math import sqrt
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
from .data import player_instances
from .data import hitbox_instances
from .data import shared_path
from engines.precache import Model
from players import UserCmd
from players.constants import PlayerButtons
from players.helpers import index_from_userid
from time import time
from configobj import ConfigObj
import random
import string

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

# ======================================================
# => Dictionaries
# ======================================================
bbox_triggers = {}
hitbox_triggers = {}
server_data = {'tick': 0}
TRIGGER_MODEL = Model('models/hostage/hostage.mdl')


class EntityHandler(Entity):
    def __init__(self, index):
        super().__init__(index)
        self.did_touch = False
        self.touched = None
        self.pre_origin = None
        self.pre_time = time()
        self.pre_spawn_origin = self.origin


entity_instances = EntityDictionary(EntityHandler)


def unload():
    # Remove all custom bounding boxes when unloading the plugin.
    remove_all_hitbox_entities()


def remove_hitbox_entities(player):
    for hitbox_index in player.custom_hitboxes:
        if hitbox_index in hitbox_instances:
            hitbox = hitbox_instances[hitbox_index]
            hitbox.remove()
    player.custom_hitboxes = []


def remove_all_hitbox_entities():
    # Remove all custom bounding boxes when unloading the plugin.
    for player in player_instances.values():
        for hitbox_index in player.custom_hitboxes:
            hitbox = hitbox_instances[hitbox_index]
            hitbox.remove()
        player.custom_hitboxes = []


@EntityPreHook(EntityCondition.is_player, 'start_touch')
def start_touch_sky(args):
    # Get the parent of the entity
    try:
        base_entity0 = make_object(BaseEntity, args[0])
        if not base_entity0.is_player():
            return
    except:
        return

    parent_handle = base_entity0.parent_inthandle
    # Is the parent valid?

    if parent_handle != -1:
        # Get an Entity instance of the parent
        return

    base_entity1 = make_object(BaseEntity, args[1])
    if not base_entity1.is_player():
        return

    player = player_instances[index_from_pointer(args[1])]
    other = player_instances[index_from_pointer(args[0])]

    pOrigin = player.origin
    oOrigin = other.origin
    pVel = player.velocity
    oVel = other.velocity

    is_player_above = oOrigin.z - pOrigin.z - player.maxs.z

    if is_player_above > 0.0 and is_player_above < 2.0 and not other.skyboost:
        if pVel.z < 300 and pVel.z > 0.0 and not other.flags & PlayerStates.DUCKING and not other.is_grounded:
            if oVel.length_2D >= 750:
                pVel.z = 250

            other.skyVelBooster = player.velocity
            other.skyVelFlyer = other.velocity
            other.skyboost = True
            other.ticks = 0
            other.speed = 1.0

    if is_player_above > 0.0 and is_player_above < 2.0:
        if not other.skyboost or not other.boost_step == 0 and not other.jumping:
            if other.jumped:
                other.repeater_runboost_tick = 200
                other.speed = 0.64
                if not other.repeater_runboost:
                    other.repeater_runboost = Repeat(runboost_slow, args=(other, player), cancel_on_level_end=True)
                    other.repeater_runboost.start(0.001)

                elif other.repeater_runboost.status & RepeatStatus.STOPPED:
                    other.repeater_runboost = Repeat(runboost_slow, args=(other, player), cancel_on_level_end=True)
                    other.repeater_runboost.start(0.001)

            other.jumped = False


def runboost_slow(player, target):
    if player.skyboost or not player.boost_step == 0:
        player.repeater_runboost_tick = 0
        player.speed = 1
        player.repeater_runboost.stop()

    player.repeater_runboost_tick -= 1
    player.jumped_target_height = target.origin.z + 64

    if player.speed < 1.0:
        if player.jumped_height <= player.jumped_target_height:
            player.speed += 0.003263
        else:
            player.speed += 0.005312

    if player.speed >= 1:
        player.speed = 1
        player.repeater_runboost.stop()

    if player.repeater_runboost_tick <= 0:
        player.repeater_runboost.stop()


@EntityPreHook(EntityCondition.equals_entity_classname('trigger_multiple'), 'start_touch')
def start_touch_func(args):
    try:
        hitbox = make_object(BaseEntity, args[0])
    except:
        return
    try:
        flash = make_object(BaseEntity, args[1])
    except:
        return
    if 'flashbang_projectile' not in flash.classname:
        return

    flash_index = flash.index
    hitbox_index = hitbox.index
    if hitbox_index not in hitbox_instances:
        return
    hitbox = hitbox_instances[hitbox.index]
    flash = entity_instances[flash_index]
    hitbox_owner = hitbox.parent.index
    flash_owner = flash.owner.index
    if hitbox_owner == flash_owner:
        return

    if flash.did_touch:
        return

    player = player_instances[hitbox_owner]
    flasher = player_instances[flash_owner]

    if player.realm != flasher.realm:
        flash.did_touch = False
        return
    player_pos = player.origin

    player_vel = player.velocity

    d = flasher.boost['amount'].z * ((time() - flasher.boost['time']) * 0.30)
    # SayText2('Added time: %s' % (round(d ,2))).send()
    flasher.boost['amount'].z = flasher.boost['amount'].z - d
    boost_vector = flasher.boost['amount']
    hitbox_height = hitbox.maxs.z

    flash_over_player = (10 + hitbox.origin.z - flash.origin.z) <= 0 and hitbox_height >= 20
    if not player.is_grounded and hitbox_height <= 20:
        flash.did_touch = True
        player.speed = 1
        player.playerVel = player_vel
        player.flashVel = boost_vector
        player.boost_step = 1
        flash.touched = player.index
        player.boost_stats['hit'] = 'Yes'

    if not player.is_grounded and hitbox_height <= 20:
        flash.did_touch = True
        player.speed = 1
        player.playerVel = player_vel
        player.flashVel = boost_vector
        player.boost_step = 1
        flash.touched = player.index
        player.boost_stats['hit'] = 'Yes'

    if flash_over_player:
        flash.did_touch = True
        pVel = player.velocity.normalized() * 10
        fVel = flash.velocity.normalized() * 10

        check_x = 0
        check_y = 0
        if pVel[0] > 0 and fVel[0] < 0 or pVel[0] < 0 and fVel[0] > 0:
            check_y = 1

        if pVel[1] > 0 and fVel[1] < 0 or pVel[1] < 0 and fVel[1] > 0:
            check_x = 1

        if check_x and check_y:
            player.teleport(None, None, Vector(0, 0, player.velocity[2]))

    player_pos.z += player.maxs.z / 2

    flash_sound = random.choice(MimicSound_Flashbang)
    flash_sound.index = player.index

    flash_sound.play()

    if player_vel.z <= -700:
        fall_sound = random.choice(MimicSound_Falldamage)
        fall_sound.index = player.index
        fall_sound.play()

    # First pass at calculating the custom bounding box normal.
    # If you were to use this, it would act more like a cylinder and not a box.
    if flash_over_player:
        normal = flash.origin - player_pos
        normal.normalize()
        # Second and final pass at calculating the normal, this one should work.
        # Subtract the normalized projectile velocity from the normal to get
        # more pronounced values. Maybe I'm overthinking this?
        final_normal = get_box_normal(normal - flash.velocity.normalized())

        # Calculate the direction / velocity of the bouncing projectile.
        bounce_direction = final_normal * final_normal.dot(flash.velocity) * 2
        bounce_velocity = flash.velocity - bounce_direction
        # Decrease the velocity of the projectile by 45%.
        bounce_velocity.length = flash.velocity.length * 0.34
        # Add the new velocity to the projectile.
        flash.teleport(None, None, bounce_velocity)
    flash.delay(0.25, flash.remove, cancel_on_level_end=True)


@EntityPostHook(EntityCondition.is_player, 'post_think')
def pre_post_think(stack_data, a):
    player = player_instances[index_from_pointer(stack_data[0])]
    # Is the player dead or a spectator?
    if player.is_dead:
        return
    if not player.custom_hitboxes:
        return
    if player.flags & PlayerStates.ONGROUND:
        if not player.is_grounded and not player.is_grounded_timer:
            player.delay(0.48, change_state_grounded, args=(player, True), cancel_on_level_end=True)
            player.is_grounded_timer = True

    else:
        player.is_grounded = False
        player.is_grounded_timer = False
    if player.boost_step == 1:
        boost_vec = Vector(player.flashVel.x * 0.135, player.flashVel.y * 0.135, player.flashVel.z * -0.135)
        for ent in entity_instances.values():
            if ent.touched == player.index:
                ent.teleport(None, None, boost_vec)
        player.boost_step = 2


def change_state_grounded(player, state):
    player.is_grounded = state


class Boost_Threading:
    def __init__(self):
        self.index = None
        self.repeater = None
        self.thread = None

    def _threader(self):
        try:
            for player in player_instances.values():
                if not player.is_dead:
                    efficiency_avg = average(player.boost_stats['efficiency_avg'])

                    if player.boost_stats['enabled']:
                        efficiency = player.boost_stats['efficiency']
                        angle = player.boost_stats['angle']
                        velocity = player.boost_stats['velocity']
                        amount = player.boost_stats['amount']
                        x = player.boost_stats['x']
                        boost_type = player.boost_stats['type']
                        hit = player.boost_stats['hit']

                        color_1 = "#FF0000"
                        if hit == 'Yes':
                            color_1 = "#17d817"

                        color_progress = ['#FF0909', '#FF2E09', '#FF5309', '#FF6C09', '#FFB709', '#FFCF09', '#FFE809',
                                          '#FFE809', '#09FF32', '#09FF32']
                        try:
                            eff = int(efficiency / 10) - 1
                            if eff < 0 or eff > 9:
                                eff = 0
                                efficiency = "-.--"

                            eff_2 = int(efficiency_avg / 10) - 1
                            if eff_2 < 0 or eff_2 > 9:
                                eff_2 = 0

                            color_choice = color_progress[eff]
                            color_choice_2 = color_progress[eff_2]
                            if not eff:
                                color_choice = "#004A83"
                        except IndexError:
                            color_choice = color_progress[5]
                            color_choice_2 = color_progress[5]

                        speed = str(round(player.velocity.length_2D, 1))

                        HintText('Efficiency: {0}%\n'
                                 '(avg: {7}%)\n'
                                 'Speed: {10}\n'
                                 'Angle: {6}\n'.format(
                            efficiency,
                            velocity.length_2D,
                            x,
                            boost_type,
                            hit,
                            color_1,
                            angle,
                            efficiency_avg,
                            color_choice,
                            color_choice_2,
                            speed)).send(player.index)
                        for spec in player.spectators:
                            spec.realm = player.realm

        except ValueError:
            SayText2('Correcting errors').send()

    def repeat_thread(self):
        self.repeater = Repeat(self._threader, cancel_on_level_end=True)
        self.repeater.start(0.1)

    def start_thread(self):
        # Creates the thread
        self.thread = GameThread(target=self.repeat_thread)
        self.thread.daemon = True
        self.thread.start()


boost_thread = Boost_Threading()


def average(eff_list):
    length = len(eff_list)
    if length > 0:
        n = 0
        for object in eff_list:
            n += object

        n = n / length
        return round(n, 1)
    else:
        return 0


def closeplayer(player, radius):
    for other in player_instances.values():
        if not player.index == other.index and not other.is_dead:
            dist = player.origin.get_distance(other.origin)
            if dist <= radius:
                return dist, other

    return 10000, None


def cal_distance(x, y):
    return abs(x - y)


@EntityPreHook(EntityCondition.is_player, 'run_command')
def player_run_command(args):
    player = player_instances[index_from_pointer(args[0])]
    if not player.is_dead:
        cmd = make_object(UserCmd, args[1])

        if player.flags & PlayerStates.ONGROUND:
            if player.test['msg'] == 0 and (player.test['height'] > 63 or player.test['distance'] >= 240):
                player.test['msg'] = 1
                ox, oy, oz = player.test['origin']
                nx, ny, nz = player.origin
                distance = Vector(ox, oy, 0).get_distance(Vector(nx, ny, 0)) + 32
                #SayText2('Name: %s > Height: %s, Dist: %s' % (player.name, round(player.test['height'],1), round(distance, 1))).send()
            player.test['height'] = 0
            player.test['origin'] = player.origin
        else:
            player.test['msg'] = 0
            player.test['air'] = 1
            ox,oy,oz = player.test['origin']
            nx,ny,nz = player.origin
            height = Vector(0,0,oz).get_distance(Vector(0,0,nz))
            if dist > player.test['height']:
                player.test['height'] = dist






        if player.boost_step == 0 and not player.skyboost:
            is_surfing, plane_normal = is_player_surfing(player)
            if is_surfing and player.flags & PlayerStates.ONGROUND and not player.playerGroundLastTick:

                #SayText2("Slope fix").send()
                vLast = player.playerVelLastTick
                vLast[2] -= float(ConVar("sv_gravity")) * (1 / 128) * 0.5

                fBackOff = vLast.dot(plane_normal)

                change = 0
                vVel = Vector(0, 0, 0)
                for i in range(2):
                    change = plane_normal[i] * fBackOff
                    vVel[i] = vLast[i] - change

                fAdjust = vVel.dot(plane_normal)

                if (fAdjust < 0.0):
                    for i in range(2):
                        vVel[i] -= (plane_normal[i] * fAdjust)

                vVel[2] = 0
                vLast[2] = 0

                if (vVel.length > vLast.length):
                    if player.flags & EntityStates.BASEVELOCITY:
                        vVel += player.base_velocity

                    player.teleport(None, None, vVel)


        if player.boost_step == 0 and player.skyboost:
            bVel = player.skyVelBooster
            fVel = player.skyVelFlyer

            boost_z = calculate_sky_boost(bVel.z) + (fVel.length_2D * 0.2072)
            if boost_z >= 865:
                boost_z = 865
            boost_vec = Vector(fVel.x, fVel.y, boost_z)

            player.teleport(None, None, boost_vec)
            player.skyboost = False

        if player.boost_step == 2:
            flashVel = player.flashVel
            playerVel = player.playerVel
            boost_vec = Vector(playerVel.x - flashVel.x, playerVel.y - flashVel.y, flashVel.z)
            player.teleport(None, None, boost_vec)
            player.boost_step = 3

        elif player.boost_step == 3:
            flashVel = player.flashVel
            playerVel = player.velocity
            boost_vec = Vector(playerVel.x + (flashVel.x * 0.1350), playerVel.y + (flashVel.y * 0.1350), playerVel.z)

            player.teleport(None, None, boost_vec)
            player.boost_step = 0

        if player.flags & PlayerStates.ONGROUND and player.flags & PlayerStates.DUCKING and player.friction_jump:
            if not cmd.buttons & PlayerButtons.JUMP:

                if player.friction_tick >= 8:
                    player.teleport(None, None, player.velocity * 0.82)
                if player.friction_tick >= 0:
                    player.set_property_float('cslocaldata.m_flStamina', player.friction_tick)

                    player.friction_tick -= 1
                else:
                    player.friction_jump = False
        else:
            player.friction_tick = 14



        player.playerVelLastTick = player.velocity
        player.playerGroundLastTick =  player.flags & PlayerStates.ONGROUND


@OnLevelEnd
def on_level_end():
    # Remove all custom bounding boxes when changing map
    try:
        for player in player_instances.values():
            player.custom_hitboxes = []
    except ValueError:
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


@Event('weapon_fire')
def _weapon_fire(game_event):
    weapon = game_event['weapon']
    if weapon != 'weapon_flashbang':
        return


ent_track = {'index': 0,
             'velocity': 0,
             'origin': 0,
             'origin_now': 0,
             'height': 0,
             'tick_spawn': 0,
             'tick_velocity': 0,
             'tick_height': 0,
             'msg': 0,
             'falling': 0,
             'angle': 20}


@OnTick
def on_tick():
    if ent_track['index'] in entity_instances:
        ent = entity_instances[ent_track['index']]

        if ent_track['msg'] == 0:
            norm_2D = ent.velocity.length_2D
            ent_track['origin'] = ent.origin.z
            # SayText2("Velocity XY: %s" % norm_2D).send()
            # SayText2("Angle: %s" % ent.get_view_angle()).send()
            # SayText2("Velocity XYZ: %s" % ent.velocity.length).send()
            # SayText2('Tick Now: %s vs Tick Spawn %s' % (server.tick, ent_track['tick_spawn'])).send()
            # SayText2('Distance: %s' % str(cal_distance(ent_track['origin_now'], ent.origin.z))).send()
            # SayText2('Now: %s' % str(ent.origin.z)).send()
            ent_track['msg'] = 1

        dist = cal_distance(ent_track['origin'], ent.origin.z)
        if ent.origin.z > ent_track['origin']:
            ent_track['height'] = dist
            ent_track['origin_now'] = ent.origin.z
            ent_track['tick_height'] = server.tick
    else:
        if ent_track['height'] != 0:
            # SayText2('Max height: %s' % ent_track['height']).send()
            pass
        ent_track['msg'] = 0
        ent_track['height'] = 0
        ent_track['velocity'] = 0
        ent_track['origin'] = 0
        ent_track['origin_now'] = 0
        ent_track['tick_spawn'] = 0
        ent_track['falling'] = 0


# 20 degress : Velocity XY: 597.2142333984375
# 30 degress : Velocity XY: 541.4331665039062
# 40 degrees : Velocity XY: 472.6466979980469
# 50 degrees : Velocity XY: 392.5072326660156
# 60 degrees : Velocity XY: 302.939453125
# 70 degrees : Velocity XY: 206.09503173828125
# 80 degrees : Velocity XY: 104.30016326904297

@OnEntitySpawned
def spawned(base_entity):
    if base_entity.classname == "flashbang_projectile":
        ent = entity_instances[base_entity.index]
        ent_track['index'] = base_entity.index
        ent_track['tick_spawn'] = server.tick
        player = player_instances[ent.owner.index]
        player_angle = abs(player.get_view_angle().x)
        player_full_angle = player.get_view_angle()
        # SayText2(str(player_full_angle)).send()
        # player.teleport(player.origin, QAngle(-15, player_full_angle.y, player_full_angle.z), Vector(0,0,0))
        player_vel = player.velocity
        player_vel_xy = player.velocity.length_2D
        entity_vel = ent.velocity
        ent.delay(1.4, ent.remove, cancel_on_level_end=True)
        ent.delay(0, get_flash_vel, args=(ent, entity_vel, player_angle, player_vel_xy, player, player_vel),
                  cancel_on_level_end=True)


BOOST_MAX_FORWARD = int(SETTINGS["Boost_Properties"]["MAX_FORWARD"])
BOOST_MAX_HEIGHT = int(SETTINGS["Boost_Properties"]["MAX_HEIGHT"])
BOOST_MIN_HEIGHT = int(SETTINGS["Boost_Properties"]["MIN_HEIGHT"])
BOOST_MAX_JUMP_SPEED = int(SETTINGS["Boost_Properties"]["JUMP_SPEED"])
BOOST_EFFICIENCY_COEF = 100 / BOOST_MAX_JUMP_SPEED
BOOST_EFFICIENCY_HELPER = 1.04
BOOST_TIME_POWER = (BOOST_MAX_HEIGHT - BOOST_MIN_HEIGHT) / 2


def calculate_sky_boost(x):
    if x > 300:
        x = 300
    boost = 0.383139126937465e-4 * x ** 3 - 0.105106488752637e-1 * x ** 2 + 1.26257372918474 * x + 397.842857797988

    return boost


def calculate_boost_height(x):
    boost = 4.74865523472641 * 10 ** (
        -9) * x ** 6 - 0.164481346798051e-5 * x ** 5 + 0.221663993562309e-3 * x ** 4 - 0.146542081194908e-1 * x ** 3 + .408309732177254 * x ** 2 + 7.34990410595208 * x + 108.736721968420

    return boost


def calculate_boost_forward(x):
    boost = 1.34594917120970 * 10 ** (
        -8) * x ** 6 - 0.410942701971319e-5 * x ** 5 + 0.477533119489353e-3 * x ** 4 - 0.250315025042308e-1 * x ** 3 + .425269812125225 * x ** 2 - .107563916437797 * x + 596.599847796541

    return boost


def get_flash_vel(ent, entity_vel, player_angle, player_vel_xy, player, player_vel):
    forward = calculate_boost_forward(player_angle) + player_vel_xy
    height = calculate_boost_height(player_angle) + player_vel.z
    ent_vel = ent.velocity
    norm_2D = ent_vel.length_2D
    norm = Vector(ent_vel.x / norm_2D, ent_vel.y / norm_2D, 1)
    path = Vector(norm.x * forward, norm.y * forward, height)

    player.boost['angle'] = player_angle
    player.boost['velocity'] = player.velocity
    player.boost['amount'] = path
    player.boost['time'] = time()
    # 626, 17.9

    # x = "Mine: %s, %s, %s" % (round(path.x, 1),round(path.y, 1),round(path.z, 1))
    # y = "Enge: %s, %s, %s"% (round(ent.velocity.x, 1),round(ent.velocity.y, 1),round(ent.velocity.z, 1))
    efficiency = abs(round(BOOST_EFFICIENCY_COEF * player_vel.z, 1))
    if efficiency >= 100:
        efficiency = 100

    player.boost['angle'] = player_angle
    player.boost['velocity'] = player.velocity
    player.boost['amount'] = path
    player.boost['time'] = time()
    player.boost['efficiency'] = efficiency

    player.boost_stats['angle'] = round(player_angle, 1)
    player.boost_stats['amount'] = path

    if player_angle >= 80:
        player.boost_stats['type'] = 'MH'
    elif 30 <= player_angle < 80:
        player.boost_stats['type'] = 'ML Mid'
    elif player_angle < 30:
        player.boost_stats['type'] = 'ML Low'

    if player.velocity.z <= 100:
        player.boost_stats['type'] = player.boost_stats['type'].replace('ML', 'Normal').replace('MH', 'Normal High')

    player.boost_stats['efficiency'] = efficiency
    if player_vel.z > 10:
        player.boost_stats['efficiency_avg'].append(round(BOOST_EFFICIENCY_COEF * player_vel.z, 1))


@Event('player_death', 'player_team', 'player_disconnect')
def events_for_removal(event):
    userid = event['userid']
    try:
        player = player_instances.from_userid(userid)
        # Does the player have a custom bounding box?
        remove_hitbox_entities(player)
    except ValueError:
        return


@Event("player_spawn")
def OnSpawn(game_event):
    userid = game_event['userid']
    try:
        player = player_instances[index_from_userid(userid)]
    except ValueError:
        return

    if not player.is_player() and not player.is_dead:
        return

    for x in range(2):
        if x >= 1:
            create_hitbox(
                origin=player.origin,
                model=player.model,
                mins=Vector(-17, -17, 0.0),
                maxs=Vector(17, 17, 8),
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


def create_hitbox(origin, model, mins, maxs, player, return_entity=False, delta=2):
    hitbox = Entity.create('trigger_multiple')
    hitbox.set_parent(player, -1)
    hitbox.model = player.model
    # Don't render the 'trigger_multiple'.
    # Without this the players' consoles will get spammed with this error:
    # ERROR:  Can't draw studio model models/props/cs_assault/money.mdl
    # because CBaseTrigger is not derived from C_BaseAnimating
    hitbox.effects |= EntityEffects.NODRAW
    hitbox.origin = Vector(origin.x, origin.y, origin.z - delta)
    # Enable collisions with everything (not including physics debris).
    # https://developer.valvesoftware.com/wik ... iple#Flags
    hitbox.spawn_flags = 8
    # Set the bounding box size.
    # Make sure the 'trigger_multiple' uses its bounding box for collision.
    hitbox.spawn()
    hitbox.mins = mins
    hitbox.maxs = maxs
    hitbox.solid_type = SolidType.BBOX
    # hitbox.collision_group = CollisionGroup.DEBRIS_BLOCK_PROJECTILE
    # How often can the 'trigger_multiple' be triggered? (0 - all the time)
    hitbox.wait = 0
    # Add the 'trigger_multiple' index to a dictionary.
    # (trigger_multiple index:player userid)
    hitbox_index = hitbox.index
    hitbox = hitbox_instances[hitbox_index]
    hitbox.player_owner = player.index
    hitbox.name_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    # Does the player already have a custom bounding box?
    player.custom_hitboxes.append(hitbox_index)

    if return_entity:
        return hitbox


@Event("player_jump")
def OnJump(game_event):
    userid = game_event['userid']
    player = player_instances[index_from_userid(userid)]
    base_vel = player.base_velocity
    player.jumped_height = player.origin.z
    target_info = closeplayer(player, radius=156)
    if target_info[0] <= 156:
        target = target_info[1]
        if target.flags & PlayerStates.DUCKING:
            if target.origin.z <= player.jumped_height:
                player.base_velocity = Vector(base_vel.x, base_vel.y, base_vel.z + 22)
                player.jumped = True

        else:
            player.base_velocity = Vector(base_vel.x, base_vel.y, base_vel.z + 24)
            player.jumped = True
        player.speed = 1.0
    player.friction_jump = True


from entities.hooks import EntityCondition
from entities.hooks import EntityPreHook
from core import PLATFORM
from core import SOURCE_ENGINE
from memory import Convention, DataType


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
    victim = make_object(Player, stack_data[0])
    damage_info = make_object(TakeDamageInfo, stack_data[1])
    attacker = Player(damage_info.attacker)
    attacker_weapon = attacker.active_weapon.classname
    damage = damage_info.damage
    xvv, yvv, zvv = victim.velocity
    xva, yva, zva = attacker.velocity

    xa, ya, za = attacker.view_angle
    xnv, ynv, znv = Vector(xva, yva, 0).normalized()
    default_boost_knife = Vector((525 * xnv), (525 * ynv), 350) + Vector(xva * 1.325, yva * 1.325, 0)
    # SayText2(str(damage_info.damage)).send()
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
            switch(player_instances[attacker.index], "weapon_flashbang")
            WeaponSwitch(player_instances[attacker.index], "weapon_flashbang")


def switch(player, weapon):
    if not player.is_dead:
        player.client_command('use %s' % weapon, server_side=True)


def WeaponSwitch(player, weapon):
    if not player.is_dead:
        if weapon == 'weapon_flashbang':
            player.set_property_float('m_flNextAttack', 1.0)
            player.set_property_bool('m_bWaitForNoAttack', False)


from cvars import ConVar
from engines.trace import ContentMasks
from engines.trace import GameTrace
from engines.trace import Ray
from engines.trace import TraceFilterSimple
from engines.trace import engine_trace
from listeners import OnPlayerRunCommand
from mathlib import Vector

sv_maxvelocity = ConVar("sv_maxvelocity")


def is_player_surfing(player):
    origin = player.origin

    destination = Vector(origin.x, origin.y, origin.z - sv_maxvelocity.get_int())

    trace = GameTrace()

    engine_trace.trace_ray(
        Ray(origin, destination, player.mins, player.maxs),
        ContentMasks.PLAYER_SOLID_BRUSH_ONLY,
        TraceFilterSimple((player,)),
        trace,
    )

    is_surfing = False

    if trace.did_hit():
        # Sometimes I'm getting 0.00048828125, mostly 0.0
        destination_distance = trace.end_position.get_distance(origin)
        #SayText2(str(trace.plane.normal.z)).send()
        #SayText2(str(trace.plane.normal.z)).send(player.index)
        if (destination_distance <= 1 and trace.plane.normal.z >= 0.7 and trace.plane.normal.z < 1.0):

            is_surfing = True

    return is_surfing, trace.plane.normal
