# 🎯 Jules AI Fund: Daily Mission & Research Briefing
**วันที่:** 2026-09-18 | **สถานะพอร์ต:** ว่าง 4/4 ไม้ | **เงินทุนเริ่มต้น:** ฿30,000.00 THB

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
| **1. WHAIR.BK** | ฿8.65 | **800** หุ้น | ฿6,920.00 | ฿8.30 (-4.0%) | ฿9.25 (Swing Target) | RSI: 66.5 | Vol: 3.9x | Swing Score: 83.1 |
| **2. PIS.BK** | ฿6.10 | **1,100** หุ้น | ฿6,710.00 | ฿5.90 (-3.3%) | ฿6.45 (Swing Target) | RSI: 68.1 | Vol: 2.9x | Swing Score: 82.2 |
| **3. ITC.BK** | ฿17.70 | **300** หุ้น | ฿5,310.00 | ฿17.10 (-3.4%) | ฿18.80 (Swing Target) | RSI: 60.8 | Vol: 4.0x | Swing Score: 75.5 |
| **4. COM7.BK** | ฿30.50 | **200** หุ้น | ฿6,100.00 | ฿29.00 (-4.9%) | ฿33.25 (Swing Target) | RSI: 58.7 | Vol: 2.7x | Swing Score: 70.1 |

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
# Order Template 1: WHAIR.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_WHAIR.yaml
action: buy
symbol: "WHAIR.BK"
shares: 800
entry_price: 8.65
stop_price: 8.30
target_price: 9.25
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```

```yaml
# Order Template 2: PIS.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_PIS.yaml
action: buy
symbol: "PIS.BK"
shares: 1100
entry_price: 6.10
stop_price: 5.90
target_price: 6.45
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```

```yaml
# Order Template 3: ITC.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_ITC.yaml
action: buy
symbol: "ITC.BK"
shares: 300
entry_price: 17.70
stop_price: 17.10
target_price: 18.80
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```

```yaml
# Order Template 4: COM7.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_COM7.yaml
action: buy
symbol: "COM7.BK"
shares: 200
entry_price: 30.50
stop_price: 29.00
target_price: 33.25
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```
