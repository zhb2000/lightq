"""
[预期效果]
群友 1：/weather
Bot：您想查询哪个城市的天气？
群友 1：武汉
Bot：武汉的天气为小雨

群友 2：/mute_all
Bot：您确定要开启全员禁言吗？请回复“是”或“否”
群友 2：no
Bot：请回复“是”或“否”
群友 2：否
"""

import asyncio
from datetime import datetime, timedelta
from lightq import resolvers, resolve, message_handler, Bot, Controller, handler_property
from lightq.decorators import regex_fullmatch
from lightq.entities import GroupMessage, MessageChain


class Status:
    def __init__(self, command: str, time: datetime):
        self.command = command
        self.time = time  # 收到命令的时间，做超时判断之用


class AssistantController(Controller):
    def __init__(self):
        # (group_id, sender_id) => status
        self.status: dict[tuple[int, int], Status] = {}

    @handler_property
    def weather_command(self):
        @regex_fullmatch('/weather')
        @resolve(resolvers.group_id, resolvers.sender_id)
        @message_handler(GroupMessage)
        def handler(group_id: int, sender_id: int) -> str:
            self.status[(group_id, sender_id)] = Status('/weather', datetime.now())
            return '您想查询哪个城市的天气？'

        return handler

    @handler_property
    def mute_all_command(self):
        @regex_fullmatch('/mute_all')
        @resolve(resolvers.group_id, resolvers.sender_id)
        @message_handler(GroupMessage)
        def handler(group_id: int, sender_id: int) -> str:
            self.status[(group_id, sender_id)] = Status('/mute_all', datetime.now())
            return '您确定要开启全员禁言吗？请回复“是”或“否”'

        return handler

    @handler_property
    def lowest_priority_handler(self):
        """根据每个用户的状态做出不同的反应"""

        @resolve(resolvers.group_id, resolvers.sender_id)
        @message_handler(GroupMessage, after=[self.weather_command, self.mute_all_command])
        async def handler(
            group_id: int,
            sender_id: int,
            chain: MessageChain,
            bot: Bot
        ) -> str | None:
            status = self.status.pop((group_id, sender_id), None)
            if status is None or datetime.now() - status.time > timedelta(seconds=30):
                # 连续对话时，用户需要在 30 秒内做出反应，超过 30 秒的回复会被 bot 忽略
                return None
            if status.command == '/weather':
                return await query_weather(str(chain))
            else:  # /mute_all
                if str(chain) == '是':
                    await bot.api.mute_all(group_id)
                    return None
                elif str(chain) == '否':
                    return None
                else:
                    self.status[(group_id, sender_id)] = Status('/mute_all', datetime.now())
                    return '请回复“是”或“否”'

        return handler


async def query_weather(city: str) -> str:
    """模拟一个查询天气的 API"""
    return f'{city}的天气为小雨'


async def main():
    bot = Bot(123456789, 'verify-key')  # 请替换为相应的 QQ 号和 verify key
    controller = AssistantController()
    bot.add_all(controller.handlers())
    await bot.run()


if __name__ == '__main__':
    asyncio.run(main())
