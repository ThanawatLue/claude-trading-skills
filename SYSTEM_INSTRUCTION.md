# Trading Skills System — คู่มือการใช้งาน (Powered by Gemini)

> อัปเดตล่าสุด: 2026-05-06 | ทดสอบบนระบบจริง Windows 11 + Python 3.14

---

## 📋 ภาพรวมระบบ

โปรเจกต์นี้เป็น **ระบบช่วยวิเคราะห์และเทรดหุ้น** ที่ใช้ Gemini AI เป็นสมองกลาง ประกอบด้วย:

| ส่วนประกอบ | คำอธิบาย |
|---|---|
| **54 Trading Skills** | เครื่องมือวิเคราะห์หุ้นแต่ละประเภท |
| **Improvement Pipeline** | ระบบ AI ตรวจสอบและอัปเกรด Skill อัตโนมัติ |
| **Generation Pipeline** | ระบบ AI สร้าง Skill ใหม่จาก Session Logs |

---

## 🔧 การตั้งค่าเบื้องต้น (ทำครั้งเดียว)

### 1. ติดตั้ง Dependencies
```powershell
# รันใน Terminal ที่โฟลเดอร์ d:\ex_work\trading
pip install pyyaml jsonschema scipy google-genai
```

### 2. ตั้งค่า API Keys

**Gemini API Key (จำเป็น — ใช้รัน AI):**
```powershell
# ชั่วคราว (เฉพาะ Session นี้)
$env:GEMINI_API_KEY = "your-gemini-api-key-here"
```
หรือตั้งถาวรผ่าน: Start → "Edit system environment variables" → Environment Variables → New

**API Keys อื่นๆ (ต้องการตามเครื่องมือที่ใช้):**
```powershell
$env:FMP_API_KEY = "your-fmp-key"          # สำหรับ VCP, FTD, Earnings, ฯลฯ
$env:FINVIZ_API_KEY = "your-finviz-key"    # สำหรับ Finviz Screener
```

> **หมายเหตุ:** FMP API Key ได้จาก https://financialmodelingprep.com (มีแผนฟรี)
> FINVIZ API Key ได้จาก https://finviz.com/elite.ashx (Elite plan)

---

## 🚀 วิธีใช้งาน: ระบบ AI Pipelines

### Pipeline 1: ระบบปรับปรุง Skill อัตโนมัติ

Gemini AI จะสุ่มเลือก Skill มาตรวจสอบ และหากคะแนนต่ำกว่า 90/100 จะลงมือแก้โค้ดให้อัตโนมัติ

```powershell
# ทดสอบโดยไม่แก้ไขไฟล์จริง (แนะนำให้รันก่อน)
python scripts/run_skill_improvement_loop.py --dry-run

# รันจริง (Gemini จะแก้โค้ด Skill ให้อัตโนมัติ)
python scripts/run_skill_improvement_loop.py
```

**ดูผลลัพธ์:** โฟลเดอร์ `reports/skill-improvement-log/`

---

### Pipeline 2: ระบบสร้าง Skill ใหม่

**ขั้นตอนที่ 1 — Weekly: ขุดไอเดียใหม่จาก Session Logs (ทุกสัปดาห์)**
```powershell
# ทดสอบ (ไม่เรียก Gemini จริง)
python scripts/run_skill_generation_pipeline.py --mode weekly --dry-run

# รันจริง (Gemini วิเคราะห์ Log แล้วหาไอเดีย Skill ใหม่)
python scripts/run_skill_generation_pipeline.py --mode weekly
```
> ต้องการ: Claude/Gemini session logs ใน `~/.claude/projects/` หรือ `~/.gemini/projects/`

**ขั้นตอนที่ 2 — Daily: ออกแบบและสร้าง Skill ใหม่ (ทุกวัน)**
```powershell
# ทดสอบ
python scripts/run_skill_generation_pipeline.py --mode daily --dry-run

# รันจริง (Gemini เขียนโค้ด Skill ใหม่และสร้างโฟลเดอร์ให้อัตโนมัติ)
python scripts/run_skill_generation_pipeline.py --mode daily
```

---

### ระบบ Review: ตรวจสอบคุณภาพ Skill

```powershell
# ตรวจสอบ Skill ทั้งหมดพร้อมกัน (ดูภาพรวม)
python skills/dual-axis-skill-reviewer/scripts/run_dual_axis_review.py --all --skip-tests --output-dir reports

# ตรวจสอบ Skill เฉพาะ (ตัวอย่าง: vcp-screener)
python skills/dual-axis-skill-reviewer/scripts/run_dual_axis_review.py --skill vcp-screener --skip-tests
```

**ผลคะแนน Skill ปัจจุบัน (จากการทดสอบจริง):**

| ระดับคะแนน | Skills |
|---|---|
| 88-89/100 (เกือบผ่าน) | backtest-expert, pead-screener, position-sizer, signal-postmortem, skill-idea-miner, skill-integration-tester, stanley-druckenmiller-investment, strategy-pivot-designer, theme-detector |
| 80-87/100 (ปานกลาง) | breadth-chart-analyst, canslim-screener, finviz-screener, institutional-flow-tracker, macro-regime-detector, market-breadth-analyzer, market-environment-analysis, market-news-analyst, market-top-detector, options-strategy-advisor, parabolic-short-trade-planner, scenario-analyzer, sector-analyst, technical-analyst, trader-memory-core, uptrend-analyzer, vcp-screener |
| 49-79/100 (ต้องปรับปรุง) | breakout-trade-planner, downtrend-duration-analyzer, earnings-calendar, earnings-trade-analyzer, economic-calendar-fetcher, edge-*, exposure-coach, ftd-detector, ibd-distribution-day-monitor, pair-trade-screener, portfolio-manager, trade-hypothesis-ideator, us-market-bubble-detector, us-stock-analysis, value-dividend-screener |

> **เกณฑ์:** ต้องการ ≥ 90/100 จึงจะ "ผ่าน" — ยังไม่มี Skill ใดผ่านเกณฑ์นี้ในขณะนี้

---

## 📊 วิธีใช้งาน: เครื่องมือเทรดหุ้น (54 Skills)

### 🔍 กลุ่ม: Stock Screeners (ต้องการ FMP_API_KEY)

#### VCP Screener — หาหุ้น Volatility Contraction Pattern
```powershell
python skills/vcp-screener/scripts/screen_vcp.py --help
python skills/vcp-screener/scripts/screen_vcp.py --output-dir reports/vcp
```
> **ใช้งาน:** สแกนหาหุ้นที่ Volatility หดตัวแบบ VCP ตามตำรา Mark Minervini

#### CANSLIM Screener — หาหุ้น High Growth
```powershell
python skills/canslim-screener/scripts/screen_canslim.py --help
```
> **ใช้งาน:** กรองหุ้นตาม Criteria ของ William O'Neil (EPS Growth, RS, Accumulation)

#### PEAD Screener — หา Post-Earnings Drift
```powershell
python skills/pead-screener/scripts/screen_pead.py --help
```
> **ใช้งาน:** หาหุ้นที่มีแนวโน้ม Drift หลัง Earnings Surprise

#### Finviz Screener — สแกนด้วย Finviz (ต้องการ FINVIZ_API_KEY)
```powershell
python skills/finviz-screener/scripts/run_screener.py --help
```

---

### 📈 กลุ่ม: Market Analysis (ต้องการ FMP_API_KEY)

#### Market Breadth Analyzer — วัดสุขภาพตลาด
```powershell
python skills/market-breadth-analyzer/scripts/analyze_breadth.py --help
```
> **ใช้งาน:** คำนวณ Advance/Decline, % หุ้นเหนือ MA50/200, McClellan Oscillator

#### Macro Regime Detector — ตรวจสภาวะเศรษฐกิจ
```powershell
python skills/macro-regime-detector/scripts/detect_regime.py --help
```
> **ใช้งาน:** บ่งชี้ว่าตลาดอยู่ใน Regime ไหน (Risk-On, Risk-Off, Stagflation)

#### Market Top Detector — ตรวจจับ Market Top
```powershell
python skills/market-top-detector/scripts/detect_top.py --help
```
> **ใช้งาน:** ใช้สัญญาณ Distribution Days + Breadth Divergence ตรวจหา Market Top

#### FTD Detector — หาวัน Follow-Through Day
```powershell
python skills/ftd-detector/scripts/detect_ftd.py --help
```
> **ใช้งาน:** ตรวจหาวันที่ตลาดยืนยันการ Bottom (ตาม IBD Method)

---

### 💰 กลุ่ม: Trade Management

#### Position Sizer — คำนวณขนาด Position
```powershell
python skills/position-sizer/scripts/calculate_position.py --help
```
> **ใช้งาน:** คำนวณจำนวนหุ้นที่ควรซื้อตาม Risk % และจุด Stop-Loss

#### Backtest Expert — ทดสอบกลยุทธ์
```powershell
python skills/backtest-expert/scripts/run_backtest.py --help
```
> **ใช้งาน:** ทดสอบ Trading Strategy กับข้อมูลในอดีต

#### Signal Postmortem Analyzer — วิเคราะห์ผลการเทรด
```powershell
python skills/signal-postmortem-analyzer/scripts/analyze_postmortem.py --help
```
> **ใช้งาน:** วิเคราะห์ผลการเทรดที่ผ่านมาว่า Edge ยังคงอยู่ไหม

---

### 🧠 กลุ่ม: Strategy & Ideas

#### Trade Hypothesis Ideator — สร้างไอเดียการเทรด
```powershell
# ไม่ต้องการ API Key — ใช้ Knowledge Base
# เรียกใช้ผ่าน AI Assistant ด้วย SKILL.md เป็น Prompt
```

#### Stanley Druckenmiller Investment — กลยุทธ์แบบ Druckenmiller
```powershell
# เรียกใช้ผ่าน AI Assistant — เป็น Knowledge-based Skill
```

---

## ✅ สรุปสถานะระบบ (ผลทดสอบจริง 2026-05-06)

| Component | สถานะ | หมายเหตุ |
|---|---|---|
| `gemini_adapter.py` | ✅ พร้อมใช้ | ใช้ SDK ใหม่ google-genai |
| `run_skill_improvement_loop.py` | ✅ พร้อมใช้ | dry-run ทำงานสมบูรณ์ |
| `run_skill_generation_pipeline.py` | ✅ พร้อมใช้ | dry-run ทำงานสมบูรณ์ |
| `run_dual_axis_review.py` | ✅ พร้อมใช้ | review ครบ 54 skills |
| Trading Skills (54 ตัว) | ⚠️ ต้องใส่ API Key | ต้องการ FMP/FINVIZ Key |
| Score ≥ 90 | ❌ ยังไม่มี | Gemini Pipeline จะค่อยๆ แก้ |

---

## 🐛 ปัญหาที่แก้ไขไปแล้ว

| Bug | ไฟล์ | สถานะ |
|---|---|---|
| `google.generativeai` deprecated → เปลี่ยนเป็น `google.genai` | `gemini_adapter.py` | ✅ Fixed |
| Claude CLI guards block execution | `run_skill_generation_pipeline.py` | ✅ Fixed |
| `CLAUDE_TIMEOUT` NameError | `run_skill_generation_pipeline.py` | ✅ Fixed |
| `import sys` ลืม | `mine_session_logs.py`, `score_ideas.py` | ✅ Fixed |
| `write_file()` crash เมื่อ path ไม่มี parent dir | `gemini_adapter.py` | ✅ Fixed |
| Default model เป็น `gemini-1.5-flash` | ทุกไฟล์ | ✅ Fixed → `gemini-3-flash-preview` |

---

## 📁 โครงสร้างโฟลเดอร์สำคัญ

```
d:\ex_work\trading\
├── scripts/
│   ├── gemini_adapter.py          ← Gemini AI Bridge (หัวใจหลัก)
│   ├── run_skill_improvement_loop.py  ← AI ปรับปรุง Skill อัตโนมัติ
│   └── run_skill_generation_pipeline.py ← AI สร้าง Skill ใหม่
├── skills/
│   ├── vcp-screener/              ← หา VCP Pattern
│   ├── canslim-screener/          ← CANSLIM Screener
│   ├── market-breadth-analyzer/   ← วัดสุขภาพตลาด
│   ├── macro-regime-detector/     ← ตรวจ Macro Regime
│   └── ... (54 skills รวม)
├── reports/                       ← ผลลัพธ์ทุกการรัน
├── logs/                          ← Log ประวัติการทำงาน
└── SYSTEM_INSTRUCTION.md         ← ไฟล์นี้
```
