from . import entities
from .entities import MessageChain
from .framework import RecvContext, ExceptionContext


def get_group_id(context: RecvContext | ExceptionContext) -> int | None:
    data = context.data if isinstance(context, RecvContext) else context.context.data
    if isinstance(data, entities.Message):
        return data.sender.group.id if isinstance(data.sender, entities.Member) else None
    elif isinstance(data, entities.Event):
        if hasattr(data, 'group') and isinstance(data.group, entities.Group):
            return data.group.id
        elif hasattr(data, 'operator') and isinstance(data.operator, entities.Member):
            return data.operator.group.id
        elif hasattr(data, 'member') and isinstance(data.member, entities.Member):
            return data.member.group.id
        elif hasattr(data, 'group_id') and isinstance(data.group_id, int):
            return data.group_id
        elif isinstance(data, entities.NudgeEvent):
            return data.subject.id if data.subject.kind == 'Group' else None
        else:
            return None
    else:
        return None


def group_id(context: RecvContext | ExceptionContext) -> int:
    group = get_group_id(context)
    assert group is not None, \
        'Cannot resolve group id from data: ' \
        f'{context.data if isinstance(context, RecvContext) else context.context.data}'
    return group


def get_sender_id(context: RecvContext | ExceptionContext) -> int | None:
    data = context.data if isinstance(context, RecvContext) else context.context.data
    if isinstance(data, entities.Message):
        return data.sender.id
    elif isinstance(data, entities.Event):
        if hasattr(data, 'operator') and isinstance(data.operator, entities.Member):
            return data.operator.id
        elif hasattr(data, 'friend') and isinstance(data.friend, entities.Friend):
            return data.friend.id
        elif hasattr(data, 'from_id') and isinstance(data.from_id, int):
            return data.from_id
        elif isinstance(data, entities.FriendRecallEvent):
            return data.author_id
        elif isinstance(data, entities.NudgeEvent):
            return data.from_id
        else:
            return None
    else:
        return None


def sender_id(context: RecvContext | ExceptionContext) -> int:
    sender = get_sender_id(context)
    assert sender is not None, \
        "Cannot resolve sender's user id from data: " \
        f'{context.data if isinstance(context, RecvContext) else context.context.data}'
    return sender


def get_operator_id(context: RecvContext | ExceptionContext) -> int | None:
    data = context.data if isinstance(context, RecvContext) else context.context.data
    if hasattr(data, 'operator') and isinstance(data.operator, entities.Member):
        return data.operator.id
    else:
        return None


def texts(context: RecvContext | ExceptionContext) -> list[str]:
    return [plain.text for plain in MessageChain.from_context(context).get_all(entities.Plain)]


def get_text(context: RecvContext | ExceptionContext) -> str | None:
    plain = MessageChain.from_context(context).get(entities.Plain)
    return plain.text if plain is not None else None


def text(context: RecvContext | ExceptionContext) -> str:
    return MessageChain.from_context(context)[entities.Plain].text


def at_targets(context: RecvContext | ExceptionContext) -> list[int]:
    return [at.target for at in MessageChain.from_context(context).get_all(entities.At)]
