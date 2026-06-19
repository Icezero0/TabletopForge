# Asset 与资源库模块设计

版本：v0.4  
状态：Living Draft（2026-06-19 对齐当前实现）

---

# 1 模块定位

项目中有两层资源概念：

1. `assets`：底层文件资产，负责文件存储、MIME/大小、内容读取、引用计数与鉴权。
2. `library_resources`：用户资源库中的业务资源，负责地图、指示物、音乐等游戏语义。

底层 asset 可以被多个业务资源或用户记录引用；删除业务资源时只释放引用，`ref_count` 归零后才删除物理文件。

---

# 2 Asset 类型

当前底层 asset 覆盖：

| `asset_type` | 说明 |
| --- | --- |
| `avatar` | 用户个人头像 |
| `feedback_image` | 反馈/建议附图 |
| `image` | 用户资源库通用图片 |
| `audio` | 用户资源库通用音频 |
| `map_background` | 地图底图 |
| `token_image` | 指示物头像图片 |

读取：

- `GET /assets/{asset_id}/content` 需要符合对应资产的鉴权规则。
- 前端会对 asset 内容做本地 blob 缓存，以 asset id 为索引，降低重复下载和弱网加载失败概率。

---

# 3 资源库 Resource 类型

当前 `library_resources` 支持：

| `type` | 说明 | 主要文件字段 |
| --- | --- | --- |
| `map_background` | 地图资源，可记录网格校准信息 | `image` / `primary_asset_id` |
| `token` | 指示物资源，提供 room token 头像来源 | `image` / `primary_asset_id` |
| `sound` | 背景音乐资源 | `audio` / `primary_asset_id` |

API：

```text
GET    /library/resources
POST   /library/resources
GET    /library/resources/{resource_id}
PATCH  /library/resources/{resource_id}
DELETE /library/resources/{resource_id}
```

说明：

- `GET` 支持按 `type=map_background|token|sound` 过滤。
- `POST` 使用 multipart 创建资源。
- `PATCH` 当前主要用于改名和资源元数据更新。
- `DELETE` 需要资源未被占用；否则返回冲突。

---

# 4 角色与指示物资源

角色卡有两个头像相关字段：

- `portrait_asset_id`：角色头像。
- `token_image_asset_id`：主要指示物头像；未设置时可回退到角色头像。

角色还维护：

- `primary_token_resource_id`：角色生命周期绑定的主要资源库 token。

规则：

- 角色存在时，应确保主要资源库 token 存在。
- 角色头像或 token 图像更新时，同步更新主要资源库 token。
- 角色删除时释放该主要资源库 token 的占用。
- 次要指示物配置引用的资源库 token 也参与占用统计。
- Room token 使用资源库 token 作为头像来源，但资源库 token 删除后应能回退到名称首字头像。

---

# 5 地图资源

地图可以通过两条路径进入房间：

1. 直接上传地图：先创建地图资源，再创建 room map。
2. 从资源库选择地图：通过 `POST /rooms/{room_id}/maps/from-resource` 创建 room map。

地图资源可保存网格校准信息，如：

- `map_grid_x`
- `map_grid_y`
- `map_grid_size`
- `map_grid_cell_height`
- `map_grid_calibration`

Room map 是场景中的实例，保存位置、缩放、锁定、图层等桌面状态。

---

# 6 音频资源

`sound` 资源用于房间背景音乐。

房间音乐状态保存在 `room_tabletop_settings.music_state`，包含：

- 播放列表资源。
- 当前曲目。
- 播放/暂停。
- 播放位置。
- 循环模式：单曲循环、列表循环、随机播放。

GM 控制房间播放状态；各玩家本地控制音量。

---

# 7 权限与可见性

| 资源 | 读取 | 写入 / 删除 |
| --- | --- | --- |
| avatar | 公开可读 | 本人更新 |
| feedback_image | 提交者 / admin | 随反馈创建 |
| image / audio | 登录用户可读 | 上传者 |
| map_background / token / sound | 登录用户可读；业务侧再限制使用入口 | 所有者，且未被占用 |

资源库资源属于用户；房间中使用资源时，业务层负责判断当前用户是否有权限把资源加入房间。

---

# 8 后续

- 缩略图生成与图片压缩。
- 更细的资源标签、搜索与批量管理。
- 默认素材库。
- Asset 内容缓存的失效策略。
- 资源占用统计的自动一致性检查。
