# Project Migration & Feature Updates

โปรเจกต์นี้ได้รับการปรับปรุงและพัฒนาอย่างต่อเนื่องเพื่อเพิ่มความสามารถในการวิเคราะห์ตลาดหลักทรัพย์และจำลองการเทรด โดยครอบคลุมทั้งตลาดสหรัฐฯ และตลาดหุ้นไทย (SET) รวมถึงการย้ายระบบประมวลผล LLM และการเชื่อมต่อข้อมูลระบบคลาวด์

## 1. การเปลี่ยนผ่านระบบ LLM: จาก Claude CLI เป็น Gemini Native
*   **การเปลี่ยนระบบ Engine**: เปลี่ยนระบบ Automation จากการเรียกใช้ `claude` CLI มาเป็นการเรียกใช้ **Gemini API** โดยตรงเพื่อลดการพึ่งพา Claude Token
*   **รุ่นที่ใช้งาน**: ปัจจุบันระบบใช้รุ่น **Gemini 3.5 Flash** (อัปเกรดจาก 2.5 Flash / 1.5 Flash เดิม) เป็นค่าเริ่มต้นเพื่อความรวดเร็วและประหยัดค่าใช้จ่าย
*   **ระบบ Adapter (`scripts/gemini_adapter.py`)**: ทำหน้าที่เป็น Bridge ในการทำ Tool Use (Function Calling) เช่น `read_file`, `write_file`, `list_files`, และ `grep_search` เพื่อให้โมเดลสามารถดำเนินการปรับปรุงโค้ดและแก้ไขไฟล์ในเครื่องได้ในแบบ Agent Loop รวมถึงมีระบบ Auto-retry เมื่อเจอข้อผิดพลาดจำพวก transient errors (429 Rate Limit, 503 Service Unavailable)

## 2. ระบบจำลองการเทรด (Paper Trade Simulator) [NEW]
ระบบจำลองการส่งคำสั่งซื้อขายแบบ Paper Trading โดยไม่ต้องใช้เงินจริง เพื่อช่วยฝึกฝนวินัยและประเมินประสิทธิภาพกลยุทธ์
*   **ฐานข้อมูล**: บันทึกสถานะการเทรดผ่าน SQLite (`state/market_cache.db`)
*   **ฟีเจอร์การวัดผล**:
    *   คำนวณกำไร/ขาดทุนแบบ R-multiple P/L
    *   วัดระดับจุดสูงสุดและต่ำสุดระหว่างถือสถานะ (MAE/MFE - Maximum Adverse/Favorable Excursion)
    *   ระบบบันทึกความคิดเห็นรายวัน (Trade Journaling) และประเมินอารมณ์ความรู้สึกด้วย Emotion tags (เช่น Fear, Greed, Discipline, Impulse) เพื่อคำนวณคะแนนวินัย (Discipline Scorecard)
*   **REST API ใน Dashboard (`dashboard/app.py`)**:
    *   `/api/paper/open` - เปิดสถานะจำลองใหม่
    *   `/api/paper/close` - ปิดสถานะจำลอง
    *   `/api/paper/list` - รายการสถานะที่ถือครองหรือปิดไปแล้ว
    *   `/api/paper/stats` - สรุปสถิติพอร์ตจำลองแยกรายตลาด (TH / US)
    *   `/api/paper/update_marks` - ดึงราคาล่าสุดมาปรับปรุงค่า Mark-to-Market และคำนวณจุด Stop/Target อัตโนมัติ

## 3. การซิงก์ฐานข้อมูลกับ Hugging Face (SQLite Dataset Sync) [NEW]
เพื่อแก้ไขปัญหาการจัดเก็บฐานข้อมูล SQLite บนเครื่องจำลองหรือ Cloud Server ที่ไม่มี Disk ถาวร (Ephemeral storage)
*   **สคริปต์ทำงาน (`dashboard/hf_sync.py`)**:
    *   ระบบจะทำการดาวน์โหลดฐานข้อมูล `market_cache.db` ล่าสุดจาก Hugging Face Hub Dataset ในช่วงเริ่มต้น (Startup)
    *   เมื่อใดก็ตามที่มีการทำธุรกรรม (เปิด/ปิดสถานะ หรือบันทึก Journal) ระบบจะอัปโหลดไฟล์ไปที่ Hugging Face Dataset ทันทีในแบบเบื้องหลัง (Background Thread) เพื่อไม่ให้กระทบต่อความเร็วการประมวลผลหน้าเว็บ
*   **Environment Variables**: ต้องระบุ `HF_TOKEN` (สิทธิ์ในการ Write) และ `HF_DB_REPO_ID` (เช่น username/dataset-repo)

## 4. ระบบการสแกนและวิเคราะห์หุ้นไทย (Thai SET Market Screeners) [NEW]
โปรเจกต์ได้ขยายความสามารถในการวิเคราะห์ข้ามไปยัง **ตลาดหุ้นไทย (SET)** โดยออกแบบให้ดึงข้อมูลฟรีจาก TradingView Public Screener ทำให้**ไม่ต้องใช้ API Key เสียเงิน**ใดๆ
*   **Thai Breadth Analyzer (`thai-breadth-analyzer`)**: สแกนความกว้างของตลาด SET กว่า 900 ตัวเพื่อประเมินความแข็งแกร่งของภาพรวม (สัดส่วนหุ้นเหนือ SMA50/SMA200, Advance-Decline, RSI Distribution, Composite Breadth Score)
*   **Thai Sector Heatmap (`thai-sector-heatmap`)**: วัดความแข็งแกร่งและแนวโน้มการไหลเข้าออกของเงินรายกลุ่มอุตสาหกรรม (Sector Momentum 1M, 3M, 6M, YTD)
*   **Thai Watchlist Builder (`thai-watchlist-builder`)**: คัดกรองหุ้นเข้ากลุ่มเฝ้าระวัง 4 สไตล์ ได้แก่ Growth, Value, Momentum, และ Mean-Reversion
*   **Thai Dividend Screener (`thai-dividend-screener`)**: ค้นหาหุ้นปันผลเด่น คัดกรอง Yield, Valuation, Liquidity, และ Trend Health
*   **Thai Swing Screener (`skills/vcp-screener/scripts/screen_thai_swing.py`)**: ค้นหาจุดเข้าซื้อสไตล์ Swing Trade (ถือครอง 3-5 วัน) แบ่งกลยุทธ์เป็น Dip Buy (ซื้อเมื่อย่อในขาขึ้น) และ Momentum (ซื้อเมื่อทะลุหรือจังหวะวิ่งแรง) พร้อมคำนวณ Stop Loss และ Target ตามความผันผวน ATR รายตัว

## 5. การสลับรุ่น AI และการตั้งค่าระบบ (Configuration & Models)
หากต้องการเปลี่ยนรุ่น AI หรือปรับแต่งการทำงาน:
*   **สคริปต์หลัก**: สามารถเปลี่ยนค่า `model_name` ใน `scripts/gemini_adapter.py` หรือตัวแปรเรียกใช้ในโค้ดอื่น เช่นเปลี่ยนเป็น `"gemini-1.5-flash"` หรือรุ่นอื่นๆ ตามต้องการ
*   **Environment Variables ที่เกี่ยวข้อง**:
    *   `GEMINI_API_KEY`: API Key จาก [Google AI Studio](https://aistudio.google.com/) (จำเป็นสำหรับระบบพัฒนาและ Improvement Loop)
    *   `FMP_API_KEY`: สำหรับดึงข้อมูลการเงินตลาด US (ใช้ในกลยุทธ์ฝั่งสหรัฐฯ)
    *   `FINVIZ_API_KEY`: (ตัวเลือกเสริม) สำหรับดึงข้อมูลคัดกรองหุ้นสหรัฐฯ
    *   `HF_TOKEN` & `HF_DB_REPO_ID`: สำหรับใช้งานซิงก์ข้อมูลของจำลองพอร์ต

## 6. สคริปต์การจัดการเอกสาร (Documentation Scripts)
เพื่อให้การบันทึกรายการทักษะ (Skills Index) และเอกสารคู่มือของโค้ดสอดคล้องกัน โปรเจกต์มีระบบเอกสารกึ่งอัตโนมัติดังนี้:
*   `python scripts/validate_skills_index.py`: ตรวจสอบความถูกต้องของสกีมา `skills-index.yaml`
*   `python scripts/generate_catalog_from_index.py`: อัปเดตตารางสรุปสกิลใน `README.md` และตาราง API Matrix ใน `CLAUDE.md` โดยดึงข้อมูลโดยตรงจาก `skills-index.yaml`
*   `python scripts/generate_skill_docs.py --overwrite`: สร้างคู่มือแยกรายสกิลภายใต้โฟลเดอร์ `docs/en/skills/` โดยอิงตามเนื้อหาใน `SKILL.md` และสร้างหน้าสรุปรวมสกิล
*   `python scripts/generate_workflow_docs.py`: สร้างคู่มือแสดงขั้นตอนทำงาน (Workflows) ภายใต้ `docs/en/workflows.md`
