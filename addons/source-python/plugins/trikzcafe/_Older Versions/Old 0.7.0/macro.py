from entities.hooks import EntityCondition
from entities.hooks import EntityPreHook
from events import Event
from entities.helpers import index_from_pointer
from players.constants import PlayerButtons
from players.helpers import index_from_userid
from memory import make_object
from players import UserCmd
from .data import player_instances



server = {'start_attack':0, 'end_attack':1, 'while_attack':0, 'other_attack':1}

@EntityPreHook(EntityCondition.is_player, 'run_command')
def player_run_command(args):
    player = player_instances[index_from_pointer(args[0])]
    if player.is_dead:
        return
    if player.macro:
        ucmd = make_object(UserCmd, args[1])
        attack2 = ucmd.buttons & PlayerButtons.ATTACK2
        if attack2 and player.end_attack:
            # Block right click
            ucmd.buttons &= ~PlayerButtons.ATTACK2
            player.start_attack = 0
            ForceAttack(player, ucmd, False)
            player.other_attack = 0

        if not player.start_attack and not player.while_attack and player.other_attack and player.weapon_fire:
            player.weapon_fire_2 = player.delay(0.08, StartJump, args=(player, ucmd), cancel_on_level_end=True)
            player.weapon_fire = 0

        if player.buttons_state == 3:
            ForceJump(player, ucmd)

    ucmd = make_object(UserCmd, args[1])
    jump = ucmd.buttons & PlayerButtons.JUMP
    if jump:
        player.jumping = True
    else:
        player.jumping = False



def ForceAttack(player, ucmd, jump=True):
    player.start_attack  = 0
    ucmd.buttons |= PlayerButtons.ATTACK
    player.while_attack  = 1
    player.delay(0.01, StopAttack, args=(player, ucmd, jump), cancel_on_level_end=True)

def StopAttack(player, ucmd, jump):
    player.start_attack = 0
    player.while_attack = 0
    player.end_attack = 1
    player.delay(0.48, OtherAttack, args=(player,), cancel_on_level_end=True)

def OtherAttack(player):
    player.weapon_fire = 0
    player.other_attack = 1


def ForceJump(player, ucmd):
    ucmd.buttons |= PlayerButtons.JUMP

def StopJump(player, cmd):
    player.buttons_state = 3

def StartJump(player, ucmd):
    player.buttons_state = 3
    player.delay(0.01, StopJump, args=(player, ucmd), cancel_on_level_end=True)
    player.delay(0.1, ResetMacro, args=(player,), cancel_on_level_end=True)

def ResetMacro(player):
    player.buttons_state = 0
    player.weapon_fire_2 = 0
    player.macro = 1

@Event('weapon_fire')
def _weapon_fire(game_event):
    userid = game_event['userid']
    player = player_instances[index_from_userid(userid)]
    weapon = game_event['weapon']
    if weapon != 'weapon_flashbang':
        return

    player.weapon_fire = 1
