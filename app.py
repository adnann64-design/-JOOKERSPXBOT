"""
JOKER ULTIMATE ELITE — SPX Options Signal Bot
Flask Backend + Telegram Sender
"""

import os, math, time, logging, threading
from datetime import datetime
import pytz
import numpy as np
import pandas as pd
import yfinance as yf
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import requests as req

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app  = Flask(__name__)
CORS(app)

# ══════════════════════════════════
#  CONFIG (from environment / .env)
# ══════════════════════════════════
BOT_TOKEN  = os.environ.get("BOT_TOKEN",  "")
CHAT_ID    = os.environ.get("CHAT_ID",    "")
NY_TZ      = pytz.timezone("America/New_York")

# ══════════════════════════════════
#  SHARED STATE
# ══════════════════════════════════
state = {
    "last_signal":  None,
    "last_price":   0,
    "bull_score":   0,
    "bear_score":   0,
    "rsi":          50,
    "adx":          20,
    "trend_up":     True,
    "htf_bull":     True,
    "is_whale":     False,
    "last_scan":    "—",
    "scan_count":   0,
    "signals_sent": 0,
    "log":          [],
    "auto_scan":    False,
}

def add_log(tag, msg):
    now = datetime.now(NY_TZ).strftime("%H:%M:%S")
    state["log"].append({"time": now, "tag": tag, "msg": msg})
    if len(state["log"]) > 100:
        state["log"].pop(0)
    logger.info(f"[{tag}] {msg}")

# ══════════════════════════════════
#  MATH HELPERS
# ══════════════════════════════════
def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()

def rma(s, n):
    return s.ewm(alpha=1/n, adjust=False).mean()

def atr(df, n=14):
    h,l,c = df["High"], df["Low"], df["Close"]
    tr = pd.concat([(h-l),(h-c.shift()).abs(),(l-c.shift()).abs()], axis=1).max(axis=1)
    return rma(tr, n)

def rsi(s, n=14):
    d = s.diff()
    g = rma(d.clip(lower=0), n)
    ls = rma((-d).clip(lower=0), n)
    return 100 - 100/(1+g/ls.replace(0,np.nan))

def adx_calc(df, n=14):
    h,l,c = df["High"],df["Low"],df["Close"]
    up = h-h.shift(); dn = l.shift()-l
    pdm = np.where((up>dn)&(up>0), up, 0.0)
    mdm = np.where((dn>up)&(dn>0), dn, 0.0)
    tr  = pd.concat([(h-l),(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    a14 = rma(tr, n)
    pdi = 100*rma(pd.Series(pdm,index=df.index),n)/a14
    mdi = 100*rma(pd.Series(mdm,index=df.index),n)/a14
    dx  = 100*(pdi-mdi).abs()/((pdi+mdi).replace(0,np.nan))
    return rma(dx.fillna(0), n), pdi, mdi

def supertrend(df, f=3.0, n=10):
    a = atr(df, n)
    hl2 = (df["High"]+df["Low"])/2
    up  = hl2+f*a; lo = hl2-f*a
    d = pd.Series(1, index=df.index)
    for i in range(1,len(df)):
        d.iloc[i] = -1 if df["Close"].iloc[i]>up.iloc[i-1] else (1 if df["Close"].iloc[i]<lo.iloc[i-1] else d.iloc[i-1])
    return d

def pivot_high(s, n=5):
    r = pd.Series(np.nan, index=s.index)
    for i in range(n, len(s)-n):
        if s.iloc[i] == s.iloc[i-n:i+n+1].max():
            r.iloc[i] = s.iloc[i]
    return r

def pivot_low(s, n=5):
    r = pd.Series(np.nan, index=s.index)
    for i in range(n, len(s)-n):
        if s.iloc[i] == s.iloc[i-n:i+n+1].min():
            r.iloc[i] = s.iloc[i]
    return r

# ══════════════════════════════════
#  ANALYSIS ENGINE
# ══════════════════════════════════
def analyze(min_score=7):
    try:
        add_log("FETCH", "Downloading SPX data...")
        df  = yf.download("^GSPC", period="5d",  interval="5m",  progress=False, auto_adjust=True)
        dfh = yf.download("^GSPC", period="30d", interval="1h",  progress=False, auto_adjust=True)

        if isinstance(df.columns,  pd.MultiIndex): df.columns  = df.columns.get_level_values(0)
        if isinstance(dfh.columns, pd.MultiIndex): dfh.columns = dfh.columns.get_level_values(0)

        if df.empty or len(df) < 60:
            add_log("ERR","Not enough data"); return None

        c,h,l,o,v = df["Close"],df["High"],df["Low"],df["Open"],df["Volume"]

        atr_v  = float(atr(df).iloc[-1])
        avgvol = v.rolling(20).mean()
        rsi_v  = float(rsi(c).iloc[-1])
        ema9   = float(ema(c,9).iloc[-1])
        ema21  = float(ema(c,21).iloc[-1])
        ema50  = float(ema(c,50).iloc[-1])
        ema200 = float(ema(c,200).iloc[-1])
        adx_v, pdi_v, mdi_v = adx_calc(df)
        adx_v  = float(adx_v.iloc[-1])
        st_dir = int(supertrend(df).iloc[-1])

        cv = float(c.iloc[-1]); hv=float(h.iloc[-1]); lv=float(l.iloc[-1]); ov=float(o.iloc[-1]); vv=float(v.iloc[-1])
        avgv = float(avgvol.iloc[-1])

        # HTF
        htf_bull = True
        if len(dfh) >= 50:
            htf_e = float(ema(dfh["Close"],200).iloc[-1]) if len(dfh)>=200 else float(ema(dfh["Close"],50).iloc[-1])
            htf_bull = float(dfh["Close"].iloc[-1]) > htf_e

        is_whale = vv > avgv * 1.8
        high_vol = vv > avgv * 1.5
        trend_up = cv > ema200
        trend_dn = cv < ema200
        strong   = adx_v > 25
        adx_ok   = adx_v > 20

        rsi5  = rsi(c).iloc[-6:-1]
        bull_div = (lv < float(l.iloc[-6:-1].min())) and (rsi_v > float(rsi5.min()))
        bear_div = (hv > float(h.iloc[-6:-1].max())) and (rsi_v < float(rsi5.max()))

        # SR levels
        ph = pivot_high(h,5).dropna().tail(8)
        pl = pivot_low(l,5).dropna().tail(8)
        near_sup = any(abs(lv-x)<atr_v*1.2 for x in pl.values)
        near_res = any(abs(hv-x)<atr_v*1.2 for x in ph.values)
        sup_lvl  = min(pl.values, key=lambda x:abs(lv-x)) if len(pl) else cv
        res_lvl  = min(ph.values, key=lambda x:abs(hv-x)) if len(ph) else cv

        # FVG
        fvg_bull = float(h.iloc[-3])<float(l.iloc[-1]) and (float(l.iloc[-1])-float(h.iloc[-3]))>atr_v*0.1
        fvg_bear = float(l.iloc[-3])>float(h.iloc[-1]) and (float(l.iloc[-3])-float(h.iloc[-1]))>atr_v*0.1

        # Liq sweep
        ll5 = float(l.iloc[-6:-1].min()); hh5 = float(h.iloc[-6:-1].max())
        liq_bull = (lv<ll5) and (cv>ll5) and is_whale
        liq_bear = (hv>hh5) and (cv<hh5) and is_whale

        # Candle
        bull_pin = (cv-lv)>(hv-lv)*0.6; bear_pin=(hv-cv)>(hv-lv)*0.6
        bull_wk  = (cv-lv)>(hv-cv)*1.5; bear_wk =(hv-cv)>(cv-lv)*1.5
        bull_c   = cv>ov; bear_c=cv<ov

        # BOS
        ph5=float(h.iloc[-6]); pl5=float(l.iloc[-6])
        bos_bull = cv>ph5 and trend_up; bos_bear=cv<pl5 and trend_dn
        choch_b  = cv>ph5 and trend_dn; choch_s =cv<pl5 and trend_up

        bs = sum([
            2 if near_sup else 0, 2 if bos_bull else 0, 1 if choch_b else 0,
            2 if is_whale else 0, 1 if trend_up else 0, 1 if htf_bull else 0,
            2 if bull_div else 0, 1 if strong else 0,   2 if liq_bull else 0,
            1 if st_dir==-1 else 0, 1 if fvg_bull else 0, 1 if (bull_pin or bull_wk) else 0])

        ss = sum([
            2 if near_res else 0,  2 if bos_bear else 0, 1 if choch_s else 0,
            2 if is_whale else 0,  1 if trend_dn else 0, 1 if not htf_bull else 0,
            2 if bear_div else 0,  1 if strong else 0,   2 if liq_bear else 0,
            1 if st_dir==1 else 0, 1 if fvg_bear else 0, 1 if (bear_pin or bear_wk) else 0])

        rfi_b = rsi_v<70; rfi_s=rsi_v>30
        base_b = rfi_b and adx_ok and high_vol and (bull_c or bull_pin or bull_wk)
        base_s = rfi_s and adx_ok and high_vol and (bear_c or bear_pin or bear_wk)

        final_buy  = bs>=min_score and base_b and htf_bull
        final_sell = ss>=min_score and base_s and (not htf_bull)

        sig = "BUY" if final_buy else ("SELL" if final_sell else None)
        score = bs if final_buy else (ss if final_sell else max(bs,ss))

        # TP/SL
        if final_buy:
            sl = (float(sup_lvl)-atr_v*1.5) if near_sup else (lv-atr_v*1.5)
            risk = cv-sl
            tp1=cv+risk; tp2=cv+risk*2; tp3=cv+risk*3
        elif final_sell:
            sl = (float(res_lvl)+atr_v*1.5) if near_res else (hv+atr_v*1.5)
            risk = sl-cv
            tp1=cv-risk; tp2=cv-risk*2; tp3=cv-risk*3
        else:
            sl=tp1=tp2=tp3=risk=None

        strike=exp=opt_type=None
        if sig:
            strike = round((cv+(5 if final_buy else -5))/5)*5
            wd = datetime.now(NY_TZ).weekday()
            exp = "Daily (0DTE)" if wd in [0,2,4] else "Weekly (~2d)"
            opt_type = "CALL" if final_buy else "PUT"

        trigs = []
        if bos_bull or bos_bear: trigs.append("BOS")
        if bull_div or bear_div:  trigs.append("Divergence")
        if is_whale:              trigs.append("Whale Volume")
        if liq_bull or liq_bear:  trigs.append("Liq Sweep")
        if near_sup:              trigs.append("Near Support")
        if near_res:              trigs.append("Near Resistance")
        if strong:                trigs.append("ADX Strong")

        conf = "🔥 قوي جداً" if score>=12 else ("✅ قوي" if score>=9 else "⚡ متوسط")

        result = dict(
            signal=sig, price=round(cv,2), bull_score=bs, bear_score=ss,
            score=score, conf=conf, sl=round(sl,2) if sl else None,
            tp1=round(tp1,2) if tp1 else None, tp2=round(tp2,2) if tp2 else None,
            tp3=round(tp3,2) if tp3 else None, risk=round(risk,2) if risk else None,
            option_type=opt_type, strike=strike, expiry=exp,
            rsi=round(rsi_v,1), adx=round(adx_v,1),
            trend_up=trend_up, htf_bull=htf_bull, is_whale=is_whale,
            strong=strong, triggers=trigs
        )

        state.update(last_price=cv, bull_score=bs, bear_score=ss,
                     rsi=round(rsi_v,1), adx=round(adx_v,1),
                     trend_up=trend_up, htf_bull=htf_bull, is_whale=is_whale,
                     last_scan=datetime.now(NY_TZ).strftime("%H:%M:%S"),
                     scan_count=state["scan_count"]+1)
        if sig:
            state["last_signal"] = result

        add_log(sig or "WAIT", f"SPX:{cv:.2f} | Bull:{bs} Bear:{ss} | Score:{score}/17")
        return result

    except Exception as e:
        add_log("ERR", str(e)); logger.exception(e); return None

# ══════════════════════════════════
#  TELEGRAM SENDER
# ══════════════════════════════════
def build_message(d):
    isBull = d["signal"] == "BUY"
    emo    = "🟢" if isBull else "🔴"
    now    = datetime.now(NY_TZ).strftime("%Y-%m-%d %H:%M ET")
    trigs  = " | ".join(d["triggers"]) or "—"
    return f"""{emo}{emo}{emo} إشارة جديدة — SPX Options {emo}{emo}{emo}

{"📈 CALL شراء" if isBull else "📉 PUT شراء"}
🕐 {now}
💰 SPX الحالي: {d['price']:,}

━━━━━━━━━━━━━━━━━━━━━━━
📋 تفاصيل العقد:
• النوع:      {d['option_type']}
• السترايك:   {d['strike']:,}
• الانتهاء:   {d['expiry']}

━━━━━━━━━━━━━━━━━━━━━━━
🎯 الأهداف والوقف:
✅ TP1 (1R):  {d['tp1']:,.2f}
✅ TP2 (2R):  {d['tp2']:,.2f}
✅ TP3 (3R):  {d['tp3']:,.2f}
🛑 SL:        {d['sl']:,.2f}
📐 المخاطرة:  {d['risk']:,.2f} نقطة

━━━━━━━━━━━━━━━━━━━━━━━
📊 المؤشرات:
• Score:  {d['score']}/17 — {d['conf']}
• RSI:    {d['rsi']}
• ADX:    {d['adx']}

⚡ المحفزات: {trigs}

━━━━━━━━━━━━━━━━━━━━━━━
⚠️ لا تخاطر بأكثر من 2% من الحساب
🤖 JOKER ULTIMATE ELITE"""

def send_telegram(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r   = req.post(url, json={"chat_id": chat_id, "text": text}, timeout=15)
    return r.json()

# ══════════════════════════════════
#  AUTO SCAN THREAD
# ══════════════════════════════════
_last_auto_signal = None

def auto_scan_loop():
    global _last_auto_signal
    while True:
        time.sleep(300)
        if not state["auto_scan"]: continue
        now_ny = datetime.now(NY_TZ)
        if now_ny.weekday() >= 5: continue
        if not (9*60+30 <= now_ny.hour*60+now_ny.minute <= 16*60): continue
        token = BOT_TOKEN; chat = CHAT_ID
        if not token or not chat: continue
        data = analyze()
        if data and data["signal"] and data["signal"] != _last_auto_signal:
            _last_auto_signal = data["signal"]
            msg = build_message(data)
            r   = send_telegram(token, chat, msg)
            if r.get("ok"):
                state["signals_sent"] += 1
                add_log("AUTO", f"Signal sent: {data['signal']} | Score:{data['score']}/17")
            else:
                add_log("ERR", f"Telegram error: {r.get('description','')}")

threading.Thread(target=auto_scan_loop, daemon=True).start()

# ══════════════════════════════════
#  ROUTES
# ══════════════════════════════════
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    body      = request.get_json() or {}
    min_score = int(body.get("min_score", 7))
    data      = analyze(min_score)
    if data is None:
        return jsonify({"error": "فشل التحليل، حاول مرة أخرى"}), 500
    return jsonify(data)

@app.route("/api/send", methods=["POST"])
def api_send():
    body    = request.get_json() or {}
    token   = body.get("token", BOT_TOKEN)
    chat_id = body.get("chat_id", CHAT_ID)
    signal  = body.get("signal")

    if not token or not chat_id:
        return jsonify({"error": "Bot Token أو Chat ID مفقود"}), 400
    if not signal:
        return jsonify({"error": "لا توجد إشارة للإرسال"}), 400

    msg = build_message(signal)
    r   = send_telegram(token, chat_id, msg)
    if r.get("ok"):
        state["signals_sent"] += 1
        add_log("SENT", f"Manual send: {signal.get('signal')} to {chat_id}")
        return jsonify({"ok": True})
    return jsonify({"error": r.get("description", "Telegram error")}), 400

@app.route("/api/test", methods=["POST"])
def api_test():
    body  = request.get_json() or {}
    token = body.get("token", BOT_TOKEN)
    if not token:
        return jsonify({"error": "Token مفقود"}), 400
    r = req.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10).json()
    if r.get("ok"):
        return jsonify({"ok": True, "username": r["result"]["username"]})
    return jsonify({"error": r.get("description", "Invalid token")}), 400

@app.route("/api/status")
def api_status():
    return jsonify({
        "price":       state["last_price"],
        "bull_score":  state["bull_score"],
        "bear_score":  state["bear_score"],
        "rsi":         state["rsi"],
        "adx":         state["adx"],
        "trend_up":    state["trend_up"],
        "htf_bull":    state["htf_bull"],
        "is_whale":    state["is_whale"],
        "last_scan":   state["last_scan"],
        "scan_count":  state["scan_count"],
        "signals_sent":state["signals_sent"],
        "auto_scan":   state["auto_scan"],
        "log":         state["log"][-20:],
    })

@app.route("/api/auto", methods=["POST"])
def api_auto():
    body = request.get_json() or {}
    state["auto_scan"] = bool(body.get("enabled", False))
    if state["auto_scan"]:
        token = body.get("token", ""); chat = body.get("chat_id", "")
        if token: os.environ["BOT_TOKEN"] = token
        if chat:  os.environ["CHAT_ID"]   = chat
        global BOT_TOKEN, CHAT_ID
        BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
        CHAT_ID   = os.environ.get("CHAT_ID",   "")
    add_log("AUTO", f"Auto scan {'enabled' if state['auto_scan'] else 'disabled'}")
    return jsonify({"ok": True, "auto_scan": state["auto_scan"]})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
