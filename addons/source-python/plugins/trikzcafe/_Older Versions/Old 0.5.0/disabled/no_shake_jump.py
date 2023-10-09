from events import Event
from entities.helpers import index_from_pointer
from messages import SayText2
from players.helpers import index_from_userid
import active_menus
from entities.constants import SolidType, SolidFlags, EntityEffects, CollisionGroup, EntityFlags, RenderMode
from .data import player_instances
from entities.dictionary import EntityDictionary
import memory
from memory import Convention
from memory import DataType
from entities.hooks import EntityCondition, EntityPreHook, EntityPostHook
from memory.manager import TypeManager
from path import Path
from listeners import OnEntitySpawned, OnLevelInit, OnLevelEnd, OnEntityOutput
from listeners.tick import RepeatStatus
from entities.datamaps import Variant
from memory import NULL, get_size
from listeners.tick import Repeat
from filters.entities import EntityIter
from filters.players import PlayerIter
from entities.entity import Entity
from players.entity import Player
from entities.constants import EntityEffects
from entities import CheckTransmitInfo
from entities.entity import BaseEntity
from memory import make_object
from memory.hooks import PreHook
from memory import Function
from entities.helpers import index_from_edict
from memory.hooks import HookType
from memory import get_virtual_function
from time import time
from commands.say import SayCommand

tracked_inputs = ('Break', 'Toggle', 'Open', 'Enable')
tracked_triggers = ('func_button', 'trigger_multiple')

@EntityPreHook(EntityCondition.is_player, "accept_input")
def pre_accept_input(stack_data):

    SayText2("Hello").send()
    input_name = stack_data[1]
    # Don't go further if this isn't an input we're tracking.
    if input_name not in tracked_inputs:
        return

    try:
        activator = make_object(BaseEntity, stack_data[2])
        if not activator.is_player:
            return
    except:
        return

    # Get the BaseEntity on which the input was called.
    # (func_door, func_breakable, func_wall_toggle, etc.)
    base_entity = make_object(Entity, stack_data[0])

    SayText2(str(base_entity.classname)).send()