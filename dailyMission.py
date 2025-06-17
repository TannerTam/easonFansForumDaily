from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from time import sleep
import re
import os
import argparse
import json
import time
from PIL import Image
from io import BytesIO
import pytesseract
import base64
import shutil

import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
import io
import sys
from functools import partial
from datetime import datetime

username = None
password = None
mail_user = None
mail_pass = None

def login(driver):
    try:
        driver.get("https://www.easonfans.com/FORUM/member.php?mod=logging&action=login")

        verify_img = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "verifyimg"))
        )

        img_url = verify_img.get_attribute("src")

        base64_data = img_url.split(',')[1]

        image_data = base64.b64decode(base64_data)
        image = Image.open(BytesIO(image_data))

        # image.save("debug_verify_code.png")
        # print("[调试] 验证码图片已保存为 debug_verify_code.png")

        code = pytesseract.image_to_string(image)
        # print(f"识别的验证码: {code.strip()}")
        time.sleep(0.5)

        input_box = driver.find_element(By.ID, "intext")
        input_box.send_keys(code)

        # 填写登录表单
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        driver.find_element(By.NAME, "username").send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.NAME, "loginsubmit").click()

        # 检查是否登录成功
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "umLogin"))
        )
        print("登录成功！")
        return True

    except Exception as e:
        print(f"登录过程中出现错误")
        # return e
        # driver.quit()

def signin(driver):
    # 导航到签到页面
    driver.get("https://www.easonfans.com/forum/plugin.php?id=dsu_paulsign:sign")
    
    # 检查是否有徽章弹窗
    try:
        badge_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "fwin_badgewin_7ree"))
        )
        if badge_element:
            print("徽章弹窗出现，准备领取徽章。")
            # 打开徽章领取页面
            driver.get("https://www.easonfans.com/forum/plugin.php?id=badge_7ree:badge_7ree&code=1")

            
            button = driver.find_element("css selector", 'a[href*="plugin.php?id=badge_7ree"]')
            before_click_content = driver.page_source  # 记录点击前页面内容
            button.click()  # 点击领取按钮
            WebDriverWait(driver, 5).until(
                EC.staleness_of(badge_element)  # 等待元素失效（通常意味着页面刷新）
            )
            after_click_content = driver.page_source  # 记录点击后页面内容

            if before_click_content != after_click_content:
                print("徽章领取成功！")
            else:
                print("徽章领取失败。")

    except TimeoutException:
        print("没有徽章弹窗。")
    
    # 导航到签到页面
    driver.get("https://www.easonfans.com/forum/plugin.php?id=dsu_paulsign:sign")
    
    # 开始签到流程
    try:
        # 检查是否已经签到或签到未开始
        message_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), '您今天已经签到过了或者签到时间还未开始')]"))
        )
        print("今天已签到或签到未开始。")
    except TimeoutException:
        # 签到按钮可点击，开始签到流程
        try:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[@onclick=\"showWindow('qwindow', 'qiandao', 'post', '0');return false\"]"))
            )

            # 点击签到触发元素
            li_element = driver.find_element(By.ID, "kx")
            li_element.click()

            radio_button = driver.find_element(By.CSS_SELECTOR, "input[type='radio'][name='qdmode'][value='3']")
            radio_button.click()

            link = driver.find_element(By.XPATH, "//a[@onclick=\"showWindow('qwindow', 'qiandao', 'post', '0');return false\"]")
            link.click()

            # 重新检查是否签到成功
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), '您今天已经签到过了或者签到时间还未开始')]"))
                )
                print("签到成功！")
            except TimeoutException:
                print("签到失败。")
        except Exception as e:
            print(f"签到过程中出现错误。")


def question(driver):
    base_url = "https://www.easonfans.com/forum/plugin.php?id=ahome_dayquestion:index"
    question_count = 0
    max_attempts = 3

    while question_count < max_attempts:
        driver.get(base_url)
        try:
            # 等待页面加载完成并检查参与情况
            participated_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "inner"))
            )
            matches = re.search(r"\((\d+)/(\d+)\)", participated_element.text)
            if matches:
                participated, total = matches.groups()
                if participated == total:
                    print("今日答题已完成。")
                    break
                else:
                    answer_question(driver, int(participated))
                    question_count += 1
            else:
                print("未找到答题信息。")
                break
        except Exception as e:
            print(f"答题过程中出现错误。")
            break

def answer_question(driver, question_number):
    # 等待选项加载并点击
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "a1"))).click()
    # 提交答案
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[@name='submit'][@value='true']"))
    ).click()
    print(f"回答第 {question_number + 1} 题成功！")

def check_free_lottery(driver):
    driver.get("https://www.easonfans.com/forum/plugin.php?id=gplayconstellation:front")
    try:
        # 等待并检查是否还有剩余的免费抽奖次数
        message_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//span[contains(text(), '今日剩余免费次数：0次')]"))
        )
        return False  # 没有剩余免费抽奖次数
    except:
        return True  # 还有剩余免费抽奖次数

def lottery(driver):
    if not check_free_lottery(driver):
        print("今天已免费抽奖。")
        return

    # 等待抽奖按钮可点击并点击
    
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "pointlevel"))
        ).click()
        print("开始免费抽奖。")
        sleep(5)  # 等待抽奖结果

        # 重新检查是否抽奖成功
        if not check_free_lottery(driver):
            print("免费抽奖成功！")
        else:
            print("免费抽奖失败。")
    except Exception as e:
        print(f"抽奖过程中出现错误。")

def getMoney(driver):
    driver.get("https://www.easonfans.com/forum/home.php?mod=spacecp&ac=credit&showcredit=1")
    try:
        money_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//li[@class='xi1 cl']"))
        )
        money_text = money_element.text
        money_amount = [int(s) for s in money_text.split() if s.isdigit()][0]  # 提取数字并假设第一个数字为金钱数额
        return money_amount
    except Exception as e:
        print(f"获取金钱失败。")
        return 0
    
def sendEmail(msg):
    sender = receiver = mail_user
    message = MIMEText(msg, 'plain', 'utf-8')
    message['From'] = formataddr(("Daily mission Assitance", sender))
    message['To'] = formataddr(("Tanner", receiver))
    message['Subject'] = Header('签到脚本运行报告', 'utf-8')
    try:
        server=smtplib.SMTP_SSL("smtp.qq.com", 465)
        server.login(mail_user,mail_pass)  
        server.sendmail(sender,[receiver],message.as_string())
        print ("邮件发送成功。")
        server.quit()  # 关闭连接
    except smtplib.SMTPException as e:
        print(f"邮件发送失败。")

def capture_output(func):
    # 重定向标准输出到一个内存缓冲区
    buffer = io.StringIO()
    sys.stdout = buffer
    func()
    sys.stdout = sys.__stdout__  # 恢复标准输出
    return buffer.getvalue()
    
def merge(headless: bool, chromedriver_path: str):
    global username, password, mail_user, mail_pass

    # 模拟浏览器打开网站
    chrome_options = webdriver.ChromeOptions()
    if headless:
        chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    print(f"=== Script started at {datetime.now()} ===")
    login_success = False
    while not login_success:
        login_success = login(driver)
        if login_success:
            break
        else:
            print("5s后重试...")
            sleep(5)
    # login(driver)
    initial_money = getMoney(driver)
    signin(driver)
    question(driver)
    lottery(driver)
    final_money = getMoney(driver)
    print(f"金钱变化：{initial_money} -> {final_money}。")
    driver.quit()

def main():
    global username, password, mail_user, mail_pass

    parser = argparse.ArgumentParser()
    parser.add_argument('--local', action='store_true', help='Use local config and chromedriver path')
    parser.add_argument('--headless', action='store_true', help='Enable headless mode')
    args = parser.parse_args()
    # args.local = True
    # 配置加载
    try:
        if args.local:
            chromedriver_path = "/home/tanner/Scripts/chromedriver-linux64/chromedriver"
            with open('/home/tanner/Scripts/easonFansForumDaily/config.json', 'r') as f:
                config = json.load(f)
            username = config['USERNAME']
            password = config['PASSWORD']
            mail_user = config['MAIL_USERNAME']
            mail_pass = config['MAIL_PASSWORD']
        else:
            chromedriver_path = shutil.which("chromedriver")
            username = os.environ['USERNAME']
            password = os.environ['PASSWORD']
            mail_user = os.environ['MAIL_USERNAME']
            mail_pass = os.environ['MAIL_PASSWORD']
    except KeyError as e:
        raise Exception(f"Missing required configuration: {e}")

    # merge(headless=args.headless, chromedriver_path=chromedriver_path)
    merge_fn = partial(merge, headless=args.headless, chromedriver_path=chromedriver_path)
    output_message = capture_output(merge_fn)
    sendEmail(output_message)

if __name__ == '__main__':
    main()