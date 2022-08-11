import asyncio
from lightq import resolvers, resolve, message_handler, event_handler, Bot, scan_handlers
from lightq.entities import GroupMessage, NudgeEvent, MessageChain


@resolve(resolvers.group_id, member_id=resolvers.sender_id)
@message_handler(GroupMessage)
def group_message_handler(chain: MessageChain, group_id: int, member_id: int):
    print(f'收到一条群组消息，群号 {group_id}，群员 QQ 号 {member_id}，内容为：{chain}')


@event_handler(NudgeEvent)
async def nudge_response(event: NudgeEvent, bot: Bot):
    """谁拍一拍我，我就拍一拍谁"""
    if (event.subject.kind == 'Group'
        and event.target == bot.bot_id
        and event.from_id != bot.bot_id):
        await bot.api.send_nudge(event.from_id, event.subject.id, 'Group')


async def main():
    bot = Bot(123456789, 'verify-key')  # 请替换为相应的 QQ 号和 verify key
    bot.add_all(scan_handlers(__name__))
    await bot.run()


if __name__ == '__main__':
    asyncio.run(main())
