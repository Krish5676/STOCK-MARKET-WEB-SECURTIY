from flask import Flask, render_template, request, redirect, session
import pandas as pd
import os
import random
from datetime import datetime
import hashlib
import yfinance as yf

from rsa_utils import encrypt_password, decrypt_password
from otp_email import send_otp
from email_passkey import send_passkey

app = Flask(__name__)
app.secret_key = "secret123"

# ================= DATABASE =================
def init_db():
    if not os.path.exists("database.xlsx"):
        df = pd.DataFrame(columns=[
            "username","email","mobile","password",
            "attempts","blocked","balance","photo"
        ])
        df.to_excel("database.xlsx", index=False)

    if not os.path.exists("transactions.xlsx"):
        df = pd.DataFrame(columns=[
            "username","stock","type","qty","price","date","signature"
        ])
        df.to_excel("transactions.xlsx", index=False)

init_db()

# ================= STOCK API =================
def get_stock_price(symbol):
    stock = yf.Ticker(symbol + ".NS")
    data = stock.history(period="1d")
    if data.empty:
        return None
    return round(data['Close'].iloc[-1], 2)

@app.route("/stock_data/<symbol>")
def stock_data(symbol):
    stock = yf.Ticker(symbol + ".NS")
    data = stock.history(period="7d")

    return {
        "prices": list(data['Close']),
        "dates": [str(d.date()) for d in data.index]
    }

# ================= SIGNUP =================
@app.route("/", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        u = request.form["username"]
        e = request.form["email"]
        m = request.form["mobile"]
        p = request.form["password"]
        c = request.form["confirm"]

        if p != c:
            return "Password mismatch"

        df = pd.read_excel("database.xlsx")

        if e in df["email"].values:
            return "Email exists"

        enc = encrypt_password(p)

        photo = request.files.get("photo")
        fname = photo.filename if photo and photo.filename else "default.png"
        if photo and photo.filename:
            photo.save("static/images/" + fname)

        new = {
            "username":u,"email":e,"mobile":m,
            "password":enc,"attempts":0,
            "blocked":False,"balance":10000,
            "photo":fname
        }

        df = pd.concat([df,pd.DataFrame([new])], ignore_index=True)
        df.to_excel("database.xlsx", index=False)

        return redirect("/login")

    return render_template("signup.html")

# ================= LOGIN =================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = request.form["user"]
        pw = request.form["password"]

        df = pd.read_excel("database.xlsx")
        row = df[(df["username"]==user)|(df["email"]==user)]

        if row.empty:
            return "User not found"

        i = row.index[0]

        if df.at[i,"blocked"]:
            return "Account BLOCKED"

        real = decrypt_password(df.at[i,"password"])

        if pw == real:
            df.at[i,"attempts"] = 0
            df.to_excel("database.xlsx", index=False)
            session["user"] = df.at[i,"username"]
            return redirect("/dashboard")

        else:
            df.at[i,"attempts"] += 1

            if df.at[i,"attempts"] >= 3:
                df.at[i,"blocked"] = True

            df.to_excel("database.xlsx", index=False)
            return "Wrong Password"

    return render_template("login.html")

# ================= UNBLOCK =================
@app.route("/unblock", methods=["GET","POST"])
def unblock():
    if request.method == "POST":
        email = request.form["email"]
        otp = send_otp(email)
        session["otp"] = otp
        session["email"] = email
        return redirect("/verify_otp")

    return render_template("unblock.html")

@app.route("/verify_otp", methods=["GET","POST"])
def verify_otp():
    if request.method == "POST":
        if request.form["otp"] == session["otp"]:
            df = pd.read_excel("database.xlsx")
            i = df[df["email"]==session["email"]].index[0]

            df.at[i,"blocked"] = False
            df.at[i,"attempts"] = 0
            df.to_excel("database.xlsx", index=False)

            return "Account Unblocked!"

        return "Wrong OTP"

    return render_template("verify_otp.html")

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    df = pd.read_excel("database.xlsx")
    user = df[df["username"]==session["user"]].iloc[0]

    return render_template("dashboard.html", user=user)

# ================= TRADE =================
@app.route("/trade", methods=["GET","POST"])
def trade():
    if request.method == "POST":
        stock = request.form["stock"]
        qty = int(request.form["qty"])
        ttype = request.form["type"]

        price = get_stock_price(stock)

        if price is None:
            return "Invalid Stock"

        passkey = send_passkey(
            pd.read_excel("database.xlsx")
            [pd.read_excel("database.xlsx")["username"]==session["user"]]["email"].values[0]
        )

        session["passkey"] = passkey
        session["trade"] = (stock, qty, ttype, price)

        return redirect("/verify_trade")

    return render_template("trade.html")

# ================= VERIFY TRADE =================
@app.route("/verify_trade", methods=["GET","POST"])
def verify_trade():
    if request.method == "POST":
        if request.form["passkey"] == session["passkey"]:

            stock, qty, ttype, price = session["trade"]

            sign = hashlib.sha256(
                f"{session['user']}{stock}{qty}{price}".encode()
            ).hexdigest()

            df = pd.read_excel("transactions.xlsx")

            new = {
                "username":session["user"],
                "stock":stock,
                "type":ttype,
                "qty":qty,
                "price":price,
                "date":datetime.now(),
                "signature":sign
            }

            df = pd.concat([df,pd.DataFrame([new])], ignore_index=True)
            df.to_excel("transactions.xlsx", index=False)

            return "Trade Success!"

        return "Wrong Passkey"

    return render_template("verify_trade.html")

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)