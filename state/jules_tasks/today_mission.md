# 🎯 Jules AI Fund: Daily Mission & Research Briefing
**วันที่:** 2026-09-24 | **สถานะพอร์ต:** ว่าง 4/4 ไม้ | **เงินทุนเริ่มต้น:** ฿30,000.00 THB

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
| **1. HTECH.BK** | ฿5.05 | **1,300** หุ้น | ฿6,565.00 | ฿4.78 (-5.3%) | ฿5.55 (Swing Target) | RSI: 65.0 | Vol: 3.5x | Swing Score: 84.9 |
| **2. SMT.BK** | ฿6.35 | **1,100** หุ้น | ฿6,985.00 | ฿5.85 (-7.9%) | ฿7.30 (Swing Target) | RSI: 65.7 | Vol: 2.8x | Swing Score: 83.0 |
| **3. PYLON.BK** | ฿3.96 | **1,700** หุ้น | ฿6,732.00 | ฿3.88 (-2.0%) | ฿4.12 (Swing Target) | RSI: 67.6 | Vol: 2.7x | Swing Score: 76.9 |
| **4. SPCG.BK** | ฿11.60 | **600** หุ้น | ฿6,960.00 | ฿10.70 (-7.8%) | ฿13.20 (Swing Target) | RSI: 62.5 | Vol: 2.7x | Swing Score: 74.1 |

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
# Order Template 1: HTECH.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_HTECH.yaml
action: buy
symbol: "HTECH.BK"
shares: 1300
entry_price: 5.05
stop_price: 4.78
target_price: 5.55
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```

```yaml
# Order Template 2: SMT.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_SMT.yaml
action: buy
symbol: "SMT.BK"
shares: 1100
entry_price: 6.35
stop_price: 5.85
target_price: 7.30
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```

```yaml
# Order Template 3: PYLON.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_PYLON.yaml
action: buy
symbol: "PYLON.BK"
shares: 1700
entry_price: 3.96
stop_price: 3.88
target_price: 4.12
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```

```yaml
# Order Template 4: SPCG.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_SPCG.yaml
action: buy
symbol: "SPCG.BK"
shares: 600
entry_price: 11.60
stop_price: 10.70
target_price: 13.20
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```
