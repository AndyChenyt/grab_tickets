import os
import time
import pickle
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# 配置信息
DAMAI_URL = "https://www.damai.cn/"
LOGIN_URL = "https://passport.damai.cn/login?ru=https%3A%2F%2Fwww.damai.cn%2F"
COOKIE_PATH = "cookies.pkl"
STEALTH_JS_PATH = "stealth.min.js"

class DamaiSnatcher:
    def __init__(self, target_url, ticket_priority=None, viewer_names=None):
        self.target_url = target_url
        self.ticket_priority = ticket_priority or [] # 票档优先级列表
        self.viewer_names = viewer_names or [] # 观演人姓名列表
        self.status = 0 # 0: 未登录, 1: 已登录, 2: 抢票中
        
        # 初始化浏览器
        options = webdriver.ChromeOptions()
        # 禁用自动化栏
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.maximize_window()
        
        # 注入 stealth.min.js
        self.inject_stealth()

    def inject_stealth(self):
        if os.path.exists(STEALTH_JS_PATH):
            with open(STEALTH_JS_PATH, 'r') as f:
                stealth_js = f.read()
                self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                    'source': stealth_js
                })
            print("### 已注入 Stealth 脚本 ###")
        else:
            print("### 警告: 未找到 stealth.min.js，反爬能力将受限 ###")

    def save_cookies(self):
        pickle.dump(self.driver.get_cookies(), open(COOKIE_PATH, "wb"))
        print("### Cookie 已保存 ###")

    def load_cookies(self):
        if os.path.exists(COOKIE_PATH):
            self.driver.get(DAMAI_URL)
            cookies = pickle.load(open(COOKIE_PATH, "rb"))
            for cookie in cookies:
                self.driver.add_cookie(cookie)
            self.driver.refresh()
            print("### 已加载本地 Cookie ###")
            return True
        return False

    def login(self):
        if self.load_cookies():
            # 检查是否真的登录成功
            try:
                # 寻找首页的“退出”或“个人中心”标志
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//span[contains(text(), '退出')] | //a[contains(text(), '个人中心')]"))
                )
                print("### 自动登录成功 ###")
                self.status = 1
                return
            except:
                print("### Cookie 已失效，请重新登录 ###")
        
        # 手动登录流程
        self.driver.get(LOGIN_URL)
        print("### 请在浏览器中完成扫码登录 ###")
        while True:
            try:
                # 等待跳转回首页或检测到登录成功的元素
                if "damai.cn" in self.driver.current_url and "login" not in self.driver.current_url:
                    print("### 检测到登录成功 ###")
                    self.save_cookies()
                    self.status = 1
                    break
            except:
                pass
            time.sleep(1)

    def snatch(self):
        print(f"### 正在进入目标场次: {self.target_url} ###")
        self.driver.get(self.target_url)
        
        # 1. 监控抢票按钮
        print("### 正在监控开抢状态... ###")
        while True:
            try:
                # 尝试寻找“立即购买”或“立即预订”按钮
                # 大麦网按钮类名通常包含 'buybtn'
                buy_button = WebDriverWait(self.driver, 1).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, 'buybtn'))
                )
                print("### 发现可点击按钮，立即开抢！ ###")
                buy_button.click()
                break
            except TimeoutException:
                # 如果没找到，刷新页面或继续循环（取决于具体逻辑，通常高频刷新或等待状态改变）
                # 这里简单处理为循环等待，实际中可能需要根据倒计时刷新
                pass
            except Exception as e:
                print(f"### 抢票异常: {e} ###")
                break

        # 2. 选座/选票档 (如果弹出)
        # 注意：大麦网有时在详情页选，有时在弹出层选
        # 这里演示点击后的处理逻辑
        try:
            # 假设进入了订单确认页或选票页
            print("### 正在处理订单确认... ###")
            
            # 选择观演人 (如果需要)
            if self.viewer_names:
                for name in self.viewer_names:
                    try:
                        viewer_xpath = f"//span[contains(text(), '{name}')]/preceding-sibling::span"
                        WebDriverWait(self.driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, viewer_xpath))
                        ).click()
                        print(f"### 已勾选观演人: {name} ###")
                    except:
                        print(f"### 未能勾选观演人: {name} ###")

            # 提交订单
            submit_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '提交订单')]"))
            )
            submit_button.click()
            print("### 订单已提交！请尽快完成支付！ ###")
            
        except Exception as e:
            print(f"### 订单确认阶段异常: {e} ###")

    def run(self):
        self.login()
        if self.status == 1:
            self.snatch()
        
        # 保持浏览器开启，方便支付
        print("### 程序运行结束，请在浏览器中完成后续操作 ###")
        # time.sleep(3600) 

if __name__ == "__main__":
    # 示例用法
    target = "https://detail.damai.cn/item.htm?id=123456789" # 替换为实际演唱会ID
    snatcher = DamaiSnatcher(target, viewer_names=["张三", "李四"])
    # snatcher.run() # 实际运行时取消注释
