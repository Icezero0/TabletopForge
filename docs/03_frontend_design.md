# TabletopForge 前端设计

版本：v0.3  
状态：Draft

---

# 1 文档定位

本文档描述 TabletopForge 前端的目录结构、页面结构、组件划分、状态管理、实时同步与交互原则。

每页的 **核心功能、交互流与行为规则** 以 [`01_product_requirements.md`](01_product_requirements.md) §5 为准；本章侧重布局与组件划分。

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

## 4.2 RoomPage（跑团主界面）

房间主工作台。跑团桌面 MVP 以 **地图视窗为核心**，旧版「右侧多 Tab 工作区」由下列分区替代；成员审批等治理入口仍可从顶栏进入（路由或抽屉，不占地图核心区域）。

### 4.2.1 布局

```text
RoomPage
├── TopToolBar                 # 顶栏工具（模式互斥）
├── TableLayout
│   ├── TopLeftDock
│   │   ├── InGameCharacterList   # 场上角色列表
│   │   └── ChatFloatingPanel     # 聊天悬浮（列表下方）
│   ├── MapViewport               # 核心地图视窗
│   ├── RightInspector
│   │   ├── InfoPanel             # 当前查看信息（单槽，新替旧）
│   │   └── PersonalMemo          # 个人备忘录（可收起）
│   └── BottomAssetBar            # 素材：添加地图 / 添加角色
└── RoomChrome                    # 房间名、治理入口等（轻量顶栏）
```

```text
┌────────────────────────────────────────────────────────────┐
│ RoomChrome + TopToolBar                                     │
├──────────┬──────────────────────────────────┬──────────────┤
│ 左上      │                                  │ RightInspector│
│ 角色列表  │        MapViewport               │ InfoPanel     │
│ 悬浮聊天  │        网格常显                  │ PersonalMemo  │
├──────────┴──────────────────────────────────┴──────────────┤
│ BottomAssetBar                                              │
└────────────────────────────────────────────────────────────┘
```

### 4.2.2 TopToolBar（工具模式）

同一时间 **一种主工具模式**（互斥），避免与选中、拖拽冲突：

| 工具 | 作用 |
|---|---|
| **手型** | 平移 / 缩放视口 |
| **绘制** | 笔刷、直线、方形、圆形、**文本框**（字号、颜色）；线条 **粗细、颜色**；橡皮擦；框选删除（绘制 band z=200，全员可用） |
| **Pointer** | 常驻：同步他用户 **光标位置 + 用户名标签**；按住：**激光指向**（临时点/线，松手消失） |

**测距**：**不在 MVP**（后续 Token 轨迹测距，见 `tabletop_scene.md` §3.5）。

绘制 / Pointer 激光激活时：**不触发**地图与 Token 的选中（无选中框）。

建议提供 **选择模式**（或手型旁「箭头」）：用于单击选中对象。未明示工具时默认视为选择模式。

### 4.2.3 MapViewport

组件：`SceneCanvas`、`MapLayer`(基准 z=0)、`GridLayer`（常显，不占场景三档 band）、`TokenLayer`(基准 z=100)、`DrawingLayer`(基准 z=200)、`SelectionOverlay`、`MeasureOverlay`、`PointerOverlay`、`ContextMenu`。

场景对象叠放见 `tabletop_scene.md` §3.2；**图层**菜单只调整 **同类内** 顺序。

**选中模型（选择模式下）**：

1. **单击**可选中对象（权限内）→ **外部选中框 + 缩放柄** + **Context Menu**。
2. 新选中 **替换**上一选中；不与右侧 InfoPanel 自动绑定，需菜单「查看信息」或等价操作打开。

**地图底图（GM）**：

- 直接：拖拽、缩放（未锁定）。
- 菜单：**删除**、**锁定 / 解锁**、**图层**（地图类内 z-index，§3.2.3）。

**Token（按权限）**：

- 直接：拖拽、缩放。
- 菜单：**查看信息**、**删除**（GM 任意；PL 仅自己创建的角色 Token）。

### 4.2.4 TopLeftDock

**InGameCharacterList**（场上角色列表，非房间成员列表）：

- 展示：名称、HP 摘要、是否已有 Token 等。
- 交互：点击可在右侧打开角色定义信息；提供「上场」从库生成 Token。

**ChatFloatingPanel**：

- 锚定在角色列表 **下方**，悬浮于地图之上，可折叠。
- 普通聊天（已实现能力迁入此面板）。

### 4.2.5 BottomAssetBar

| 操作 | GM | PL |
|---|---|---|
| 添加地图 | 是 | 否 |
| 添加角色 | 任意 | 仅自己资源库 |
| 展示 | 房间角色库；上场 | PL 不可将 GM 怪物放上场 |

### 4.2.6 RightInspector

**InfoPanel（单槽）**：

- **同时仅展示一条**「查看信息」内容；新打开 **替换**旧的。
- 由 Token 菜单「查看信息」或角色列表等触发。
- **GM 怪物 Token**：实例名称（可改）、已受伤害、详细信息；HP 来自 **CharacterState**。
- **PL Token / 角色**：按权限展示；怪物精确 HP 对 PL 隐藏。
- 关闭信息块后 InfoPanel 可为空。

**PersonalMemo**：

- 底部区域，**可收起**。
- **仅当前用户可见**；按 **房间** 持久化（HTTP 保存）。
- 与其他用户不同步内容。

### 4.2.7 治理与其它入口

- 房间成员、入房审批、房间设置：`GovernanceDock`（左上悬浮，成员 / 入房请求 / 设置 Tab）。
- 骰子、RP、Logs 等：**不在**本版跑团主界面布局内（见 §6 说明）。

### 4.2.8 MVP 悬浮面板布局（固定锚点）

跑团桌面 **MVP** 内，下列面板通过 `FloatingPanel` / `GovernanceDock` 实现，**锚点与收起方向固定**；是否显示由布局写死（不可从统一入口关闭，**不可** 在视口上自由拖动）。MVP **完成后** 的可配置与拖动见 §11。

| 面板 ID | 内容 | MVP 锚点 / 收起 |
|---|---|---|
| `governance` | 成员、入房请求、房间设置 | 左上 |
| `chat` | 普通聊天 | 左下 |
| `toolbar` | 手型 / 绘制 / Pointer、网格比例尺 | 顶中 → 向上收起 |
| `asset_bar` | 添加地图 / 添加角色 | 底中 → 向下收起 |
| `info` | InfoPanel 单槽 | 右 → 向右收起 |
| `memo` | 个人备忘录 | 右栏叠放 → 向右收起 |
| `character_list` | 场上角色列表、上场（Step 5） | 左上区（与治理分区，实现时定） |

`MapViewport` 始终全屏底层；`game_role` 控制面板 **内容** 权限，非布局权限。

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

# 5 MapViewport 交互细则

与 [`09_module_design/tabletop_scene.md`](09_module_design/tabletop_scene.md)、[`token_system.md`](09_module_design/token_system.md)、[`character_card.md`](09_module_design/character_card.md) 一致。页面分区见 §4.2。

## 5.1 视口

- **手型工具**：平移 / 缩放视口，不改变对象权威坐标。

## 5.2 图层

- 地图底图基准 z=0（可锁定）；**地图类内** z-index 可调
- Token 基准 z=100；**Token 类内** z-index 可调（effective z = 100 + 类内序号）
- 绘制基准 z=200（含文本框）；**绘制类内** z-index 可调
- **图层**菜单仅重排同类，不跨 band（见 `tabletop_scene.md` §3.2.3）
- **网格常显**；底图导入后缩放适配网格

## 5.3 绘制与 Pointer

- 绘制工具：笔刷、线、方、圆、**文本框**（字号、颜色）；线宽与颜色；橡皮擦、框选删除。
- Pointer：多用户光标同步 + 按住激光指向（WS）。
- 测距：MVP 不做。

## 5.4 选中、菜单与删除

- **选择模式**下单击 → 选中框 + 缩放柄 + Context Menu。
- 地图：删除 / 锁定 / 图层在 **菜单**；拖拽缩放在未锁定时直接操作。
- Token：菜单含 **查看信息**、删除；查看信息打开右侧 **单槽** InfoPanel（新替旧）。

## 5.5 Token 展示

- 无 Token 图：显示 **名称首字**。
- 地图上可 HP 预览；详情以 InfoPanel 为准。
- 怪物：member 仅伤害记录，无精确 HP。

初始版本不要求六边形网格。移动可先乐观更新，再以服务端 / WS 为准。

---

# 6 工作区交互（长期 Tab 与 MVP 关系）

跑团桌面 MVP 的聊天、角色库、素材入口已并入 §4.2（悬浮聊天、左下角色列表、底栏素材、右侧 InfoPanel）。下列 Tab 为 **长期** RoomPage 扩展，本版可不实现独立侧栏 Tab。

## 6.1 Chat Tab

普通聊天。MVP 使用 **ChatFloatingPanel**（§4.2.4）。

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
- 当前用户 room_role（治理）
- 当前用户 game_role（GM / PL / OB）
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

- 当前工具模式（手型 / 绘制 / Pointer / 选择）
- 当前选中对象（地图 / Token，至多一个）
- 当前 InfoPanel 条目（单槽，可空）
- PersonalMemo 展开 / 收起与草稿
- 地图视口缩放、偏移
- Pointer 远端光标与激光状态
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

---

# 11 MVP 后：悬浮面板可配置与自由拖动

**前提**：跑团桌面 MVP（§4.2、§5）交付完成后实施。产品条目见 `01_product_requirements.md` §4.3。

## 11.1 目标

1. **统一入口**：房间界面一处（如顶栏「布局」/「面板」，名称实现时定）勾选 §4.2.8 面板目录中要显示的面板。
2. **自由拖动**：已启用面板可在 `MapViewport` 之上任意定位，不再绑定固定 `anchor`；收起可改为贴边条或最小化（实现时定）。
3. **持久化**：布局偏好按 **用户 + 房间**（或用户全局）存本地 / HTTP；刷新恢复；**默认各用户布局互不同步**。

## 11.2 约束

- `MapViewport` 仍全屏底层；面板与场景对象 z-index band（§5.2）无关。
- `game_role` 仍决定面板内操作权限（如 PL 无「添加地图」），不限制谁能拖动自己的布局。
- 不改变 `governance` 内部 Tab 结构。

## 11.3 实现提示（非 MVP）

- 面板 registry 与 §4.2.8 ID 对齐；布局 state 可进 Pinia + `localStorage` 或 `room_member_ui_prefs`（API 执行时再定）。
