# TabletopForge 权限设计

版本：v0.2  
状态：Draft

---

# 1 文档定位

本文档描述 TabletopForge 的身份模型、权限边界、权限矩阵与审批规则。

---

# 2 三层身份模型

系统采用三层身份：

```text
site_role
room_role
game_role
```

三者互相独立，不做隐式绑定。

---

# 3 site_role

site_role 是站点级身份，存储在用户表中。

枚举：

```text
user
admin
```

负责：

- 提交反馈
- 查看自己的反馈
- 查看全部反馈
- 处理反馈
- 设置其他用户的 site_role

site_role 不自动授予任何房间内权限。

---

# 4 room_role

room_role 是房间级身份，存储在 room_members 中。

枚举：

```text
owner
manager
member
```

负责：

- 审批加入房间
- 踢出成员
- 修改房间信息
- 设置或解除 manager

当前后端地基已移除房间配置空壳；房间配置能力后续有明确业务需求时再设计。

---

# 5 game_role

game_role 是游戏级身份的**长期模型**，与 `room_role` 独立，不做隐式绑定。

建议枚举：

```text
DM
PLAYER
VIEWER
```

后续可扩展：

```text
ASSISTANT_DM
NPC_CONTROLLER
```

负责：

- 切换场景
- 管理地图
- 管理 Token
- 修改角色状态
- 暗骰
- 管理战斗
- 查看隐藏信息
- 发送 RP 消息

## 5.1 当前 MVP 落地方式

**当前代码与下一版 MVP 均不新增 `game_role` 字段**，跑团内权限通过现有 `room_members.role`（`room_role`）映射：

| 产品称呼 | room_role | 说明 |
|---|---|---|
| DM | `owner`, `manager` | 地图底图、Token、怪物全量信息、角色管理 |
| 玩家（PL） | `member` | 绘制层；自己创建的角色库与 Token；主 PC + 附加角色；怪物仅看伤害记录 |

`game_role` 留待需要与房间治理权解耦时再引入（例如「会批人但不会改图」的 manager）。详见 §6.4。

---

# 6 权限矩阵

## 6.1 site 权限

| 权限 | user | admin |
|---|---|---|
| create_feedback | 是 | 是 |
| view_own_feedback | 是 | 是 |
| view_all_feedback | 否 | 是 |
| update_feedback | 否 | 是 |
| delete_feedback | 否 | 是 |
| manage_site_roles | 否 | 是 |

## 6.2 room 权限

| 权限 | owner | manager | member |
|---|---|---|---|
| view_room | 是 | 是 | 是 |
| update_room | 是 | 是 | 否 |
| delete_room | 是 | 否 | 否 |
| view_members | 是 | 是 | 是 |
| invite_user | 是 | 是 | 是 |
| 审批加入房间 | 是 | 是 | 否 |
| manage_members | 是 | 是 | 否 |
| manage_managers | 是 | 否 | 否 |
| view_messages | 是 | 是 | 是 |
| send_message | 是 | 是 | 是 |

移除成员规则：

- 移除普通成员需要 `manage_members`，owner 和 manager 均可执行。
- 移除 manager 需要 `manage_managers`，当前只有 owner 可执行。
- owner 不能被移除。
- 成员主动退出房间走 leave room，不走 remove member。

## 6.3 game 权限

| 权限 | DM | PLAYER | VIEWER |
|---|---|---|---|
| 创建场景 | 是 | 否 | 否 |
| 切换场景 | 是 | 否 | 否 |
| 上传地图 | 是 | 否/可配置 | 否 |
| 创建任意 Token | 是 | 否 | 否 |
| 移动任意 Token | 是 | 否 | 否 |
| 移动自己 Token | 是 | 是 | 否 |
| 修改所有角色状态 | 是 | 否 | 否 |
| 修改自己角色状态 | 是 | 是 | 否 |
| 公开骰 | 是 | 是 | 可配置 |
| 暗骰 | 是 | 否 | 否 |
| 发送 RP | 是 | 是 | 可配置 |
| 查看隐藏对象 | 是 | 否 | 否 |
| 管理战斗 | 是 | 否 | 否 |

## 6.4 Tabletop 权限（MVP，映射到 room_role）

下列权限在 MVP 中由 `room_role` 判定，**不依赖** `game_role` 字段。DM 列对应 `owner` 与 `manager`；玩家列对应 `member`。

| 权限 | owner | manager | member |
|---|---|---|---|
| 上传 / 删除地图底图 | 是 | 是 | 否 |
| 锁定 / 解锁地图底图 | 是 | 是 | 否 |
| 移动未锁定地图底图 | 是 | 是 | 否 |
| 创建 / 编辑 / 删除绘制 | 是 | 是 | 是 |
| 橡皮擦 / 框选删除绘制 | 是 | 是 | 是 |
| 使用测距工具 | 是 | 是 | 是 |
| 创建 / 删除任意 Token | 是 | 是 | 否 |
| 移动任意 Token | 是 | 是 | 否 |
| 移动绑定己方 PC 的 Token | 是 | 是 | 是 |
| 查看怪物精确 HP | 是 | 是 | 否 |
| 查看怪物伤害记录 | 是 | 是 | 是 |
| 修改任意角色卡 | 是 | 是 | 否 |
| 修改己方角色卡 | 是 | 是 | 是 |
| 创建角色定义 | 是（任意） | 是（任意） | 是（主 PC + 附加角色，归自己） |
| 编辑 / 删除角色定义 | 是（任意） | 是（任意） | 是（仅 `created_by` 为自己） |
| 查看角色定义 | 是（任意） | 是（任意） | 是（全部列表；怪物正文 / HP 受可见性限制） |
| 管理自己创建的角色资源 | 是 | 是 | 是（含附加角色与对应 Token） |
| 从库复用并新建 Token | 是（任意定义） | 是（任意定义） | 是（仅自己创建的定义） |
| 平移 / 缩放 Table 视口 | 是 | 是 | 是 |

前端按上表隐藏或禁用操作入口；后端在 Service 层做最终校验。

---

# 7 审批规则

## 7.1 加入房间

1. 用户提交加入申请。
2. 房间侧由 owner 或 manager 审批。
3. 审批通过后创建 room_member。
4. 默认 room role 为 member。

当前还保留自动通过、手动审核和自动拒绝三种入房审核模式。

## 7.2 game_role 变更（未实现）

`game_role` 字段尚未落地。若未来引入，建议流程：

1. 成员提交 game_role 变更申请。
2. owner 或 manager 审批。
3. 审批通过后更新 `room_members.game_role`。
4. 写入操作日志并广播身份变化事件。

当前 MVP 通过调整 `room_role`（如设为 `manager`）表达 DM 能力，无单独审批流。

---

# 8 资源级授权

部分游戏资源可能需要独立授权，例如：

- 某玩家临时控制 NPC Token
- 某玩家编辑另一个角色卡
- 某玩家查看私密笔记

这类能力不应通过改变 game_role 实现，而应通过资源级权限实现。

后续可设计：

```text
token_permissions
character_permissions
note_permissions
```

---

# 9 权限设计原则

1. site_role、room_role、game_role 分别处理不同层级权限。
2. 不同层级权限不做隐式继承。
3. 前端只负责隐藏操作入口，后端负责最终权限校验。
4. 审批类权限归 room_role 管理。
5. 游戏内操作权限在 MVP 由 `room_role` 映射（§6.4）；长期可归 `game_role` 管理。
6. 特殊资源控制使用资源级授权，不滥用身份切换。
