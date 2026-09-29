# 🎯 Jules AI Fund: Daily Mission & Research Briefing
**วันที่:** 2026-09-29 | **สถานะพอร์ต:** ว่าง 3/4 ไม้ | **เงินทุนเริ่มต้น:** ฿30,000.00 THB

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
| **1. TPRIME.BK** | ฿8.60 | **800** หุ้น | ฿6,880.00 | ฿8.45 (-1.7%) | ฿8.90 (Swing Target) | RSI: 63.0 | Vol: 2.8x | Swing Score: 83.7 |
| **2. NER.BK** | ฿4.62 | **1,500** หุ้น | ฿6,930.00 | ฿4.50 (-2.6%) | ฿4.84 (Swing Target) | RSI: 46.0 | Vol: 1.9x | Swing Score: 78.0 |
| **3. ERW.BK** | ฿3.70 | **1,800** หุ้น | ฿6,660.00 | ฿3.62 (-2.2%) | ฿3.84 (Swing Target) | RSI: 50.0 | Vol: 1.0x | Swing Score: 73.1 |
| **4. III.BK** | ฿4.92 | **1,400** หุ้น | ฿6,888.00 | ฿4.80 (-2.4%) | ฿5.10 (Swing Target) | RSI: 47.0 | Vol: 0.8x | Swing Score: 71.7 |

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
# Order Template 1: TPRIME.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_TPRIME.yaml
action: buy
symbol: "TPRIME.BK"
shares: 800
entry_price: 8.60
stop_price: 8.45
target_price: 8.90
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```

```yaml
# Order Template 2: NER.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_NER.yaml
action: buy
symbol: "NER.BK"
shares: 1500
entry_price: 4.62
stop_price: 4.50
target_price: 4.84
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```

```yaml
# Order Template 3: ERW.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_ERW.yaml
action: buy
symbol: "ERW.BK"
shares: 1800
entry_price: 3.70
stop_price: 3.62
target_price: 3.84
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```

```yaml
# Order Template 4: III.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_III.yaml
action: buy
symbol: "III.BK"
shares: 1400
entry_price: 4.92
stop_price: 4.80
target_price: 5.10
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```
