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
from commands.say import SayCommand
from memory import DataType
from entities.hooks import EntityCondition, EntityPreHook
from memory.manager import TypeManager
from path import Path
from listeners import OnEntitySpawned, OnLevelInit
from filters.entities import EntityIter
from entities.entity import Entity
from entities.constants import EntityEffects
from entities import CheckTransmitInfo
from entities.entity import BaseEntity
from memory import make_object
from memory.hooks import PreHook
from entities.helpers import index_from_edict

# This is used to get the offset from a custom data file. This way you don't
# have to add the offset to the SP data file after every update.
manager = TypeManager()
CBaseEntity = manager.create_type_from_file(
    'CBaseEntity', Path(__file__).parent / 'CBaseEntity.ini')

server = memory.find_binary('server', srv_check=False)

PassServerEntityFilter = server[b'\x55\xB8\x01\x00\x00\x00\x89\xE5\x83\xEC\x38\x89\x5D\xF4'].make_function(
    Convention.CDECL,
    [DataType.POINTER, DataType.POINTER],
    DataType.BOOL
)

class LevelHandler(Entity):
    def __init__(self, index):
        super().__init__(index)
        # Instance of the 'trigger_multiple' used for the custom bounding box.
        self.finished = []
        if self.classname in func_properties:
            self.timer = func_properties[self.classname]['timer']
        else: self.timer = 10

    def add_player(self, indexs, timer=True):
        if isinstance(indexs, int):
            if indexs not in self.finished:
                self.finished.append(indexs)
                if timer:
                    self.delay(self.timer, self.remove_player, args=(indexs,), cancel_on_level_end=True)
            else:
                self.notify_already_open(indexs)
                return False
        else:
            for object in indexs:
                if object not in self.finished:
                    self.finished.append(object)
                    if timer:
                        self.delay(self.timer, self.remove_player, args=(object,), cancel_on_level_end=True)
                else:
                    self.notify_already_open(indexs)
                    return False

        SayText2('\x02You have opened a level!').send(indexs)
        return True


    def remove_player(self, indexs):
        if isinstance(indexs, int):
            self.finished.remove(indexs)
        else:
            for object in indexs:
                self.finished.remove(object)

    def notify_already_open(self, indexs):
            SayText2('\x02Level is already open!').send(indexs)


level_instances = EntityDictionary(LevelHandler)

# =============================================================================
# >> CLIENT COMMANDS / SAY COMMAND
# >>
# =============================================================================
@SayCommand(['c'])
def trikzText(say, index, team_only=None):
    '''
    Called whenever a player says something.
    '''
    SayText2(str(memory.Function.is_hooked(Entity.set_transmit))).send()

@PreHook(PassServerEntityFilter)
def _pre_pass_server_entity_filter(args):
    try:
        index_1 = index_from_pointer(args[0])
        index_2 = index_from_pointer(args[1])
    except ValueError:
        return

    try:
        base_entity0 = BaseEntity(index_1)
        base_entity1 = BaseEntity(index_2)


        if base_entity0.is_player() and base_entity0.is_player() or index_1 == index_2:
            return

        entity = Entity(index_1)
        if index_2 > 64:
            player = Entity(index_2)
        else:
            player = player_instances[index_2]
        if player.is_dead:
            return

        classname = entity.classname
        if entity in level_instances.values():
            level = level_instances[entity.index]
            level_classname = level.classname
            if player.index in level.finished:
                if level_classname in func_properties:
                    return func_properties[level_classname]['collision']
    
        if classname in func_properties:
            return func_properties[classname]['default']
    except ValueError:
        pass
        

# These inputs will be tracked inside the AcceptInput hook.
tracked_inputs = ('Break', 'Toggle', 'Open')


@EntityPreHook(EntityCondition.is_player, "accept_input")
def pre_accept_input(stack_data):
    input_name = stack_data[1]
    # Don't go further if this isn't an input we're tracking.
    if input_name not in tracked_inputs:
        return
    # Get the BaseEntity on which the input was called.
    # (func_door, func_breakable, func_wall_toggle, etc.)
    base_entity = memory.make_object(BaseEntity, stack_data[0])

    # Get the BaseEntity that triggered the input.
    activator = memory.make_object(BaseEntity, stack_data[2])
    if not activator.is_player:
        return

    SayText2(base_entity.classname).send()
    player = player_instances[activator.index]
    # Add the index of the level blocking entity.
    level = level_instances[base_entity.index]

    level.add_player(player.partners)
    # Block the input from actually going through.
    # Gotta keep those walls, doors, and other level blocking entities in the
    # same state / position for the players that haven't completed the level.
    return False

def transmit_filter(entity, player, classname):
    if entity in level_instances.values():
        level = level_instances[entity.index]
        if player.index in level.finished:
            return func_properties[classname]['toggle']

    return func_properties[classname]['default']


# We can use the worldspawn entity, because it's using
# CBaseEntity::SetTransmit just like all triggers
@OnLevelInit
def map_start(map):
    Entity.find_or_create("worldspawn")

@EntityPreHook(EntityCondition.is_not_player, 'set_transmit')
def pre_set_transmit(args):

        entity = make_object(BaseEntity, args[0])
        edict = make_object(CheckTransmitInfo, args[1]).client

        player = player_instances[index_from_edict(edict)]
        # We always transmit the player to himself. If we don't, bad things happen.
        if player.index == entity.index:
            return None

        classname = entity.classname
        SayText2(classname).send()
        if classname not in func_properties:
            return



        return None if transmit_filter(Entity(entity.index), player, classname) else False


func_properties = {'func_wall_toggle':{'default':False,
                                       'toggle':True,
                                       'collision':True,
                                       'timer':15},

                   'func_breakable':{'default':True,
                                     'toggle':False,
                                     'collision':False,
                                     'timer':15},

                   'func_door':{'default':True,
                                'toggle':False,
                                'collision':False,
                                'timer':15},
                   'func_button':{'default': True,
                                  'toggle':True,
                                  'collision':True},
                                  'timer':10}



def show_entity(entity):
    classname = entity.classname
    entity.solid_flags = SolidFlags.NOT_MOVEABLE
    if classname == "func_button":
        entity.set_key_value_int('wait', 0)
    entity.edict.clear_transmit_state()
    #entity.render_mode = RenderMode.NORMAL
    entity.effects &= ~EntityEffects.NODRAW

"""
for classname in func_properties:
    for ent in EntityIter(classname, True):
        show_entity(ent)
"""



@OnEntitySpawned
def on_entity_spawned(base_entity):
    classname = base_entity.classname
    if classname in func_properties:
        try:
            index = base_entity.index
            show_entity(Entity(index))
        except ValueError:
            pass



