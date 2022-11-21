# LightQ

![PyPI](https://img.shields.io/pypi/v/lightq?logo=pypi&logoColor=white) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/lightq?logo=python&logoColor=white) ![mirai-api-http version](https://img.shields.io/badge/mirai--api--http-v2.6.2-blue) ![PyPI - License](https://img.shields.io/pypi/l/lightq)

LightQ 是一个基于 [mirai-api-http](https://github.com/project-mirai/mirai-api-http) 的 QQ 机器人框架。

## 安装

从 PyPI 安装：

```shell
pip install lightq
```

从源代码安装：

```shell
git clone https://github.com/zhb2000/lightq.git
cd lightq
pip install .
```

## 前置条件

环境要求：

- Python 3.10
- mirai-api-http 2.6.2

LightQ 需要借助网络 API 调用 Mirai 的功能，因此请先安装并配置好  [Mirai Console Loader](https://github.com/iTXTech/mirai-console-loader) 和 [mirai-api-http](https://github.com/project-mirai/mirai-api-http) 插件：

1. 安装 [Mirai Console Loader (MCL)](https://github.com/iTXTech/mirai-console-loader)。
1. 在 MCL 中配置 QQ 账号和密码，确保能正常登录账号，中途可能需要使用 [TxCaptchaHelper](https://github.com/mzdluo123/TxCaptchaHelper) 应对滑动验证码。
1. 为 MCL 安装 [mirai-api-http](https://github.com/project-mirai/mirai-api-http) 插件。
1. 在 mirai-api-http 的配置文件中启用 websocket 适配器。

LightQ 使用 Python 标准库的 [asyncio](https://docs.python.org/zh-cn/3/library/asyncio.html) 完成异步操作，如果你不熟悉 Python 的协程，可以先看看 Python 文档中[协程与任务](https://docs.python.org/zh-cn/3/library/asyncio-task.html)这一节。

## 简明教程
### 快速起步

```python
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
```

上述代码实现了一个最简单的 QQ 机器人，无论谁给它发消息，它都只会回复 Hello。

`message_handler` 装饰器将 `say_hello` 函数包装为一个 `MessageHandler` 对象，该消息处理器只会响应好友消息 `FriendMessage`。LightQ 还提供了 `event_handler` 和 `exception_handler` 装饰器，分别用于创建事件处理器和异常处理器。

`bot.add_all(scan_handlers(__name__))` 的作用是获取当前模块中所有 public 的 handler，并将它们添加到 `bot` 中。

- 注 1：[`__name__` 是 Python 中一个特殊的变量，表示当前模块的全限定名称](https://docs.python.org/zh-cn/3/reference/import.html#name__)。
- 注 2：在 Python 中不以下划线开头的变量为模块的 public 成员，另一种做法是在模块中用 `__all__` 列出所有 public 成员的名字。

一个合法的 handler 函数需要返回 `str` 或 `MessageChain` 或 `None`。Handler 函数既可以是同步函数也可以是异步函数。

```python
from lightq import message_handler
from lightq.entities import FriendMessage, MessageChain, Plain

@message_handler(FriendMessage)
async def say_hello() -> MessageChain:  # 一个返回 MessageChain 的异步函数
    await asyncio.sleep(1)
    return MessageChain([Plain('Hello')])
```

### 过滤器

如何实现 handler 的有条件执行？需要使用过滤器。我们继续改进之前的 `say_hello`：

```python
from lightq import RecvContext

def condition(context: RecvContext) -> bool:
    return str(context.data.message_chain) == 'Hello'

@message_handler(FriendMessage, filters=condition)
def say_hello() -> str:
    """当别人对 bot 说 Hello 时回复 Hello"""
    return 'Hello'
```

上面代码中的 `condition` 函数就是一个过滤器。`lightq.filters` 模块提供了一些现成的过滤器，可以直接使用。让我们再修改一下 `say_hello`，为它设置两个条件：

```python
from lightq import RecvContext, filters

def condition(context: RecvContext) -> bool:
    return str(context.data.message_chain) == 'Hello'

@message_handler(FriendMessage, filters=[filters.from_user(987654321), condition])
def say_hello() -> str:
    """当 QQ 号为 987654321 的用户对 bot 说 Hello 时回复 Hello"""
    return 'Hello'
```

### 参数解析
#### 基于类型的参数解析

如果你用过 Spring Boot 之类的 Web 框架，对于参数解析这个概念应该不会陌生。LightQ 框架支持基于类型和基于函数两种参数解析机制。下面这个示例展示了如何使用基于类型的参数解析：

```python
from lightq.entities import GroupMessage, MessageChain

@message_handler(GroupMessage)
def group_message_handler(chain: MessageChain):
    print(f'收到一条群组消息，内容为：{chain}')
```

注意到 `group_message_handler` 函数带有参数类型注解 `chain: MessageChain`，这个类型注解是不可或缺的。LightQ 框架使用 Python 的内省 (inspect) 机制获取 `chain` 参数的类型，接收到消息后解析出消息链对象，再自动地将消息链对象注入 `chain` 参数中。

参数解析机制的一个重要用途是在 handler 内获取 bot 的引用，并直接调用 bot 对象上的方法：

```python
@event_handler(NudgeEvent)
async def nudge_response(event: NudgeEvent, bot: Bot):
    """谁拍一拍我，我就拍一拍谁"""
    if (event.subject.kind == 'Group'
        and event.target == bot.bot_id
        and event.from_id != bot.bot_id):
        await bot.api.send_nudge(event.from_id, event.subject.id, 'Group')
```

LightQ 框架支持自动解析的类型有：

- `Bot`
- `RecvContext`
- `ExceptionContext`
- `MessageChain`
- `Message` 及其子类
- `Event` 及其子类
- `Exception` 及其子类

参数解析机制也支持自定义类型，只需让你自己的类型继承 `lightq.framework` 中的 `FromContext` / `FromRecvContext` / `FromExceptionContext` 抽象类并重写对应的方法即可。

#### 基于函数的参数解析

基于类型的参数解析无法覆盖所有场景，例如：希望从群组消息中解析出群号和发送者的 QQ 号，但二者皆为 `int` 类型，仅凭类型无法区分。此时需要使用基于函数的参数解析，请看如下例子：

```python
from lightq import resolvers  # resolvers 是一个模块
from lightq import resolve  # resolve 是一个装饰器

@resolve(resolvers.group_id, member_id=resolvers.sender_id)
@message_handler(GroupMessage)
def group_message_handler(chain: MessageChain, group_id: int, member_id: int):
    print(f'收到一条群组消息，群号 {group_id}，群员 QQ 号 {member_id}，内容为：{chain}')
```

`resolvers.group_id` 和 `resolvers.sender_id` 是两个类型为 `(RecvContext) -> int` 的函数，分别从 `RecvContext` 对象中解析出发送者的群号和 QQ 号，再配合 `resolve` 装饰器就可以实现参数解析和自动注入的效果。

使用 `resolve` 装饰器时，若以普通方式传参（上面的 `@resolve(resolvers.group_id)`），则根据解析器的 `__name__` 属性注入同名的参数（[Python 函数的 `__name__` 属性默认为该函数的名字](https://docs.python.org/zh-cn/3/library/stdtypes.html#definition.__name__)）；若以命名参数的方式传参（上面的 `@resolve(member_id=resolvers.sender_id)`），则表示手动指定注入参数。

本节的示例代码放在 [examples/resolver_example.py](./examples/resolver_example.py) 中。

### 正则表达式

`lightq.decorators` 模块中有三个很实用的装饰器：`regex_match`、`regex_search`、`regex_fullmatch`，分别对应 Python 标准库中的 `re.match`, `re.search`, `re.fullmatch`，可以通过正则表达式匹配消息的内容。

```python
import re
from lightq.decorators import regex_match

@regex_match('(?P<first_group>\w+) (?P<second_group>\w+)')
@message_handler(GroupMessage)
def handler(first_group: str, second_group: str, match: re.Match):
    assert first_group == match['first_group']
    assert second_group == match['second_group']
```

正则表达式中形如 `(?P<name>...)` 的是命名组语法。如果消息的内容与正则表达式相匹配，那么将捕获的组按照组的名字注入到 handler 的同名参数中，匹配对象将自动注入到类型为 `re.Match` 的参数中。

正则表达式装饰器可以用来构建 QQ 机器人的指令系统：

```python
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
```

`regex_match` 的实现非常简单，其原理是将过滤器和解析器构造出来插入 handler 中，并不需要引入额外的组件。你可以在 [src/lightq/decorators/_regex.py](./src/lightq/decorators/_regex.py) 找到其源代码。

### 设置 handler 的优先级

若不显式地指定 handler 间的优先关系，则机器人遍历各个 handler 的顺序是不确定的，这有时候会带来问题。以下是一个复读机程序，可通过“开始复读”和“停止复读”命令来开关复读功能。

```python
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
```

注意到，必须先判断 `switch` 的条件是否满足，然后再判断 `repeat` 的条件是否满足，即 `switch` 的优先级必须高于 `repeat`，否则当用户输入“停止复读”时，程序会继续复读“停止复读”这句话而不是把复读功能关掉。

怎样设置 handler 的优先级呢？有三种方法：

- 使用装饰器的 `after` 参数或 `before` 参数，如上述代码在 `repeat` 的装饰器中设置了 `after=switch`。
- 直接修改 handler 的 `after` 或 `before` 属性，如 `repeat.after.append(switch)`。
- 使用 `Bot` 的 `add_order` 方法，如 `bot.add_order(switch, repeat)`。

本节的示例代码放在 [examples/repeater.py](./examples/repeater.py) 中。

### 使用 controller

以上示例中所有的 bot 都是“一问一答”型，而一个具备连续对话能力的 bot 看起来会更加有趣：

```text
群友 1：/weather
Bot：您想查询哪个城市的天气？
群友 1：武汉
Bot：武汉的天气为小雨

群友 2：/mute_all
Bot：您确定要开启全员禁言吗？请回复“是”或“否”
群友 2：no
Bot：请回复“是”或“否”
群友 2：否
```

若要实现连续对话功能，就必须保存每个用户的状态。可以将状态保存到全局变量中。如果你不喜欢全局变量这种代码风格，也可以将状态封装到 controller 类中统一管理。Controller 类的编写方法如下：

```python
class MyController(lightq.Controller):  # 继承 lightq.Controller 类
    def __init__(self):
        self.status = ...  # 将状态作为成员变量封装到 controller 中

    # 过滤器方法
    def condition(self, context: RecvContext) -> bool: ...

    # 解析器方法
    def resolver(self, context: RecvContext): ...

    # 用 message_handler 装饰器将 my_handler 方法转换为消息处理器
    # - 使用 condition 方法作为过滤条件
    # - 使用 resolver 方法作为参数解析器
    @resolve(data=resolver)
    @message_handler(Message, filters=condition)
    def my_handler(self, data):
        self.status  # 在方法内部可以通过 self 引用保存的状态
        ...

controller = MyController()
# 通过 handlers 方法获取所有 public 的 handler
bot.add_all(controller.handlers())
# ...
```

[examples/assistant.py](./examples/assistant.py) 提供了一个完整的 controller 示例，实现了一个支持 `/weather` 和 `/mute_all` 命令的机器人。

此外，你还可以用 `handler_property` 装饰器将属性方法转换为处理器，示例代码见 [examples/assistant_property_style.py](./examples/assistant_property_style.py).

### 其他功能
#### 定时任务、后台任务

相关的函数和方法：

- `asyncio.sleep`：可用于延迟执行等场景。
- `lightq.utils.sleep_until`：延迟到某个时刻执行，该函数是对 `asyncio.sleep` 的简单封装。
- `Bot.create_task`：创建后台任务，该方法是对 `asyncio.create_task` 的简单封装。
- `Bot.create_everyday_task`：创建每日定时任务。

#### 日志

LightQ 使用 Python 标准库中的 `logging` 模块来打印日志，可通过 `lightq.logger` 获得 logger 对象。默认的日志打印级别为 INFO。

#### 自定义路由

LightQ 默认的路由会根据消息/事件/异常的类型将数据送给指定的 handler。你也可以根据实际场景设计更高效的路由机制。继承 `MessageRouter` / `EventRouter` / `ExceptionRouter` 抽象类（位于 `lightq.framework` 模块中）并重写对应的方法以实现自定义路由机制。

## 未来

（可能是）将来的一些工作：

- 完善文档
- 支持文件操作
- 补齐剩余的 API 功能
- 中间件/钩子函数？
