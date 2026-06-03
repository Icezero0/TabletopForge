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

建议枚举：

```text
USER
SITE_ADMIN
SUPER_ADMIN
```

负责：

- 查看反馈
- 处理反馈
- 管理站点公告
- 查看站点统计
- 用户状态管理

site_role 不自动授予任何房间内权限。

---

# 4 room_role

room_role 是房间级身份，存储在 room_members 中。

建议枚举：

```text
OWNER
ADMIN
MEMBER
```

负责：

- 审批加入房间
- 踢出成员
- 修改房间设置
- 设置 room_role
- 审批 game_role 变更
- 管理房间公告

---

# 5 game_role

game_role 是游戏级身份，存储在 room_members 中。

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

---

# 6 权限矩阵

## 6.1 site 权限

| 权限 | USER | SITE_ADMIN | SUPER_ADMIN |
|---|---|---|---|
| 提交反馈 | 是 | 是 | 是 |
| 查看反馈 | 否 | 是 | 是 |
| 处理反馈 | 否 | 是 | 是 |
| 管理用户状态 | 否 | 否/可配置 | 是 |

## 6.2 room 权限

| 权限 | OWNER | ADMIN | MEMBER |
|---|---|---|---|
| 修改房间信息 | 是 | 是/可配置 | 否 |
| 审批加入房间 | 是 | 是 | 否 |
| 踢出成员 | 是 | 是 | 否 |
| 设置 ADMIN | 是 | 否 | 否 |
| 修改 room_role | 是 | 否/可配置 | 否 |
| 审批 game_role 变更 | 是 | 是 | 否 |
| 删除房间 | 是 | 否 | 否 |

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

---

# 7 审批规则

## 7.1 加入房间

1. 用户提交加入申请。
2. 用户可选择期望 game_role。
3. OWNER 或 ADMIN 审批。
4. 审批通过后创建 room_member。
5. 默认 room_role 为 MEMBER。
6. game_role 根据审批结果写入。

## 7.2 game_role 变更

1. 成员提交 game_role 变更申请。
2. OWNER 或 ADMIN 审批。
3. 审批通过后更新 room_members.game_role。
4. 写入操作日志。
5. 广播成员身份变化事件。

DM 不天然拥有审批 game_role 变更的权限。

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
5. 游戏内操作权限归 game_role 管理。
6. 特殊资源控制使用资源级授权，不滥用身份切换。
