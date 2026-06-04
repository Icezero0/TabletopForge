# 核心业务模块设计目录

本目录维护 TabletopForge 各核心业务模块的详细设计。

当前包含：

```text
character_card.md       角色卡模块
dnd5e_rules.md          DND5E 规则计算模块
tabletop_scene.md       场景与地图模块
token_system.md         Token 模块
asset_library.md        资源库模块
chat_and_rp.md          普通聊天与 RP 模块
dice.md                 骰子模块
operation_log.md        操作日志模块
combat_assistant.md     战斗辅助模块
```

模块文档用于维护模块目标、核心概念、数据模型、前端交互、后端服务、API、WebSocket 事件、权限与后续扩展。

跑团桌面 MVP 以 `tabletop_scene.md`、`token_system.md`、`character_card.md`（v0.3）为准；权限映射见 `08_permission_design.md` §6.4，不新增 `game_role` 字段。
