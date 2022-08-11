import asyncio
from lightq import message_handler, Bot, scan_handlers
from lightq.entities import GroupMessage, MessageChain
from lightq.decorators import regex_fullmatch

repeat_on = False


@regex_fullmatch('(?P<option>开始|停止)复读')
@message_handler(GroupMessage)
def switch(option: str):
    global repeat_on
    repeat_on = option == '开始'
    return f'复读已{option}'


@message_handler(GroupMessage, filters=lambda ctx: repeat_on, after=switch)
def repeat(chain: MessageChain) -> MessageChain:
    return chain


async def main():
    bot = Bot(123456789, 'verify-key')  # 请替换为相应的 QQ 号和 verify key
    bot.add_all(scan_handlers(__name__))
    await bot.run()


if __name__ == '__main__':
    asyncio.run(main())
