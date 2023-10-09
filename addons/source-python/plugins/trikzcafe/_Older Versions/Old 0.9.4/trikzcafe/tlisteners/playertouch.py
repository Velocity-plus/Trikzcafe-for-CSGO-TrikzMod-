from entities.hooks import EntityCondition
from mathlib import NULL_VECTOR, Vector
from entities.helpers import index_from_pointer
from entities.hooks import EntityPreHook
from entities.entity import BaseEntity, Entity
from listeners.tick import Delay
from listeners import ListenerManager
from listeners import ListenerManagerDecorator
from trikzcafe.tcore.instances import HITBOX
from trikzcafe.tcore.instances import ENTITY
from trikzcafe.tcore.instances import PLAYER
from messages import SayText2
from colors import Color
from entities.constants import SolidType
from entities.constants import MoveType
from entities.constants import EntityEffects
from entities.constants import RenderEffects, RenderMode
from engines.precache import Model
from entities.constants import CollisionGroup
from filters.players import PlayerIter
__all__ = (
    'OnPlayerOnTop',
    'OnPlayerSky',
    )


class OnPlayerOnTop(ListenerManagerDecorator):
    """Register/unregister a OnPlayerOnTop listener."""
    manager = ListenerManager()

class OnPlayerSky(ListenerManagerDecorator):
    """Register/unregister a OnPlayerOnTop listener."""
    manager = ListenerManager()


@EntityPreHook(EntityCondition.is_human_player, 'start_touch')
@EntityPreHook(EntityCondition.is_human_player, 'touch')
def start_touch_func(args):
    index1 = index_from_pointer(args[0])
    index2 = index_from_pointer(args[1])

    if index1 not in PLAYER:
        return
    if index2 not in PLAYER:
        return

    p1 = PLAYER[index_from_pointer(args[1])]
    p2 = PLAYER[index_from_pointer(args[0])]

    p_up = p1
    p_down = p2
    if p_up.origin.z < p_down.origin.z:
        p_up = p2
        p_down = p1

    p_up_org = p_up.origin
    p_down_org = p_down.origin

    is_player_above = p_up_org.z - p_down_org.z - p_down.maxs.z
    if is_player_above >= 0.0 and not p_up.skyboost and not p_up.is_grounded:
        if not p_up.ducking and p_down.velocity.z > 0.0 and not p_up.boost_step > 0 and p_up.velocity.z < 0.0:
            OnPlayerSky.manager.notify(p_up, p_down)

    if is_player_above >= 0.0 and p_up.on_ground:
        OnPlayerOnTop.manager.notify(p_up, p_down)



