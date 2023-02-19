from core import GAME_NAME, PLATFORM
from mathlib import QAngle
from memory import Convention, DataType, find_binary, make_object
from memory.hooks import PreHook
 
 
if GAME_NAME == 'csgo':
    srv_check = False
    if PLATFORM == 'windows':
        SET_LOCAL_ANGLES_IDENTIFIER = b'\x55\x8B\xEC\x83\xE4\xC0\x83\xEC\x34\x2A\x2A\x2A\x2A\x2A\x2A\x2A\x2A\x53\x2A\x2A\x2A\x56\x57'
    else:
        SET_LOCAL_ANGLES_IDENTIFIER = b'\x55\x89\xE5\x56\x53\x83\xEC\x20\x8B\x5D\x0C\xF3\x0F\x10\x15\x2A\x2A\x2A\x2A'
else:
    srv_check = True
    if PLATFORM == 'windows':
        SET_LOCAL_ANGLES_IDENTIFIER = b'\x55\x8B\xEC\x2A\x2A\x2A\x2A\x2A\x2A\x2A\x2A\x83\xEC\x10\x0F\x28\xC1'
    else:
        SET_LOCAL_ANGLES_IDENTIFIER = '_ZN11CBaseEntity14SetLocalAnglesERK6QAngle'
 
server = find_binary('server', srv_check=srv_check)
 
# void CBaseEntity::SetLocalAngles( const QAngle& angles )
set_local_angles = server[SET_LOCAL_ANGLES_IDENTIFIER].make_function(
    Convention.THISCALL,
    (DataType.POINTER, DataType.POINTER),
    DataType.VOID
)
 
 
@PreHook(set_local_angles)
def pre_set_local_angles(args):
    angle = make_object(QAngle, args[1])
    angle.x = (angle.x % 360 - 360) if angle.x < 0 else (angle.x % 360)
    angle.y = (angle.y % 360 - 360) if angle.y < 0 else (angle.y % 360)
    angle.z = (angle.z % 360 - 360) if angle.z < 0 else (angle.z % 360)