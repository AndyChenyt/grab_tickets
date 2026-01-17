# 大麦网演唱会抢票软件设计原理与架构

## 1. 概述

本项目旨在设计并实现一个针对大麦网（Damai.cn）演唱会门票的自动化抢票软件。鉴于大麦网对自动化工具的防御机制，本软件将采用**基于浏览器的自动化（Selenium）**技术路线，模拟真实用户的行为，以提高抢票成功率。

**免责声明：** 本软件仅供学习和研究网页自动化技术使用，不鼓励任何违反网站服务条款的行为。用户应确保在合法合规的前提下使用本代码。

## 2. 软件架构设计

抢票软件将采用模块化设计，主要由以下五个核心模块构成：

| 模块名称 | 核心功能 | 使用技术 |
| :--- | :--- | :--- |
| **配置管理模块** | 加载用户配置（如目标场次URL、票档、观演人信息、抢票数量等）。 | Python `configparser` 或 `json` |
| **浏览器驱动模块** | 初始化和管理Selenium WebDriver，设置浏览器参数。 | Python `Selenium` |
| **会话管理模块** | 实现Cookie免登录，持久化用户登录状态，避免抢票时进行二次登录。 | Python `Selenium` + `pickle` |
| **反爬虫对抗模块** | 注入`stealth.min.js`等脚本，修改浏览器指纹，模拟真实用户环境。 | Python `Selenium` `execute_cdp_cmd` |
| **核心抢票逻辑模块** | 实现抢票的自动化流程，包括页面监控、元素定位、快速点击和订单提交。 | Python `Selenium` `WebDriverWait` |

## 3. 核心算法与流程

抢票的核心在于**速度**和**稳定性**。本软件将采用“**预加载 + 快速点击 + 订单提交**”的策略。

### 3.1. 预加载与登录

1.  **初始化：** 启动Chrome浏览器，并最大化窗口。
2.  **反爬虫配置：** 在页面加载前，通过Chrome DevTools Protocol (CDP) 注入`stealth.min.js`脚本，隐藏Selenium的特征，如`navigator.webdriver`属性。
3.  **会话恢复：** 检查本地是否存在有效的`cookies.pkl`文件。
    *   **存在：** 加载Cookie并导航至大麦网首页，验证登录状态。
    *   **不存在：** 导航至登录页，提示用户扫码登录。登录成功后，将Cookie序列化保存到`cookies.pkl`。
4.  **目标页预加载：** 导航至目标演唱会详情页，等待开抢。

### 3.2. 核心抢票逻辑（Rapid Purchase Sequence）

抢票逻辑是一个高频、低延迟的循环过程，旨在在开票瞬间完成所有操作。

| 步骤 | 动作描述 | 关键技术点 |
| :--- | :--- | :--- |
| **1. 监控开抢** | 持续监控“立即购买”按钮的状态。一旦按钮变为可点击（通常是颜色或文本变化），立即执行下一步。 | `WebDriverWait` 配合 `ExpectedConditions`，或使用 `try-except` 循环高频查找元素。 |
| **2. 快速点击** | 找到“立即购买”按钮并点击。 | 使用精确的XPath或CSS选择器，避免页面结构变化导致失败。 |
| **3. 票档选择** | 在弹出的票档/场次选择框中，根据用户配置的优先级，快速选择目标票档和数量。 | 预先定位所有票档元素，使用`element.click()`，避免使用`select`标签的慢速操作。 |
| **4. 提交订单** | 点击“确定”或“提交订单”按钮，进入订单确认页。 | 确保在票档选择后，页面元素能被快速识别。 |
| **5. 确认订单** | 在订单确认页，自动选择观演人（根据用户配置），并点击“提交订单”按钮。 | 预先配置观演人信息，使用`element.click()`快速勾选。 |
| **6. 支付提示** | 订单提交成功后，页面跳转至支付宝或微信支付页面。程序暂停，提示用户在**限定时间内**手动完成支付。 | 打印清晰的支付提示信息，并保持浏览器窗口打开。 |

### 3.3. 关键代码实现思路

#### A. Cookie免登录

使用Python的`pickle`库来序列化和反序列化Selenium的Cookie对象，实现登录状态的持久化。

```python
import pickle
from selenium import webdriver

# 保存Cookie
def save_cookies(driver, path="cookies.pkl"):
    pickle.dump(driver.get_cookies(), open(path, "wb"))

# 加载Cookie
def load_cookies(driver, path="cookies.pkl"):
    driver.get("https://www.damai.cn") # 必须先访问一个域名才能设置cookie
    try:
        cookies = pickle.load(open(path, "rb"))
        for cookie in cookies:
            driver.add_cookie(cookie)
        driver.refresh() # 刷新页面以应用cookie
        return True
    except FileNotFoundError:
        return False
```

#### B. 反爬虫Stealth脚本注入

在初始化`WebDriver`后，通过执行CDP命令注入`stealth.min.js`的内容。

```python
# 假设 stealth_js_content 是 stealth.min.js 的文件内容
driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
    'source': stealth_js_content
})
```

#### C. 快速元素定位与点击

在抢票瞬间，使用`find_element`和`click`必须快速且稳定。

```python
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 监控抢票按钮
def monitor_button(driver, selector, timeout=600):
    # 等待直到元素可点击
    WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.CLASS_NAME, selector))
    ).click()
```

## 4. 总结

本抢票软件的设计核心在于**模拟真实用户行为**和**优化自动化流程的速度**。通过Cookie持久化避免二次登录，通过Stealth脚本对抗反爬虫机制，并通过高频监控和快速点击序列来抓住开票的瞬间。最终，软件将依赖用户手动完成最后的支付环节，以确保交易的安全性。
