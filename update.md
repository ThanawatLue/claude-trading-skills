# Trading Automation Update

Last updated: 2026-07-04

## สถานะล่าสุด

โปรเจกต์ขยับจากชุดเครื่องมือวิเคราะห์ ไปสู่ระบบเก็บผลลัพธ์และเรียนรู้จาก signal จริงแล้วบางส่วน

ระดับปัจจุบัน:

```text
Level 1: Auto collect signals              - partially done
Level 2: Auto track outcomes               - done for cached forward outcomes
Level 3: Auto paper trade                  - infrastructure done, waiting for fresh eligible signals
Level 4: Auto calibration report           - partially visible in dashboard
Level 5: Auto suggest rule changes         - early readiness-based suggestions
Level 6: Auto adjust weights with limits   - not yet
Level 7: Real-money execution approval     - intentionally not yet
```

สิ่งที่ทำเสร็จแล้ว:

- เพิ่ม `Signal Results` tab ใน dashboard
- เพิ่ม `scripts/signal_ledger.py`
  - ตาราง `signal_ledger`
  - ตาราง `signal_outcome`
  - ingest thesis จาก `state/theses`
  - track forward outcomes ที่ 5D / 20D / 60D จาก `price_bar`
- เพิ่ม `scripts/auto_paper.py`
  - dry-run เป็น default
  - เปิด paper trade เฉพาะเมื่อใช้ `--execute`
  - กัน stale signal
  - กัน duplicate open paper position
  - link paper trade กลับไปที่ signal ledger
- เพิ่ม tests:
  - `scripts/tests/test_signal_ledger.py`
  - `scripts/tests/test_auto_paper.py`

ผลจากข้อมูลปัจจุบัน:

```text
Ledger signals: 28
Forward-tested signals: 27
vcp-screener 5D outcomes: 27
vcp-screener 5D win rate: 44%
vcp-screener avg 5D return: +0.2%
vcp-screener 20D outcomes: 11
vcp-screener avg 20D return: +2.2%
Auto-paper eligible: 0
```

เหตุผลที่ `Auto-paper eligible = 0`:

- signal ปัจจุบันมาจาก 2026-05-25
- gate ปัจจุบันรับเฉพาะ signal อายุไม่เกิน 10 วัน
- ไม่มี signal สดที่ผ่าน `score >= 70`

นี่เป็นพฤติกรรมที่ถูกต้อง เพราะระบบไม่ควรเปิด paper trade จาก signal เก่าจนกลายเป็น backfill หลอกตัวเอง

## คำสั่งใช้งานปัจจุบัน

Ingest thesis เข้า signal ledger:

```powershell
uv run python scripts\signal_ledger.py ingest-theses
```

Update forward outcomes:

```powershell
uv run python scripts\signal_ledger.py update-outcomes --market TH
uv run python scripts\signal_ledger.py update-outcomes --market US
```

ดู summary:

```powershell
uv run python scripts\signal_ledger.py summary --market TH
```

Auto-paper dry-run:

```powershell
uv run python scripts\auto_paper.py --market TH --min-score 70 --max-age-days 10
```

Auto-paper execute:

```powershell
uv run python scripts\auto_paper.py --market TH --min-score 70 --max-age-days 10 --execute
```

คำสั่ง `--execute` เปิดเฉพาะ paper trade ไม่ใช่เงินจริง

## แผนพัฒนาส่วนที่เหลือ

### Phase A: ทำ daily automation ให้ครบ

เป้าหมาย:

ให้ระบบทำงานเองหลังตลาดปิด แม้ผู้ใช้ไม่ได้เข้า dashboard

งานที่ต้องทำ:

- สร้าง orchestrator เช่น `scripts/run_daily_signal_pipeline.py`
- ลำดับงาน:
  1. run fresh analysis / screeners
  2. ingest new theses/signals เข้า `signal_ledger`
  3. update forward outcomes ของ signals เก่า
  4. run auto-paper dry-run
  5. ถ้า config อนุญาต ให้ auto-paper execute
  6. export daily summary report
- เพิ่ม config file เช่น `state/automation_config.yaml`
- เพิ่ม Windows Task Scheduler หรือ batch runner

Definition of done:

- รันคำสั่งเดียวแล้วจบครบ loop
- dashboard เห็น signal ใหม่และ outcome ใหม่
- ไม่มี duplicate paper positions
- default ยังไม่แตะเงินจริง

### Phase B: ทำ signal export ให้เป็นมาตรฐาน

เป้าหมาย:

ทุก screener ต้องส่งออก signal format เดียวกัน ไม่ใช่พึ่ง thesis YAML อย่างเดียว

งานที่ต้องทำ:

- กำหนด canonical schema:

```text
signal_id
symbol
market
source_skill
signal_date
direction
raw_score
entry_price
stop_price
target_price
time_horizon
market_regime
reason
payload_json
```

- ปรับ VCP / CANSLIM / PEAD / Thai screeners ให้ export signal records
- เพิ่ม validator สำหรับ signal JSON
- ให้ `signal_ledger.py` ingest ได้ทั้งจาก thesis และ signal JSON

Definition of done:

- ไม่ต้องพึ่ง manual thesis ingestion อย่างเดียว
- signal ใหม่เข้าระบบอัตโนมัติทุกวัน
- dashboard แยก source ได้ถูกต้อง

### Phase C: Auto-paper policy และ risk guard

เป้าหมาย:

ทำให้ Level 3 ปลอดภัยขึ้นและควบคุม risk ของ paper portfolio ได้

งานที่ต้องทำ:

- เพิ่ม policy config:

```yaml
auto_paper:
  enabled: false
  market: TH
  min_score: 70
  max_age_days: 10
  max_new_positions_per_day: 3
  max_open_positions: 10
  default_stop_pct: 8
  target_r: 2
  require_regime_allowed: true
```

- เพิ่ม guard:
  - ห้ามเปิดถ้า market regime เป็น restrictive
  - ห้ามเปิดถ้า source ยังไม่มี sample เพียงพอ แล้วเปิดขนาดเล็กเท่านั้น
  - ห้ามเปิดถ้าซ้ำ symbol
  - จำกัดจำนวน position ต่อวัน
  - จำกัดจำนวน open paper positions รวม

Definition of done:

- auto-paper เปิดได้เฉพาะเมื่อผ่าน policy
- dashboard บอกเหตุผลได้ว่า signal ถูก skip เพราะอะไร

### Phase D: Calibration report แบบจริงจัง

เป้าหมาย:

ให้ dashboard ตอบได้ว่า source ไหนเริ่มน่าเชื่อถือ และควรใช้ใน regime ไหน

งานที่ต้องทำ:

- เพิ่ม metrics:
  - 5D / 20D / 60D win rate
  - average return
  - average R เมื่อมี stop
  - hit stop rate
  - hit target rate
  - MAE / MFE
  - score bucket calibration
  - regime-specific expectancy
- เพิ่ม dashboard sections:
  - Source Reliability
  - Score Bucket Calibration
  - Best/Worst Regime
  - Sample Confidence

Definition of done:

- sample < 30 แสดงเป็น `Collecting`
- sample 30-99 แสดงเป็น `Calibrating`
- sample >= 100 แสดงเป็น `Validated` หรือ `Needs Revision` ตามผลลัพธ์

### Phase E: Postmortem automation

เป้าหมาย:

ปิด loop จาก signal outcome ไปสู่ improvement backlog

งานที่ต้องทำ:

- สร้าง postmortem record เมื่อ:
  - signal ครบ 5D / 20D / 60D
  - paper trade ปิด
- บันทึก:
  - source
  - regime
  - outcome category
  - false positive / true positive
  - notes
- เชื่อมกับ `signal-postmortem`
- สร้าง feedback files สำหรับปรับ rule/weight

Definition of done:

- dashboard เห็น postmortem count > 0
- มี improvement backlog ที่อิงจาก performance จริง ไม่ใช่แค่ readiness

### Phase F: Rule improvement engine

เป้าหมาย:

ให้ระบบเสนอการปรับปรุงจากหลักฐานจริง

งานที่ต้องทำ:

- สร้าง rule suggestions:
  - reduce weight ใน regime ที่ false positive สูง
  - เพิ่ม min score
  - ลด/เพิ่ม stop pct
  - เปลี่ยน holding period
  - disable source ชั่วคราวถ้า edge decay
- ใส่ sample confidence:

```text
sample < 30: warning only
30 <= sample < 100: soft suggestion
sample >= 100: rule change candidate
```

Definition of done:

- suggestion ทุกอันมี evidence
- ไม่มี auto-adjust จาก sample เล็ก
- ผู้ใช้ approve ก่อนเปลี่ยน rule จริง

### Phase G: Scheduler / unattended mode

เป้าหมาย:

ให้ระบบทำงานเองตามเวลา

งานที่ต้องทำ:

- Windows batch เช่น `run_daily_pipeline.bat`
- optional Task Scheduler setup doc
- logging:
  - `logs/daily_signal_pipeline.log`
  - `reports/daily_signal_summary_YYYY-MM-DD.md`
- failure handling:
  - data fetch fail
  - API key missing
  - no eligible signals
  - DB locked

Definition of done:

- ผู้ใช้ไม่ต้องเปิด dashboard ทุกวัน
- วันไหนไม่มี signal ก็มี summary ว่าไม่มี เพราะอะไร

## สิ่งที่ยังไม่ควรทำตอนนี้

- ยังไม่ควร auto-buyเงินจริง
- ยังไม่ควรปรับ strategy weight อัตโนมัติจาก sample ต่ำ
- ยังไม่ควรเพิ่ม screener ใหม่จำนวนมากก่อน calibration แข็งแรง
- ยังไม่ควร treat win rate 5D เพียงอย่างเดียวเป็นคำตอบสุดท้าย

## ลำดับที่แนะนำต่อจากนี้

1. ทำ `run_daily_signal_pipeline.py`
2. เพิ่ม `automation_config.yaml`
3. ให้ fresh analysis export signal JSON มาตรฐาน
4. ให้ auto-paper execute ได้หลัง dry-run ผ่าน
5. เพิ่ม calibration dashboard แบบ score bucket / horizon / regime
6. เพิ่ม postmortem auto generation
7. เพิ่ม rule suggestion engine

## หลักการสำคัญ

ระบบนี้ควรเป็น autonomous research and paper-trading system ก่อน ไม่ใช่ auto-trading bot

เป้าหมายระยะใกล้:

```text
คุณติดงานได้
ระบบยังเก็บ signal ทุกวัน
ตามผลทุกตัว
เปิด paper เฉพาะตัวที่ผ่าน gate
สรุปว่า source ไหนเริ่มใช้ได้
แล้วเสนอ improvement จากหลักฐานจริง
```

## Implementation Update: 2026-07-01

งานที่ลงมือเพิ่มแล้ว:

- แก้ syntax error ใน `skills/macro-regime-detector/scripts/fmp_client.py` ที่ทำให้ pytest collection หยุด
- แก้ error handling ใน `skills/paper-trade-simulator/scripts/paper_trade.py`
  - ถ้า discipline warning check ล้มเหลว ระบบยังเปิด paper position ได้
  - เพิ่ม warning กลับไปในผลลัพธ์แทนการทำให้ flow ล้มทั้งก้อน
- เพิ่ม `scripts/run_daily_signal_pipeline.py`
  - optional analysis trigger ผ่าน dashboard API
  - ingest thesis เข้า signal ledger
  - update forward outcomes
  - run auto-paper แบบ dry-run หรือ execute ตาม config
  - export daily summary เป็น JSON และ Markdown
- เพิ่ม `state/automation_config.yaml`
  - default ปลอดภัย: `analysis.enabled=false`
  - default auto-paper เป็น dry-run: `auto_paper.execute=false`
- เพิ่ม `scripts/tests/test_daily_signal_pipeline.py`
- ปรับ `scripts/signal_ledger.py` ให้ update outcomes ไม่ล้มเมื่อ DB ใหม่ยังไม่มี `price_bar`

คำสั่ง daily pipeline:

```powershell
uv run python scripts\run_daily_signal_pipeline.py --config state\automation_config.yaml --market TH
```

ถ้าต้องการระบุวันทดสอบ:

```powershell
uv run python scripts\run_daily_signal_pipeline.py --config state\automation_config.yaml --market TH --as-of 2026-07-01
```

ผล dry-run ล่าสุด:

```text
Ingest: 28 total, 0 inserted, 28 updated
Outcomes updated: 84
Complete outcomes: 38
Auto-paper eligible: 0
Auto-paper opened: 0
Dry-run: true
```

รายงานถูกสร้างที่:

```text
reports/daily-signal-pipeline/daily_signal_pipeline_2026-07-01.json
reports/daily-signal-pipeline/daily_signal_pipeline_2026-07-01.md
```

Verification ล่าสุด:

```text
21 passed
ruff: all checks passed for touched files
py_compile: passed for touched Python files
```

หมายเหตุ:

`uv run pytest -q` ทั้ง repo ยังไม่ green ทั้งหมด มี failure เดิมจำนวนมากใน skill อื่น ๆ และ encoding issue บน Windows test บางชุด ดังนั้นตอนนี้ถือว่า verified เฉพาะระบบที่แก้/เพิ่มในรอบนี้ก่อน

## Implementation Update: Canonical Signal Ingest

งานที่ลงมือเพิ่มแล้ว:

- เพิ่ม source normalization:
  - `vcp` → `vcp-screener`
  - `vcp_screener` → `vcp-screener`
  - `canslim` / `canslim_screener` → `canslim-screener`
  - `thai_swing_dip` → `thai-swing-dip`
  - `thai_swing_momentum` → `thai-swing-momentum`
- เพิ่ม canonical signal JSON ingest ใน `scripts/signal_ledger.py`
  - รองรับ `signals[]` schema กลาง
  - รองรับ fallback จาก report เดิม:
    - `reports/vcp_screener_*.json`
    - `reports/canslim_screener_*.json`
    - `reports/thai_swing_*.json`
  - ดึง `entry/stop/target` จาก `plan` ของ Thai swing ได้
- เพิ่มคำสั่ง:

```powershell
uv run python scripts\signal_ledger.py ingest-signals reports\thai_swing_2026-07-01_171537.json
```

- ต่อ daily pipeline ให้ ingest signal files จาก config:

```yaml
signal_files:
  enabled: true
  patterns:
    - state/signals/*.json
    - state/signals/*.yaml
    - reports/vcp_screener_*.json
    - reports/canslim_screener_*.json
    - reports/thai_swing_*.json
  max_files_per_pattern: 3
```

ผล dry-run ล่าสุดหลัง ingest signal files:

```text
Ledger signals: 82
canslim-screener: 40
vcp-screener: 28
thai-swing-momentum: 12
thai-swing-dip: 2
Auto-paper eligible: 3
Auto-paper opened: 0
```

Auto-paper candidates ล่าสุด:

```text
EASTW.BK  thai-swing-momentum  score 80.2  entry 4.60  stop 4.37  target 5.05
AH.BK     thai-swing-dip       score 79.3  entry 13.90 stop 13.59 target 14.52
INET.BK   thai-swing-momentum  score 72.8  entry 4.26  stop 4.08  target 4.62
```

Dashboard API verified:

```text
paper_sources: thai-swing-dip, vcp-screener
source_readiness rows: canslim-screener, thai-swing-dip, thai-swing-momentum, vcp-screener
```

Verification:

```text
22 passed
ruff: all checks passed for touched files
py_compile: passed
dashboard API: eligible=3 and vcp source normalized
```

## Implementation Update: GCP Online Automation

งานที่ลงมือเพิ่มแล้ว:

- เพิ่ม `scripts/run_gcp_daily_pipeline.sh`
  - wrapper สำหรับ cron/systemd บน GCP VM
  - รัน `scripts/run_daily_signal_pipeline.py`
  - เขียน log แยกตาม market:
    - `logs/daily_signal_pipeline_TH.log`
    - `logs/daily_signal_pipeline_US.log`
  - ใช้ lock file ผ่าน `flock` ถ้ามี เพื่อกัน pipeline รันซ้อน
- เขียน `scripts/setup_gcp_cron.sh` ใหม่เป็น ASCII ทั้งไฟล์
  - แก้ปัญหาอักขระเพี้ยนเดิม
  - คง dashboard scan jobs เดิม
  - เพิ่ม signal pipeline follow-up jobs หลัง scan
- อัปเดต `.github/workflows/deploy.yml`
  - หลัง push เข้า `main` แล้ว deploy ไป GCP VM จะ:
    1. `git pull origin main`
    2. `uv sync`
    3. สร้าง `logs/`, `reports/daily-signal-pipeline/`, `state/`
    4. `chmod +x` automation scripts
    5. รัน `bash scripts/setup_gcp_cron.sh`
    6. restart `dashboard.service`
- เพิ่มเอกสาร `GCP_ONLINE_UPDATE.md`

Cron schedule ที่ตั้งไว้:

```text
TH scan:      10:15, 16:15 Mon-Fri
TH pipeline:  10:45, 16:45 Mon-Fri
US scan:      20:30 Mon-Fri
US pipeline:  21:00 Mon-Fri
```

คำสั่งตรวจบน GCP VM หลัง push:

```bash
cd ~/tong_trading
crontab -l
sudo systemctl status dashboard.service
bash scripts/run_gcp_daily_pipeline.sh TH
tail -n 80 logs/daily_signal_pipeline_TH.log
```

หมายเหตุ:

ผมตรวจ live GCP VM จากเครื่องนี้ไม่ได้ เพราะไม่มี SSH credentials / GitHub secrets ใน workspace นี้ ต้องดูผลจริงหลัง push ผ่าน GitHub Actions และ log บน VM

## Implementation Update: GCP Deploy Fix

Observed live GitHub Actions failure:

- `cd ~/tong_trading` failed because that path did not exist on the VM.
- `uv` was not available in the SSH PATH after the failed `cd`.
- `dashboard.service` did not exist yet.

Fix added:

- `.github/workflows/deploy.yml` now stops on the first deployment error.
- It resolves the project directory from:
  1. `GCP_PROJECT_DIR` secret
  2. `~/tong_trading`
  3. `~/claude-trading-skills-1`
  4. `~/claude-trading-skills`
- If no checkout exists, it clones the repo into `~/claude-trading-skills-1`.
- It installs `uv` on the VM if missing.
- It creates `dashboard.service` if missing, then restarts it.
- Optional service override: `GCP_DASHBOARD_SERVICE`.

This should allow a fresh or partially configured GCP VM to become usable after a push to `main`.

## Implementation Update: Cron Timezone Fix

Cron setup now installs the trading automation inside a managed block:

- `CRON_TZ=Asia/Bangkok`
- old unmanaged TH/US automation lines are removed before writing the new block
- future deploys replace the managed block instead of adding duplicate jobs

Current scheduled times are Bangkok time:

```text
TH scan:      10:15, 16:15 Mon-Fri
TH pipeline:  10:45, 16:45 Mon-Fri
US scan:      20:30 Mon-Fri
US pipeline:  21:00 Mon-Fri
```

## Implementation Update: Result Diagnostics

Added dashboard diagnostics for the next improvement loop:

- Signal Results now includes a Freshness Monitor.
  - Shows latest report file per source.
  - Marks reports as fresh, aging, stale, or missing.
- Signal Results now includes VCP Near Miss.
  - Shows the VCP funnel.
  - New VCP reports include `near_misses[]` with reasons such as not enough contractions, volume not dry enough, pivot distance, high risk, or bad execution state.
  - Old VCP reports show a rerun note because they were generated before near-miss diagnostics existed.
- Signal Results now includes Auto-paper Gate.
  - Shows selected candidates.
  - Shows skipped candidates and reasons such as score below threshold, stale signal, already linked/open, invalid risk, or ranked below `max_new_positions`.

Verification:

```text
pytest: scripts/tests/test_auto_paper.py + skills/vcp-screener/scripts/tests/test_vcp_screener.py passed
ruff: touched Python files passed
py_compile: dashboard/app.py, auto_paper.py, screen_vcp.py, report_generator.py passed
node --check: dashboard/static/js/app.js passed
browser: Signal Results panels rendered on desktop and mobile; mobile width matched viewport
```

## Implementation Update: Manual Run Signal Follow-up

The dashboard Run Fresh Analysis flow now runs the daily signal follow-up immediately after a scan:

- `/api/run` and `/api/run/stream` both call the daily signal pipeline after the primary screeners finish.
- The follow-up updates the signal ledger, completed outcomes, auto-paper eligibility, and daily pipeline report.
- Signal Results refreshes after manual runs so the dashboard does not keep showing stale pipeline diagnostics.
- The scan result includes a `signal_pipeline` summary with counts for total signals, completed signals, auto-paper eligible names, and opened positions.

This makes a manual Run behave more like the scheduled automation. If the scheduled cron misses a run, pressing Run from the dashboard should now refresh both the raw scans and the downstream decision result.

## Implementation Update: GCP Dashboard Version Guard

The public GCP dashboard served updated static assets while backend routes could still come from an older Flask process. Deployment now guards against that mismatch:

- `/api/health` returns the running dashboard commit and feature flags.
- GCP deploy rewrites `dashboard.service` on every deployment instead of keeping an old unit file.
- GCP deploy clears stale listeners on port `5050` before starting the managed service.
- GCP deploy resets the VM checkout to `origin/main`, so deployment recovers cleanly even after a force-updated branch.
- GCP deploy now runs the managed dashboard on public port `80`; local development still defaults to `5050`.
- GCP cron uses the same local dashboard URL that the managed service exposes.
- GCP deploy writes `dashboard.service` via a temporary unit file to avoid SSH wrapper heredoc pollution.
- GCP deploy now removes stale Python listeners on ports `80` and `5050` using both `fuser` and `ss` PID detection.
- GCP deploy fails if `/api/health` does not report the pushed commit.
- GCP deploy also checks `/api/signal-results?market=TH` before marking the workflow successful.

Verification after deploy:

```text
public health: http://35.212.209.201/api/health returned commit 1634931
public signal results: /api/signal-results?market=TH returned successfully
latest deploy workflow: completed successfully
```

## Implementation Update: Trading Guide UI Cleanup

The top Trading Decision Guide now behaves as a progressive-disclosure panel:

- Default state is hidden, because the guide is reference material and does not need to be read on every visit.
- The toggle button now uses clear text: `แสดงคู่มือ` / `ซ่อนคู่มือ`.
- The glossary table wraps long Thai/English descriptions instead of creating a horizontal scrollbar.
- On narrow screens, glossary rows stack into block-style sections so text stays within the viewport.
- The toggle uses `aria-expanded` for clearer keyboard/screen-reader state.

Verification:

```text
node --check: dashboard/static/js/app.js passed
pre-commit: touched UI files passed
browser desktop: guide hidden by default; no horizontal overflow when opened
browser mobile viewport: glossary stacks and no horizontal overflow
GCP deploy: public health returned commit 1634931
```

## Current GCP Schedule Status

GCP automation is installed in cron with `CRON_TZ=Asia/Bangkok` and points to the managed dashboard on `127.0.0.1:80`.

Current scheduled times:

```text
TH scan:       10:15, 16:15 Mon-Fri
TH pipeline:   10:45, 16:45 Mon-Fri
US scan:       20:30 Mon-Fri
US pipeline:   21:00 Mon-Fri
```

Latest deploy log confirmed:

```text
Cron jobs successfully installed or updated.
Dashboard health check passed for commit 1634931.
```

## Implementation Update: Auto-paper Execution Enabled

Observed on 2026-07-04:

- GCP schedule did run on Friday 2026-07-03.
  - TH scan reports existed around 16:17-16:20.
  - Daily signal pipeline existed at 21:00.
- The system looked inactive because `auto_paper.execute` was still `false`.
  - Signal Results showed eligible candidates.
  - Paper portfolio still had zero open positions because the pipeline was in dry-run mode.

Change:

- `state/automation_config.yaml` now sets `auto_paper.execute: true`.
- This still affects paper portfolio only, not real-money trading.
- Future scheduled pipeline runs should open eligible paper positions automatically, subject to:
  - `min_score: 70`
  - `max_age_days: 10`
  - `max_new_positions: 3`
  - duplicate/open-position guards in the auto-paper module

Current eligible candidates from the latest public dashboard check:

```text
ASEFA.BK   score 88.9  source thai-swing-dip       signal date 2026-07-02
VAYU1.BK   score 84.8  source thai-swing-momentum  signal date 2026-07-03
EPG.BK     score 80.9  source thai-swing-momentum  signal date 2026-07-03
```

## Implementation Update: Schedule and Signal Follow-up Hardening (2026-07-04)

What was found after the latest GCP check:

- The schedule was not completely broken: reports from Friday 2026-07-03 existed, and Saturday 2026-07-04 is outside the normal Mon-Fri cron window.
- A manual GCP run on 2026-07-04 generated fresh reports and opened simulated paper positions.
- Public paper stats then showed 3 open paper trades.
- One issue was found in the first execute run: `VAYU1.BK` opened twice because two different signal dates for the same symbol passed the gate in the same batch.
- The scan cron used silent `curl` calls, so a long run or failure was hard to diagnose.
- Open paper positions also needed an automated mark update after scans, otherwise the positions looked static until a manual update.

Changes made:

- `scripts/auto_paper.py` now reserves each symbol as soon as it is selected, preventing duplicate same-symbol paper positions within one batch.
- `scripts/tests/test_auto_paper.py` now covers same-symbol duplicate signals.
- `dashboard/app.py` Signal Results now reads `state/automation_config.yaml`, so it reports `execute: true` and `dry_run: false` correctly.
- Signal recommendations now recognize that paper positions may already be open and waiting for outcomes.
- `scripts/setup_gcp_cron.sh` now:
  - logs TH scans to `logs/gcp_scan_TH.log`
  - logs US scans to `logs/gcp_scan_US.log`
  - applies a 45-minute scan timeout with a curl max-time guard
  - uses scan locks to avoid overlapping runs
  - calls `/api/paper/update_marks` after scans and logs it to `logs/gcp_paper_marks.log`

Verification:

```text
uv run pytest scripts\tests\test_auto_paper.py scripts\tests\test_daily_signal_pipeline.py scripts\tests\test_signal_ledger.py -q
15 passed

Local /api/signal-results?market=TH returned 200.
Signal Results config showed execute=true and dry_run=false.
scripts/setup_gcp_cron.sh passed shell syntax check with Git Bash.
```

Important note:

- The existing duplicate `VAYU1.BK` paper record came from the old logic before this fix.
- The new code prevents future duplicates, but the already-open duplicate was left in paper history rather than closed automatically.

Deploy verification:

- GCP deploy succeeded after adding stale dashboard process cleanup to `.github/workflows/deploy.yml`.
- Public health check returned commit `426c1e7`.
- Public Signal Results returned `execute: true`, `dry_run: false`, `auto_eligible: 3`, and `paper_open: 3`.
- Current next eligible paper candidates after the duplicate guard are:
  - `EPG.BK`
  - `SEAFCO.BK`
  - `TMD.BK`

## Implementation Update: Edge Lab Dashboard (2026-07-06)

Reason:

- The trading system needed a clearer way to decide what to improve next.
- Opening logic should not be loosened only because few trades fire; rule changes need outcome evidence.
- VCP currently has many scanned candidates, but the latest top near-miss still did not pass the hard entry gate.

Change:

- Added a new dashboard tab: `Edge Lab`.
- The tab uses existing system data from Signal Results and Paper Portfolio to show:
  - source-level calibration readiness
  - paper trades, closed outcomes, win rate, and expectancy by source
  - score-bucket performance
  - VCP gate funnel and top near-miss reasons
  - current open-risk budget
  - suggested next rule tests

Current local finding after implementation:

- Closed sample is still early: `3/30`.
- Sources with paper evidence: `2/4`.
- Best current source from closed sample: `Thai Swing Dip`.
- Latest VCP top near-miss score: `67.0`, below the current `70` auto-open gate.
- Suggested next step is to keep rule changes in paper mode until at least 30 closed outcomes exist.

Verification:

```text
node --check dashboard/static/js/app.js
git diff --check

Local browser check:
- Edge Lab tab rendered.
- Source Calibration rendered 4 rows.
- Score Bucket Calibration rendered 2 rows.
- VCP Gate Lab rendered top near-miss details.
- Browser console showed no page errors.
```

## Implementation Update: Paper Risk Controls for Short Holding (2026-07-08)

Reason:

- Public paper results showed the system was collecting data, but open positions grew too quickly.
- The prior auto-close logic mainly waited for stop or full 2R target.
- Thai short-swing targets, especially momentum names, were often too far for fast capital rotation.

Changes:

- Added `closed_time` as a paper-trade exit status.
- Added source-specific paper exit rules in `update_marks.py`:
  - short profit target by R multiple
  - maximum holding days
  - time stop when a trade has not made enough progress
- Added source-specific auto-paper entry risk rules:
  - Thai Swing Dip: target `1.0R`, stop cap `2.5%`
  - Thai Swing Momentum: target `0.9R`, stop cap `4.0%`
  - VCP: target `1.5R`, stop cap `5.0%`
- Changed auto-paper from a hard open-position cap to a soft-cap model:
  - normal open cap: `5`
  - high-score override: score `85+`
  - high-score open cap: `8`
- Reduced new paper entries per run from `3` to `2`.
- Dashboard Signal Results now exposes the new cap and source-rule config.

Design note:

- This is still paper trading only.
- The soft cap avoids locking too much capital, while still allowing unusually strong signals to enter.
- Existing open positions are evaluated by the new exit rules the next time `/api/paper/update_marks` runs.

Verification:

```text
python -m pytest scripts/tests/test_auto_paper.py skills/paper-trade-simulator/scripts/tests/test_paper_trade.py -q
19 passed

python -m pytest scripts/tests/test_daily_signal_pipeline.py -q
4 passed

node --check dashboard/static/js/app.js
```

## GCP Update: Soft Cap Applied and Paper Marks Refreshed (2026-07-08)

What changed after deployment:

- GCP dashboard is running commit `3f5e609`.
- Auto-paper config now uses:
  - normal open cap: `5`
  - high-score override: score `85+`
  - override open cap: `8`
  - max new positions per run: `2`
- This means the system does not block every new trade after the normal cap. It only lets a new trade through above the cap when the signal score is materially stronger.

Live paper mark refresh:

- Ran `/api/paper/update_marks` on GCP after the new exit rules were deployed.
- Result:
  - `1` position closed by short profit target at `1R`.
  - `3` positions closed by time stop.
  - open positions reduced from `15` to `11`.
- Updated stats after refresh:
  - total trades: `17`
  - closed trades: `6`
  - open positions: `11`
  - win rate: `33.3%`
  - expectancy: `+0.155R`
  - realized R: `+0.93R`

Current interpretation:

- The `85+` score bucket is still much better than the `70-84` bucket on the current sample.
- Keeping a soft cap is better than a hard cap: it preserves capital discipline while still allowing unusually strong opportunities to enter.
- The next improvement should be a ranking / replacement rule: if a new signal is stronger than an existing weak open position, the dashboard should show which current position should be reviewed or rotated out first.

Deployment reliability note:

- The deploy workflow briefly failed because an old dashboard process on port `80` answered the health check with an older commit.
- Added a one-time health-check recovery step that recycles stale listeners and restarts the dashboard if the deployed commit does not match.
- Extended the deploy health window to allow the dashboard enough time to finish startup before the workflow marks deployment as failed.

## Result Check: TH Paper Portfolio After 2026-07-09 Refresh

Observed on GCP:

- Dashboard health: OK on commit `9694ffd`.
- Latest TH reports were generated on `2026-07-09`.
- VCP scan ran and produced:
  - universe: `100`
  - pre-filter passed: `44`
  - trend-template passed: `30`
  - VCP candidates: `29`
  - no entry-ready VCP candidates yet
- Top VCP near-miss:
  - `SCGP.BK`, composite score `68.2`
  - rejected because pivot distance was `+7.6%` and state was `Extended`

Paper portfolio after manually refreshing marks:

- total trades: `17`
- closed trades: `10`
- open positions: `7`
- wins / losses: `4 / 6`
- win rate: `40.0%`
- realized R: `+3.41R`
- expectancy: `+0.341R`
- realized P/L: `+76 THB`
- unrealized P/L: `+43 THB`

New closes from the refresh:

- `BKGI.BK`: closed by time stop, `-0.40R`
- `MGC.BK`: closed by time stop, `-0.12R`
- `SMT.BK`: closed at target, `+2.00R`
- `AMATA.BK`: closed at short profit target, `+1.00R`

Current interpretation:

- Thai Swing Dip is currently stronger than Thai Swing Momentum:
  - Thai Swing Dip expectancy: `+0.755R`
  - Thai Swing Momentum expectancy: `-0.074R`
- Score bucket `85+` remains much stronger than `70-84`:
  - `85+` expectancy: `+1.55R`
  - `70-84` expectancy: `+0.039R`
- The system found `WHAUP.BK` as a new high-score candidate:
  - source: `thai-swing-momentum`
  - score: `87.0`
  - entry: `7.50`
  - stop: `7.20`
  - target: `7.77`

Automation issue found:

- The GCP evening pipeline ran before the mark refresh had freed old positions.
- Because of that order, new high-score candidate `WHAUP.BK` was blocked by capacity at pipeline time, then became eligible after marks were refreshed.

Fix:

- Updated `scripts/run_gcp_daily_pipeline.sh` so every scheduled pipeline refreshes paper marks before auto-paper selection.
- The refresh is best-effort: if mark refresh fails, it logs a warning and still runs the pipeline.
- This should prevent the system from missing a stronger new candidate simply because stale open positions had not been closed yet.

Deployment follow-up:

- The first deploy attempt for this fix failed before service restart because the GCP VM could not fetch the private GitHub repo over HTTPS without credentials.
- Updated the deploy workflow to fetch with the GitHub Actions token for that command only, while keeping the VM's stored `origin` URL credential-free.

## Execution Integrity Upgrade: Conservative TH Paper Validation (2026-07-10)

Reason:

- The first positive paper results were too early to prove an edge: only 10 closed trades existed.
- The simulator could open a Thai paper position after the regular market session using a stale signal price.
- Some paper entry, stop, and target prices did not conform to SET tick sizes.
- Existing results did not include an estimate for round-trip execution cost.

Changes:

- Auto-paper now permits a new Thai entry only during the normal SET trading sessions and only for a same-day signal.
- Thai entry prices round up to the next valid SET tick; stop and target prices round down to valid ticks.
- New paper trades record a configurable per-side transaction-cost estimate. The TH automation default is 15 bps per side, covering a conservative combined allowance for commission, VAT, spread, and slippage. Historic records retain zero cost so the audit trail is unchanged.
- Paper exit records now retain gross P/L, entry cost, exit cost, and net P/L / R.
- Entry policy is now more selective while the sample matures:
  - Thai Swing Dip: signal age no more than 1 day.
  - Thai Swing Momentum: score at least 85 and signal age 0 days.
  - General auto-paper signal age: no more than 2 days.

Interpretation:

- This deliberately reduces trade count. It is a validation control, not an attempt to make the backtest look better.
- Existing duplicate VAYU1 records are retained as historical audit data and will be handled in the separate portfolio-cleanup / replacement phase.
- The system remains paper-only. Do not use the current sample as evidence to enable real-money execution.

Verification:

```text
27 passed
scripts/tests/test_auto_paper.py
skills/paper-trade-simulator/scripts/tests/test_paper_trade.py
scripts/tests/test_daily_signal_pipeline.py
```

## Portfolio Risk Sizing and Replacement Review (2026-07-10)

Reason:

- The former fixed quantity of 100 shares did not make the risk of each paper trade comparable.
- A simple position-count cap could block a stronger new signal without showing which open position should be reconsidered.

Changes:

- Auto-paper now sizes new positions from a configurable paper account:
  - account size: THB `100,000`
  - risk per trade: `0.5%`
  - maximum position value: `10%`
  - maximum combined portfolio heat: `2%`
  - board-lot rounding: `100` shares
- A candidate is skipped when the risk budget cannot fund one board lot or when its initial risk would exceed the portfolio heat budget.
- Each candidate now records planned shares, initial risk, position value, and risk percent of the paper account.
- Signal Results now includes a read-only `Replacement Review` panel.
  - It appears only when normal capacity blocks a candidate that is at least 10 score points stronger than a weak open position.
  - It identifies the candidate and the position to review, but never auto-closes any paper trade.

Design note:

- These values are paper-account defaults, not a recommendation for real capital. They are stored in `state/automation_config.yaml` and can be changed before the next validation cycle.
- This change improves risk comparability and capital rotation without adding any real-money execution path.

Verification:

```text
30 passed
scripts/tests/test_auto_paper.py
scripts/tests/test_daily_signal_pipeline.py
skills/paper-trade-simulator/scripts/tests/test_paper_trade.py
```

## InnovestX Paper-Validation Profile And Online Dashboard (2026-07-13)

Changes:

- Replaced the conservative validation profile with an explicit TH paper-account profile:
  - account size: THB `30,000`
  - risk per trade: `1%` (`THB 300`)
  - maximum position value: `20%` (`THB 6,000`)
  - maximum combined portfolio heat: `3%` (`THB 900`)
  - maximum new/open positions: `4`
- Added the InnovestX cash-balance fee model to `state/automation_config.yaml`:
  - commission: `0.15%`
  - trading fee: `0.005%`
  - clearing fee: `0.001%`
  - VAT: `7%` on broker fees
  - estimated slippage: `5 bps` (paper-trading assumption)
  - effective estimated cost: `21.692 bps` per side
- Updated the dashboard Signal Results endpoint to expose the fee model and use the configured effective transaction cost.
- Deployed the profile and dashboard update to the GCP VM. The public health endpoint reports commit `a622f45`.

Safety:

- This remains paper trading only. `execute: true` enables the paper simulator; it does not connect to InnovestX or submit real orders.
- Existing signal/outcome records are retained. A deployment does not create fresh signals automatically; the scheduled pipeline must run before new candidates appear.

Verification:

```text
32 passed, 1 time-sensitive session test deselected
scripts/tests/test_fee_model.py
scripts/tests/test_daily_signal_pipeline.py
scripts/tests/test_auto_paper.py
skills/paper-trade-simulator/scripts/tests/test_paper_trade.py
```
