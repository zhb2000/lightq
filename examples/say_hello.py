import asyncio
from lightq import filters, message_handler, Bot, scan_handlers, RecvContext
from lightq.entities import FriendMessage


def condition(context: RecvContext) -> bool:
    return str(context.data.message_chain) == 'Hello'


@message_handler(FriendMessage, filters=[filters.from_user(987654321), condition])
def say_hello() -> str:
    """当 QQ 号为 987654321 的用户对 bot 说 Hello 时回复 Hello"""
    return 'Hello'


async def main():
    bot = Bot(123456789, 'verify-key')  # 请替换为相应的 QQ 号和 verify key
    bot.add_all(scan_handlers(__name__))
    await bot.run()


if __name__ == '__main__':
    asyncio.run(main())
