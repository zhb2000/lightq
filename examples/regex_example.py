import asyncio
from lightq import resolvers, message_handler, resolve, Bot, scan_handlers
from lightq.entities import GroupMessage
from lightq.decorators import regex_fullmatch


@regex_fullmatch(r'/mute\s+(?P<member_id>\d+)\s+(?P<duration>\d+)')
@resolve(resolvers.group_id)
@message_handler(GroupMessage)
async def mute_command(group_id: int, member_id: str, duration: str, bot: Bot):
    """
    输入 /mute member_id duration 命令以禁言用户

    :param group_id: 群号
    :param member_id: 被禁言的用户
    :param duration: 禁言时长（秒）
    """
    await bot.api.mute(group_id, int(member_id), int(duration))


async def main():
    bot = Bot(123456789, 'verify-key')  # 请替换为相应的 QQ 号和 verify key
    bot.add_all(scan_handlers(__name__))
    await bot.run()


if __name__ == '__main__':
    asyncio.run(main())
