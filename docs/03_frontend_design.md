# TabletopForge 前端设计

版本：v0.2  
状态：Draft

---

# 1 文档定位

本文档描述 TabletopForge 前端的目录结构、页面结构、组件划分、状态管理、实时同步与交互原则。

---

# 2 前端职责

前端负责：

- 用户界面展示
- 页面路由
- 表单输入与校验
- Table 区域渲染与交互
- Token 拖拽、缩放与选中
- 聊天与 RP 输入
- 角色卡展示与编辑
- 资源库管理
- 骰子操作入口
- WebSocket 事件响应
- 本地 UI 状态管理

前端不负责权威状态判定。关键业务状态以后端返回或 WebSocket 广播结果为准。

---

# 3 推荐目录结构

```text
src/
├── app/
│   ├── router/
│   ├── stores/
│   └── bootstrap/
├── shared/
│   ├── api/
│   ├── ws/
│   ├── components/
│   ├── composables/
│   ├── utils/
│   └── types/
├── features/
│   ├── auth/
│   ├── rooms/
│   ├── members/
│   ├── chat/
│   ├── rp/
│   ├── characters/
│   ├── table/
│   ├── assets/
│   ├── dice/
│   ├── logs/
│   └── permissions/
└── pages/
    ├── LoginPage.vue
    ├── RoomListPage.vue
    ├── RoomPage.vue
    └── CharacterPage.vue
```

---

# 4 页面设计

## 4.1 RoomListPage

展示用户可访问的房间。

主要功能：

- 创建房间
- 查看已加入房间
- 查看申请状态
- 进入房间

## 4.2 RoomPage

房间主工作台，是核心业务页面。

结构：

```text
RoomPage
├── RoomTopBar
├── TableArea
└── WorkspacePanel
```

### RoomTopBar

显示：

- 房间名
- 当前场景
- 在线成员
- 当前用户身份
- 骰子快捷入口
- 房间信息和成员管理入口

### TableArea

负责地图桌面显示。

包含：

- SceneCanvas
- MapLayer
- GridLayer
- TokenLayer
- SelectionOverlay
- ContextMenu

### WorkspacePanel

右侧或底部工作区。

包含 tabs：

- Chat
- Role Play
- Characters
- Assets
- Dice
- Logs
- Combat

初始版本可先实现 Chat、Role Play、Characters、Assets、Logs。

## 4.3 CharacterPage

展示和编辑单个角色。

包含：

- 基础信息
- 属性
- 技能
- 战斗状态
- 资源
- 装备
- 背景
- 操作日志

---

# 5 Table 区域交互

Table 区域需要支持：

- 地图平移
- 地图缩放
- 网格显示
- Token 显示
- Token 选中
- Token 拖拽
- Token 缩放
- Token 删除
- 右键菜单

初始版本只要求方格网格，不要求六边形网格。

Token 移动可以前端先进行临时视觉更新，再等待服务端确认事件修正最终状态。

---

# 6 工作区交互

## 6.1 Chat Tab

普通聊天，用于 OOC 交流。

## 6.2 Role Play Tab

角色扮演消息输入区。

推荐输入项：

- 选择角色
- 行动描述
- 台词内容

行动描述和台词内容可只填其一。

## 6.3 Characters Tab

展示房间内角色状态摘要。

支持：

- 查看角色详情
- 快速修改 HP
- 快速查看状态
- 根据权限进入编辑

## 6.4 Assets Tab

展示个人资源和房间资源。

当前后端地基只提供头像和反馈图片 assets。业务资源库的 Assets Tab 后续随 `image` 资源库一起实现。

支持：

- 上传图片
- 资源分类
- 拖放到地图创建 Token

## 6.5 Logs Tab

展示关键操作日志。

支持按类型、角色、操作者筛选。

---

# 7 状态管理

建议将状态分为：

## 7.1 全局状态

- 当前用户
- token
- site_role
- 全局通知

## 7.2 房间状态

- 当前房间
- 成员列表
- 当前用户 room_role
- 当前用户 game_role（后续游戏业务阶段）
- 当前场景
- 在线状态

## 7.3 业务状态

- 消息列表
- RP 消息列表
- 角色列表
- Token 列表
- 资源列表
- 日志列表

## 7.4 UI 状态

- 当前选中 Token
- 当前打开 tab
- 地图缩放
- 地图偏移
- 弹窗状态

---

# 8 权限控制

前端需要根据权限控制 UI 展示，但不承担最终权限判定。

原则：

- 前端隐藏不可用操作入口。
- 后端始终进行最终权限校验。
- 权限判断逻辑应封装为 composable 或 helper。

示例：

```text
canSwitchScene
canMoveToken
canEditCharacter
canApproveMember
canRollSecretDice
```

---

# 9 WebSocket 响应

前端 WebSocket client 负责：

- 建立连接
- 鉴权
- 心跳
- 断线重连
- 事件分发
- 房间状态更新

事件处理不应散落在组件中，应统一分发到 store 或 feature handler。

---

# 10 前端设计原则

1. 页面结构围绕房间工作台组织。
2. Table 区域和工作区解耦。
3. 组件负责交互展示，业务规则尽量下沉到 store / service。
4. WebSocket 事件统一处理。
5. 前端权限只控制体验，后端权限控制安全。
