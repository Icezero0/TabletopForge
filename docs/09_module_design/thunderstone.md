# ThunderStone 房间模式与卡牌资产模块

版本：v0.1  
状态：Draft  
最后核对：2026-06-19

---

# 1 模块定位

ThunderStone 模式用于将 Thunderstone / Thunderstone Advance 类 DBG 桌游电子化。它与 DND5E 的桌面跑团模式差异很大，不应复用 DND5E 的角色卡、指示物、战斗面板、地图桌面等业务 UI。

当前目标不是立刻实现完整规则自动化，而是先完成：

1. 卡牌图片资产导入。
2. 卡牌文字与图片分离。
3. 结构化卡牌定义草稿。
4. 后续牌区、牌堆、玩家操作、原子动作与效果脚本系统的基础设计。

---

# 2 与房间基础层的关系

ThunderStone 复用房间基础层：

- 房间基础信息。
- 成员、权限、邀请。
- 房间基础 WebSocket 会话。
- 普通聊天 / 掷骰日志是否复用需后续再定。

ThunderStone 不直接复用：

- DND5E 角色卡。
- DND5E 指示物。
- DND5E 地图 / 绘制 / 迷雾 / 战斗面板。
- DND5E Token 信息面板。

前端入口：

```text
RoomPage.vue
  ├─ Dnd5eRoomMode.vue
  └─ ThunderStoneRoomMode.vue
```

---

# 3 当前资产结构

当前 ThunderStone 原始资产放在：

```text
data/thunderstone/source/cards/
```

其中：

```text
deck_XX_网格_r行_c列.png
.card_localizer_state.json
.card_localizer_work/work_state.json
.card_localizer_work/*_image.png
```

## 3.1 根目录 deck 图片

根目录 `deck_XX_...png` 是从原始大图切出的单卡参考图，命名保留来源位置：

```text
deck_09_10x7_r01_c01.png
```

可解析为：

- `deck_09`：来源 deck 编号。
- `10x7`：原始排版网格。
- `r01_c01`：行列位置。

这些图片适合保留为原始参考，不应作为最终电子卡牌主图。

## 3.2 空白卡牌底图

真正适合作为电子卡牌图片资产的是：

```text
data/thunderstone/source/cards/.card_localizer_work/*_image.png
```

这些图片是通过工具消去标题、类型、效果文字后的空白卡牌底图。系统内应将这些图片作为卡牌底图，再由前端或渲染层叠加文字。

## 3.3 work_state.json

`work_state.json` 当前结构：

```json
{
  "version": 1,
  "images": {
    "deck_09_10x7_r01_c01.png": {
      "source_path": "deck_09_10x7_r01_c01.png",
      "image_path": ".card_localizer_work\\..._deck_09_10x7_r01_c01_image.png",
      "preview_path": "outputs\\deck_09_10x7_r01_c01_localized.png",
      "masks": [],
      "texts": [],
      "has_unsaved_changes": false,
      "updated_at": "..."
    }
  }
}
```

`texts` 是最重要的字段，包含文字块、坐标和样式：

```json
{
  "x": 118,
  "y": 60,
  "w": 227,
  "h": 42,
  "text": "蚀酸蜥人",
  "font_family": "STLiti",
  "font_size": 41,
  "color": "#ffffff",
  "align": "center"
}
```

---

# 4 建议 catalog 草稿

第一阶段建议生成：

```text
data/thunderstone/catalog/cards.draft.json
```

每张卡结构建议：

```json
{
  "id": "deck_09_10x7_r01_c01",
  "source": {
    "source_file": "deck_09_10x7_r01_c01.png",
    "deck": 9,
    "grid": "10x7",
    "row": 1,
    "column": 1
  },
  "image": {
    "blank_path": ".card_localizer_work\\..._deck_09_10x7_r01_c01_image.png",
    "preview_path": "outputs\\deck_09_10x7_r01_c01_localized.png"
  },
  "text_layer": {
    "blocks": []
  },
  "parsed": {
    "name": "蚀酸蜥人",
    "type_line": "蜥蜴人・类人生物",
    "rules_text": "战斗：你可以摧毁手牌中任意数量的物品..."
  },
  "card": {
    "category": null,
    "subtypes": [],
    "stats": {},
    "effect_script": null
  }
}
```

说明：

- `source` 用于追溯来源。
- `image.blank_path` 是主图。
- `text_layer.blocks` 保留全部文字块与样式。
- `parsed` 是从坐标和文本块推断出的草稿。
- `card` 是后续人工校对后的正式结构化字段。

---

# 5 卡牌分类方向

初步分类：

```text
地下城牌
  ├─ 怪物
  └─ 地下城特征
      ├─ 环境
      ├─ 陷阱
      ├─ 宝藏
      └─ 其他

村庄牌
  ├─ 英雄
  ├─ 武器
  ├─ 法术
  ├─ 物品
  ├─ 村民
  └─ 其他
```

分类不应只依赖 deck 编号，最终应由 `type_line` 和人工校对确认。

---

# 6 效果系统方向

ThunderStone 卡牌效果建议分层：

```text
游戏状态层
  ├─ 玩家
  ├─ 手牌 / 抽牌堆 / 弃牌堆
  ├─ 村庄区域
  ├─ 地下城区域
  └─ 当前阶段 / 回合

原子动作层
  ├─ 抽牌
  ├─ 弃牌
  ├─ 摧毁
  ├─ 获得牌
  ├─ 移动牌
  ├─ 调整金币 / 攻击 / 光源 / 经验
  └─ 展示 / 翻开 / 洗牌

效果脚本层
  ├─ 触发时机
  ├─ 条件
  ├─ 目标选择
  ├─ 数量表达式
  ├─ 分支
  └─ 调用原子动作
```

原则：

- 卡牌文字永远保留为权威展示。
- 自动化效果是对原子动作的编排，不写死在前后端代码里。
- 第一阶段不要求所有卡牌全自动，但底层模型应允许逐步补充效果脚本。

---

# 7 待办

1. 编写 `backend/scripts/thunderstone/build_card_catalog.py`，从 `work_state.json` 生成 `cards.draft.json`。
2. 识别空白/占位图片，避免作为有效卡牌导入。
3. 设计 ThunderStone 后端模型：
   - card set
   - card definition
   - card asset
   - room game state
   - player deck / hand / discard
4. 设计卡牌校对 UI。
5. 设计原子动作与效果脚本 JSON schema。
