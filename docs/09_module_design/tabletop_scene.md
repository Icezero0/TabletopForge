# 场景与地图桌面模块设计

版本：v0.6  
状态：Implemented / Living Document  
最后核对：2026-06-19

---

# 1 模块目标

本模块描述 DND5E 房间模式中的桌面能力：地图、视口、网格、绘制、测距、Pointer、战争迷雾、背景音乐、场景快照与图层关系。

注意：这些能力属于 DND5E 房间模式，不应默认绑定到 ThunderStone 等其他游戏模式。

---

# 2 当前前端结构

主要文件：

```text
frontend/src/pages/room/Dnd5eRoomMode.vue
frontend/src/features/table/components/TableStage.vue
frontend/src/features/table/components/MapViewport.vue
frontend/src/features/table/components/MapLayer.vue
frontend/src/features/table/components/DrawingLayer.vue
frontend/src/features/table/components/TokenLayer.vue
frontend/src/features/table/components/FogOverlay.vue
frontend/src/features/table/components/PointerOverlay.vue
frontend/src/features/table/components/MeasureOverlay.vue
frontend/src/features/table/components/TopToolBar.vue
frontend/src/features/table/components/BottomAssetBar.vue
```

主要状态：

```text
useTabletopStore
useRoomRealtimeSession        # 房间基础 WS
useTabletopRealtimeEvents     # tabletop 专用 WS
```

---

# 3 后端数据

当前实时桌面状态仍以 room 级表保存：

```text
room_tabletop_settings
room_maps
room_drawings
room_tokens
```

场景快照：

```text
room_scenes
```

`room_tabletop_settings` 当前包含：

```text
grid_cell_ft
grid_cell_px
combat_state
music_state
fog_state
```

---

# 4 图层模型

当前核心图层顺序：

```text
地图
Token
绘制
战争迷雾
测距 / Pointer / 临时绘制预览 / 选择框 / 菜单等交互层
```

说明：

- 战争迷雾需要覆盖地图、token、绘制。
- draw / pointer / 测距等工具层高于战争迷雾，便于 GM/PL 操作与指示。
- 被战争迷雾完全覆盖的 token 不应响应点击；若只覆盖一部分，未覆盖区域仍可点击。
- Context Menu 的 z-index 必须高于各浮动面板和桌面对象。

同类图层排序：

- 地图只在地图类内调整。
- token 只在 token 类内调整。
- 绘制只在绘制类内调整。
- token 右键菜单的图层操作已收拢到“图层”次级菜单。

---

# 5 地图

地图来源于资源库 `library_resources(type=map_background)`。

能力：

- 上传地图。
- 从资源库添加地图。
- 上传后先填写地图名称与备注，再标记网格。
- 地图网格标定。
- 锁定 / 解锁。
- 删除。
- 右键地图填充战争迷雾。
- 多地图在同一场景中可共存。

上传地图后会创建 asset 与 library resource，再应用到当前房间。

---

# 6 视口

能力：

- 缩放。
- 平移。
- 重置视窗。
- 选择工具 / 手型工具。
- 在选择或手型状态下，按住鼠标滚轮可拖动视窗。
- 双击战斗先攻轴 token 可平滑移动视窗到对应 token。

视窗位置与缩放属于前端本地状态，可按房间/场景在本地保存。

---

# 7 绘制工具

当前工具：

- 笔刷。
- 直线。
- 矩形。
- 圆形。
- 文本。
- 橡皮 / 删除。

已调整：

- 椭圆工具改为圆形。
- 矩形与圆形支持轮廓 / 遮罩。
- 遮罩透明度 0–100。
- 默认拖动为矩形/圆形；按住 Ctrl 约束为正方形/正圆。
- 绘制笔刷大小使用滑条，并有笔刷大小预览。
- 绘制工具中 `Ctrl+Z` 移除上一条绘制。

权限：

- GM / PL 可绘制。
- OB 只读。

---

# 8 测距与 Pointer

测距：

- 已作为桌面工具存在。
- 用于场景坐标下的距离估算。

Pointer：

- 通过 WebSocket 实时同步位置。
- pointer 位置通过网络传输，拖尾由前端本地渲染。
- 当前激光表现为 fading trail，而不是从按下点到当前位置的直线。
- 使用者本地也能看到拖尾。

---

# 9 战争迷雾

战争迷雾属于 DND5E 桌面工具，仅 GM 可编辑。

工具：

- 填充战争迷雾。
- 擦除战争迷雾。
- 共用笔刷大小。
- 工具栏有笔刷大小滑条。
- 工具栏有非 GM 视角预览开关。
- 工具栏有非 GM 迷雾不透明度滑条。

显示：

- GM 视角：半透明黑色遮罩，当前约 0.6。
- PL / OB 视角：接近不透明黑色遮罩，当前约 0.95，可由房间设置同步。
- 羽化已取消，避免边缘效果差。

数据：

- 当前 fog state 存于 `room_tabletop_settings.fog_state`。
- 每个 room map 应拥有独立 fog mask；删除地图时，对应迷雾不应污染新地图。
- 未来建议将 fog mask 正式转为灰度图资产或二进制数据，而不是无限积累笔刷操作。

---

# 10 背景音乐

背景音乐工具位于桌面工具栏。

能力：

- GM 添加资源库音乐。
- GM 上传音频，上传后先创建资源库对象，再应用到房间。
- 播放 / 暂停。
- 上一首 / 下一首。
- 播放进度。
- 单曲循环 / 列表循环 / 随机播放。
- 播放列表。
- 所有玩家可本地调整音量。

同步：

- 当前播放列表、曲目、进度、播放状态等存入 `room_tabletop_settings.music_state`。
- 本地音量不进入房间状态。

---

# 11 场景

场景功能已落地，不再是后续概念。

数据：

```text
room_scenes
```

能力：

- 素材面板中通过“切换场景”打开场景菜单。
- 新建空场景。
- 切换场景时，先保存当前 tabletop 到当前场景，再加载目标场景。
- 编辑场景名称。
- 删除场景。
- 场景删除需要确认。

场景快照应包含：

- 地图。
- 绘制。
- token。
- 战争迷雾。
- 与场景绑定的掷骰日志。

视窗位置和缩放属于每个用户的前端本地状态，也应按场景保存。

---

# 12 实时事件

当前相关事件：

```text
tabletop_settings_updated
tabletop_snapshot_replaced
map_created
map_updated
map_deleted
drawing_created
drawing_updated
drawing_deleted
token_created
token_updated
token_deleted
token_transform_preview
pointer_presence
pointer_laser
object_selection
```

说明：

- 拖拽 token 中途通过 `token_transform_preview` 走 WS 预览，结束时通过 HTTP PATCH 持久化。
- Pointer 通过 WS 传位置，轨迹本地渲染。
- 场景切换通过 `tabletop_snapshot_replaced` 通知客户端重载。

---

# 13 权限规则

| 操作 | GM | PL | OB |
|---|---|---|---|
| 查看桌面 | ✓ | ✓ | ✓ |
| 地图管理 | ✓ | — | — |
| 绘制 | ✓ | ✓ | — |
| 测距 | ✓ | ✓ | — |
| Pointer | ✓ | ✓ | — |
| 战争迷雾编辑 | ✓ | — | — |
| 音乐播放状态 | ✓ | — | — |
| 本地音量 | ✓ | ✓ | ✓ |
| 场景管理 | ✓ | — | — |

---

# 14 后续

- 正式化 `fog_state` schema。
- 将 fog mask 从笔刷操作栈升级为灰度图/压缩 mask。
- 拆出 DND5E tabletop 与房间基础 shell 的边界文档。
- 为场景切换、战争迷雾、音乐状态补测试。
- 将当前巨大的 `Dnd5eRoomMode.vue` 继续拆分。
