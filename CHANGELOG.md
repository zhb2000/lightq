# 更新日志
## [0.2.0] - 2022-09-08
### 新增

- `message_handler`、`event_handler`、`exception_handler` 和 `resolve` 装饰器可以直接用于装饰 `Controller` 类的方法，无需像 0.1.0 中那样额外用 `handler_property` 定义属性方法
- 支持在处理器方法上使用正则表达式装饰器
- 新增群公告相关 API

### 修复

- 修复了 `handler_property` 错误的缓存行为
- 修复了 `Controller.handlers` 无法获取从基类继承的 handler 的问题
- 修复并完善类型标注

### 变更

`Controller` 类的 `handlers`、`message_handlers`、`event_handlers` 和 `exception_handlers` 由属性改为方法。

## [0.1.0] - 2022-08-11

第一个版本
