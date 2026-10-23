# 课程审计导出格式 v1

`scripts/audit_curriculum.py` 使用 Python 标准库，读取实际内容导出的 JSON，输出检查结果 JSON，失败时退出码为 1。不限网站框架；将网站已有字段映射到此快照，不必改变运行时架构。命令见 SKILL.md。

**必须从实际课程数据导出**。正文、例子、题干和反馈导出真实字符串，不能把它们都填成“已完成”让检查过关。本脚本不检查网页是否使用了这些数据，也不理解数学、语义或教学质量；专门复算与浏览器验收另做。

## 字段

- `schema_version`: `1`。
- `course`: 课程名。
- `materials`: `slides`、`papers` 各为 `provided` 或 `none`，表示已确认资料状态；`scope_basis` 为范围依据说明。确认前不能用 `none` 代替未知。
- `sources`: 来源数组，每项 `id`、`kind`、`locator`（文件或 URL）；`kind` 可为 `slides/paper/sample/notes/textbook/syllabus/official`；有页资料填正整数 `pages`（总页数）。课件型讲义可用 `notes`。正式卷与样卷分开，笔记不冒充卷。
- `chapters`: 每项 `id`、`priority_reason`（题量和优先级原因）。
- `topics`: 每项 `id`、`title`、`chapter`、布尔 `core`、`prerequisites`（知识点 ID 数组）、`citations`。它是共同的知识地图，不要求两模式一一对应相同节数。
- `lessons`: 每项 `id`、`mode`（`learn/review`）、`topics`（关联知识点 ID 数组）、`body`（实际正文）。初学另需 `example` 和 `classroom_check`；复习另需 `recall_prompt` 与 `conditions`（重要前提/边界，没有额外特殊条件也用清楚文字说明）。多个初学节可合并对应一个复习专题。
- `questions`: 每项 `id`、`mode`、`chapter`、`topics`、`family`、`difficulty`（`foundation/standard/challenge`）、`tier`（`core/optional`）、`kind`（如 `choice/numeric/sequence/written/code`）、`prompt`、`grading`（`auto/self`）、非空 `answer`、`explanation`、`basis`（`course/paper/general`）及 `citations`。自评题另需字符串 `rubric`。跨章题设置 `cross_chapter: true`。

所有类别 ID 在该数组内唯一；两模式题目 ID 也不能重复。`answer` 可以是数、字符串、数组或结构化评分参考；单选题 `answer` 必须是从 0 开始的选项序号。每个核心知识点两模式都须有讲解及主线题。复习题总量应更多；用户明确改变这一要求时在 `review_count_exception` 写清约定，不能为绕过检查而虚构例外。

## 引用和选择题

引用为 `{"source":"slides-1","page":3}`（原资料第 3 页，从 1 开始）；不按页的网页用 `{"source":"official-1","section":"具体章节锚点或标题"}`。脚本核对来源存在及页码范围，不核对原页语义，因此还必须看原资料。`paper` 题必须引用正式卷或样卷；`course` 题必须引用课程资料；`general` 可无题目引用，但知识地图仍有范围来源。

正式选择题和 `classroom_check` 都含 `prompt`、`options`（字符串数组）、`answer`（0 起序号）、`option_feedback`（与选项等长的逐项解释数组）。下面仅展示课堂小练字段形状，不是可用的课程内容：

```json
{
  "prompt": "本题完整问题",
  "options": ["选项内容一", "选项内容二", "选项内容三"],
  "answer": 0,
  "option_feedback": ["第一项为何成立", "第二项对应的误解及纠正", "第三项对应的误解及纠正"]
}
```

## 本脚本覆盖与未覆盖

覆盖：必需字段、重复 ID、来源页界限、资料状态冲突、先修循环/悬空引用、两模式核心覆盖、逐项反馈和自评评分点缺失、题量与题族统计。

需另行核验：解释是否易懂、知识是否正确、选项是否误导、跨模式是否只是换皮、难度标注是否真实、权重是否合理、内容是否出现在网页上、题目多解和判分、先修抽题约束、公式与交互、所有视觉与离线行为。不要把输出 `ok: true` 当完整交付许可。
