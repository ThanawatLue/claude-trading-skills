# 🎯 Jules AI Fund: Daily Mission & Research Briefing
**วันที่:** 2026-09-15 | **สถานะพอร์ต:** ว่าง 4/4 ไม้ | **เงินทุนเริ่มต้น:** ฿30,000.00 THB

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
| **1. TIDLOR.BK** | ฿19.20 | **300** หุ้น | ฿5,760.00 | ฿18.05 (-6%) | ฿21.73 (+2.2R) | CANSLIM Score: 67.8 | 52w Dist: -14.7% |
| **2. GULF.BK** | ฿63.00 | **100** หุ้น | ฿6,300.00 | ฿59.22 (-6%) | ฿71.32 (+2.2R) | CANSLIM Score: 67.5 | 52w Dist: -8.0% |
| **3. AMATA.BK** | ฿26.50 | **200** หุ้น | ฿5,300.00 | ฿24.91 (-6%) | ฿30.00 (+2.2R) | CANSLIM Score: 63.8 | 52w Dist: -5.4% |
| **4. SINGER.BK** | ฿9.95 | **700** หุ้น | ฿6,965.00 | ฿9.35 (-6%) | ฿11.27 (+2.2R) | CANSLIM Score: 62.5 | 52w Dist: -1.5% |

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
# Order Template 1: TIDLOR.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_TIDLOR.yaml
action: buy
symbol: "TIDLOR.BK"
shares: 300
entry_price: 19.20
stop_price: 18.05
target_price: 21.73
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง]"
```

```yaml
# Order Template 2: GULF.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_GULF.yaml
action: buy
symbol: "GULF.BK"
shares: 100
entry_price: 63.00
stop_price: 59.22
target_price: 71.32
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง]"
```

```yaml
# Order Template 3: AMATA.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_AMATA.yaml
action: buy
symbol: "AMATA.BK"
shares: 200
entry_price: 26.50
stop_price: 24.91
target_price: 30.00
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง]"
```

```yaml
# Order Template 4: SINGER.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_SINGER.yaml
action: buy
symbol: "SINGER.BK"
shares: 700
entry_price: 9.95
stop_price: 9.35
target_price: 11.27
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง]"
```
