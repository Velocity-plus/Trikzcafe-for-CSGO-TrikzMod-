from entities.hooks import EntityPreHook
from entities.hooks import EntityCondition
from entities.entity import BaseEntity
from entities.helpers import index_from_pointer
from memory import make_object
from players.constants import PlayerStates
from mathlib import Vector, NULL_VECTOR
from .tcore.instances import PLAYER
from entities.constants import CollisionGroup
from entities.constants import SolidType
from listeners.tick import RepeatStatus
from colors import Color
from listeners.tick import Repeat
from messages import SayText2
from .data import shared_path
from configobj import ConfigObj
SETTINGS = ConfigObj(shared_path + 'settings.ini')
C_1 = SETTINGS["Block_Ghost_Color"]["ghost"].split(",")
C_2 = SETTINGS["Block_Ghost_Color"]["block"].split(",")
COLOR_GHOST = Color(int(C_1[0]), int(C_1[1]), int(C_1[2]), int(C_1[3]))
COLOR_BLOCK = Color(int(C_2[0]), int(C_2[1]), int(C_2[2]), int(C_2[3]))
SETTINGS  = ConfigObj(shared_path + 'settings.ini')

REPEATER_RATE = float(SETTINGS["AS_Refresh"]["RATE"])


@EntityPreHook(EntityCondition.is_human_player, 'start_touch')
#@EntityPreHook(EntityCondition.is_human_player, 'touch')
def start_touch_func(args):
    # Get the parent of the entity
    index1 = index_from_pointer(args[0])
    index2 = index_from_pointer(args[1])

    if index2 not in PLAYER:
        return
    if index1 not in PLAYER:
        return

    target = PLAYER[index1]
    player = PLAYER[index2]

    target_max = Vector(32, 32, 72)
    player_max = Vector(32, 32, 72)
    if target.flags & PlayerStates.DUCKING:
        target_max = Vector(32, 32, 54)

    if player.flags & PlayerStates.DUCKING:
        player_max = Vector(32, 32, 54)

    if player.velocity.length == 0.0 or target.velocity.length == 0.0:
        if box_in_solid(player.origin,
                        target.origin,
                        target_max,
                        player_max):
            player.is_stuck = True
            a_toggle_ghost(player)
            a_toggle_ghost(target)

            if not player.repeater_stuck:
                player.repeater_stuck = Repeat(check_stuck, args=(player, target), cancel_on_level_end=True)
                player.repeater_stuck.start(0.1)
            elif player.repeater_stuck.status & RepeatStatus.STOPPED:
                player.repeater_stuck = Repeat(check_stuck, args=(player, target), cancel_on_level_end=True)
                player.repeater_stuck.start(0.1)


def a_toggle_block(player):
    player.collision_group = CollisionGroup.PLAYER
    player.solid_type = SolidType.BBOX
    player.color = COLOR_BLOCK

def a_toggle_ghost(player):
    player.collision_group = CollisionGroup.PLAYER
    player.solid_type = SolidType.NONE
    player.color = COLOR_GHOST

def check_stuck(player, target):
    target_max = Vector(32, 32, 72)
    player_max = Vector(32, 32, 72)
    if target.flags & PlayerStates.DUCKING:
        target_max = Vector(32, 32, 54)
    if player.flags & PlayerStates.DUCKING:
        player_max = Vector(32, 32, 54)
    if not box_in_solid(player.origin,
                        target.origin,
                        target_max,
                        player_max):

        if player.blocking:
            a_toggle_block(player)
        if target.blocking:
            a_toggle_block(target)
        player.is_stuck = False
        player.repeater_stuck.stop()


def box_in_solid(box_1, box_2, d1, d2):
    s1 = abs(box_1.x + d1.x - (box_2.x + d2.x))
    s2 = abs(box_1.y + d1.y - (box_2.y + d2.y))
    s3 = abs(box_1.z - box_2.z)
    if s1 < d1.x and s2 < d1.y and s3 < d1.z and s3 < d2.z:
        return True
    else: return False
