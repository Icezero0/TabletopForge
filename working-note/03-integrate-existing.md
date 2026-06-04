# Step 3：迁入已有功能

**目标**：在 Step 2 布局壳内，接回 **Phase 1 已实现** 的能力，跑团桌可正常「进群、聊天、管人」，中央地图区仍可为空网格。本步 **不** 做地图/角色新业务表。

**依据**：`docs/10` §4.1、`docs/01` §5.10。

---

## 迁入清单

| 能力 | 原位置 | 迁入目标 | 说明 |
|---|---|---|---|
| 普通聊天 | `RoomChatTab` / `ChatPanel` | `ChatFloatingPanel` | 保留 WS、`messages.store` |
| 房间成员 | `RoomMembersTab` 等 | 左上列表 **或** 治理抽屉 | 与「场上角色列表」UI 可并存：成员 vs 角色 Step 5 再分 |
| 入房请求 | `RoomRequestsTab` | 治理入口 / 抽屉 | owner/manager 可见 |
| 房间设置 | `RoomSettingsTab` | 设置入口 | 对接 Step 1 房间配置 |
| 实时会话 | `useRoomRealtimeSession` | 房间级 bootstrap | 消息、成员事件 |
| 首次进入 sync gate | `router` meta | 保持 | 避免消息竞态 |

### 建议：Step 3 左上列表

本步左上可暂显示 **房间成员**（用户昵称 + `room_role` / `game_role`），邀请入口链到已有邀请/公开房间流程。  
**场上角色列表**（角色卡摘要）留给 Step 5，避免与成员列表混淆。

---

## 本步做

- 删除或降级旧 **右侧主 Tab 条** 为次要入口（避免双轨 UI）。
- 聊天在悬浮窗内完整可用（发、收、滚动）。
- 成员管理、踢人、设 manager、改 `game_role`（Step 1 API）在治理 UI 可用。
- 个人备忘录：若本步做持久化，按 PRD **按房间、仅自己可见** 接 API；也可标为 Step 5 前的小任务。

---

## 本步不做

- 地图底图、绘制层、Token（Step 4–5）。
- 新角色/怪物 CRUD。
- InfoPanel 绑定 Token/角色详情（Step 5）。
- 测距、Pointer 实时。

---

## 验收清单

- [ ] 房间内聊天与线上一致（刷新、WS）。
- [ ] 审批入房、成员列表、改 game_role 在新布局下可用。
- [ ] 房间设置保存生效。
- [ ] 中央仍为网格占位，无回归旧版全屏 Tab 布局。

---

## 依赖

- **Step 1** 完成（`game_role`、房间设置 API）。
- **Step 2** 完成（布局壳）。
