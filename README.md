# 中山大学中法核生存手册

> 一本面向中山大学中法核工程与技术学院（IFCEN）学生的开源生存手册。当前为 **v0.1.0 框架版（逐章补写）**：已补充声明与序言正文，其余章节将逐步完善。

## 这个仓库是什么

这是一个 GitBook 风格的纯 Markdown 仓库，用 [SUMMARY.md](SUMMARY.md) 组织全书目录。每一页都是可以直接在 GitHub 上阅读的文字，不依赖任何构建工具，也不包含 PDF、图片或二进制文件。

## 当前状态

- 版本：v0.1.0 框架版
- 结构：序、立志篇、访谈集、生存技巧、附录
- 阅读页面：64 个（原有 59 页，新增 5 篇导览；不含协作文件、模板和目录文件）
- 正文进度：[声明](xu/sheng-ming.md)与[序言](xu/xu.md)已补充；其余章节暂保留框架与写作提示
- 目录：[SUMMARY.md](SUMMARY.md)
- 协作：[CONTRIBUTING.md](CONTRIBUTING.md)

## 全书结构

| 部分 | 页面 | 回答的问题 |
| --- | --- | --- |
| 序（含导览） | 4 | 为什么写、怎么用、边界在哪里 |
| 立志篇（含导览） | 16 | 学院、专业、第一年与长期方向 |
| 访谈集（含导览） | 23 | 交换、科研、保研、就业、转行 |
| 生存技巧（含导览） | 13 | 选课、考试、法语、实习、生活、心理 |
| 附录（含导览） | 7 | 时间线、联系方式、术语、资源、贡献 |

以上五篇共 63 页，加本首页共 64 页。各篇文件夹和含子目录的主题组都有 `README.md` 导览。

## 怎么读

- **刚入学**：先读[序](xu/xu.md)和[使用说明](xu/shi-yong-shuo-ming.md)，再看[新生第一年](li-zhi-pian/xin-sheng-di-yi-nian.md)。
- **想了解专业**：从[学院与专业速览](li-zhi-pian/xue-yuan-yu-zhuan-ye-su-lan.md)开始。
- **准备实习或升学**：直接跳到[实习与实践](sheng-cun-ji-qiao/shi-xi-yu-shi-jian.md)和[深造与职业选择](sheng-cun-ji-qiao/shen-zao-yu-zhi-ye-xuan-ze.md)。
- **想参与写作**：先读[贡献指南](CONTRIBUTING.md)，再从任意“待补充”页面开始。

## 目录结构

```text
.
├── README.md                 # 手册首页
├── SUMMARY.md                # 全书导航
├── xu/                       # 序：声明、序言、使用说明
├── li-zhi-pian/              # 立志篇；含思维方式子目录
├── fang-tan-ji/              # 访谈集；含五个主题子目录
├── sheng-cun-ji-qiao/        # 生存技巧
├── fu-lu/                    # 附录
├── templates/                # 普通章节与访谈写作模板
├── scripts/check_structure.py # 本地目录与链接检查
├── .github/                  # 检查流程、PR 模板
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── CHANGELOG.md
├── LICENSE
├── .gitbook.yaml
├── .gitignore
├── .gitattributes
└── .editorconfig
```

## 如何预览

- **GitHub**：直接点开任意 `.md` 文件，链接都可以互相跳转。
- **GitBook**：把仓库导入 GitBook，以根目录的 `.gitbook.yaml` 配置首页和 `SUMMARY.md`。实际在线同步需在 GitBook 中连接仓库。
- **本地**：任何 Markdown 编辑器都可以打开，不需要安装依赖。

## 维护时检查

本地安装 Python 3.10 或更高版本后，在仓库根目录运行：

```bash
python scripts/check_structure.py
```

检查相对链接、目录覆盖、重复条目、文件命名、配置和纯文本要求。外部网站是否仍可访问、页面中的政策事实是否准确，需要单独核对。推送与提交 PR 时，GitHub Actions 会执行同一检查。

## 如何贡献

见 [CONTRIBUTING.md](CONTRIBUTING.md)。如果只是指出某页缺失、过时或写错，可以在仓库 Issue 区留言，写清页面路径、问题类型和信息来源。

## 免责声明

本手册是学生自发编写的学习交流资料，**不是中山大学或中法核工程与技术学院的官方出版物**。涉及培养方案、推免、实习、就业等政策性内容时，均应以学院和学校当年发布的正式通知为准。

## License

除非另有说明，本作品采用 [CC BY-NC-SA 4.0](LICENSE) 许可协议。
