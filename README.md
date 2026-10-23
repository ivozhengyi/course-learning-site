# Course Learning Site · 课程学习网站 Skill

**把课程资料，整理成能学、能练、能复习的网站。**

一个面向 AI 编程助手的可复用工作流：先问清课程与资料，再分析课件和考卷，制作初学/复习双路线，最后检查内容、判分与实际浏览器体验。

它来自 [DS Quest 数据结构学习站](https://github.com/ivozhengyi/ds-quest) 的制作与多轮内容打磨经验。这里公开的是可迁移的方法与检查工具，不绑定原课程文件，也不要求所有课程套同一题量。

[阅读工作流](SKILL.md) · [交付检查标准](references/quality-gates.md) · [体验参考网站](https://ivozhengyi.github.io/ds-quest/) · [提交反馈](https://github.com/ivozhengyi/course-learning-site/issues)

## 一句话启动

安装后，在目标课程目录中对 Codex 说：

> 用 $course-learning-site 做一个计算机网络课程的学习网站。

也可以把已知条件一起说清：

> 用 $course-learning-site 做一个通信原理学习网站。根目录有 PPT，没有历年卷，我是零基础，覆盖全部课件。

**信息缺失会先问。** 在 Codex 提供相应能力时，使用可点击选择题并等待真实回答；不会把未回答当作“没有资料”。没有选择题工具的环境使用精简文字选项。

## 它约束的，是交付质量

| 环节 | 工作流要求 |
| --- | --- |
| 资料分析 | 看原页、辨重复、区分正式卷/样卷/笔记，不编造高频或官方答案 |
| 初学 | 一个小目标、必要术语、小例子、图示过程、即时小练；再展开正式定义 |
| 复习 | 主动回忆、公式前提、易混条件、完整解题链条；按重要程度安排题量 |
| 练习 | 两套独立题库，基础与提高兼顾；逐选项反馈、过程解析、多解与单位约定 |
| 学习闭环 | 搜索、演示、错题、进度、笔记与备份；经验不冒充掌握度 |
| 验收 | 独立复算、公式渲染、存档检查、桌面/平板实际操作，记录真实结果 |

支持有/无课件、有/无历年卷四种资料组合。无考卷时按确认的课程范围训练，不能伪称本校历年重点；计算机网络和通信原理另有领域适配检查提示。

## 安装到 Codex

将本仓库克隆到用户技能目录的 `course-learning-site` 文件夹。默认目录的示例：

```bash
git clone https://github.com/ivozhengyi/course-learning-site.git ~/.codex/skills/course-learning-site
```

若你配置了其他 `CODEX_HOME`，放到其 `skills/course-learning-site` 下。若同名目录已存在，先检查现有内容，避免覆盖自定义修改。在新课程任务中显式调用 `$course-learning-site`。

其他支持读取技能文件的助手可从 [SKILL.md](SKILL.md) 进入；所需参考文件均使用仓库内相对路径。具体交互与浏览器操作取决于目标环境实际提供的工具。

## 检查工具

网站制作过程中，从真实内容导出课程清单，再运行：

```bash
python3 scripts/audit_curriculum.py /path/to/site/维护/课程审计.json
```

[审计字段说明](references/audit-format.md)包括来源、先修图、两轮内容与题库、核心覆盖和逐项反馈。脚本只用 Python 标准库，检查结构性遗漏、悬空引用、循环与题量。

运行工具的回归测试：

```bash
python3 -B scripts/test_audit_curriculum.py -v
```

**审计通过不等于内容正确。** 公式推导、题目多解、教学可理解性与浏览器交互仍需实际验收。本仓库验证了 skill 结构和 14 项审计工具测试，尚未声称所有课程都已完成端到端验证；模型、资料与工具能力也会影响结果。

## 文件结构

```text
SKILL.md                    工作流入口
agents/openai.yaml          Codex 展示与调用信息
references/intake.md        需求交互及四种资料组合
references/content-and-exams.md  教学分层与考法分析
references/course-adaptation.md 网络/通信等课程适配
references/quality-gates.md 完整交付验收标准
references/audit-format.md  课程审计数据格式
scripts/                   审计工具与回归测试
```

## 参与改进

欢迎带着真实调用案例反馈：哪里反复追问、哪里解释过难、哪些考法被漏练、什么检查抓住了问题。请移除私人资料，见 [贡献说明](CONTRIBUTING.md)。

想追踪工作流与检查工具的版本改进，可在 **Watch → Custom → Releases** 订阅更新。只有经过验证的修改才会写入版本说明。

[MIT License](LICENSE)。
