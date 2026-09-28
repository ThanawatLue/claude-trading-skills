# 🎯 Jules AI Fund: Daily Mission & Research Briefing
**วันที่:** 2026-09-28 | **สถานะพอร์ต:** ว่าง 4/4 ไม้ | **เงินทุนเริ่มต้น:** ฿30,000.00 THB

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
| **1. III.BK** | ฿4.98 | **1,400** หุ้น | ฿6,972.00 | ฿4.82 (-3.2%) | ฿5.25 (Swing Target) | RSI: 49.7 | Vol: 1.2x | Swing Score: 74.6 |
| **2. MDX.BK** | ฿3.72 | **1,800** หุ้น | ฿6,696.00 | ฿3.58 (-3.8%) | ฿4.00 (Swing Target) | RSI: 65.1 | Vol: 8.7x | Swing Score: 70.9 |
| **3. GUNKUL.BK** | ฿5.30 | **1,300** หุ้น | ฿6,890.00 | ฿5.00 (-5.7%) | ฿5.80 (Swing Target) | RSI: 58.2 | Vol: 2.5x | Swing Score: 69.8 |
| **4. BANPU.BK** | ฿14.60 | **400** หุ้น | ฿5,840.00 | ฿13.80 (-5.5%) | ฿16.00 (Swing Target) | RSI: 40.6 | Vol: 1.1x | Swing Score: 68.6 |

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
# Order Template 1: III.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_III.yaml
action: buy
symbol: "III.BK"
shares: 1400
entry_price: 4.98
stop_price: 4.82
target_price: 5.25
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```

```yaml
# Order Template 2: MDX.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_MDX.yaml
action: buy
symbol: "MDX.BK"
shares: 1800
entry_price: 3.72
stop_price: 3.58
target_price: 4.00
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```

```yaml
# Order Template 3: GUNKUL.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_GUNKUL.yaml
action: buy
symbol: "GUNKUL.BK"
shares: 1300
entry_price: 5.30
stop_price: 5.00
target_price: 5.80
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```

```yaml
# Order Template 4: BANPU.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_BANPU.yaml
action: buy
symbol: "BANPU.BK"
shares: 400
entry_price: 14.60
stop_price: 13.80
target_price: 16.00
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```
