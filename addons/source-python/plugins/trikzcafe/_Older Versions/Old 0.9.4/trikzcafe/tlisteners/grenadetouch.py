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
from engines.trace import ContentMasks
from engines.trace import GameTrace
from engines.trace import Ray
from engines.trace import TraceFilterSimple
from engines.trace import engine_trace
__all__ = (
    'OnPlayerGrenadeTouch',
    'OnPlayerGrenadeTouchUnder'
    'OnPlayerGrenadeBlock'
    )


class OnPlayerGrenadeTouch(ListenerManagerDecorator):
    """Register/unregister a OnPlayerGrenadeTouch listener."""
    manager = ListenerManager()


class OnPlayerGrenadeTouchUnder(ListenerManagerDecorator):
    """Register/unregister a OnPlayerGrenadeTouch listener."""
    manager = ListenerManager()


class OnPlayerGrenadeBlock(ListenerManagerDecorator):
    manager = ListenerManager()


@EntityPreHook(EntityCondition.equals_entity_classname('prop_dynamic_override'), 'start_touch')
#@EntityPreHook(EntityCondition.equals_entity_classname('prop_dynamic_override'), 'touch')
def on_player_grenade_block(args):
    index1 = index_from_pointer(args[0])
    index2 = index_from_pointer(args[1])

    if index2 not in ENTITY:
        return

    grenade = ENTITY[index2]


    if index1 in HITBOX:

        hitbox = HITBOX[index1]
        player = PLAYER[hitbox.parent.index]

        if hitbox.parent.index == grenade.owner.index:
            return

        height_difference = grenade.origin.z - hitbox.origin.z
        if height_difference <= 2:
            return
        #destination = Vector(origin.x, origin.y, origin.z)

        trace = GameTrace()

        engine_trace.trace_ray(
            Ray(grenade.origin, grenade.origin + (grenade.velocity.normalized() * 5), Vector(-2,-2,0), Vector(2,2,4)),
            ContentMasks.ALL,
            TraceFilterSimple((player, grenade)),
            trace,
        )

        if trace.did_hit():
            direction = trace.plane.normal

            p_direction = player.velocity.normalized()
            vel = player.velocity
            stop_dir = direction.dot(p_direction)
            #2("Dot: %s" % round(stop_dir,2)).send()
            if stop_dir >= 0.0 and vel.length > 0.0:
                #SayText2('Stop player').send()
                velocity = NULL_VECTOR
                velocity.z = player.velocity.z * 0.5
                player.teleport(None, None, velocity)
                grenade.remove()


@EntityPreHook(EntityCondition.equals_entity_classname('prop_dynamic_override'), 'touch')
def no_self_touch(args):
    index1 = index_from_pointer(args[0])
    index2 = index_from_pointer(args[1])

    if index2 not in ENTITY:
        return

    grenade = ENTITY[index2]

    if index1 in HITBOX:
        hitbox = HITBOX[index1]
        if grenade.owner.index == hitbox.parent.index:
            prevent_self_touch(hitbox)
            return


def prevent_self_touch(hitbox):
    if hitbox == "UNDER":
        if not hitbox.ghost:

            if hitbox.ghost_delay:
                hitbox.ghost_delay.cancel()

            hitbox.collision_group = CollisionGroup.DEBRIS
            hitbox.ghost = True
            hitbox.ghost_delay = hitbox.delay(0.1, change_collision, args=(hitbox, True), cancel_on_level_end=True)

        else:
            if hitbox.ghost_delay:
                hitbox.ghost_delay.cancel()

            hitbox.collision_group = CollisionGroup.DEBRIS
            hitbox.ghost = True
            hitbox.ghost_delay = hitbox.delay(0.1, change_collision, args=(hitbox, True), cancel_on_level_end=True)


def change_collision(hitbox, player):
    hitbox.ghost_delay = None
    hitbox.collision_group = CollisionGroup.DEBRIS_BLOCK_PROJECTILE
    hitbox.ghost = False



@EntityPreHook(EntityCondition.is_human_player, 'start_touch')
@EntityPreHook(EntityCondition.equals_entity_classname('trigger_multiple'), 'start_touch')
@EntityPreHook(EntityCondition.equals_entity_classname('prop_dynamic_override'), 'start_touch')
def start_touch_func(args):
    # Hitbox Arg 0
    # Flashbang Arg 1
    index1 = index_from_pointer(args[0])
    index2 = index_from_pointer(args[1])

    if index2 not in ENTITY:
        return

    grenade = ENTITY[index2]

    # Touched
    did_touch = grenade.did_touch

    # Prevent crashes
    grenade.touches += 1
    grenade_velocity = grenade.velocity
    if grenade.touches >= 9:
        grenade.remove()
        return

    if index1 in HITBOX:
        hitbox = HITBOX[index1]
        self_touch = False
        if grenade.owner.index == hitbox.parent.index:
            prevent_self_touch(hitbox)
            self_touch = True

        OnPlayerGrenadeTouch.manager.notify(hitbox, grenade, self_touch, did_touch)
        _on_player_touch_under_check(hitbox, grenade, self_touch, did_touch)

        if grenade.owner.index != hitbox.parent.index:
            grenade.did_touch = True
        return

    if index1 in PLAYER:
        player = PLAYER[index1]
        self_touch = False
        if grenade.owner.index == player.index:
            self_touch = True
        OnPlayerGrenadeTouch.manager.notify(player, grenade, self_touch, did_touch)
        _on_player_touch_under_check(player, grenade, self_touch, did_touch)

        if grenade.owner.index != player.index:
            grenade.did_touch = True


def _on_player_touch_under_check(entity, grenade, self_touch, did_touch):
    height_difference = grenade.origin.z - entity.origin.z
    if not did_touch:
        """
        if entity.classname == "prop_dynamic":
            if grenade.owner.index != entity.parent.index:
                SayText2('[P]: %s' % round(height_difference,2)).send()
        elif entity.classname == "trigger_multiple":
            if grenade.owner.index != entity.parent.index:
                SayText2('<T>: %s' % round(height_difference,2)).send()
        else:
            if grenade.owner.index != entity.index:
                SayText2('!C!: %s' % round(height_difference, 2)).send()
        """
    if height_difference <= 2:
        OnPlayerGrenadeTouchUnder.manager.notify(entity, grenade, self_touch, did_touch)





