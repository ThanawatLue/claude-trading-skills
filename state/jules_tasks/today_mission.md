# 🎯 Jules AI Fund (TH): Daily Mission & Research Briefing
**วันที่:** 2026-10-08 | **สถานะพอร์ต:** ว่าง 4/4 ไม้ | **เงินทุนเริ่มต้น:** ฿30,000.00 THB

---

## 🧬 Trader DNA Memory (Gen 4)
Jules ต้องใช้กฎที่เรียนรู้มาในอดีตมาช่วยตัดสินใจเลือกลงทุน:
- 📜 Always verify positive Q2/Q3 net profit growth before entering.
- 📜 Avoid stocks trading within 5 days of XD dividend record date.
- 📜 Enforce minimum stop width floor >= 4.5% to eliminate commission drag and noise whipouts.
- 📜 Two-Tier Scale-Out Engine: Take 50% profit at T1 (1.5R) and move stop to Breakeven (+0.05R buffer).
- 📜 Runner Trail to T2: Let remaining 50% ride to T2 (2.5R) with trailing ratchet active after 2.0R (lock 1.0R).
- 📜 Velocity Stall: Auto-exit stagnant trades after 4 days if peak MFE < 0.3R.
- 📜 If price stalls without momentum within 3 days, exit to preserve capital.
- 🛡️ **Two-Tier Scale-Out Engine:** แบ่งขายทำกำไร 50% ที่เป้า T1 (+1.5R) และเลื่อน Stop Loss ขึ้นมาที่ทุน (Breakeven +0.05R buffer) ทันที เพื่อล็อกกำไรและตัดความเสี่ยง!
- 🏃 **Runner Trail to T2:** ปล่อย 50% ที่เหลือวิ่งไปเป้า T2 (+2.5R) โดยเริ่ม Ratchet ปกป้องกำไรเมื่อถึง +2.0R (ล็อก +1.0R)
- ⏱️ **Velocity Stall Exit:** หากถือครบ 4 วันทำการแล้วราคาไม่ไปไหน (MFE < 0.3R) ระบบจะคัดทิ้งทันทีเพื่อรักษาความคุ้มค่าของเงินทุน
- 🎯 **Resistance-Aware Exits:** หากมีแนวต้านยอดเดิมขวางอยู่ก่อนเป้าหมาย ให้ตั้งเป้าขายทำกำไรที่แนวต้านร่วมกับเจ้ามือทันที

### ⚠️ ข้อผิดพลาดในอดีตที่ห้ามทำซ้ำ:
- ⚠️ Do NOT use premature breakeven ratchet at +0.5R; 40%+ of winning runners retest entry before launching.
- ⚠️ Holding losing positions too long. Cut stalled trades within 3 days.

---

## 🔍 รายชื่อหุ้นเป้าหมายวันนี้ (Top Scouted Candidates)
ระบบ VM Scout คัดกรองหุ้นสวิงโมเมนตัมและงบการเงินมาให้พิจารณา 4 ตัว:

| Ticker | ราคาล่าสุด | จำนวนซื้อแนะนำ | วงเงินประมาณ | จุด Stop Loss | เป้าทำกำไร (Resistance-Aware) | สรุปประเด็นเด่น |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **1. EPG.BK** | ฿6.60 | **1,000** หุ้น | ฿6,600.00 | ฿6.25 (-5.3%) | ฿7.20 (Swing Target) | RSI: 64.8 | Vol: 2.8x | Swing Score: 80.1 |
| **2. SICT.BK** | ฿3.56 | **1,900** หุ้น | ฿6,764.00 | ฿3.36 (-5.6%) | ฿3.96 (Swing Target) | RSI: 70.7 | Vol: 5.0x | Swing Score: 72.0 |
| **3. WHA.BK** | ฿4.96 | **1,400** หุ้น | ฿6,944.00 | ฿4.78 (-3.6%) | ฿5.25 (Swing Target) | RSI: 62.0 | Vol: 3.3x | Swing Score: 63.1 |
| **4. CNT.BK** | ฿3.30 | **2,100** หุ้น | ฿6,930.00 | ฿3.14 (-4.8%) | ฿3.60 (Swing Target) | RSI: 57.3 | Vol: 2.3x | Swing Score: 61.8 |

---

## 📋 ภารกิจสำหรับ Jules (Action Required)
1. **คัดกรองปัจจัยพื้นฐาน (Fundamental & Business Check):**
   - ตรวจสอบโมเดลธุรกิจ: กำไรโตจริง หรือแค่ภาพลวงตา?
   - ค้นหาข่าวด่วนล่าสุดจาก Google Search: มีข่าวลบ / XD / Dilution หรือไม่?
2. **ตัดสินใจ (Approve or Veto):**
   - หากหุ้นตัวใดผ่านเกณฑ์ และเข้าตา Jules ที่สุด **เลือก 1 ตัว**
   - บันทึกไฟล์ Order ตาม Template ด้านล่างลงในโฟลเดอร์ `state/jules_orders/`
   - เมื่อ Push ขึ้น GitHub แล้ว ระบบบน VM จะเข้าซื้อให้อัตโนมัติ!

---

## 📝 คำสั่งซื้อสำเร็จรูป (Order Templates)
```yaml
# Order Template 1: EPG.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_EPG.yaml
action: buy
symbol: "EPG.BK"
market: "TH"
shares: 1000
entry_price: 6.60
stop_price: 6.25
target_price: 7.20
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: Scale-out 50% ที่ T1 (1.5R), ขยับ Stop บังทุน, ปล่อยรันเนอร์ไป T2 (2.5R)"
```

```yaml
# Order Template 2: SICT.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_SICT.yaml
action: buy
symbol: "SICT.BK"
market: "TH"
shares: 1900
entry_price: 3.56
stop_price: 3.36
target_price: 3.96
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: Scale-out 50% ที่ T1 (1.5R), ขยับ Stop บังทุน, ปล่อยรันเนอร์ไป T2 (2.5R)"
```

```yaml
# Order Template 3: WHA.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_WHA.yaml
action: buy
symbol: "WHA.BK"
market: "TH"
shares: 1400
entry_price: 4.96
stop_price: 4.78
target_price: 5.25
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: Scale-out 50% ที่ T1 (1.5R), ขยับ Stop บังทุน, ปล่อยรันเนอร์ไป T2 (2.5R)"
```

```yaml
# Order Template 4: CNT.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_CNT.yaml
action: buy
symbol: "CNT.BK"
market: "TH"
shares: 2100
entry_price: 3.30
stop_price: 3.14
target_price: 3.60
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: Scale-out 50% ที่ T1 (1.5R), ขยับ Stop บังทุน, ปล่อยรันเนอร์ไป T2 (2.5R)"
```
