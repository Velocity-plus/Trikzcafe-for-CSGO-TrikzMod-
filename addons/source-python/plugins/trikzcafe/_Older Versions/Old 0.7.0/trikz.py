from menus import PagedMenu
from menus import PagedOption
from commands import CommandReturn
from commands.say import SayCommand
from commands.client import ClientCommand
from entities.constants import CollisionGroup
from entities.constants import SolidType
from entities.hooks import EntityCondition
from entities.hooks import EntityPreHook
from entities.helpers import index_from_pointer
from events import Event
from listeners.tick import Repeat
from listeners.tick import GameThread
from listeners import OnLevelInit
from messages import SayText2
from messages import HudMsg
from mathlib import NULL_VECTOR
from filters.players import PlayerIter
from filters.entities import EntityIter
from colors import Color
from players.entity import Player
from players.helpers import index_from_userid
from memory import make_object
from weapons.entity import Weapon
from .data import player_instances
from .data import shared_path
from operator import itemgetter
from configobj import ConfigObj

import active_menus


SETTINGS = ConfigObj(shared_path + 'settings.ini')
WEP_PISTOL = ConfigObj(shared_path + 'weapons_pistols.ini')
WEP_RIFLES = ConfigObj(shared_path + 'weapons_rifles.ini')
C_1 = SETTINGS["Block_Ghost_Color"]["ghost"].split(",")
C_2 = SETTINGS["Block_Ghost_Color"]["block"].split(",")
COLOR_GHOST = Color(int(C_1[0]), int(C_1[1]), int(C_1[2]), int(C_1[3]))
COLOR_BLOCK = Color(int(C_2[0]), int(C_2[1]), int(C_2[2]), int(C_2[3]))
COLOR_HUDMSG = Color(230, 255, 230, 255)

weapons_dict_pistol = {}

for object in WEP_PISTOL:
    weapons_dict_pistol[object] = {"name": WEP_PISTOL[object]["name"],
                                   "vip": int(WEP_PISTOL[object]["vip"])}

weapons_dict_rifles = {}

for object in WEP_RIFLES:
    weapons_dict_rifles[object] = {"name": WEP_RIFLES[object]["name"],
                                   "vip": int(WEP_RIFLES[object]["vip"])}



@Event("player_spawn")
def trikz_player_spawn(game_event):
    userid = game_event['userid']
    index = index_from_userid(userid)
    player = player_instances[index]
    if not player.is_player() and player.is_dead:
        return
    player.set_godmode(True)
    player.set_property_float('m_fLerpTime', 0.0)

    if player.auto_flash:
        if player.get_projectile_ammo('flashbang_projectile') <= 0:
            player.give_named_item('weapon_flashbang')

        player.set_projectile_ammo('flashbang_projectile', 4)

    primary = player.primary
    secondary = player.secondary

    if secondary is not None:
        secondary.remove()

    pistol = player.weapon_preference_pistol
    if pistol is not None:
        player.give_named_item(pistol)
        SayText2(
            '\x06Your favorite weapon is set to: \x02{0}\x06, you can change this buy typing \x03guns\x06 in chat.'.format(
                weapons_dict_pistol[pistol]['name'])).send(index)

    if primary is not None:
        primary.remove()

    rifle = player.weapon_preference_rifle
    if rifle is not None:
        SayText2('\x06Your favorite weapon is set to: \x02%s' % (weapons_dict_rifles[rifle]['name'])).send(index)
        player.give_named_item(rifle)

    if player.auto_jump:
        player.send_convar_value('sv_autobunnyhopping', 1)
    else:
        player.send_convar_value('sv_autobunnyhopping', 0)


class Trikz_Threading:
    def __init__(self):
        self.index = None
        self.repeater = None
        self.repeater_info = None
        self.thread = None

    def _info(self):
        try:
            for player in player_instances.values():
                if player.display_speed and not player.boost_stats['enabled']:
                    index = player.index
                    vel_length_xy = round(player.velocity.length_2D, 1)
                    if vel_length_xy > 0:
                        HudMsg(str(vel_length_xy), y=0.86, color1=COLOR_HUDMSG, hold_time=0.1).send(index)
        except RuntimeError:
            pass

    def _threader(self):
        try:
            for player in player_instances.values():
                if not player.is_dead:

                    if player.tick_adverts <= 0:
                        player.tick_adverts = 80
                    else:
                        player.tick_adverts -= 0.05

                    if player.get_property_float('m_flDuckSpeed') < 7.0:
                        player.set_property_float('m_flDuckSpeed', 7.0)

                    if player.blocking and not player.is_stuck:
                        player.collision_group = CollisionGroup.PLAYER
                        player.solid_type = SolidType.BBOX
                        player.color = COLOR_BLOCK

                    else:
                        player.collision_group = CollisionGroup.DEBRIS
                        player.solid_type = SolidType.NONE
                        player.color = COLOR_GHOST

                    if player.tick_ghost >= 0:
                        player.tick_ghost -= 1

                    if player.auto_flash:
                        if player.get_projectile_ammo('flashbang_projectile') <= 0:
                            player.give_named_item('weapon_flashbang')

                        player.set_projectile_ammo('flashbang_projectile', 4)

        except ValueError:
            pass

    def repeat_thread(self):
        self.repeater = Repeat(self._threader, cancel_on_level_end=True)
        self.repeater.start(0.1)
        self.repeater_info = Repeat(self._info, cancel_on_level_end=True)
        self.repeater_info.start(0.075)

    def start_thread(self):
        # Creates the thread
        self.thread = GameThread(target=self.repeat_thread)
        self.thread.daemon = True
        self.thread.start()


trikz_thread = Trikz_Threading()


@OnLevelInit
def on_level_init(map_name):
    trikz_thread.start_thread()


# =============================================================================
# >> CLIENT COMMANDS / SAY COMMAND
# >>
# =============================================================================
@SayCommand(list(SETTINGS["Command_Trikz_Menu"]["commands"].split(",")))
def trikzText(say, index, team_only=None):
    '''
    Called whenever a player says something.
    '''
    send.trikz(index)
    if say.command_string.startswith('/'):
        return CommandReturn.BLOCK


@SayCommand(list(SETTINGS["Command_Weapon_Menu"]["commands"].split(",")))
def textGiveUsp(say, index, team_only=None):
    '''
    Called whenever a player says something.
    '''
    send.weapon_select(index)
    if say.command_string.startswith('/'):
        return CommandReturn.BLOCK


@SayCommand(['!tp', '/tp', '!tpto', '/tpto'])
def teleportText(say, index, team_only=None):
    '''
    Called whenever a player says something.
    '''
    send.teleport_player(index)
    if say.command_string.startswith('/'):
        return CommandReturn.BLOCK


@SayCommand(['!p', '/p', '!partner', '/partner'])
def teleportText(say, index, team_only=None):
    '''
    Called whenever a player says something.
    '''
    # send.partner_player(index)
    SayText2("This feature is disabled for now").send(index)
    if say.command_string.startswith('/'):
        return CommandReturn.BLOCK


# =============================================================================
# >> CLIENT COMMANDS / SAY COMMAND
# >>
# =============================================================================
@SayCommand(['!spec', '/spec', '!spectate', '/spectate'])
def hintSpec(say, index, team_only=None):
    '''
    Called whenever a player says something.
    '''
    Player(index).set_team(1)
    if say.command_string.startswith('/'):
        return CommandReturn.BLOCK


@SayCommand(['!stopmusic', '/stopmusic', '!music', '/music'])
def hintStopMusic(say, index, team_only=None):
    '''
    Called whenever a player says something.
    '''
    # Remove all custom bounding boxes when changing map
    for ent in EntityIter('ambient', exact_match=False):
        ent.remove()

    SayText2('\x06Music has been stopped!').send(index)
    if say.command_string.startswith('/'):
        return CommandReturn.BLOCK


@SayCommand(['!cp', '/cp', '!checkpoint', '/checkpoint'])
def hintCP(say, index, team_only=None):
    '''
    Called whenever a player says something.
    '''
    send.checkpoints(index)
    if say.command_string.startswith('/'):
        return CommandReturn.BLOCK


@ClientCommand('sp_cp')
def cmdCP(client, index, team_only=None):
    '''
    Called whenever a player says something.
    '''
    send.checkpoints(index)
    return CommandReturn.BLOCK


@SayCommand(['!b', '/b', '!block', '/block', '!ghost', '/ghost'])
def hintBlock(say, index, team_only=None):
    '''
    Called whenever a player says something.
    '''
    player = player_instances[index]
    if player.blocking:
        player.blocking = 0
        player.is_stuck = False
        SayText2('\x06Blocking is OFF').send(index)

    elif not player.blocking:
        player.blocking = 1
        SayText2('\x06Blocking is ON').send(index)

    if say.command_string.startswith('/'):
        return CommandReturn.BLOCK


@SayCommand(['!hud', '/hud'])
def hintHud(say, index, team_only=None):
    '''
    Called whenever a player says something.
    '''
    player = player_instances[index]
    if player.display_speed:
        player.display_speed = 0
        SayText2('\x06Speed hud is OFF').send(index)

    elif not player.display_speed:
        player.display_speed = 1
        SayText2('\x06Speed hud is ON').send(index)

    if say.command_string.startswith('/'):
        return CommandReturn.BLOCK


@ClientCommand('sp_block')
def cmdBlock(client, index, team_only=None):
    '''
    Called whenever a player says something.
    '''
    player = player_instances[index]
    if player.blocking:
        player.blocking = 0
        player.is_stuck = False
        SayText2('\x06Blocking is OFF').send(index)

    elif not player.blocking:
        player.blocking = 1
        SayText2('\x06Blocking is ON').send(index)
    return CommandReturn.BLOCK


def realm_player_count(realm):
    count = 0
    for player in player_instances.values():
        if player.realm == realm:
            count += 1
    return count


class Menus:
    def __init__(self):
        self.menu = None

    def trikz(self, index):
        player = player_instances[index]
        steamid = player.steamid
        self.menu = PagedMenu(
            title='Trikz Menu',
            top_separator=' ',
            bottom_separator=' ',
            select_callback=self.trikz_callback
        )
        if player.boost_stats['enabled']:
            self.menu.append(PagedOption('MLStats: ON', 'mlstats'))
        else:
            self.menu.append(PagedOption('MLStats: OFF', 'mlstats'))

        current = "(VIP Only) "
        vip = player.is_vip
        if vip:
            current = ""
        if player.macro:
            self.menu.append(PagedOption(current + 'Macro Assist: ON', 'macro', highlight=vip))
        else:
            self.menu.append(PagedOption(current + 'Macro Assist: OFF', 'macro', highlight=vip))

        if player.blocking:
            self.menu.append(PagedOption('Blocking: ON\n ', 'blocking'))
        else:
            self.menu.append(PagedOption('Blocking: OFF\n ', 'blocking'))

        self.menu.append(PagedOption('Checkpoints', 'checkpoints'))
        self.menu.append(PagedOption('Teleport to player', 'teleport_player'))
        self.menu.append(PagedOption('Auto-Settings', 'automatic_menu'))
        self.menu.send(index)
        active_menus.am.addMenu(index, self.menu)

    def trikz_automatic(self, index):
        player = player_instances[index]
        steamid = player.steamid
        self.menu = PagedMenu(
            title='Trikz Menu',
            top_separator='=> Automatic stuff',
            bottom_separator=' ',
            select_callback=self.trikz_automatic_callback,
            parent_menu=self.trikz,
            parent_menu_args=index
        )
        if player.auto_flash:
            self.menu.append(PagedOption('Auto-Flash: ON', 'auto_flash'))
        else:
            self.menu.append(PagedOption('Auto-Flash: OFF', 'auto_flash'))
        if player.auto_switch:
            self.menu.append(PagedOption('Auto-Switch: ON', 'auto_switch'))
        else:
            self.menu.append(PagedOption('Auto-Switch: OFF', 'auto_switch'))
        if player.auto_jump:
            self.menu.append(PagedOption('Auto-Jump: ON', 'auto_jump', highlight=False))
        else:
            self.menu.append(PagedOption('Auto-Jump: OFF', 'auto_jump', highlight=False))
        self.menu.append(PagedOption('Anti Stuck: On', 'anti_stuck', highlight=False))
        self.menu.send(index)
        active_menus.am.addMenu(index, self.menu)

    def trikz_automatic_callback(self, menu, index, option):
        player = player_instances[index]

        if option.value == 'auto_flash':
            if player.auto_flash:
                player.auto_flash = 0
                SayText2('\x06Auto-Flash is OFF').send(index)
            elif not player.auto_flash:
                player.auto_flash = 1
                SayText2('\x06Auto-Flash is ON').send(index)

        if option.value == 'auto_switch':
            if player.auto_switch:
                player.auto_switch = 0
                SayText2('\x06Auto-Switch is OFF').send(index)
            elif not player.auto_switch:
                player.auto_switch = 1
                SayText2('\x06Auto-Switch is ON').send(index)

        self.trikz_automatic(index)

    def trikz_callback(self, menu, index, option):
        player = player_instances[index]
        if option.value == 'mlstats':
            if player.boost_stats['enabled']:
                player.boost_stats['enabled'] = 0
                SayText2('\x06MLStats is OFF, your hud should dissappear in a second').send(index)

            elif not player.boost_stats['enabled']:
                player.boost_stats['enabled'] = 1
                SayText2('\x06MLStats is ON').send(index)

        if option.value == 'macro':
            if player.is_vip:
                if player.macro:
                    player.macro = 0
                    SayText2(
                        '\x03[VIP - Trial] \x04Macro Assist has been \x01disabled\x04 - you will have to jump yourself now! \x03(Be sure to try macro as it will be only available for VIPs in 1 week)').send(
                        index)

                else:
                    player.macro = 1
                    SayText2(
                        '\x03[VIP - Trial] \x04Macro Assist has been \x01enabled\x04 - it will now automaticly jump for you when you shoot! \x03(This feature wil be available for non-VIPs for 1 week)').send(
                        index)
                    SayText2('\x02 - Left Click = Attack + Jump').send(index)
                    SayText2('\x02 - Right Click = Normal Attack').send(index)

        if option.value == 'blocking':
            if player.blocking:
                player.blocking = 0
                player.is_stuck = False
                SayText2('\x06Blocking is OFF').send(index)

            elif not player.blocking:
                player.blocking = 1
                SayText2('\x06Blocking is ON').send(index)

        self.trikz(index)

        if option.value == 'automatic_menu':
            self.trikz_automatic(index)
        if option.value == 'teleport_player':
            self.teleport_player(index)
        if option.value == 'checkpoints':
            self.checkpoints(index)

    def checkpoints(self, index):
        player = player_instances[index]
        steamid = player.steamid
        self.menu = PagedMenu(
            title='Checkpoints',
            top_separator='',
            bottom_separator=' ',
            select_callback=self.checkpoints_callback,
            parent_menu=self.trikz,
            parent_menu_args=index
        )
        self.menu.append(PagedOption('Save CP 1', 'cp_save_1'))
        self.menu.append(PagedOption('Teleport to CP 1\n ', 'teleport_cp_1'))
        self.menu.append(PagedOption('Save CP 2', 'cp_save_2'))
        self.menu.append(PagedOption('Teleport to CP 2\n ', 'teleport_cp_2'))
        if player.checkpoints['cp_velocity_toggle']:
            self.menu.append(PagedOption('Save Velocity: YES', 'cp_velocity_toggle'))
        else:
            self.menu.append(PagedOption('Save Velocity: NO', 'cp_velocity_toggle'))
        if player.checkpoints['cp_view_angle_toggle']:
            self.menu.append(PagedOption('Save View Angle: YES', 'cp_view_angle_toggle'))
        else:
            self.menu.append(PagedOption('Save View Angle: NO', 'cp_view_angle_toggle'))

        self.menu.send(index)
        active_menus.am.addMenu(index, self.menu)

    def checkpoints_callback(self, menu, index, option):
        player = player_instances[index]
        steamid = player.steamid
        if option.value == 'cp_save_1':
            player.checkpoints['cp_1'] = player.origin
            SayText2('\x06Checkpoint 1 has been saved!').send(index)
            player.checkpoints['cp_1_velocity'] = player.velocity
            player.checkpoints['cp_1_view_angle'] = player.get_view_angle()

        if option.value == 'teleport_cp_1':
            if player.checkpoints['cp_1'] != NULL_VECTOR:
                origin = player.checkpoints['cp_1']
                vel = NULL_VECTOR
                eye = None
                if player.checkpoints['cp_velocity_toggle']:
                    vel = player.checkpoints['cp_1_velocity']

                if player.checkpoints['cp_view_angle_toggle']:
                    eye = player.checkpoints['cp_1_view_angle']

                player.tick_ghost = 500
                player.Teleport(origin, eye, vel)

        if option.value == 'cp_save_2':
            player.checkpoints['cp_2'] = player.origin
            SayText2('\x06Checkpoint 1 has been saved!').send(index)
            player.checkpoints['cp_2_velocity'] = player.velocity
            player.checkpoints['cp_2_view_angle'] = player.get_view_angle()

        if option.value == 'teleport_cp_2':
            if player.checkpoints['cp_2'] != NULL_VECTOR:
                origin = player.checkpoints['cp_2']
                vel = NULL_VECTOR
                eye = None
                if player.checkpoints['cp_velocity_toggle']:
                    vel = player.checkpoints['cp_2_velocity']

                if player.checkpoints['cp_view_angle_toggle']:
                    eye = player.checkpoints['cp_2_view_angle']

                player.tick_ghost = 500
                player.Teleport(origin, eye, vel)

        if option.value == 'cp_velocity_toggle':
            if player.checkpoints['cp_velocity_toggle']:
                player.checkpoints['cp_velocity_toggle'] = 0
            else:
                player.checkpoints['cp_velocity_toggle'] = 1

        if option.value == 'cp_view_angle_toggle':
            if player.checkpoints['cp_view_angle_toggle']:
                player.checkpoints['cp_view_angle_toggle'] = 0
            else:
                player.checkpoints['cp_view_angle_toggle'] = 1

        return self.checkpoints(index)

    def teleport_player(self, index):
        player = Player(index)
        steamid = player.steamid
        self.menu = PagedMenu(
            title='Teleport to...',
            top_separator='',
            bottom_separator='',
            select_callback=self.teleport_player_callback
        )
        for other in PlayerIter('alive'):
            if other.index != player.index:
                self.menu.append(PagedOption(other.name, other))
        self.menu.send(index)
        active_menus.am.addMenu(index, self.menu)

    def teleport_player_confirmation(self, index, target_index):
        player = player_instances[index]
        target = player_instances[target_index]
        steamid = player.steamid
        self.menu = PagedMenu(
            title='Teleport confirmation\n%s wants to teleport you...' % target.name,
            top_separator='',
            bottom_separator='',
            select_callback=self.teleport_player_confirmation_callback
        )
        self.menu.append(PagedOption("Yes", target))
        self.menu.append(PagedOption("No", "decline"))
        self.menu.send(index)
        active_menus.am.addMenu(index, self.menu)

    def teleport_player_confirmation_callback(self, menu, index, option):
        player = player_instances[index]
        steamid = player.steamid
        if not option.value == "decline":
            SayText2('\x06%s has accepted your teleport request!' % player.name).send(option.value.index)
            SayText2('\x06%s has teleported to you!' % option.value.name).send(index)
            option.value.origin = player.origin

    def teleport_player_callback(self, menu, index, option):
        player = player_instances[index]
        steamid = player.steamid
        self.teleport_player_confirmation(option.value.index, index)
        SayText2('\x06You have sent teleport request to %s' % option.value.name).send(index)

    def partner_player(self, index):
        player = Player(index)
        steamid = player.steamid
        self.menu = PagedMenu(
            title='Choose a partner\nYou will be joining a different realm...',
            top_separator='',
            bottom_separator='',
            select_callback=self.partner_player_callback
        )
        for other in PlayerIter('human'):
            if other.index != player.index:
                self.menu.append(PagedOption(other.name, other))
        self.menu.send(index)
        active_menus.am.addMenu(index, self.menu)

    def partner_player_callback(self, menu, index, option):
        player = player_instances[index]
        steamid = player.steamid
        self.partner_player_confirmation(option.value.index, index)
        SayText2('\x06You have sent partner request to %s' % option.value.name).send(index)

    def partner_player_confirmation(self, index, target_index):
        player = player_instances[index]
        target = player_instances[target_index]
        steamid = player.steamid
        self.menu = PagedMenu(
            title='Partner confirmation\n%s wants to partner up with you' % target.name,
            top_separator='',
            bottom_separator='',
            select_callback=self.partner_player_confirmation_callback
        )
        self.menu.append(PagedOption("Yes", target))
        self.menu.append(PagedOption("No", "decline"))
        self.menu.send(index)
        active_menus.am.addMenu(index, self.menu)

    def partner_player_confirmation_callback(self, menu, index, option):
        player = player_instances[index]
        steamid = player.steamid
        if not option.value == "decline":
            SayText2('\x06%s has accepted your partner request!' % player.name).send(option.value.index)
            SayText2('\x06%s has partnered up with you!' % option.value.name).send(index)

            other = player_instances[option.value.index]
            other.partners.append(player.index)
            player.partners.append(option.value.index)

    def weapon_select(self, index):
        player = player_instances[index]
        pistol = player.weapon_preference_pistol
        rifle = player.weapon_preference_rifle
        if pistol:
            pistol = weapons_dict_pistol[str(pistol)]['name']
        if rifle:
            rifle = weapons_dict_rifles[str(rifle)]['name']
        self.menu = PagedMenu(
            title='Select Your Weapon',
            top_separator='\nYour Favorite Pistol is: %s\nYour Favorite Rifle is: %s \n ' % (pistol,
                                                                                             rifle),
            bottom_separator=' ',
            select_callback=self.weapon_select_callback
        )
        self.menu.append(PagedOption("Pistols", "pistol_menu"))
        self.menu.append(PagedOption("Rifles", "rifle_menu"))
        self.menu.send(index)
        active_menus.am.addMenu(index, self.menu)

    def weapon_select_callback(self, menu, index, option):
        player = player_instances[index]

        if option.value == "pistol_menu":
            self.weapon_select_pistols(index)

        if option.value == "rifle_menu":
            self.weapon_select_rifles(index)

        self.menu.send(index)

    def weapon_select_pistols(self, index):
        player = player_instances[index]
        self.menu = PagedMenu(
            title='Select Your Weapon\n=> Pistols',
            top_separator=' \n',
            bottom_separator='\n ',
            select_callback=self.weapon_select_pistols_callback,
            parent_menu=self.weapon_select,
            parent_menu_args=index,
        )

        weapon_list = []
        for key in weapons_dict_pistol:
            temp_dict = {'item': key,
                         'name': weapons_dict_pistol[key]['name'],
                         'vip': weapons_dict_pistol[key]['vip']}
            weapon_list.append(temp_dict)
        weapon_list_sorted = sorted(weapon_list, key=itemgetter('vip', 'name'))

        vip = player.is_vip
        notify = "(VIP Only) "
        if vip: notify = ""

        current = ""
        for object in weapon_list_sorted:
            if object['item'] == str(player.weapon_preference_pistol):
                current = " (USING)"

            if object['vip']:
                if not vip: object['item'] = 'vip'
                self.menu.append(PagedOption(notify + object['name'] + current, object['item'], highlight=vip))
            else:
                self.menu.append(PagedOption(object['name'] + current, object['item'], highlight=True))
            current = ""
        self.menu.send(index)
        active_menus.am.addMenu(index, self.menu)

    def weapon_select_pistols_callback(self, menu, index, option):
        player = player_instances[index]
        if option.value == 'vip':
            SayText2(
                '\x04You are not \x05VIP\x04 and do not have access to this feature. If you would like to purchase VIP contact an admin!').send(
                index)
            return self.weapon_select_pistols(index)

        player.weapon_preference_pistol = option.value
        if not player.is_dead:
            secondary = player.secondary
            if secondary is not None:
                secondary.remove()
            player.give_named_item(option.value)
        SayText2(
            '\x06Your prefered pistol has been changed to:\x02 %s' % weapons_dict_pistol[option.value]['name']).send(
            index)

        self.weapon_select_pistols(index)

    def weapon_select_rifles(self, index):
        player = player_instances[index]
        self.menu = PagedMenu(
            title='Select Your Weapon\n=> Rifles',
            top_separator=' \n',
            bottom_separator='\n ',
            select_callback=self.weapon_select_rifles_callback,
            parent_menu=self.weapon_select,
            parent_menu_args=index,
        )

        weapon_list = []
        for key in weapons_dict_rifles:
            temp_dict = {'item': key,
                         'name': weapons_dict_rifles[key]['name'],
                         'vip': weapons_dict_rifles[key]['vip']}
            weapon_list.append(temp_dict)
        weapon_list_sorted = sorted(weapon_list, key=itemgetter('vip', 'name'))

        vip = player.is_vip
        notify = "(VIP Only) "
        if vip: notify = ""

        current = ""
        for object in weapon_list_sorted:
            if object['item'] == str(player.weapon_preference_rifle):
                current = " (USING)"

            if object['vip']:
                if not vip: object['item'] = "vip"
                self.menu.append(PagedOption(notify + object['name'] + current, object['item'], highlight=vip))
            else:
                self.menu.append(PagedOption(object['name'] + current, object['item'], highlight=True))
            current = ""
        self.menu.send(index)
        active_menus.am.addMenu(index, self.menu)

    def weapon_select_rifles_callback(self, menu, index, option):
        player = player_instances[index]
        if option.value == 'vip':
            SayText2(
                '\x04You are not \x05VIP\x04 and do not have access to this feature. If you would like to purchase VIP contact an admin!').send(
                index)
            return self.weapon_select_rifles(index)

        player.weapon_preference_rifle = option.value
        if not player.is_dead:
            primary = player.primary
            if primary is not None:
                primary.remove()
            player.give_named_item(option.value)
        SayText2(
            '\x06Your prefered rifle has been changed to:\x02 %s' % weapons_dict_rifles[option.value]['name']).send(
            index)

        self.weapon_select_rifles(index)


send = Menus()


@Event('weapon_fire')
def _weapon_fire(game_event):
    userid = game_event['userid']
    player = player_instances[index_from_userid(userid)]
    weapon = game_event['weapon']
    if weapon != 'weapon_flashbang':
        return

    player.set_projectile_ammo('flashbang_projectile', 4)

    if player.auto_switch:
        player.custom_delays['switch_knife'] = player.delay(0.58, switch,
                                                            kwargs={'player': player, 'weapon': 'weapon_knife'},
                                                            cancel_on_level_end=True)
        player.custom_delays['switch_flashbang'] = player.delay(0.59, switch,
                                                                kwargs={'player': player, 'weapon': 'weapon_flashbang'},
                                                                cancel_on_level_end=True)
        player.custom_delays['switch_fire'] = player.delay(0.6, WeaponSwitch,
                                                           kwargs={'player': player, 'weapon': weapon},
                                                           cancel_on_level_end=True)


def switch(player, weapon):
    if not player.is_dead:
        player.client_command('use %s' % weapon, server_side=True)


@EntityPreHook(EntityCondition.is_player, 'weapon_switch')
def pre_weapon_switch(stack_data):
    # Was the switch successful?
    player = player_instances[index_from_pointer(stack_data[0])]
    weapon = make_object(Weapon, stack_data[1])
    if player.is_dead:
        return

    if player.custom_delays['switch_knife']:
        if player.custom_delays['switch_knife'].running:
            player.custom_delays['switch_knife'].cancel()
            player.custom_delays['switch_flashbang'].cancel()
            player.custom_delays['switch_fire'].cancel()
        else:
            player.delay(0.5, WeaponSwitch, kwargs={'player': player, 'weapon': weapon.classname},
                         cancel_on_level_end=True)


def WeaponSwitch(player, weapon):
    if not player.is_dead:
        if weapon == 'weapon_flashbang':
            player.set_property_float('m_flNextAttack', 1.0)
            player.set_property_bool('m_bWaitForNoAttack', False)
