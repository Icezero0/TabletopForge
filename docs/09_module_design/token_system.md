# Token 模块设计

版本：v0.3  
状态：Draft

---

# 1 模块目标

Token 模块用于维护地图桌面（z-index **1** 层）上的可操作对象，包括玩家角色 Token、怪物 Token 等。

---

# 2 核心属性

Token 包含：

- 所属房间
- 资源图片（可选；见 character_card §3.4 缺省首字）
- 绑定角色（`character_id`；同一角色定义可对应多个 Token 实例以复用）
- 名称
- 类型（`character` | `monster` | 后续扩展）
- 场景坐标、尺寸、旋转
- 层内 z-index（相对同层其他 Token）
- 锁定状态（可选，与地图底图锁定区分）
- 关联用户（玩家 Token 可选）

怪物类型 Token 另关联怪物信息（MVP 为大文本字段，见 `character_card.md`）。

---

# 3 前端交互

- 从房间角色库 **复用** 已有定义创建 Token
- 创建 / 编辑 Token（DM 任意定义；member 仅自己创建的角色定义）
- 拖拽、缩放（权限内）
- 选中 Token
- **删除**：选中 → **右键 Context Menu → 删除**（未选中不可删）
- 绑定角色
- 地图上的 **HP 预览**（角色 Token）；怪物 Token 对 member 不显示精确 HP

角色 Token 点击打开角色详情（侧栏 / 抽屉）。怪物 Token：DM 看全量信息与 HP；member 仅看 **累计受伤害 / 伤害记录**。

**缺省图**：绑定角色无 Token 图时，显示 **名称首字**（与 `character_card.md` §3.4 一致）。

---

# 4 权限规则

通过 `room_role` 判定，见 `08_permission_design.md` §6.4：

- `owner` / `manager`：所有 Token 的增删改、移动。
- `member`：移动绑定 **自己创建的角色定义** 的 Token（含主 PC 与附加角色）；仅可为自己创建的定义新建 Token；不可删除 / 新建 DM 怪物 Token。

---

# 5 可见性与 HP

| 对象 | owner / manager | member |
|---|---|---|
| 角色 Token HP | 精确当前 HP 等 | 己方角色可见；他人按角色卡权限 |
| 怪物 Token HP | 精确 current / max HP | **不展示**精确 HP；仅 **伤害记录 / 累计受伤害** |
| 怪物详情正文 | 可读可编（DM） | 不展示完整私密字段（MVP 怪物为大文本，member 不看 DM 编辑区） |

服务端存储权威 HP；对 member 的 API / WS payload 过滤精确怪物 HP 字段。

---

# 6 实时事件

- TOKEN_CREATED
- TOKEN_MOVED
- TOKEN_UPDATED
- TOKEN_DELETED

---

# 7 后续扩展

- Token 状态图标、条件血条样式
- 可见性分层、战争迷雾联动
- 临时控制权（资源级授权）
- 范围模板、移动路径记录
- 多场景下 `scene_id` 归属
