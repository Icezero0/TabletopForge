# Step 6 杂项收尾

| # | 项 | 状态 |
|---|---|---|
| 1 | 角色类型：`pc_main` / `pc_additional` / `npc` | 已完成（`20260606_0012` 迁移 + 前后端 + 测试） |
| 2 | 根据实际改动更新 `working-note` / `docs` | 已完成（`4730ec6` 后本轮同步） |
| 3 | 分步提交、合并 `origin/dev`、推送 | 已完成（`4730ec6`） |

## 本轮已落地（除 kind 外）

- **AI 角色导入**：`POST /characters/import-preview`；编辑页「AI 导入」主入口；`import_prompt` / `import_service`
- **属性 Tab**：豁免/技能纯文本 `+X`，左对齐紧凑布局
- **信息预览**：`InfoPanel` 不展示 `features.custom_fields`
- **编辑页**：无改动也可点保存（仅 `isSaving` 时禁用）
- **成员主色**：`room_members.player_color`；`PlayerColorPicker`；Pointer/绘制默认色
- **地图底栏**：`MapSpawnPopover` 地图列表切换；角色上场仍走 `CharacterSpawnPopover`
- **房间 Popover 关联全局库**：`GET /characters` 与房间库按 `character_id` 去重合并；未入库卡「未入库」标签；点击 `POST /rooms/{id}/characters/link` 后 `spawn-token`（`spawnCharacters.ts`）
- **GM Popover 创建者**：每张卡显示 `owner_id` 对应用户名（`room.characters.createdBy`）

## 近期提交（`origin/dev`）

- `1a8b021` — backend link API + pytest
- `eabe5ed` — membership `user_is_gm_in_any_room` 查询修复
- `d7fd04c` — frontend 合并列表、link 上场、GM 创建者
- `4730ec6` — working-note 首版记录

## 关键迁移

- `20260606_0011` — `room_members.player_color`
- `20260606_0012` — `characters.kind` / `room_characters.kind` 重命名与数据映射
