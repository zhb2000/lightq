import abc
import importlib
import typing
from dataclasses import dataclass
from typing import Any, Iterable, SupportsIndex, overload, TypeVar, cast

from . import _mixin as mixin
from ._entity import Entity, UnsupportedEntity
from .._from_context import FromContext

if typing.TYPE_CHECKING:
    from ._message import Message
    from ._sync_message import SyncMessage
    from ..framework import RecvContext

__all__ = [
    'MessageElement',
    'MessageChain',
    'UnsupportedMessageElement',
    'Source',
    'Quote',
    'At',
    'AtAll',
    'Face',
    'Plain',
    'Image',
    'FlashImage',
    'Voice',
    'Xml',
    'Json',
    'App',
    'Poke',
    'Dice',
    'MarketFace',
    'MusicShare',
    'Forward',
    'File',
    'MiraiCode'
]


class MessageElement(Entity, abc.ABC):
    @abc.abstractclassmethod
    def to_json(self) -> dict[str, Any]:
        raise NotImplementedError

    @classmethod
    def from_json(cls, obj: dict[str, Any]) -> 'MessageElement':
        return message_element_from_json(obj)


MessageElementType = TypeVar('MessageElementType', bound=MessageElement)


class UnsupportedMessageElement(UnsupportedEntity, MessageElement):
    pass


class MessageChain(list[MessageElement], FromContext, Entity):
    def __init__(self, elements: Iterable[MessageElement] = ()):
        super().__init__(elements)
        assert all(isinstance(e, MessageElement) for e in self)

    def to_json(self) -> list[dict[str, Any]]:
        return [element.to_json() for element in self]

    @overload
    def get(
        self,
        index: type[MessageElementType],
        default: MessageElementType | None = None
    ) -> MessageElementType | None: pass

    @overload
    def get(
        self,
        index: SupportsIndex,
        default: MessageElement | None = None
    ) -> MessageElement | None: pass

    def get(self, index, default=None):
        try:
            return self[index]
        except IndexError:
            return default

    def get_all(self, element_type: type[MessageElementType]) -> list[MessageElementType]:
        return [e for e in self if isinstance(e, element_type)]

    def copy(self) -> 'MessageChain':
        return MessageChain(self)

    def __add__(self, other: MessageElement | Iterable[MessageElement]) -> 'MessageChain':
        if isinstance(other, MessageElement):
            other = (other,)
        return MessageChain([*self, *other])

    def __contains__(self, item: MessageElement | type[MessageElement]) -> bool:
        if isinstance(item, type):
            assert issubclass(item, MessageElement)
            return any(isinstance(e, item) for e in self)
        else:
            return super().__contains__(item)

    def __eq__(self, other) -> bool:
        return isinstance(other, MessageChain) and super().__eq__(other)

    @overload
    def __getitem__(self, index: slice) -> 'MessageChain': pass

    @overload
    def __getitem__(self, index: type[MessageElementType]) -> MessageElementType: pass

    @overload
    def __getitem__(self, index: SupportsIndex) -> MessageElement: pass

    def __getitem__(self, index):
        if isinstance(index, type):
            assert issubclass(index, MessageElement)
            for e in self:
                if isinstance(e, index):
                    return e
            raise IndexError(f'no {index.__name__} element in message chain')
        if isinstance(index, slice):
            return MessageChain(super().__getitem__(index))
        else:
            return super().__getitem__(index)

    def __iadd__(self, other: MessageElement | Iterable[MessageElement]) -> 'MessageChain':
        if isinstance(other, MessageElement):
            self.append(other)
        else:
            self.extend(other)
        return self

    def __imul__(self, n: SupportsIndex) -> 'MessageChain':
        super().__imul__(n)
        return self

    def __mul__(self, n: SupportsIndex) -> 'MessageChain':
        return MessageChain(super().__mul__(n))

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __repr__(self) -> str:
        return f'MessageChain({super().__repr__()})'

    def __str__(self) -> str:
        return ''.join(str(e) for e in self if not isinstance(e, Source | UnsupportedMessageElement))

    def __rmul__(self, n: SupportsIndex) -> 'MessageChain':
        return self * n

    @classmethod
    def from_json(cls, obj: list[dict[str, Any]]) -> 'MessageChain':
        return MessageChain([MessageElement.from_json(e) for e in obj])

    @classmethod
    def from_recv_context(cls, context: 'RecvContext') -> 'MessageChain':
        return cast('Message | SyncMessage', context.data).message_chain


class AbstractMessageElement(mixin.FromJson, mixin.ToJson, MessageElement, abc.ABC):
    pass


@dataclass
class Source(AbstractMessageElement):
    """消息来源元数据"""

    id: int
    """消息的识别号，用于引用回复（Source 类型永远为 chain 的第一个元素）"""

    time: int
    """时间戳"""


@dataclass
class Quote(AbstractMessageElement):
    id: int
    """被引用回复的原消息的 messageId"""

    group_id: int
    """被引用回复的原消息所接收的群号，当为好友消息时为 0"""

    sender_id: int
    """被引用回复的原消息的发送者的 QQ 号"""

    target_id: int
    """被引用回复的原消息的接收者者的 QQ 号（或群号）"""

    origin: MessageChain
    """被引用回复的原消息的消息链对象"""

    def __str__(self) -> str:
        return '[引用消息]'


@dataclass
class At(AbstractMessageElement):
    """提及某人"""

    target: int
    """群员 QQ 号"""

    display: str = ''
    """At 时显示的文字，发送消息时无效，自动使用群名片"""

    def __str__(self) -> str:
        return f'@{self.target}'


@dataclass
class AtAll(AbstractMessageElement):
    """提及全体成员"""

    def __str__(self) -> str:
        return '@全体成员'


@dataclass
class Face(AbstractMessageElement):
    """原生表情"""

    face_id: int | None = None
    """QQ 表情编号，可选，优先高于 name"""

    name: str | None = None
    """QQ 表情拼音，可选"""

    def __str__(self) -> str:
        return f'[{self.name}]'


@dataclass
class Plain(AbstractMessageElement):
    """纯文本"""

    text: str
    """文字消息"""

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return f'Plain({self.text!r})'


@dataclass
class Image(AbstractMessageElement):
    """
    自定义图片

    三个参数任选其一，出现多个参数时，按照 imageId > url > path > base64 的优先级
    """

    image_id: str | None = None
    """图片的 imageId，群图片与好友图片格式不同。不为空时将忽略 url 属性"""

    url: str | None = None
    """图片的 URL，发送时可作网络图片的链接；接收时为腾讯图片服务器的链接，可用于图片下载"""

    path: str | None = None
    """
    图片的路径，发送本地图片，路径相对于 JVM 工作路径（默认是当前路径，可通过
    -Duser.dir=... 指定），也可传入绝对路径。
    """

    base64: str | None = None
    """图片的 Base64 编码"""

    def __str__(self) -> str:
        return '[图片]'


@dataclass
class FlashImage(AbstractMessageElement):
    """
    闪照

    同 ``Image``，三个参数任选其一，出现多个参数时，按照 imageId > url > path > base64 的优先级
    """

    image_id: str | None = None
    url: str | None = None
    path: str | None = None
    base64: str | None = None

    def __str__(self) -> str:
        return '[闪照]'


@dataclass
class Voice(AbstractMessageElement):
    """
    语音

    三个参数任选其一，出现多个参数时，按照 voiceId > url > path > base64 的优先级
    """

    voice_id: str | None = None
    """语音的 voiceId，不为空时将忽略 url 属性"""

    url: str | None = None
    """语音的URL，发送时可作网络语音的链接；接收时为腾讯语音服务器的链接，可用于语音下载"""

    path: str | None = None
    """
    语音的路径，发送本地语音，路径相对于 JVM 工作路径（默认是当前路径，可通过
    -Duser.dir=... 指定），也可传入绝对路径。
    """

    base64: str | None = None
    """语音的 Base64 编码"""

    length: int | None = None
    """返回的语音长度, 发送消息时可以不传"""

    def __str__(self) -> str:
        return '[语音消息]'


@dataclass
class Xml(AbstractMessageElement):
    xml: str
    """XML 文本"""

    def __str__(self) -> str:
        return '[XML]'

    def __repr__(self) -> str:
        return f'Xml({self.xml}!r)'


@dataclass
class Json(AbstractMessageElement):
    json: str
    """JSON 文本"""

    def __str__(self) -> str:
        return '[JSON]'

    def __repr__(self) -> str:
        return f'Json({self.json}!r)'


@dataclass
class App(AbstractMessageElement):
    content: str
    """内容"""

    def __str__(self) -> str:
        return '[APP]'

    def __repr__(self) -> str:
        return f'App({self.content}!r)'


@dataclass
class Poke(AbstractMessageElement):
    """
    戳一戳消息（消息非动作）

    戳一戳的类型：

    - ``"Poke"``: 戳一戳
    - ``"ShowLove"``: 比心
    - ``"Like"``: 点赞
    - ``"Heartbroken"``: 心碎
    - ``"SixSixSix"``: 666
    - ``"FangDaZhao"``: 放大招
    """

    name: str
    """戳一戳的类型"""

    def __str__(self) -> str:
        return '[戳一戳]'

    def __repr__(self) -> str:
        return f'Poke({self.name}!r)'


@dataclass
class Dice(AbstractMessageElement):
    """魔法表情骰子"""

    value: int
    """点数"""

    def __str__(self) -> str:
        return f'[骰子:{self.value}]'

    def __repr__(self) -> str:
        return f'Dice({self.value}!r)'


@dataclass
class MarketFace(AbstractMessageElement):
    """
    商城表情

    目前商城表情仅支持接收和转发，不支持构造发送
    """

    id: int
    """商城表情唯一标识"""

    name: str
    """表情显示名称"""

    def __str__(self) -> str:
        return self.name if self.name.startswith('[') and self.name.endswith(']') else f'[{self.name}]'


@dataclass
class MusicShare(AbstractMessageElement):
    """音乐分享"""

    kind: str
    """类型"""

    title: str
    """标题"""

    summary: str
    """概括"""

    jump_url: str
    """跳转路径"""

    picture_url: str
    """封面路径"""

    music_url: str
    """音源路径"""

    brief: str
    """简介"""

    def __str__(self) -> str:
        return f'[分享]{self.title}'


@dataclass
class Forward(AbstractMessageElement):
    """合并转发"""

    @dataclass
    class Node(mixin.FromJsonWithoutType, mixin.ToJsonWithoutType, Entity):
        sender_id: int
        """发送人QQ号"""

        time: int
        """发送时间"""

        sender_name: str
        """显示名称"""

        message_chain: MessageChain
        """消息数组"""

        message_id: str
        """可以只使用消息 messageId，从缓存中读取一条消息作为节点"""

    node_list: list[Node]
    """消息节点"""

    def __str__(self) -> str:
        return '[转发消息]'

    def __repr__(self) -> str:
        return f'Forward({self.node_list}!r)'


@dataclass
class File(AbstractMessageElement):
    """文件消息"""

    id: str
    """文件识别 id"""

    name: str
    """文件名"""

    size: int
    """文件大小"""

    def __str__(self) -> str:
        return f'[文件]{self.name}'


@dataclass
class MiraiCode(AbstractMessageElement):
    """Mirai 码"""

    code: str
    """Mirai 码"""

    def __str__(self) -> str:
        return self.code

    def __repr__(self) -> str:
        return f'MiraiCode({self.code}!r)'


def make_class_dict() -> dict[str, type[MessageElement]]:
    module = importlib.import_module(__name__)
    exclude = {'MessageElement', 'MessageChain', 'UnsupportedMessageElement', 'MESSAGE_ELEMENT_CLASSES'}
    return {name: getattr(module, name) for name in __all__ if name not in exclude}


MESSAGE_ELEMENT_CLASSES = make_class_dict()


def message_element_from_json(obj: dict[str, Any]) -> MessageElement:
    cls = MESSAGE_ELEMENT_CLASSES.get(obj['type'], UnsupportedMessageElement)
    return cls.from_json(obj)
