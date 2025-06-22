import os
import time
import requests
import json
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from datetime import datetime


login_url = 'https://plogin.m.jd.com/login/login?appid=300&returnurl=https%3A%2F%2Fm.jd.com%2F&source=wq_passport'  # 京东登录页面

def getCookies():
    """ 获取登录后的 cookies """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # 启动浏览器
        page = browser.new_page()
        page.goto(login_url)  # 打开登录界面
        print("登录页面已跳转，建议使用手机验证码登录以获得较长有效期的 cookies。")
        
        # 等待用户手动登录京东
        while True:
            try:
                # 检查页面是否已经跳转到京东主页
                page.wait_for_url('https://m.jd.com/', timeout=3000)
                print("成功登录京东！")
                break
            except PlaywrightTimeoutError:
                print("等待用户完成登录...")

        # 获取 cookies 并保存到文件
        cookies = page.context.cookies()
        # 提取 pt_key 和 pt_pin
        pt_key_cookie = next((c for c in cookies if c["name"] == "pt_key"), None)
        pt_pin_cookie = next((c for c in cookies if c["name"] == "pt_pin"), None)

        if pt_key_cookie and pt_pin_cookie:
            new_pt_key = pt_key_cookie["value"]
            pt_pin = pt_pin_cookie["value"]
            print("pt_key 的值是：", new_pt_key)

            # 构造你需要的结构
            data = [{
                "value": f"pt_key={new_pt_key};pt_pin={pt_pin};",
                "name": "JD_COOKIE",
                "remarks": ""
            }]
            print(f"data: {data}")
        else:
            print("未找到 pt_key 或 pt_pin")
    return data

def qinglon(datas):
    """ 青龙登录 """
    ql_domain = '192.168.31.245'
    ql_port = 5700
    client_id = "V7f_RwILbWMy"
    client_secret = "Q3xg3V_dnVFZeQVs8O-VMb2Y"
    today = datetime.now().strftime("%Y-%m-%d")

    data = {
        "id": 2,
        "name": "JD_COOKIE",
        "value": datas[0]["value"],
        "remarks": f"京东cookie{today}自动更新"
    }

    #登录
    a = requests.get("http://%s:%d/open/auth/token?client_id=%s&client_secret=%s"%(ql_domain,ql_port,client_id,client_secret))
    if a.status_code == 200  and a.json()["code"] == 200:
        token = a.json()["data"]["token"]
        print("token:%s"%token)
    else:
        print("获取token失败")

    # 发送 PUT 请求到根路径 `/`
    put_resp = requests.put(
        f"http://{ql_domain}:{ql_port}/open/envs",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        data=json.dumps(data)
    )
    if put_resp.status_code == 200 and put_resp.json()["code"] == 200:
        print("青龙环境变量更新成功")
        envs = put_resp.json()["data"]
        # print(envs)
        if envs["status"]== 1:
            print(f"状态为{envs['status']}, 未启用")
            put_resp = requests.put(
                f"http://{ql_domain}:{ql_port}/open/envs/enable",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json=[envs["id"]]
            )
            if put_resp.status_code == 200 and put_resp.json()["code"] == 200:
                print("青龙环境变量启用成功")
            else:
                print("青龙环境变量启用失败")
        else:
            print(f"状态为{envs['status']}, 已启用")
    else:
        print("青龙环境变量更新失败")



if __name__ == '__main__':
    datas = getCookies()
    qinglon(datas)

