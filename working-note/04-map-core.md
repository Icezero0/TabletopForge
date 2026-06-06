# Step 4：地图与绘制核心

**目标**：中央 MapViewport 具备 **可协作的地图桌面**：底图、网格对齐、视口、锁定、图层、绘制。本步 **不** 做 Token、角色卡、测距。

**依据**：`docs/09_module_design/tabletop_scene.md`、`docs/08` §6.4、`docs/01` §4.2.2。

**数据模型（MVP）**：扁平 room 级 — `room_tabletop_settings`、`room_maps`、`room_drawings`；`assets.map_background`。暂不建 `scenes` / `scene_maps`（见 `docs/07` MVP 注记）。

---

## 分 Phase 推进

| Phase | 范围 | 状态 |
|---|---|---|
| **1** | Migration、tabletop HTTP API、`map_background` asset、WS 增量事件、API 测试、文档、`GET tabletop` 前端拉取 | 已完成 |
| **2** | 视口 pan/zoom、`MapLayer`、GM 上传/拖拽/缩放/锁定、WS 渲染 | 已完成 |
| **3** | 绘制层 CRUD UI（笔刷/线/方/圆/文本、橡皮、框选删）、PL 同步 | 已完成 |
| **4** | 选择模式、Context Menu、地图类内图层、房间 `grid_cell_ft/px` 同步 | 已完成 |
| **4b** | 文本框再编辑（双击 + 右键菜单） | 已完成 |
| **5** | Pointer 光标 + 激光（WS 节流） | 已完成 |
| **6** | 测距工具（对角线、整格 ft 取整、纯前端 overlay） | 待验收 |

### Phase 1 验收

- [x] `GET /rooms/{id}/tabletop` 返回 settings + maps + drawings。
- [x] GM `POST /rooms/{id}/maps`（multipart）成功；PL/OB → 403。
- [x] GM/PL `POST /rooms/{id}/drawings` 成功；OB → 403。
- [x] 变更后房间 WS 广播 `map_*` / `drawing_*` / `tabletop_settings_updated`。
- [x] 前端进房拉取 tabletop 快照（尚无画布交互）。

### Phase 2–5 验收

见文末 **总验收清单**（每 Phase 完成后勾选对应项）。

---

## 数据与 API（概要）

- **`room_maps`**：底图（`asset_id`、x/y、scale、locked、类内 `z_index`，band 0）。每房间 **可多张**，由 GM 上传、移动、删除与类内图层排序。
- **`room_drawings`**：笔刷/线/方/圆/文本；`geometry`/`style` JSON；band 200。
- **`room_tabletop_settings`**：`grid_cell_ft`、`grid_cell_px`（房间级，GM 可 PATCH）。
- HTTP 持久化 + WS：`map_created` / `map_updated` / `map_deleted`、`drawing_*`、`tabletop_settings_updated`；Phase 5 加 `pointer_*`。

---

## 本步做

| 功能 | 边界 |
|---|---|
| **导入地图** | GM 从底栏上传；底图在地图 band（基准 z=0）；缩放 **适配网格** |
| **视口** | 手型：平移、缩放整个画布 |
| **地图拖拽/缩放** | 未锁定时可拖、可缩放；**锁定**后位置固定 |
| **地图图层** | **地图类内** z-index；Context Menu：删除 / 锁定 / 图层 |
| **网格** | 常显；房间级「每格 ft」+ `grid_cell_px`（HTTP 同步） |
| **自定义绘制** | GM/PL；笔刷、线、方、圆、文本框；橡皮擦、框选删 |
| **选中交互** | 选择模式：单击 → 边框 + 缩放柄 + 菜单（地图） |
| **Pointer** | Phase 5：多用户光标 + 按住激光 |
| **测距** | Phase 6：顶栏测距模式，拖拽粗对角线，按 5 ft/格取整显示 |

### 权限

- 一律 `game_role`（`08` §6.4），与 `room_role` 无关。

---

## 本步不做

| 项 | 归属 |
|---|---|
| Token 创建/移动/删除 | Step 5 |
| 角色库、InfoPanel 角色字段 | Step 5 |
| **Token 移动测距 / 困难地形** | PRD 后续 |
| 困难地形 | 后续 |
| 多地图 / Campaign / Session / Scene | 后续 |
| 操作日志完整审计 | 可简记或 Step 5 统一 |

---

### Phase 3 验收

- [x] GM/PL 绘制子工具条；OB 只读渲染。
- [x] `DrawingLayer` SVG 渲染 + `POST`/`DELETE` bulk；WS `drawing_*` 合并。
- [x] 笔刷/线/矩形/椭圆/文本；橡皮擦与框选删除。

### Phase 4 验收

- [x] `useTabletopSelection` + `SelectionOverlay`（地图外框与拖拽/缩放柄）。
- [x] 右键 `ContextMenu`：地图删除/锁定/图层；绘制删除。
- [x] 顶栏移除地图锁定双入口；地图删除仅菜单。
- [x] 格尺固定 5 ft/格（已移除顶栏 `grid_cell_ft` ±；保留 `grid_cell_px` 比例尺调节）。

### Phase 2 验收

- [x] GM 上传 PNG/WebP，PL/OB 同房间可见底图（authenticated blob URL）。
- [x] 底图初始 scale 按网格短边约 20 格适配。
- [x] 未锁定：GM 可拖、角点缩放；锁定后不可拖。
- [x] 手型模式：pan/zoom 视口；网格不随场景 transform。
- [x] 刷新后 map 状态从 `GET tabletop` 恢复。

## 总验收清单（Step 4 完成时）

- [x] GM 上传地图后全员可见并对齐网格。
- [x] 锁定后 GM 不可再拖底图；视口仍可 pan/zoom。
- [x] PL 可绘制且全员同步；PL 不能改底图。
- [x] 绘制可擦除、框选删除；文本框可设字号颜色。
- [x] 地图删除仅菜单 + 选中流程。
- [x] Pointer：双端可见光标与激光。
- [x] 文本框：选择模式下双击或右键「编辑文本」可再编辑并 PATCH 同步。

### Phase 6 验收

- [ ] 顶栏测距可点击，与手型/绘制/Pointer 互斥。
- [ ] 按下拖拽显示粗对角线与中点 `N ft`（N = 格数 × 5 ft，按比例尺一格取整）；松开鼠标后消失。
- [ ] GM / PL / OB 均可测距；不写入 drawing、不发 WS。
- [ ] 切换其他工具后测距线清除。

---

## 依赖

- Step 1–3 完成（含 `game_role`、布局、WS 管道可复用）。
