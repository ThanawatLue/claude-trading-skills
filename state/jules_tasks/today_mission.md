# 🎯 Jules AI Fund: Daily Mission & Research Briefing
**วันที่:** 2026-09-16 | **สถานะพอร์ต:** ว่าง 3/4 ไม้ | **เงินทุนเริ่มต้น:** ฿30,000.00 THB

---

## 🧬 Trader DNA Memory (Gen 2)
Jules ต้องใช้กฎที่เรียนรู้มาในอดีตมาช่วยตัดสินใจเลือกลงทุน:
- 📜 Always verify positive Q2/Q3 net profit growth before entering.
- 📜 Avoid stocks trading within 5 days of XD dividend record date.
- 📜 Cut positions early if volume contracts by more than 60% on day 1 post-entry.
- 📜 Hold winning momentum trades until 2.2R target without premature manual closure.

### ⚠️ ข้อผิดพลาดในอดีตที่ห้ามทำซ้ำ:
- ไม่มีข้อผิดพลาดซ้ำเดิมในประวัติ

---

## 🔍 รายชื่อหุ้นเป้าหมายวันนี้ (Top Scouted Candidates)
ระบบ VM Scout คัดกรองหุ้นที่มีความผิดปกติทางวอลุ่มและงบการเงินมาให้พิจารณา 4 ตัว:

| Ticker | ราคาล่าสุด | จำนวนซื้อแนะนำ | วงเงินประมาณ | จุด Stop Loss | เป้ากำไร (2.2R) | สรุปประเด็นเด่น |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **1. CENTEL.BK** | ฿44.50 | **100** หุ้น | ฿4,450.00 | ฿41.83 (-6%) | ฿50.37 (+2.2R) | CANSLIM Score: 69.4 | 52w Dist: -0.6% |
| **2. PTTGC.BK** | ฿49.75 | **100** หุ้น | ฿4,975.00 | ฿46.77 (-6%) | ฿56.31 (+2.2R) | CANSLIM Score: 65.5 | 52w Dist: -2.5% |
| **3. KCE.BK** | ฿67.50 | **100** หุ้น | ฿6,750.00 | ฿63.45 (-6%) | ฿76.41 (+2.2R) | CANSLIM Score: 65.0 | 52w Dist: 1.1% |
| **4. IVL.BK** | ฿29.25 | **200** หุ้น | ฿5,850.00 | ฿27.49 (-6%) | ฿33.12 (+2.2R) | CANSLIM Score: 62.5 | 52w Dist: -2.5% |

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
entry_price: 44.50
stop_price: 41.83
target_price: 50.37
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง]"
```

```yaml
# Order Template 2: PTTGC.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_PTTGC.yaml
action: buy
symbol: "PTTGC.BK"
shares: 100
entry_price: 49.75
stop_price: 46.77
target_price: 56.31
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง]"
```

```yaml
# Order Template 3: KCE.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_KCE.yaml
action: buy
symbol: "KCE.BK"
shares: 100
entry_price: 67.50
stop_price: 63.45
target_price: 76.41
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง]"
```

```yaml
# Order Template 4: IVL.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_IVL.yaml
action: buy
symbol: "IVL.BK"
shares: 200
entry_price: 29.25
stop_price: 27.49
target_price: 33.12
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง]"
```
