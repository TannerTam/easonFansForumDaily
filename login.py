from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep

# 使用Service对象设置Chrome驱动器的路径
service = Service(executable_path='C:/Program Files/Google/Chrome/Application/chromedriver.exe')

# 创建一个Chrome浏览器实例
driver = webdriver.Chrome(service=service)


try:
    # 打开目标网页
    driver.get("https://www.easonfans.com/forum/plugin.php?id=ahome_dayquestion:index")

    # 等待并填写登录表单（请根据实际表单结构调整代码）
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )
    driver.find_element(By.NAME, "username").send_keys("xx")
    driver.find_element(By.NAME, "password").send_keys("xx")
    driver.find_element(By.NAME, "loginsubmit").click()

    # 登录后的操作
    try:
        # 使用显式等待来确定文本出现
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "umLogin"))
        )
        print("登录成功！")
    except:      
        print("登录失败。")
        driver.quit()
        exit() 

    for i in range(3):
        # 等待页面中ID为"inner"的元素加载完毕，并检查其文本
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "inner"))
        )
        # 如果已经答完题了，就退出循环
        if element.text == "今日已参与 (3/3)":  
            break

        print(f"开始回答第 {i+1} 题。")  # 使用 f-string 格式化输出
        # 等待第一个点击元素（单选按钮）加载完毕    
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
    print("答题完成！") 

    # 导航到签到页面
    driver.get("https://www.easonfans.com/forum/plugin.php?id=dsu_paulsign:sign")
    
    try:
        # 使用显式等待来确定文本出现
        message_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), '您今天已经签到过了或者签到时间还未开始')]"))
        )
        print("今天已签到!")
    except:
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
        print("签到成功！")

        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "inner"))
        )
    
    # 导航到抽奖页面
    driver.get("https://www.easonfans.com/forum/plugin.php?id=gplayconstellation:front")
    
    try:
        # 使用显式等待来确定文本出现
        message_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//span[contains(text(), '今日剩余免费次数：0次')]"))
        )
        print("今天已抽奖!")
    except:
        # 等待抽奖按钮可点击
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "pointlevel"))
        )

        # 开始抽奖
        div_element = driver.find_element(By.ID, "pointlevel")
        div_element.click()
        print("抽奖成功！")

    print("finished!")

    # input("Press Enter to exit...")
    

finally:
    # 确保无论如何都能关闭驱动，防止资源泄露
    driver.quit()
