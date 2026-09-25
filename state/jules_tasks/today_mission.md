# 🎯 Jules AI Fund: Daily Mission & Research Briefing
**วันที่:** 2026-09-25 | **สถานะพอร์ต:** ว่าง 4/4 ไม้ | **เงินทุนเริ่มต้น:** ฿30,000.00 THB

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
| **1. CENTEL.BK** | ฿43.75 | **100** หุ้น | ฿4,375.00 | ฿41.50 (-5.1%) | ฿48.25 (2.0R) | CANSLIM Score: 71.6 | 52w Dist: -3.8% |
| **2. TASCO.BK** | ฿16.90 | **400** หุ้น | ฿6,760.00 | ฿16.50 (-2.4%) | ฿17.60 (Swing Target) | RSI: 51.2 | Vol: 0.9x | Swing Score: 70.2 |
| **3. TEGH.BK** | ฿3.30 | **2,100** หุ้น | ฿6,930.00 | ฿3.16 (-4.2%) | ฿3.56 (Swing Target) | RSI: 58.0 | Vol: 3.3x | Swing Score: 67.7 |
| **4. PTT.BK** | ฿43.00 | **100** หุ้น | ฿4,300.00 | ฿42.00 (-2.3%) | ฿44.75 (Swing Target) | RSI: 70.3 | Vol: 2.1x | Swing Score: 66.9 |

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
# Order Template 1: CENTEL.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_CENTEL.yaml
action: buy
symbol: "CENTEL.BK"
shares: 100
entry_price: 43.75
stop_price: 41.50
target_price: 48.25
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```

```yaml
# Order Template 2: TASCO.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_TASCO.yaml
action: buy
symbol: "TASCO.BK"
shares: 400
entry_price: 16.90
stop_price: 16.50
target_price: 17.60
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```

```yaml
# Order Template 3: TEGH.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_TEGH.yaml
action: buy
symbol: "TEGH.BK"
shares: 2100
entry_price: 3.30
stop_price: 3.16
target_price: 3.56
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```

```yaml
# Order Template 4: PTT.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_PTT.yaml
action: buy
symbol: "PTT.BK"
shares: 100
entry_price: 43.00
stop_price: 42.00
target_price: 44.75
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```
