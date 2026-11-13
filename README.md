# AI 行业雷达：云端原型

这是一个尚未部署的实验原型。GitHub Actions 云端采集元数据，另一工作流负责可选 Gemini 中文提炼，GitHub Pages 显示页面。电脑离线不影响云端任务；所有外部服务都有延迟和额度限制。

## 当前状态
- 默认不启用云端模型。仅当设置 GEMINI_API_KEY secret 且 ENABLE_FREE_AI 变量为 true 时调用；每日客户端调用上限默认 30 次，并非免费额度保证。务必只使用未关联付费计费的免费 API 项目。
- 采集每 10 分钟、提炼每 10 分钟错峰、网页每 10 分钟错峰部署。GitHub 可能延迟或跳过工作流；30 天保留期、请求上限、队列速度均为原型参数。
- 公开仓库和 GitHub Pages 会公开所有采集标题、链接、来源和摘要，不要将密钥或个人信息放入仓库。仅存元数据与摘要，不存原文正文。注意信息源和模型使用条款。
- 从 Gemini 返回 429 或失败会停止/延后重试，不会自动切换付费模型。模型和账号是否实际免费应由账户配置保证，项目自身不能核验计费状态。
- 目前尚未用真实 API 密钥或 GitHub 云环境验证；Google 跳转、网站反爬、模型免费额度与服务条款随时可能改变。

## 部署条件
1. 可用的 GitHub 账号及公开仓库；仓库默认分支应为 main。启用 Actions 与 GitHub Pages（Source: GitHub Actions）。
2. 将项目文件推送到仓库；先手动运行 collection 和 Publish 工作流，确认网页和抓取记录。
3. 如需云端 AI，使用 Google AI Studio 中未关联付费账单的免费项目，仅在仓库 Actions Secrets 添加 GEMINI_API_KEY，并将 Actions Variables 的 ENABLE_FREE_AI 设置为 true。不要把密钥写进文件或聊天。
4. 每次增加额度或调整模型前检查账户实际免费配额；daily limit 只是本项目的上限，不会防止关联计费账户产生费用。
5. 检查工作流错误、失败源、队列积压和 Pages 更新。该实验使用 JSON + Git 存储，需要评估仓库增长、并发推送及扩大规模后的迁移；生产版更适合数据库。

## 本地验证
使用 Python 3.12+ 安装 requirements.txt，然后执行 `python -m unittest discover -s tests -v` 和 `python radar.py collect`。`python -m http.server 8765` 后打开 http://localhost:8765/ 可查看页面。
