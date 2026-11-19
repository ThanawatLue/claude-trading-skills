# 🎯 Jules AI Fund (TH): Daily Mission & Research Briefing
**วันที่:** 2026-11-19 | **สถานะพอร์ต:** ว่าง 4/4 ไม้ | **เงินทุนเริ่มต้น:** ฿30,000.00 THB

---

## 🧬 Trader DNA Memory (Gen 4)
Jules ต้องใช้กฎที่เรียนรู้มาในอดีตมาช่วยตัดสินใจเลือกลงทุน:
- 📜 Always verify positive Q2/Q3 net profit growth before entering.
- 📜 Avoid stocks trading within 5 days of XD dividend record date.
- 📜 Enforce minimum stop width floor >= 4.5% to eliminate commission drag and noise whipouts.
- 📜 Two-Tier Scale-Out Engine: Take 50% profit at T1 (1.5R) and move stop to Breakeven (+0.05R buffer).
- 📜 Runner Trail to T2: Let remaining 50% ride to T2 (2.5R) with trailing ratchet active after 2.0R (lock 1.0R).
- 📜 Velocity Stall: Auto-exit stagnant trades after 4 days if peak MFE < 0.3R.
- 🛡️ **Two-Tier Scale-Out Engine:** แบ่งขายทำกำไร 50% ที่เป้า T1 (+1.5R) และเลื่อน Stop Loss ขึ้นมาที่ทุน (Breakeven +0.05R buffer) ทันที เพื่อล็อกกำไรและตัดความเสี่ยง!
- 🏃 **Runner Trail to T2:** ปล่อย 50% ที่เหลือวิ่งไปเป้า T2 (+2.5R) โดยเริ่ม Ratchet ปกป้องกำไรเมื่อถึง +2.0R (ล็อก +1.0R)
- ⏱️ **Velocity Stall Exit:** หากถือครบ 4 วันทำการแล้วราคาไม่ไปไหน (MFE < 0.3R) ระบบจะคัดทิ้งทันทีเพื่อรักษาความคุ้มค่าของเงินทุน
- 🎯 **Resistance-Aware Exits:** หากมีแนวต้านยอดเดิมขวางอยู่ก่อนเป้าหมาย ให้ตั้งเป้าขายทำกำไรที่แนวต้านร่วมกับเจ้ามือทันที

### ⚠️ ข้อผิดพลาดในอดีตที่ห้ามทำซ้ำ:
- ⚠️ Do NOT use premature breakeven ratchet at +0.5R; 40%+ of winning runners retest entry before launching.

---

## 🔍 รายชื่อหุ้นเป้าหมายวันนี้ (Top Scouted Candidates)
ระบบ VM Scout คัดกรองหุ้นสวิงโมเมนตัมและงบการเงินมาให้พิจารณา 6 ตัว:

| Ticker | ราคาล่าสุด | จำนวนซื้อแนะนำ | วงเงินประมาณ | จุด Stop Loss | เป้าทำกำไร (Resistance-Aware) | สรุปประเด็นเด่น |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **1. CENTEL.BK** | ฿44.70 | **100** หุ้น | ฿4,470.00 | ฿42.25 (-5.5%) | ฿49.50 (2.0R) | CANSLIM Score: 73.8 | 52w Dist: -5.9% |
| **2. BEM.BK** | ฿6.54 | **1,000** หุ้น | ฿6,540.00 | ฿6.30 (-3.7%) | ฿6.90 (Swing Target) | RSI: 62.6 | Vol: 3.0x | Swing Score: 63.6 |
| **3. BJC.BK** | ฿20.30 | **300** หุ้น | ฿6,090.00 | ฿19.60 (-3.4%) | ฿21.50 (Swing Target) | RSI: 61.8 | Vol: 1.6x | Swing Score: 62.4 |
| **4. TU.BK** | ฿12.90 | **500** หุ้น | ฿6,450.00 | ฿12.50 (-3.1%) | ฿13.60 (Swing Target) | RSI: 47.2 | Vol: 1.1x | Swing Score: 60.9 |
| **5. SCGD.BK** | ฿5.82 | **1,200** หุ้น | ฿6,984.00 | ฿5.65 (-2.9%) | ฿6.10 (Swing Target) | RSI: 56.8 | Vol: 2.2x | Swing Score: 60.7 |
| **6. OSP.BK** | ฿18.95 | **300** หุ้น | ฿5,685.00 | ฿18.00 (-5.0%) | ฿20.80 (2.0R) | CANSLIM Score: 60.7 | 52w Dist: -5.2% |

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
# Order Template 1: CENTEL.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_CENTEL.yaml
action: buy
symbol: "CENTEL.BK"
market: "TH"
shares: 100
entry_price: 44.70
stop_price: 42.25
target_price: 49.50
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: Scale-out 50% ที่ T1 (1.5R), ขยับ Stop บังทุน, ปล่อยรันเนอร์ไป T2 (2.5R)"
```

```yaml
# Order Template 2: BEM.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_BEM.yaml
action: buy
symbol: "BEM.BK"
market: "TH"
shares: 1000
entry_price: 6.54
stop_price: 6.30
target_price: 6.90
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: Scale-out 50% ที่ T1 (1.5R), ขยับ Stop บังทุน, ปล่อยรันเนอร์ไป T2 (2.5R)"
```

```yaml
# Order Template 3: BJC.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_BJC.yaml
action: buy
symbol: "BJC.BK"
market: "TH"
shares: 300
entry_price: 20.30
stop_price: 19.60
target_price: 21.50
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: Scale-out 50% ที่ T1 (1.5R), ขยับ Stop บังทุน, ปล่อยรันเนอร์ไป T2 (2.5R)"
```

```yaml
# Order Template 4: TU.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_TU.yaml
action: buy
symbol: "TU.BK"
market: "TH"
shares: 500
entry_price: 12.90
stop_price: 12.50
target_price: 13.60
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: Scale-out 50% ที่ T1 (1.5R), ขยับ Stop บังทุน, ปล่อยรันเนอร์ไป T2 (2.5R)"
```

```yaml
# Order Template 5: SCGD.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_SCGD.yaml
action: buy
symbol: "SCGD.BK"
market: "TH"
shares: 1200
entry_price: 5.82
stop_price: 5.65
target_price: 6.10
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: Scale-out 50% ที่ T1 (1.5R), ขยับ Stop บังทุน, ปล่อยรันเนอร์ไป T2 (2.5R)"
```

```yaml
# Order Template 6: OSP.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_OSP.yaml
action: buy
symbol: "OSP.BK"
market: "TH"
shares: 300
entry_price: 18.95
stop_price: 18.00
target_price: 20.80
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: Scale-out 50% ที่ T1 (1.5R), ขยับ Stop บังทุน, ปล่อยรันเนอร์ไป T2 (2.5R)"
```
