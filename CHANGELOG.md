# 更新日志
## [0.3.0] - 2022-11-21
### 新增

`MiraiApi` 新增 `bot_list` 方法，用于获取已登录的 QQ 号。

### 修复

修复了 `MiraiApi` 不能多次 `close` 和 `connect` 的问题。

### 变更

依赖的 mirai-api-http 版本从 2.5.x 升级至 2.6.x。

由于升级后 mirai-api-http 的接口发生了变更，因此 `MiraiApi` 类的一些方法的参数发生了变化：

- `message_from_id`
- `recall`
- `set_essence`

## [0.2.0] - 2022-09-08
### 新增

- `message_handler`、`event_handler`、`exception_handler` 和 `resolve` 装饰器可以直接用于装饰 `Controller` 类的方法，无需像 0.1.0 中那样额外用 `handler_property` 定义属性方法
- 支持在处理器方法上使用正则表达式装饰器
- 新增群公告相关 API
- 支持在 `message_handler` 和 `event_handler` 装饰器中使用基类类型，如 `@message_handler(Message) ...`

### 修复

- 修复了 `handler_property` 错误的缓存行为
- 修复了 `Controller.handlers` 无法获取从基类继承的 handler 的问题
- 修复并完善类型标注

### 变更

`Controller` 类的 `handlers`、`message_handlers`、`event_handlers` 和 `exception_handlers` 由属性改为方法。

## [0.1.0] - 2022-08-11

第一个版本
