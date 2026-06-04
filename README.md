# TabletopForge 文档入口

本文档目录用于维护 TabletopForge 的产品、系统、前端、后端、接口、实时协议、数据库、权限与核心业务模块设计。

**文档与代码对照**：实现进度见 [`docs/10_repository_status.md`](docs/10_repository_status.md)；产品范围见 [`docs/01_product_requirements.md`](docs/01_product_requirements.md) §4；**各页面功能 / 布局 / 交互流** 见同文档 §5。

TabletopForge 是一个面向 TRPG / DND 跑团场景的在线协作桌面系统，目标是提供房间、角色卡、地图桌面、Token、聊天、RP、骰子、日志与实时同步能力。

## 文档结构

```text
README.md
docs/
├── 00_overview.md              # 系统设计总览
├── 01_product_requirements.md  # 产品需求与阶段目标
├── 02_architecture.md          # 系统架构设计
├── 03_frontend_design.md       # 前端设计
├── 04_backend_design.md        # 后端设计
├── 05_api_design.md            # HTTP API 设计
├── 06_websocket_protocol.md    # WebSocket 协议设计
├── 07_database_design.md       # 数据库设计
├── 08_permission_design.md     # 权限设计
├── 09_module_design/           # 核心业务模块设计（tabletop / token / 角色卡等）
└── 10_repository_status.md     # 仓库现状（代码与文档落地对照，随实现更新）
```

## 文档维护原则

1. 总览文档只描述系统边界、核心概念和模块关系，不承载过多实现细节。
2. 前端、后端、API、WebSocket、数据库、权限文档分别维护对应领域的设计。
3. 业务模块细节放入 `09_module_design/` 下独立维护。
4. 文档应与代码同步更新，避免只在代码中隐含业务规则。
