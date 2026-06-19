# 指示物 / Token 模块设计

版本：v0.5  
状态：Living Draft（2026-06-19 对齐当前实现）

---

# 1 模块定位

本模块描述 DND5E 房间桌面中的 room token，以及它和角色卡、资源库 token 的关系。

当前项目中文 UI 正式称呼为“指示物”；代码中仍大量使用 `token`。

---

# 2 两类 Token 概念

## 2.1 资源库 Token

资源库 token 是 `library_resources(type=token)`，表示可复用的指示物素材。

用途：

- 提供 room token 头像来源。
- 供角色卡次要指示物配置引用。
- 供角色卡主要指示物对应的资源库 token 绑定角色生命周期。

生命周期：

- 角色存在时，应有一个绑定角色生命周期的主要资源库 token。
- 角色头像 / token 图像变化时，主要资源库 token 同步更新。
- 角色删除后，主要资源库 token 的占用释放，才允许删除对应资源。
- 次要指示物配置引用的资源库 token 也会参与占用统计。

注意：room token 对资源库 token 不是强依赖。资源库 token 被删除或不可读时，前端回退到名称首字头像。

## 2.2 Room Token

Room token 是房间桌面上的实例，存储在 `room_tokens`。它是场景中可移动、可选择、可展示信息面板的对象。

主要字段：

- `room_id`
- `library_resource_id`
- `linked_character_id`
- `owner_user_id`
- `name`
- `x` / `y` / `width` / `height` / `rotation`
- `z_index`
- `visible`
- `locked`
- `panel`

Room token 不直接保存完整角色卡，而是保存生成时的面板快照；后续可在信息面板中独立修改。

---

# 3 主要指示物

主要指示物由角色卡自动派生，不再作为用户手动编辑的 `token_config`。

来源：

- 名称：角色卡名称。
- 头像：`token_image_asset_id` 优先，其次 `portrait_asset_id`。
- 信息面板：从角色卡属性、状态、法术、资源、背包、特性等生成。
- 资源库 token：`characters.primary_token_resource_id`。

生成 room token 时，主要指示物会直接从角色卡当前数据生成快照，并使用主要资源库 token 作为头像资源。

---

# 4 次要指示物

次要指示物仍保存在 `character_token_configs`。

用途：

- 召唤物、变身形态、随从、特殊标记等。
- 用户可编辑名称、头像资源、面板初始数据、特性、资源、背包等。

次要指示物生成 room token 时，以其 `panel_initial` 作为面板快照来源。

---

# 5 信息面板与隐藏数据

Room token 信息面板按 tab 展示：

- 概览
- 能力
- 法术
- 资源
- 背包
- 特性

隐藏数据：

- GM 可在 token 信息面板开启/关闭隐藏数据。
- 房间角色也有隐藏数据设置；通过该角色生成的新 token 默认继承。
- 非 GM 视角下，隐藏数据会被马赛克遮盖，但仍可展示累计伤害。
- 累计伤害由 `max_hp - current_hp` 计算，不作为独立权威字段保存。

---

# 6 实时与竞争控制

持久化修改通过 HTTP：

- `POST /rooms/{room_id}/tokens`
- `PATCH /rooms/{room_id}/tokens/{token_id}`
- `DELETE /rooms/{room_id}/tokens/{token_id}`
- `POST /rooms/{room_id}/characters/{character_id}/spawn-token`

实时预览通过 WebSocket：

- `token_transform_preview`

拖拽这类人类级持续操作会占用对象，避免多人同时拖拽竞争；只读选择与右键瞬时操作不应占用对象。占用状态会以用户头像/名称浮标展示。

---

# 7 权限

| 操作 | GM | PL | OB |
| --- | --- | --- | --- |
| 查看可见 token | ✓ | ✓ | ✓ |
| 创建/删除任意 token | ✓ | — | — |
| 移动/编辑任意 token | ✓ | — | — |
| 移动/编辑自己角色对应 token | ✓ | ✓ | — |
| 从自己角色生成 token | ✓ | ✓ | — |
| 修改隐藏数据 | ✓ | — | — |

战争迷雾覆盖的 token 对 PL/OB 不响应点击；若只覆盖一部分，未覆盖区域仍可点击。

---

# 8 后续

- 为 token 面板快照建立更严格的 schema。
- 补充 room token 与 scene snapshot 的测试。
- 梳理资源库 token 占用统计与角色删除释放的边界测试。
