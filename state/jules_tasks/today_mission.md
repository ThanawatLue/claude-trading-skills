# 🎯 Jules AI Fund: Daily Mission & Research Briefing
**วันที่:** 2026-09-17 | **สถานะพอร์ต:** ว่าง 4/4 ไม้ | **เงินทุนเริ่มต้น:** ฿30,000.00 THB

---

## 🧬 Trader DNA Memory (Gen 2)
Jules ต้องใช้กฎที่เรียนรู้มาในอดีตมาช่วยตัดสินใจเลือกลงทุน:
- 📜 Always verify positive Q2/Q3 net profit growth before entering.
- 📜 Avoid stocks trading within 5 days of XD dividend record date.
- 📜 Cut positions early if volume contracts by more than 60% on day 1 post-entry.
- 📜 Hold winning momentum trades until 2.2R target without premature manual closure.
- 🛡️ **MFE Ratchet Protection:** หากราคาหุ้นบวกแตะ +0.5R ระบบจะเลื่อน Stop Loss ขึ้นมาที่ทุน (Breakeven) อัตโนมัติ เพื่อป้องกันไม่ให้กำไรกลายเป็นขาดทุน!
- 🎯 **Resistance-Aware Exits:** หากมีแนวต้านยอดเดิมขวางอยู่ก่อน 2.0R ให้ตั้งเป้าขายทำกำไรที่แนวต้านร่วมกับเจ้ามือทันที

### ⚠️ ข้อผิดพลาดในอดีตที่ห้ามทำซ้ำ:
- ไม่มีข้อผิดพลาดซ้ำเดิมในประวัติ

---

## 🔍 รายชื่อหุ้นเป้าหมายวันนี้ (Top Scouted Candidates)
ระบบ VM Scout คัดกรองหุ้นสวิงโมเมนตัมและงบการเงินมาให้พิจารณา 4 ตัว:

| Ticker | ราคาล่าสุด | จำนวนซื้อแนะนำ | วงเงินประมาณ | จุด Stop Loss | เป้าทำกำไร (Resistance-Aware) | สรุปประเด็นเด่น |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **1. BBGI.BK** | ฿6.50 | **1,000** หุ้น | ฿6,500.00 | ฿6.17 (-5.1%) | ฿7.15 (Swing Target) | RSI: 66.3 | Vol: 2.2x | Swing Score: 74.2 |
| **2. STECON.BK** | ฿18.80 | **300** หุ้น | ฿5,640.00 | ฿17.86 (-5.0%) | ฿20.69 (Swing Target) | RSI: 57.8 | Vol: 2.4x | Swing Score: 61.5 |
| **3. SPRC.BK** | ฿13.40 | **500** หุ้น | ฿6,700.00 | ฿12.97 (-3.2%) | ฿14.26 (Swing Target) | RSI: 60.6 | Vol: 1.5x | Swing Score: 58.9 |
| **4. III.BK** | ฿4.86 | **1,400** หุ้น | ฿6,804.00 | ฿4.75 (-2.3%) | ฿5.08 (Swing Target) | RSI: 47.1 | Vol: 1.9x | Swing Score: 84.5 |

---

## 📋 ภารกิจสำหรับ Jules (Action Required)
1. **คัดกรองปัจจัยพื้นฐาน (Fundamental & Business Check):**
   - ตรวจสอบโมเดลธุรกิจ: กำไรโตจริง หรือแค่ภาพลวงตา?
   - ค้นหาข่าวด่วนล่าสุดจาก Google Search หรือข่าวทันหุ้น: มีข่าวลบ / XD / Dilution หรือไม่?
2. **ตัดสินใจ (Approve or Veto):**
   - หากหุ้นตัวใดผ่านเกณฑ์ และเข้าตา Jules ที่สุด **เลือก 1 ตัว**
   - บันทึกไฟล์ Order ตาม Template ด้านล่างลงในโฟลเดอร์ `state/jules_orders/`
   - เมื่อ Push ขึ้น GitHub แล้ว ระบบบน VM จะเข้าซื้อให้อัตโนมัติ!

---

## 📝 คำสั่งซื้อสำเร็จรูป (Order Templates)
```yaml
# Order Template 1: BBGI.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_BBGI.yaml
action: buy
symbol: "BBGI.BK"
shares: 1000
entry_price: 6.50
stop_price: 6.17
target_price: 7.15
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```

```yaml
# Order Template 2: STECON.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_STECON.yaml
action: buy
symbol: "STECON.BK"
shares: 300
entry_price: 18.80
stop_price: 17.86
target_price: 20.69
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```

```yaml
# Order Template 3: SPRC.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_SPRC.yaml
action: buy
symbol: "SPRC.BK"
shares: 500
entry_price: 13.40
stop_price: 12.97
target_price: 14.26
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```

```yaml
# Order Template 4: III.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_III.yaml
action: buy
symbol: "III.BK"
shares: 1400
entry_price: 4.86
stop_price: 4.75
target_price: 5.08
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```
