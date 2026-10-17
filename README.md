# easonFansForumDaily

自动完成神经研究所每日签到、答题和摩天轮抽奖，并持续积累已确认的题目答案。

## 功能

- 自动登录、签到和免费抽奖。
- 答题前查询本地题库，优先使用已确认的正确答案。
- 排除题库中已确认的错误选项，再沿用原有 API 答题逻辑。
- 每次提交后确认答案对错，并将结果写入题库。
- GitHub Actions 运行后自动备份和提交题库。
- 提供支持模糊检索的 GitHub Pages 网页。

## 网页检索

[https://tannertam.github.io/easonFansForumDaily/](https://tannertam.github.io/easonFansForumDaily/)

支持模糊检索题目和答案。搜索结果中，绿色表示正确答案，红色表示错误答案。

## GitHub Actions 配置

Fork 仓库后，在 **Settings → Secrets and variables → Actions** 中添加：

- `USERNAME`、`PASSWORD`：第一个神经研究所账号和密码。
- `USERNAME1`、`PASSWORD1`：第二个账号和密码；不使用第二个账号时可相应调整 workflow。
- `MAIL_USERNAME`、`MAIL_PASSWORD`：接收运行报告的邮箱 SMTP 账号和密码。
- `API_KEY`：阿里百炼 API Key；如不使用也建议设置为 `0`。

API Key 可在[阿里百炼平台](https://bailian.console.aliyun.com)申请。

![配置示例一](img/tutorial1.png "tutorial1")
![配置示例二](img/tutorial2.png "tutorial2")

## 本地运行

1. 克隆仓库并创建环境：

    ```bash
    git clone git@github.com:TannerTam/easonFansForumDaily.git
    cd easonFansForumDaily
    conda create -n easonFansForumDaily python=3.10.0
    conda activate easonFansForumDaily
    pip install -r requirements.txt
    sudo apt update
    sudo apt install -y tesseract-ocr
    ```

2. 在仓库根目录创建 `config.json`：

    ```json
    {
      "USERNAME": "",
      "PASSWORD": "",
      "MAIL_USERNAME": "",
      "MAIL_PASSWORD": "",
      "API_KEY": ""
    }
    ```

3. 从 [Chrome for Testing](https://googlechromelabs.github.io/chrome-for-testing/#stable) 下载与本机 Chrome 匹配的 ChromeDriver，并把解压后的 `chromedriver-linux64` 或 `chromedriver-win64` 目录放在仓库根目录。

4. 运行脚本：

    ```bash
    # 无界面运行
    python dailyMission.py --local --headless

    # 显示浏览器窗口
    python dailyMission.py --local
    ```

## 文件说明

- `dailyMission.py`：执行登录、签到、答题和抽奖。
- `question_bank.py`：管理题库查询、记录和判定。
- `question_bank.json`：保存题目、选项及每次答题结果。
- `site/`：题库检索网页。
- `scripts/build_pages.py`：生成 GitHub Pages 发布文件。
- `.github/workflows/python-app.yml`：运行每日任务并回写题库。
- `.github/workflows/pages.yml`：测试并发布题库检索网页。

## 题库与自动回写

### 答题时如何处理

每道题提交前，脚本按以下顺序处理：

1. 如果题库有已确认的正确答案，直接选择该答案，不调用 API。
2. 如果没有正确答案，但题库有已确认的错误答案，会把**所有已确认错误的选项一起排除**，再把剩余选项发给原有 API。
3. 如果题库没有这道题的明确答案记录，沿用原有 API 逻辑。

API 调用方式、响应解析和调用次数限制保持不变。API 返回异常时仍会使用备选答案，但不会选择任何已确认错误的选项。即使只剩一个候选选项，也仍按原流程调用 API；如果所有选项都已确认错误，脚本会停止本次答题，等待人工检查题库。

### 重复题目如何进入题库

题目的唯一键由以下内容共同生成：

```text
题目文字 + 全部选项文字的集合
```

- 题目相同、选项集合也相同：视为同一道题。选项顺序或 `a1`、`a2`、`a3`、`a4` 标签变化不会创建新题。
- 题目相同、选项集合不同：视为不同题目，分别保存和判断。
- 每次提交都会在对应题目的 `attempts` 中追加一条记录，不会覆盖历史记录。

题目和选项目前只会合并多余空白；标点、繁简体或其他字符不同仍可能形成不同条目。

### 多次答题结果如何生效

题库按答案文字汇总历史记录，同一答案以最后一次明确的 `true` 或 `false` 为准：

- 最后一次为 `true`：下次直接选择。
- 最后一次为 `false`：下次从候选项中排除。
- `correct: null`：表示结果未确认，不会覆盖已有的明确结果，也不会参与选择或排除。

如果一道题已确认多个错误答案，这些错误答案会全部被排除，而不只是排除最近的一个。如果异常数据中同时存在多个当前有效的正确答案，脚本会选择当前页面选项顺序中的第一个。

### 如何判断答案是否正确

提交前后会比较网站统计：

- “累计答题”增加 1 且“累计答对”增加 1：记录为正确。
- “累计答题”增加 1 且“累计答对”不变：记录为错误。
- 统计缺失、没有更新或变化异常：记录为未确认，并停止本次答题以避免重复提交。

题库不会保存账号、密码或 API Key。

运行 Python 测试：

```bash
python -m unittest discover -s tests -v
```
