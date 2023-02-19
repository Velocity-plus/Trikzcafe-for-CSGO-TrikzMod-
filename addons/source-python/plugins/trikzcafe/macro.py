from entities.hooks import EntityCondition
from entities.hooks import EntityPreHook
from events import Event
from entities.helpers import index_from_pointer
from listeners import OnPlayerRunCommand
from players.constants import PlayerButtons
from players.helpers import index_from_userid
from memory import make_object
from players import UserCmd
from .tcore.instances import PLAYER
from messages import SayText2
from entities.entity import Entity


@OnPlayerRunCommand
def player_run_command(player, ucmd):
    player = PLAYER[player.index]
    if player.is_dead:
        return
    if player.macro:
        attack2 = ucmd.buttons & PlayerButtons.ATTACK2
        attack1 = ucmd.buttons & PlayerButtons.ATTACK
        if attack2:
            player.buttons_state = 0

        if attack2 and player.end_attack:
            # Block right click
            ucmd.buttons &= ~PlayerButtons.ATTACK2
            player.buttons_state = 0
            player.start_attack = 0
            player.while_attack = 2
            ForceAttack(player, ucmd, False)
            player.other_attack = 0

        if player.weapon_fire and player.while_attack != 2:
            player.while_attack = 1
            player.weapon_fire_2 = player.delay(0.08, StartJump, args=(player, ucmd), cancel_on_level_end=True)
            player.weapon_fire = 0

        if player.buttons_state == 3 and player.while_attack != 2:
            ForceJump(player, ucmd)
            player.buttons_state = 0
    jump = ucmd.buttons & PlayerButtons.JUMP
    if jump:
        player.jumping = True
    else:
        player.jumping = False


def ForceAttack(player, ucmd, jump=True):
    player.start_attack  = 0
    ucmd.buttons |= PlayerButtons.ATTACK
    player.while_attack  = 2
    try:
        if player.weapon_fire_2:
            player.weapon_fire_2.cancel()
    except ValueError:
        pass
    player.weapon_fire_2 = player.delay(0.2, StopAttack, args=(player, ucmd, jump), cancel_on_level_end=True)

def StopAttack(player, ucmd, jump):
    player.start_attack = 0
    player.while_attack = 0
    player.end_attack = 1
    player.buttons_state = 0
    ResetMacro(player)

def ForceJump(player, ucmd):
    ucmd.buttons |= PlayerButtons.JUMP


def reset_jump(player):
    player.jumped3 = False


def StartJump(player, ucmd):
    player.buttons_state = 3
    player.jumped3 = True
    player.delay(0.5, reset_jump, args=(player,))
    player.delay(0.1, ResetMacro, args=(player,), cancel_on_level_end=True)


def ResetMacro(player):
    player.while_attack = 0
    player.buttons_state = 0
    player.weapon_fire_2 = 0
    player.macro = 1


@Event('weapon_fire')
def _weapon_fire(game_event):
    userid = game_event['userid']
    player = PLAYER[index_from_userid(userid)]
    weapon = game_event['weapon']
    if weapon != 'weapon_flashbang':
        return

    if player.while_attack != 2:
        player.weapon_fire = 1
