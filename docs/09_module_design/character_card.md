# 角色卡模块设计

版本：v0.2  
状态：Draft

---

# 1 模块目标

角色卡模块用于维护房间内玩家角色、NPC 与怪物的基础信息、规则数据、当前状态与背景设定。

第一阶段优先支持 DND5E 角色卡的基础字段和状态追踪。

---

# 2 核心概念

## 2.1 Character

角色实体，可以是：

- 玩家角色
- NPC
- 怪物

## 2.2 CharacterState

角色当前状态，例如 HP、临时 HP、AC、状态效果等。

## 2.3 CharacterResource

角色资源，例如法术位、职业资源、短休资源、长休资源等。

---

# 3 数据范围

角色卡包含：

- 基础信息
- 属性
- 技能
- 豁免
- 战斗状态
- 资源
- 装备
- 法术位
- 背景设定
- 公开信息
- 私密信息

---

# 4 前端交互

角色卡前端应提供：

- 角色列表
- 角色详情
- 角色编辑
- HP 快速修改
- 状态效果添加 / 移除
- 资源消耗 / 恢复
- 法术位记录

---

# 5 后端服务

后端服务负责：

- 创建角色
- 更新角色基础信息
- 更新角色状态
- 更新资源
- 写入操作日志
- 发布实时事件

---

# 6 权限规则

- DM 可查看和修改房间内所有角色。
- 玩家可查看和修改自己拥有的角色。
- 旁观者默认只读。
- 私密字段需要单独做可见性控制。

---

# 7 实时事件

- CHARACTER_CREATED
- CHARACTER_UPDATED
- CHARACTER_DELETED
- CHARACTER_STATE_CHANGED
- CHARACTER_HP_CHANGED
- CHARACTER_RESOURCE_CHANGED
- CHARACTER_EFFECT_ADDED
- CHARACTER_EFFECT_REMOVED

---

# 8 后续扩展

- 角色导入导出
- 职业升级辅助
- 法术管理
- 装备管理
- 角色模板
- NPC / 怪物快速创建
