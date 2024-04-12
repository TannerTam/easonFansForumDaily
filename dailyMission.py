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

username = os.environ['USERNAME']
password = os.environ['PASSWORD']

def login(driver):
    # 打开网页
    driver.get("https://www.easonfans.com/forum/plugin.php?id=ahome_dayquestion:index")

    # 等待并填写登录表单
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )
    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.NAME, "loginsubmit").click()

    login_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "umLogin"))
    )
    # 登录后的操作
    if login_element:
        print("登录成功！")
    else:      
        print("登录失败。")
        driver.quit()
        exit() 

def signin(driver):
    # 导航到签到页面
    driver.get("https://www.easonfans.com/forum/plugin.php?id=dsu_paulsign:sign")

    try:
        # 检查是否已经签到或签到未开始
        message_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), '您今天已经签到过了或者签到时间还未开始')]"))
        )
        print("今天已签到或签到未开始。")
    except TimeoutException:
        # 签到按钮可点击，开始签到流程
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
            matches = re.search(r"今日已参与 \((\d+)/(\d+)\)", participated_element.text)
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
            print(f"遇到异常：{e}")
            break

def answer_question(driver, question_number):
    # 等待选项加载并点击
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "a4"))).click()
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

def perform_lottery(driver):
    # 等待抽奖按钮可点击并点击
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "pointlevel"))
    ).click()
    print("开始免费抽奖。")
    sleep(5)  # 等待抽奖结果

def lottery(driver):
    if not check_free_lottery(driver):
        print("今天已免费抽奖。")
        return

    perform_lottery(driver)

    # 重新检查是否抽奖成功
    if not check_free_lottery(driver):
        print("免费抽奖成功！")
    else:
        print("免费抽奖失败。")

if __name__ == '__main__':
    # 模拟浏览器打开网站
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chromedriver = "/usr/local/bin/chromedriver.exe"
    # os.environ["webdriver.chrome.driver"] = chromedriver
    service = Service(executable_path='/usr/local/bin/chromedriver.exe')
    driver = webdriver.Chrome(options=chrome_options)
    login(driver)
    signin(driver)
    question(driver)
    lottery(driver)
    driver.quit()  