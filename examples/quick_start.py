import asyncio
from lightq import message_handler, Bot, scan_handlers
from lightq.entities import FriendMessage


@message_handler(FriendMessage)
def say_hello() -> str:
    return 'Hello'


async def main():
    bot = Bot(123456789, 'verify-key')  # 请替换为相应的 QQ 号和 verify key
    bot.add_all(scan_handlers(__name__))
    await bot.run()


if __name__ == '__main__':
    asyncio.run(main())
