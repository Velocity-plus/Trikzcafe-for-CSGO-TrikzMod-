import random
from menus import PagedMenu
from menus import PagedOption
from commands import CommandReturn
from commands.say import SayCommand
from commands.client import ClientCommand
from entities.constants import CollisionGroup
from entities.constants import SolidType
from entities.entity import Entity
from entities.hooks import EntityCondition
from entities.hooks import EntityPreHook
from entities.constants import RenderMode
from entities.helpers import index_from_pointer
from events import Event
from listeners.tick import Repeat
from listeners import OnEntityDeleted
from listeners.tick import GameThread
from listeners import OnLevelInit, OnLevelEnd
from messages import SayText2
from messages import HudMsg
from mathlib import NULL_VECTOR
from filters.players import PlayerIter
from filters.entities import EntityIter
from colors import Color
from players.entity import Player
from core import echo_console
from players.helpers import index_from_userid
from memory import make_object
from weapons.entity import Weapon
from .tcore.instances import PLAYER
from .tcore.instances import shared_path, LDB
#from .tcore.instances import TEAMS
from operator import itemgetter
from configobj import ConfigObj
#from .model_glow import enable_glow, create_player_glow, update_model_glow
#from .flash_glow import enable_flash_glow, create_flash_glow
from stringtables.downloads import Downloadables
#from .antistuck import start_ignore_anti_stuck
from commands.client import get_client_command
import active_menus
from commands.client import ClientCommandFilter
# Source.Python
from commands import CommandReturn
from commands.client import ClientCommand
from engines.precache import Model
from engines.server import engine_server

downloads = Downloadables()
# Make sure the players download the heartbeat sounds.
downloads.add_directory('models')
downloads.add_directory('materials')
downloads.add_directory('resource')

# ../change_model/change_model.py

model_path = 'models/player/custom_player/kirby/leetkumla/leetkumla.mdl'
arms_path = 'models/weapons/t_arms_professional.mdl'


SETTINGS = ConfigObj(shared_path + 'settings.ini')
WEP_PISTOL = ConfigObj(shared_path + 'weapons_pistols.ini')
WEP_RIFLES = ConfigObj(shared_path + 'weapons_rifles.ini')
MODELS = ConfigObj(shared_path + 'models.ini')
MODELS_GLOW_INI = ConfigObj(shared_path + 'model_glow.ini')
C_1 = SETTINGS["Block_Ghost_Color"]["ghost"].split(",")
C_2 = SETTINGS["Block_Ghost_Color"]["block"].split(",")
COLOR_GHOST = Color(int(C_1[0]), int(C_1[1]), int(C_1[2]), int(C_1[3]))
COLOR_BLOCK = Color(int(C_2[0]), int(C_2[1]), int(C_2[2]), int(C_2[3]))
COLOR_HUDMSG = Color(230, 255, 230, 255)

weapons_dict_pistol = {}
weapons_dict_rifles = {}
models_dict = {}
models_glow_dict = {}

for object in WEP_PISTOL:
    weapons_dict_pistol[object] = {"name": WEP_PISTOL[object]["name"],
                                   "auth": WEP_PISTOL[object]["auth"].strip().split(","),
                                   'hidden': int(WEP_PISTOL[object]["hidden"]),
                                   'order':int(WEP_PISTOL[object]['order'])}

for object in WEP_RIFLES:
    weapons_dict_rifles[object] = {"name": WEP_RIFLES[object]["name"],
                                   "auth": WEP_RIFLES[object]["auth"].strip().split(","),
                                   'hidden': int(WEP_RIFLES[object]["hidden"]),
                                   'order':int(WEP_RIFLES[object]['order'])}

for object in MODELS:
    models_dict[object] = {"name": MODELS[object]["name"],
                           "order": int(MODELS[object]["order"]),
                           "auth": MODELS[object]["auth"].strip().split(","),
                           'arms': MODELS[object]['arms'],
                           'hidden': int(MODELS[object]["hidden"])}

for object in MODELS_GLOW_INI:
    models_glow_dict[object] = {"name": MODELS_GLOW_INI[object]["name"],
                                "order": int(MODELS_GLOW_INI[object]["order"]),
                                "auth": MODELS_GLOW_INI[object]["auth"].strip().split(","),
                                'hidden': int(MODELS_GLOW_INI[object]["hidden"])}


def use_default_model(player):
    for object in models_dict:
        if models_dict[object]["name"] == "Player Male":
            player.model_preference = object
            engine_server.precache_model(object)
            player.model = Model(object)
            player.set_property_string('m_szArmsModel', '')

@SayCommand(['!model', '!m', 'model', '/model', '!models'])
def change_model(say, index, team_only=None):
    """Changes the player's world and arms model."""
    player = PLAYER[index]
    send.model_select(index)

@SayCommand(['!macro', 'macro', '/macro'])
def change_model(say, index, team_only=None):
    """Changes the player's world and arms model."""
    player = PLAYER[index]
    if player.macro:
        player.macro = 0
        SayText2(
            '\x04Macro Assist has been \x01disabled\x04 - you will have to jump yourself now!').send(
            index)

    else:
        player.macro = 1
        SayText2(
            '\x04Macro Assist has been \x01enabled\x04 - it will now automatically jump for you when you throw flashbang!').send(
            index)
        SayText2('\x02 - Left Click = Attack + Jump').send(index)
        SayText2('\x02 - Right Click = Normal Attack').send(index)

@OnEntityDeleted
def save_on_delete(entity):
    try:
        index = entity.index
        if index in PLAYER:
            player = PLAYER[index]
            LDB.save_one(player)
    except ValueError:
        pass

@OnLevelEnd
def save_database():
    LDB.save_db()


@ClientCommandFilter
def client_command_filter(command, index):
    # Get the player entity
    player  = PLAYER[index]
    # Block 'jointeam'
    if command[0] == 'jointeam':
        # Get the team the player wants to join
        team_choice = command[1]
        if player.team in [1,2,3] and team_choice in ['2']:
            player.set_team(3)
            return CommandReturn.BLOCK

@Event("player_spawn")
def trikz_player_spawn(game_event):
    userid = game_event['userid']
    index = index_from_userid(userid)
    player = PLAYER[index]
    if not player.is_player() or player.is_dead:
        return
    player.set_godmode(True)

    if player.auto_flash:
        if player.get_projectile_ammo('flashbang_projectile') <= 0:
            player.give_named_item('weapon_flashbang')

        player.set_projectile_ammo('flashbang_projectile', 2)

    primary = player.primary
    secondary = player.secondary

    if secondary is not None:
        secondary.remove()

    SayText2('\x05\x08 [Discord] \x01 discord.gg/vEJ7N5NebG \x09 Enjoy your time!').send(index)
    pistol = player.weapon_preference_pistol
    if pistol is not None:
        player.give_named_item(pistol)
    if primary is not None:
        primary.remove()

    #rifle = player.weapon_preference_rifle
    #if rifle is not None:
    #    player.give_named_item(rifle)

    SayText2('\x02  -\x08 !t \x06 to change trikz settings.').send(index)
    SayText2('\x02  -\x08 !models \x06 to change your model.').send(index)
    SayText2('\x02  -\x08 !guns \x06 to change weapons.').send(index)

    player.delay(0.5, change_player_model, args=(player, player.model_preference))
    if player.model_preference:
        SayText2('\x06Your current model: \x02%s ' % models_dict[player.model_preference]["name"]).send(index)

ADS = ["\x06Last update for the Mod: \x0228-01-2023. \x02Version 1.0.0",
       "\x06Please note that the server is not official yet! Consider yourself special for being available to play now!",
       "\x02Tip: \x06You can use ur knife to boost.",
       "\x02Tip: \x06If you don't know how to play, just ask someone!",
       "\x02[Discord] \x06 Join our discord server: \x06discord.gg/vEJ7N5NebG"]

def change_player_model(player, model):
    player.model_preference = model
    if player.model_preference:
        engine_server.precache_model(model)
        player.model = Model(model)
        if models_dict[model]['arms'] != "None":
            engine_server.precache_model(models_dict[model]['arms'])
            #player.set_property_string('m_szArmsModel', models_dict[model]['arms'])
        else:
            player.set_property_string('m_szArmsModel', '')
    else:
        use_default_model(player)


class Trikz_Threading:
    def __init__(self):
        self.index = None
        self.repeater = None
        self.repeater_info = None
        self.thread = None

    def ads(self):
        SayText2(random.choice(ADS)).send()

    def repeat_thread(self):

        self.repeater = Repeat(self.ads, cancel_on_level_end=True)
        self.repeater.start(120)

    def start_thread(self):
        # Creates the thread
        self.thread = GameThread(target=self.repeat_thread)
        self.thread.daemon = True
        self.thread.start()


trikz_thread = Trikz_Threading()


@OnLevelInit
def on_level_init(map_name):
    for object in models_dict:
        engine_server.precache_model(object)
    trikz_thread.start_thread()


# =============================================================================
# >> CLIENT COMMANDS / SAY COMMAND
# >>
# =============================================================================

@SayCommand(['!restart', '!r', 'r', '/r'])
def change_model(say, index, team_only=None):
    """Changes the player's world and arms model."""
    player = PLAYER[index]
    player.spawn(True)
    if say.command_string.startswith('/'):
        return CommandReturn.BLOCK

@SayCommand(['!k', '!knife', 'knife', '/knife'])
def change_model(say, index, team_only=None):
    """Changes the player's world and arms model."""
    player = PLAYER[index]
    player.give_named_item("weapon_knife")
    if say.command_string.startswith('/'):
        return CommandReturn.BLOCK


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


@SayCommand(['!ent', '/ent'])
def giveWeaponText(say, index, team_only=None):
    '''
    Called whenever a player says something.
    '''
    player = PLAYER[index]
    x = player.get_view_entity().classname
    SayText2(x).send()
    if say.command_string.startswith('/'):
        return CommandReturn.BLOCK

# =============================================================================
# >> CLIENT COMMANDS / SAY COMMAND
# >>
# =============================================================================

class Menus:
    def __init__(self):
        self.menu = None

    def trikz(self, index):
        player = PLAYER[index]
        toggle_firstperson(player)
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

        if player.macro:
            self.menu.append(PagedOption('Macro Assist: ON', 'macro'))
        else:
            self.menu.append(PagedOption('Macro Assist: OFF', 'macro'))

        if player.blocking:
            self.menu.append(PagedOption('Blocking: ON\n ', 'blocking'))
        else:
            self.menu.append(PagedOption('Blocking: OFF\n ', 'blocking'))

        self.menu.append(PagedOption('Checkpoints', 'checkpoints'))
        self.menu.append(PagedOption('Teleport to player', 'teleport_player'))
        self.menu.append(PagedOption('Effects & Models', 'effect_menu'))
        self.menu.append(PagedOption('Auto-Settings', 'automatic_menu'))

        self.menu.send(index)
        active_menus.am.addMenu(index, self.menu)

    def trikz_automatic(self, index):
        player = PLAYER[index]
        steamid = player.steamid
        self.menu = PagedMenu(
            title='Trikz Menu',
            top_separator='=> Automatic stuff',
            bottom_separator=' ',
            select_callback=self.trikz_automatic_callback,
            parent_menu=self.trikz,
            parent_menu_args=index,
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
        player = PLAYER[index]

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
        player = PLAYER[index]
        if option.value == 'mlstats':
            if player.boost_stats['enabled']:
                player.boost_stats['enabled'] = 0
                SayText2('\x06MLStats is OFF, your hud should dissappear in a second').send(index)

            elif not player.boost_stats['enabled']:
                player.boost_stats['enabled'] = 1
                SayText2('\x06MLStats is ON').send(index)

        if option.value == 'macro':
                if player.macro:
                    player.macro = 0
                    SayText2(
                        '\x04Macro Assist has been \x01disabled\x04 - you will have to jump yourself now!').send(
                        index)

                else:
                    player.macro = 1
                    SayText2(
                        '\x04Macro Assist has been \x01enabled\x04 - it will now automatically jump for you when you throw flashbang!').send(
                        index)
                    SayText2('\x02 - Left Click = Attack + Jump').send(index)
                    SayText2('\x02 - Right Click = Normal Attack').send(index)

        if option.value == 'automatic_menu':
            self.trikz_automatic(index)
        elif option.value == 'teleport_player':
            self.teleport_player(index)
        elif option.value == 'checkpoints':
            self.checkpoints(index)
        elif option.value == 'effect_menu':
            self.trikz_effects(index)
        else:
            self.trikz(index)

    def trikz_effects(self, index):
        player = PLAYER[index]
        toggle_firstperson(player)
        steamid = player.steamid
        self.menu = PagedMenu(
            title='Effects Menu',
            top_separator='=> Models/GLow/Colors',
            bottom_separator=' ',
            select_callback=self.trikz_effects_callback,
            parent_menu=self.trikz,
            parent_menu_args=index,
        )
        self.menu.append(PagedOption('Player Models', 'player_models'))
        self.menu.append(PagedOption('Player Effects', 'player_effects'))
        self.menu.append(PagedOption('Flash Effects', 'flash_effects'))
        self.menu.send(index)
        active_menus.am.addMenu(index, self.menu)

    def trikz_effects_callback(self, menu, index, option):
        player = PLAYER[index]
        steamid = player.steamid
        if option.value == 'player_models':
            self.model_select(index)
        if option.value == 'player_effects':
            self.model_glow_select(index)
        if option.value == 'flash_effects':
            self.model_glow_flash_select(index)
        self.menu.send(index)

    def checkpoints(self, index):
        player = PLAYER[index]
        toggle_firstperson(player)
        steamid = player.steamid
        self.menu = PagedMenu(
            title='Checkpoints',
            top_separator='',
            bottom_separator=' ',
            select_callback=self.checkpoints_callback,
            parent_menu=self.trikz,
            parent_menu_args=index,
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
        player = PLAYER[index]
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
                #start_ignore_anti_stuck(player, 2)
                player.Teleport(origin, eye, vel)

        if option.value == 'cp_save_2':
            player.checkpoints['cp_2'] = player.origin
            SayText2('\x06Checkpoint 2 has been saved!').send(index)
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

                #start_ignore_anti_stuck(player, 2)
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
        player = PLAYER[index]
        target = PLAYER[target_index]
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
        player = PLAYER[index]
        steamid = player.steamid
        if not option.value == "decline":
            SayText2('\x06%s has accepted your teleport request!' % player.name).send(option.value.index)
            SayText2('\x06%s has teleported to you!' % option.value.name).send(index)
            option.value.origin = player.origin

    def teleport_player_callback(self, menu, index, option):
        player = PLAYER[index]
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
        player = PLAYER[index]
        steamid = player.steamid
        self.partner_player_confirmation(option.value.index, index)
        SayText2('\x06You have sent partner request to %s' % option.value.name).send(index)

    def partner_player_confirmation(self, index, target_index):
        player = PLAYER[index]
        target = PLAYER[target_index]
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
        player = PLAYER[index]
        steamid = player.steamid
        if not option.value == "decline":
            SayText2('\x06%s has accepted your partner request!' % player.name).send(option.value.index)
            SayText2('\x06%s has partnered up with you!' % option.value.name).send(index)

    def sortBy(self, *keys, data):
        items = []
        for key in data:
            temp_dict = {'key':key}
            for key2 in data[key]:
                temp_dict[key2] = data[key][key2]
            items.append(temp_dict)
        items_sorted = sorted(items, key=itemgetter(*keys))
        return items_sorted

    def append_items(self, player, current_item, items):
        auth = player.get_auth
        for item in items:
            current = ""
            if item['key'] == current_item:
                current = " [Using]"

            if item['auth'][0] != "":
                if player.check_auth(item['auth']):
                    notify = "(%s)" % auth[0]
                    self.menu.append(PagedOption(notify + item['name'] + current, item['key'], highlight=True))
                elif not item['hidden']:
                    notify = "(Private) "
                    item['key'] = 'vip'
                    self.menu.append(PagedOption(notify + item['name'] + current, item['key'], highlight=False))
            else:
                self.menu.append(PagedOption(str(item['name']) + current, item['key'], highlight=True))

    def model_select(self, index):
        player = PLAYER[index]
        toggle_thirdperson(player)
        self.menu = PagedMenu(
            title='Select Your Model\n=> Models',
            top_separator=' \n',
            bottom_separator='\n ',
            select_callback=self.model_select_callback,
            close_callback=self.model_close_callback,
        )

        item_list = self.sortBy('order', 'name', 'hidden', data=models_dict)
        self.append_items(player, player.model_preference, item_list)
        self.menu.send(index)
        active_menus.am.addMenu(index, self.menu)

    def model_close_callback(self, menu, index):
        player = PLAYER[index]
        toggle_firstperson(player)

    def model_select_callback(self, menu, index, option):
        player = PLAYER[index]
        if option.value == 'vip':
            SayText2(
                '\x04You are not \x05VIP\x04 and do not have access to this feature.').send(
                index)
            return self.model_select(index)

        player.model_preference = option.value
        if not player.is_dead:
            change_player_model(player, option.value)
        SayText2(
            '\x06Your prefered model has been changed to:\x02 %s' % models_dict[option.value]['name']).send(
            index)

        self.model_select(index)


    def model_glow_select(self, index):
        player = PLAYER[index]
        self.menu = PagedMenu(
            title='Select Your Glow Color\n=> Model Glow Color',
            top_separator=' \n',
            bottom_separator='\n ',
            select_callback=self.model_glow_select_callback,
            close_callback=self.model_glow_close_callback,
            parent_menu=self.trikz_effects,
            parent_menu_args=index,
        )
        toggle_thirdperson(player)
        if player.glow_enabled:
            self.menu.append(PagedOption("Glow: [On]\n ", "enabled"))
        else:
            self.menu.append(PagedOption("Glow: [Off]\n ", "enabled"))

        r, g, b, a = player.glow_color
        item_list = self.sortBy('order', 'name', 'hidden', data=models_glow_dict)
        self.append_items(player, str(r)+","+str(g)+","+str(b), item_list)
        self.menu.send(index)
        active_menus.am.addMenu(index, self.menu)

    def model_glow_close_callback(self, menu, index):
        player = PLAYER[index]
        toggle_firstperson(player)

    def model_glow_select_callback(self, menu, index, option):

        player = PLAYER[index]
        if option.value == 'vip':
            SayText2(
                '\x04You are not \x05VIP\x04 and do not have access to this feature.').send(
                index)
            return self.model_glow_select(index)

        elif option.value == 'enabled':
            if player.glow_enabled:
                SayText2('\x06You have disabled \x02 glow!').send(index)
                #enable_glow(player.index)
            else:
                SayText2('\x06You have enabled \x02 glow!').send(index)
                #enable_glow(player.index)
        else:
            r,g,b = option.value.split(",")
            player.glow_color = Color(int(r),int(g),int(b))
            SayText2(
                '\x06Your prefered glow color has been changed to:\x02 %s' % models_glow_dict[option.value]['name']).send(
                index)

            #for glow_model in player.glow_prop.values():
            #   create_player_glow(glow_model, player.glow_color)
        self.model_glow_select(index)



    def model_glow_flash_select(self, index):
        player = PLAYER[index]
        self.menu = PagedMenu(
            title='Select Flash Properties\n=> Flash Glow/Color/Skin Color',
            top_separator=' \n',
            bottom_separator='\n ',
            select_callback=self.model_glow_flash_select_callback,
            parent_menu=self.trikz_effects,
            parent_menu_args=index,
        )

        if player.glow_flash_enabled:
            self.menu.append(PagedOption("Glow: [On]", "enabled"))
        else:
            self.menu.append(PagedOption("Glow: [Off]", "enabled"))

        self.menu.append(PagedOption("Glow Style: %s" % player.glow_flash_style, "enabled_style"))


        if player.flash_skin_enabled:
            self.menu.append(PagedOption("Skin: [On]\n ", "enabled_skin"))
        else:
            self.menu.append(PagedOption("Skin: [Off]\n ", "enabled_skin"))

        r, g, b, a = player.glow_flash_color
        item_list = self.sortBy('order', 'name', 'hidden', data=models_glow_dict)
        self.append_items(player, str(r)+","+str(g)+","+str(b), item_list)
        self.menu.send(index)
        active_menus.am.addMenu(index, self.menu)


    def model_glow_flash_select_callback(self, menu, index, option):
        player = PLAYER[index]
        if option.value == 'vip':
            SayText2(
                '\x04You are not \x05VIP\x04 and do not have access to this feature.').send(
                index)
            return self.model_glow_flash_select(index)

        elif option.value == 'enabled_skin':
            if player.flash_skin_enabled:
                SayText2('\x06You have disabled flash \x02 skin!').send(index)
                player.flash_skin_enabled = False
            else:
                SayText2('\x06You have enabled flash \x02 skin!').send(index)
                player.flash_skin_enabled = True
        elif option.value == 'enabled_style':
            if player.glow_flash_style > 2:
                player.glow_flash_style = 0
            else:
                player.glow_flash_style += 1
            SayText2('\06You have changed glow style to: %s' % player.glow_flash_style).send(player.index)

        else:
            r,g,b = option.value.split(",")
            player.glow_flash_color = Color(int(r),int(g),int(b))
            SayText2(
                '\x06Your prefered glow color has been changed to:\x02 %s' % models_glow_dict[option.value]['name']).send(
                index)

        self.model_glow_flash_select(index)

    def weapon_select(self, index):
        player = PLAYER[index]
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
        player = PLAYER[index]

        if option.value == "pistol_menu":
            self.weapon_select_pistols(index)

        if option.value == "rifle_menu":
            self.weapon_select_rifles(index)

        self.menu.send(index)

    def weapon_select_pistols(self, index):
        player = PLAYER[index]
        self.menu = PagedMenu(
            title='Select Your Weapon\n=> Pistols',
            top_separator=' \n',
            bottom_separator='\n ',
            select_callback=self.weapon_select_pistols_callback,
            parent_menu=self.weapon_select,
            parent_menu_args=index,

        )

        item_list = self.sortBy('order', 'name', 'hidden', data=weapons_dict_pistol)
        self.append_items(player, player.weapon_preference_pistol, item_list)
        self.menu.send(index)
        active_menus.am.addMenu(index, self.menu)

    def weapon_select_pistols_callback(self, menu, index, option):
        player = PLAYER[index]
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
        player = PLAYER[index]
        self.menu = PagedMenu(
            title='Select Your Weapon\n=> Rifles',
            top_separator=' \n',
            bottom_separator='\n ',
            select_callback=self.weapon_select_rifles_callback,
            parent_menu=self.weapon_select,
            parent_menu_args=index,
        )

        item_list = self.sortBy('order', 'name', 'hidden', data=weapons_dict_rifles)
        self.append_items(player, player.weapon_preference_rifle, item_list)
        self.menu.send(index)
        active_menus.am.addMenu(index, self.menu)

    def weapon_select_rifles_callback(self, menu, index, option):
        player = PLAYER[index]
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
    player = PLAYER[index_from_userid(userid)]
    weapon = game_event['weapon']
    if weapon != 'weapon_flashbang':
        return

    if player.auto_flash:
        if player.get_projectile_ammo('flashbang_projectile') <= 1:
            player.set_projectile_ammo("flashbang_projectile", 2)

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

def toggle_thirdperson(player):
    if not player.is_dead:
        player.glow_enabled_self = True
        player.client_command("thirdperson")

def toggle_firstperson(player):
    if player.glow_enabled_self:
        player.glow_enabled_self = False
    player.client_command("firstperson")

@EntityPreHook(EntityCondition.is_player, 'weapon_switch')
def pre_weapon_switch(stack_data):
    # Was the switch successful?
    player = PLAYER[index_from_pointer(stack_data[0])]
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