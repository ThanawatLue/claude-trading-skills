# 🎯 Jules AI Fund (TH): Daily Mission & Research Briefing
**วันที่:** 2026-10-19 | **สถานะพอร์ต:** ว่าง 4/4 ไม้ | **เงินทุนเริ่มต้น:** ฿30,000.00 THB

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
| **1. CNT.BK** | ฿3.06 | **2,200** หุ้น | ฿6,732.00 | ฿2.96 (-3.3%) | ฿3.20 (Swing Target) | RSI: 43.6 | Vol: 2.3x | Swing Score: 92.0 |
| **2. HANA.BK** | ฿50.25 | **100** หุ้น | ฿5,025.00 | ฿48.50 (-3.5%) | ฿52.50 (Swing Target) | RSI: 50.2 | Vol: 1.0x | Swing Score: 73.3 |
| **3. TASCO.BK** | ฿17.80 | **300** หุ้น | ฿5,340.00 | ฿17.20 (-3.4%) | ฿18.40 (Swing Target) | RSI: 64.9 | Vol: 1.9x | Swing Score: 70.3 |
| **4. AMATA.BK** | ฿32.25 | **200** หุ้น | ฿6,450.00 | ฿30.75 (-4.7%) | ฿34.25 (Swing Target) | RSI: 51.9 | Vol: 1.5x | Swing Score: 68.7 |

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
# Order Template 1: CNT.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_CNT.yaml
action: buy
symbol: "CNT.BK"
market: "TH"
shares: 2200
entry_price: 3.06
stop_price: 2.96
target_price: 3.20
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: Scale-out 50% ที่ T1 (1.5R), ขยับ Stop บังทุน, ปล่อยรันเนอร์ไป T2 (2.5R)"
```

```yaml
# Order Template 2: HANA.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_HANA.yaml
action: buy
symbol: "HANA.BK"
market: "TH"
shares: 100
entry_price: 50.25
stop_price: 48.50
target_price: 52.50
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: Scale-out 50% ที่ T1 (1.5R), ขยับ Stop บังทุน, ปล่อยรันเนอร์ไป T2 (2.5R)"
```

```yaml
# Order Template 3: TASCO.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_TASCO.yaml
action: buy
symbol: "TASCO.BK"
market: "TH"
shares: 300
entry_price: 17.80
stop_price: 17.20
target_price: 18.40
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: Scale-out 50% ที่ T1 (1.5R), ขยับ Stop บังทุน, ปล่อยรันเนอร์ไป T2 (2.5R)"
```

```yaml
# Order Template 4: AMATA.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_AMATA.yaml
action: buy
symbol: "AMATA.BK"
market: "TH"
shares: 200
entry_price: 32.25
stop_price: 30.75
target_price: 34.25
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: Scale-out 50% ที่ T1 (1.5R), ขยับ Stop บังทุน, ปล่อยรันเนอร์ไป T2 (2.5R)"
```
