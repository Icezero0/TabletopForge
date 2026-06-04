# Step 5：角色与 Token 核心

**目标**：底栏「添加角色」、左上 **场上角色列表**、地图 **Token**、右侧 **InfoPanel** 单槽联通；角色 **稳定层 + CharacterState** 分离。本步完成 PRD 跑团桌面 **MVP 闭环**。

**依据**：`docs/09_module_design/character_card.md`、`token_system.md`、`docs/01` §4.2.3–4.2.5。

---

## 数据与 API（概要）

- `characters`（稳定层）+ `character_states`（实时层），`created_by_user_id`。
- 自定义 key/value（JSON 或附表）。
- Token：绑定 `character_id`，位置/缩放/**Token 类内** z-index（band 基准 100）/实例名。
- 业务 asset：`token_image`；无图 → **名称首字**。
- 怪物 HP：GM 看 CharacterState 全量；PL 看 **伤害记录** 接口字段过滤。

---

## 本步做

### 5.1 角色资源（含「导入」边界）

| 类型 | 稳定层 | 状态层 | 谁可建 |
|---|---|---|---|
| 主 PC | 六维/技能手填、预览字段、RP 第1/2页大文本、自定义 KV | HP/AC/Buff | PL 自建 |
| 附加角色 | 名称+简字段+大文本 | HP/AC 等 | PL 自建 |
| 怪物 | 大文本为主 | HP 等 | GM |

**「角色导入」本步边界**：

- **做**：表单创建 + 可选 Token 图上传；从 **房间角色库** 选已有定义「上场」。
- **不做**：外部文件批量导入（JSON/XML）、完整 DND5E 规则书导入（放 `01` §4.3）。
- **不做**：属性/技能自动计算。

### 5.2 Token 与地图联动

- Token band（基准 z=100）；拖拽、缩放；菜单：查看信息、删除（权限见 `08` §6.4）；**图层**菜单只调 Token 类内顺序。
- 同一 `character_id` 可多个 Token（复用）。
- 地图 HP 预览读 CharacterState。

### 5.3 右侧 InfoPanel

- **单槽**，新查看 **替换** 旧。
- GM 怪物：实例名（可改）、已受伤害、详情大文本。
- PL/角色：按权限展示稳定层 + 状态层字段。
- PersonalMemo 已在 Step 3 经 HTTP 持久化；本步仅扩展与 InfoPanel 联动（如有需要）。

### 5.4 左上列表

- 切换为 **场上角色列表**（名称、HP 摘要、是否已上场）。
- 「上场」→ 在地图创建 Token。
- 成员治理仍在 Step 3 入口，与本列表并存。

---

## 本步不做

- 测距、Token 移动可达判定。
- Campaign / Session / Scene。
- `game_role=OB` 完整体验。
- 操作日志全量、战斗先攻、骰子/RP。

---

## 验收清单

- [ ] PL 创建主 PC + 附加角色，仅管理自己创建的资源。
- [ ] GM 创建怪物，PL 不可改正文，仅见伤害记录。
- [ ] 角色库复用 → 多 Token 同定义。
- [ ] 无图 Token 显示首字；点击查看 InfoPanel。
- [ ] 与 Step 4 地图/绘制同屏协作无冲突。

---

## 依赖

- Step 1–4 完成。

---

## MVP 完成定义

完成 Step 5 后，对照 `docs/01` §6「跑团桌面 MVP」成功标准做一次总验收，并更新 `docs/10_repository_status.md` §4.1/4.2 实现对照表。
