from listeners import OnPlayerRunCommand


class ActiveMenu:
    def __init__(self):
        self.active_menus = {}

    def addMenu(self, index, menu):
        if index in am.active_menus:
            for m in self.active_menus[index]['active']:
                m.close()
            self.active_menus[index]['active'] = [menu]

        else:
            self.active_menus[index]= {'active':[]}





am = ActiveMenu()

@OnPlayerRunCommand
def on_player_run_cmd(player, cmd):
    if player.index not in am.active_menus:
        am.active_menus[player.index] = {'active':[]}


