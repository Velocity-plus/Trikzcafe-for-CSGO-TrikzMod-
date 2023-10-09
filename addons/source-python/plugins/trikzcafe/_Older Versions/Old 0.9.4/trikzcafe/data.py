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


gamedata = {}
SERVER_OS = system()
shared_path = ADDONS_PATH + '/TrikzCafePlugins/TrikzMod/'
SETTINGS  = ConfigObj(shared_path+'vip.ini')


VIP = SETTINGS["VIP"]["VIPS"].split(",")


class HitboxData(Entity):
    def __init__(self, index):
        super().__init__(index)
        self.name_id = ""
        self.player_owner = None


HITBOX = EntityDictionary(HitboxData)


class PlayerData(Player):
    def __init__(self, index):
        super().__init__(index)
        self.auto_flash = 1
        self.auto_switch = 1
        self.auto_jump = 1
        self.blocking = 1
        self.has_pointer = self.pointer
        self.is_stuck = False
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
                            'cp_view_angle_toggle': 1}
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
        self.test = {'height':0,
                     'distance':0,
                     'air':0,
                     'msg':0,
                     'origin':NULL_VECTOR,
                     'flash':0,
                     'display':0}

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
        self.custom_hitboxes = []
        self.ticks = 0
        self.custom_delays = {'switch_knife': None,
                              'switch_flashbang': None,
                              'switch_fire': None}

        self.weapon_preference_pistol = "weapon_glock"
        self.weapon_preference_rifle = None
        self.weapon_preference_nades = None
        self.weapon_preference_knife = None
        self.is_grounded = False
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
        # REGION PHASE
        self.partners = self.index
        self.realm = "Alpha"
        self.level = {'cooldown': time()}

    def region_get_location(self):
        self.region_valid_locations.append(self.origin)
        if self.flags & PlayerStates.ONGROUND or self.velocity.z == 0:
            self.region_repeater_get_location.stop()

    def Teleport(self, origin, angle, velocity):
        if SERVER_OS == 'Windows':
            self.teleport(origin, angle, velocity)
        else:
            self.delay(0, self.teleport, args=(origin, angle, velocity), cancel_on_level_end=True)

    @property
    def is_dead(self):
        return self.get_property_bool('pl.deadflag')

    @property
    def is_vip(self):
        return True


PLAYER = PlayerDictionary(PlayerData)
