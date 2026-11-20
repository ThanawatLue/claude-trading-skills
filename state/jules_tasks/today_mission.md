# 🎯 Jules AI Fund (TH): Daily Mission & Research Briefing
**วันที่:** 2026-11-20 | **สถานะพอร์ต:** ว่าง 4/4 ไม้ | **เงินทุนเริ่มต้น:** ฿30,000.00 THB

---

## 🧬 Trader DNA Memory (Gen 4)
Jules ต้องใช้กฎที่เรียนรู้มาในอดีตมาช่วยตัดสินใจเลือกลงทุน:
- 📜 Always verify positive Q2/Q3 net profit growth before entering.
- 📜 Avoid stocks trading within 5 days of XD dividend record date.
- 📜 Enforce minimum stop width floor >= 4.5% to eliminate commission drag and noise whipouts.
- 📜 Two-Tier Scale-Out Engine: Take 50% profit at T1 (1.5R) and move stop to Breakeven (+0.05R buffer).
- 📜 Runner Trail to T2: Let remaining 50% ride to T2 (2.5R) with trailing ratchet active after 2.0R (lock 1.0R).
- 📜 Velocity Stall: Auto-exit stagnant trades after 4 days if peak MFE < 0.3R.
- 🛡️ **Two-Tier Scale-Out Engine:** แบ่งขายทำกำไร 33% ที่เป้า T1 (+1.5R) และเลื่อน Stop Loss ขึ้นมาที่ทุน (Breakeven + 1 Tick buffer) ทันทีเพื่อล็อกกำไร (สำหรับพอร์ต 100 หุ้นในตลาดไทย ให้เลื่อน Stop บังทุนเพื่อรันทั้งไม้)
- 🏃 **Runner Trail to T2:** ปล่อย 67% ที่เหลือวิ่งไปเป้า T2 (+2.5R) โดยเริ่ม Ratchet ปกป้องกำไรเมื่อถึง +2.0R (ล็อก +1.0R)
- ⏱️ **Velocity Stall Exit:** หากถือครบ 7 วันทำการแล้วราคาไม่ไปไหน (MFE < 0.3R) ระบบจะคัดทิ้งทันทีเพื่อรักษาความคุ้มค่าของเงินทุน
- 🎯 **Resistance-Aware Exits:** หากมีแนวต้านยอดเดิมขวางอยู่ก่อนเป้าหมาย ให้ตั้งเป้าขายทำกำไรที่แนวต้านร่วมกับเจ้ามือทันที

### ⚠️ ข้อผิดพลาดในอดีตที่ห้ามทำซ้ำ:
- ⚠️ Do NOT use premature breakeven ratchet at +0.5R; 40%+ of winning runners retest entry before launching.

---

## 🔍 รายชื่อหุ้นเป้าหมายวันนี้ (Top Scouted Candidates)
ระบบ VM Scout คัดกรองหุ้นสวิงโมเมนตัมและงบการเงินมาให้พิจารณา 6 ตัว:

| Ticker | ราคาล่าสุด | จำนวนซื้อแนะนำ | วงเงินประมาณ | จุด Stop Loss | เป้าทำกำไร (Resistance-Aware) | สรุปประเด็นเด่น |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **1. PLANB.BK** | ฿7.72 | **900** หุ้น | ฿6,948.00 | ฿7.15 (-7.4%) | ฿8.80 (Swing Target) | RSI: 42.8 | Vol: 1.4x | Swing Score: 82.2 |
| **2. CENTEL.BK** | ฿45.00 | **100** หุ้น | ฿4,500.00 | ฿42.75 (-5.0%) | ฿49.50 (2.0R) | CANSLIM Score: 74.6 | 52w Dist: -5.3% |
| **3. CPN.BK** | ฿64.50 | **100** หุ้น | ฿6,450.00 | ฿62.50 (-3.1%) | ฿68.25 (Swing Target) | RSI: 46.9 | Vol: 1.7x | Swing Score: 73.9 |
| **4. OSP.BK** | ฿19.10 | **300** หุ้น | ฿5,730.00 | ฿18.10 (-5.2%) | ฿21.10 (2.0R) | CANSLIM Score: 63.7 | 52w Dist: -4.5% |
| **5. TTB.BK** | ฿2.68 | **2,600** หุ้น | ฿6,968.00 | ฿2.54 (-5.2%) | ฿2.96 (2.0R) | High Volume: 248,154,500 shares @ ฿2.68 |
| **6. BDMS.BK** | ฿20.45 | **300** หุ้น | ฿6,135.00 | ฿19.40 (-5.1%) | ฿22.50 (2.0R) | High Volume: 119,121,800 shares @ ฿20.45 |

---

## 📋 ภารกิจสำหรับ Jules (Action Required)
1. **คัดกรองปัจจัยพื้นฐาน (Fundamental & Business Check):**
   - ตรวจสอบโมเดลธุรกิจ: กำไรโตจริง หรือแค่ภาพลวงตา?
   - ค้นหาข่าวด่วนล่าสุดจาก Google Search: มีข่าวลบ / XD / Dilution หรือไม่?
2. **ตัดสินใจ (Approve or Veto):**
   - หากหุ้นตัวใดผ่านเกณฑ์ และเข้าตา Jules ที่สุด **เลือก 1 ตัว**
   - บันทึกไฟล์ Order ตาม Template ด้านล่างลงในโฟลเดอร์ `state/jules_orders/`
   - เมื่อ Push ขึ้น GitHub แล้ว ระบบบน VM จะเข้าซื้อให้อัตโนมัติ!

---

## 📝 คำสั่งซื้อสำเร็จรูป (Order Templates)
```yaml
# Order Template 1: PLANB.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_PLANB.yaml
action: buy
symbol: "PLANB.BK"
market: "TH"
shares: 900
entry_price: 7.72
stop_price: 7.15
target_price: 8.80
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: Scale-out 50% ที่ T1 (1.5R), ขยับ Stop บังทุน, ปล่อยรันเนอร์ไป T2 (2.5R)"
```

```yaml
# Order Template 2: CENTEL.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_CENTEL.yaml
action: buy
symbol: "CENTEL.BK"
market: "TH"
shares: 100
entry_price: 45.00
stop_price: 42.75
target_price: 49.50
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: Scale-out 50% ที่ T1 (1.5R), ขยับ Stop บังทุน, ปล่อยรันเนอร์ไป T2 (2.5R)"
```

```yaml
# Order Template 3: CPN.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_CPN.yaml
action: buy
symbol: "CPN.BK"
market: "TH"
shares: 100
entry_price: 64.50
stop_price: 62.50
target_price: 68.25
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: Scale-out 50% ที่ T1 (1.5R), ขยับ Stop บังทุน, ปล่อยรันเนอร์ไป T2 (2.5R)"
```

```yaml
# Order Template 4: OSP.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_OSP.yaml
action: buy
symbol: "OSP.BK"
market: "TH"
shares: 300
entry_price: 19.10
stop_price: 18.10
target_price: 21.10
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: Scale-out 50% ที่ T1 (1.5R), ขยับ Stop บังทุน, ปล่อยรันเนอร์ไป T2 (2.5R)"
```

```yaml
# Order Template 5: TTB.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_TTB.yaml
action: buy
symbol: "TTB.BK"
market: "TH"
shares: 2600
entry_price: 2.68
stop_price: 2.54
target_price: 2.96
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: Scale-out 50% ที่ T1 (1.5R), ขยับ Stop บังทุน, ปล่อยรันเนอร์ไป T2 (2.5R)"
```

```yaml
# Order Template 6: BDMS.BK
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_BDMS.yaml
action: buy
symbol: "BDMS.BK"
market: "TH"
shares: 300
entry_price: 20.45
stop_price: 19.40
target_price: 22.50
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: Scale-out 50% ที่ T1 (1.5R), ขยับ Stop บังทุน, ปล่อยรันเนอร์ไป T2 (2.5R)"
```
