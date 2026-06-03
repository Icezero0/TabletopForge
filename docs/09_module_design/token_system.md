# Token 模块设计

版本：v0.2  
状态：Draft

---

# 1 模块目标

Token 模块用于维护地图桌面上的可操作对象。

Token 可以代表玩家角色、NPC、怪物、道具、标记或效果范围。

---

# 2 核心属性

Token 包含：

- 所属房间
- 所属场景
- 资源图片
- 绑定角色
- 名称
- 类型
- 坐标
- 尺寸
- 旋转
- 层级
- 可见性
- 锁定状态
- 所有者

---

# 3 前端交互

- 创建 Token
- 拖拽 Token
- 缩放 Token
- 旋转 Token
- 选中 Token
- 删除 Token
- 右键菜单
- 绑定角色

---

# 4 权限规则

- DM 可操作所有 Token。
- 玩家可操作自己拥有或被授权的 Token。
- 旁观者默认不可操作 Token。

---

# 5 实时事件

- TOKEN_CREATED
- TOKEN_MOVED
- TOKEN_UPDATED
- TOKEN_DELETED

---

# 6 后续扩展

- Token 状态图标
- 血条显示
- 可见性分层
- 临时控制权
- 范围模板
- 移动路径记录
