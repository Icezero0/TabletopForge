# TabletopForge MVP 推进笔记

本目录记录 **分步实现边界**，与正式设计文档配合使用，不替代 `docs/`。

| 正式文档 | 用途 |
|---|---|
| [`docs/01_product_requirements.md`](../docs/01_product_requirements.md) §4–5 | 产品范围与页面 PRD |
| [`docs/03_frontend_design.md`](../docs/03_frontend_design.md) §4.2 | 跑团主界面布局 |
| [`docs/08_permission_design.md`](../docs/08_permission_design.md) | 身份与 Tabletop 权限 |
| [`docs/10_repository_status.md`](../docs/10_repository_status.md) | 代码已实现对照 |

## 推进顺序

```text
Step 1  基础身份与房间治理 ──► Step 2  主界面空壳布局
        │                              │
        └──────────────► Step 3  迁入已有功能 ◄────────────┘
                              │
                    Step 4  地图核心
                              │
                    Step 5  角色 / Token 核心
```

| 步骤 | 文档 | 一句话 |
|---|---|---|
| 1 | [01-identity-and-room.md](./01-identity-and-room.md) | `game_role`、房间 CRUD、拉人/入房、身份配置 |
| 2 | [02-table-layout-shell.md](./02-table-layout-shell.md) | 五区布局占位，工具栏槽位，不接业务 |
| 3 | [03-integrate-existing.md](./03-integrate-existing.md) | 聊天、成员、审批、设置等迁入新壳 |
| 4 | [04-map-core.md](./04-map-core.md) | 地图导入、网格、锁定、图层、绘制 |
| 5 | [05-character-core.md](./05-character-core.md) | 角色库、稳定层/状态层、Token 上场 |

## 原则

- 每步 **可独立验收**，完成后再开下一步。
- 每步写明 **做 / 不做**，避免范围蔓延。
- 与 PRD 冲突时以 `docs/01` 为准（例如：**测距不在 MVP**，Step 2 仅预留按钮）。

## 状态

| 步骤 | 状态 |
|---|---|
| 1 | 已完成 |
| 2 | 已完成 |
| 3 | 未开始 |
| 4 | 未开始 |
| 5 | 未开始 |
