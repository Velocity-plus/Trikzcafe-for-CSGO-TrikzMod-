from entities.hooks import EntityPreHook
from entities.hooks import EntityCondition
from entities.entity import BaseEntity
from entities.helpers import index_from_pointer
from memory import make_object
from players.constants import PlayerStates
from mathlib import Vector, NULL_VECTOR
from .data import player_instances
from listeners.tick import RepeatStatus
from listeners.tick import Repeat
from .data import shared_path
from configobj import ConfigObj

SETTINGS  = ConfigObj(shared_path + 'settings.ini')

REPEATER_RATE = float(SETTINGS["AS_Refresh"]["RATE"])


@EntityPreHook(EntityCondition.is_player, 'start_touch')
def start_touch_func(args):
    # Get the parent of the entity
    base_entity0 = make_object(BaseEntity, args[0])
    if not base_entity0.is_player():
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
    target = player_instances[index_from_pointer(args[0])]

    target_max = Vector(32, 32, 72)
    player_max = Vector(32, 32, 72)
    if target.flags & PlayerStates.DUCKING:
        target_max = Vector(32, 32, 54)

    if player.flags & PlayerStates.DUCKING:
        player_max = Vector(32, 32, 54)

    if player.tick_ghost <= 0 and player.velocity == NULL_VECTOR or target.velocity == NULL_VECTOR:
        if box_in_solid(player.origin,
                        target.origin,
                        target_max,
                        player_max):
            player.is_stuck = True

            if not player.repeater_stuck:
                player.repeater_stuck = Repeat(check_stuck, args=(player, target), cancel_on_level_end=True)
                player.repeater_stuck.start(0.1)
            elif player.repeater_stuck.status & RepeatStatus.STOPPED:
                player.repeater_stuck = Repeat(check_stuck, args=(player, target), cancel_on_level_end=True)
                player.repeater_stuck.start(0.1)


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
        player.is_stuck = False
        player.repeater_stuck.stop()


def box_in_solid(box_1, box_2, d1, d2):
    s1 = abs(box_1.x + d1.x - (box_2.x + d2.x))
    s2 = abs(box_1.y + d1.y - (box_2.y + d2.y))
    s3 = abs(box_1.z - box_2.z)
    if s1 < d1.x and s2 < d1.y and s3 < d1.z and s3 < d2.z:
        return True
    else: return False
