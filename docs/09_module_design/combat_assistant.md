# 战斗辅助模块设计

版本：v0.4  
状态：Implemented / Living Document  
最后核对：2026-06-19

---

# 1 模块目标

战斗辅助模块用于 DND5E 房间管理先攻表、轮数、当前回合和参战 token。当前实现以轻量 JSON 状态存储在房间 tabletop settings 中：

```text
room_tabletop_settings.combat_state
```

---

# 2 当前能力

已落地：

- GM 开启战斗。
- GM 结束战斗。
- 开启战斗时选择当前场上 token。
- 自动根据每个 token 的先攻加值投掷先攻。
- 自动写入掷骰日志，标签为“先攻掷骰”。
- 按先攻排序显示先攻轴。
- 先攻相同情况下，PL token 优先于非 PL token。
- 当前回合 token 高亮。
- 轮数显示。
- 当前 token 归属玩家可结束回合。
- GM 可强制结束回合。
- GM 可编辑参战 token。
- GM 可右键先攻轴 token：
  - 设置为当前回合。
  - 设置为本轮行动。
  - 设置为下轮行动。
- 若当前回合 token 被设置为下轮行动，回合自动推进到下一位。
- 场上 token 被删除时，应从战斗先攻轴移除。
- token 可通过右键菜单加入当前战斗（仅 GM 可见，且战斗开启时有效）。

---

# 3 前端组件

主要组件：

```text
frontend/src/features/table/components/CombatPanel.vue
frontend/src/features/table/components/CombatTokenAvatar.vue
```

位置：

- 战斗面板位于房间页面底部中间。
- 非战斗状态显示“当前没有战斗”。
- 战斗状态下水平显示先攻轴，每个 token 使用头像上、名称下的样式。

交互：

- 单击先攻轴 token：选中桌面对应 token 并显示信息面板。
- 双击先攻轴 token：平滑移动视窗到对应 token。
- hover 不改变布局高度。

---

# 4 开启 / 编辑战斗弹窗

GM 开启或编辑战斗时，弹窗分上下两块：

```text
未参战 token
已参战 token
```

点击 token 在上下区域间移动。样式与先攻轴保持一致。

中途加入战斗规则：

- 新加入 token 立即投掷先攻。
- 根据先攻值插入先攻队列对应位置。
- 本轮没有回合，到下一轮才可行动。
- UI 需要用特殊样式表示“本轮没有回合”。

---

# 5 状态模型

当前状态存储为 JSON，建议概念结构：

```json
{
  "active": true,
  "round": 1,
  "turn_index": 0,
  "participants": [
    {
      "token_id": 1,
      "initiative": 17,
      "initiative_roll": 14,
      "initiative_bonus": 3,
      "acts_this_round": true
    }
  ]
}
```

字段说明：

- `round`：当前轮数。
- `turn_index`：当前回合在 participants 中的位置。
- `initiative`：最终先攻值。
- `initiative_roll`：d20 自然结果。
- `initiative_bonus`：先攻加值。
- `acts_this_round`：本轮是否有回合。中途加入的 token 在当前轮为 `false`。

---

# 6 权限规则

| 操作 | GM | 当前 token 归属 PL | 其他 PL/OB |
|---|---|---|---|
| 查看战斗面板 | ✓ | ✓ | ✓ |
| 开启 / 结束战斗 | ✓ | — | — |
| 编辑参战 token | ✓ | — | — |
| 设置当前回合 | ✓ | — | — |
| 设置本轮/下轮行动 | ✓ | — | — |
| 结束当前回合 | ✓ | 当前回合属于自己时 ✓ | — |
| 右键 token 加入战斗 | ✓ | — | — |

---

# 7 同步方式

当前没有单独 combat WebSocket event。

战斗状态作为 tabletop settings 的一部分写入，触发：

```text
tabletop_settings_updated
```

所有客户端收到后更新战斗面板。

---

# 8 与骰子模块关系

开启战斗时，每个参与 token 会自动进行先攻投掷：

- 使用 token 的先攻加值。
- 生成掷骰记录。
- 标签为“先攻掷骰”。
- 主体为对应 token。

---

# 9 后续

- 为 `combat_state` 定义正式 schema。
- 为战斗状态变更增加后端单元测试。
- 若未来战斗系统复杂化，可拆出独立 `room_combats` / `room_combat_participants` 表。
- 接入状态持续时间、专注检定提醒、死亡豁免、短休/长休恢复等 DND 自动化。
