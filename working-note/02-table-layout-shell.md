# Step 2：跑团主界面布局空壳

**目标**：`/rooms/:id` 为 **全屏地图 + 比例尺** 底层，治理/聊天/工具/素材/信息/备忘录均为 **圆角悬浮面板**，可向对应角落收起；**不接** 地图/角色/绘制真实数据。治理（成员/入房请求/设置）在左上悬浮面板内 Tab 切换，无顶栏 RoomChrome。

**依据**：`docs/03` §4.2、`docs/01` §5.10。

---

## 布局结构（必须落地）

```text
MapViewport（全屏网格 + 比例尺）
├── 左上 GovernanceDock（成员/请求/设置 Tab，向左上收起）
├── 左下 ChatFloatingPanel（向左下收起）
├── 顶部 TopToolBar 悬浮条（向上收起，含测距 disabled）
├── 底部 BottomAssetBar 悬浮条（向下收起）
└── 右侧 InfoPanel + PersonalMemo（各向右收起）
```

### 区域说明

| 区域 | 本步内容 |
|---|---|
| **中央 MapViewport** | 常显 **方格网格** + ft 尺度标注（静态配置即可）；无底图、无 Token |
| **TopToolBar** | 手型、绘制、Pointer 按钮；**测距按钮可显示但 disabled** 或隐藏（PRD：MVP 不测距） |
| **TopLeftDock** | 场上角色列表 **假数据/空态**；邀请/上场按钮 **仅 UI** |
| **左下聊天** | 悬浮面板容器，可折叠，**不接消息**（Step 3 接入） |
| **BottomAssetBar** | 添加地图 / 添加角色 按钮（GM/PL 显隐用 `game_role` 占位逻辑） |
| **RightInspector** | InfoPanel 单槽空态；PersonalMemo 输入框 UI（可不持久化） |

---

## 本步做

- 从旧 `RoomPage` **右侧多 Tab 主结构** 拆出，改为上述分区（Tab 内容 Step 3 迁入）。
- 工具 **模式互斥** 的 UI 状态（选中高亮），无需画布逻辑。
- 响应式：中央区域占满剩余空间；左右 dock 最小宽度约定。
- `game_role` 控制按钮可见性（如 PL 不显示「添加地图」）。

---

## 本步不做

- WebSocket 地图事件、真实聊天、成员 API 绑定（Step 3）。
- 地图导入、Token、绘制、选中框、Context Menu（Step 4–5）。
- Pointer 光标同步、激光（可留按钮，Step 4 后接 WS）。
- 角色库真实数据、InfoPanel 真实字段。

---

## 验收清单

- [x] 进入房间即见五区布局，与 `03` §4.2 示意图一致。
- [x] 网格在中央区域常显。
- [x] 顶栏工具可切换选中态；测距未实现且符合 PRD。
- [x] 右栏备忘录可收起；InfoPanel 仅占位。
- [x] PL 看不到「添加地图」类按钮（占位逻辑即可）。

---

## 与 Step 3 的交接

Step 3 将把 **ChatFloatingPanel、成员/审批/设置** 从旧 Tab **嵌入** 本壳，不推翻布局。
