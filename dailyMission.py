from time import sleep
import re
import os

username = os.environ['USERNAME']
password = os.environ['PASSWORD']

def login():
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

def signin():
    # 导航到签到页面
    driver.get("https://www.easonfans.com/forum/plugin.php?id=dsu_paulsign:sign")
    message_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), '您今天已经签到过了或者签到时间还未开始')]"))
    )

    if message_element:
        print("今天已签到。")
    else:
        # 等待签到按钮可点击
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@onclick=\"showWindow('qwindow', 'qiandao', 'post', '0');return false\"]"))
        )

        # 开始签到
        li_element = driver.find_element(By.ID, "kx")
        li_element.click()
        radio_button = driver.find_element(By.CSS_SELECTOR, "input[type='radio'][name='qdmode'][value='3']")
        radio_button.click()
        link = driver.find_element(By.XPATH, "//a[@onclick=\"showWindow('qwindow', 'qiandao', 'post', '0');return false\"]")
        link.click()

        driver.get("https://www.easonfans.com/forum/plugin.php?id=dsu_paulsign:sign")
        message_element_1 = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), '您今天已经签到过了或者签到时间还未开始')]"))
        )
        if message_element_1:
            print("签到成功！")
        else:
            print("签到失败。")

def question():
    for i in range(4):
        driver.get("https://www.easonfans.com/forum/plugin.php?id=ahome_dayquestion:index")
        participated_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "inner"))
        )
        matches = re.search(r"今日已参与 \((\d+)/(\d+)\)", participated_element.text)
        participated = matches.group(1)

        if participated == "3":
            print("今日答题已完成。")
            break

        # 等待选项加载完毕    
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "a4"))
        )

        # 点击单选按钮
        radio_button = driver.find_element(By.ID, "a4")
        radio_button.click()

        # 等待提交按钮加载完毕
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@name='submit'][@value='true']"))
        )

        # 点击提交按钮
        submit_button = driver.find_element(By.XPATH, "//button[@name='submit'][@value='true']")
        submit_button.click()
        print(f"回答第 {participated+1} 题成功！")

def lottery():
    # 导航到抽奖页面
    driver.get("https://www.easonfans.com/forum/plugin.php?id=gplayconstellation:front")

    message_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//span[contains(text(), '今日剩余免费次数：0次')]"))
    )

    if message_element:
        print("今天已免费抽奖。")
    else:
        # 等待抽奖按钮可点击
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "pointlevel"))
        )

        # 开始抽奖
        div_element = driver.find_element(By.ID, "pointlevel")
        div_element.click()
        print("开始免费抽奖。")
        sleep(5)

        # 判断抽奖是否成功
        driver.get("https://www.easonfans.com/forum/plugin.php?id=gplayconstellation:front")

        message_element_1 = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//span[contains(text(), '今日剩余免费次数：0次')]"))
        )
        if message_element_1:
            print("免费抽奖成功！")
        else:
            print("免费抽奖失败。")

if __name__ == '__main__':
    login()
    signin()
    question()
    lottery()
    driver.quit()  