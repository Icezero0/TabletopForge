# Token 模块设计

版本：v0.4  
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
- 创建 / 编辑 Token（GM 任意；PL 仅自己创建的角色定义）
- 拖拽、缩放（权限内）
- 选中 Token
- **删除**：选中 → **右键 Context Menu → 删除**（未选中不可删）
- 绑定角色
- 地图上的 **HP 预览**（角色 Token）；怪物 Token 对 member 不显示精确 HP

角色 Token 点击打开角色详情。怪物 Token：GM 看全量 **CharacterState**；PL 仅看 **累计受伤害 / 伤害记录**。

**缺省图**：绑定角色无 Token 图时，显示 **名称首字**（与 `character_card.md` §3.4 一致）。

---

# 4 权限规则

通过 `game_role` 判定，见 `08_permission_design.md` §6.4：

- **GM**：所有 Token 增删改、移动。
- **PL**：移动并管理绑定 **自己创建角色** 的 Token；不可新建 GM 怪物 Token。

---

# 5 可见性与 HP

| 对象 | GM | PL | OB |
|---|---|---|---|
| 角色 Token HP | CharacterState 全量 | 己方全量；他人按策略 | 只读摘要 |
| 怪物 Token HP | 精确 HP | 仅伤害记录 | 仅伤害记录 |
| 怪物详情正文 | 可读可编 | 不可编辑 GM 怪物正文 | 只读 |

权威 HP 在 **CharacterState**；对 PL 的 API / WS 过滤怪物精确 HP。

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
