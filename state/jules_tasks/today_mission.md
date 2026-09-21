# 🎯 Jules AI Fund: Daily Mission & Research Briefing
**วันที่:** 2026-09-21 | **สถานะพอร์ต:** ว่าง 4/4 ไม้ | **เงินทุนเริ่มต้น:** ฿30,000.00 THB

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
| **1. TU.BK** | ฿12.70 | **500** หุ้น | ฿6,350.00 | ฿12.10 (-4.7%) | ฿13.70 (Swing Target) | RSI: 48.4 | Vol: 1.4x | Swing Score: 72.7 |
| **2. CENTEL.BK** | ฿43.25 | **100** หุ้น | ฿4,325.00 | ฿41.00 (-5.2%) | ฿47.75 (2.0R) | CANSLIM Score: 71.6 | 52w Dist: -3.4% |
| **3. AJ.BK** | ฿3.50 | **2,000** หุ้น | ฿7,000.00 | ฿3.30 (-5.7%) | ฿3.86 (Swing Target) | RSI: 49.6 | Vol: 1.3x | Swing Score: 71.5 |
| **4. FTREIT.BK** | ฿13.50 | **500** หุ้น | ฿6,750.00 | ฿12.90 (-4.4%) | ฿14.60 (Swing Target) | RSI: 64.9 | Vol: 1.9x | Swing Score: 70.0 |

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
# Order Template 1: TU.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_TU.yaml
action: buy
symbol: "TU.BK"
shares: 500
entry_price: 12.70
stop_price: 12.10
target_price: 13.70
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```

```yaml
# Order Template 2: CENTEL.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_CENTEL.yaml
action: buy
symbol: "CENTEL.BK"
shares: 100
entry_price: 43.25
stop_price: 41.00
target_price: 47.75
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```

```yaml
# Order Template 3: AJ.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_AJ.yaml
action: buy
symbol: "AJ.BK"
shares: 2000
entry_price: 3.50
stop_price: 3.30
target_price: 3.86
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```

```yaml
# Order Template 4: FTREIT.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_FTREIT.yaml
action: buy
symbol: "FTREIT.BK"
shares: 500
entry_price: 13.50
stop_price: 12.90
target_price: 14.60
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```
