"""Project the immutable pre-branding descriptor into the Groundlark namespace.

Only schema file paths and fully qualified type/package names change. Buf still
compares every field, tag, enum, presence rule and service against the original
baseline. This is not a replacement baseline or an exception to wire checks.
"""
from google.protobuf import descriptor_pb2


def renamed_baseline(data):
    result = descriptor_pb2.FileDescriptorSet.FromString(data)
    old, new = 'senseshake', 'groundlark'

    def qualify(value):
        return '.' + new + value[len(old)+1:] if value.startswith('.' + old + '.') else value

    def types(message):
        if message.DESCRIPTOR.full_name == 'google.protobuf.EnumValueDescriptorProto' and message.name == 'BOARD_T1':
            message.name = 'BOARD_DAQHAT_01'
        for field, value in message.ListFields():
            if field.type == field.TYPE_MESSAGE:
                for item in value if field.label == field.LABEL_REPEATED else [value]:
                    types(item)
            elif field.name in ('type_name', 'extendee', 'input_type', 'output_type'):
                setattr(message, field.name, qualify(value))

    for file in result.file:
        if file.name.startswith(old + '/'):
            file.name = new + file.name[len(old):]
        if file.package.startswith(old + '.'):
            file.package = new + file.package[len(old):]
        for i, name in enumerate(file.dependency):
            if name.startswith(old + '/'):
                file.dependency[i] = new + name[len(old):]
        types(file)
    return result.SerializeToString(deterministic=True)
