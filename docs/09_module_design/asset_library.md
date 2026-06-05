# Asset 与资源库模块设计

版本：v0.3  
状态：Draft

---

## 1 模块目标

后端 `assets` 模块管理底层文件资产，覆盖用户头像、反馈图片、用户资源库图片和音频，以及角色卡头像/图库图片。

当前已实现用户级底层资源库；房间资源库、地图背景和 Token 等游戏语义层模型后续再实现。

---

## 2 当前资产类型

| `asset_type` | 说明 |
| --- | --- |
| `avatar` | 用户个人头像 |
| `feedback_image` | 反馈/建议中的附图 |
| `image` | 用户资源库通用图片 |
| `audio` | 用户资源库通用音频 |

跑团桌面 MVP 拟增加业务用途，例如：

- `map_background`：地图底图
- `token_image`：角色 / 怪物 Token 图（由创建者上传，挂在角色定义上）

未上传 Token 图时，前端使用角色**名称首字**渲染，不强制落库 asset。

---

## 3 资源范围

### 3.1 用户头像

用户上传头像后，`users.avatar_asset_id` 指向当前头像 asset。

同时，`user_avatar_history` 记录用户上传过的全部头像 asset。切换或重新上传头像只更新
`users.avatar_asset_id`；旧头像因仍存在于历史记录，`ref_count` 不归零，文件不会被删除。
用户手动删除历史头像记录时，释放对应 asset 的一次引用，归零后文件才真正删除。

前端"历史头像"面板支持从历史记录中直接恢复旧头像（不重新上传，只更新 `avatar_asset_id`）。

### 3.2 反馈图片

反馈图片通过 `feedback_id` 关联到反馈记录。`feedback_image` 不参与去重（绑定到特定反馈
可见性，需要保持独立）。

### 3.3 用户资源库（图片 / 音频）

用户可通过"资源库"页面上传、查看、删除自己的 `image` 和 `audio` 资产。

- 上传时计算 SHA-256 内容哈希；按 `asset_type + content_hash + size_bytes + content_type`
  去重复用已有文件。
- `ref_count` 计数底层文件被引用次数；用户删除资产记录只是释放一次引用，`ref_count`
  归零才删除物理文件。

### 3.4 角色卡图片

角色卡与 asset 的关联点：

- `characters.portrait_asset_id`：角色头像，外键指向 `assets.id`，级联置空（角色删除不删除
  asset）。
- `characters.identity.gallery_asset_ids`：JSONB 数组，存放最多 3 张图片的 asset id，
  用于角色卡图库展示。

角色头像在编辑时通过裁剪对话框（`AvatarCropDialog`）上传，生成新 asset 后写入
`portrait_asset_id`。前端通过 `useAuthenticatedAssetUrl` 加载带鉴权的图片 blob URL。

---

## 4 当前功能范围

- 上传用户头像；分页读取当前用户历史头像。
- 创建反馈时上传反馈图片。
- 上传、列表、读取、删除用户资源库 `image` / `audio`。
- 上传角色头像及图库图片。
- 读取任意 asset 内容（鉴权见第 5 节）。
- 校验图片类型和大小限制。
- SHA-256 去重：`avatar`、`image`、`audio` 参与去重；`feedback_image` 不参与。
- `ref_count` 生命周期管理：删除用户资源库 asset 或历史头像记录时释放一次引用，归零才删除文件。

当前暂不实现：资源重命名、分类标签、搜索、房间资源、从资源创建 Token、批量上传、文件压缩。

---

## 5 权限规则

| 资产类型 | 读取 | 写入 / 释放 |
| --- | --- | --- |
| `avatar` | 公开可读 | 本人更新自己头像 |
| `feedback_image` | 反馈创建者；具备查看全部反馈权限的 admin | 随反馈创建 |
| `image` / `audio` | 登录用户均可读（供共同游戏使用） | 上传者释放引用 |
| 角色头像 / 图库 | 登录用户均可读 | 角色拥有者 |

房间资源和游戏语义资源权限后续随业务模块一起设计。

---

## 6 后续扩展

- 游戏语义资源类型（`map_background`、`token_image` 等）
- 资源标签与搜索
- 资源批量上传
- 图片压缩 / 缩略图生成
- 默认素材库（官方预设地图、Token 等）
- 文件定期清理任务（清理 `ref_count = 0` 的孤立文件）
- 图片用途 `purpose`（同一文件用于不同业务场景）
