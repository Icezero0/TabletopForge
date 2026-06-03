# TabletopForge 数据库设计

版本：v0.2  
状态：Draft

---

# 1 文档定位

本文档描述 TabletopForge 的核心数据表、字段方向、关系和索引建议。

字段为初始设计，可在实现中根据 ORM 和迁移需求调整。

---

# 2 用户与站点

## 2.1 users

用途：存储系统用户。

核心字段：

```text
id
username
email
password_hash
avatar_url
site_role
created_at
updated_at
```

## 2.2 feedback

用途：存储用户反馈。

核心字段：

```text
id
user_id
category
content
status
handled_by
handled_at
created_at
updated_at
```

---

# 3 房间与成员

## 3.1 rooms

用途：存储跑团房间。

核心字段：

```text
id
name
description
owner_user_id
ruleset
visibility
current_scene_id
created_at
updated_at
deleted_at
```

## 3.2 room_members

用途：存储用户与房间的成员关系。

核心字段：

```text
id
room_id
user_id
room_role
game_role
status
joined_at
created_at
updated_at
```

索引建议：

```text
unique(room_id, user_id)
index(user_id)
index(room_id, room_role)
index(room_id, game_role)
```

## 3.3 room_join_requests

用途：存储加入房间申请。

核心字段：

```text
id
room_id
applicant_user_id
requested_game_role
message
status
reviewed_by
reviewed_at
created_at
updated_at
```

## 3.4 role_change_requests

用途：存储 room_role 或 game_role 变更申请。

核心字段：

```text
id
room_id
user_id
role_type
from_role
to_role
reason
status
reviewed_by
reviewed_at
created_at
updated_at
```

---

# 4 消息

## 4.1 messages

用途：普通聊天消息。

核心字段：

```text
id
room_id
sender_user_id
content
created_at
updated_at
```

## 4.2 rp_messages

用途：结构化 RP 消息。

核心字段：

```text
id
room_id
character_id
sender_user_id
action_text
speech_text
visibility
created_at
updated_at
```

---

# 5 角色

## 5.1 characters

用途：角色卡基础信息。

核心字段：

```text
id
room_id
owner_user_id
name
character_type
ruleset
avatar_asset_id
race
class_name
level
background
alignment
public_bio
private_notes
created_at
updated_at
deleted_at
```

## 5.2 character_attributes

用途：DND5E 属性。

核心字段：

```text
id
character_id
strength
dexterity
constitution
intelligence
wisdom
charisma
created_at
updated_at
```

## 5.3 character_states

用途：角色当前状态。

核心字段：

```text
id
character_id
max_hp
current_hp
temp_hp
armor_class
initiative_bonus
speed
death_save_successes
death_save_failures
inspiration
concentration
created_at
updated_at
```

## 5.4 character_resources

用途：角色资源，如法术位、职业资源。

核心字段：

```text
id
character_id
name
current_value
max_value
recovery_type
sort_order
created_at
updated_at
```

## 5.5 character_effects

用途：角色状态效果。

核心字段：

```text
id
character_id
name
description
source
duration
created_at
updated_at
```

---

# 6 地图桌面

## 6.1 scenes

用途：房间内场景。

核心字段：

```text
id
room_id
name
description
sort_order
created_at
updated_at
```

## 6.2 scene_maps

用途：场景地图配置。

核心字段：

```text
id
scene_id
background_asset_id
width
height
grid_enabled
grid_size
grid_offset_x
grid_offset_y
snap_to_grid
created_at
updated_at
```

## 6.3 tokens

用途：地图上的可操作对象。

核心字段：

```text
id
room_id
scene_id
asset_id
linked_character_id
name
token_type
x
y
width
height
rotation
z_index
visible
locked
owner_user_id
created_at
updated_at
```

索引建议：

```text
index(scene_id)
index(room_id)
index(linked_character_id)
```

---

# 7 资源

## 7.1 assets

用途：图片资源元信息。

核心字段：

```text
id
owner_user_id
room_id
asset_type
name
url
mime_type
size_bytes
width
height
created_at
updated_at
```

room_id 为空时表示个人资源。

---

# 8 骰子与日志

## 8.1 dice_rolls

用途：骰子记录。

核心字段：

```text
id
room_id
character_id
roller_user_id
expression
result_detail
total
roll_type
visibility
created_at
```

## 8.2 operation_logs

用途：关键操作日志。

核心字段：

```text
id
room_id
operator_user_id
entity_type
entity_id
action_type
before_value
after_value
description
created_at
```

索引建议：

```text
index(room_id, created_at)
index(room_id, action_type)
index(operator_user_id)
index(entity_type, entity_id)
```

---

# 9 数据库设计原则

1. 房间相关数据必须包含 room_id 或可追溯到 room_id。
2. 高频查询字段需要建立索引。
3. 关键业务对象建议软删除。
4. 操作日志不应被普通业务删除。
5. 资源表只存元信息，不直接存储文件二进制。
6. DND5E 字段先满足当前需求，复杂规则后续逐步拆分。
