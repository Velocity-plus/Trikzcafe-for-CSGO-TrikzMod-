from .antistuck import *
#from .region_address import *
from .boost import *
from .trikz import *
from .macro import *
#from .no_shake_jump import *
#from .region_phase import *
#from .trigger import *
from filters.players import PlayerIter





def load():
    load_hitboxes()
    trikz_thread.start_thread()
    boost_thread.start_thread()



def load_hitboxes():
    for ply in PlayerIter('alive'):
        player = player_instances[ply.index]

        for x in range(2):
            if x >= 1:
                create_hitbox(
                    origin=player.origin,
                    model=player.model,
                    mins=Vector(-16, -16, 0.0),
                    maxs=Vector(16, 16, 8),
                    player=player
                )

            else:
                create_hitbox(
                    origin=player.origin,
                    model=player.model,
                    mins=player.mins,
                    maxs=player.maxs,
                    player=player
                )

        #x.teleport(player.origin, None, None)
        SayText2('Logging data...').send()
        SayText2('Hitboxes registered: %s' % (str(player.custom_hitboxes))).send()






