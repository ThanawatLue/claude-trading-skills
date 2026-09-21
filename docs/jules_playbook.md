# คู่มือปฏิบัติการ Jules AI Fund & Agent Playbook

เอกสารนี้รวบรวม **สถาปัตยกรรมการทำงานอัตโนมัติ 100% (Autonomous Fund)** และ **คู่มือการสั่งงาน Jules AI Agent** เพื่อบริหารพอร์ตหุ้นไทย (SET) ร่วมกับ Python Engine บน GCP VM (`35.212.209.201`)

---

## 0. สถาปัตยกรรม Jules AI Autonomous Fund (100% Fully Automated)

ระบบทำงานอัตโนมัติตามกำหนดการบน GCP VM โดยไม่ต้องรอคำสั่งจากผู้ใช้:

1. **08:30 น. (Morning Scout - `run_gcp_morning_scout.sh`):**
   - สแกนหุ้น SET ด้วย **Adaptive Matrix** (U/D Volume Ratio, Mansfield RS, Thematic Clusters)
   - คัดกรองหุ้นกับดักที่มีแรงขายสะสมออก (`U/D < 0.85`)
   - สร้างรายงานและคำสั่งซื้อจำลองใน `state/jules_tasks/today_mission.md`
2. **09:40 น. (Decision Maker - `run_gcp_auto_decision.sh`):**
   - ตรวจสอบ Market Exposure Posture (`REDUCE_ONLY` / `CASH_PRIORITY` บังคับ `HOLD_CASH` เพื่อคุ้มครองเงินต้น)
   - ตรวจสอบ Circuit Breaker (แพ้ 2 ไม้ติดลด Size 50%, แพ้ 3 ไม้หยุดเทรด 3 วัน)
   - คำนวณ SET Tick Ladder และออก Order Staging (อายุคำสั่ง TTL 45 นาที)
3. **10:15–16:45 น. (Order Processor - `run_gcp_order_processor.sh` ทุก 15 นาที):**
   - รอจังหวะราคาหลังเปิดตลาด 15 นาที (ORB-15 ข้าม ATO 10:00 น.)
   - บังคับใช้ **Max Chase Envelope ($\le +1.0\%$)** ห้ามไล่ราคาเด็ดขาด
   - แยกออเดอร์ที่มีปัญหาเข้า Dead-Letter Queue (`quarantine/`)
4. **17:05 น. (Post-Market Review - `run_gcp_post_market.sh`):**
   - ตรวจสอบ **MFE Ratchet Breakeven Stop** (+0.5R ขยับ Stop บังทุนทันที)
   - สรุปผลและส่งต่อให้ Evolver อัปเดต Trader DNA ใน `state/jules_memory/trader_dna.json`

---

## 1. ผังการแบ่งบทบาท 2 บัญชี (Dual-Agent Research Support)

| บัญชี / Agent | โควตา | บทบาทหลัก | ผลลัพธ์ที่ส่งมอบ |
| :--- | :---: | :--- | :--- |
| **User 1: Agent Alpha** | 100 Tasks | **Chief Fundamental & News Gatekeeper**<br>• วิเคราะห์โมเดลธุรกิจและงบการเงิน<br>• กวาดข่าวเรียลไทม์หาความเสี่ยงและ Catalyst<br>• ตัดสินใจให้คะแนน Confirmation Score / ใช้สิทธิ์ Veto | ไฟล์ `state/theses/<ticker>.yaml`<br>(พร้อมคะแนน 0.0 - 1.0) |
| **User 2: Agent Beta** | 100 Tasks | **Quantitative Research & Self-Evolution**<br>• ชันสูตรไม้ที่ปิดสถานะ (Trade Postmortem)<br>• วิจัยปรับแต่งกลยุทธ์จากแท่งเทียน 42,695 แท่ง<br>• เปิด Pull Request (PR) บน GitHub พัฒนาระบบอัตโนมัติ | ไฟล์ `reports/postmortems/` และ<br>**GitHub Pull Requests (PR)** |

---

## 2. ขั้นตอนการเชื่อมต่อ Jules เข้ากับ GitHub Repository

1. เข้าไปที่ [Jules Console (Google Labs)](https://jules.google/) ด้วยบัญชี Google ที่ได้รับสิทธิ์ Premium
2. กด **Connect GitHub** และอนุญาตให้ Jules เข้าถึง Repository:
   ```text
   ThanawatLue/claude-trading-skills
   ```
3. เมื่อเชื่อมต่อแล้ว คุณจะสามารถสร้าง Task ใหม่ได้โดยตรงจากหน้าเว็บ Jules หรือสั่งผ่าน Issue บน GitHub

---

## 3. ชุดคำสั่งสำเร็จรูป (Prompt Templates) สำหรับสั่งงาน Jules

---

### Template 1 (User 1 - Agent Alpha): วิเคราะห์ปัจจัยพื้นฐานและสร้าง Thesis Card
**เวลาที่ใช้:** ทุกเช้าก่อนตลาดเปิด (08:30 – 09:15 น.)  
**ความถี่:** วันละ 2–3 หุ้น (ตามที่สแกนเนอร์ส่งสัญญาณออกมา)

```markdown
คุณคือ "Jules Agent Alpha" ทำหน้าที่เป็น Chief Fundamental Analyst สำหรับพอร์ตหุ้นไทย (SET Market)
งานของคุณคือวิเคราะห์ปัจจัยพื้นฐานและสร้าง Investment Thesis Card ให้กับหุ้น: [ระบุชื่อหุ้น เช่น GULF.BK, BDMS.BK]

ขั้นตอนการทำงาน:
1. ศึกษาโมเดลธุรกิจ โครงสร้างรายได้ และความสามารถในการแข่งขันของบริษัท
2. ตรวจสอบงบการเงินไตรมาสล่าสุด:
   - รายได้และกำไรสุทธิเติบโตหรือไม่?
   - อัตราหนี้สินต่อทุน (D/E) และกระแสเงินสดจากการดำเนินงานเป็นอย่างไร?
3. ตรวจสอบความเสี่ยงทางองค์กรและตลาดทุน (Veto Signals):
   - มีการเพิ่มทุน (Dilution) หรือไม่?
   - มีวันขึ้นเครื่องหมาย XD ใน 7 วันทำการนี้หรือไม่?
   - มีคดีความหรือการสอบสวนจาก ก.ล.ต./DSI หรือไม่?
4. ให้คะแนน Confirmation Score ระหว่าง 0.0 ถึง 1.0 (เกณฑ์ผ่านคือ >= 0.60)
5. สร้างหรืออัปเดตไฟล์ Thesis ในโฟลเดอร์ state/theses/ ด้วยรูปแบบ YAML ตามมาตรฐาน trader-memory-core
   - ตั้งชื่อไฟล์: state/theses/th_[ticker_lowercase]_[date].yaml
   - กำหนด status เป็น "APPROVED" หรือ "REJECTED"
   - สรุป thesis_statement, catalysts, และ kill_criteria ให้ชัดเจน
```

---

### Template 2 (User 1 - Agent Alpha): ตรวจสอบข่าวด่วนและ Sentiment รายวัน
**เวลาที่ใช้:** เช้าก่อนตลาดเปิด (09:15 – 09:30 น.) หรือช่วงเที่ยง (12:30 น.)

```markdown
คุณคือ "Jules Agent Alpha" ทำหน้าที่ตรวจสอบข่าวสารและ Sentiment ตลาดหุ้นไทย (SET Market)
งานของคุณคือค้นหาและวิเคราะห์ข่าวสารล่าสุดของหุ้นใน Watchlist วันนี้: [ระบุชื่อหุ้น เช่น GULF.BK, AMATA.BK]

ขั้นตอนการทำงาน:
1. ค้นหาข่าวสารจากสื่อการเงินไทย (ข่าวหุ้น, ทันหุ้น, สำนักข่าวอินโฟเควสท์, ข่าวแจ้งตลาดหลักทรัพย์ SET) ในช่วง 24 ชั่วโมงที่ผ่านมา
2. ประเมินว่ามีข่าวที่มีผลกระทบต่อราคาอย่างมีนัยสำคัญหรือไม่:
   - ข่าวบวก (Catalyst): งานประมูลใหม่, กำไรดีกว่าคาด, พันธมิตรธุรกิจ
   - ข่าวลบ (Headwind): ต้นทุนพุ่ง, ถูกปรับลดเครดิต, ข้อพิพาททางกฎหมาย
3. หากพบข่าวลบรุนแรง ให้ระบุคำสั่ง "VETO: [ชื่อหุ้น]" พร้อมเหตุผล เพื่อให้ระบบระงับการเปิดสถานะในเช้าวันนี้
4. รายงานสรุปผลสั้นๆ 1 ย่อหน้าต่อ 1 หุ้น
```

---

### Template 3 (User 2 - Agent Beta): ชันสูตรไม้ที่เทรดจบ (Trade Postmortem)
**เวลาที่ใช้:** ช่วงเย็นหลังตลาดปิด (17:00 – 18:30 น.)

```markdown
คุณคือ "Jules Agent Beta" ทำหน้าที่เป็น Lead Quantitative Risk & Postmortem Analyst
งานของคุณคือวิเคราะห์ประวัติการเทรดที่ปิดสถานะไปแล้ว เพื่อหาสาเหตุและพัฒนาการเทรดให้ดียิ่งขึ้น

ขั้นตอนการทำงาน:
1. ตรวจสอบข้อมูลไม้ที่ปิดสถานะล่าสุดจากตาราง paper_trade ใน state/market_cache.db (หรือผ่าน API /api/signal-results?market=TH)
2. วิเคราะห์สาเหตุการปิดสถานะของแต่ละไม้:
   - หากเป็น "closed_target": หุ้นวิ่งขึ้นไปถึงเป้าหมาย 2.2R ได้อย่างไร? ใช้เวลากี่วัน?
   - หากเป็น "closed_fakeout": วอลุ่มหดตัวจริงหรือไม่? ช่วยประหยัดความเสียหายได้เท่าไหร่?
   - หากเป็น "closed_stalled": ทำไมราคาจึงแช่นิ่งเกิน 4 วัน? มีแนวต้านใหญ่ขวางอยู่หรือไม่?
   - หากเป็น "closed_stop": เกิดจาก Noise ตลาด หรือสัญญาณเบรกหลอก?
3. บันทึกผลการชันสูตรลงในโฟลเดอร์ reports/postmortems/ ในรูปแบบ Markdown:
   - สรุป Root Cause
   - Lesson Learned สำหรับการปรับปรุงเกณฑ์คัดกรองในอนาคต
```

---

### Template 4 (User 2 - Agent Beta): วิจัยปรับปรุงกลยุทธ์และเปิด GitHub Pull Request
**เวลาที่ใช้:** รายสัปดาห์ (วันศุกร์เย็น หรือช่วงสุดสัปดาห์)

```markdown
คุณคือ "Jules Agent Beta" ทำหน้าที่พัฒนาและปรับปรุงระบบ Trading Engine บน GitHub Repository
งานของคุณคือทดสอบสมมติฐานการปรับปรุงกลยุทธ์ และส่งมอบโค้ดผ่าน GitHub Pull Request

ขั้นตอนการทำงาน:
1. อ่านผลการทดสอบ Backtest ล่าสุดใน walkthrough.md และสคริปต์ใน scripts/optimize_trading_engine.py
2. ทดลองรัน Backtest บนฐานข้อมูล state/market_cache.db ด้วยการปรับปรุง Parameter หรือฟิลเตอร์ใหม่ เช่น:
   - ปรับแต่งเกณฑ์ Early Fakeout Volume Ratio (เช่น 0.35x vs 0.40x)
   - ทดสอบค่า Dynamic ATR Multiplier (1.2x vs 1.4x)
   - ทดสอบเงื่อนไข Sector RS Filter
3. ตรวจสอบว่าผลลัพธ์ใหม่มี Net PnL, Win Rate, และ Profit Factor ที่ดีขึ้นกว่า Champion เดิมหรือไม่
4. รันชุดทดสอบด้วยคำสั่ง:
   uv run pytest scripts/tests/ skills/paper-trade-simulator/scripts/tests/
   และตรวจเช็กโค้ดด้วย:
   uv run ruff check scripts/ skills/
5. หากทุกอย่างผ่าน 100% ให้สร้าง Branch ใหม่และเปิด "Pull Request (PR)" บน GitHub พร้อมสรุปตารางเปรียบเทียบผลงานก่อนและหลังปรับปรุง
```

---

## 4. ปฏิทินบริหารโควตา 200 Tasks (Quota Management)

| สัปดาห์ | User 1 (Agent Alpha - Fundamental) | User 2 (Agent Beta - Quant/R&D) | รวม Tasks |
| :---: | :---: | :---: | :---: |
| **สัปดาห์ที่ 1** | 20 Tasks (วันละ ~4 Tasks: Thesis & ข่าว) | 20 Tasks (Postmortem 10 + Backtest 10) | 40 Tasks |
| **สัปดาห์ที่ 2** | 20 Tasks (วันละ ~4 Tasks: Thesis & ข่าว) | 20 Tasks (Postmortem 10 + PR ปรับปรุง 10) | 40 Tasks |
| **สัปดาห์ที่ 3** | 20 Tasks (วันละ ~4 Tasks: Thesis & ข่าว) | 20 Tasks (Postmortem 10 + Backtest 10) | 40 Tasks |
| **สัปดาห์ที่ 4** | 20 Tasks (วันละ ~4 Tasks: Thesis & ข่าว) | 20 Tasks (Monthly Review & Strategy PR) | 40 Tasks |
| **สำรองฉุกเฉิน** | 20 Tasks (สแกนรอบพิเศษช่วงงบออก) | 20 Tasks (แก้บั๊กและ Refactor โค้ด) | 40 Tasks |
| **รวมทั้งเดือน** | **100 Tasks** | **100 Tasks** | **200 Tasks** |

---

## 5. การตรวจสอบความปลอดภัย (CI/CD Safety Gate)

ทุกครั้งที่ **Jules Agent Beta** เปิด Pull Request (PR) บน GitHub:
1. **GitHub Actions CI (`.github/workflows/ci.yml`):** จะรัน Unit Test 338 ข้ออัตโนมัติทันที
2. **Auto Deploy (`.github/workflows/deploy.yml`):** เมื่อคุณตรวจสอบ PR และกดปุ่ม **Merge to main** บน GitHub ระบบจะนำโค้ดใหม่ไปรันบน Google Cloud VM ทันทีโดยที่คุณไม่ต้องพิมพ์คำสั่ง SSH เองเลยครับ!

---

## 6. สมรภูมิประชันผลงาน: The Great Alpha Arena (Quant Champion vs Jules AI Fund)

ระบบได้แบ่งพอร์ตการทดลองออกเป็น 2 กองทุนคู่ขนาน (เงินทุนตั้งต้นกองละ ฿30,000.00):
* **🤖 กองทุนที่ 1: Quant Systematic Fund (ฝั่งคุณ + Engine)** เทรดตามระเบียบวินัยและอินดิเคเตอร์ทางเทคนิค
* **🧠 กองทุนที่ 2: Jules AI Autonomous Fund (ฝั่ง AI Coach + Jules)** เทรดตามปัจจัยพื้นฐาน, โมเดลธุรกิจ, ข่าวสาร, และการตัดสินใจเชิงตรรกะ

### คำสั่งสำหรับ Jules ในการส่งคำสั่งซื้อขาย:
1. **ตรวจเช็กสถานะพอร์ตของ Jules:**
   ```bash
   python scripts/jules_fund.py status
   ```
2. **สั่งซื้อหุ้นเข้าพอร์ต Jules:**
   ```bash
   python scripts/jules_fund.py buy --symbol BDMS.BK --shares 1000 --thesis "งบ Q2 โตเด่น ได้แรงหนุนผู้ป่วยต่างชาติ"
   ```
3. **สั่งขายหุ้นทำกำไร/ตัดขาดทุน:**
   ```bash
   python scripts/jules_fund.py sell --symbol BDMS.BK --reason "ราคาแตะเป้าหมาย 2.2R"
   ```
4. **ส่งคำสั่งผ่าน GitHub Commit (Queue):**
   Jules สามารถสร้างไฟล์คำสั่งซื้อ เช่น `state/jules_orders/buy_BDMS.yaml` แล้ว Commit ขึ้น GitHub เพื่อให้ระบบบน Cloud ดึงไปเคาะซื้ออัตโนมัติ:
   ```yaml
   action: "buy"
   symbol: "BDMS.BK"
   shares: 1000
   thesis: "โรงพยาบาลเอกชนกำไรแข็งแกร่ง"
   ```
5. **ติดตามผลการประชันแบบ Real-Time บน Dashboard:**
   เข้าแท็บ **⚔️ AI Battle Arena** ที่ `http://35.212.209.201/` หรือเรียกผ่าน API:
   ```bash
   curl http://35.212.209.201/api/arena/overview?market=TH
   ```
