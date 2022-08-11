import abc
import functools
from typing import Any, TypeVar

Self = TypeVar('Self')


class MiraiApiException(Exception, abc.ABC):
    code: int

    def __init__(self, response: dict[str, Any]):
        self.message = response.get('msg', '')
        self.response = response

    def __repr__(self) -> str:
        return f'{type(self).__name__}(code={self.code}, message={repr(self.message)})'

    @classmethod
    def from_response(cls: type[Self], response: dict[str, Any]) -> Self:
        return _mirai_api_exception_from_response(cls, response)


class UnsupportedApiException(MiraiApiException):
    def __init__(self, response: dict[str, Any]):
        super().__init__(response)
        self.code = response['code']


class WrongVerifyKey(MiraiApiException):
    """
    错误的 verify key（状态码 1）
    """
    code = 1


class BotNotExist(MiraiApiException):
    """
    指定的 bot 不存在（状态码 2）
    """
    code = 2


class InvalidSession(MiraiApiException):
    """
    Session 失效或不存在（状态码 3）
    """
    code = 3


class InactiveSession(MiraiApiException):
    """
    Session 未认证（未激活）（状态码 4）
    """
    code = 4


class TargetNotExist(MiraiApiException):
    """
    发送消息目标不存在（指定对象不存在）（状态码 5）
    """
    code = 5


class FileNotExist(MiraiApiException):
    """
    指定文件不存在，出现于发送本地图片（状态码 6）
    """
    code = 6


class NoPermission(MiraiApiException):
    """
    无操作权限，指 bot 没有对应操作的限权（状态码 10）
    """
    code = 10


class BotInSilence(MiraiApiException):
    """
    Bot 被禁言，指 bot 当前无法向指定群发送消息（状态码 20）
    """
    code = 20


class MessageTooLong(MiraiApiException):
    """
    消息过长（状态码 30）
    """
    code = 30


class IncorrectAccess(MiraiApiException):
    """
    错误的访问，如参数错误等（状态码 400）
    """
    code = 400


CODE_TO_EXCEPTION = {
    1: WrongVerifyKey,
    2: BotNotExist,
    3: InvalidSession,
    4: InactiveSession,
    5: TargetNotExist,
    6: FileNotExist,
    10: NoPermission,
    20: BotInSilence,
    30: MessageTooLong,
    400: IncorrectAccess
}


def _mirai_api_exception_from_response(cls: type[Self], response: dict[str, Any]) -> Self:
    code: int = response['code']
    exception_class = CODE_TO_EXCEPTION.get(code, UnsupportedApiException)
    if cls != MiraiApiException:
        assert exception_class == cls
    return exception_class(response)
