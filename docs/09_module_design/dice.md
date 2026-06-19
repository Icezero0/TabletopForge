# 骰子模块设计

版本：v0.5  
状态：Implemented / Living Document  
最后核对：2026-06-19

---

# 1 模块目标

骰子模块为房间提供服务端权威掷骰、掷骰日志、暗骰、投掷主体、公式编辑与用户预设能力。

当前实现偏底层：骰子系统不直接理解“攻击”“豁免”“技能”等语义，只负责按公式投掷并记录结果；右键菜单、角色/Token 信息面板等上层功能负责生成对应公式。

---

# 2 后端实现

主要模块：

```text
backend/app/modules/dice/engine.py
backend/app/modules/dice/preset_service.py
backend/app/modules/dice/preset_repository.py
backend/app/modules/rooms/dice/service.py
backend/app/modules/rooms/dice/repository.py
backend/app/modules/rooms/dice/schemas.py
```

主要数据表：

```text
room_dice_rolls
dice_presets
```

`room_dice_rolls` 已按 `scene_id` 作用域迁移。场景删除时，对应掷骰记录应随场景清理。

---

# 3 公式能力

当前支持方向：

- 标准骰：`1d20+5`、`d20`（省略数量时视为 `1d20`）。
- `d` 后省略面数时默认 `d20`，例如 `d优势+7` 等价于 `2d20kh1+7`。
- 多段骰：`2d8+2d4+3`。
- 保留最高/最低：`kh` / `kl`。
- 中文优势/劣势：
  - `1d优势20` 表达 `2d20kh1`
  - `2d优势20` 表达 `4d20kh2`
  - 劣势同理使用最低。
- 可忽略前导 `r` / `R`，例如 `r1d4` 等价于 `1d4`。
- 掷骰次数前缀：`x#formula`。
  - `2#1d20+5` 输出 2 条掷骰记录。
  - 省略时视为 `1#`。
- 固定加值、负数骰项和简单组合由 dice engine 解析。

不支持的公式应返回本地化错误提示。

---

# 4 明骰 / 暗骰

当前只有两种可见性：

```text
公开骰
暗骰
```

暗骰语义：仅 GM 能看到掷骰记录和结果。对非 GM 来说，暗骰本身不显示；因为“发生过一次暗骰”也是信息。

前端暗骰按钮使用眼睛类 icon 状态表达，不显示“非暗骰”文字。

---

# 5 投掷主体

每条掷骰记录有主体：

```text
actor_type: user | token
actor_id
```

显示规则：

- `user`：用户头像 + 用户名。
- `token`：指示物图像 + 指示物名称。

主体选择器：

- 永远包含当前用户。
- GM 可选择房间内全部可操控 token。
- PL 只可选择自己角色对应的 token。
- OB 不应拥有主动掷骰权限。

右键 token 使用预设或生成公式时，主体自动设置为该 token。

---

# 6 前端形态

主要组件：

```text
frontend/src/features/room/components/workspace/DiceRollPanel.vue
frontend/src/features/table/components/DicePresetMenuTree.vue
frontend/src/ui/base/BaseEntitySelect.vue
```

房间会话面板分为：

- 会话
- 掷骰日志
- 冒险日志（当前提示“待完善”）

掷骰日志下方保留：

- 暗骰按钮
- 投掷主体选择器
- 标签输入框
- 手写公式输入框
- 编辑按钮
- 掷骰按钮

编辑按钮打开掷骰编辑弹窗。弹窗内支持：

- 检定 / 数值 两种模式。
- 普通 / 优势 / 劣势 / 自定义。
- 自定义可设置投掷次数与保留数量，用于 `akhb` / `aklb` 类表达。
- 附加骰子 / 固定加值项。
- 掷骰次数，公式体现为 `x#`。

公式输入框支持命令历史：上下键切换上一条/下一条发送过的公式。发送后清空输入框。

---

# 7 掷骰预设

预设已从前端本地转为后端存储：

```text
dice_presets
```

能力：

- 保存 / 加载 / 删除预设。
- 分组。
- 排序。
- 移动预设到其他分组。
- 右键 token 菜单中“使用预设”按目录结构展开。

预设编辑不在菜单里直接完成，而是在弹窗中管理。

---

# 8 与 DND5E 的关系

DND5E 的攻击、法术攻击、豁免、六维检定、技能检定等不是 dice engine 的职责。

当前由上层从 token/角色快照中读取：

- 属性加值。
- 熟练 / 精通。
- 技能 / 豁免覆盖值。
- 先攻加值。
- 法术攻击加值。

然后生成公式写入掷骰面板。

---

# 9 实时事件

掷骰记录写入后广播：

```text
dice_roll
```

前端 `useRoomRealtimeSession` 接收后按当前 active scene 过滤。

---

# 10 后续

- 补完整公式 AST 与错误信息文档。
- 明确 `kh/kl/优势/劣势/自定义保留` 的内部规范格式。
- 给暗骰、scene scope、预设分组移动补专项测试。
- 冒险日志与掷骰日志进一步分离。
