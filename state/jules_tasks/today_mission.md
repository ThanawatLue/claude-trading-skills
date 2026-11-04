# 🎯 Jules AI Fund (TH): Daily Mission & Research Briefing
**วันที่:** 2026-11-04 | **สถานะพอร์ต:** ว่าง 3/4 ไม้ | **เงินทุนเริ่มต้น:** ฿30,000.00 THB

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
| **1. RCL.BK** | ฿47.00 | **100** หุ้น | ฿4,700.00 | ฿45.50 (-3.2%) | ฿49.75 (Swing Target) | RSI: 49.5 | Vol: 1.8x | Swing Score: 85.7 |
| **2. SMT.BK** | ฿6.85 | **1,000** หุ้น | ฿6,850.00 | ฿6.60 (-3.6%) | ฿7.25 (Swing Target) | RSI: 48.1 | Vol: 1.8x | Swing Score: 84.3 |
| **3. APH** | ฿79.84 | **100** หุ้น | ฿7,984.00 | ฿75.75 (-5.1%) | ฿88.00 (2.0R) | CANSLIM Score: 60.5 | 52w Dist: -11.2% |
| **4. IRPC.BK** | ฿2.88 | **2,400** หุ้น | ฿6,912.00 | ฿2.72 (-5.6%) | ฿3.20 (2.0R) | High Volume: 92,247,300 shares @ ฿2.88 |

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
# Order Template 1: RCL.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_RCL.yaml
action: buy
symbol: "RCL.BK"
market: "TH"
shares: 100
entry_price: 47.00
stop_price: 45.50
target_price: 49.75
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: Scale-out 50% ที่ T1 (1.5R), ขยับ Stop บังทุน, ปล่อยรันเนอร์ไป T2 (2.5R)"
```

```yaml
# Order Template 2: SMT.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_SMT.yaml
action: buy
symbol: "SMT.BK"
market: "TH"
shares: 1000
entry_price: 6.85
stop_price: 6.60
target_price: 7.25
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: Scale-out 50% ที่ T1 (1.5R), ขยับ Stop บังทุน, ปล่อยรันเนอร์ไป T2 (2.5R)"
```

```yaml
# Order Template 3: APH
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_APH.yaml
action: buy
symbol: "APH"
market: "TH"
shares: 100
entry_price: 79.84
stop_price: 75.75
target_price: 88.00
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: Scale-out 50% ที่ T1 (1.5R), ขยับ Stop บังทุน, ปล่อยรันเนอร์ไป T2 (2.5R)"
```

```yaml
# Order Template 4: IRPC.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_IRPC.yaml
action: buy
symbol: "IRPC.BK"
market: "TH"
shares: 2400
entry_price: 2.88
stop_price: 2.72
target_price: 3.20
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: Scale-out 50% ที่ T1 (1.5R), ขยับ Stop บังทุน, ปล่อยรันเนอร์ไป T2 (2.5R)"
```
