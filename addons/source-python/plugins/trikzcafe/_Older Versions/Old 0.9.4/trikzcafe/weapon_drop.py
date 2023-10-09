#   Entities
from entities.hooks import EntityCondition
from entities.hooks import EntityPostHook
#   Memory
from memory import make_object
#   Players
from players.entity import Player
#   Weapons
from weapons.entity import Weapon
from .tcore.instances import PLAYER
from .tcore.instances import WEAPON
from entities.helpers import index_from_pointer
from messages import SayText2
from players.helpers import index_from_userid

@EntityPostHook(EntityCondition.is_player, "drop_weapon")
def post_drop_weapon(args, return_value):
    index1 = index_from_pointer(args[0])
    if index1 not in PLAYER:
        return
    player = PLAYER[index1]
    player.dropped_weapons += 1

    index2 = index_from_pointer(args[1])
    weapon = WEAPON[index2]

    if player.dropped_weapons >= 4:
        weapon.remove_timer = weapon.delay(1, remove_weapon,args=(weapon,))
        if player.dropped_weapons_spam:
            player.dropped_weapons_spam.cancel()
        player.dropped_weapons_spam = player.delay(30, reset_drop, args=(player,))

    else:
        weapon.remove_timer = weapon.delay(120, remove_weapon,args=(weapon,))

def reset_drop(player):
    player.dropped_weapons_spam = None
    player.dropped_weapons = 0

def remove_weapon(weapon):
    weapon.remove_timer = None
    weapon.remove()

from events.hooks import EventAction, PreEvent

@PreEvent('item_pickup')
def _pre_pickup(game_event):
    item = game_event['item']
    player = PLAYER[index_from_userid(game_event['userid'])]

    primary = player.primary
    secondary = player.secondary
    if primary:
        if item in primary.classname:
            weapon = WEAPON[primary.index]
            if weapon.remove_timer:
                weapon.remove_timer.cancel()
    if secondary:
        if item in secondary.classname:
            weapon = WEAPON[secondary.index]
            if weapon.remove_timer:
                weapon.remove_timer.cancel()