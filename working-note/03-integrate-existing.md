# Step 3：迁入已有功能

**目标**：在 Step 2 布局壳内，接回 **Phase 1 已实现** 的能力，跑团桌可正常「进群、聊天、管人」，中央地图区仍可为空网格。本步 **不** 做地图/角色新业务表。

**依据**：`docs/10` §4.1、`docs/01` §5.10。

> **说明**：Step 2 实现时已迁入聊天、成员治理、入房请求与房间设置。本步完成 **验收对齐、备忘录 HTTP 持久化、场上角色列表占位**，以及文档收尾。

---

## 迁入清单

| 能力 | 原位置 | 迁入目标 | 状态 |
|---|---|---|---|
| 普通聊天 | `RoomChatTab` | 左下 `FloatingPanel` | ✓ Step 2 |
| 房间成员 | `RoomMembersTab` | `GovernanceDock` 成员 Tab | ✓ Step 2 |
| 入房请求 | `RoomRequestsTab` | 治理面板请求 Tab | ✓ Step 2 |
| 房间设置 | `RoomSettingsTab` | 治理面板设置 Tab | ✓ Step 2 |
| 实时会话 | `useRoomRealtimeSession` | 房间级 bootstrap | ✓ Step 2 |
| 个人备忘录 | — | `GET/PUT /rooms/{id}/personal-memo` | ✓ Step 3 |
| 场上角色列表 | — | 左上 `InGameCharacterList` 空态 | ✓ Step 3（Step 5 业务数据） |

---

## 本步做

- 对照 Step 3 验收清单做回归（聊天 WS、审批、改 `game_role`、设置保存）。
- 个人备忘录：按 PRD **按房间、仅自己可见** 接 HTTP API（`room_personal_memos`）。
- 左上治理区与 **场上角色** 面板区分展示（后者空态）。
- 同步更新 `docs/10`、`docs/03` §4.2 示意图。

---

## 本步不做

- 地图底图、绘制层、Token（Step 4–5）。
- 新角色/怪物 CRUD。
- InfoPanel 绑定 Token/角色详情（Step 5）。
- 测距、Pointer 实时。

---

## 验收清单

- [x] 房间内聊天与线上一致（刷新、WS）— Step 2 已具备，本步复核。
- [x] 审批入房、成员列表、改 game_role 在新布局下可用 — Step 2 已具备，本步复核。
- [x] 房间设置保存生效 — Step 2 已具备，本步复核。
- [x] 中央仍为网格占位，无回归旧版全屏 Tab 布局。
- [x] 个人备忘录按房间 HTTP 持久化（用户隔离）。

---

## 依赖

- **Step 1** 完成。
- **Step 2** 完成。

**Step 3 状态：已完成**（2026-06-04）。
