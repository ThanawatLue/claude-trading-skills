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
| **1. GROREIT.BK** | ฿9.60 | **700** หุ้น | ฿6,720.00 | ฿9.38 (-2.3%) | ฿10.04 (Swing Target) | RSI: 71.0 | Vol: 4.4x | Swing Score: 72.5 |
| **2. VIH.BK** | ฿9.15 | **700** หุ้น | ฿6,405.00 | ฿8.87 (-3.1%) | ฿9.71 (Swing Target) | RSI: 67.4 | Vol: 9.8x | Swing Score: 71.9 |
| **3. TIDLOR.BK** | ฿19.20 | **300** หุ้น | ฿5,760.00 | ฿18.24 (-5.0%) | ฿21.12 (2.0R) | CANSLIM Score: 67.8 | 52w Dist: -14.7% |
| **4. GULF.BK** | ฿63.00 | **100** หุ้น | ฿6,300.00 | ฿59.85 (-5.0%) | ฿69.30 (2.0R) | CANSLIM Score: 67.5 | 52w Dist: -8.0% |

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
# Order Template 1: GROREIT.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_GROREIT.yaml
action: buy
symbol: "GROREIT.BK"
shares: 700
entry_price: 9.60
stop_price: 9.38
target_price: 10.04
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```

```yaml
# Order Template 2: VIH.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_VIH.yaml
action: buy
symbol: "VIH.BK"
shares: 700
entry_price: 9.15
stop_price: 8.87
target_price: 9.71
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```

```yaml
# Order Template 3: TIDLOR.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_TIDLOR.yaml
action: buy
symbol: "TIDLOR.BK"
shares: 300
entry_price: 19.20
stop_price: 18.24
target_price: 21.12
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```

```yaml
# Order Template 4: GULF.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_GULF.yaml
action: buy
symbol: "GULF.BK"
shares: 100
entry_price: 63.00
stop_price: 59.85
target_price: 69.30
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```
