# 🎯 Jules AI Fund: Daily Mission & Research Briefing
**วันที่:** 2026-10-02 | **สถานะพอร์ต:** ว่าง 3/4 ไม้ | **เงินทุนเริ่มต้น:** ฿30,000.00 THB

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
| **1. CENTEL.BK** | ฿44.00 | **100** หุ้น | ฿4,400.00 | ฿41.75 (-5.1%) | ฿48.50 (2.0R) | CANSLIM Score: 71.6 | 52w Dist: -3.3% |
| **2. PTTGC.BK** | ฿48.50 | **100** หุ้น | ฿4,850.00 | ฿46.00 (-5.2%) | ฿53.50 (2.0R) | CANSLIM Score: 63.5 | 52w Dist: -4.9% |
| **3. KCE.BK** | ฿67.00 | **100** หุ้น | ฿6,700.00 | ฿63.50 (-5.2%) | ฿74.00 (2.0R) | CANSLIM Score: 62.0 | 52w Dist: -3.6% |
| **4. PTT.BK** | ฿42.75 | **100** หุ้น | ฿4,275.00 | ฿40.50 (-5.3%) | ฿47.25 (2.0R) | CANSLIM Score: 61.9 | 52w Dist: -2.3% |

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
entry_price: 44.00
stop_price: 41.75
target_price: 48.50
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```

```yaml
# Order Template 2: PTTGC.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_PTTGC.yaml
action: buy
symbol: "PTTGC.BK"
shares: 100
entry_price: 48.50
stop_price: 46.00
target_price: 53.50
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```

```yaml
# Order Template 3: KCE.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_KCE.yaml
action: buy
symbol: "KCE.BK"
shares: 100
entry_price: 67.00
stop_price: 63.50
target_price: 74.00
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```

```yaml
# Order Template 4: PTT.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_PTT.yaml
action: buy
symbol: "PTT.BK"
shares: 100
entry_price: 42.75
stop_price: 40.50
target_price: 47.25
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
```
