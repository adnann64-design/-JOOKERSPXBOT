# 🃏 JOKER ELITE - SPX Options Signal Bot

## 📊 نظام إشارات تداول SPX Options احترافي

بوت متقدم يحلل مؤشر S&P 500 باستخدام 12 مؤشراً تقنياً ويرسل إشارات تداول الأوبشن (CALL/PUT) مباشرة إلى تيليجرام مع تحديد السترايك المثالي وأهداف الربح ووقف الخسارة.

---

## ✨ المميزات

### 🎯 تحليل متقدم
- **12 مؤشراً تقنياً**: RSI, ADX, SuperTrend, EMA, Volume Analysis
- **SMC Analysis**: Break of Structure, Fair Value Gaps, Liquidity Sweeps
- **Support & Resistance**: كشف تلقائي للمستويات الحرجة
- **نظام تسجيل نقاط**: 17 نقطة تقاطع لتحديد قوة الإشارة

### 📈 إشارات دقيقة
- تحديد نوع العقد (CALL/PUT)
- السترايك الأمثل
- تاريخ انتهاء العقد (0DTE / Weekly)
- 3 أهداف ربح (1R, 2R, 3R)
- وقف خسارة محسوب

### ⚡ الإرسال التلقائي
- **Auto Scan**: فحص السوق كل 5 دقائق
- إرسال تلقائي لتيليجرام
- يعمل فقط خلال ساعات التداول (9:30-16:00 ET)
- لا يرسل نفس الإشارة مرتين

### 🎨 واجهة احترافية
- تصميم Cyberpunk متقدم
- Dashboard مباشر للسوق
- معاينة الرسائل قبل الإرسال
- سجل مباشر للعمليات

---

## 🚀 النشر السريع

### المتطلبات
1. **Telegram Bot Token** من [@BotFather](https://t.me/BotFather)
2. **Chat ID** للقناة/المجموعة (استخدم [@userinfobot](https://t.me/userinfobot))
3. حساب على [Render.com](https://render.com) (مجاني)

### خطوات النشر

#### 1️⃣ رفع المشروع على GitHub
```bash
git clone https://github.com/adnann64-design/-JOOKERSPXBOT.git
cd -JOOKERSPXBOT
```

#### 2️⃣ النشر على Render.com
1. اذهب إلى [Render.com](https://render.com)
2. سجل دخول بحساب GitHub
3. اضغط **"New Web Service"**
4. اختر repository: `-JOOKERSPXBOT`
5. Render سيكتشف الإعدادات تلقائياً من `render.yaml`

#### 3️⃣ ضبط متغيرات البيئة
في لوحة Render، اذهب إلى **Environment** وأضف:
```
BOT_TOKEN  =  توكن_البوت_من_BotFather
CHAT_ID    =  معرف_القناة_أو_المجموعة
```

#### 4️⃣ النشر
- اضغط **Deploy**
- انتظر 2-3 دقائق
- ستحصل على رابط مثل: `https://jookerspxbot.onrender.com`

---

## 🎮 طريقة الاستخدام

### 1. فتح الموقع
افتح الرابط الخاص بك في المتصفح

### 2. إدخال البيانات
- **Bot Token**: توكن البوت من BotFather
- **Chat ID**: معرف قناتك
- **Sensitivity**: حدد مستوى الدقة (7+ موصى به)

### 3. اختبار الاتصال
اضغط **"اختبار التوكن"** للتأكد من صحة البيانات

### 4. الحصول على إشارة
- اضغط **"تحليل الآن"** للحصول على إشارة فورية
- اضغط **"إرسال لتيليجرام"** لإرسال الإشارة

### 5. التشغيل التلقائي
- فعّل **"Auto Scan"**
- البوت سيفحص السوق كل 5 دقائق تلقائياً
- يرسل الإشارات مباشرة عند توفرها

---

## 📱 مثال على الإشارة

```
🟢🟢🟢 إشارة جديدة — SPX Options 🟢🟢🟢

📈 CALL شراء
🕐 2026-03-01 14:30 ET
💰 SPX الحالي: 5,850.00

━━━━━━━━━━━━━━━━━━━━━━━
📋 تفاصيل العقد:
• النوع:      CALL
• السترايك:   5,855
• الانتهاء:   Daily (0DTE)

━━━━━━━━━━━━━━━━━━━━━━━
🎯 الأهداف والوقف:
✅ TP1 (1R):  5,862.50
✅ TP2 (2R):  5,875.00
✅ TP3 (3R):  5,887.50
🛑 SL:        5,837.50
📐 المخاطرة:  12.50 نقطة

━━━━━━━━━━━━━━━━━━━━━━━
📊 المؤشرات:
• Score: 11/17 — ✅ قوي
• RSI: 48.5  |  ADX: 29.3

⚡ المحفزات: BOS | Whale Volume | Near Support

━━━━━━━━━━━━━━━━━━━━━━━
⚠️ لا تخاطر بأكثر من 2% من الحساب
🤖 JOKER ULTIMATE ELITE
```

---

## 🛠️ التقنيات المستخدمة

- **Backend**: Flask (Python)
- **Data**: yFinance, pandas, numpy
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Hosting**: Render.com
- **API**: Telegram Bot API

---

## 📊 المؤشرات التقنية

1. **RSI** (14) - مؤشر القوة النسبية
2. **ADX** (14) - قوة الاتجاه
3. **SuperTrend** (3, 10)
4. **EMA** (9, 21, 50, 200)
5. **Volume Analysis** - Whale Detection
6. **ATR** (14) - متوسط المدى الحقيقي
7. **Break of Structure (BOS)**
8. **Change of Character (CHOCH)**
9. **Fair Value Gaps (FVG)**
10. **Liquidity Sweeps**
11. **Support/Resistance Levels**
12. **RSI Divergence**

---

## ⚙️ الإعدادات المتقدمة

### UptimeRobot (لإبقاء الموقع يقظاً)
الخطة المجانية على Render تنام بعد 15 دقيقة من عدم الاستخدام.

**الحل**:
1. سجّل في [UptimeRobot.com](https://uptimerobot.com)
2. أضف Monitor من نوع HTTP(S)
3. ضع رابط موقعك
4. اضبط الفاصل الزمني على 5 دقائق

### ضبط مستوى الحساسية
- **Aggressive (4+ نقاط)**: إشارات أكثر، دقة أقل
- **High Accuracy (7+ نقاط)**: متوازن - موصى به
- **Ultra Precision (10+ نقاط)**: إشارات أقل، دقة أعلى

---

## ⚠️ تحذيرات مهمة

1. **للأغراض التعليمية**: هذا البوت للتعلم والتحليل فقط
2. **تداول الأوبشن عالي المخاطرة**: لا تخاطر بأكثر من 2% من رأس المال
3. **ليس نصيحة مالية**: قم بأبحاثك الخاصة
4. **استخدم حساب تجريبي أولاً**: اختبر الإشارات قبل التداول الحقيقي

---

## 📞 الدعم

للمشاكل التقنية، افتح [Issue على GitHub](https://github.com/adnann64-design/-JOOKERSPXBOT/issues)

---

## 📄 الترخيص

هذا المشروع مفتوح المصدر للأغراض التعليمية.

---

## 🎯 خارطة الطريق

- [ ] إضافة دعم للعملات الرقمية
- [ ] تطوير استراتيجيات متقدمة
- [ ] إضافة Backtesting
- [ ] تطبيق موبايل
- [ ] AI/ML للتحسين الذاتي

---

**💎 JOKER ULTIMATE ELITE - Your Professional SPX Options Companion**

⚡ Built with passion for precision trading
