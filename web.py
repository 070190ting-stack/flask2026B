import requests
from bs4 import BeautifulSoup

from flask import Flask, render_template, request
from datetime import datetime


import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# 判斷是在 Vercel 還是本地
if os.path.exists('serviceAccountKey.json'):
    # 本地環境：讀取檔案
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    # 雲端環境：從環境變數讀取 JSON 字串
    firebase_config = os.getenv('FIREBASE_CONFIG')
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)

firebase_admin.initialize_app(cred)




app = Flask(__name__)

@app.route("/")
def index():
    link = "<h1>歡迎來到施程瀚的網站20260409</h1>"
    link += "<a href=/mis>課程</a><hr>"
    link += "<a href=/today>現在時間日期</a><hr>"
    link += "<a href=/me>關於我</a><hr>"
    link += "<a href=/welcome?u=程瀚&d=靜宜資管&c=資訊管理導論>Get傳值</a><hr>"
    link += "<a href=/account>post傳值</a><hr>"
    link += "<a href=/math>次方與根號計算</a><hr>"
    link += "<br><a href=/read>讀取Firestore資料</a><br>"
    link += "<br><a href=/read2>讀取Firestore資料(輸入關鍵字)</a><br>"
    link += "<br><a href=/spider>爬取子青老師本學期課程</a><br>"
    link += "<br><a href=/m1>即將上映電影</a><br>"
    return link

@app.route("/m1")
def m1():
    # 1. 透過 GET 請求，取得網址列上的 keyword 參數 (預設為空字串)
    q = request.args.get("keyword", "")
    
    # 2. 建立一個包含搜尋框的 HTML 字串
    # value="q" 可以讓搜尋完後，框框裡面還保留著剛剛輸入的字
    R = f"""
    <h2>近期上映電影查詢</h2>
    <form action="/m1" method="GET">
        請輸入片名關鍵字：
        <input type="text" name="keyword" value="{q}">
        <button type="submit">查詢</button>
    </form>
    <hr>
    """

    # 3. 開始爬蟲
    url = "https://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    result = sp.select(".filmListAllX li")
    
    # 4. 處理資料並過濾
    for item in result:
        # 防呆：先把 img 標籤找出來，確定存在才繼續
        img_tag = item.find("img")
        if not img_tag:
            continue
            
        alt_text = img_tag.get("alt", "") # 電影名稱
        
        # 核心邏輯：如果使用者有輸入關鍵字，且關鍵字「不在」電影名稱中，就跳過這筆資料
        if q and q not in alt_text:
            continue
            
        # 如果符合條件（或是沒輸入關鍵字時），就把它加入結果中
        introuce = "https://www.atmovies.com.tw" + item.find("a").get("href")
        R += "<a href='" + introuce + "'>" + alt_text + "</a><br>"
        
        post = "https://www.atmovies.com.tw" + img_tag.get("src")
        R += "<img src='" + post + "'><br><br>"
        
    return R
    
@app.route("/spider")
def spider():
    R = ""
    url = "https://www1.pu.edu.tw/~tcyang/course.html"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    #print(Data.text)
    sp = BeautifulSoup(Data.text, "html.parser")
    result=sp.select(".team-box a")

    for i in result:
        R += i.text + i.get("href") + "<br>"
    return R

@app.route("/read2")
def read2():
    keyword = request.args.get("keyword")
    
    if not keyword:
        html_form = """
        <h2>搜尋老師系統</h2>
        <form action="/read2" method="GET">
            請輸入名字關鍵字：<input type="text" name="keyword" required>
            <input type="submit" value="開始搜尋">
        </form>
        <br>
        <a href="/">返回首頁</a>
        """
        return html_form

    db = firestore.client()
    collection_ref = db.collection("靜宜資管")
    docs = collection_ref.stream() 
    
    Result = f"<h3>您搜尋的關鍵字：{keyword}</h3>"
    found_data = False 
    
    for doc in docs:
        teacher = doc.to_dict()
        if "name" in teacher and keyword in teacher["name"]:
            Result += str(teacher) + "<br><br>"
            found_data = True

    if not found_data:
        Result += "抱歉，找不到符合的老師資料。<br><br>"
        
    Result += '<br><a href="/read2">返回重新搜尋</a>'
    
    return Result

@app.route("/read")
def read():
    Result = ""
    db = firestore.client()
    collection_ref = db.collection("靜宜資管")    
    docs = collection_ref.order_by("lab",direction=firestore.Query.DESCENDING).get()    
    for doc in docs:         
        Result += str(doc.to_dict()) + "<br>"    
    return Result

@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><a href=/>返回首頁</a>"
@app.route("/today")
def today():
    now = datetime.now()
    return render_template("today.html",datetime=str(now))

@app.route("/me")
def me():
    return render_template("MIS2B.html")

@app.route("/welcome", methods=["GET"])
def welcome():
    user = request.values.get("u")
    d = request.values.get("d")
    c = request.values.get("c")
    return render_template("welcome.html", name=user, dep=d, course = c)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        result = "您輸入的帳號是：" + user + "; 密碼為：" + pwd 
        return result
    else:
        return render_template("account.html")

@app.route("/math", methods=["GET", "POST"])
def math_calc():
    if request.method == "POST":
        try:
            x = float(request.form["x"])
            opt = request.form["opt"]
            y = float(request.form["y"])
           
            if opt == "^":
                result = x ** y
            elif opt == "√":
                if y == 0:
                    result = "錯誤：不能開0次方根"
                else:
                    result = x ** (1/y)
            else:
                result = "運算符號錯誤"
            return f"計算結果為：{result} <br><a href='/math'>回計算機</a>"
        except:
            return "請輸入正確的數字！<br><a href='/math'>返回</a>"
    else:
   
        return render_template("math.html")


if __name__ == "__main__":
    app.run(debug=True)
