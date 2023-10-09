from memory import *
from entities.factories import *

binary = 'server'
identifier = b'\x55\x89\xE5\x53\x83\xEC\x04\x8B\x5D\x08\xE8\x2A\x2A\x2A\x2A\x83\xEC\x08\x8B\x10\x53'
offset = 11

addr = find_binary(binary, srv_check=False)[identifier];print(1)
fo = addr.get_pointer(offset);print(2)
addr += offset + 4 + fo;print(3)

factories = make_object(
    EntityFactoryDictionary,
    addr.make_function(Convention.CDECL, (), DataType.POINTER)()
);print(4)

print('>>', factories[33])