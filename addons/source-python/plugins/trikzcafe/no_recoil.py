from cvars import cvar
from cvars.flags import ConVarFlags
from engines.server import execute_server_command
from engines.server import queue_command_string
from listeners import OnLevelInit

commands = {'weapon_recoil_view_punch_extra':{'value':0, 'cheat_flag':1},
            'weapon_recoil_scale': {'value': 0, 'cheat_flag': 1}
            }



@OnLevelInit
def _on_level_init(map_name):
    for c in commands:
        CVAR = cvar.find_base(c)
        if commands[c]['cheat_flag']:
            CVAR.remove_flags(ConVarFlags.CHEAT)
        if commands[c]['value'] is not None:
            queue_command_string("%s %s" % (c, commands[c]['value']))
