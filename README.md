# easonFansForumDaily
自动完成神经研究所每日任务

## 文件说明
- dailyMission.py 保存了完成每日任务的脚本，包括签到、答题和摩天轮抽奖。

## 使用方法
fork本repositroy后，在Settings->Secrets中新建仓库密码（New repository secret）。添加Name为`USERNAME`和`PASSWORD`的环境变量，分别添加自己神经研究所的账号和密码。添加Name为`MAIL_USERNAME`和`MAIL_PASSWORD`的环境变量，分别添加自己邮箱的SMTP账号和密码。
![tutorial1](img/tutorial1.png "tutorial1")
![tutorial2](img/tutorial2.png "tutorial2")

## 本地运行
1. 将dailyMission.py复制一份并改名为dailyMissionLocal.py
2. 将文件中的变量用户名等变量修改为自己的
3. 下载与自己chrome版本相符合的chrome driver，并将路径保存到变量chromedriver