from mathlib import NULL_VECTOR, NULL_QANGLE, Vector
from colors import Color
from players.entity import Player
from entities.entity import Entity
from players.dictionary import PlayerDictionary
from entities.dictionary import EntityDictionary
from weapons.dictionary import WeaponDictionary
from platform import system
from messages import SayText2
from time import time
from configobj import ConfigObj
from paths import ADDONS_PATH
from mathlib import NULL_VECTOR, NULL_QANGLE
from players.entity import Player
from entities.entity import Entity
from players.dictionary import PlayerDictionary
from entities.dictionary import EntityDictionary
from platform import system
from messages import SayText2
from players.constants import PlayerStates
from time import time
from configobj import ConfigObj
from paths import ADDONS_PATH
from engines.precache import Model
from entities.constants import SolidType
from entities.constants import EntityEffects
from entities.constants import CollisionGroup

SERVER_OS = system()
shared_path = ADDONS_PATH + '/TrikzCafePlugins/TrikzMod/'
SETTINGS  = ConfigObj(shared_path+'vip.ini')


VIP = SETTINGS["VIP"]["VIPS"].split(",")


class HitboxInstance(Entity):
    def __init__(self, index):
        super().__init__(index)
        self.identifier = None
        self.ghost = False
        self.ghost_delay = None


        self.ghost_quick_under_delay = None
        self.ghost_quick_over_delay = None

    @property
    def get_player(self):
        return self.parent.index


HITBOX = EntityDictionary(HitboxInstance)


class EntityInstance(Entity):
    def __init__(self, index):
        super().__init__(index)
        self.did_touch = False
        self.touches = 0
        # data


ENTITY = EntityDictionary(EntityInstance)

class WeaponInstance(Entity):
    def __init__(self, index):
        super().__init__(index)
        self.remove_timer = None
        # data


WEAPON = WeaponDictionary(WeaponInstance)



class PlayerInstance(Player):
    def __init__(self, index):
        super().__init__(index)
        self.auto_flash = 1
        self.auto_switch = 1
        self.auto_jump = 1
        self.blocking = 1
        self.has_pointer = self.pointer
        self.is_stuck = False
        self.boost_time = 0.0
        self.repeater_stuck = None
        self.repeater_runboost = None
        self.repeater_runboost_tick = 0
        self.checkpoints = {'cp_1': NULL_VECTOR,
                            'cp_1_velocity': NULL_VECTOR,
                            'cp_1_view_angle': NULL_QANGLE,
                            'cp_2': NULL_VECTOR,
                            'cp_2_velocity': NULL_VECTOR,
                            'cp_2_view_angle': NULL_QANGLE,
                            'cp_velocity_toggle': 0,
                            'cp_view_angle_toggle': 0}
        self.boost = {'angle': 0,
                      'velocity': NULL_VECTOR,
                      'amount': 0}

        self.boost_stats = {'enabled': 1,
                            'angle': 0,
                            'velocity': NULL_VECTOR,
                            'amount': 0,
                            'efficiency': 0,
                            'efficiency_avg': [],
                            'x': 0,
                            'type': 'None',
                            'hit': 'No'}
        self.test = {'height': 0,
                     'distance': 0,
                     'air': 0,
                     'msg': 0,
                     'origin': NULL_VECTOR,
                     'flash': 0,
                     'display': 0}

        self.display_speed = 1
        self.tick = 0
        self.tick_ghost = 0
        self.tick_adverts = 100
        self.slide_vel = NULL_VECTOR
        self.slide_bool = True
        self.boost_step = 1
        self.playerGroundLastTick = False
        self.playerVelLastTick = NULL_VECTOR
        self.playerVel = NULL_VECTOR
        self.flashVel = NULL_VECTOR
        self.flash_index = None
        self.skyVelBooster = NULL_VECTOR
        self.skyVelFlyer = NULL_VECTOR
        self.jumped = False
        self.jumping = False
        self.jumped_height = 0
        self.jumped_target_height = 0
        self.skyboost = False
        self.view_angle_p = NULL_QANGLE
        self.ticks = 0
        self.custom_delays = {'switch_knife': None,
                              'switch_flashbang': None,
                              'switch_fire': None}

        self.weapon_preference_pistol = "weapon_glock"
        self.weapon_preference_rifle = None
        self.weapon_preference_nades = None
        self.weapon_preference_knife = None
        self.is_grounded = False
        self.is_crouched = False
        self.is_grounded_timer = False
        self.friction_tick = 12
        self.friction_jump = False
        # Macro
        self.buttons_state = 0
        self.macro = 0
        self.start_attack = 0
        self.while_attack = 0
        self.end_attack = 1
        self.other_attack = 1
        self.weapon_fire = 0
        self.weapon_fire_2 = 0

        self.dropped_weapons_spam = None
        self.dropped_weapons = 0
        self.flash_x = 0
        # REGION PHASE
        self.hitbox_prop = EntityDictionary()
        self.hitbox_trigger = EntityDictionary()
        self.did_boost = False

        self.model_preference = None

    def region_get_location(self):
        self.region_valid_locations.append(self.origin)
        if self.flags & PlayerStates.ONGROUND or self.velocity.z == 0:
            self.region_repeater_get_location.stop()

    def Teleport(self, origin, angle, velocity):
        if SERVER_OS == 'Windows':
            self.teleport(origin, angle, velocity)
        else:
            self.delay(0, self.teleport, args=(origin, angle, velocity), cancel_on_level_end=True)

    def get_spectators(self, generator=None):
        """Return all players observing this player.

        :return:
            The generator yields :class:`players.entity.Player` objects.
        :rtype: generator
        """
        if generator is None:
            from filters.players import PlayerIter
            generator = PlayerIter('dead')

        for other in generator:
            if self.inthandle == other.observer_target:
                yield other

    @property
    def ducking(self):
        return self.flags & PlayerStates.DUCKING

    @property
    def on_ground(self):
        return self.flags & PlayerStates.ONGROUND

    @property
    def is_dead(self):
        return self.get_property_bool('pl.deadflag')

    @property
    def is_vip(self):
        if self.steamid in VIP:
            return True
        return False



PLAYER = PlayerDictionary(PlayerInstance)


def create_hitbox_prop(origin, model, mins, maxs, player, identifier, offset):
    player = PLAYER[player.index]
    hitbox = Entity.create('prop_dynamic_override')
    hitbox.set_parent(player, "H%s" % identifier)
    hitbox.model = Model('models/props/cs_assault/money.mdl')
    hitbox.effects |= EntityEffects.NODRAW

    hitbox.origin = Vector(origin.x, origin.y, origin.z + offset)
    hitbox.spawn_flags = 64
    hitbox.spawn()

    hitbox.mins = mins
    hitbox.maxs = maxs

    hitbox.solid_type = SolidType.BBOX
    hitbox.collision_group = CollisionGroup.DEBRIS_BLOCK_PROJECTILE
    hitbox.color = Color(0, 0, 0, 150)

    # How often can the 'trigger_multiple' be triggered? (0 - all the time)
    # hitbox.wait = 0
    hitbox = HITBOX[hitbox.index]
    hitbox.identifier = identifier
    phit = player.hitbox_prop[hitbox.index]


def create_hitbox_trigger(origin, model, mins, maxs, player, identifier, offset):
    player = PLAYER[player.index]
    hitbox = Entity.create('trigger_multiple')
    hitbox.set_parent(player, "H%s" % identifier)
    hitbox.model = Model('models/props/cs_assault/money.mdl')
    # Don't render the 'trigger_multiple'.
    # Without this the players' consoles will get spammed with this error:
    # ERROR:  Can't draw studio model models/props/cs_assault/money.mdl
    # because CBaseTrigger is not derived from C_BaseAnimating
    hitbox.effects |= EntityEffects.NODRAW
    ###
    hitbox.origin = Vector(origin.x, origin.y, origin.z + offset)
    # Enable collisions with everything (not including physics debris).
    # https://developer.valvesoftware.com/wik ... iple#Flags
    hitbox.spawn_flags = 64
    # Set the bounding box size.
    # Make sure the 'trigger_multiple' uses its bounding box for collision.
    hitbox.spawn()
    hitbox.mins = mins
    hitbox.maxs = maxs
    hitbox.solid_type = SolidType.BBOX
    # hitbox.render_mode = RenderMode.WORLD_GLOW
    # hitbox.move_type = MoveType.NOCLIP
    # hitbox.collision_group = CollisionGroup.DEBRIS_BLOCK_PROJECTILE
    # How often can the 'trigger_multiple' be triggered? (0 - all the time)
    # hitbox.wait = 0
    # Add the 'trigger_multiple' index to a dictionary.
    # (trigger_multiple index:player userid)
    hitbox = HITBOX[hitbox.index]
    hitbox.identifier = identifier
    phit = player.hitbox_trigger[hitbox.index]


def remove_all_hitbox():
    hitbox_indices = [index for index in HITBOX]
    for index in hitbox_indices:
        if index in hitbox_indices:
            HITBOX[index].remove()
    SayText2('Removed: %s' % len(HITBOX)).send()


def remove_hitbox_from_player(player):
    trigger_indices = [index for index in player.hitbox_trigger]
    for index in trigger_indices:
        player.hitbox_trigger[index].remove()

    prop_indices = [index for index in player.hitbox_prop]
    for index in prop_indices:
        player.hitbox_prop[index].remove()


def create_player_hitbox(player):
    create_hitbox_prop(
        origin=player.origin,
        model=player.model,
        mins=Vector(-19, -19, 0),
        maxs=Vector(19, 19, 8),
        player=player,
        offset=0,
        identifier="UNDER"
    )
    create_hitbox_prop(
        origin=player.origin,
        model=player.model,
        mins=Vector(-18, -18, 0),
        maxs=Vector(18, 18, 64),
        player=player,
        offset=8,
        identifier="OVER"
    )

    """
    create_hitbox_trigger(
        origin=player.origin,
        model=player.model,
        mins=Vector(-17, -17, 0),
        maxs=Vector(17, 17, 64),
        player=player,
        offset=8,
        identifier="BACKUP"

    )
    """