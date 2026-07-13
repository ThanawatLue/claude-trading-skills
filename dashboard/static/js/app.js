const LEGENDS = {
  breadth: {
    title: '📊 คู่มือ: Market Breadth Score',
    html: `<div class="legend-section">
      <h3>คะแนนสุขภาพตลาด (0–100)</h3>
      <div class="legend-row"><div class="legend-symbol" style="color:#00e676">🟢 80-100</div><div class="legend-desc"><strong>Strong</strong> — แข็งแรงมาก ซื้อได้เต็มที่</div></div>
      <div class="legend-row"><div class="legend-symbol" style="color:#8bc34a">🟢 60-79</div><div class="legend-desc"><strong>Healthy</strong> — ตลาดดี เดินหน้าต่อ</div></div>
      <div class="legend-row"><div class="legend-symbol" style="color:#ffd700">🟡 40-59</div><div class="legend-desc"><strong>Neutral</strong> — ไม่ชัดเจน เลือกหุ้นมากขึ้น</div></div>
      <div class="legend-row"><div class="legend-symbol" style="color:#ff9800">🟠 20-39</div><div class="legend-desc"><strong>Weakening</strong> — ตลาดอ่อน ลดความเสี่ยง</div></div>
      <div class="legend-row"><div class="legend-symbol" style="color:#f44336">🔴 0-19</div><div class="legend-desc"><strong>Critical</strong> — อันตราย ⛔ อย่าซื้อเพิ่ม</div></div>
      <h3 style="margin-top:12px">Theory: Stan Weinstein's Stage Analysis</h3>
      <p style="font-size:.8rem;color:var(--muted)">วิเคราะห์สุขภาพตลาดโดยดูจาก "จำนวนหุ้นที่เต้นระบำตามตลาด" ไม่ใช่แค่ดัชนีเดียว</p>
      <div class="legend-row"><div class="legend-symbol">High Score</div><div class="legend-desc">ตลาดอยู่ใน Stage 2 (ขาขึ้น) หุ้นส่วนใหญ่มีส่วนร่วม — เทรดได้เต็มที่</div></div>
      <div class="legend-row"><div class="legend-symbol">Low Score</div><div class="legend-desc">ตลาดอยู่ใน Stage 4 (ขาลง) หรือเปราะบาง — ควรลดพอร์ตหรือถือเงินสด</div></div>
      <div class="legend-row"><div class="legend-symbol">Components</div><div class="legend-desc">ดู % หุ้นเหนือเส้น SMA 200, 150, 50 วัน และ Advance-Decline Line</div></div>
    </div>`
  },
  uptrend: {
    title: '📈 คู่มือ: Uptrend Ratio Score',
    html: `<div class="legend-section">
      <h3>Uptrend Analyzer วัดอะไร?</h3>
      <div class="legend-desc" style="margin-bottom:12px">วัดว่า % ของหุ้นในตลาดที่อยู่ใน uptrend จริงๆ — ต่างจาก Breadth ที่วัด MA crossing</div>
      <h3>Zone</h3>
      <div class="legend-row"><div class="legend-symbol"><span class="zone-StrongBull">Strong Bull</span></div><div class="legend-desc">80%+ ของหุ้นอยู่ใน uptrend — ซื้อเต็มที่</div></div>
      <div class="legend-row"><div class="legend-symbol"><span class="zone-Bull">Bull</span></div><div class="legend-desc">ตลาดขาขึ้นกว้าง — เปิด position ใหม่ได้</div></div>
      <div class="legend-row"><div class="legend-symbol"><span class="zone-Neutral">Neutral</span></div><div class="legend-desc">ตลาดผสม — เลือกเฉพาะหุ้นแข็งแกร่ง</div></div>
      <div class="legend-row"><div class="legend-symbol"><span class="zone-Cautious">Cautious</span></div><div class="legend-desc">ตลาดอ่อนแอ — ลด size ลง</div></div>
      <div class="legend-row"><div class="legend-symbol"><span class="zone-Bear">Bear</span></div><div class="legend-desc">ขาลง — ถือเงินสด</div></div>
    </div>`
  },
  ibd: {
    title: '📉 คู่มือ: IBD Distribution Day Monitor',
    html: `<div class="legend-section">
      <h3>Distribution Day คืออะไร?</h3>
      <div class="legend-desc">วันที่ดัชนีปิดลดลง ≥0.2% พร้อมปริมาณสูงกว่าวันก่อน — สัญญาณ Institutional Selling</div>
      <h3 style="margin-top:12px">ระดับความเสี่ยง</h3>
      <div class="legend-row"><div class="legend-symbol"><span class="risk-NORMAL">NORMAL</span></div><div class="legend-desc">DD น้อย ตลาดปกติ</div></div>
      <div class="legend-row"><div class="legend-symbol"><span class="risk-CAUTION">CAUTION</span></div><div class="legend-desc">เริ่มระวัง ลด position size</div></div>
      <div class="legend-row"><div class="legend-symbol"><span class="risk-HIGH">HIGH</span></div><div class="legend-desc">หยุดซื้อใหม่ เพิ่มเงินสด</div></div>
      <div class="legend-row"><div class="legend-symbol"><span class="risk-SEVERE">SEVERE</span></div><div class="legend-desc">ขายออก รอ Follow-Through Day</div></div>
      <h3 style="margin-top:12px">Theory: William O'Neil's Distribution Days</h3>
      <p style="font-size:.8rem;color:var(--muted)">ตรวจจับ "รอยเท้าของรายใหญ่" ผ่านดัชนี (S&P500 / NASDAQ)</p>
      <div class="legend-row"><div class="legend-symbol">Distribution Day</div><div class="legend-desc">วันที่ดัชนีปิดลบพร้อมวอลุ่มสูงกว่าวันก่อน — รายใหญ่เริ่มทิ้งของ</div></div>
      <div class="legend-row"><div class="legend-symbol">DD Count</div><div class="legend-desc">สะสมเกิน 5-6 วันในช่วงสั้นๆ = สัญญาณจบคะแนนขาขึ้น (Market Top)</div></div>
    </div>`
  },
  exposure: {
    title: '🛡️ คู่มือ: Exposure Coach',
    html: `<div class="legend-section">
      <h3>Theory: Progressive Exposure (Minervini)</h3>
      <p style="font-size:.8rem;color:var(--muted)">"ความเสี่ยงมาก่อนกำไรเสมอ" — ปรับขนาดพอร์ตตามความง่ายของตลาด</p>
      <div class="legend-row"><div class="legend-symbol" style="color:var(--red)">CASH_PRIORITY</div><div class="legend-desc">ตลาดอันตราย ⛔ ถือเงินสดไว้ก่อน ไม่ควรซื้อ (composite &lt; 30)</div></div>
      <div class="legend-row"><div class="legend-symbol" style="color:var(--red)">REDUCE_ONLY</div><div class="legend-desc">ตลาดเสี่ยงสูง ให้ขายหุ้นที่เริ่มเสียทรง ห้ามซื้อเพิ่ม (composite &lt; 50)</div></div>
      <div class="legend-row"><div class="legend-symbol" style="color:var(--green)">NEW_ENTRY_ALLOWED</div><div class="legend-desc">ตลาดเป็นใจ ให้ขยายฐานการลงทุนได้ตาม Exposure Ceiling (composite ≥ 50)</div></div>
    </div>`
  },
  vcp: {
    title: '🔍 คู่มือ: VCP & SEPA Strategy',
    html: `<div class="legend-section">
      <h3>Theory: Mark Minervini's VCP Pattern</h3>
      <p style="font-size:.8rem;color:var(--muted)">ค้นหา "หุ้นที่มีพลังแฝง" ผ่านการบีบตัวของราคา (Volatility Contraction)</p>
      <div class="legend-row"><div class="legend-symbol">Trend Template</div><div class="legend-desc">หุ้นต้องเป็นขาขึ้น Stage 2 (SMA เรียงตัวสวย) ก่อนสแกน</div></div>
      <div class="legend-row"><div class="legend-symbol">Contractions</div><div class="legend-desc">การบีบตัวของราคา (T1, T2, T3) ที่แคบลงเรื่อยๆ พร้อมวอลุ่มแห้งสนิท</div></div>
      <div class="legend-row"><div class="legend-symbol">Pivot Point</div><div class="legend-desc">จุดตัดสินใจที่ราคาจะ "ระเบิด" (Breakout) ออกจากฐานราคาที่แคบที่สุด</div></div>

      <h3 style="margin-top:12px">State ของหุ้น (Execution State)</h3>
      <div class="legend-row"><div class="legend-symbol"><span class="state-pill bg-green">Pre-breakout</span></div><div class="legend-desc">กำลังสะสมพลัง ใกล้ Pivot — น่าสนใจที่สุด</div></div>
      <div class="legend-row"><div class="legend-symbol"><span class="state-pill bg-green">Breakout</span></div><div class="legend-desc">ผ่าน Pivot แล้ว — ยังเป็นโอกาสถ้าไม่เกิน 5% จากจุดซื้อ</div></div>
      <div class="legend-row"><div class="legend-symbol"><span class="state-pill bg-orange">Extended</span></div><div class="legend-desc">ขึ้นมาแล้ว (5-10%) — เสี่ยงถ้าจะไล่ราคา รอ Pullback</div></div>
      <div class="legend-row"><div class="legend-symbol"><span class="state-pill bg-red">Overextended</span></div><div class="legend-desc">ราคาห่างจากเส้นค่าเฉลี่ยมากเกินไป (>50% จาก SMA200) — ห้ามซื้อเด็ดขาด</div></div>
      <div class="legend-row"><div class="legend-symbol"><span class="state-pill bg-red">Damaged</span></div><div class="legend-desc">Pattern เสียหาย หรือหลุดแนวรับสำคัญ — หลีกเลี่ยง</div></div>

      <h3 style="margin-top:12px">Dynamic Pattern Stats</h3>
      <div class="legend-row"><div class="legend-symbol" style="color:var(--cyan)">Context-Aware</div><div class="legend-desc">สแกนแพทเทิร์นล่าสุด (Breakout, Volume Climax ฯลฯ) แล้วคำนวณ <strong>Win Rate</strong> ถ้ายอมถือข้ามวัน</div></div>
      <div class="legend-row"><div class="legend-symbol" style="color:var(--green)">Win Rate &gt;60%</div><div class="legend-desc">โอกาสชนะสูง ให้ <strong>ถือข้ามวัน (Hold/Buy ATC)</strong></div></div>
      <div class="legend-row"><div class="legend-symbol" style="color:var(--red)">Win Rate ต่ำ</div><div class="legend-desc">แนวโน้มไม่ดี ให้ <strong>ชิงขายทำกำไร หรือ ชะลอการซื้อ</strong></div></div>
    </div>`
  },
  breakout: {
    title: '🎯 คู่มือ: Breakout Trade Plan',
    html: `<div class="legend-section">
      <h3>Theory: Van Tharp's R-Multiple & Risk Management</h3>
      <div class="legend-row"><div class="legend-symbol">Signal Entry</div><div class="legend-desc">จุดเข้าซื้อที่ดีที่สุด (Pivot + 0.1%)</div></div>
      <div class="legend-row"><div class="legend-symbol">Stop Loss</div><div class="legend-desc">จุดที่ทฤษฎีผิดทาง (Natural Low) — ห้ามฝืนถือ</div></div>
      <div class="legend-row"><div class="legend-symbol">Target (2R)</div><div class="legend-desc">เป้าหมายกำไรขั้นต่ำ (ต้องเป็น 2 เท่าของความเสี่ยงเพื่อให้กำไรสุทธิเป็นบวก)</div></div>
      <div class="legend-row"><div class="legend-symbol">Position Size</div><div class="legend-desc">คำนวณจำนวนหุ้นให้เสียเงินไม่เกิน X% ของพอร์ตหากผิดทาง</div></div>
    </div>`
  },
  downtrend: {
    title: '⏱️ คู่มือ: Downtrend Duration Analysis',
    html: `<div class="legend-section">
      <h3>Theory: Historical Cycle Statistics</h3>
      <div class="legend-desc" style="margin-bottom:12px">วิเคราะห์ข้อมูลในอดีตว่าช่วงตลาดขาลงมักจะกินเวลากี่วัน เพื่อให้เรา "ไม่รีบเข้าซื้อเร็วเกินไป" ในช่วงที่ตลาดยังปรับฐานไม่จบ</div>
      <div class="legend-row"><div class="legend-symbol">Median Case</div><div class="legend-desc">ระยะเวลาปกติที่การพักตัวมักจะจบลง</div></div>
    </div>`
  },
  earnings: {
    title: '📈 คู่มือ: Earnings Trade Analyzer',
    html: `<div class="legend-section">
      <h3>5-Factor Scoring System (Post-Earnings Drift)</h3>
      <div class="legend-row"><div class="legend-symbol">Gap & Go</div><div class="legend-desc">ค้นหาหุ้นที่เบรกเอาท์ด้วยแรงกระโดดหลังงบออก (Positive Surprise)</div></div>
      <div class="legend-row"><div class="legend-symbol">Grade A</div><div class="legend-desc">โมเมนตัมแข็งแกร่งที่สุด — มีโอกาสวิ่งต่อได้หลายสัปดาห์</div></div>
    </div>`
  },
  canslim: {
    title: '🏆 คู่มือ: CANSLIM Screener',
    html: `<div class="legend-section">
      <h3>Theory: William O'Neil's CANSLIM</h3>
      <p style="font-size:.8rem;color:var(--muted)">7 ปัจจัยที่หุ้นชั้นนำต้องมีก่อนวิ่งใหญ่ (Phase 3 — Full 7 components)</p>
      <div class="legend-row"><div class="legend-symbol" style="color:var(--cyan)">C — Current Earnings</div><div class="legend-desc">กำไรไตรมาสล่าสุด +25%+ YoY (น้ำหนัก 15%)</div></div>
      <div class="legend-row"><div class="legend-symbol" style="color:var(--cyan)">A — Annual Growth</div><div class="legend-desc">กำไรรายปี CAGR +25%+ ใน 3 ปี (น้ำหนัก 15%)</div></div>
      <div class="legend-row"><div class="legend-symbol" style="color:var(--cyan)">N — New High/Product</div><div class="legend-desc">ราคาใกล้ 52-week high หรือมีผลิตภัณฑ์ใหม่ (น้ำหนัก 15%)</div></div>
      <div class="legend-row"><div class="legend-symbol" style="color:var(--cyan)">S — Supply/Demand</div><div class="legend-desc">Up/Down Volume Ratio สะสมแบบ Accumulation (น้ำหนัก 15%)</div></div>
      <div class="legend-row"><div class="legend-symbol" style="color:var(--cyan)">L — Leadership RS</div><div class="legend-desc">RS Percentile ≥80 — หุ้นต้องแข็งแกร่งกว่า S&P500 (น้ำหนัก 15%)</div></div>
      <div class="legend-row"><div class="legend-symbol" style="color:var(--cyan)">I — Institutional</div><div class="legend-desc">Institutional holders ≥30 คน หรือ ownership ≥20% (น้ำหนัก 10%)</div></div>
      <div class="legend-row"><div class="legend-symbol" style="color:var(--cyan)">M — Market Direction</div><div class="legend-desc">ตลาดต้องอยู่ใน uptrend — ห้ามซื้อในตลาดขาลง (น้ำหนัก 15%)</div></div>

      <h3 style="margin-top:12px">Dynamic Pattern Stats</h3>
      <div class="legend-row"><div class="legend-symbol" style="color:var(--cyan)">Context-Aware</div><div class="legend-desc">สแกนแพทเทิร์นล่าสุด (Breakout, Volume Climax ฯลฯ) แล้วคำนวณ <strong>Win Rate</strong> ถ้ายอมถือข้ามวัน</div></div>
      <div class="legend-row"><div class="legend-symbol" style="color:var(--green)">Win Rate &gt;60%</div><div class="legend-desc">โอกาสชนะสูง ให้ <strong>ถือข้ามวัน (Hold/Buy ATC)</strong></div></div>
      <div class="legend-row"><div class="legend-symbol" style="color:var(--red)">Win Rate ต่ำ</div><div class="legend-desc">แนวโน้มไม่ดี ให้ <strong>ชิงขายทำกำไร หรือ ชะลอการซื้อ</strong></div></div>

      <h3 style="margin-top:12px">Score Interpretation</h3>
      <div class="legend-row"><div class="legend-symbol" style="color:var(--green)">≥90 Exceptional+</div><div class="legend-desc">Multi-bagger setup — all components near-perfect</div></div>
      <div class="legend-row"><div class="legend-symbol" style="color:var(--green)">70-89 Strong</div><div class="legend-desc">Solid CANSLIM candidate — consider buying</div></div>
      <div class="legend-row"><div class="legend-symbol" style="color:var(--gold)">50-69 Average</div><div class="legend-desc">Watchlist — wait for improvement</div></div>
      <div class="legend-row"><div class="legend-symbol" style="color:var(--red)">&lt;50 Weak</div><div class="legend-desc">Avoid — does not meet CANSLIM criteria</div></div>
    </div>`
  },
  tools: {
    title: '🛠️ ทฤษฎีเบื้องหลัง Indicators',
    html: `<div class="legend-section">
      <div class="legend-row"><div class="legend-symbol">SMA 200/150</div><div class="legend-desc">Long-term Trend — ถ้าราคาอยู่ใต้เส้นนี้ ห้ามซื้อเด็ดขาด (Stage 4)</div></div>
      <div class="legend-row"><div class="legend-symbol">RS Rank</div><div class="legend-desc">Relative Strength (O'Neil) — หุ้นต้องแข็งแกร่งกว่าตลาด (เป้า >80)</div></div>
      <div class="legend-row"><div class="legend-symbol">ATR</div><div class="legend-desc">Average True Range — วัดความผันผวนเพื่อตั้งจุด Stop Loss ที่เหมาะสม</div></div>
      <div class="legend-row"><div class="legend-symbol">VCP</div><div class="legend-desc">Volatility Contraction — การสะสมพลังของราคาก่อนการวิ่งรอบใหญ่</div></div>
    </div>`
  }
};

function toggleGuide() {
  const content = document.getElementById('guideContent');
  const icon = document.getElementById('guideToggleIcon');
  if (content.style.display === 'none') {
    content.style.display = 'block';
    icon.textContent = 'ซ่อนคู่มือ';
    icon.setAttribute('aria-expanded', 'true');
    localStorage.setItem('showTradingGuide', '1');
  } else {
    content.style.display = 'none';
    icon.textContent = 'แสดงคู่มือ';
    icon.setAttribute('aria-expanded', 'false');
    localStorage.setItem('showTradingGuide', '0');
  }
}

function initTradingGuide() {
  const content = document.getElementById('guideContent');
  const icon = document.getElementById('guideToggleIcon');
  if (localStorage.getItem('tradingGuideDefaultHiddenV2') !== '1') {
    localStorage.setItem('showTradingGuide', '0');
    localStorage.setItem('tradingGuideDefaultHiddenV2', '1');
  }
  const show = localStorage.getItem('showTradingGuide');
  if (show === '1') {
    content.style.display = 'block';
    icon.textContent = 'ซ่อนคู่มือ';
    icon.setAttribute('aria-expanded', 'true');
  } else {
    content.style.display = 'none';
    icon.textContent = 'แสดงคู่มือ';
    icon.setAttribute('aria-expanded', 'false');
  }
}

let RAW_DATA = null;
let CURRENT_BREAKOUT_PLAN = null;
// Default market = TH (Thai market). Will be overridden by loadSettings() from localStorage
// if user has previously selected another market.
let currentMarket = 'TH';
window.BENCHMARK_DATA = null;

async function fetchBenchmarkData(m) {
  const symbol = m === 'TH' ? '^SET.BK' : 'SPY';
  try {
    const res = await fetch(`/api/history/${symbol}`);
    if (res.ok) {
      window.BENCHMARK_DATA = await res.json();
    } else {
      window.BENCHMARK_DATA = null;
    }
  } catch (e) {
    console.error("Failed to load benchmark data for " + symbol, e);
    window.BENCHMARK_DATA = null;
  }
}
let VCP_SORT = { col: 'composite_score', dir: -1 };
let CANSLIM_SORT = { col: 'composite_score', dir: -1 };
let _canslimResults = [];
let CURRENT_DASHBOARD_TAB = 'main';

// --- FAVORITES & WATCHLIST JS LOGIC ---
let _starredStocks = JSON.parse(localStorage.getItem('starred_stocks') || '[]');
let _favoritesCache = {}; // Cache for stock prices/changes

function isStarred(symbol) {
  return _starredStocks.includes(symbol);
}

function toggleStar(event, symbol) {
  if (event) event.stopPropagation();
  const idx = _starredStocks.indexOf(symbol);
  if (idx > -1) {
    _starredStocks.splice(idx, 1);
  } else {
    _starredStocks.push(symbol);
  }
  localStorage.setItem('starred_stocks', JSON.stringify(_starredStocks));

  // Refresh views to update star symbols and lists
  updateTables();
  renderFavoritesCard();
}

function updateTables() {
  if (typeof updateVCP === 'function') updateVCP();
  if (typeof updateCANSLIM === 'function') updateCANSLIM();
  if (RAW_DATA) {
    if (RAW_DATA.thai_swing && typeof renderThaiSwing === 'function') renderThaiSwing(RAW_DATA.thai_swing);
    if (RAW_DATA.thai_watchlists && typeof renderThaiWatchlists === 'function') renderThaiWatchlists(RAW_DATA.thai_watchlists);
    if (RAW_DATA.thai_dividends && typeof renderThaiDividends === 'function') renderThaiDividends(RAW_DATA.thai_dividends);
  }
}

function getStateClass(state) {
  if (!state) return 'bg-orange';
  state = state.toLowerCase();
  if (state.includes('breakout') || state.includes('pre-breakout') || state.includes('buy') || state.includes('growth') || state.includes('excellent')) return 'bg-green';
  if (state.includes('damaged') || state.includes('avoid')) return 'bg-red';
  return 'bg-orange';
}

function findStockInRawData(sym) {
  if (!RAW_DATA) return null;

  // Check VCP Screener
  if (RAW_DATA.vcp && RAW_DATA.vcp.results) {
    const found = RAW_DATA.vcp.results.find(r => r.symbol === sym);
    if (found) {
      return {
        companyName: found.company_name,
        price: found.price,
        state: found.execution_state,
        changePct: found.relative_strength?.daily_change_pct || null,
        sector: found.sector || null
      };
    }
  }

  // Check CANSLIM Screener
  if (RAW_DATA.canslim && RAW_DATA.canslim.results) {
    const found = RAW_DATA.canslim.results.find(r => r.symbol === sym);
    if (found) {
      const rec = found.threshold_check?.recommendation;
      const stateLabel = rec === 'buy' ? 'Breakout Plan' : rec === 'watchlist' ? 'Watchlist' : 'Avoid';
      return {
        companyName: found.company_name,
        price: found.price,
        state: stateLabel,
        changePct: null,
        sector: found.sector || null
      };
    }
  }

  if (RAW_DATA.thai_swing) {
    const list = [...(RAW_DATA.thai_swing.dip_buy || []), ...(RAW_DATA.thai_swing.momentum || [])];
    const found = list.find(r => r.symbol === sym);
    if (found) {
      return {
        companyName: found.name,
        price: found.price || found.plan?.entry,
        state: 'Swing Trade Setup',
        changePct: null,
        sector: found.sector || null
      };
    }
  }

  if (RAW_DATA.thai_watchlists && RAW_DATA.thai_watchlists.buckets) {
    for (const [bucket, rows] of Object.entries(RAW_DATA.thai_watchlists.buckets)) {
      const found = rows.find(r => r.symbol === sym);
      if (found) {
        return {
          companyName: '',
          price: found.price,
          state: `Watchlist (${bucket.toUpperCase()})`,
          changePct: null,
          sector: found.sector || null
        };
      }
    }
  }

  if (RAW_DATA.thai_dividends && RAW_DATA.thai_dividends.candidates) {
    const found = RAW_DATA.thai_dividends.candidates.find(r => r.symbol === sym);
    if (found) {
      return {
        companyName: '',
        price: found.price,
        state: `Dividend (${found.grade})`,
        changePct: null,
        sector: found.sector || null
      };
    }
  }

  return null;
}

async function fetchStockPriceAndChange(sym) {
  if (_favoritesCache[sym]) return;
  try {
    const res = await fetch(`/api/history/${sym}`);
    if (!res.ok) return;
    const history = await res.json();
    if (!history || history.length < 2) return;

    const latestBar = history[history.length - 1];
    const prevBar = history[history.length - 2];

    const price = latestBar.close;
    const prevClose = prevBar.close;
    const changePct = ((price - prevClose) / prevClose) * 100;

    _favoritesCache[sym] = { price, changePct };

    const priceEl = document.getElementById(`fav-price-${sym}`);
    const changeEl = document.getElementById(`fav-change-${sym}`);

    if (priceEl) {
      const priceSign = currentMarket === 'TH' ? '฿' : '$';
      priceEl.textContent = `${priceSign}${price.toFixed(2)}`;
    }

    if (changeEl) {
      const sign = changePct >= 0 ? '+' : '';
      changeEl.textContent = `${sign}${changePct.toFixed(2)}%`;
      changeEl.style.color = changePct >= 0 ? 'var(--green)' : 'var(--red)';
    }
  } catch (err) {
    console.error(`Failed to fetch live price for ${sym}:`, err);
  }
}

function toggleFavRow(i) {
  const r = document.getElementById('fav-row-' + i);
  if (!r) return;
  const isOpen = r.classList.toggle('open');
  if (isOpen) {
    const sym = r.previousElementSibling.getAttribute('data-symbol');
    initFavChart(sym);
  }
}

function toggleFavRowClick(event, i) {
  event.stopPropagation();
  toggleFavRow(i);
}

function calculatePatternStats(bars, currentIndex) {
  if (currentIndex < 1) return null;

  let currentGapStreak = 0;
  let currentGapDir = 0;
  let currentColorStreak = 0;
  let currentColorDir = 0;

  const sma50 = [];
  const sma200 = [];
  const vol20 = [];
  const high20 = [];
  const range10 = [];

  for (let i = 0; i < bars.length; i++) {
    if (i < 49) {
      sma50.push(null);
    } else {
      let sum = 0;
      for (let j = 0; j < 50; j++) sum += bars[i - j].close;
      sma50.push(sum / 50);
    }

    if (i < 199) {
      sma200.push(null);
    } else {
      let sum = 0;
      for (let j = 0; j < 200; j++) sum += bars[i - j].close;
      sma200.push(sum / 200);
    }

    if (i < 19) {
      vol20.push(null);
      high20.push(null);
    } else {
      let vSum = 0;
      let hMax = -Infinity;
      for (let j = 0; j < 20; j++) {
        vSum += (bars[i - j].volume || 0);
        if (bars[i - j].high > hMax) hMax = bars[i - j].high;
      }
      vol20.push(vSum / 20);
      high20.push(hMax);
    }

    if (i < 9) {
      range10.push(null);
    } else {
      let rSum = 0;
      for (let j = 0; j < 10; j++) rSum += (bars[i - j].high - bars[i - j].low);
      range10.push(rSum / 10);
    }
  }

  // ── True Range & ATR 14 ──
  const tr = [];
  for (let i = 0; i < bars.length; i++) {
    if (i === 0) {
      tr.push(bars[i].high - bars[i].low);
    } else {
      tr.push(Math.max(
        bars[i].high - bars[i].low,
        Math.abs(bars[i].high - bars[i-1].close),
        Math.abs(bars[i].low - bars[i-1].close)
      ));
    }
  }
  const atr14 = [];
  for (let i = 0; i < bars.length; i++) {
    if (i < 13) {
      atr14.push(null);
    } else {
      let sum = 0;
      for (let j = 0; j < 14; j++) sum += tr[i-j];
      atr14.push(sum / 14);
    }
  }

  // ── RSI 14 ──
  const rsi14 = [];
  let avgGain = 0;
  let avgLoss = 0;
  for (let i = 0; i < bars.length; i++) {
    if (i === 0) {
      rsi14.push(null);
      continue;
    }
    const diff = bars[i].close - bars[i-1].close;
    const gain = diff > 0 ? diff : 0;
    const loss = diff < 0 ? -diff : 0;
    if (i <= 14) {
      avgGain += gain;
      avgLoss += loss;
      if (i === 14) {
        avgGain /= 14;
        avgLoss /= 14;
        const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
        rsi14.push(100 - (100 / (1 + rs)));
      } else {
        rsi14.push(null);
      }
    } else {
      avgGain = (avgGain * 13 + gain) / 14;
      avgLoss = (avgLoss * 13 + loss) / 14;
      const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
      rsi14.push(100 - (100 / (1 + rs)));
    }
  }

  // ── RSI Divergences ──
  let isRsiBullDiv = false;
  let isRsiBearDiv = false;
  if (currentIndex >= 20 && rsi14[currentIndex] !== null) {
    const priceToday = bars[currentIndex].close;
    const rsiToday = rsi14[currentIndex];

    let prevLowIdx = -1;
    for (let j = currentIndex - 5; j >= currentIndex - 25; j--) {
      if (j >= 2 && bars[j].low <= bars[j-1].low && bars[j].low <= bars[j-2].low &&
          bars[j].low <= bars[j+1].low && bars[j].low <= bars[j+2].low) {
        prevLowIdx = j;
        break;
      }
    }

    if (prevLowIdx !== -1 && rsi14[prevLowIdx] !== null) {
      const pricePrevLow = bars[prevLowIdx].close;
      const rsiPrevLow = rsi14[prevLowIdx];
      if (priceToday < pricePrevLow && rsiToday > rsiPrevLow && rsiToday < 45) {
        isRsiBullDiv = true;
      }
    }

    let prevHighIdx = -1;
    for (let j = currentIndex - 5; j >= currentIndex - 25; j--) {
      if (j >= 2 && bars[j].high >= bars[j-1].high && bars[j].high >= bars[j-2].high &&
          bars[j].high >= bars[j+1].high && bars[j].high >= bars[j+2].high) {
        prevHighIdx = j;
        break;
      }
    }

    if (prevHighIdx !== -1 && rsi14[prevHighIdx] !== null) {
      const pricePrevHigh = bars[prevHighIdx].close;
      const rsiPrevHigh = rsi14[prevHighIdx];
      if (priceToday > pricePrevHigh && rsiToday < rsiPrevHigh && rsiToday > 55) {
        isRsiBearDiv = true;
      }
    }
  }

  // ── Inside Day & NR7 ──
  const isInsideDay = currentIndex > 0 &&
    bars[currentIndex].high < bars[currentIndex - 1].high &&
    bars[currentIndex].low > bars[currentIndex - 1].low;

  let isNR7 = false;
  if (currentIndex >= 6) {
    const getRange = (idx) => bars[idx].high - bars[idx].low;
    const todayRange = getRange(currentIndex);
    let smallest = true;
    for (let j = 1; j <= 6; j++) {
      if (getRange(currentIndex - j) <= todayRange) {
        smallest = false;
        break;
      }
    }
    isNR7 = smallest;
  }

  // ── Weekly Trend (Weekly 10-SMA) ──
  const getWeeklyCloses = (dailyBars, limitIndex) => {
    const weeklyCloses = [];
    for (let i = 0; i <= limitIndex; i++) {
      const b = dailyBars[i];
      const dateObj = new Date(b.time);
      const nextB = dailyBars[i+1];
      const isLastDayOfWeek = !nextB || i === limitIndex ||
        new Date(nextB.time).getDay() < dateObj.getDay() ||
        (new Date(nextB.time) - dateObj) > 4 * 24 * 60 * 60 * 1000;

      if (isLastDayOfWeek) {
        weeklyCloses.push(b.close);
      }
    }
    return weeklyCloses;
  };

  const weeklyCloses = getWeeklyCloses(bars, currentIndex);
  let isWeeklyBull = false;
  let weeklySMA10Val = null;
  if (weeklyCloses.length >= 10) {
    let sum = 0;
    for (let j = 0; j < 10; j++) {
      sum += weeklyCloses[weeklyCloses.length - 1 - j];
    }
    weeklySMA10Val = sum / 10;
    isWeeklyBull = weeklyCloses[weeklyCloses.length - 1] > weeklySMA10Val;
  }

  // ── Minervini Weighted Relative Strength (RS) ──
  let rsPercentile = null;
  let rsScore = null;
  let rawWeightedRs = null;

  if (window.BENCHMARK_DATA && window.BENCHMARK_DATA.length > 0) {
    const benchmark = window.BENCHMARK_DATA;

    const getReturnPct = (pricesArr, days, refTime) => {
      const idx = pricesArr.findIndex(p => p.time === refTime);
      if (idx < 0) return 0.0;
      const startIdx = Math.max(0, idx - days);
      const currentClose = pricesArr[idx].close;
      const pastClose = pricesArr[startIdx].close;
      if (pastClose <= 0) return 0.0;
      return ((currentClose - pastClose) / pastClose) * 100;
    };

    const refTime = bars[currentIndex].time;
    const stockIdx = bars.findIndex(p => p.time === refTime);
    const benchIdx = benchmark.findIndex(p => p.time === refTime);

    if (stockIdx >= 30 && benchIdx >= 30) {
      const stock_63 = getReturnPct(bars, 63, refTime);
      const bench_63 = getReturnPct(benchmark, 63, refTime);
      const r_63 = stock_63 - bench_63;

      const stock_126 = getReturnPct(bars, 126, refTime);
      const bench_126 = getReturnPct(benchmark, 126, refTime);
      const r_126 = stock_126 - bench_126;

      const stock_189 = getReturnPct(bars, 189, refTime);
      const bench_189 = getReturnPct(benchmark, 189, refTime);
      const r_189 = stock_189 - bench_189;

      const stock_252 = getReturnPct(bars, 252, refTime);
      const bench_252 = getReturnPct(benchmark, 252, refTime);
      const r_252 = stock_252 - bench_252;

      rawWeightedRs = 0.40 * r_63 + 0.20 * r_126 + 0.20 * r_189 + 0.20 * r_252;

      const score_rs_map = (val) => {
        if (val >= 50) return [100, 99];
        if (val >= 30) return [95, 95];
        if (val >= 20) return [90, 90];
        if (val >= 10) return [80, 80];
        if (val >= 5) return [70, 70];
        if (val >= 0) return [60, 60];
        if (val >= -5) return [50, 50];
        if (val >= -10) return [40, 40];
        if (val >= -20) return [20, 25];
        return [0, 10];
      };

      const [sc, pct] = score_rs_map(rawWeightedRs);
      rsScore = sc;
      rsPercentile = pct;
    }
  }

  // ── Day-of-Week Bias ──
  let dayOfWeekBias = null;
  if (currentIndex >= 5) {
    const todayDate = new Date(bars[currentIndex].time);
    const targetDay = todayDate.getDay();
    const dayNames = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
    const dayName = dayNames[targetDay];

    let sameDayCount = 0;
    let sameDayWins = 0;
    let sameDayReturnSum = 0;

    for (let i = 1; i <= currentIndex; i++) {
      const barDate = new Date(bars[i].time);
      if (barDate.getDay() === targetDay) {
        sameDayCount++;
        const prevClose = bars[i-1].close;
        const currentClose = bars[i].close;
        const ret = prevClose > 0 ? (currentClose - prevClose) / prevClose * 100 : 0;
        sameDayReturnSum += ret;
        if (ret > 0) {
          sameDayWins++;
        }
      }
    }

    if (sameDayCount > 0) {
      dayOfWeekBias = {
        day: dayName,
        winRate: (sameDayWins / sameDayCount * 100).toFixed(1),
        avgReturn: (sameDayReturnSum / sameDayCount).toFixed(2),
        count: sameDayCount
      };
    }
  }


  for (let i = currentIndex; i >= 1; i--) {
    const gap = bars[i].open - bars[i-1].close;
    if (Math.abs(gap) > 0) {
      const gDir = gap > 0 ? 1 : -1;
      if (currentGapStreak === 0) {
        currentGapDir = gDir;
        currentGapStreak++;
      } else if (gDir === currentGapDir) {
        currentGapStreak++;
      } else {
        break;
      }
    } else {
      break;
    }
  }

  for (let i = currentIndex; i >= 0; i--) {
    const cDir = bars[i].close > bars[i].open ? 1 : (bars[i].close < bars[i].open ? -1 : 0);
    if (cDir !== 0) {
      if (currentColorStreak === 0) {
        currentColorDir = cDir;
        currentColorStreak++;
      } else if (cDir === currentColorDir) {
        currentColorStreak++;
      } else {
        break;
      }
    } else {
      break;
    }
  }

  const findRecentStats = (conditionFn) => {
    const occurrences = [];
    for (let i = 1; i <= currentIndex - 1; i++) {
      if (i + 1 >= bars.length) continue;
      if (conditionFn(i)) {
        const b = bars[i];
        const next_b = bars[i+1];
        const ret = (next_b.close - b.close) / b.close * 100;
        occurrences.push(ret);
      }
    }
    occurrences.reverse();
    return occurrences;
  };

  const findForwardStats = (conditionFn, periods) => {
    const results = {};
    periods.forEach(p => results[p] = []);
    for (let i = 1; i <= currentIndex - 1; i++) {
      if (conditionFn(i)) {
        periods.forEach(p => {
          if (i + p < bars.length) {
            const ret = (bars[i+p].close - bars[i].close) / bars[i].close * 100;
            results[p].push(ret);
          }
        });
      }
    }
    return results;
  };

  const gapCondition = (i) => {
    if (currentGapStreak === 0) return false;
    if (i - currentGapStreak + 1 < 1) return false;
    for (let j = 0; j < currentGapStreak; j++) {
      const idx = i - j;
      const gap = bars[idx].open - bars[idx-1].close;
      const gDir = gap > 0 ? 1 : (gap < 0 ? -1 : 0);
      if (gDir !== currentGapDir) return false;
    }
    return true;
  };

  const colorCondition = (i) => {
    if (currentColorStreak === 0) return false;
    if (i - currentColorStreak + 1 < 0) return false;
    for (let j = 0; j < currentColorStreak; j++) {
      const idx = i - j;
      const cDir = bars[idx].close > bars[idx].open ? 1 : (bars[idx].close < bars[idx].open ? -1 : 0);
      if (cDir !== currentColorDir) return false;
    }
    return true;
  };

  const pullbackCondition = (i) => {
    return sma50[i] && bars[i].low <= sma50[i] && bars[i].close >= sma50[i] * 0.99;
  };

  const breakoutCondition = (i) => {
    return i > 0 && high20[i-1] && bars[i].close > high20[i-1];
  };

  const volumeSpikeCondition = (i) => {
    return vol20[i] && (bars[i].volume || 0) >= vol20[i] * 2.0;
  };

  const volumeDryUpCondition = (i) => {
    return vol20[i] && (bars[i].volume || 0) < vol20[i] * 0.5;
  };

  const hammerCondition = (i) => {
    const body = Math.abs(bars[i].close - bars[i].open);
    const lowerWick = Math.min(bars[i].close, bars[i].open) - bars[i].low;
    const isHammerShape = lowerWick >= body * 2 && lowerWick > 0;
    if (!isHammerShape) return false;

    const isNearSMA50 = sma50[i] && Math.abs(bars[i].low - sma50[i]) / sma50[i] <= 0.02;
    const isNearSMA200 = sma200[i] && Math.abs(bars[i].low - sma200[i]) / sma200[i] <= 0.02;
    const isAfterDowntrend = i >= 4 && bars[i-1].close < bars[i-2].close && bars[i-2].close < bars[i-3].close && bars[i-3].close < bars[i-4].close;
    return isNearSMA50 || isNearSMA200 || isAfterDowntrend;
  };

  const strongCloseCondition = (i) => {
    const range = bars[i].high - bars[i].low;
    if (range <= 0) return false;
    const closePos = (bars[i].close - bars[i].low) / range;
    return closePos >= 0.75 && bars[i].close > bars[i].open && vol20[i] && (bars[i].volume || 0) > vol20[i];
  };

  const wideRangeBullCondition = (i) => {
    const range = bars[i].high - bars[i].low;
    return range10[i] && range >= range10[i] * 1.5 && bars[i].close > bars[i].open;
  };

  const wideRangeBearCondition = (i) => {
    const range = bars[i].high - bars[i].low;
    return range10[i] && range >= range10[i] * 1.5 && bars[i].close < bars[i].open;
  };

  const aboveSMA200Condition = (i) => {
    return sma200[i] && bars[i].close > sma200[i];
  };

  const belowSMA200Condition = (i) => {
    return sma200[i] && bars[i].close <= sma200[i];
  };

  const isPullback = pullbackCondition(currentIndex);
  const isBreakout = breakoutCondition(currentIndex);
  const isVolumeSpike = volumeSpikeCondition(currentIndex);
  const isVolumeDryUp = volumeDryUpCondition(currentIndex);
  const isHammer = hammerCondition(currentIndex);
  const isStrongClose = strongCloseCondition(currentIndex);
  const isWideRangeBull = wideRangeBullCondition(currentIndex);
  const isWideRangeBear = wideRangeBearCondition(currentIndex);
  const isAboveSMA200 = aboveSMA200Condition(currentIndex);
  const isBelowSMA200 = belowSMA200Condition(currentIndex);

  const gapReturns = findRecentStats(gapCondition);
  const colorReturns = findRecentStats(colorCondition);
  const pullbackReturns = isPullback ? findForwardStats(pullbackCondition, [3, 5, 10, 20]) : null;
  const breakoutReturns = isBreakout ? findForwardStats(breakoutCondition, [3, 5, 10, 20]) : null;
  const volumeSpikeReturns = isVolumeSpike ? findForwardStats(volumeSpikeCondition, [3, 5, 10, 20]) : null;
  const volumeDryUpReturns = isVolumeDryUp ? findForwardStats(volumeDryUpCondition, [3, 5, 10, 20]) : null;
  const hammerReturns = isHammer ? findForwardStats(hammerCondition, [3, 5, 10]) : null;
  const strongCloseReturns = isStrongClose ? findForwardStats(strongCloseCondition, [3, 5, 10]) : null;
  const wideRangeBullReturns = isWideRangeBull ? findForwardStats(wideRangeBullCondition, [3, 5, 10]) : null;
  const wideRangeBearReturns = isWideRangeBear ? findForwardStats(wideRangeBearCondition, [3, 5, 10]) : null;
  const aboveSMA200Returns = isAboveSMA200 ? findForwardStats(aboveSMA200Condition, [5, 10, 20]) : null;
  const belowSMA200Returns = isBelowSMA200 ? findForwardStats(belowSMA200Condition, [5, 10, 20]) : null;

  const calcRet = (rets, n) => {
    const slice = n === 'all' ? rets : rets.slice(0, n);
    if (slice.length === 0) return null;
    const wins = slice.filter(r => r > 0).length;
    const avg = slice.reduce((a, b) => a + b, 0) / slice.length;
    return { winRate: (wins / slice.length * 100).toFixed(1), avg: avg.toFixed(2), total: slice.length };
  };

  const buildStatsObj = (rets, periods) => {
    const obj = {};
    periods.forEach(p => {
      obj[p] = calcRet(rets, p);
    });
    return obj;
  };

  const buildForwardStatsObj = (forwardStats) => {
    const obj = {};
    for (const p in forwardStats) {
      obj[p] = calcRet(forwardStats[p], 'all');
    }
    return obj;
  };

  return {
    gap: {
      streak: currentGapStreak,
      dir: currentGapDir,
      stats: buildStatsObj(gapReturns, [10, 20, 'all'])
    },
    color: {
      streak: currentColorStreak,
      dir: currentColorDir,
      stats: buildStatsObj(colorReturns, [5, 10, 'all'])
    },
    pullback: isPullback ? { stats: buildForwardStatsObj(pullbackReturns) } : null,
    breakout: isBreakout ? { stats: buildForwardStatsObj(breakoutReturns) } : null,
    volumeSpike: isVolumeSpike ? { stats: buildForwardStatsObj(volumeSpikeReturns) } : null,
    volumeDryUp: isVolumeDryUp ? { stats: buildForwardStatsObj(volumeDryUpReturns) } : null,
    hammer: isHammer ? { stats: buildForwardStatsObj(hammerReturns) } : null,
    strongClose: isStrongClose ? { stats: buildForwardStatsObj(strongCloseReturns) } : null,
    wideRangeBull: isWideRangeBull ? { stats: buildForwardStatsObj(wideRangeBullReturns) } : null,
    wideRangeBear: isWideRangeBear ? { stats: buildForwardStatsObj(wideRangeBearReturns) } : null,
    regime: {
      isAbove: isAboveSMA200,
      stats: buildForwardStatsObj(isAboveSMA200 ? aboveSMA200Returns : belowSMA200Returns)
    },
    insideDay: isInsideDay,
    nr7: isNR7,
    rsi: rsi14[currentIndex] !== null ? rsi14[currentIndex].toFixed(1) : null,
    rsiDivergence: {
      isBull: isRsiBullDiv,
      isBear: isRsiBearDiv
    },
    atr: atr14[currentIndex] ? {
      val: atr14[currentIndex],
      pct: (atr14[currentIndex] / bars[currentIndex].close * 100).toFixed(2)
    } : null,
    weeklyTrend: {
      isWeeklyBull: isWeeklyBull,
      weeklySMA10: weeklySMA10Val
    },
    rs: rawWeightedRs !== null ? {
      percentile: rsPercentile,
      score: rsScore,
      raw: rawWeightedRs.toFixed(2)
    } : null,
    dayBias: dayOfWeekBias
  };
}

function setupChartLegend(chart, container, symbol, prices, candleSeries) {
  container.style.position = 'relative';
  const legend = document.createElement('div');
  legend.style.position = 'absolute';
  legend.style.left = '12px';
  legend.style.top = '12px';
  legend.style.zIndex = 10;
  legend.style.fontFamily = "'JetBrains Mono', monospace";
  legend.style.fontSize = '11px';
  legend.style.color = 'var(--text)';
  legend.style.background = 'rgba(13, 17, 23, 0.9)';
  legend.style.padding = '8px 12px';
  legend.style.borderRadius = '8px';
  legend.style.pointerEvents = 'none';
  legend.style.border = '1px solid var(--border)';
  legend.style.boxShadow = '0 6px 16px rgba(0,0,0,0.4)';
  legend.style.minWidth = '280px';
  legend.style.maxWidth = '360px';

  container.appendChild(legend);

  const formatStat = (s, n) => {
    if (!s || !s[n]) return `<span style="color:var(--muted)">N/A</span>`;
    const col = s[n].avg > 0 ? 'var(--green)' : 'var(--red)';
    return `<span style="color:${col}">${s[n].winRate}% (${s[n].avg}%)</span>`;
  };

  const SECTOR_ETF_MAP = {
    "Technology": "XLK",
    "Financial Services": "XLF",
    "Financials": "XLF",
    "Healthcare": "XLV",
    "Consumer Cyclical": "XLY",
    "Consumer Discretionary": "XLY",
    "Industrials": "XLI",
    "Communication Services": "XLC",
    "Consumer Defensive": "XLP",
    "Consumer Staples": "XLP",
    "Energy": "XLE",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
    "Basic Materials": "XLB",
    "Materials": "XLB"
  };

  let currentActiveBar = prices[prices.length - 1];

  // Metadata lazy loading
  if (container.dataset.symbol !== symbol) {
    container.dataset.symbol = symbol;
    container.chartMetadata = {
      earnings: null,
      sectorName: null,
      sectorETF: null,
      sectorHistory: null
    };

    // 1. Fetch earnings data
    fetch(`/api/earnings/${symbol}`)
      .then(res => res.ok ? res.json() : null)
      .then(metaData => {
        if (metaData && container.dataset.symbol === symbol) {
          container.chartMetadata.earnings = metaData;
          if (currentActiveBar) setLegendContent(currentActiveBar);
        }
      })
      .catch(err => console.error("Error fetching earnings:", err));

    // 2. Resolve Sector & fetch ETF
    const STOCK_SECTOR_FALLBACKS = {
      "AAPL": "Technology", "MSFT": "Technology", "NVDA": "Technology", "AMD": "Technology",
      "AVGO": "Technology", "LRCX": "Technology", "AMAT": "Technology", "INTC": "Technology",
      "FFIV": "Technology", "DELL": "Technology", "CSCO": "Technology", "ANET": "Technology",
      "JBL": "Technology", "APH": "Technology", "VRT": "Technology", "ADI": "Technology",
      "TXN": "Technology", "MU": "Technology",
      "JNJ": "Healthcare", "INCY": "Healthcare", "BIIB": "Healthcare", "MRNA": "Healthcare",
      "MRK": "Healthcare", "CVS": "Healthcare", "UNH": "Healthcare", "HUM": "Healthcare",
      "LLY": "Healthcare", "DVA": "Healthcare", "WELL": "Healthcare", "CNC": "Healthcare",
      "IRM": "Real Estate", "EQIX": "Real Estate", "XLRE": "Real Estate",
      "FIX": "Industrials", "JBHT": "Industrials", "ODFL": "Industrials", "FDX": "Industrials",
      "CAT": "Industrials", "GE": "Industrials", "HON": "Industrials", "CSX": "Industrials",
      "TPR": "Consumer Cyclical", "RL": "Consumer Cyclical", "TGT": "Consumer Cyclical",
      "ROST": "Consumer Cyclical", "MGM": "Consumer Cyclical",
      "TRGP": "Energy", "VLO": "Energy", "MPC": "Energy",
      "C": "Financials", "BEN": "Financials", "BNY": "Financials", "IBKR": "Financials", "MS": "Financials",
      "GL": "Financials", "STT": "Financials", "CFG": "Financials",
      "GOOGL": "Communication Services", "GOOG": "Communication Services"
    };

    const stockInfo = findStockInRawData(symbol);
    let sector = null;
    if (stockInfo) {
      sector = (stockInfo.sector && stockInfo.sector !== 'Unknown') ? stockInfo.sector : (STOCK_SECTOR_FALLBACKS[symbol] || null);
    } else {
      sector = STOCK_SECTOR_FALLBACKS[symbol] || null;
    }

    if (sector) {
      container.chartMetadata.sectorName = sector;
      const etf = SECTOR_ETF_MAP[sector];
      if (etf && currentMarket === 'US') {
        container.chartMetadata.sectorETF = etf;
        fetch(`/api/history/${etf}`)
          .then(res => res.ok ? res.json() : null)
          .then(hist => {
            if (hist && container.dataset.symbol === symbol) {
              container.chartMetadata.sectorHistory = hist;
              if (currentActiveBar) setLegendContent(currentActiveBar);
            }
          })
          .catch(err => console.error("Error fetching sector ETF:", err));
      }
    }
  }

  const setLegendContent = (priceData) => {
    if (!priceData) {
      legend.innerHTML = `<strong>${symbol}</strong><br>Hover over chart for details`;
      return;
    }

    currentActiveBar = priceData;
    const currentIndex = prices.findIndex(p => p.time === priceData.time);
    const stats = currentIndex >= 0 ? calculatePatternStats(prices, currentIndex) : null;
    const meta = container.chartMetadata || {};

    const color = priceData.close >= priceData.open ? 'var(--green)' : 'var(--red)';
    const barClose = priceData.close;
    const barVol = prices[currentIndex] ? (prices[currentIndex].value || prices[currentIndex].volume || 0) : 0;

    // Earnings warning overlay
    let earningsHtml = "";
    if (meta.earnings && meta.earnings.date) {
      const daysTo = meta.earnings.days_to_earnings;
      if (daysTo !== null && daysTo >= 0 && daysTo <= 7) {
        earningsHtml = `<div style="background:rgba(244,67,54,0.15);color:#f44336;padding:4px 6px;border-radius:4px;margin-bottom:6px;font-weight:bold;text-align:center;border:1px solid rgba(244,67,54,0.3)">
          ⚠️ Earnings in ${daysTo} days (${meta.earnings.date})
        </div>`;
      } else if (daysTo !== null && daysTo >= 0) {
        earningsHtml = `<div style="color:var(--muted);margin-bottom:4px">📅 Earnings: ${meta.earnings.date} (in ${daysTo} days)</div>`;
      }
    }

    // Sector display
    let sectorHtml = "";
    if (meta.sectorName) {
      if (currentMarket === 'US') {
        let sectorRSStr = `<span style="color:var(--muted)">Loading...</span>`;
        if (meta.sectorETF && meta.sectorHistory && meta.sectorHistory.length > 0 && window.BENCHMARK_DATA) {
          const secStats = calculatePatternStats(meta.sectorHistory, meta.sectorHistory.length - 1);
          if (secStats && secStats.rs) {
            const secColor = secStats.rs.percentile >= 70 ? 'var(--green)' : (secStats.rs.percentile < 40 ? 'var(--red)' : '#ff9800');
            sectorRSStr = `<span style="color:${secColor};font-weight:bold">RS ${secStats.rs.percentile}</span>`;
          }
        }
        sectorHtml = `<div style="color:var(--cyan);margin-bottom:6px;display:flex;justify-content:space-between">
          <span>Sector: ${meta.sectorName} (${meta.sectorETF || '—'})</span>
          <span>${sectorRSStr}</span>
        </div>`;
      } else if (currentMarket === 'TH' && RAW_DATA && RAW_DATA.thai_sector_heatmap) {
        const sectors = RAW_DATA.thai_sector_heatmap.sectors || [];
        const targetSec = sectors.find(s => (s.sector || '').toLowerCase() === (meta.sectorName || '').toLowerCase());
        if (targetSec) {
          const score = targetSec.momentum_score || 0;
          const secColor = score >= 60 ? 'var(--green)' : (score < 40 ? 'var(--red)' : '#ff9800');
          sectorHtml = `<div style="color:var(--cyan);margin-bottom:6px;display:flex;justify-content:space-between">
            <span>Sector: ${meta.sectorName}</span>
            <span style="color:${secColor};font-weight:bold">Score ${score.toFixed(1)}</span>
          </div>`;
        } else {
          sectorHtml = `<div style="color:var(--cyan);margin-bottom:6px">Sector: ${meta.sectorName}</div>`;
        }
      }
    }

    // Calculations UI
    let accuracyHtml = "";
    let patternsHtml = "";
    if (stats) {
      // 1. Inside Day / NR7 badges
      let badges = [];
      if (stats.insideDay) badges.push(`<span style="background:rgba(88,166,255,0.15);color:#58a6ff;padding:2px 4px;border-radius:3px;font-weight:bold;font-size:9px">INSIDE</span>`);
      if (stats.nr7) badges.push(`<span style="background:rgba(210,168,255,0.15);color:#d2a8ff;padding:2px 4px;border-radius:3px;font-weight:bold;font-size:9px">NR7</span>`);
      let badgeRow = badges.length > 0 ? `<div style="display:flex;gap:4px;margin-bottom:6px">${badges.join("")}</div>` : "";

      // 2. ATR Position Size
      let atrStr = "N/A";
      let posSizeStr = "N/A";
      if (stats.atr) {
        atrStr = `${stats.atr.val.toFixed(2)} (${stats.atr.pct}%)`;
        const settings = getSettings();
        const acct = parseFloat(settings.account_size) || 50000;
        const risk = parseFloat(settings.risk_pct) || 0.5;
        const riskAmt = acct * (risk / 100);
        const stopDistance = 2 * stats.atr.val;
        const shares = Math.floor(riskAmt / stopDistance);
        if (shares > 0 && barClose > 0) {
          const allocation = (shares * barClose) / acct * 100;
          const currencySign = currentMarket === 'TH' ? '฿' : '$';
          posSizeStr = `${shares} shares (${allocation.toFixed(1)}% / ${currencySign}${(shares * barClose).toLocaleString(undefined, {maximumFractionDigits:0})})`;
        }
      }

      // 3. Weekly trend
      const weeklyColor = stats.weeklyTrend.isWeeklyBull ? 'var(--green)' : 'var(--red)';
      const weeklyStr = `<span style="color:${weeklyColor};font-weight:bold">${stats.weeklyTrend.isWeeklyBull ? 'Bullish 📈' : 'Bearish 📉'}</span>`;

      // 4. RSI & Divergence
      let rsiDivergenceStr = "";
      if (stats.rsiDivergence.isBull) {
        rsiDivergenceStr = ` <span style="background:rgba(46,164,79,0.2);color:var(--green);padding:1px 3px;border-radius:2px;font-size:9px">BULL DIV</span>`;
      } else if (stats.rsiDivergence.isBear) {
        rsiDivergenceStr = ` <span style="background:rgba(207,34,46,0.2);color:var(--red);padding:1px 3px;border-radius:2px;font-size:9px">BEAR DIV</span>`;
      }
      const rsiColor = (stats.rsi >= 70) ? 'var(--red)' : (stats.rsi <= 30 ? 'var(--green)' : 'var(--text)');
      const rsiStr = stats.rsi ? `<span style="color:${rsiColor}">${stats.rsi}</span>${rsiDivergenceStr}` : "N/A";

      // 5. RS rating
      let rsStr = "N/A";
      if (stats.rs) {
        const rsColor = stats.rs.percentile >= 80 ? 'var(--green)' : (stats.rs.percentile < 50 ? 'var(--red)' : '#ff9800');
        rsStr = `<span style="color:${rsColor};font-weight:bold">Percentile ${stats.rs.percentile} (${stats.rs.raw}%)</span>`;
      }

      // 6. Day bias
      let dayBiasStr = "N/A";
      if (stats.dayBias) {
        const biasColor = parseFloat(stats.dayBias.avgReturn) >= 0 ? 'var(--green)' : 'var(--red)';
        dayBiasStr = `${stats.dayBias.day}: <span style="color:${biasColor}">${stats.dayBias.winRate}% (Avg ${stats.dayBias.avgReturn}%)</span>`;
      }

      // 7. Confluence Score
      let bullWeight = 0;
      let bearWeight = 0;
      if (stats.gap.streak > 0 && stats.gap.dir === 1) bullWeight += 1;
      if (stats.gap.streak > 0 && stats.gap.dir === -1) bearWeight += 1;
      if (stats.color.streak > 0 && stats.color.dir === 1) bullWeight += 1;
      if (stats.color.streak > 0 && stats.color.dir === -1) bearWeight += 1;
      if (stats.pullback) bullWeight += 1.5;
      if (stats.breakout) bullWeight += 2;
      if (stats.volumeSpike) {
        if (priceData.close > priceData.open) bullWeight += 1.5;
        else if (priceData.close < priceData.open) bearWeight += 1.5;
      }
      if (stats.volumeDryUp) bullWeight += 1;
      if (stats.hammer) bullWeight += 1.5;
      if (stats.strongClose) bullWeight += 1;
      if (stats.wideRangeBull) bullWeight += 1;
      if (stats.wideRangeBear) bearWeight += 1;
      // Note: insideDay and nr7 are neutral, so they are not counted towards bull/bear weights.
      if (stats.weeklyTrend.isWeeklyBull) bullWeight += 1;
      if (stats.rsiDivergence.isBull) bullWeight += 2;
      if (stats.rsiDivergence.isBear) bearWeight += 2;
      if (stats.regime.isAbove) bullWeight += 1;
      else bearWeight += 1;

      const netScore = bullWeight - bearWeight;
      let confluenceText = "Neutral";
      let confluenceColor = 'var(--text)';
      if (netScore >= 5) {
        confluenceText = "Strong Bullish 🐂";
        confluenceColor = 'var(--green)';
      } else if (netScore >= 1) {
        confluenceText = "Bullish";
        confluenceColor = 'var(--green)';
      } else if (netScore <= -5) {
        confluenceText = "Strong Bearish 🐻";
        confluenceColor = 'var(--red)';
      } else if (netScore <= -1) {
        confluenceText = "Bearish";
        confluenceColor = 'var(--red)';
      }

      const confluenceScoreHtml = `<div style="border-top:1px solid rgba(255,255,255,0.15);margin-top:6px;padding-top:6px;display:flex;justify-content:space-between;font-weight:bold">
        <span>Confluence Score:</span>
        <span style="color:${confluenceColor}">${bullWeight.toFixed(1)}B - ${bearWeight.toFixed(1)}S (Net: ${netScore > 0 ? '+' : ''}${netScore.toFixed(1)})</span>
      </div>
      <div style="display:flex;justify-content:space-between;color:var(--muted);font-size:10px;margin-bottom:6px">
        <span>Bias assessment:</span>
        <span style="color:${confluenceColor}">${confluenceText}</span>
      </div>`;

      accuracyHtml = `
        <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:6px;padding:6px;margin-bottom:8px">
          ${badgeRow}
          <div style="display:flex;justify-content:space-between"><span>ATR (14):</span> <span>${atrStr}</span></div>
          <div style="display:flex;justify-content:space-between"><span>Rec. Size (2 ATR):</span> <span style="color:var(--gold)">${posSizeStr}</span></div>
          <div style="display:flex;justify-content:space-between"><span>Weekly Trend:</span> <span>${weeklyStr}</span></div>
          <div style="display:flex;justify-content:space-between"><span>RSI (14):</span> <span>${rsiStr}</span></div>
          <div style="display:flex;justify-content:space-between"><span>Relative Strength:</span> <span>${rsStr}</span></div>
          <div style="display:flex;justify-content:space-between"><span>Day Bias:</span> <span>${dayBiasStr}</span></div>
          ${confluenceScoreHtml}
        </div>
      `;

      let activePatternsList = "";
      const renderRecent = (label, icon, statsObj, periods, col='var(--text)') => {
        let html = `<div style="margin-bottom:4px"><div style="color:${col}">${icon} ${label}</div>`;
        periods.forEach(p => {
          html += `<div style="display:flex;justify-content:space-between;font-size:10px;color:var(--muted)"><span>· ${p === 'all' ? 'All Time' : 'Last ' + p + ' times'}:</span> ${formatStat(statsObj, p)}</div>`;
        });
        html += `</div>`;
        return html;
      };

      const renderForward = (label, icon, statsObj, col='var(--text)') => {
        let html = `<div style="margin-bottom:4px"><div style="color:${col}">${icon} ${label}</div>`;
        const periods = Object.keys(statsObj).sort((a,b) => parseInt(a) - parseInt(b));
        periods.forEach(p => {
          html += `<div style="display:flex;justify-content:space-between;font-size:10px;color:var(--muted)"><span>· Hold ${p} Days:</span> ${formatStat(statsObj, p)}</div>`;
        });
        html += `</div>`;
        return html;
      };

      if (stats.gap.streak > 0) {
        const gName = stats.gap.dir === 1 ? 'Gap Up' : 'Gap Down';
        const gCol = stats.gap.dir === 1 ? 'var(--green)' : 'var(--red)';
        activePatternsList += renderRecent(`${gName} (${stats.gap.streak} days)`, stats.gap.dir === 1 ? '📈' : '📉', stats.gap.stats, [10, 20, 'all'], gCol);
      }
      if (stats.color.streak > 0) {
        const cName = stats.color.dir === 1 ? 'Green Bar' : 'Red Bar';
        const cCol = stats.color.dir === 1 ? 'var(--green)' : 'var(--red)';
        activePatternsList += renderRecent(`${cName} (${stats.color.streak} days)`, stats.color.dir === 1 ? '🟩' : '🟥', stats.color.stats, [5, 10, 'all'], cCol);
      }
      if (stats.pullback) {
        activePatternsList += renderForward(`SMA50 Pullback Bounce`, '↩️', stats.pullback.stats, '#ff9800');
      }
      if (stats.breakout) {
        activePatternsList += renderForward(`20-Day Breakout`, '🚀', stats.breakout.stats, 'var(--green)');
      }
      if (stats.volumeSpike) {
        activePatternsList += renderForward(`Volume Climax (>2x)`, '📊', stats.volumeSpike.stats, '#58a6ff');
      }
      if (stats.volumeDryUp) {
        activePatternsList += renderForward(`Volume Dry-Up (<0.5x)`, '🏜️', stats.volumeDryUp.stats, '#a3a3a3');
      }
      if (stats.hammer) {
        activePatternsList += renderForward(`Rejection Tail (Pin Bar)`, '🔨', stats.hammer.stats, '#ffeb3b');
      }
      if (stats.strongClose) {
        activePatternsList += renderForward(`Strong Close (Top 25% + Vol)`, '💪', stats.strongClose.stats, 'var(--green)');
      }
      if (stats.wideRangeBull) {
        activePatternsList += renderForward(`Wide Range Bullish (>1.5x)`, '📏📈', stats.wideRangeBull.stats, '#d2a8ff');
      }
      if (stats.wideRangeBear) {
        activePatternsList += renderForward(`Wide Range Bearish (>1.5x)`, '📏📉', stats.wideRangeBear.stats, '#ff7b72');
      }

      if (activePatternsList) {
        patternsHtml = `
          <div style="border-top:1px solid rgba(255,255,255,0.15);padding-top:6px;margin-top:6px">
            <div style="color:#c9d1d9;margin-bottom:4px;font-weight:bold">🧩 Active Pattern Stats</div>
            ${activePatternsList}
          </div>
        `;
      }
    } else {
      accuracyHtml = `<div style="margin-top:4px">Not enough data</div>`;
    }

    legend.innerHTML = `
      ${earningsHtml}
      <div style="font-weight:bold;font-size:13px;margin-bottom:2px;">${symbol} <span style="font-size:10px;color:var(--muted);font-weight:normal;margin-left:4px">${priceData.time}</span></div>
      ${sectorHtml}
      <div style="display:flex;gap:6px;margin-bottom:8px;border-bottom:1px solid rgba(255,255,255,0.15);padding-bottom:6px;font-size:10px;color:var(--muted)">
        <span>O: <span style="color:${color}">${priceData.open.toFixed(2)}</span></span>
        <span>H: <span style="color:${color}">${priceData.high.toFixed(2)}</span></span>
        <span>L: <span style="color:${color}">${priceData.low.toFixed(2)}</span></span>
        <span>C: <span style="color:${color}">${priceData.close.toFixed(2)}</span></span>
        <span>Vol: <span style="color:${color}">${(barVol >= 1e6 ? (barVol/1e6).toFixed(1) + 'M' : (barVol/1e3).toFixed(0) + 'K')}</span></span>
      </div>
      ${accuracyHtml}
      ${patternsHtml}
    `;
  };

  setLegendContent(prices[prices.length-1]);
  chart.subscribeCrosshairMove((param) => {
    if (param.point === undefined || !param.time || param.point.x < 0 || param.point.x > container.clientWidth || param.point.y < 0 || param.point.y > container.clientHeight) {
      setLegendContent(prices[prices.length-1]);
    } else {
      const priceData = param.seriesData.get(candleSeries);
      if (priceData) {
        setLegendContent(priceData);
      }
    }
  });
}

async function initFavChart(symbol) {
  const container = document.getElementById(`fav-chart-${symbol}`);
  if (!container) return;
  if (container.querySelector('.tv-lightweight-charts')) return;

  try {
    const res = await fetch(`/api/history/${symbol}`);
    if (!res.ok) throw new Error('API Error');
    const data = await res.json();

    if (container._resizeObserver) {
      container._resizeObserver.disconnect();
      delete container._resizeObserver;
    }
    container.innerHTML = '';
    container.classList.remove('chart-loading');
    container.classList.add('chart-container');

    const chart = LightweightCharts.createChart(container, {
      width: container.clientWidth,
      height: container.clientHeight || 560,
      layout: { background: { type: 'solid', color: '#0d1117' }, textColor: '#c9d1d9' },
      grid: { vertLines: { color: 'rgba(240, 246, 252, 0.05)' }, horzLines: { color: 'rgba(240, 246, 252, 0.05)' } },
      crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
      timeScale: { borderColor: 'rgba(240, 246, 252, 0.1)' }
    });

    const resizeObserver = new ResizeObserver(entries => {
      for (let entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0) {
          chart.resize(width, height);
        }
      }
    });
    resizeObserver.observe(container);
    container._resizeObserver = resizeObserver;

    const candleSeries = chart.addCandlestickSeries({
      upColor: '#2ea44f', downColor: '#cf222e', borderUpColor: '#2ea44f',
      borderDownColor: '#cf222e', wickUpColor: '#2ea44f', wickDownColor: '#cf222e'
    });

    const volSeries = chart.addHistogramSeries({
      color: '#2188ff', priceFormat: { type: 'volume' }, priceScaleId: 'volume'
    });

    chart.priceScale('volume').applyOptions({ scaleMargins: { top: 0.78, bottom: 0 } });

    const prices = data.map(b => ({ time: b.time, open: b.open, high: b.high, low: b.low, close: b.close }));
    const vols = data.map(b => ({ time: b.time, value: b.value, color: b.close >= b.open ? 'rgba(46,164,79,0.3)' : 'rgba(207,34,46,0.3)' }));

    candleSeries.setData(prices);
    volSeries.setData(vols);

    const closes = data.map(b => b.close);
    const addLine = (points, color, title) => {
      if (!points.length) return;
      const s = chart.addLineSeries({ color, lineWidth: 1, title, crosshairMarkerVisible: false, lastPriceAnimationLimit: 0 });
      s.setData(points);
    };

    const calcSMA = (vals, len) => {
      const res = [];
      for (let i = 0; i < vals.length; i++) {
        if (i < len - 1) continue;
        let sum = 0;
        for (let j = 0; j < len; j++) sum += vals[i - j];
        res.push({ time: data[i].time, value: sum / len });
      }
      return res;
    };

    addLine(calcSMA(closes, 50), '#ff9800', 'SMA50');
    addLine(calcSMA(closes, 150), '#2196f3', 'SMA150');
    addLine(calcSMA(closes, 200), '#9c27b0', 'SMA200');

    setupChartLegend(chart, container, symbol, data, candleSeries);
    chart.timeScale().fitContent();
  } catch (err) {
    container.innerHTML = `<span style="color:var(--red)">❌ โหลดกราฟไม่สำเร็จสำหรับ ${symbol}</span>`;
  }
}

async function renderFavoritesCard() {
  const containerTitle = document.getElementById('favoritesSection');
  const containerCard = document.getElementById('favoritesCard');
  const containerContent = document.getElementById('favoritesContent');

  if (!containerTitle || !containerCard || !containerContent) return;

  const isTH = currentMarket === 'TH';
  const marketStars = _starredStocks.filter(sym => {
    const isSymTH = sym.endsWith('.BK');
    return isTH ? isSymTH : !isSymTH;
  });

  if (marketStars.length === 0) {
    containerTitle.style.display = 'flex';
    containerCard.style.display = 'block';
    containerContent.innerHTML = `
      <div style="text-align:center; padding:30px 20px; color:var(--muted);">
        <div style="font-size:2.5rem; margin-bottom:12px; color:var(--gold);">☆</div>
        <h4 style="margin:0 0 8px 0; color:var(--text);">ยังไม่มีหุ้นที่ติดดาวติดตามไว้ (No Starred Stocks)</h4>
        <p style="margin:0 auto; max-width:600px; font-size:.82rem; line-height:1.6;">
          คุณสามารถเลือกติดดาวหุ้นที่ต้องการติดตามเพื่อซื้อหรือเฝ้าดูราคาและการเปลี่ยนแปลงล่าสุดได้ง่ายๆ
          โดยการกดปุ่ม <span style="color:var(--gold); font-weight:bold;">☆</span> ข้างชื่อย่อหุ้นในตารางสเต็ปต่างๆ ด้านล่าง (เช่น VCP Screener, CANSLIM หรือ Watchlist)
        </p>
      </div>
    `;
    return;
  }

  containerTitle.style.display = 'flex';
  containerCard.style.display = 'block';

  const priceSign = isTH ? '฿' : '$';

  let rowsHtml = marketStars.map((sym, i) => {
    let companyName = '';
    let price = null;
    let state = 'กำลังโหลดราคาล่าสุด...';
    let changePct = null;

    const foundData = findStockInRawData(sym);
    if (foundData) {
      companyName = foundData.companyName || '';
      price = foundData.price;
      state = foundData.state || 'เฝ้าติดตาม';
      changePct = foundData.changePct;
    }

    if (_favoritesCache[sym]) {
      price = _favoritesCache[sym].price;
      changePct = _favoritesCache[sym].changePct;
    }

    const priceDisplay = price != null ? `${priceSign}${price.toFixed(2)}` : '—';
    let changeDisplay = '—';
    let changeCol = 'var(--muted)';
    if (changePct != null) {
      const sign = changePct >= 0 ? '+' : '';
      changeDisplay = `${sign}${changePct.toFixed(2)}%`;
      changeCol = changePct >= 0 ? 'var(--green)' : 'var(--red)';
    }

    return `
      <tr style="cursor:pointer" onclick="toggleFavRow(${i})" data-symbol="${sym}">
        <td style="font-weight:700">
          <span class="star-btn" style="color:var(--gold); margin-right:8px;" onclick="toggleStar(event, '${sym}')">★</span>
          <span class="sym">${sym}</span>
          ${companyName ? `<br><small style="color:var(--muted); font-weight:normal">${companyName}</small>` : ''}
        </td>
        <td class="price" id="fav-price-${sym}">${priceDisplay}</td>
        <td style="font-family:'JetBrains Mono',monospace; font-weight:700; color:${changeCol}" id="fav-change-${sym}">
          ${changeDisplay}
        </td>
        <td>
          <span class="state-pill ${getStateClass(state)}" id="fav-state-${sym}">${state}</span>
        </td>
        <td>
          <button class="btn-primary" style="padding:4px 10px; font-size:.72rem; border-radius:6px; background:var(--bg3); border:1px solid var(--border); color:var(--text);" onclick="toggleFavRowClick(event, ${i})">
            📊 ดูกราฟ
          </button>
        </td>
      </tr>
      <tr class="expand-row" id="fav-row-${i}">
        <td colspan="5" class="expand-cell">
          <div id="fav-chart-${sym}" class="chart-loading"></div>
        </td>
      </tr>
    `;
  }).join('');

  containerContent.innerHTML = `
    <div style="overflow-x:auto">
      <table style="width:100%">
        <thead>
          <tr>
            <th>หุ้นที่ติดตาม (Symbol)</th>
            <th>ราคาล่าสุด</th>
            <th>การเปลี่ยนแปลงรายวัน</th>
            <th>สถานะความเห็น</th>
            <th>การควบคุม</th>
          </tr>
        </thead>
        <tbody>
          ${rowsHtml}
        </tbody>
      </table>
    </div>
  `;

  marketStars.forEach(sym => {
    fetchStockPriceAndChange(sym);
  });
}


function saveSettings() {
  localStorage.setItem('tradingSettings', JSON.stringify({
    account: document.getElementById('settingAccount').value,
    risk: document.getElementById('settingRisk').value,
    target: document.getElementById('settingTarget').value,
    market: currentMarket,
  }));
}

function onSliderInput() {
  const riskVal = parseFloat(document.getElementById('settingRisk').value) || 0.5;
  const targetVal = parseFloat(document.getElementById('settingTarget').value) || 2.0;

  const valRiskEl = document.getElementById('valRisk');
  if (valRiskEl) valRiskEl.textContent = riskVal.toFixed(1) + '%';
  const valTargetEl = document.getElementById('valTarget');
  if (valTargetEl) valTargetEl.textContent = targetVal.toFixed(1) + 'R';

  recalculateAndRenderBreakout();
}

function loadSettings() {
  const s = localStorage.getItem('tradingSettings');
  if (!s) return;
  try {
    const p = JSON.parse(s);
    if (p.account) document.getElementById('settingAccount').value = p.account;
    if (p.risk) {
      document.getElementById('settingRisk').value = p.risk;
      const valRiskEl = document.getElementById('valRisk');
      if (valRiskEl) valRiskEl.textContent = parseFloat(p.risk).toFixed(1) + '%';
    }
    if (p.target) {
      document.getElementById('settingTarget').value = p.target;
      const valTargetEl = document.getElementById('valTarget');
      if (valTargetEl) valTargetEl.textContent = parseFloat(p.target).toFixed(1) + 'R';
    }
    // Restore market preference if previously selected
    if (p.market && (p.market === 'TH' || p.market === 'US')) {
      currentMarket = p.market;
    }
  } catch(e) {}
}

// ─── THEME TOGGLE ────────────────────────────────────────────────────────────
function applyTheme(theme) {
  if (theme === 'light') {
    document.documentElement.setAttribute('data-theme', 'light');
    const t = document.getElementById('themeToggle'); if (t) t.textContent = '☼';
  } else {
    document.documentElement.removeAttribute('data-theme');
    const t = document.getElementById('themeToggle'); if (t) t.textContent = '☾';
  }
}
function toggleTheme() {
  const current = localStorage.getItem('theme') === 'light' ? 'light' : 'dark';
  const next = current === 'light' ? 'dark' : 'light';
  localStorage.setItem('theme', next);
  applyTheme(next);
}
// Apply theme as early as possible (before paint) to avoid flash
(function initTheme(){
  const saved = localStorage.getItem('theme');
  if (saved === 'light') applyTheme('light');
})();
// Chart palette helper — reads current CSS variables so charts adapt to theme
function getChartTheme() {
  const s = getComputedStyle(document.documentElement);
  return {
    bg: s.getPropertyValue('--bg').trim() || '#0d1117',
    text: s.getPropertyValue('--text').trim() || '#e6edf3',
    border: s.getPropertyValue('--border').trim() || '#30363d',
    green: s.getPropertyValue('--green').trim() || '#3fb950',
    red: s.getPropertyValue('--red').trim() || '#f85149',
  };
}

function getSettings() {
  return {
    account_size: document.getElementById('settingAccount').value || '50000',
    risk_pct: document.getElementById('settingRisk').value || '0.5',
    target_r: document.getElementById('settingTarget').value || '2.0',
  };
}

function showLegend(key) {
  document.getElementById('modalTitle').textContent = LEGENDS[key].title;
  let html = LEGENDS[key].html;
  const benchmarkName = currentMarket === 'TH' ? 'SET Index' : 'S&P500';
  html = html.replace(/S&amp;P500/g, benchmarkName).replace(/S&P500/g, benchmarkName);
  document.getElementById('modalBody').innerHTML = html;
  document.getElementById('modalOverlay').classList.add('open');
}
function closeModal() { document.getElementById('modalOverlay').classList.remove('open'); }

async function setMarket(m) {
  currentMarket = m;
  document.querySelectorAll('.mkt-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(`mkt-${m}`).classList.add('active');

  // Dynamic currency label swap
  const accountLabel = document.getElementById('labelAccountSize');
  if (accountLabel) {
    accountLabel.textContent = m === 'TH' ? 'Account Size (฿)' : 'Account Size ($)';
  }

  // Pre-fetch benchmark data for the market
  await fetchBenchmarkData(m);

  await refreshHistoryList();
  await loadData();
  if (CURRENT_DASHBOARD_TAB === 'results') await loadSignalResults();
  if (CURRENT_DASHBOARD_TAB === 'decisions') await loadTradeDecisions();
  if (CURRENT_DASHBOARD_TAB === 'edge') await loadEdgeLab();
}

async function refreshHistoryList() {
  try {
    const res = await fetch(`/api/runs?market=${currentMarket}&limit=60`);
    const d = await res.json();
    const sel = document.getElementById('historySelect');
    const currentVal = sel.value;
    sel.innerHTML = '<option value="">⚡ ล่าสุด (Live)</option>';
    (d.runs || []).forEach((r, i) => {
      const label = i === 0 ? `${r.replace('T',' ')} (ล่าสุด)` : r.replace('T',' ');
      const opt = document.createElement('option');
      opt.value = r;
      opt.textContent = label;
      sel.appendChild(opt);
    });
    // restore selection if still available
    if (currentVal && [...sel.options].some(o => o.value === currentVal)) {
      sel.value = currentVal;
    }
  } catch(e) { console.warn('Could not load history list', e); }
}

function onHistoryChange() {
  const at = document.getElementById('historySelect').value;
  const badge = document.getElementById('historyBadge');
  badge.style.display = at ? 'inline-block' : 'none';
  loadData(at);
}

async function loadData(at) {
  const ts = document.getElementById('ts');
  ts.textContent = `⏳ กำลังโหลดข้อมูล...ด ${currentMarket}...`;
  try {
    const url = at
      ? `/api/data?market=${currentMarket}&at=${encodeURIComponent(at)}`
      : `/api/data?market=${currentMarket}`;
    const res = await fetch(url);
    RAW_DATA = await res.json();

    if (RAW_DATA.breadth) renderBreadth(RAW_DATA.breadth);
    if (RAW_DATA.exposure) renderExposure(RAW_DATA.exposure);
    if (RAW_DATA.ibd) renderIBD(RAW_DATA.ibd);
    if (RAW_DATA.earnings_trade) renderEarnings(RAW_DATA.earnings_trade);
    if (RAW_DATA.breakout_plan) renderBreakoutPlan(RAW_DATA.breakout_plan);
    if (RAW_DATA.uptrend) renderUptrend(RAW_DATA.uptrend);
    if (RAW_DATA.downtrend) renderDowntrend(RAW_DATA.downtrend);
    if (RAW_DATA.canslim) renderCANSLIM(RAW_DATA.canslim);
    renderThaiSwing(RAW_DATA.thai_swing);
    renderThaiBreadth(RAW_DATA.thai_breadth);
    renderThaiSectorHeatmap(RAW_DATA.thai_sector_heatmap);
    renderThaiWatchlists(RAW_DATA.thai_watchlists);
    renderThaiDividends(RAW_DATA.thai_dividends);

    const usOnly = currentMarket === 'US';
    const thOnly = currentMarket === 'TH';
    // US-only sections (IBD, Earnings, Downtrend)
    ['ibdSection','ibdCard','earnSection','earnCard',
     'downtrendSection','downtrendCard'].forEach(id => {
      document.getElementById(id).style.display = usOnly ? '' : 'none';
    });
    // Uptrend Analyzer: script only supports US market data — show warning badge for TH
    const uptrendNote = document.getElementById('uptrendUsNote');
    const uptrendCard = document.getElementById('uptrendCard');
    if (uptrendNote && uptrendCard) {
      uptrendNote.style.display = thOnly ? 'inline' : 'none';
      uptrendCard.style.opacity  = thOnly ? '0.5' : '1';
    }
    // CANSLIM: visible for both US and TH (backend runs it for both markets)
    // Thai Swing + TH Suite — TH only
    ['thaiSwingSection','thaiSwingCard',
     'thaiSuiteSection',
     'thBreadthSection','thBreadthCard',
     'thSectorSection','thSectorCard',
     'thWatchlistsSection','thWatchlistsCard',
     'thDividendsSection','thDividendsCard'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.style.display = thOnly ? '' : 'none';
    });

    updateVCP();
    renderFavoritesCard();

    const runAt = RAW_DATA._run_at || '';
    if (at) {
      ts.textContent = `📅 ข้อมูลย้อนหลัง ${at.replace('T',' ')} (${currentMarket})`;
    } else if (RAW_DATA.breadth?.metadata?.generated_at) {
      let genAtStr = RAW_DATA.breadth.metadata.generated_at;
      try {
        if (!genAtStr.endsWith('Z') && genAtStr.length === 19) {
          // Legacy format "YYYY-MM-DD HH:MM:SS" which was actually UTC on some servers or Local on others.
          // We will assume UTC and append Z if it looks like a UTC timestamp that caused 07:50:52 in TH,
          // but safely, we'll try to parse it first. If it's standard ISO, it handles natively.
          genAtStr = genAtStr.replace(' ', 'T') + 'Z';
        }
        const d = new Date(genAtStr);
        if (!isNaN(d.getTime())) {
          genAtStr = d.getFullYear() + "-" +
                     String(d.getMonth() + 1).padStart(2, '0') + "-" +
                     String(d.getDate()).padStart(2, '0') + " " +
                     String(d.getHours()).padStart(2, '0') + ":" +
                     String(d.getMinutes()).padStart(2, '0') + ":" +
                     String(d.getSeconds()).padStart(2, '0');
        }
      } catch(e) {}
      ts.textContent = `ข้อมูลตลาด ${currentMarket} ณ ${genAtStr}`;
    } else {
      ts.textContent = `⚠️ ไม่มีข้อมูลล่าสุดสำหรับตลาด ${currentMarket} — กรุณารัน Fresh Analysis`;
    }
  } catch(e) {
    console.error(e);
    ts.textContent = `❌ โหลดข้อมูลไม่สำเร็จ`;
  }
}

function renderBreadth(b) {
  if (!b || !b.composite) return;
  const s = b.composite.composite_score || 0;
  const zone = b.composite.zone || 'Unknown';
  const colors = { Strong:'#00e676', Healthy:'#8bc34a', Neutral:'#ffd700', Weakening:'#ff9800', Critical:'#f44336' };
  const col = colors[zone] || 'var(--cyan)';
  const scoreEl = document.getElementById('mbScore');
  scoreEl.textContent = s.toFixed(1);
  scoreEl.style.color = col;
  const badge = document.getElementById('mbBadge');
  badge.textContent = zone;
  badge.style.background = col + '25';
  badge.style.color = col;
  document.getElementById('mbBar').style.width = s + '%';
  document.getElementById('mbBar').style.background = col;
  document.getElementById('mbExposure').textContent = b.composite.exposure_guidance || '—';
  document.getElementById('mbComponents').innerHTML = Object.entries(b.components || {}).map(([k, v]) => {
    const score = v.score || 0;
    const c = score >= 70 ? '#00e676' : score >= 40 ? '#ffd700' : '#f44336';
    return `<div class="component" style="border-left-color:${c}">
      <div class="component-header"><span class="component-name">${k.replace(/_/g,' ').toUpperCase()}</span><span class="component-score">${typeof score === 'number' ? score.toFixed(0) : score}</span></div>
      <div class="component-bar"><div class="component-bar-fill" style="width:${score}%;background:${c}"></div></div>
      <div class="component-signal">${v.signal || ''}</div>
    </div>`;
  }).join('');
}

function renderUptrend(u) {
  if (!u || !u.composite) return;
  const s = u.composite.composite_score || 0;
  const zone = (u.composite.zone || '').replace(/\s+/g, '');
  const zoneLabel = u.composite.zone || '—';
  const colors = { StrongBull:'#00e676', Bull:'#8bc34a', Neutral:'#ffd700', Cautious:'#ff9800', Bear:'#f44336' };
  const col = colors[zone] || 'var(--purple)';
  const scoreEl = document.getElementById('uptrendScore');
  scoreEl.textContent = s.toFixed(1);
  scoreEl.style.color = col;
  const zoneEl = document.getElementById('uptrendZone');
  zoneEl.textContent = zoneLabel;
  zoneEl.style.background = col + '25';
  zoneEl.style.color = col;
  document.getElementById('uptrendBar').style.width = s + '%';
  document.getElementById('uptrendBar').style.background = col;
  document.getElementById('uptrendGuidance').textContent = u.composite.exposure_guidance || '—';
  const warnings = u.composite.active_warnings || [];
  document.getElementById('uptrendWarnings').innerHTML = warnings.map(w =>
    `<div style="font-size:.7rem;color:var(--orange);margin-top:4px">⚠️ ${typeof w === 'string' ? w : (w.label || w.flag || JSON.stringify(w))}</div>`
  ).join('');
}

function renderIBD(ibd) {
  const state = ibd.market_distribution_state || {};
  const action = ibd.portfolio_action || {};
  const risk = state.overall_risk_level || 'UNKNOWN';
  const indexResults = state.index_results || [];
  const indexCards = indexResults.map(idx => {
    const rc = `risk-${idx.risk_level || 'LOW'}`;
    const ddToday = idx.is_distribution_day_today ? '🔴 DD Today!' : '✅ No DD Today';
    return `<div class="ibd-index-card">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
        <span class="sym">${idx.symbol}</span><span class="${rc}">${idx.risk_level}</span>
      </div>
      <div style="font-size:.72rem;color:var(--muted);margin-bottom:8px">${ddToday}</div>
      <div class="ibd-dd-counts">
        <div class="ibd-dd-count"><div class="val" style="color:${(idx.d5_count||0)>=3?'var(--red)':'var(--text)'}">${idx.d5_count??'—'}</div><div class="lbl">d5</div></div>
        <div class="ibd-dd-count"><div class="val" style="color:${(idx.d15_count||0)>=5?'var(--red)':'var(--text)'}">${idx.d15_count??'—'}</div><div class="lbl">d15</div></div>
        <div class="ibd-dd-count"><div class="val" style="color:${(idx.d25_count||0)>=7?'var(--red)':'var(--text)'}">${idx.d25_count??'—'}</div><div class="lbl">d25</div></div>
      </div>
    </div>`;
  }).join('');
  const actionLabel = action.recommended_action || action.action;
  const actionHtml = actionLabel
    ? `<div class="logic-box" style="margin-top:12px"><strong>Portfolio Action [${action.instrument||''}]:</strong> ${actionLabel} — ${action.rationale||''}</div>` : '';
  document.getElementById('ibdContent').innerHTML = `
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px">
      <div style="font-size:.85rem;color:var(--muted)">Overall Risk:</div>
      <span class="risk-${risk}" style="font-size:1rem">${risk}</span>
      <div style="font-size:.75rem;color:var(--muted);margin-left:auto">As of: ${state.as_of||'—'}</div>
    </div>
    <div class="ibd-index-grid">${indexCards}</div>${actionHtml}`;
}

function renderExposure(e) {
  document.getElementById('expRec').textContent = e.recommendation || '—';
  document.getElementById('expCeiling').textContent = (e.exposure_ceiling_pct || 0) + '%';
  document.getElementById('expBias').textContent = e.bias || '—';
  document.getElementById('expConf').textContent = e.confidence || '—';
  const colors = { CASH_PRIORITY:'var(--red)', REDUCE_ONLY:'var(--red)', NEW_ENTRY_ALLOWED:'var(--green)' };
  document.getElementById('expRec').style.color = colors[e.recommendation] || 'var(--text)';
  document.getElementById('expRationale').innerHTML = `<strong>ตรรกะ:</strong> ${e.rationale||'—'}`;
}

function renderBreakoutPlan(plan) {
  CURRENT_BREAKOUT_PLAN = plan;
  recalculateAndRenderBreakout();
}

function recalculateAndRenderBreakout() {
  if (!CURRENT_BREAKOUT_PLAN) return;
  const plan = CURRENT_BREAKOUT_PLAN;
  const actionable = plan.actionable_orders || [];
  const watchlist = plan.watchlist || [];
  const revalidation = plan.revalidation || [];
  const summary = plan.summary || {};
  const params = plan.parameters || {};
  const priceSign = currentMarket === 'TH' ? '฿' : '$';

  // Read current settings
  const accountSize = parseFloat(document.getElementById('settingAccount').value) || 50000;
  const baseRiskPct = parseFloat(document.getElementById('settingRisk').value) || 0.5;
  const targetR = parseFloat(document.getElementById('settingTarget').value) || 2.0;

  let actionableCount = 0;
  let tableRows = '';

  actionable.forEach(o => {
    const tp = o.trade_plan || {};
    const signalEntry = tp.signal_entry || 0;
    const worstEntry = tp.worst_entry || 0;
    const stopLoss = tp.stop_loss_price || 0;
    const multiplier = tp.sizing_multiplier != null ? tp.sizing_multiplier : 1.0;
    const riskPerShare = worstEntry - stopLoss;

    // Sizing calculation client-side
    const effectiveRiskPct = baseRiskPct * multiplier;
    let shares = 0;
    let riskDollars = 0;
    if (riskPerShare > 0 && effectiveRiskPct > 0) {
      const dollarRisk = accountSize * (effectiveRiskPct / 100);
      const maxPositionPct = params.max_position_pct != null ? params.max_position_pct : 10.0;
      const maxByPos = Math.floor((accountSize * (maxPositionPct / 100)) / worstEntry);
      shares = Math.min(Math.floor(dollarRisk / riskPerShare), maxByPos);
      if (shares < 0) shares = 0;
      riskDollars = shares * riskPerShare;
    }

    if (shares > 0) {
      actionableCount++;
    }

    // Dynamic targets client-side
    const targetPrice = signalEntry + targetR * (signalEntry - stopLoss);
    const target1rPrice = signalEntry + 1.0 * (signalEntry - stopLoss);

    tableRows += `<tr>
      <td>
        <span class="star-btn" onclick="toggleStar(event, '${o.symbol}')" title="${isStarred(o.symbol) ? 'เลิกติดตาม' : 'ติดตาม'}">
          ${isStarred(o.symbol) ? '★' : '☆'}
        </span>
        <span class="sym">${o.symbol}</span><br><small style="color:var(--muted)">${o.company_name||''}</small>
      </td>
      <td>
        <span class="cls-actionable">ACTIONABLE</span><br>
        <button class="btn-paper-add" onclick="event.stopPropagation(); paperAddPick('${o.symbol}', '${currentMarket}', ${signalEntry}, ${stopLoss}, ${targetPrice}, 'step-5-breakout', ${o.composite_score||100}, ${shares})" title="Add to Paper Portfolio">➕ Add to Paper</button>
      </td>
      <td class="entry-price">${priceSign}${signalEntry.toFixed(2)}<br><small style="color:var(--muted)">max: ${priceSign}${worstEntry.toFixed(2)}</small></td>
      <td class="stop-price">${priceSign}${stopLoss.toFixed(2)}<br><small style="color:var(--muted)">${(tp.risk_pct_worst||0).toFixed(1)}% risk</small></td>
      <td class="target-price">
        ${priceSign}${targetPrice.toFixed(2)}<br>
        <small style="color:var(--muted)">${targetR.toFixed(1)}R (full)</small>
        ${target1rPrice ? `<br><small style="color:#ffb347">⚡ 1R: ${priceSign}${target1rPrice.toFixed(2)}</small>` : ''}
        ${target1rPrice ? `<br><small style="color:var(--muted);font-size:.62rem">💡 ขาย 50% @ 1R · trail ส่วนที่เหลือ</small>` : ''}
      </td>
      <td style="font-family:'JetBrains Mono',monospace">${shares.toLocaleString()}<br><small style="color:var(--muted)">${priceSign}${riskDollars.toFixed(0)} risk</small></td>
      <td style="font-size:.72rem;color:var(--muted)">${o.sector||'—'}</td>
    </tr>`;
  });

  revalidation.forEach(o => {
    tableRows += `<tr>
      <td>
        <span class="star-btn" onclick="toggleStar(event, '${o.symbol}')" title="${isStarred(o.symbol) ? 'เลิกติดตาม' : 'ติดตาม'}">
          ${isStarred(o.symbol) ? '★' : '☆'}
        </span>
        <span class="sym">${o.symbol}</span><br><small style="color:var(--muted)">${o.company_name||''}</small>
      </td>
      <td><span class="cls-revalidation">REVALIDATE</span></td>
      <td class="entry-price" colspan="2">ยืนยัน Breakout ก่อนซื้อ<br><small style="color:var(--muted)">Current: ${priceSign}${(o.current_price||0).toFixed(2)}</small></td>
      <td colspan="2" style="font-size:.75rem;color:var(--muted)">${o.revalidation_note||''}</td>
      <td style="font-size:.72rem;color:var(--muted)">${o.sector||'—'}</td>
    </tr>`;
  });

  watchlist.forEach(w => {
    tableRows += `<tr style="opacity:.7">
      <td>
        <span class="star-btn" onclick="toggleStar(event, '${w.symbol}')" title="${isStarred(w.symbol) ? 'เลิกติดตาม' : 'ติดตาม'}">
          ${isStarred(w.symbol) ? '★' : '☆'}
        </span>
        <span class="sym">${w.symbol}</span><br><small style="color:var(--muted)">${w.company_name||''}</small>
      </td>
      <td><span class="cls-watchlist">WATCHLIST</span></td>
      <td class="entry-price">${priceSign}${(w.pivot_price||0).toFixed(2)}<br><small style="color:var(--muted)">pivot level</small></td>
      <td class="stop-price">${priceSign}${(w.stop_loss_price||0).toFixed(2)}</td>
      <td colspan="2" style="font-size:.75rem;color:var(--muted)">${w.alert_trigger||'—'}</td>
      <td style="font-size:.72rem;color:var(--muted)">${w.sector||'—'}</td>
    </tr>`;
  });

  if (!tableRows) {
    tableRows = `<tr><td colspan="7" style="text-align:center;color:var(--muted);padding:40px">ไม่มีหุ้นผ่านเกณฑ์ Breakout Trade Plan — ตลาดอาจยังไม่พร้อม</td></tr>`;
  }

  const summaryBar = `
    <div style="display:flex;gap:16px;margin-bottom:20px;flex-wrap:wrap;align-items:center">
      <div style="background:var(--bg3);border-radius:8px;padding:10px 18px;text-align:center">
        <div style="font-size:1.5rem;font-weight:800;color:var(--green)">${actionableCount}</div>
        <div style="font-size:.65rem;color:var(--muted)">ACTIONABLE</div>
      </div>
      <div style="background:var(--bg3);border-radius:8px;padding:10px 18px;text-align:center">
        <div style="font-size:1.5rem;font-weight:800;color:var(--gold)">${summary.watchlist_count||0}</div>
        <div style="font-size:.65rem;color:var(--muted)">WATCHLIST</div>
      </div>
      <div style="background:var(--bg3);border-radius:8px;padding:10px 18px;text-align:center">
        <div style="font-size:1.5rem;font-weight:800;color:var(--cyan)">${summary.revalidation_count||0}</div>
        <div style="font-size:.65rem;color:var(--muted)">REVALIDATE</div>
      </div>
      <div style="flex:1;text-align:right;font-size:.72rem;color:var(--muted)">
        Account: ${priceSign}${accountSize.toLocaleString()} &nbsp;|&nbsp;
        Risk: ${baseRiskPct.toFixed(1)}% &nbsp;|&nbsp;
        Target: ${targetR.toFixed(1)}R &nbsp;|&nbsp;
        Generated: ${(plan.generated_at||'').slice(0,16)}
      </div>
    </div>`;

  document.getElementById('breakoutContent').innerHTML = summaryBar + `
    <div style="overflow-x:auto">
      <table>
        <thead><tr>
          <th>Ticker</th><th>Status</th>
          <th style="color:var(--cyan)">🟢 Buy Price</th>
          <th style="color:var(--red)">🔴 Stop Loss</th>
          <th style="color:var(--green)">🎯 Target</th>
          <th>Shares / Risk (${priceSign})</th>
          <th>Sector</th>
        </tr></thead>
        <tbody>${tableRows}</tbody>
      </table>
    </div>`;
}

function renderDowntrend(dt) {
  if (!dt || !dt.summary) return;
  const s = dt.summary;
  const byCap = dt.by_market_cap || {};
  const bySector = dt.by_sector || {};

  const capOrder = ['Mega','Large','Mid','Small'];
  const capCards = capOrder.filter(t => byCap[t]).map(t => {
    const d = byCap[t];
    return `<div class="dt-stat"><div class="val">${d.median_days}d</div><div class="lbl">${t} Cap median</div></div>`;
  }).join('');

  const topSectors = Object.entries(bySector)
    .sort((a,b) => a[1].median_days - b[1].median_days)
    .slice(0, 6)
    .map(([sec, d]) => `<div class="dt-stat"><div class="val" style="font-size:1rem">${d.median_days}d</div><div class="lbl">${sec.replace(' ','<br>')}</div></div>`)
    .join('');

  document.getElementById('downtrendContent').innerHTML = `
    <div style="margin-bottom:16px">
      <div style="font-size:.85rem;color:var(--muted);margin-bottom:8px">S&P 500 Historical Correction Duration — ${s.total_downtrends} events analyzed</div>
      <div class="dt-grid">
        <div class="dt-stat"><div class="val">${s.median_duration_days}d</div><div class="lbl">Median (P50)</div></div>
        <div class="dt-stat"><div class="val">${s.p75_duration_days}d</div><div class="lbl">P75 conservative</div></div>
        <div class="dt-stat"><div class="val">${s.p90_duration_days}d</div><div class="lbl">P90 worst-case</div></div>
        <div class="dt-stat"><div class="val" style="font-size:1rem">${s.mean_duration_days}d</div><div class="lbl">Mean</div></div>
      </div>
    </div>
    ${capCards ? `<div style="font-size:.8rem;font-weight:700;color:var(--muted);margin-bottom:8px;text-transform:uppercase">By Market Cap</div><div class="dt-grid">${capCards}</div>` : ''}
    ${topSectors ? `<div style="font-size:.8rem;font-weight:700;color:var(--muted);margin:12px 0 8px;text-transform:uppercase">Fastest Recovery Sectors</div><div class="dt-grid">${topSectors}</div>` : ''}
    <div class="logic-box" style="margin-top:12px">
      <strong>วิธีใช้:</strong> ถ้าหุ้น VCP ที่คุณสนใจกำลัง correct อยู่ ให้ดูว่า sector ของมันมี median correction กี่วัน — ถ้าเกิน P75 แล้วยังไม่ฟื้น อาจมีปัญหากับหุ้นตัวนั้นโดยเฉพาะ
    </div>`;
}

function renderEarnings(data) {
  const results = data.results || [];
  const summary = data.summary || {};
  const meta = data.metadata || {};
  const summaryBar = `
    <div class="earn-summary">
      <div class="earn-grade-stat"><div class="val grade-A">${summary.grade_a||0}</div><div class="lbl">Grade A</div></div>
      <div class="earn-grade-stat"><div class="val grade-B">${summary.grade_b||0}</div><div class="lbl">Grade B</div></div>
      <div class="earn-grade-stat"><div class="val grade-C">${summary.grade_c||0}</div><div class="lbl">Grade C</div></div>
      <div class="earn-grade-stat"><div class="val grade-D">${summary.grade_d||0}</div><div class="lbl">Grade D</div></div>
      <div style="flex:1;text-align:right;align-self:center;font-size:.75rem;color:var(--muted)">
        Lookback: ${meta.lookback_days||'—'} วัน | ${(meta.generated_at||'').slice(0,16)}
      </div>
    </div>`;
  const rows = results.map(r => {
    const gradeCls = `grade-${r.grade||'D'}`;
    const gapColor = (r.gap_pct||0) >= 5 ? 'var(--green)' : (r.gap_pct||0) >= 0 ? 'var(--gold)' : 'var(--red)';
    return `<tr>
      <td><span class="sym">${r.symbol}</span><br><small style="color:var(--muted)">${r.company_name||''}</small></td>
      <td><span class="${gradeCls}">${r.grade}</span></td>
      <td><span class="score-pill" style="background:rgba(0,212,255,.15);color:var(--cyan)">${(r.composite_score||0).toFixed(1)}</span></td>
      <td style="color:${gapColor};font-family:'JetBrains Mono',monospace;font-weight:600">${r.gap_pct!=null?(r.gap_pct>=0?'+':'')+r.gap_pct.toFixed(1)+'%':'—'}</td>
      <td class="price">$${(r.current_price||0).toFixed(2)}</td>
      <td style="font-size:.75rem;color:var(--muted)">${r.earnings_date||'—'} <span style="color:var(--border)">${r.earnings_timing||''}</span></td>
      <td style="font-size:.75rem;color:var(--muted)">${r.sector||'—'}</td>
    </tr>`;
  }).join('');
  document.getElementById('earnContent').innerHTML = summaryBar + `
    <div style="overflow-x:auto"><table>
      <thead><tr><th>Ticker</th><th>Grade</th><th>Score</th><th>Gap</th><th>Price</th><th>Earnings Date</th><th>Sector</th></tr></thead>
      <tbody>${rows||'<tr><td colspan="7" style="text-align:center;color:var(--muted)">ไม่มีผลลัพธ์</td></tr>'}</tbody>
    </table></div>`;
}

function renderThaiSwing(data) {
  const el = document.getElementById('thaiSwingContent');
  if (!el) return;
  if (!data) {
    el.innerHTML = '<span style="color:var(--muted);font-size:.85rem">⚠️ ยังไม่มีข้อมูล Swing — รัน screen_thai_swing.py ก่อน</span>';
    return;
  }
  const currentLimit = document.getElementById('swingLimit')?.value || '10';
  const limit = parseInt(currentLimit);
  const dip = data.dip_buy || [];
  const mom = data.momentum || [];
  const ts = (data.generated || '').slice(0, 16).replace('_', ' ');

  let swingRowIdx = 0;
  function swingRows(list, strategyLabel) {
    const sliced = list.slice(0, limit);
    if (!sliced.length) return `<tr><td colspan="9" style="text-align:center;color:var(--muted);padding:20px">ไม่มี setup วันนี้</td></tr>`;
    return sliced.map(s => {
      const idx = swingRowIdx++;
      const p = s.plan || {};
      const rsiCol = s.rsi <= 45 ? 'var(--cyan)' : s.rsi >= 60 ? 'var(--green)' : 'var(--gold)';
      const avgVol = s.avg_volume || 1;
      const volRatio = ((s.volume || 0) / avgVol).toFixed(1);
      const volCol = volRatio >= 2 ? 'var(--green)' : volRatio >= 1.4 ? 'var(--gold)' : 'var(--muted)';
      const risk = p.risk_pct || 0;
      const riskCol = risk <= 3 ? 'var(--green)' : risk <= 7 ? 'var(--gold)' : 'var(--red)';
      const badges = (s.set_membership || []).map(t => {
        const color = t==='SET50' ? 'var(--gold)' : t==='SET100' ? 'var(--cyan)' : 'var(--green)';
        return `<span style="background:${color}22;color:${color};padding:1px 4px;border-radius:3px;font-size:.62rem;margin-right:2px">${t}</span>`;
      }).join('');
      const srcTag = strategyLabel === 'DIP' ? 'thai-swing-dip' : 'thai-swing-momentum';
    return `<tr class="vcp-row" style="cursor:pointer" onclick="toggleSwingRow(${idx}, '${s.symbol}')">
        <td>
          <span class="star-btn" onclick="toggleStar(event, '${s.symbol}')" title="${isStarred(s.symbol) ? 'เลิกติดตาม' : 'ติดตาม'}">
            ${isStarred(s.symbol) ? '★' : '☆'}
          </span>
          <span class="paper-btn" style="background:var(--cyan)22;color:var(--cyan);border-color:var(--cyan)" onclick="event.stopPropagation();paperAddPick('${s.symbol}','TH',${p.entry||0},${p.stop||0},${p.target||0},'${srcTag}',${s.score||0},100)" title="Add to Paper Portfolio">📝</span>
          <span class="sym">${s.symbol}</span> ${badges}<br>
          <small style="color:var(--muted)">${(s.name||'').slice(0,16)}</small>
        </td>
        <td><span class="score-pill" style="background:var(--cyan)22;color:var(--cyan)">${(s.score||0).toFixed(0)}</span></td>
        <td style="color:${rsiCol};font-family:'JetBrains Mono',monospace">${(s.rsi||0).toFixed(1)}<br><small style="font-size:.6rem;opacity:.7">${(s.rsi_weekly||0).toFixed(1)}W</small></td>
        <td style="color:${volCol};font-family:'JetBrains Mono',monospace">${volRatio}x</td>
        <td class="price">฿${(p.entry||0).toFixed(2)}</td>
        <td style="color:var(--red);font-family:'JetBrains Mono',monospace">฿${(p.stop||0).toFixed(2)}</td>
        <td style="color:var(--green);font-family:'JetBrains Mono',monospace">฿${(p.target||0).toFixed(2)}</td>
        <td style="color:${riskCol}">${risk.toFixed(1)}%</td>
        <td style="color:var(--gold)">2:1</td>
      </tr>
      <tr class="expand-row" id="swing-row-${idx}">
        <td colspan="9" class="expand-cell">
          <div id="swing-chart-${s.symbol}" class="chart-loading"></div>
        </td>
      </tr>`;
    }).join('');
  }

  el.innerHTML = `
    <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:16px;align-items:center">
      <div style="background:var(--bg3);border-radius:8px;padding:10px 16px;text-align:center">
        <div style="font-size:1.4rem;font-weight:800;color:var(--cyan)">${dip.length}</div>
        <div style="font-size:.65rem;color:var(--muted)">DIP BUY</div>
      </div>
      <div style="background:var(--bg3);border-radius:8px;padding:10px 16px;text-align:center">
        <div style="font-size:1.4rem;font-weight:800;color:var(--green)">${mom.length}</div>
        <div style="font-size:.65rem;color:var(--muted)">MOMENTUM</div>
      </div>
      <div style="font-size:.72rem;color:var(--muted);margin-left:auto">อัปเดต: ${ts}</div>
    </div>

    <div style="display:flex;justify-content:flex-end;margin-bottom:12px">
      <select id="swingLimit" onchange="renderThaiSwing(RAW_DATA.thai_swing)" style="background:var(--bg3);border:1px solid var(--border);color:var(--text);padding:8px 12px;border-radius:8px;font-size:0.85rem">
        <option value="10" ${currentLimit === '10' ? 'selected' : ''}>แสดง 10 ตัวแรก</option>
        <option value="999" ${currentLimit === '999' ? 'selected' : ''}>แสดงทั้งหมด</option>
      </select>
    </div>

    <div style="font-weight:700;color:var(--cyan);margin-bottom:8px">📉 A: Dip Buy — RSI pullback ใน uptrend (ถือ 2–4 วัน)</div>
    <div style="overflow-x:auto;margin-bottom:20px"><table>
      <thead><tr>
        <th>Ticker</th><th>Score</th><th>RSI</th><th>Volume</th>
        <th>Entry</th><th>Stop</th><th>Target</th><th>Risk</th><th>R/R</th>
      </tr></thead>
      <tbody>${swingRows(dip, 'DIP')}</tbody>
    </table></div>

    <div style="font-weight:700;color:var(--green);margin-bottom:8px">📈 B: Momentum — Volume surge + RSI momentum (ถือ 3–5 วัน)</div>
    <div style="overflow-x:auto;margin-bottom:12px"><table>
      <thead><tr>
        <th>Ticker</th><th>Score</th><th>RSI</th><th>Volume</th>
        <th>Entry</th><th>Stop</th><th>Target</th><th>Risk</th><th>R/R</th>
      </tr></thead>
      <tbody>${swingRows(mom, 'MOM')}</tbody>
    </table></div>

    <div class="logic-box">
      <strong>วิธีอ่าน:</strong> คลิกแถวเพื่อดูกราฟ | Dip Buy = RSI 35–52 เหนือ SMA50 รอ bounce | Momentum = RSI 55–72 + Volume > 1.4× avg | Risk ≤ 3% = ดี (เขียว) | R/R ทุกตัว = 2:1
    </div>`;
}

function toggleSwingRow(idx, symbol) {
  const r = document.getElementById('swing-row-' + idx);
  const isOpen = r.classList.toggle('open');
  if (isOpen) {
    const allItems = [
      ...(RAW_DATA?.thai_swing?.dip_buy || []),
      ...(RAW_DATA?.thai_swing?.momentum || []),
    ];
    const item = allItems.find(x => x.symbol === symbol);
    if (item) initSwingChart(item.symbol, item.plan || {});
  }
}

async function initSwingChart(symbol, plan) {
  const container = document.getElementById(`swing-chart-${symbol}`);
  if (!container || container.dataset.loaded === '1') return;
  container.dataset.loaded = '1';
  container.innerHTML = '⏳ กำลังโหลดกราฟ...';
  try {
    const res = await fetch(`/api/history/${symbol}`);
    const data = await res.json();
    if (data.error) throw new Error(data.error);

    if (container._resizeObserver) {
      container._resizeObserver.disconnect();
      delete container._resizeObserver;
    }
    container.innerHTML = '';
    container.classList.remove('chart-loading');
    container.classList.add('chart-container');

    const chart = LightweightCharts.createChart(container, {
      width: container.clientWidth,
      height: container.clientHeight || 560,
      layout: { background: { color: getChartTheme().bg }, textColor: getChartTheme().text },
      grid: { vertLines: { color: getChartTheme().border }, horzLines: { color: getChartTheme().border } },
      timeScale: { borderColor: getChartTheme().border },
      rightPriceScale: { borderColor: getChartTheme().border, scaleMargins: { top: 0.08, bottom: 0.28 } },
    });

    const resizeObserver = new ResizeObserver(entries => {
      for (let entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0) {
          chart.resize(width, height);
        }
      }
    });
    resizeObserver.observe(container);
    container._resizeObserver = resizeObserver;

    // Candlestick
    const candleSeries = chart.addCandlestickSeries({
      upColor:'#00e676', borderUpColor:'#00e676', wickUpColor:'#00e676',
      downColor:'#f44336', borderDownColor:'#f44336', wickDownColor:'#f44336',
    });
    candleSeries.setData(data);

    // Volume
    const volSeries = chart.addHistogramSeries({
      color: '#26a69a', priceFormat: { type: 'volume' }, priceScaleId: 'volume',
    });
    chart.priceScale('volume').applyOptions({ scaleMargins: { top: 0.78, bottom: 0 } });
    volSeries.setData(data.map(d => ({
      time: d.time, value: d.value,
      color: d.close >= d.open ? '#00e67650' : '#f4433650',
    })));

    // SMA lines
    const closes = data.map(d => d.close);
    const calcSMA = (arr, n) => arr.map((_, i) =>
      i < n - 1 ? null : arr.slice(i - n + 1, i + 1).reduce((s, v) => s + v, 0) / n
    );
    const addLine = (vals, color, title) => {
      const s = chart.addLineSeries({ color, lineWidth: 1, title,
        lastValueVisible: false, priceLineVisible: false, crosshairMarkerVisible: false });
      s.setData(data.map((d, i) => vals[i] != null ? { time: d.time, value: vals[i] } : null).filter(Boolean));
    };
    addLine(calcSMA(closes, 20),  '#26a69a', 'SMA20');  // teal
    addLine(calcSMA(closes, 50),  '#ff9800', 'SMA50');  // orange (aligned with VCP chart)
    addLine(calcSMA(closes, 150), '#a855f7', 'SMA150'); // purple
    addLine(calcSMA(closes, 200), '#00d4ff', 'SMA200'); // cyan

    // Entry / Stop / Target horizontal lines (last 60 bars)
    if (plan && data.length > 0) {
      const startIdx = Math.max(0, data.length - 60);
      const startTime = data[startIdx].time;
      const endTime = data[data.length - 1].time;
      const addLevel = (price, color, title, style) => {
        const s = chart.addLineSeries({ color, lineWidth: 2, lineStyle: style,
          title, lastValueVisible: true, priceLineVisible: false });
        s.setData([{ time: startTime, value: price }, { time: endTime, value: price }]);
      };
      if (plan.entry)  addLevel(plan.entry,  '#00e676', 'Entry',  0); // solid green
      if (plan.stop)   addLevel(plan.stop,   '#f44336', 'Stop',   1); // dashed red
      if (plan.target) addLevel(plan.target, '#ffd700', 'Target', 1); // dashed gold
    }

    setupChartLegend(chart, container, symbol, data, candleSeries);
    chart.timeScale().fitContent();
  } catch(e) {
    container.innerHTML = '❌ โหลดกราฟไม่สำเร็จ — ' + e.message;
  }
}

function renderCANSLIM(data) {
  if (!data) return;
  _canslimResults = data.results || [];
  const meta = data.metadata || {};
  const mkt = meta.market_condition || {};

  const mktColor = mkt.M_score >= 70 ? 'var(--green)' : mkt.M_score >= 40 ? 'var(--gold)' : 'var(--red)';
  const header = `
    <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:16px;align-items:center">
      <div style="background:var(--bg3);border-radius:8px;padding:10px 16px;text-align:center">
        <div style="font-size:1.4rem;font-weight:800;color:var(--cyan)">${_canslimResults.length}</div>
        <div style="font-size:.65rem;color:var(--muted)">STOCKS SCORED</div>
      </div>
      <div style="background:var(--bg3);border-radius:8px;padding:10px 16px;text-align:center">
        <div style="font-size:1.4rem;font-weight:800;color:${mktColor}">${mkt.M_score??'—'}</div>
        <div style="font-size:.65rem;color:var(--muted)">M SCORE (Market)</div>
      </div>
      <div style="background:var(--bg3);border-radius:8px;padding:10px 16px;text-align:center">
        <div style="font-size:1rem;font-weight:700;color:${mktColor}">${mkt.trend||'—'}</div>
        <div style="font-size:.65rem;color:var(--muted)">MARKET TREND</div>
      </div>
      <div style="font-size:.72rem;color:var(--muted);margin-left:auto">
        ${meta.phase||''} | ${(meta.generated_at||'').slice(0,16)}
        ${mkt.warning ? '<br><span style="color:var(--red)">⚠️ '+mkt.warning+'</span>' : ''}
      </div>
    </div>`;

  const currentLimit = document.getElementById('canslimLimit')?.value || '10';
  const controls = `
    <div style="display:flex;gap:10px;margin-bottom:16px;flex-wrap:wrap">
      <input type="text" id="canslimSearch" placeholder="🔍 ค้นหา Ticker / ชื่อหุ้น..." oninput="updateCANSLIM()"
        style="flex:1;background:var(--bg3);border:1px solid var(--border);color:var(--text);padding:10px 15px;border-radius:10px;min-width:160px">
      <select id="canslimRecFilter" onchange="updateCANSLIM()"
        style="background:var(--bg3);border:1px solid var(--border);color:var(--text);padding:10px;border-radius:10px">
        <option value="">ทุก Recommendation</option>
        <option value="buy">✅ Buy</option>
        <option value="watchlist">👀 Watchlist</option>
        <option value="avoid">❌ Avoid</option>
      </select>
      <select id="canslimLimit" onchange="updateCANSLIM()"
        style="background:var(--bg3);border:1px solid var(--border);color:var(--text);padding:10px;border-radius:10px">
        <option value="10" ${currentLimit === '10' ? 'selected' : ''}>10 ตัวแรก</option>
        <option value="999" ${currentLimit === '999' ? 'selected' : ''}>ทั้งหมด</option>
      </select>
    </div>`;

  const benchmarkName = currentMarket === 'TH' ? 'SET Index' : 'S&P500';
  document.getElementById('canslimContent').innerHTML = header + controls + `
    <div style="overflow-x:auto"><table>
      <thead><tr>
        <th>Ticker</th>
        <th class="sortable" onclick="setCANSLIMSort('composite_score')">Score</th>
        <th>Guidance</th>
        <th title="C=Earnings A=Annual N=NewHigh S=Supply L=Leadership I=Institutional M=Market">CANSLIM</th>
        <th class="sortable" onclick="setCANSLIMSort('rs_percentile')" title="RS Percentile vs ${benchmarkName} — เป้าหมาย ≥80">RS% 📈</th>
        <th class="sortable" onclick="setCANSLIMSort('price')">Price</th>
        <th>Sector</th>
      </tr></thead>
      <tbody id="canslimTbody"></tbody>
    </table></div>
    <div class="logic-box" style="margin-top:12px">
      <strong>วิธีอ่าน:</strong> Score ≥70 = Strong CANSLIM | แต่ละตัวอักษรสีเขียว = ผ่าน ≥70 | RS% = เปอร์เซ็นไทล์เทียบ ${benchmarkName} (เป้าหมาย ≥80) | คลิกแถวเพื่อดูกราฟ
    </div>`;

  updateCANSLIM();
}

function setCANSLIMSort(col) {
  if (CANSLIM_SORT.col === col) CANSLIM_SORT.dir *= -1;
  else { CANSLIM_SORT.col = col; CANSLIM_SORT.dir = -1; }
  updateCANSLIM();
  // Update sort arrow on CANSLIM table headers (scoped to canslimContent)
  document.querySelectorAll('#canslimContent th.sortable').forEach(th => {
    th.classList.remove('sort-asc','sort-desc');
    if (th.getAttribute('onclick').includes(`'${col}'`))
      th.classList.add(CANSLIM_SORT.dir === 1 ? 'sort-asc' : 'sort-desc');
  });
}

function updateCANSLIM() {
  const tbody = document.getElementById('canslimTbody');
  if (!tbody) return;
  const priceSign = currentMarket === 'TH' ? '฿' : '$';
  const search = (document.getElementById('canslimSearch')?.value || '').toLowerCase();
  const recFilter = document.getElementById('canslimRecFilter')?.value || '';
  const limit = parseInt(document.getElementById('canslimLimit')?.value || '10');

  let results = [..._canslimResults].filter(r => {
    const mSearch = !search
      || r.symbol.toLowerCase().includes(search)
      || (r.company_name||'').toLowerCase().includes(search);
    const mRec = !recFilter || (r.threshold_check?.recommendation||'') === recFilter;
    return mSearch && mRec;
  });

  results.sort((a, b) => {
    let valA, valB;
    const col = CANSLIM_SORT.col;
    if (col === 'composite_score') { valA = a.composite_score; valB = b.composite_score; }
    else if (col === 'price') { valA = a.price; valB = b.price; }
    else if (col === 'rs_percentile') {
      valA = a.l_component?.rs_rank_percentile ?? a.l_component?.rs_rank_estimate ?? -1;
      valB = b.l_component?.rs_rank_percentile ?? b.l_component?.rs_rank_estimate ?? -1;
    }
    else { valA = a[col]||0; valB = b[col]||0; }
    return (valA < valB ? -1 : valA > valB ? 1 : 0) * CANSLIM_SORT.dir;
  });

  const slicedResults = results.slice(0, limit);
  const CANSLIM_LABELS = {c:'C Earnings',a:'A Annual',n:'N New High',s:'S Supply',l:'L Leadership',i:'I Institut.',m:'M Market'};
  tbody.innerHTML = slicedResults.map((r, i) => {
    const sc = r.composite_score >= 70 ? 'var(--green)' : r.composite_score >= 50 ? 'var(--gold)' : 'var(--red)';
    const rec = r.threshold_check?.recommendation || '';
    const recColor = rec === 'buy' ? 'var(--green)' : rec === 'watchlist' ? 'var(--gold)' : rec === 'avoid' ? 'var(--red)' : 'var(--muted)';
    const recLabel = rec === 'buy' ? '✅ Buy' : rec === 'watchlist' ? '👀 Watch' : rec === 'avoid' ? '❌ Avoid' : '—';
    const rsP = r.l_component?.rs_rank_percentile ?? r.l_component?.rs_rank_estimate;
    const rsCol = rsP >= 80 ? 'var(--green)' : rsP >= 60 ? 'var(--gold)' : rsP >= 40 ? 'var(--orange)' : 'var(--red)';
    const comps = ['c','a','n','s','l','i','m'];
    const compBar = comps.map(k => {
      const sc2 = r[k+'_component']?.score ?? 0;
      const c2 = sc2 >= 70 ? '#00e676' : sc2 >= 40 ? '#ffd700' : '#f44336';
      return `<span title="${CANSLIM_LABELS[k]}: ${sc2}" style="display:inline-block;width:18px;height:18px;line-height:18px;text-align:center;font-size:.6rem;font-weight:700;background:${c2}22;color:${c2};border-radius:3px;margin:1px">${k.toUpperCase()}</span>`;
    }).join('');
    const guidance = r.guidance || '';
    // CANSLIM: no built-in stop/target — use defaults: stop -8%, target +25% (O'Neil's rule)
    const ptMkt = currentMarket || 'US';
    const ptPrice = r.price || 0;
    const ptStop = ptPrice * 0.92;
    const ptTarget = ptPrice * 1.25;
    const ptBtn = ptPrice > 0
      ? `<span class="paper-btn" style="background:var(--gold)22;color:var(--gold);border-color:var(--gold)" onclick="event.stopPropagation();paperAddPick('${r.symbol}','${ptMkt}',${ptPrice.toFixed(2)},${ptStop.toFixed(2)},${ptTarget.toFixed(2)},'canslim',${r.composite_score||0},100)" title="Add to Paper (O'Neil rule: stop -8%, target +25%)">📝</span>`
      : '';
    return `<tr class="vcp-row" onclick="toggleCANSLIMRow(${i})" style="cursor:pointer" data-symbol="${r.symbol}">
      <td>
        <span class="star-btn" onclick="toggleStar(event, '${r.symbol}')" title="${isStarred(r.symbol) ? 'เลิกติดตาม' : 'ติดตาม'}">
          ${isStarred(r.symbol) ? '★' : '☆'}
        </span>
        ${ptBtn}
        <span class="sym">${r.symbol}</span><br>
        <small style="color:var(--muted)">${(r.company_name||'').slice(0,20)}</small>
      </td>
      <td><span class="score-pill" style="background:${sc}22;color:${sc};font-size:.9rem">${(r.composite_score||0).toFixed(1)}</span></td>
      <td style="font-size:.78rem">
        <span style="color:${recColor};font-weight:700">${recLabel}</span>
        <br><small style="color:var(--muted);font-size:.63rem" title="${guidance}">${guidance.slice(0,32)}${guidance.length>32?'…':''}</small>
      </td>
      <td>${compBar}</td>
      <td style="font-family:'JetBrains Mono',monospace;color:${rsCol};font-weight:700;text-align:center">
        ${rsP != null ? rsP.toFixed(0) : '—'}<br>
        <small style="font-size:.62rem;opacity:.7">${r.l_component?.rs_rating||''}</small>
      </td>
      <td class="price">${priceSign}${(r.price||0).toFixed(2)}</td>
      <td style="font-size:.7rem;color:var(--muted)">${r.sector||'—'}</td>
    </tr>
    <tr class="expand-row" id="canslim-row-${i}">
      <td colspan="7" class="expand-cell">
        <div id="canslim-chart-${r.symbol}" class="chart-loading"></div>
        <div class="logic-box" style="margin-top:8px;font-size:.78rem">
          <strong>Weakest:</strong> ${r.weakest_component||'—'} (${r.weakest_score??'—'}/100)
          &nbsp;|&nbsp;
          <strong>Threshold:</strong> <span style="color:${recColor}">${r.threshold_check?.reason||'—'}</span>
        </div>
      </td>
    </tr>`;
  }).join('') || `<tr><td colspan="7" style="text-align:center;color:var(--muted);padding:40px">ไม่มีผลที่ตรงเงื่อนไข</td></tr>`;
}

function toggleCANSLIMRow(i) {
  const r = document.getElementById('canslim-row-' + i);
  const isOpen = r.classList.toggle('open');
  if (isOpen) {
    const sym = r.previousElementSibling.getAttribute('data-symbol');
    initCANSLIMChart(sym);
  }
}

async function initCANSLIMChart(symbol) {
  const container = document.getElementById(`canslim-chart-${symbol}`);
  if (!container || container.dataset.loaded === '1') return;
  container.dataset.loaded = '1';
  try {
    const res = await fetch(`/api/history/${symbol}`);
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    if (container._resizeObserver) {
      container._resizeObserver.disconnect();
      delete container._resizeObserver;
    }
    container.innerHTML = '';
    container.classList.remove('chart-loading');
    container.classList.add('chart-container');

    const chart = LightweightCharts.createChart(container, {
      width: container.clientWidth,
      height: container.clientHeight || 560,
      layout: { background: { color: getChartTheme().bg }, textColor: getChartTheme().text },
      grid: { vertLines: { color: getChartTheme().border }, horzLines: { color: getChartTheme().border } },
      timeScale: { borderColor: getChartTheme().border },
      rightPriceScale: { borderColor: getChartTheme().border, scaleMargins: { top: 0.08, bottom: 0.28 } },
    });

    const resizeObserver = new ResizeObserver(entries => {
      for (let entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0) {
          chart.resize(width, height);
        }
      }
    });
    resizeObserver.observe(container);
    container._resizeObserver = resizeObserver;

    const candleSeries = chart.addCandlestickSeries({
      upColor:'#00e676', borderUpColor:'#00e676', wickUpColor:'#00e676',
      downColor:'#f44336', borderDownColor:'#f44336', wickDownColor:'#f44336',
    });
    candleSeries.setData(data);

    const volSeries = chart.addHistogramSeries({
      color: '#26a69a', priceFormat: { type: 'volume' }, priceScaleId: 'volume',
    });
    chart.priceScale('volume').applyOptions({ scaleMargins: { top: 0.78, bottom: 0 } });
    volSeries.setData(data.map(d => ({
      time: d.time, value: d.value,
      color: d.close >= d.open ? '#00e67650' : '#f4433650',
    })));

    const closes = data.map(d => d.close);
    const calcSMA = (arr, n) => arr.map((_, i) =>
      i < n - 1 ? null : arr.slice(i - n + 1, i + 1).reduce((s, v) => s + v, 0) / n
    );
    const addSMALine = (vals, color, title) => {
      const s = chart.addLineSeries({ color, lineWidth: 1, title,
        lastValueVisible: false, priceLineVisible: false, crosshairMarkerVisible: false });
      s.setData(data.map((d, i) => vals[i] != null ? { time: d.time, value: vals[i] } : null).filter(Boolean));
    };
    addSMALine(calcSMA(closes, 50),  '#ff9800', 'SMA50');
    addSMALine(calcSMA(closes, 150), '#a855f7', 'SMA150');
    addSMALine(calcSMA(closes, 200), '#00d4ff', 'SMA200');

    setupChartLegend(chart, container, symbol, data, candleSeries);
    chart.timeScale().fitContent();
  } catch(e) {
    container.innerHTML = '❌ โหลดกราฟไม่สำเร็จ — ' + e.message;
  }
}

function setSort(col) {
  if (VCP_SORT.col === col) VCP_SORT.dir *= -1;
  else { VCP_SORT.col = col; VCP_SORT.dir = -1; }
  // Scope to VCP table only to avoid marking CANSLIM headers
  document.querySelectorAll('#vcpTable th.sortable').forEach(th => {
    th.classList.remove('sort-asc','sort-desc');
    if (th.getAttribute('onclick').includes(`'${col}'`))
      th.classList.add(VCP_SORT.dir === 1 ? 'sort-asc' : 'sort-desc');
  });
  updateVCP();
}

function updateVCP() {
  const results = [...(RAW_DATA?.vcp?.results || [])];
  const search = document.getElementById('vcpSearch').value.toLowerCase();
  const stateFilter = document.getElementById('vcpStateFilter').value;
  const minScore = parseFloat(document.getElementById('vcpMinScore').value) || 0;
  const limit = parseInt(document.getElementById('vcpLimit').value);
  let filtered = results.filter(s => {
    const mSearch = s.symbol.toLowerCase().includes(search)
      || (s.company_name||'').toLowerCase().includes(search)
      || (s.sector||'').toLowerCase().includes(search);
    const mState = !stateFilter || s.execution_state === stateFilter;
    const mScore = s.composite_score >= minScore;
    return mSearch && mState && mScore;
  });
  filtered.sort((a,b) => {
    let valA, valB;
    const col = VCP_SORT.col;
    if (col === 'symbol') { valA = a.symbol; valB = b.symbol; }
    else if (col === 'price') { valA = a.price; valB = b.price; }
    else if (col === 'pivot_price') { valA = a.vcp_pattern?.pivot_price||0; valB = b.vcp_pattern?.pivot_price||0; }
    else if (col === 'composite_score') { valA = a.composite_score; valB = b.composite_score; }
    else if (col === 'execution_state') { valA = a.execution_state; valB = b.execution_state; }
    else if (col === 'trend_score') { valA = a.trend_template?.score||0; valB = b.trend_template?.score||0; }
    else if (col === 'rs_rank_estimate') { valA = a.relative_strength?.rs_percentile||a.relative_strength?.rs_rank_estimate||0; valB = b.relative_strength?.rs_percentile||b.relative_strength?.rs_rank_estimate||0; }
    else if (col === 'atr_value') { valA = a.vcp_pattern?.atr_value||0; valB = b.vcp_pattern?.atr_value||0; }
    else if (col === 'distance_pct') {
      valA = Math.abs(a.pivot_proximity?.distance_from_pivot_pct ?? 999);
      valB = Math.abs(b.pivot_proximity?.distance_from_pivot_pct ?? 999);
    }
    else { valA = a[col]||0; valB = b[col]||0; }
    if (valA < valB) return -1 * VCP_SORT.dir;
    if (valA > valB) return 1 * VCP_SORT.dir;
    return 0;
  });
  renderVCPTable(filtered.slice(0, limit));
}

function renderVCPTable(results) {
  const tbody = document.getElementById('vcpTbody');
  if (!results || results.length === 0) {
    tbody.innerHTML = '<tr><td colspan="13" style="text-align:center;color:var(--muted);padding:40px">ไม่มีหุ้นผ่านเกณฑ์ VCP</td></tr>';
    document.getElementById('funnel').innerHTML = '';
    return;
  }
  const priceSign = currentMarket === 'TH' ? '฿' : '$';
  const benchmarkName = currentMarket === 'TH' ? 'SET Index' : 'S&P500';

  // Update table header tooltip dynamically
  const rsHeader = document.querySelector('#vcpTable th[onclick="setSort(\'rs_rank_estimate\')"]');
  if (rsHeader) {
    rsHeader.title = `RS Percentile vs ${benchmarkName} (O'Neil method) — ≥80 = Market Leader`;
  }
  const f = RAW_DATA?.vcp?.metadata?.funnel || {};
  document.getElementById('funnel').innerHTML = `
    <div class="funnel-step"><div class="funnel-step-num">${f.universe||'—'}</div><div class="funnel-step-label">Universe</div></div>
    <div class="arrow">→</div>
    <div class="funnel-step"><div class="funnel-step-num" style="color:var(--orange)">${f.pre_filter_passed||'—'}</div><div class="funnel-step-label">Pre-Filter</div></div>
    <div class="arrow">→</div>
    <div class="funnel-step"><div class="funnel-step-num" style="color:var(--gold)">${f.trend_template_passed||'—'}</div><div class="funnel-step-label">Trend Template</div></div>
    <div class="arrow">→</div>
    <div class="funnel-step"><div class="funnel-step-num" style="color:var(--green)">${f.vcp_candidates||'—'}</div><div class="funnel-step-label">VCP Candidates</div></div>`;
  tbody.innerHTML = results.map((s, i) => {
    const sc = s.composite_score >= 70 ? '#00e676' : s.composite_score >= 50 ? '#ffd700' : '#f44336';
    const stCls = s.execution_state === 'Pre-breakout' || s.execution_state === 'Breakout' ? 'bg-green'
                : s.execution_state === 'Damaged' ? 'bg-red' : 'bg-orange';
    const trendVal = s.trend_template?.score || 0;
    const trndCls = trendVal >= 95 ? 'trend-perfect' : trendVal >= 80 ? 'trend-good' : 'trend-weak';
    // RS Rating
    const rsP = s.relative_strength?.rs_percentile ?? s.relative_strength?.rs_rank_estimate;
    const rsRating = s.relative_strength?.rs_rating ||
      (rsP >= 90 ? 'Market Leader' : rsP >= 80 ? 'Strong' : rsP >= 60 ? 'Above Avg' : rsP >= 40 ? 'Average' : rsP != null ? 'Laggard' : '');
    const rsCol = rsP >= 80 ? 'var(--green)' : rsP >= 60 ? 'var(--gold)' : rsP >= 40 ? 'var(--orange)' : 'var(--red)';
    const rsDisplay = rsP != null ? rsP.toFixed(0) : '—';
    // ATR
    const atr = s.vcp_pattern?.atr_value;
    const atrPct = (atr && s.price) ? (atr / s.price * 100) : null;
    const atrCol = atrPct > 5 ? 'var(--red)' : atrPct > 3 ? 'var(--orange)' : 'var(--green)';
    const atrDisplay = atr ? atr.toFixed(2) : '—';
    const atrPctDisplay = atrPct ? atrPct.toFixed(1) + '%' : '';
    // Distance from pivot
    const dist = s.pivot_proximity?.distance_from_pivot_pct;
    const distCol = dist == null ? 'var(--muted)'
      : Math.abs(dist) <= 1 ? 'var(--green)'
      : Math.abs(dist) <= 3 ? 'var(--gold)'
      : 'var(--orange)';
    const distDisplay = dist != null ? (dist >= 0 ? '+' : '') + dist.toFixed(1) + '%' : '—';
    // Contractions count
    const conCount = s.vcp_pattern?.contractions?.length || 0;
    const conCol = conCount >= 2 && conCount <= 4 ? 'var(--green)' : 'var(--gold)';
    const settings = getSettings();
    const targetR = parseFloat(settings.target_r) || 2.0;
    const pivot = s.vcp_pattern?.pivot_price;
    const sl = s.pivot_proximity?.stop_loss_price;
    const targetPrice = (pivot && sl) ? pivot + (targetR * (pivot - sl)) : null;

    const ptMkt = currentMarket || 'US';
    // Prefer VCP plan values (pivot/SL/target); fall back to O'Neil rule (-8%/+25% of current price)
    const ptHasPlan = pivot && sl && targetPrice;
    const ptEntry = ptHasPlan ? pivot : (s.price || 0);
    const ptStop = ptHasPlan ? sl : ptEntry * 0.92;
    const ptTarget = ptHasPlan ? targetPrice : ptEntry * 1.25;
    const ptColor = ptHasPlan ? 'var(--cyan)' : 'var(--muted)';
    const ptTitle = ptHasPlan
      ? `Add to Paper (entry=pivot ${ptEntry.toFixed(2)}, stop=SL ${ptStop.toFixed(2)}, target=${targetR}R)`
      : `Add to Paper (fallback: no pivot yet — entry=current ${ptEntry.toFixed(2)}, stop -8%, target +25%)`;
    const ptBtn = ptEntry > 0
      ? `<span class="paper-btn" style="background:${ptColor}22;color:${ptColor};border-color:${ptColor}" onclick="event.stopPropagation();paperAddPick('${s.symbol}','${ptMkt}',${ptEntry.toFixed(2)},${ptStop.toFixed(2)},${ptTarget.toFixed(2)},'vcp-screener',${s.composite_score},100)" title="${ptTitle}">📝</span>`
      : '';
    return `
      <tr onclick="toggleRow(${i})" style="cursor:pointer" data-symbol="${s.symbol}">
        <td>
          <span class="star-btn" onclick="toggleStar(event, '${s.symbol}')" title="${isStarred(s.symbol) ? 'เลิกติดตาม' : 'ติดตาม'}">
            ${isStarred(s.symbol) ? '★' : '☆'}
          </span>
          ${ptBtn}
          <span class="sym">${s.symbol}</span><br>
          <small style="color:var(--muted)">${s.company_name||''}</small>
        </td>
        <td><span class="score-pill" style="background:${sc}22;color:${sc}">${s.composite_score.toFixed(1)}</span></td>
        <td class="price">${priceSign}${s.price?.toFixed(2)}</td>
        <td class="price" style="color:var(--gold)">${priceSign}${pivot?.toFixed(2)||'—'}</td>
        <td class="price" style="color:var(--red)">${sl ? priceSign + sl.toFixed(2) : '—'}</td>
        <td class="price" style="color:#ff80ab">${targetPrice ? priceSign + targetPrice.toFixed(2) : '—'}</td>
        <td><span class="state-pill ${stCls}">${s.execution_state}</span></td>
        <td><span class="trend-badge ${trndCls}">${trendVal.toFixed(0)}</span></td>
        <td style="font-family:'JetBrains Mono',monospace;color:${rsCol};font-weight:700" title="${rsRating}">
          ${rsDisplay}<br><small style="font-size:.65rem;opacity:.7">${rsRating}</small>
        </td>
        <td style="font-family:'JetBrains Mono',monospace;color:${atrCol}" title="ATR=${atrDisplay} (${atrPctDisplay} of price)">
          ${atrDisplay}<br><small style="font-size:.65rem;opacity:.7">${atrPctDisplay}</small>
        </td>
        <td style="font-family:'JetBrains Mono',monospace;color:${distCol};font-weight:700;text-align:center" title="ห่างจาก Pivot ${distDisplay}">
          ${distDisplay}
        </td>
        <td style="font-family:'JetBrains Mono',monospace;color:${conCol};font-weight:700;text-align:center" title="${conCount} contractions (Ideal: 2-4)">
          ${conCount||'—'}
        </td>
        <td style="font-size:.7rem;color:var(--muted)">${s.quality_rating}</td>
      </tr>
      <tr class="expand-row" id="row-${i}">
        <td colspan="13" class="expand-cell">
          <div id="chart-${s.symbol}" class="chart-loading"></div>
          ${(() => {
            const tt = s.trend_template || {};
            const cr = tt.criteria || {};
            const passedCount = Object.values(cr).filter(c => c && c.passed).length;
            const price = s.price || 0;
            const sma50  = tt.sma50;
            const sma150 = tt.sma150;
            const sma200 = tt.sma200;
            const fmtSMA = (val, label, isAbove) => {
              if (val == null) return '';
              const diff = price > 0 ? ((price - val) / val * 100).toFixed(1) : '—';
              const ok = isAbove;
              const col = ok ? 'var(--green)' : 'var(--red)';
              const icon = ok ? '✅' : '❌';
              return `<div class="sma-chip" style="border-color:${col}">
                <span style="color:var(--muted);font-size:.65rem">${label}</span>
                <span style="color:${col};font-weight:700">${priceSign}${val.toFixed(2)}</span>
                <span style="font-size:.65rem;color:${col}">${icon} ${diff > 0 ? '+' : ''}${diff}%</span>
              </div>`;
            };
            const rsRankVal = s.relative_strength?.rs_rank_estimate;
            const rsRankPassed = cr.c7_rs_rank_above_70?.passed ?? (rsRankVal != null && rsRankVal >= 70);
            const rsRankCol = rsRankPassed ? 'var(--green)' : 'var(--red)';
            return `<div class="logic-box">
              <div style="display:flex;flex-wrap:wrap;gap:.5rem;align-items:center;margin-bottom:.4rem">
                <span><strong>Strongest:</strong> ${s.strongest_component||'—'} (${s.strongest_score||0})</span>
                <span style="color:var(--muted)">|</span>
                <span><strong>Trend Criteria:</strong> ${passedCount}/7 Passed</span>
                ${rsRankVal != null ? `<span style="color:var(--muted)">|</span>
                <span style="color:${rsRankCol}"><strong>RS Rank:</strong> ${rsRankVal.toFixed(0)} ${rsRankPassed ? '✅' : '❌ (<70)'}</span>` : ''}
              </div>
              <div style="display:flex;flex-wrap:wrap;gap:.4rem">
                ${fmtSMA(sma200, 'SMA 200', price > (sma200||0))}
                ${fmtSMA(sma150, 'SMA 150', price > (sma150||0))}
                ${fmtSMA(sma50,  'SMA 50',  price > (sma50 ||0))}
              </div>
            </div>`;
          })()}
        </td>
      </tr>`;
  }).join('');
}

function toggleRow(i) {
  const r = document.getElementById('row-' + i);
  const isOpen = r.classList.toggle('open');
  if (isOpen) {
    const sym = r.previousElementSibling.getAttribute('data-symbol');
    initChart(sym);
  }
}

async function initChart(symbol) {
  const container = document.getElementById(`chart-${symbol}`);
  if (!container || container.dataset.loaded === '1') return;
  container.dataset.loaded = '1';
  try {
    const res = await fetch(`/api/history/${symbol}`);
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    if (container._resizeObserver) {
      container._resizeObserver.disconnect();
      delete container._resizeObserver;
    }
    container.innerHTML = '';
    container.classList.remove('chart-loading');
    container.classList.add('chart-container');

    const chart = LightweightCharts.createChart(container, {
      width: container.clientWidth,
      height: container.clientHeight || 560,
      layout: { background: { color: getChartTheme().bg }, textColor: getChartTheme().text },
      grid: { vertLines: { color: getChartTheme().border }, horzLines: { color: getChartTheme().border } },
      timeScale: { borderColor: getChartTheme().border },
      rightPriceScale: { borderColor: getChartTheme().border, scaleMargins: { top: 0.08, bottom: 0.28 } },
    });

    const resizeObserver = new ResizeObserver(entries => {
      for (let entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0) {
          chart.resize(width, height);
        }
      }
    });
    resizeObserver.observe(container);
    container._resizeObserver = resizeObserver;

    // Candlestick series
    const candleSeries = chart.addCandlestickSeries({
      upColor:'#00e676', borderUpColor:'#00e676', wickUpColor:'#00e676',
      downColor:'#f44336', borderDownColor:'#f44336', wickDownColor:'#f44336',
    });
    candleSeries.setData(data);

    // Volume bars (separate price scale)
    const volSeries = chart.addHistogramSeries({
      color: '#26a69a', priceFormat: { type: 'volume' }, priceScaleId: 'volume',
    });
    chart.priceScale('volume').applyOptions({ scaleMargins: { top: 0.78, bottom: 0 } });
    volSeries.setData(data.map(d => ({
      time: d.time, value: d.value,
      color: d.close >= d.open ? '#00e67650' : '#f4433650',
    })));

    // SMA lines — calculated from price history
    const closes = data.map(d => d.close);
    const calcSMA = (arr, n) => arr.map((_, i) =>
      i < n - 1 ? null : arr.slice(i - n + 1, i + 1).reduce((s, v) => s + v, 0) / n
    );
    const addSMALine = (vals, color, title) => {
      const s = chart.addLineSeries({ color, lineWidth: 1, title,
        lastValueVisible: false, priceLineVisible: false, crosshairMarkerVisible: false });
      s.setData(data.map((d, i) => vals[i] != null ? { time: d.time, value: vals[i] } : null).filter(Boolean));
    };
    addSMALine(calcSMA(closes, 50),  '#ff9800', 'SMA50');
    addSMALine(calcSMA(closes, 150), '#a855f7', 'SMA150');
    addSMALine(calcSMA(closes, 200), '#00d4ff', 'SMA200');

    // Pivot / Stop / Target horizontal lines from VCP data
    const vcpR = (RAW_DATA?.vcp?.results || []).find(r => r.symbol === symbol);
    const pivotPrice = vcpR?.vcp_pattern?.pivot_price;
    const stopPrice  = vcpR?.pivot_proximity?.stop_loss_price;
    const settings   = getSettings();
    const targetR    = parseFloat(settings.target_r) || 2.0;
    const targetPrice = (pivotPrice && stopPrice)
      ? pivotPrice + targetR * (pivotPrice - stopPrice) : null;

    if (data.length > 0 && (pivotPrice || stopPrice)) {
      const startIdx = Math.max(0, data.length - 120);
      const tStart   = data[startIdx].time;
      const tEnd     = data[data.length - 1].time;
      const addHLine = (price, color, title, style) => {
        const s = chart.addLineSeries({ color, lineWidth: 2, lineStyle: style,
          title, lastValueVisible: true, priceLineVisible: false });
        s.setData([{ time: tStart, value: price }, { time: tEnd, value: price }]);
      };
      if (pivotPrice)  addHLine(pivotPrice,  '#ffd700', 'Pivot',              1); // gold dashed
      if (stopPrice)   addHLine(stopPrice,   '#f44336', 'Stop',               1); // red  dashed
      if (targetPrice) addHLine(targetPrice, '#ff80ab', `Target(${targetR}R)`,1); // pink dashed
    }

    setupChartLegend(chart, container, symbol, data, candleSeries);
    chart.timeScale().fitContent();
  } catch(e) {
    container.innerHTML = '❌ โหลดกราฟไม่สำเร็จ — ' + e.message;
  }
}

function exportToHTML() {
  // Clone the current document to avoid modifying the active view
  const clone = document.documentElement.cloneNode(true);

  // Remove interactive action buttons from the exported report so it is perfectly clean
  const runBtn = clone.querySelector('#runBtn');
  if (runBtn) runBtn.remove();
  const exportBtn = clone.querySelector('#exportBtn');
  if (exportBtn) exportBtn.remove();

  // Remove settings panel and trade plan setup from the exported report
  const settingsPanel = clone.querySelector('.settings-panel');
  if (settingsPanel) settingsPanel.remove();

  // Remove Paper Portfolio section and its card from the exported report
  const paperSection = clone.querySelector('#paperSection');
  if (paperSection) paperSection.remove();
  const paperCard = clone.querySelector('#paperCard');
  if (paperCard) paperCard.remove();

  // Get the entire HTML content of the page
  const htmlContent = '<!DOCTYPE html>\n' + clone.outerHTML;

  const market = currentMarket || 'TH';
  const dateStr = new Date().toISOString().slice(0, 10);

  // Create Blob and trigger download
  const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `Trading_Intelligence_Dashboard_${market}_${dateStr}.html`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function showToast(msg) {
  const t = document.getElementById('toast');
  t.innerText = msg;
  t.style.display = 'block';
  setTimeout(() => t.style.display = 'none', 5000);
}

async function runAnalysis() {
  const btn = document.getElementById('runBtn');
  const oldText = btn.innerText;
  btn.disabled = true;
  const startTime = Date.now();

  const s = getSettings();
  const params = new URLSearchParams({ market: currentMarket, ...s });

  // ── Build streaming progress modal ──────────────────────────────────────
  const log = [];
  let totalTasks = 0;

  const progressHtml = () => {
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    const done = log.length;
    const pct = totalTasks > 0 ? Math.round(done / totalTasks * 100) : 0;
    const rows = log.map(l => `
      <div style="display:flex;gap:10px;align-items:flex-start;padding:7px 10px;background:${l.ok?'rgba(0,230,118,.05)':'rgba(244,67,54,.06)'};border-radius:6px;margin-bottom:5px;border-left:3px solid ${l.ok?'var(--green)':'var(--red)'}">
        <span style="font-size:1rem;flex-shrink:0">${l.ok ? '✅' : '❌'}</span>
        <div style="flex:1;min-width:0">
          <span style="font-family:'JetBrains Mono',monospace;font-size:.82rem;color:${l.ok?'var(--green)':'var(--red)'}">${l.cmd}</span>
          <span style="color:var(--muted);font-size:.72rem;margin-left:8px">${l.elapsed ?? ''}s</span>
          ${!l.ok && l.err ? `<div style="font-size:.7rem;color:var(--muted);margin-top:3px;white-space:pre-wrap">${l.err.slice(0,500)}</div>` : ''}
        </div>
      </div>`).join('');
    const pending = totalTasks > 0 && done < totalTasks
      ? `<div style="color:var(--muted);font-size:.82rem;margin-top:8px">⏳ รอผล ${totalTasks - done} งานที่เหลือ...</div>` : '';
    return `
      <div style="margin-bottom:10px">
        <div style="display:flex;justify-content:space-between;margin-bottom:4px">
          <span style="font-size:.85rem;color:var(--cyan)">${done}/${totalTasks} tasks • ${elapsed}s</span>
          <span style="font-size:.85rem;color:var(--cyan)">${pct}%</span>
        </div>
        <div style="height:6px;background:rgba(255,255,255,.08);border-radius:3px;overflow:hidden">
          <div style="height:100%;width:${pct}%;background:var(--cyan);transition:width .3s;border-radius:3px"></div>
        </div>
      </div>
      ${rows}${pending}`;
  };

  document.getElementById('modalTitle').textContent = `⚙️ กำลังวิเคราะห์ตลาด ${currentMarket}...`;
  document.getElementById('modalBody').innerHTML = progressHtml();
  document.getElementById('modalOverlay').classList.add('open');

  const timer = setInterval(() => {
    btn.innerText = `⏳ ${Math.floor((Date.now() - startTime) / 1000)}s`;
    document.getElementById('modalBody').innerHTML = progressHtml();
  }, 1000);

  try {
    const evtSource = new EventSource(`/api/run/stream?${params}`);

    await new Promise((resolve, reject) => {
      evtSource.addEventListener('start', e => {
        const d = JSON.parse(e.data);
        totalTasks = d.total_tasks || totalTasks;
      });

      evtSource.addEventListener('task_done', e => {
        const d = JSON.parse(e.data);
        log.push(d);
        document.getElementById('modalBody').innerHTML = progressHtml();
      });

      evtSource.addEventListener('done', e => {
        evtSource.close();
        const d = JSON.parse(e.data);
        const ok = log.filter(l => l.ok);
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        document.getElementById('modalTitle').textContent =
          `🚀 ผลการวิเคราะห์ — ${ok.length}/${log.length} สำเร็จ (${elapsed}s)`;
        document.getElementById('modalBody').innerHTML = progressHtml();
        resolve(d);
      });

      evtSource.onerror = (err) => {
        evtSource.close();
        reject(new Error('SSE connection error'));
      };
    });

    await refreshHistoryList();
    document.getElementById('historySelect').value = '';
    document.getElementById('historyBadge').style.display = 'none';
    await loadData();
    await loadSignalResults();
  } catch(e) {
    showToast('❌ เกิดข้อผิดพลาด: ' + e.message);
    console.error(e);
  } finally {
    clearInterval(timer);
    btn.disabled = false;
    btn.innerText = oldText;
  }
}

// ==========================================================================
// TH Suite renderers — TradingView-powered Thai market views
// ==========================================================================

function _pctColor(v) {
  const n = Number(v) || 0;
  if (n >= 10) return 'var(--green)';
  if (n >= 0) return 'var(--gold)';
  return 'var(--red)';
}

function _emoji(v) {
  const n = Number(v) || 0;
  if (n >= 10) return '🟢';
  if (n >= 0) return '🟡';
  return '🔴';
}

function renderThaiBreadth(data) {
  const el = document.getElementById('thBreadthContent');
  if (!el) return;
  if (!data) {
    el.innerHTML = '<span style="color:var(--muted)">⚠️ ยังไม่มีข้อมูล TH Breadth — กด Run Fresh Analysis</span>';
    return;
  }
  const b = data.breadth || {};
  const c = data.composite || {};
  const score = data.composite_score ?? c.score ?? 0;
  const regime = data.regime || c.regime || '—';
  const ts = (data.generated || '').replace('_', ' ');
  const regimeColor = score >= 70 ? 'var(--green)' : score >= 50 ? 'var(--cyan)' : score >= 30 ? 'var(--gold)' : 'var(--red)';

  el.innerHTML = `
    <div style="display:flex;flex-wrap:wrap;gap:24px;align-items:center;margin-bottom:12px">
      <div style="font-size:2.2rem;font-weight:700;color:${regimeColor}">${score.toFixed(1)}</div>
      <div>
        <div style="font-size:1.1rem;color:${regimeColor};font-weight:600">${regime}</div>
        <div style="color:var(--muted);font-size:.85rem">${ts} · ${b.total_stocks || 0} stocks · TradingView</div>
      </div>
    </div>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:8px;font-size:.88rem">
      <div class="metric"><b>% above SMA50</b><br><span style="color:${_pctColor(b.pct_above_sma50)}">${(b.pct_above_sma50||0).toFixed(1)}%</span></div>
      <div class="metric"><b>% above SMA200</b><br><span style="color:${_pctColor(b.pct_above_sma200)}">${(b.pct_above_sma200||0).toFixed(1)}%</span></div>
      <div class="metric"><b>A/D</b><br><span style="color:var(--green)">${b.advancers||0}</span> / <span style="color:var(--red)">${b.decliners||0}</span></div>
      <div class="metric"><b>52w Hi/Lo</b><br><span style="color:var(--green)">${b.new_52w_highs||0}</span> / <span style="color:var(--red)">${b.new_52w_lows||0}</span></div>
      <div class="metric"><b>Median RSI</b><br>${(b.median_rsi||0).toFixed(1)}</div>
      <div class="metric"><b>Median 1M</b><br><span style="color:${_pctColor(b.median_perf_1m)}">${(b.median_perf_1m||0).toFixed(2)}%</span></div>
      <div class="metric"><b>Oversold (RSI&lt;30)</b><br>${b.rsi_oversold||0}</div>
      <div class="metric"><b>Overbought (RSI&gt;70)</b><br>${b.rsi_overbought||0}</div>
    </div>
  `;
}

function renderThaiSectorHeatmap(data) {
  const el = document.getElementById('thSectorContent');
  if (!el) return;
  if (!data || !data.sectors) {
    el.innerHTML = '<span style="color:var(--muted)">⚠️ ยังไม่มีข้อมูล Sector Heatmap</span>';
    return;
  }
  const ts = (data.generated || '').replace('_', ' ');
  const num = v => (typeof v === 'number' && !isNaN(v)) ? v : 0;
  const rows = (data.sectors || []).map(s => `
    <tr>
      <td>${s.rank ?? '-'}</td>
      <td>${_emoji(s.momentum_score)} <b>${s.sector || '?'}</b></td>
      <td style="text-align:right">${s.n_stocks ?? 0}</td>
      <td style="text-align:right;color:${_pctColor(s.median_perf_1m)}">${num(s.median_perf_1m).toFixed(2)}%</td>
      <td style="text-align:right;color:${_pctColor(s.median_perf_3m)}">${num(s.median_perf_3m).toFixed(2)}%</td>
      <td style="text-align:right;color:${_pctColor(s.median_perf_6m)}">${num(s.median_perf_6m).toFixed(2)}%</td>
      <td style="text-align:right;color:${_pctColor(s.median_perf_y)}">${num(s.median_perf_y).toFixed(2)}%</td>
      <td style="text-align:right;color:${_pctColor(s.momentum_score)};font-weight:600">${num(s.momentum_score).toFixed(2)}</td>
      <td style="font-size:.78rem;color:var(--muted)">${(s.top_stocks||[]).map(t=>(t.symbol||'').replace('.BK','')).join(', ')}</td>
    </tr>
  `).join('');
  el.innerHTML = `
    <div style="color:var(--muted);font-size:.85rem;margin-bottom:8px">${ts} · ${data.universe_size||0} stocks · ${(data.sectors||[]).length} sectors</div>
    <div style="overflow-x:auto"><table style="width:100%;font-size:.85rem">
      <thead><tr>
        <th>#</th><th>Sector</th><th style="text-align:right">N</th>
        <th style="text-align:right">1M</th><th style="text-align:right">3M</th>
        <th style="text-align:right">6M</th><th style="text-align:right">1Y</th>
        <th style="text-align:right">Score</th><th>Top stocks</th>
      </tr></thead>
      <tbody>${rows}</tbody>
    </table></div>
  `;
}

function renderThaiWatchlists(data) {
  const el = document.getElementById('thWatchlistsContent');
  if (!el) return;
  if (!data || !data.buckets) {
    el.innerHTML = '<span style="color:var(--muted)">⚠️ ยังไม่มีข้อมูล Watchlists</span>';
    return;
  }
  const currentLimit = document.getElementById('thWatchlistLimit')?.value || '10';
  const limit = parseInt(currentLimit);
  const ts = (data.generated || '').replace('_', ' ');
  const titles = {
    growth: '🚀 Growth',
    value: '💎 Value',
    momentum: '🔥 Momentum',
    mean_reversion: '⚖️ Mean-Reversion',
  };
  const criteria = data.criteria || {};
  const tabs = Object.entries(data.buckets).map(([name, rows], i) => {
    const crit = criteria[name];
    const items = (rows || []).slice(0, limit).map((r, ri) => `
      <tr>
        <td>${ri+1}</td>
        <td>
          <span class="star-btn" onclick="toggleStar(event, '${r.symbol}')" title="${isStarred(r.symbol) ? 'เลิกติดตาม' : 'ติดตาม'}" style="font-size:0.95rem; margin-right:4px;">
            ${isStarred(r.symbol) ? '★' : '☆'}
          </span>
          <b>${(r.symbol||'').replace('.BK','')}</b><br>
          <small style="color:var(--muted)">${(r.sector||'').slice(0,18)}</small>
        </td>
        <td style="text-align:right">฿${(r.price||0).toFixed(2)}</td>
        <td style="text-align:right">${(r.rsi||0).toFixed(0)}</td>
        <td style="text-align:right;color:${_pctColor(r.perf_1m)}">${(r.perf_1m||0).toFixed(1)}%</td>
        <td style="text-align:right;color:${_pctColor(r.perf_3m)}">${(r.perf_3m||0).toFixed(1)}%</td>
        <td style="text-align:right;font-weight:600;color:var(--cyan)">${r.score.toFixed(1)}</td>
      </tr>
    `).join('');
    return `
      <div style="margin-bottom:18px">
        <h4 style="margin:8px 0 4px 0">${titles[name] || name.toUpperCase()} <span style="color:var(--muted);font-weight:normal">(${rows.length})</span></h4>
        ${crit ? `<div style="font-size:.72rem;color:var(--muted);margin-bottom:6px;font-style:italic">เกณฑ์: ${crit}</div>` : ''}
        ${rows.length ? `<div style="overflow-x:auto;width:100%;"><table style="width:100%;font-size:.82rem"><thead><tr><th>#</th><th>Symbol</th><th style="text-align:right">Price</th><th style="text-align:right">RSI</th><th style="text-align:right">1M</th><th style="text-align:right">3M</th><th style="text-align:right">Score</th></tr></thead><tbody>${items}</tbody></table></div>` : '<div style="color:var(--muted);padding:8px 0">ไม่มี candidate ผ่านเกณฑ์</div>'}
      </div>
    `;
  }).join('');
  el.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;color:var(--muted);font-size:.85rem;margin-bottom:8px;flex-wrap:wrap;gap:10px">
      <div>${ts} · ${data.universe_size||0} stocks scanned · top ${data.top_per_bucket||30} per bucket</div>
      <select id="thWatchlistLimit" onchange="renderThaiWatchlists(RAW_DATA.thai_watchlists)" style="background:var(--bg3);border:1px solid var(--border);color:var(--text);padding:6px 12px;border-radius:8px;font-size:0.8rem">
        <option value="10" ${currentLimit === '10' ? 'selected' : ''}>แสดง 10 ตัวแรก</option>
        <option value="15" ${currentLimit === '15' ? 'selected' : ''}>แสดง 15 ตัวแรก</option>
        <option value="999" ${currentLimit === '999' ? 'selected' : ''}>แสดงทั้งหมด</option>
      </select>
    </div>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(380px,1fr));gap:18px">
      ${tabs}
    </div>
  `;
}

function renderThaiDividends(data) {
  const el = document.getElementById('thDividendsContent');
  if (!el) return;
  if (!data || !data.candidates) {
    el.innerHTML = '<span style="color:var(--muted)">⚠️ ยังไม่มีข้อมูล Dividend Screener</span>';
    return;
  }
  const currentLimit = document.getElementById('thDividendLimit')?.value || '10';
  const limit = parseInt(currentLimit);
  const ts = (data.generated || '').replace('_', ' ');
  const rows = (data.candidates || []).slice(0, limit).map((r, i) => {
    const gradeColor = r.grade === 'Excellent' ? 'var(--green)' : r.grade === 'Good' ? 'var(--cyan)' : r.grade === 'Fair' ? 'var(--gold)' : 'var(--red)';
    return `
      <tr>
        <td>${i+1}</td>
        <td>
          <span class="star-btn" onclick="toggleStar(event, '${r.symbol}')" title="${isStarred(r.symbol) ? 'เลิกติดตาม' : 'ติดตาม'}" style="font-size:0.95rem; margin-right:4px;">
            ${isStarred(r.symbol) ? '★' : '☆'}
          </span>
          <span class="paper-btn" style="background:var(--green)22;color:var(--green);border-color:var(--green)" onclick="event.stopPropagation();paperAddPick('${r.symbol}','TH',${(r.price||0).toFixed(2)},${((r.price||0)*0.92).toFixed(2)},${((r.price||0)*1.25).toFixed(2)},'thai-dividend',${r.score||0},100)" title="Add to Paper (Stop -8%, Target +25%)">📝</span>
          <b>${(r.symbol||'').replace('.BK','')}</b><br>
          <small style="color:var(--muted)">${(r.sector||'').slice(0,20)}</small>
        </td>
        <td style="text-align:right">฿${(r.price||0).toFixed(2)}</td>
        <td style="text-align:right;color:var(--green);font-weight:600">${(r.dividend_yield||0).toFixed(2)}%</td>
        <td style="text-align:right">${(r.pe_ratio||0).toFixed(1)}</td>
        <td style="text-align:right">${(r.rsi||0).toFixed(0)}</td>
        <td style="text-align:right;color:${_pctColor(r.perf_y)}">${(r.perf_y||0).toFixed(1)}%</td>
        <td style="text-align:right;font-weight:600">${(r.score||0).toFixed(1)}</td>
        <td style="color:${gradeColor};font-weight:600">${r.grade}</td>
      </tr>
    `;
  }).join('');
  const f = data.filters || {};
  el.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;color:var(--muted);font-size:.85rem;margin-bottom:8px;flex-wrap:wrap;gap:10px">
      <div>
        ${ts} · ${data.universe_size||0} stocks scanned · ${data.candidates.length} qualified ·
        Filters: yield ≥ ${f.min_yield_pct||3}%, mcap ≥ ${((f.min_market_cap||5e9)/1e9).toFixed(1)}B THB, P/E ${(f.pe_range||[4,25]).join('-')}
      </div>
      <select id="thDividendLimit" onchange="renderThaiDividends(RAW_DATA.thai_dividends)" style="background:var(--bg3);border:1px solid var(--border);color:var(--text);padding:6px 12px;border-radius:8px;font-size:0.8rem">
        <option value="10" ${currentLimit === '10' ? 'selected' : ''}>แสดง 10 ตัวแรก</option>
        <option value="30" ${currentLimit === '30' ? 'selected' : ''}>แสดง 30 ตัวแรก</option>
        <option value="999" ${currentLimit === '999' ? 'selected' : ''}>แสดงทั้งหมด</option>
      </select>
    </div>
    <div style="overflow-x:auto"><table style="width:100%;font-size:.85rem">
      <thead><tr>
        <th>#</th><th>Symbol</th><th style="text-align:right">Price</th>
        <th style="text-align:right">Yield</th><th style="text-align:right">P/E</th>
        <th style="text-align:right">RSI</th><th style="text-align:right">1Y</th>
        <th style="text-align:right">Score</th><th>Grade</th>
      </tr></thead>
      <tbody>${rows}</tbody>
    </table></div>
  `;
}

// ────────────────────────────────────────────────────────────────────────────
// Paper Trade Simulator
// ────────────────────────────────────────────────────────────────────────────

const VALID_EMOTIONS = ['calm','fearful','greedy','frustrated','fomo','confident','uncertain'];

async function paperRefresh() {
  try {
    const marketParam = currentMarket ? `&market=${encodeURIComponent(currentMarket)}` : '';
    const [openRes, closedRes, statsRes] = await Promise.all([
      fetch(`/api/paper/list?status=open${marketParam}`).then(r=>r.json()),
      fetch(`/api/paper/list?status=closed${marketParam}`).then(r=>r.json()),
      fetch(`/api/paper/stats?market=${encodeURIComponent(currentMarket || '')}`).then(r=>r.json()),
    ]);
    renderPaperStats(statsRes);
    renderPaperOpen(openRes);
    renderPaperClosed(closedRes);
    if (CURRENT_DASHBOARD_TAB === 'decisions') {
      renderTradeDecisions([...(openRes || []), ...(closedRes || [])], statsRes);
    }
  } catch (e) {
    console.error('paperRefresh failed:', e);
  }
}

async function paperUpdateMarks(event) {
  const btn = event && event.target;
  if (btn) { btn.disabled = true; btn.textContent = '⏳ Updating...'; }
  try {
    const r = await fetch('/api/paper/update_marks', {method:'POST'});
    const d = await r.json();
    if (d.error) { alert('Update error: ' + d.error); return; }
    let summary = `Updated ${d.updated} positions`;
    const closedStop = (d.results||[]).filter(x=>x.action==='auto_closed_stop');
    const closedTgt = (d.results||[]).filter(x=>x.action==='auto_closed_target' || x.action==='auto_closed_short_target');
    const closedTime = (d.results||[]).filter(x=>x.action==='auto_closed_time');
    if (closedStop.length) summary += `\n🛑 ${closedStop.length} hit STOP: ${closedStop.map(x=>x.symbol).join(', ')}`;
    if (closedTgt.length) summary += `\n🎯 ${closedTgt.length} hit TARGET: ${closedTgt.map(x=>x.symbol).join(', ')}`;
    if (closedTime.length) summary += `\nTIME ${closedTime.length} time stop: ${closedTime.map(x=>x.symbol).join(', ')}`;
    alert(summary);
    await paperRefresh();
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '🔄 Update Marks'; }
  }
}

function renderPaperStats(s) {
  const el = document.getElementById('paperStatsBar');
  if (!el || !s) return;
  const tile = (label, value, color) => `<div class="metric" style="min-width:110px"><b>${label}</b><br><span style="color:${color||'inherit'};font-size:1rem;font-weight:600">${value}</span></div>`;
  const rColor = v => v > 0 ? 'var(--green)' : v < 0 ? 'var(--red)' : 'var(--muted)';
  const wr = s.win_rate ? (s.win_rate*100).toFixed(0) + '%' : '-';
  const d = s.discipline || {};
  const stopRate = d.stop_respect_rate !== null && d.stop_respect_rate !== undefined ? (d.stop_respect_rate*100).toFixed(0) + '%' : '-';
  el.innerHTML =
    tile('Open', s.open_positions||0) +
    tile('Closed', s.closed_trades||0) +
    tile('Win Rate', wr, s.win_rate>=0.5?'var(--green)':'var(--gold)') +
    tile('Avg Win', (s.avg_win_r||0).toFixed(2)+'R', 'var(--green)') +
    tile('Avg Loss', (s.avg_loss_r||0).toFixed(2)+'R', 'var(--red)') +
    tile('Expectancy', (s.expectancy_r||0).toFixed(2)+'R', rColor(s.expectancy_r)) +
    tile('Total R', (s.total_realized_r||0).toFixed(2)+'R', rColor(s.total_realized_r)) +
    tile('Realized P/L (ปิดแล้ว)', (s.total_realized_pnl||0).toFixed(0), rColor(s.total_realized_pnl)) +
    tile('Trading Cost (ปิดแล้ว)', (s.total_closed_cost||0).toFixed(0), 'var(--gold)') +
    tile('Unrealized P/L (ยังเปิด)', (s.total_unrealized_pnl||0).toFixed(0), rColor(s.total_unrealized_pnl)) +
    tile('Stop Respect', stopRate, d.stop_respect_rate >= 0.8 ? 'var(--green)' : 'var(--gold)') +
    tile('Patience', d.patience_score !== null && d.patience_score !== undefined ? (d.patience_score*100).toFixed(0)+'%' : '-', d.patience_score >= 0.7 ? 'var(--green)' : d.patience_score >= 0.5 ? 'var(--gold)' : 'var(--red)');
}

function _ptStaleness(lastUpdated) {
  if (!lastUpdated) return {label:'never', color:'var(--red)'};
  const ageMin = (Date.now() - new Date(lastUpdated).getTime()) / 60000;
  if (ageMin < 5) return {label:'just now', color:'var(--green)'};
  if (ageMin < 60) return {label:`${ageMin.toFixed(0)}m ago`, color:'var(--green)'};
  if (ageMin < 24*60) return {label:`${(ageMin/60).toFixed(1)}h ago`, color:'var(--gold)'};
  return {label:`${(ageMin/(24*60)).toFixed(0)}d ago`, color:'var(--red)'};
}

function renderPaperOpen(rows) {
  const el = document.getElementById('paperOpenContent');
  if (!el) return;
  if (!rows || rows.length === 0) {
    el.innerHTML = '<div style="color:var(--muted)">⚠️ ยังไม่มี open positions — กด "Add to Paper" จากตาราง Picks เพื่อเริ่มทดสอบ</div>';
    return;
  }
  const trs = rows.map((r, i) => {
    const sym = (r.symbol||'').replace('.BK','');
    const cur = r.market === 'TH' ? '฿' : '$';
    const rColor = (r.unrealized_r||0) > 0 ? 'var(--green)' : (r.unrealized_r||0) < 0 ? 'var(--red)' : 'var(--muted)';
    const drawdownPct = (r.unrealized_r && r.unrealized_r < 0) ? (r.unrealized_r * -100) : 0;
    const warn = drawdownPct >= 50 ? ' 🚨' : drawdownPct >= 25 ? ' ⚠️' : '';
    // Format P/L with proper sign, avoiding "-0" / "+0" cosmetic issues
    const pnl = r.unrealized_pnl || 0;
    const pnlRounded = Math.round(pnl);
    const pnlText = pnlRounded === 0 ? `${cur}0` : pnlRounded > 0 ? `+${cur}${pnlRounded}` : `-${cur}${Math.abs(pnlRounded)}`;
    // Color is muted (grey) when rounded value is 0 — even if technically tiny non-zero
    const rColorEff = pnlRounded === 0 ? 'var(--muted)' : rColor;
    const rValRounded = Math.round((r.unrealized_r||0) * 100) / 100;
    const rText = rValRounded === 0 ? '0.00R' : rValRounded > 0 ? `+${rValRounded.toFixed(2)}R` : `${rValRounded.toFixed(2)}R`;
    const tagBadge = r.source ? `<span style="background:var(--bg);padding:1px 4px;border-radius:3px;font-size:.7rem;color:var(--muted)">${r.source}</span>` : '';
    const stale = _ptStaleness(r.last_updated);

    // MAE/MFE chips (show how low/high it went)
    const mae = r.mae || r.entry_price;
    const mfe = r.mfe || r.entry_price;
    const maePct = ((mae - r.entry_price) / r.entry_price * 100);
    const mfePct = ((mfe - r.entry_price) / r.entry_price * 100);
    const maeChip = `<span title="Max Adverse Excursion — ราคาต่ำสุดที่ไปถึง" style="color:var(--red);font-size:.7rem">↓${cur}${mae.toFixed(2)} (${maePct.toFixed(1)}%)</span>`;
    const mfeChip = `<span title="Max Favorable Excursion — ราคาสูงสุดที่ไปถึง" style="color:var(--green);font-size:.7rem">↑${cur}${mfe.toFixed(2)} (+${mfePct.toFixed(1)}%)</span>`;

    // Notes preview
    const noteEntry = (r.notes_entry||'').slice(0,80);
    const noteJournal = (r.journal_text||'').replace(/\n/g,' ').slice(0,120);
    const hasNotes = noteEntry || noteJournal;

    return `
      <tr style="cursor:pointer" onclick="_ptToggleDetail(${i})" title="คลิกเพื่อดูรายละเอียด">
        <td>${r.id}</td>
        <td><b>${sym}</b><br>${tagBadge}</td>
        <td>${r.market}</td>
        <td style="text-align:right">${cur}${(r.entry_price||0).toFixed(2)}</td>
        <td style="text-align:right">${r.shares||0}<br><small style="color:var(--muted);font-size:.65rem">risk ${cur}${(r.initial_risk||0).toFixed(0)}</small></td>
        <td style="text-align:right;color:var(--red)">${cur}${(r.stop_price||0).toFixed(2)}</td>
        <td style="text-align:right;color:var(--green)">${cur}${(r.target_price||0).toFixed(2)}</td>
        <td style="text-align:right">${cur}${(r.last_price||0).toFixed(2)}${warn}<br><small style="color:${stale.color};font-size:.62rem">${stale.label}</small></td>
        <td style="text-align:right;color:${rColorEff};font-weight:600" title="กำไร/ขาดทุน (เงินบาท/ดอลลาร์) — exact: ${pnl.toFixed(2)}">${pnlText}</td>
        <td style="text-align:right;color:${rColorEff};font-weight:600" title="กำไร/ขาดทุน คิดเป็น R-multiple (1R = เงินที่เสี่ยง) — exact: ${(r.unrealized_r||0).toFixed(4)}R">${rText}</td>
        <td style="text-align:right">${r.days_held||0}d</td>
        <td>${r.journal_emotion||'-'}</td>
        <td onclick="event.stopPropagation()">
          <button onclick="paperClosePrompt(${r.id}, '${sym}', ${r.last_price||0})" title="ปิด position นี้ (ออกตลาด)" style="padding:3px 10px;font-size:.75rem;cursor:pointer;background:var(--red)22;color:var(--red);border:1px solid var(--red);border-radius:4px">🚪 Close</button>
          <button onclick="paperJournalPrompt(${r.id}, '${sym}')" title="บันทึก journal entry (ไม่ปิด position)" style="padding:3px 10px;font-size:.75rem;cursor:pointer;background:var(--bg);color:var(--cyan);border:1px solid var(--cyan);border-radius:4px;margin-left:4px">✎ Note</button>
        </td>
      </tr>
      <tr id="ptDetail-${i}" style="display:none;background:var(--bg)">
        <td colspan="13" style="padding:14px">
          <!-- Chart container — lazy loaded on first expand -->
          <div id="paperChart-${i}" data-symbol="${r.symbol}" data-entry="${r.entry_price}" data-stop="${r.stop_price}" data-target="${r.target_price}" data-mae="${mae}" data-mfe="${mfe}"
               style="height:320px;background:var(--bg2);border:1px solid var(--border);border-radius:8px;margin-bottom:14px;display:flex;align-items:center;justify-content:center;color:var(--muted);font-size:.85rem">
            📊 กำลังโหลดกราฟ...
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
            <div>
              <div style="color:var(--muted);font-size:.7rem;text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px">📊 Max Excursions (since entry)</div>
              <div style="display:flex;gap:12px;margin-bottom:10px">${maeChip} ${mfeChip}</div>
              <div style="color:var(--muted);font-size:.7rem;text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px">📅 Entry</div>
              <div style="font-size:.82rem">at ${(r.entry_at||'').replace('T',' ')} · source <b>${r.source||'manual'}</b> ${r.source_score?`(score ${r.source_score.toFixed(1)})`:''}</div>
            </div>
            <div>
              <div style="color:var(--muted);font-size:.7rem;text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px">📝 Entry notes</div>
              <div style="font-size:.82rem;color:${noteEntry?'var(--text)':'var(--muted)'};margin-bottom:10px">${noteEntry || '(ไม่มี — ตอนเปิดไม่ได้เขียน)'}</div>
              <div style="color:var(--muted);font-size:.7rem;text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px">📖 Journal log</div>
              <div style="font-size:.82rem;color:${noteJournal?'var(--text)':'var(--muted)'};white-space:pre-wrap;max-height:120px;overflow-y:auto">${(r.journal_text||'(ยังไม่มี journal — กด ✎ Note เพื่อบันทึก)').replace(/</g,'&lt;')}</div>
            </div>
          </div>
        </td>
      </tr>
    `;
  }).join('');
  el.innerHTML = `
    <div style="color:var(--muted);font-size:.8rem;margin-bottom:6px">📂 OPEN POSITIONS — ${rows.length} tickets</div>
    <div style="overflow-x:auto"><table style="width:100%;font-size:.82rem">
      <thead><tr>
        <th>ID</th><th>Symbol</th><th>Mkt</th>
        <th style="text-align:right">Entry</th><th style="text-align:right">Shares</th>
        <th style="text-align:right">Stop</th><th style="text-align:right">Target</th>
        <th style="text-align:right">Last</th>
        <th style="text-align:right" title="กำไร/ขาดทุน (เงินบาท/ดอลลาร์)">P/L (กำไร)</th>
        <th style="text-align:right" title="กำไร/ขาดทุนคิดเป็น R-multiple (1R = เงินที่เสี่ยง)">R</th>
        <th style="text-align:right">Days</th><th>Emotion</th><th></th>
      </tr></thead>
      <tbody>${trs}</tbody>
    </table></div>
  `;
}

function _ptToggleDetail(i, prefix) {
  prefix = prefix || 'ptDetail';
  const row = document.getElementById(prefix + '-' + i);
  if (!row) return;
  const wasHidden = row.style.display === 'none';
  row.style.display = wasHidden ? 'table-row' : 'none';
  // Lazy-load chart on first expand (only for open positions; closed don't have chart)
  if (wasHidden && prefix === 'ptDetail') {
    const chartEl = document.getElementById('paperChart-' + i);
    if (chartEl && !chartEl.dataset.loaded) {
      chartEl.dataset.loaded = '1';
      initPaperChart(chartEl);
    }
  }
}

async function initPaperChart(el) {
  const symbol = el.dataset.symbol;
  const entry = parseFloat(el.dataset.entry);
  const stop = parseFloat(el.dataset.stop);
  const target = parseFloat(el.dataset.target);
  const mae = parseFloat(el.dataset.mae);
  const mfe = parseFloat(el.dataset.mfe);
  try {
    const res = await fetch(`/api/history/${symbol}`);
    const data = await res.json();
    if (data.error || !Array.isArray(data) || data.length === 0) {
      el.innerHTML = '<span style="color:var(--red)">⚠️ ไม่พบกราฟราคา</span>';
      return;
    }
    if (el._resizeObserver) {
      el._resizeObserver.disconnect();
      delete el._resizeObserver;
    }
    el.innerHTML = '';
    const theme = getChartTheme();
    const chart = LightweightCharts.createChart(el, {
      width: el.clientWidth, height: 320,
      layout: { background: { color: theme.bg }, textColor: theme.text },
      grid: { vertLines: { color: theme.border }, horzLines: { color: theme.border } },
      timeScale: { borderColor: theme.border, timeVisible: false },
      rightPriceScale: { borderColor: theme.border, scaleMargins: { top: 0.1, bottom: 0.25 } },
      crosshair: { mode: 1 },
    });
    // Candlestick
    const candle = chart.addCandlestickSeries({
      upColor: theme.green, downColor: theme.red,
      borderUpColor: theme.green, borderDownColor: theme.red,
      wickUpColor: theme.green, wickDownColor: theme.red,
    });
    candle.setData(data);
    // Volume
    const vol = chart.addHistogramSeries({
      priceFormat:{type:'volume'}, priceScaleId:'',
      scaleMargins:{top:0.78, bottom:0}
    });
    vol.setData(data.map(d => ({
      time: d.time, value: d.value,
      color: d.close >= d.open ? theme.green + '55' : theme.red + '55'
    })));
    // Price lines: entry (cyan dashed), stop (red), target (green), MAE/MFE markers
    candle.createPriceLine({ price: entry, color: '#58a6ff', lineWidth: 2, lineStyle: 2, axisLabelVisible: true, title: `Entry ${entry.toFixed(2)}` });
    candle.createPriceLine({ price: stop, color: theme.red, lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: `Stop ${stop.toFixed(2)}` });
    candle.createPriceLine({ price: target, color: theme.green, lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: `Target ${target.toFixed(2)}` });
    if (mae && Math.abs(mae - entry) > 0.01) {
      candle.createPriceLine({ price: mae, color: theme.red + '88', lineWidth: 1, lineStyle: 1, axisLabelVisible: false, title: `MAE ${mae.toFixed(2)}` });
    }
    if (mfe && Math.abs(mfe - entry) > 0.01) {
      candle.createPriceLine({ price: mfe, color: theme.green + '88', lineWidth: 1, lineStyle: 1, axisLabelVisible: false, title: `MFE ${mfe.toFixed(2)}` });
    }
    setupChartLegend(chart, el, symbol, data, candle);
    chart.timeScale().fitContent();
    // Responsive resize
    const resizeObserver = new ResizeObserver(() => chart.applyOptions({ width: el.clientWidth }));
    resizeObserver.observe(el);
    el._resizeObserver = resizeObserver;
  } catch (e) {
    el.innerHTML = `<span style="color:var(--red)">⚠️ Chart error: ${e.message}</span>`;
  }
}

function renderPaperClosed(rows) {
  const el = document.getElementById('paperClosedContent');
  if (!el) return;
  if (!rows || rows.length === 0) { el.innerHTML = ''; return; }
  const trs = rows.slice(0, 30).map((r, i) => {
    const sym = (r.symbol||'').replace('.BK','');
    const cur = r.market === 'TH' ? '฿' : '$';
    const isWin = (r.realized_r||0) > 0;
    const color = isWin ? 'var(--green)' : (r.realized_r||0) < 0 ? 'var(--red)' : 'var(--muted)';
    const statusEmoji = r.status === 'closed_target' ? '🎯' : r.status === 'closed_stop' ? '🛑' : '✋';
    const mae = r.mae || r.entry_price;
    const mfe = r.mfe || r.entry_price;
    const maePct = ((mae - r.entry_price) / r.entry_price * 100);
    const mfePct = ((mfe - r.entry_price) / r.entry_price * 100);
    // "If you held to target": what would the R-multiple have been if mfe became exit?
    const riskPerShare = Math.abs(r.entry_price - r.stop_price);
    const ifHeldR = riskPerShare > 0 ? (mfe - r.entry_price) / riskPerShare : 0;
    const leftOnTableR = ifHeldR - (r.realized_r || 0);
    const noteEntry = (r.notes_entry||'').slice(0,80);
    const noteJournal = (r.journal_text||'').replace(/\n/g,' ').slice(0,200);

    return `
      <tr style="cursor:pointer" onclick="_ptToggleDetail(${i}, 'ptClosedDetail')">
        <td>${r.id}</td>
        <td><b>${sym}</b></td>
        <td style="text-align:right">${cur}${(r.entry_price||0).toFixed(2)}</td>
        <td style="text-align:right">${cur}${(r.exit_price||0).toFixed(2)}</td>
        <td>${statusEmoji} ${(r.status||'').replace('closed_','')}</td>
        <td style="text-align:right;color:${color};font-weight:600">${(r.realized_pnl||0).toFixed(0)}</td>
        <td style="text-align:right;color:${color};font-weight:600">${(r.realized_r||0).toFixed(2)}R</td>
        <td style="text-align:right">${r.days_held||0}d</td>
        <td>${r.journal_emotion||'-'}</td>
      </tr>
      <tr id="ptClosedDetail-${i}" style="display:none;background:var(--bg)">
        <td colspan="9" style="padding:14px">
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
            <div>
              <div style="color:var(--muted);font-size:.7rem;text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px">📊 Max Excursions during hold</div>
              <div style="font-size:.82rem;margin-bottom:10px">
                <span style="color:var(--red)">↓ MAE: ${cur}${mae.toFixed(2)} (${maePct.toFixed(1)}%)</span> &nbsp;
                <span style="color:var(--green)">↑ MFE: ${cur}${mfe.toFixed(2)} (+${mfePct.toFixed(1)}%)</span>
              </div>
              ${leftOnTableR > 0.3 ? `<div style="color:var(--gold);font-size:.78rem;padding:6px;background:var(--gold)11;border-radius:4px">💡 Left on table: ${leftOnTableR.toFixed(2)}R — ถ้าถือจนถึง MFE จะได้ ${ifHeldR.toFixed(2)}R</div>` : ''}
              <div style="color:var(--muted);font-size:.7rem;text-transform:uppercase;letter-spacing:.5px;margin-top:10px;margin-bottom:4px">📅 Timeline</div>
              <div style="font-size:.82rem">Entry ${(r.entry_at||'').replace('T',' ')}<br>Exit &nbsp;&nbsp;${(r.exit_at||'').replace('T',' ')}</div>
            </div>
            <div>
              <div style="color:var(--muted);font-size:.7rem;text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px">📝 Entry notes</div>
              <div style="font-size:.82rem;color:${noteEntry?'var(--text)':'var(--muted)'};margin-bottom:10px">${noteEntry || '(ไม่มี)'}</div>
              <div style="color:var(--muted);font-size:.7rem;text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px">📖 Journal</div>
              <div style="font-size:.82rem;color:${noteJournal?'var(--text)':'var(--muted)'};white-space:pre-wrap;max-height:120px;overflow-y:auto">${(r.journal_text||'(ไม่มี)').replace(/</g,'&lt;')}</div>
            </div>
          </div>
        </td>
      </tr>
    `;
  }).join('');
  el.innerHTML = `
    <div style="color:var(--muted);font-size:.8rem;margin:8px 0 6px">📜 CLOSED TRADES — ${rows.length} total (showing latest 30)</div>
    <div style="overflow-x:auto"><table style="width:100%;font-size:.82rem">
      <thead><tr>
        <th>ID</th><th>Symbol</th>
        <th style="text-align:right">Entry</th><th style="text-align:right">Exit</th>
        <th>Status</th>
        <th style="text-align:right" title="กำไร/ขาดทุน (เงินบาท/ดอลลาร์)">P/L (กำไร)</th>
        <th style="text-align:right" title="กำไร/ขาดทุนคิดเป็น R-multiple">R</th>
        <th style="text-align:right">Days</th><th>Emotion</th>
      </tr></thead>
      <tbody>${trs}</tbody>
    </table></div>
  `;
}

// ────────────────────────────────────────────────────────────────────────────
// Paper Trade Modal — styled replacement for prompt()
// ────────────────────────────────────────────────────────────────────────────

async function loadTradeDecisions() {
  const content = document.getElementById('tradeDecisionContent');
  if (content) content.innerHTML = 'Loading trade decisions...';
  try {
    const market = encodeURIComponent(currentMarket || '');
    const [rows, stats] = await Promise.all([
      fetch(`/api/paper/list?status=all&market=${market}`).then(r => r.json()),
      fetch(`/api/paper/stats?market=${market}`).then(r => r.json()),
    ]);
    renderTradeDecisions(rows, stats);
  } catch (e) {
    console.error('loadTradeDecisions failed:', e);
    if (content) content.innerHTML = `<span style="color:var(--red)">Could not load trade decisions: ${_tdEscape(e.message)}</span>`;
  }
}

function _tdEscape(v) {
  return String(v ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function _tdNum(v) {
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

function _tdCurrency(r) {
  return r && r.market === 'TH' ? 'THB ' : '$';
}

function _tdPrice(v, r) {
  const n = _tdNum(v);
  if (n === null) return '--';
  return `${_tdCurrency(r)}${n.toFixed(2)}`;
}

function _tdMoney(v, r) {
  const n = _tdNum(v);
  if (n === null) return '--';
  const sign = n > 0 ? '+' : n < 0 ? '-' : '';
  return `${sign}${_tdCurrency(r)}${Math.abs(n).toFixed(0)}`;
}

function _tdR(v) {
  const n = _tdNum(v);
  if (n === null) return '--';
  const sign = n > 0 ? '+' : '';
  return `${sign}${n.toFixed(2)}R`;
}

function _tdTime(ts) {
  if (!ts) return '--';
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return _tdEscape(ts);
  return d.toLocaleString(undefined, {
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function _tdSignalDate(notes) {
  const m = String(notes || '').match(/signal_date=([0-9]{4}-[0-9]{2}-[0-9]{2})/);
  return m ? m[1] : '--';
}

function _tdTechnique(source) {
  const map = {
    'thai-swing-momentum': {
      title: 'Swing Momentum',
      detail: 'Thai swing scanner momentum / continuation setup.',
    },
    'thai-swing-dip': {
      title: 'Swing Dip / Pullback',
      detail: 'Thai swing scanner pullback setup after a qualified dip.',
    },
    'vcp-screener': {
      title: 'VCP / Minervini',
      detail: 'Volatility contraction setup from the VCP scanner.',
    },
    vcp: {
      title: 'VCP / Minervini',
      detail: 'Volatility contraction setup from the VCP scanner.',
    },
    'canslim-screener': {
      title: 'CANSLIM',
      detail: 'Fundamental and relative-strength screen inspired by CANSLIM.',
    },
    'step-5-breakout': {
      title: 'Breakout Trade Plan',
      detail: 'Breakout entry plan with entry, stop, target, and position sizing.',
    },
  };
  return map[source] || {
    title: source ? source : 'Manual / Unknown',
    detail: source ? `Raw source: ${source}` : 'No source tag was recorded.',
  };
}

function _tdStatusPill(status) {
  const safe = _tdEscape(status || 'open');
  const css = ['open', 'closed_target', 'closed_stop', 'closed_time', 'closed_manual'].includes(status) ? status : 'closed_manual';
  return `<span class="trade-status-pill trade-status-${css}">${safe}</span>`;
}

function _tdCloseReason(r) {
  const status = r.status || 'open';
  if (status === 'open') return 'Still open; waiting for stop, target, or manual close.';
  if (status === 'closed_target') return 'Auto-closed because latest price hit the target.';
  if (status === 'closed_stop') return 'Auto-closed because latest price hit the stop loss.';
  if (status === 'closed_time') return 'Auto-closed because the trade exceeded the source holding limit without enough progress.';
  if (status === 'closed_manual') return 'Closed manually from the dashboard.';
  return `Closed with status: ${status}`;
}

function _tdOpenRule(r) {
  const notes = String(r.notes_entry || '');
  if (r.source && r.source !== 'manual') {
    if (notes.includes('AUTO-PAPER')) {
      return 'Auto-paper opened this because score was at least 70, signal age was within 10 days, entry/stop/target were valid, and the symbol was not already open or linked at selection time.';
    }
    return 'Opened from a saved scanner or trade-plan source; the dashboard record has entry, stop, target, shares, and score, but does not include the full original gate snapshot.';
  }
  if (notes.includes('AUTO-PAPER')) {
    return 'Auto-paper opened this because score was at least 70, signal age was within 10 days, entry/stop/target were valid, and the symbol was not already open or linked at selection time.';
  }
  return 'Manual paper trade opened from the dashboard.';
}

function renderTradeDecisions(rows, stats) {
  const content = document.getElementById('tradeDecisionContent');
  if (!content) return;

  const safeRows = Array.isArray(rows) ? rows.slice() : [];
  safeRows.sort((a, b) => {
    const at = new Date(a.entry_at || a.exit_at || 0).getTime() || 0;
    const bt = new Date(b.entry_at || b.exit_at || 0).getTime() || 0;
    return (bt - at) || ((b.id || 0) - (a.id || 0));
  });

  const openCount = safeRows.filter(r => (r.status || 'open') === 'open').length;
  const closedCount = safeRows.length - openCount;
  const realized = stats && stats.total_realized_pnl !== undefined ? stats.total_realized_pnl : safeRows.reduce((s, r) => s + (Number(r.realized_pnl) || 0), 0);
  const unrealized = stats && stats.total_unrealized_pnl !== undefined ? stats.total_unrealized_pnl : safeRows.reduce((s, r) => s + (Number(r.unrealized_pnl) || 0), 0);

  const setText = (id, value) => {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  };
  setText('tdTotal', String(safeRows.length));
  setText('tdOpen', String(openCount));
  setText('tdClosed', String(closedCount));
  setText('tdRealized', _tdMoney(realized, {market: currentMarket}));
  setText('tdUnrealized', _tdMoney(unrealized, {market: currentMarket}));
  setText('tradeDecisionAsOf', new Date().toLocaleString());

  if (safeRows.length === 0) {
    content.innerHTML = '<div class="signal-note">No paper trade decisions found for this market yet.</div>';
    return;
  }

  const rowsHtml = safeRows.map((r, i) => {
    const sym = _tdEscape((r.symbol || '').replace('.BK', ''));
    const technique = _tdTechnique(r.source);
    const score = r.source_score === null || r.source_score === undefined ? '--' : Number(r.source_score).toFixed(1);
    const signalDate = _tdSignalDate(r.notes_entry);
    const riskPerShare = Math.abs((Number(r.entry_price) || 0) - (Number(r.stop_price) || 0));
    const totalRisk = r.initial_risk !== null && r.initial_risk !== undefined ? Number(r.initial_risk) : riskPerShare * (Number(r.shares) || 0);
    const resultPnl = (r.status || 'open') === 'open' ? r.unrealized_pnl : r.realized_pnl;
    const resultR = (r.status || 'open') === 'open' ? r.unrealized_r : r.realized_r;
    const resultColor = (Number(resultR) || 0) > 0 ? 'var(--green)' : (Number(resultR) || 0) < 0 ? 'var(--red)' : 'var(--muted)';
    const resultPrice = (r.status || 'open') === 'open' ? r.last_price : r.exit_price;
    const notes = r.notes_entry || '';
    const journal = r.journal_text || '';
    const closeReason = _tdCloseReason(r);

    return `
      <tr class="trade-decision-row" onclick="_ptToggleDetail(${i}, 'ptDecisionDetail')" title="Click to expand decision detail">
        <td>
          <div class="trade-ticket">
            <span class="trade-symbol">${sym || '--'}</span>
            ${_tdStatusPill(r.status || 'open')}
            <span class="trade-subtext">#${_tdEscape(r.id)} · ${_tdEscape(r.market || currentMarket || '--')}</span>
          </div>
        </td>
        <td>
          <div class="trade-technique">${_tdEscape(technique.title)}</div>
          <div class="trade-subtext">Score ${_tdEscape(score)} · Signal ${_tdEscape(signalDate)}</div>
          <div class="trade-subtext">${_tdEscape(technique.detail)}</div>
        </td>
        <td>
          <div class="trade-price-stack">
            <div class="trade-price-line"><span>Entry</span><b>${_tdPrice(r.entry_price, r)}</b></div>
            <div class="trade-price-line"><span>Stop</span><b style="color:var(--red)">${_tdPrice(r.stop_price, r)}</b></div>
            <div class="trade-price-line"><span>Target</span><b style="color:var(--green)">${_tdPrice(r.target_price, r)}</b></div>
            <div class="trade-subtext">Shares ${_tdEscape(r.shares || 0)} · 1R ${_tdMoney(totalRisk || 0, r)}</div>
          </div>
        </td>
        <td>
          <div>Open: ${_tdEscape(_tdTime(r.entry_at))}</div>
          <div class="trade-subtext">Exit/update: ${_tdEscape(_tdTime(r.exit_at || r.last_updated))}</div>
        </td>
        <td>
          <div class="trade-result" style="color:${resultColor}">${_tdMoney(resultPnl || 0, r)} / ${_tdR(resultR || 0)}</div>
          <div class="trade-subtext">Price ${_tdPrice(resultPrice, r)} · Days ${_tdEscape(r.days_held || 0)}</div>
        </td>
        <td>
          <div>${_tdEscape(closeReason)}</div>
          <div class="trade-subtext">Emotion: ${_tdEscape(r.journal_emotion || '-')}</div>
        </td>
      </tr>
      <tr id="ptDecisionDetail-${i}" class="trade-detail-row" style="display:none">
        <td colspan="6">
          <div class="trade-detail-panel">
            <div class="trade-detail-grid">
              <div class="trade-detail-block">
                <div class="trade-detail-label">Open Rule</div>
                <div class="trade-detail-body">${_tdEscape(_tdOpenRule(r))}</div>
                <div class="trade-subtext">Source: ${_tdEscape(r.source || 'manual')} · Score: ${_tdEscape(score)} · Signal date: ${_tdEscape(signalDate)}</div>
              </div>
              <div class="trade-detail-block">
                <div class="trade-detail-label">Risk / Plan</div>
                <div class="trade-detail-body">
                  Entry ${_tdPrice(r.entry_price, r)} · Stop ${_tdPrice(r.stop_price, r)} · Target ${_tdPrice(r.target_price, r)}<br>
                  Shares ${_tdEscape(r.shares || 0)} · Risk/share ${_tdPrice(riskPerShare, r)} · Initial risk ${_tdMoney(totalRisk || 0, r)}
                </div>
                <div class="trade-subtext trade-missing-data">Market volume at entry: not recorded yet.</div>
              </div>
              <div class="trade-detail-block">
                <div class="trade-detail-label">Exit Rule / Result</div>
                <div class="trade-detail-body">${_tdEscape(closeReason)}</div>
                <div class="trade-subtext">Result: ${_tdMoney(resultPnl || 0, r)} · ${_tdR(resultR || 0)}</div>
              </div>
            </div>
            <div class="trade-detail-grid" style="margin-top:12px">
              <div class="trade-detail-block">
                <div class="trade-detail-label">Entry Notes</div>
                <div class="trade-detail-body">${notes ? _tdEscape(notes) : '<span class="signal-note">No entry notes recorded.</span>'}</div>
              </div>
              <div class="trade-detail-block">
                <div class="trade-detail-label">Journal / Close Notes</div>
                <div class="trade-detail-body">${journal ? _tdEscape(journal) : '<span class="signal-note">No journal recorded.</span>'}</div>
              </div>
              <div class="trade-detail-block">
                <div class="trade-detail-label">Audit Fields</div>
                <div class="trade-detail-body">
                  Opened: ${_tdEscape(r.entry_at || '--')}<br>
                  Closed: ${_tdEscape(r.exit_at || '--')}<br>
                  Last update: ${_tdEscape(r.last_updated || '--')}
                </div>
              </div>
            </div>
          </div>
        </td>
      </tr>
    `;
  }).join('');

  content.innerHTML = `
    <div style="overflow-x:auto">
      <table class="signal-table trade-decision-table">
        <thead>
          <tr>
            <th>Ticket</th>
            <th>Decision / Technique</th>
            <th>Open Plan</th>
            <th>Timing</th>
            <th>Result</th>
            <th>Close Reason</th>
          </tr>
        </thead>
        <tbody>${rowsHtml}</tbody>
      </table>
    </div>
  `;
}

let _ptCurrencySymbol = '฿';      // updated from market context
let _ptSelectedEmotion = null;

function paperModalOpen() { document.getElementById('paperModal').classList.add('open'); }
function paperModalClose() {
  document.getElementById('paperModal').classList.remove('open');
  _ptSelectedEmotion = null;
}

function _emotionPills(defaultEmotion) {
  _ptSelectedEmotion = defaultEmotion || null;
  return VALID_EMOTIONS.map(e => {
    const active = e === defaultEmotion ? ' active' : '';
    return `<button type="button" class="pt-emotion-btn${active}" onclick="_ptPickEmotion(this, '${e}')">${_emotionIcon(e)} ${e}</button>`;
  }).join('');
}
function _emotionIcon(e) {
  return {calm:'😌', confident:'😎', fearful:'😨', greedy:'🤑', frustrated:'😤', fomo:'🤩', uncertain:'🤔'}[e] || '🧠';
}
function _ptPickEmotion(btnEl, emotion) {
  document.querySelectorAll('.pt-emotion-btn').forEach(b => b.classList.remove('active'));
  btnEl.classList.add('active');
  _ptSelectedEmotion = emotion;
}

// Open the OPEN-POSITION modal — pre-fills from pick
function paperAddPick(symbol, market, entry, stop, target, source, sourceScore, defaultShares) {
  const cur = market === 'TH' ? '฿' : '$';
  _ptCurrencySymbol = cur;
  const symClean = symbol.replace('.BK','');
  const riskPerShare = Math.abs(entry - stop);
  const rewardPerShare = Math.abs(target - entry);
  const rr = rewardPerShare > 0 && riskPerShare > 0 ? (rewardPerShare/riskPerShare).toFixed(2) : '-';
  const acctSize = parseFloat(document.getElementById('settingAccount')?.value || 50000);

  document.getElementById('paperModalContent').innerHTML = `
    <h2 style="margin-bottom:6px;display:flex;align-items:center;gap:8px">
      📝 Open Paper Position
      <span style="background:var(--cyan)22;color:var(--cyan);font-size:.7rem;padding:2px 8px;border-radius:4px;font-weight:600">${source||'manual'}</span>
    </h2>
    <div style="color:var(--muted);font-size:.85rem;margin-bottom:18px">${symClean} • ${market} market${sourceScore?` • score ${sourceScore.toFixed(1)}`:''}</div>

    <div class="pt-grid3">
      <div class="pt-field"><label>Entry</label><input type="number" step="0.01" id="ptEntry" value="${entry.toFixed(2)}"></div>
      <div class="pt-field"><label>Stop (red)</label><input type="number" step="0.01" id="ptStop" value="${stop.toFixed(2)}" style="color:var(--red)"></div>
      <div class="pt-field"><label>Target (green)</label><input type="number" step="0.01" id="ptTarget" value="${target.toFixed(2)}" style="color:var(--green)"></div>
    </div>

    <div class="pt-field"><label>Shares</label><input type="number" id="ptShares" value="${defaultShares||100}" oninput="_ptUpdateSummary()"></div>

    <div class="pt-summary" id="ptSummary"></div>

    <div class="pt-field">
      <label>How do you feel right now? <span style="color:var(--muted);font-weight:400">(optional)</span></label>
      <div class="pt-emotion">${_emotionPills('confident')}</div>
    </div>

    <div class="pt-field">
      <label>Notes <span style="color:var(--muted);font-weight:400">(optional)</span></label>
      <textarea id="ptNotes" rows="2" placeholder="ทำไมถึงเข้าตัวนี้? เห็น signal อะไร?"></textarea>
    </div>

    <div class="pt-actions">
      <button class="pt-btn-secondary" onclick="paperModalClose()">Cancel</button>
      <button class="pt-btn-primary" onclick="_ptSubmitOpen('${symbol}','${market}','${source||''}',${sourceScore||'null'})">✅ Open Position</button>
    </div>
  `;
  paperModalOpen();
  _ptUpdateSummary();
}

function _ptUpdateSummary() {
  const entry = parseFloat(document.getElementById('ptEntry').value) || 0;
  const stop = parseFloat(document.getElementById('ptStop').value) || 0;
  const target = parseFloat(document.getElementById('ptTarget').value) || 0;
  const shares = parseInt(document.getElementById('ptShares').value) || 0;
  const cur = _ptCurrencySymbol;
  const riskPerShare = Math.abs(entry - stop);
  const totalRisk = riskPerShare * shares;
  const totalReward = Math.abs(target - entry) * shares;
  const positionSize = entry * shares;
  const rr = riskPerShare > 0 ? Math.abs(target - entry) / riskPerShare : 0;
  const acctSize = parseFloat(document.getElementById('settingAccount')?.value || 50000);
  const riskPct = acctSize > 0 ? (totalRisk / acctSize * 100) : 0;
  const riskCol = riskPct <= 1 ? 'var(--green)' : riskPct <= 2 ? 'var(--gold)' : 'var(--red)';

  document.getElementById('ptSummary').innerHTML = `
    <div class="pt-summary-row"><span class="lbl">Position size</span><span class="val">${cur}${positionSize.toFixed(2)}</span></div>
    <div class="pt-summary-row"><span class="lbl">Risk per share</span><span class="val">${cur}${riskPerShare.toFixed(2)}</span></div>
    <div class="pt-summary-row"><span class="lbl">Total risk (1R)</span><span class="val" style="color:var(--red)">${cur}${totalRisk.toFixed(2)} (${riskPct.toFixed(2)}% of acct)</span></div>
    <div class="pt-summary-row"><span class="lbl">Total reward</span><span class="val" style="color:var(--green)">${cur}${totalReward.toFixed(2)}</span></div>
    <div class="pt-summary-row"><span class="lbl">Risk:Reward</span><span class="val" style="color:var(--cyan)">1 : ${rr.toFixed(2)}</span></div>
    ${riskPct > 2 ? '<div style="color:var(--red);font-size:.78rem;margin-top:6px">⚠️ Risk > 2% — consider reducing shares</div>' : ''}
  `;
}

async function _ptSubmitOpen(symbol, market, source, sourceScore) {
  const entry = parseFloat(document.getElementById('ptEntry').value);
  const stop = parseFloat(document.getElementById('ptStop').value);
  const target = parseFloat(document.getElementById('ptTarget').value);
  const shares = parseInt(document.getElementById('ptShares').value);
  const notes = document.getElementById('ptNotes').value.trim();
  if (!shares || shares <= 0) { alert('Shares must be > 0'); return; }

  const body = {
    symbol, market, shares, entry, stop, target,
    source: source || null,
    source_score: sourceScore || null,
    emotion: _ptSelectedEmotion || null,
    notes: notes || null
  };
  const r = await fetch('/api/paper/open', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify(body)
  }).then(r=>r.json());
  if (r.error) { alert('Error: ' + r.error); return; }
  paperModalClose();
  paperToast(`✅ Opened #${r.id}: ${symbol.replace('.BK','')} • ${shares} shares • risk ${_ptCurrencySymbol}${r.initial_risk.toFixed(2)}`, 'success');
  paperRefresh();
}

// Open the CLOSE-POSITION modal
function paperClosePrompt(id, sym, suggestedPrice) {
  const cur = currentMarket === 'TH' ? '฿' : '$';
  _ptCurrencySymbol = cur;
  document.getElementById('paperModalContent').innerHTML = `
    <h2 style="margin-bottom:6px">🚪 Close Position</h2>
    <div style="color:var(--muted);font-size:.85rem;margin-bottom:18px">#${id} • ${sym}</div>

    <div class="pt-field">
      <label>Exit Price</label>
      <input type="number" step="0.01" id="ptExitPrice" value="${suggestedPrice.toFixed(2)}">
    </div>

    <div class="pt-field">
      <label>How do you feel about this exit?</label>
      <div class="pt-emotion">${_emotionPills('calm')}</div>
    </div>

    <div class="pt-field">
      <label>Notes <span style="color:var(--muted);font-weight:400">(optional)</span></label>
      <textarea id="ptCloseNotes" rows="3" placeholder="ทำไมถึงปิดตอนนี้? เหตุผลอะไร? ได้บทเรียนอะไร?"></textarea>
    </div>

    <div class="pt-actions">
      <button class="pt-btn-secondary" onclick="paperModalClose()">Cancel</button>
      <button class="pt-btn-danger" onclick="_ptSubmitClose(${id},'${sym}')">🚪 Close Position</button>
    </div>
  `;
  paperModalOpen();
}

async function _ptSubmitClose(id, sym) {
  const exit_price = parseFloat(document.getElementById('ptExitPrice').value);
  const notes = document.getElementById('ptCloseNotes').value.trim();
  if (!exit_price || exit_price <= 0) { alert('Exit price required'); return; }
  const r = await fetch('/api/paper/close', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({id, exit_price, emotion: _ptSelectedEmotion, notes: notes || null})
  }).then(r=>r.json());
  if (r.error) { alert('Error: ' + r.error); return; }
  paperModalClose();
  const rmult = r.realized_r || 0;
  const tone = rmult > 0 ? 'success' : rmult < 0 ? 'error' : 'info';
  const emoji = rmult > 0 ? '🎉' : rmult < 0 ? '😬' : '😐';
  paperToast(`${emoji} Closed ${sym.replace('.BK','')}: ${rmult.toFixed(2)}R • P/L ${_ptCurrencySymbol}${(r.realized_pnl||0).toFixed(0)}`, tone);
  paperRefresh();
}

// Journal modal
function paperJournalPrompt(id, sym) {
  document.getElementById('paperModalContent').innerHTML = `
    <h2 style="margin-bottom:6px">📖 Journal Entry</h2>
    <div style="color:var(--muted);font-size:.85rem;margin-bottom:18px">#${id} • ${sym}</div>

    <div class="pt-field">
      <label>How do you feel?</label>
      <div class="pt-emotion">${_emotionPills(null)}</div>
    </div>

    <div class="pt-field">
      <label>What's on your mind?</label>
      <textarea id="ptJournalText" rows="4" placeholder="วันนี้ตลาดเป็นไง? รู้สึกอยากปิดไหม? อะไรทำให้เครียด/มั่นใจ?" autofocus></textarea>
    </div>

    <div class="pt-actions">
      <button class="pt-btn-secondary" onclick="paperModalClose()">Cancel</button>
      <button class="pt-btn-primary" onclick="_ptSubmitJournal(${id},'${sym}')">📝 Save</button>
    </div>
  `;
  paperModalOpen();
}

async function _ptSubmitJournal(id, sym) {
  const text = document.getElementById('ptJournalText').value.trim();
  if (!text) { alert('Journal text required'); return; }
  const r = await fetch('/api/paper/journal', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({id, text, emotion: _ptSelectedEmotion})
  }).then(r=>r.json());
  if (r.error) { alert('Error: ' + r.error); return; }
  paperModalClose();
  paperToast(`📝 Journal saved for ${sym.replace('.BK','')}`, 'info');
  paperRefresh();
}

// Toast notifications (non-blocking)
function paperToast(msg, tone) {
  const colors = {success:'var(--green)', error:'var(--red)', info:'var(--cyan)'};
  const t = document.createElement('div');
  t.style.cssText = `position:fixed;top:24px;right:24px;background:var(--bg2);border:1px solid ${colors[tone]||'var(--border)'};border-left:4px solid ${colors[tone]||'var(--cyan)'};border-radius:8px;padding:14px 20px;color:var(--text);font-size:.9rem;font-weight:500;z-index:200;box-shadow:0 10px 30px rgba(0,0,0,.5);max-width:400px;animation:slideIn .25s ease-out`;
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => { t.style.opacity = '0'; t.style.transition = 'opacity .3s'; setTimeout(() => t.remove(), 300); }, 3500);
}

function setDashboardTab(tab) {
  CURRENT_DASHBOARD_TAB = tab;
  const main = document.getElementById('mainDashboard');
  const decisions = document.getElementById('tradeDecisionsDashboard');
  const edge = document.getElementById('edgeLabDashboard');
  const results = document.getElementById('signalResultsDashboard');
  const mainTab = document.getElementById('tab-main');
  const decisionsTab = document.getElementById('tab-decisions');
  const edgeTab = document.getElementById('tab-edge');
  const resultsTab = document.getElementById('tab-results');
  const isMain = tab === 'main';
  const isDecisions = tab === 'decisions';
  const isEdge = tab === 'edge';
  const isResults = tab === 'results';
  if (main) main.style.display = isMain ? '' : 'none';
  if (decisions) decisions.style.display = isDecisions ? '' : 'none';
  if (edge) edge.style.display = isEdge ? '' : 'none';
  if (results) results.style.display = isResults ? '' : 'none';
  if (mainTab) {
    mainTab.classList.toggle('active', isMain);
    mainTab.setAttribute('aria-selected', String(isMain));
  }
  if (decisionsTab) {
    decisionsTab.classList.toggle('active', isDecisions);
    decisionsTab.setAttribute('aria-selected', String(isDecisions));
  }
  if (edgeTab) {
    edgeTab.classList.toggle('active', isEdge);
    edgeTab.setAttribute('aria-selected', String(isEdge));
  }
  if (resultsTab) {
    resultsTab.classList.toggle('active', isResults);
    resultsTab.setAttribute('aria-selected', String(isResults));
  }
  localStorage.setItem('dashboardTab', tab);
  if (isDecisions) loadTradeDecisions();
  if (isEdge) loadEdgeLab();
  if (isResults) loadSignalResults();
}

function _srEscape(v) {
  return String(v ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function _srPct(v) {
  if (v === null || v === undefined || Number.isNaN(Number(v))) return '--';
  return `${(Number(v) * 100).toFixed(0)}%`;
}

function _srSignedPct(v) {
  if (v === null || v === undefined || Number.isNaN(Number(v))) return '--';
  const n = Number(v) * 100;
  const sign = n > 0 ? '+' : '';
  return `${sign}${n.toFixed(1)}%`;
}

function _srR(v) {
  if (v === null || v === undefined || Number.isNaN(Number(v))) return '--';
  const n = Number(v);
  const sign = n > 0 ? '+' : '';
  return `${sign}${n.toFixed(2)}R`;
}

function _srNum(v) {
  if (v === null || v === undefined || Number.isNaN(Number(v))) return '--';
  return Number(v).toLocaleString();
}

function _srStageLabel(stage) {
  const labels = {
    validated: 'Validated',
    calibrating: 'Calibrating',
    collecting: 'Collecting',
    needs_outcomes: 'Needs Outcomes',
    not_started: 'Not Started',
  };
  const safeStage = _srEscape(stage || 'not_started');
  return `<span class="signal-stage-pill signal-stage-${safeStage}">${labels[stage] || safeStage}</span>`;
}

function _srPriorityLabel(priority) {
  const safe = _srEscape(priority || 'P2');
  return `<span class="signal-priority-pill signal-priority-${safe}">${safe}</span>`;
}

function _srStatusLabel(status) {
  const safe = _srEscape(status || 'unknown');
  const label = {
    fresh: 'Fresh',
    aging: 'Aging',
    stale: 'Stale',
    missing: 'Missing',
    ok: 'OK',
    attention: 'Attention',
  }[status] || safe;
  return `<span class="signal-status-pill signal-status-${safe}">${label}</span>`;
}

function _srSetText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

async function loadEdgeLab() {
  const readiness = document.getElementById('edgeReadinessText');
  if (readiness) readiness.textContent = 'Loading edge diagnostics...';
  try {
    const market = encodeURIComponent(currentMarket || '');
    const [signalRes, tradesRes] = await Promise.all([
      fetch(`/api/signal-results?market=${market}`),
      fetch(`/api/paper/list?status=all&market=${market}`),
    ]);
    const signalData = await signalRes.json();
    const tradesData = await tradesRes.json();
    if (!signalRes.ok || signalData.error) throw new Error(signalData.error || `HTTP ${signalRes.status}`);
    if (!tradesRes.ok || tradesData.error) throw new Error(tradesData.error || `HTTP ${tradesRes.status}`);
    renderEdgeLab(signalData, Array.isArray(tradesData) ? tradesData : (tradesData.value || []));
  } catch (e) {
    console.error('edge lab failed', e);
    if (readiness) readiness.textContent = `Could not load Edge Lab: ${e.message}`;
  }
}

function _edgeMoney(v) {
  if (v === null || v === undefined || Number.isNaN(Number(v))) return '--';
  const n = Number(v);
  const sign = n > 0 ? '+' : n < 0 ? '-' : '';
  const currency = currentMarket === 'TH' ? 'THB ' : '$';
  return `${sign}${currency}${Math.abs(n).toLocaleString(undefined, {maximumFractionDigits: 0})}`;
}

function _edgeSourceName(source) {
  const names = {
    'thai-swing-dip': 'Thai Swing Dip',
    'thai-swing-momentum': 'Thai Swing Momentum',
    'vcp-screener': 'VCP',
    vcp: 'VCP',
    'canslim-screener': 'CANSLIM',
  };
  return names[source] || source || '--';
}

function _edgeConfidence(closed, paper) {
  if (closed >= 30) return {label: 'Stat-ready', cls: 'edge-confidence-ready'};
  if (closed >= 10) return {label: 'Calibrating', cls: 'edge-confidence-calibrating'};
  if (closed > 0) return {label: 'Early sample', cls: 'edge-confidence-early'};
  if (paper > 0) return {label: 'Waiting exits', cls: 'edge-confidence-waiting'};
  return {label: 'No paper yet', cls: 'edge-confidence-empty'};
}

function _edgeConfidencePill(closed, paper) {
  const c = _edgeConfidence(Number(closed) || 0, Number(paper) || 0);
  return `<span class="edge-confidence-pill ${c.cls}">${c.label}</span>`;
}

function _edgeSourceAction(r) {
  const source = String(r.source || '');
  const closed = Number(r.closed_trades || 0);
  const paper = Number(r.paper_trades || 0);
  const expectancy = Number(r.expectancy_r);
  if (paper === 0 && source.includes('vcp')) {
    return 'Keep VCP gate strict. Track 60-69 near-misses first; do not relax live auto-open until at least 10 paper outcomes exist.';
  }
  if (paper === 0 && source.includes('canslim')) {
    return 'Start with paper-only tracking for top scores. Fundamentals are useful, but the entry timing still needs outcome proof.';
  }
  if (closed === 0) return 'Do not tune yet. Wait for exits so win rate and R-multiple become real evidence.';
  if (closed < 10) return 'Collect more outcomes. Treat win rate and expectancy as directional only.';
  if (Number.isFinite(expectancy) && expectancy < 0) return 'Tighten this source: raise score gate, require better market regime, or reduce size.';
  if (Number.isFinite(expectancy) && expectancy > 0.5) return 'Promising. Test a slightly higher quota, but keep max risk per trade unchanged.';
  return 'Keep collecting and compare by score bucket before changing the rule.';
}

function _edgeBucketRead(bucket, stats) {
  const closed = Number(stats.closed_trades || 0);
  const expectancy = Number(stats.expectancy_r);
  if (closed === 0) return 'No exits yet';
  if (closed < 10) return 'Early read only';
  if (Number.isFinite(expectancy) && expectancy > 0.4) return 'Promising band';
  if (Number.isFinite(expectancy) && expectancy < 0) return 'Needs tighter gate';
  return 'Neutral';
}

function renderEdgeLab(data, trades) {
  const sources = data.source_readiness || [];
  const paper = data.paper || {};
  const openTrades = (trades || []).filter(t => (t.status || 'open') === 'open');
  const closedTrades = (trades || []).filter(t => (t.status || 'open') !== 'open');
  const openRisk = openTrades.reduce((sum, t) => sum + (Number(t.initial_risk) || 0), 0);
  const sourcesWithPaper = sources.filter(s => Number(s.paper_trades || 0) > 0).length;
  const bestSource = sources
    .filter(s => Number(s.closed_trades || 0) > 0 || Number.isFinite(Number(s.expectancy_r)))
    .sort((a, b) => (Number(b.expectancy_r) || -99) - (Number(a.expectancy_r) || -99))[0];
  const vcpRows = data.vcp_near_misses?.near_misses || [];
  const topVcp = vcpRows
    .slice()
    .sort((a, b) => (Number(b.composite_score) || -1) - (Number(a.composite_score) || -1))[0];
  const funnel = data.vcp_near_misses?.funnel || {};
  const analyzed = Number(funnel.analyzed || funnel.trend_template_passed || 0);
  const vcpCandidates = Number(funnel.vcp_candidates || 0);
  const gatePct = analyzed > 0 ? Math.round((vcpCandidates / analyzed) * 100) : null;
  const closedSample = Math.max(Number(paper.closed_trades || 0), closedTrades.length);

  _srSetText('edgeSourcesWithPaper', `${sourcesWithPaper}/${sources.length || 0}`);
  _srSetText('edgeOpenRisk', _edgeMoney(openRisk));
  _srSetText('edgeClosedSample', `${closedSample}/30`);
  _srSetText('edgeBestSource', bestSource ? _edgeSourceName(bestSource.source) : '--');
  _srSetText('edgeVcpTop', topVcp ? Number(topVcp.composite_score || 0).toFixed(1) : '--');
  _srSetText('edgeGateProgress', gatePct === null ? '--' : `${gatePct}%`);
  _srSetText('edgeAsOf', `as of ${data.as_of || '--'} | ${data.market || currentMarket}`);

  const readiness = closedSample === 0
    ? 'The system is collecting candidates, but there are not enough exits to tune rules from statistics yet.'
    : closedSample < 10
      ? 'There are early outcomes now. Use this page as a warning panel, not a final proof of edge.'
      : closedSample < 30
        ? 'The system is in calibration mode. Source and score-band comparisons are becoming useful.'
        : 'The sample is large enough for first-pass rule tuning. Focus on expectancy by source and score band.';
  _srSetText('edgeReadinessText', readiness);

  renderEdgeSourceRows(sources);
  renderEdgeScoreBuckets(paper.by_score_bucket || {});
  renderEdgeVcpGate(data.vcp_near_misses || {});
  renderEdgeRiskBudget(openTrades, trades || [], paper);
  renderEdgeRuleTests(data, openTrades, closedSample);
}

function renderEdgeSourceRows(rows) {
  const body = document.getElementById('edgeSourceRows');
  if (!body) return;
  if (!rows.length) {
    body.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--muted);padding:28px">No source diagnostics yet.</td></tr>';
    return;
  }
  body.innerHTML = rows.map(r => {
    const exp = r.expectancy_r === null || r.expectancy_r === undefined ? null : Number(r.expectancy_r);
    const expText = exp === null ? _srSignedPct(r.horizons?.['5']?.avg_return_pct) : _srR(exp);
    const expColor = (exp || r.horizons?.['5']?.avg_return_pct || 0) >= 0 ? 'var(--green)' : 'var(--red)';
    return `
      <tr>
        <td><strong style="color:var(--text)">${_srEscape(_edgeSourceName(r.source))}</strong><div class="signal-mini-path">${_srEscape(r.source)}</div></td>
        <td>${_srNum(r.signals)}</td>
        <td>${_srNum(r.paper_trades)}</td>
        <td>${_srNum(r.closed_trades)}</td>
        <td>${_srPct(r.win_rate)}</td>
        <td style="color:${expColor}">${expText}</td>
        <td>${_edgeConfidencePill(r.closed_trades, r.paper_trades)}</td>
        <td style="min-width:240px;color:var(--muted)">${_srEscape(_edgeSourceAction(r))}</td>
      </tr>
    `;
  }).join('');
}

function renderEdgeScoreBuckets(buckets) {
  const body = document.getElementById('edgeScoreBucketRows');
  if (!body) return;
  const order = ['>=85', '70-84', '50-69', '<50'];
  const entries = Object.entries(buckets || {}).sort((a, b) => {
    const ia = order.indexOf(a[0]);
    const ib = order.indexOf(b[0]);
    return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
  });
  if (!entries.length) {
    body.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--muted);padding:28px">No score buckets yet.</td></tr>';
    return;
  }
  body.innerHTML = entries.map(([bucket, s]) => {
    const exp = Number(s.expectancy_r);
    const expColor = (Number.isFinite(exp) ? exp : 0) >= 0 ? 'var(--green)' : 'var(--red)';
    return `
      <tr>
        <td><strong style="color:var(--text)">${_srEscape(bucket)}</strong></td>
        <td>${_srNum(s.total_trades)}</td>
        <td>${_srNum(s.open_positions)}</td>
        <td>${_srNum(s.closed_trades)}</td>
        <td>${s.avg_source_score === null || s.avg_source_score === undefined ? '--' : Number(s.avg_source_score).toFixed(1)}</td>
        <td>${_srPct(s.win_rate)}</td>
        <td style="color:${expColor}">${_srR(s.expectancy_r)}</td>
        <td>${_srEscape(_edgeBucketRead(bucket, s))}</td>
      </tr>
    `;
  }).join('');
}

function renderEdgeVcpGate(vcp) {
  const el = document.getElementById('edgeVcpGateContent');
  if (!el) return;
  const funnel = vcp.funnel || {};
  const rows = vcp.near_misses || [];
  const top = rows[0];
  const topNote = top
    ? `${_srEscape(top.symbol)} scored ${Number(top.composite_score || 0).toFixed(1)}. It missed because ${(top.reasons || ['gate not passed']).map(_srEscape).join('; ')}.`
    : 'No VCP near-miss detail is available yet.';
  const nearRows = rows.slice(0, 4).map(r => `
    <div class="edge-near-row">
      <div><strong>${_srEscape(r.symbol || '--')}</strong><div class="signal-mini-path">${(r.reasons || []).map(_srEscape).join('; ') || 'No reason recorded'}</div></div>
      <div class="edge-near-score">${r.composite_score === null || r.composite_score === undefined ? '--' : Number(r.composite_score).toFixed(1)}</div>
    </div>
  `).join('');
  el.innerHTML = `
    <div class="signal-mini-grid edge-four-grid">
      <div><span>Universe</span><strong>${_srNum(funnel.universe)}</strong></div>
      <div><span>Trend pass</span><strong>${_srNum(funnel.trend_template_passed)}</strong></div>
      <div><span>Analyzed</span><strong>${_srNum(funnel.analyzed)}</strong></div>
      <div><span>VCP candidates</span><strong>${_srNum(funnel.vcp_candidates)}</strong></div>
    </div>
    <div class="edge-callout">${topNote}</div>
    <div class="edge-near-list">${nearRows || '<div class="signal-note">No near misses in latest report.</div>'}</div>
  `;
}

function renderEdgeRiskBudget(openTrades, allTrades, paper) {
  const el = document.getElementById('edgeRiskBudgetContent');
  if (!el) return;
  const openRisk = openTrades.reduce((sum, t) => sum + (Number(t.initial_risk) || 0), 0);
  const bySource = {};
  const bySymbol = {};
  openTrades.forEach(t => {
    const source = t.source || 'unknown';
    const symbol = t.symbol || 'UNKNOWN';
    bySource[source] = (bySource[source] || 0) + 1;
    bySymbol[symbol] = (bySymbol[symbol] || 0) + 1;
  });
  const sourceRows = Object.entries(bySource)
    .sort((a, b) => b[1] - a[1])
    .map(([source, count]) => `<div class="edge-pair"><span>${_srEscape(_edgeSourceName(source))}</span><strong>${count}</strong></div>`)
    .join('');
  const duplicateSymbols = Object.entries(bySymbol).filter(([, count]) => count > 1);
  const guard = openTrades.length >= 10
    ? 'Risk guard: many open tickets. Pause lower-confidence entries until exits free capacity.'
    : openTrades.length >= 5
      ? 'Risk guard: capacity is moderate. Prefer only the highest score entries.'
      : 'Risk guard: capacity is available, but keep position size unchanged until more closed samples exist.';
  el.innerHTML = `
    <div class="edge-pair"><span>Open positions</span><strong>${_srNum(openTrades.length)}</strong></div>
    <div class="edge-pair"><span>Open initial risk</span><strong>${_edgeMoney(openRisk)}</strong></div>
    <div class="edge-pair"><span>Unrealized P/L</span><strong>${_edgeMoney(paper.total_unrealized_pnl || 0)}</strong></div>
    <div class="edge-pair"><span>Duplicate symbols</span><strong>${_srNum(duplicateSymbols.length)}</strong></div>
    <div class="edge-divider"></div>
    ${sourceRows || '<div class="signal-note">No open source concentration.</div>'}
    <div class="edge-callout">${_srEscape(guard)}</div>
  `;
}

function renderEdgeRuleTests(data, openTrades, closedSample) {
  const el = document.getElementById('edgeRuleTestsContent');
  if (!el) return;
  const sources = data.source_readiness || [];
  const vcpRows = data.vcp_near_misses?.near_misses || [];
  const topVcp = vcpRows[0];
  const tests = [];
  if (closedSample < 30) {
    tests.push('Keep all rule changes in paper mode until the system reaches 30 closed outcomes.');
  }
  if (topVcp && Number(topVcp.composite_score || 0) < 70) {
    tests.push(`Create a VCP watch band for 60-69 scores. Do not auto-open it yet; compare its next 5-10 day return first.`);
  }
  sources
    .filter(s => Number(s.paper_trades || 0) > 0 && Number(s.closed_trades || 0) === 0)
    .slice(0, 2)
    .forEach(s => tests.push(`${_edgeSourceName(s.source)} has open paper trades but no exits. Wait for outcomes before raising quota.`));
  const weak = sources.find(s => Number(s.closed_trades || 0) >= 10 && Number(s.expectancy_r) < 0);
  if (weak) tests.push(`${_edgeSourceName(weak.source)} has negative expectancy. Test a higher score gate and smaller size.`);
  if (openTrades.length >= 10) tests.push('Add a portfolio cap: stop new auto-paper entries when open tickets reach 10 unless score is 85+.');
  if (!tests.length) tests.push('Next best improvement: record richer entry context, especially market regime, source gate snapshot, and volume at entry.');
  el.innerHTML = `<ol class="edge-rule-list">${tests.map(t => `<li>${_srEscape(t)}</li>`).join('')}</ol>`;
}

async function loadSignalResults() {
  const readiness = document.getElementById('signalReadinessText');
  if (readiness) readiness.textContent = 'Loading signal outcome status...';
  try {
    const res = await fetch(`/api/signal-results?market=${encodeURIComponent(currentMarket)}`);
    const data = await res.json();
    if (!res.ok || data.error) throw new Error(data.error || `HTTP ${res.status}`);
    renderSignalResults(data);
  } catch (e) {
    console.error('signal results failed', e);
    if (readiness) readiness.textContent = `โหลด Signal Results ไม่สำเร็จ: ${e.message}`;
  }
}

function renderSignalResults(data) {
  const paper = data.paper || {};
  const theses = data.theses || {};
  const completedSignals = data.signals?.completed_signals || 0;
  const closed = Math.max(paper.closed_trades || 0, completedSignals);
  const totalSignals = Math.max(data.signals?.count || 0, theses.total || 0);
  const enoughForCalibration = closed >= 30;
  const firstSource = (data.source_readiness || []).find(r => r.completed_outcomes > 0);
  const first5d = firstSource?.horizons?.['5'];
  const expectancyText = paper.closed_trades
    ? _srR(paper.expectancy_r)
    : first5d
      ? `${_srSignedPct(first5d.avg_return_pct)} 5D`
      : _srR(paper.expectancy_r);

  _srSetText('srSignals', _srNum(totalSignals));
  _srSetText('srOpenPaper', _srNum(paper.open_positions || 0));
  _srSetText('srClosed', _srNum(closed));
  _srSetText('srExpectancy', expectancyText);
  _srSetText('srPostmortems', _srNum(data.postmortems?.count || 0));
  _srSetText('signalAsOf', `as of ${data.as_of || '--'} | ${data.market || currentMarket}`);

  const readiness = closed === 0
    ? 'ยังอยู่ช่วงเริ่มเก็บผล: มี candidates แล้ว แต่ยังไม่มี closed outcome สำหรับสรุปความแม่น'
    : enoughForCalibration
      ? 'มี sample เริ่มพอสำหรับ calibration ราย source แล้ว'
      : 'มีผลลัพธ์บางส่วนแล้ว แต่ sample ยังน้อย ควรใช้เป็น warning ก่อน';
  _srSetText('signalReadinessText', readiness);

  renderSignalMaturity(data);
  renderSignalRecommendations(data.recommendations || []);
  renderSignalCoverage(data);
  renderSignalFreshness(data.freshness || {});
  renderVcpNearMiss(data.vcp_near_misses || {});
  renderAutoPaperGate(data.auto_paper || {});
  renderSignalSourceRows(data.source_readiness || []);
  renderSignalThesisRows(theses.recent || []);
}

function renderSignalMaturity(data) {
  const paper = data.paper || {};
  const completedSignals = data.signals?.completed_signals || 0;
  const closed = Math.max(paper.closed_trades || 0, completedSignals);
  const target = 30;
  const pct = Math.max(0, Math.min(100, (closed / target) * 100));
  const firstSource = (data.source_readiness || []).find(r => r.completed_outcomes > 0);
  const first5d = firstSource?.horizons?.['5'];
  const html = `
    <div style="margin-bottom:10px;color:var(--text);font-weight:800">${closed}/${target} closed outcomes for first calibration gate</div>
    <div class="progress-container" style="margin-bottom:10px"><div class="progress-bar" style="width:${pct}%;background:${closed >= target ? 'var(--green)' : 'var(--gold)'}"></div></div>
    <div>Win rate: <strong style="color:var(--text)">${paper.closed_trades ? _srPct(paper.win_rate) : _srPct(first5d?.win_rate)}</strong></div>
    <div>Avg return: <strong style="color:var(--text)">${_srSignedPct(first5d?.avg_return_pct)} 5D</strong></div>
    <div>Avg win/loss: <strong style="color:var(--green)">${_srR(paper.avg_win_r)}</strong> / <strong style="color:var(--red)">${_srR(paper.avg_loss_r)}</strong></div>
    <div>Total realized: <strong style="color:var(--text)">${_srR(paper.total_realized_r)}</strong></div>
  `;
  const el = document.getElementById('signalMaturityContent');
  if (el) el.innerHTML = html;
}

function renderSignalRecommendations(items) {
  const el = document.getElementById('signalRecommendations');
  if (!el) return;
  if (!items.length) {
    el.innerHTML = '<div style="color:var(--green);font-weight:800">ยังไม่มี issue สำคัญจากข้อมูลปัจจุบัน</div>';
    return;
  }
  el.innerHTML = items.map(item => `
    <div class="signal-rec">
      <div class="signal-rec-title">${_srPriorityLabel(item.priority)} <span>${_srEscape(item.title)}</span></div>
      <p>${_srEscape(item.why)}</p>
      <p style="color:var(--text)">${_srEscape(item.action)}</p>
    </div>
  `).join('');
}

function renderSignalCoverage(data) {
  const theses = data.theses || {};
  const statusRows = Object.entries(theses.by_status || {})
    .map(([k, v]) => `<div style="display:flex;justify-content:space-between;gap:12px"><span>${_srEscape(k)}</span><strong style="color:var(--text)">${_srNum(v)}</strong></div>`)
    .join('');
  const feedbackRows = (data.feedback_files || []).slice(0, 4)
    .map(f => `<div style="font-size:.78rem;color:var(--muted);margin-top:6px">${_srEscape(f.name)}</div>`)
    .join('');
  const html = `
    <div style="display:grid;gap:7px;margin-bottom:12px">
      <div style="display:flex;justify-content:space-between;gap:12px"><span>Signal files</span><strong style="color:var(--text)">${_srNum(data.signals?.count || 0)}</strong></div>
      <div style="display:flex;justify-content:space-between;gap:12px"><span>Theses</span><strong style="color:var(--text)">${_srNum(theses.total || 0)}</strong></div>
      <div style="display:flex;justify-content:space-between;gap:12px"><span>Postmortems</span><strong style="color:var(--text)">${_srNum(data.postmortems?.count || 0)}</strong></div>
      <div style="display:flex;justify-content:space-between;gap:12px"><span>Auto-paper eligible</span><strong style="color:var(--text)">${_srNum(data.auto_paper?.eligible || 0)}</strong></div>
      ${statusRows}
    </div>
    <div style="border-top:1px solid var(--border);padding-top:10px">
      <strong style="color:var(--text);font-size:.8rem">Recent feedback files</strong>
      ${feedbackRows || '<div style="font-size:.78rem;color:var(--muted);margin-top:6px">No feedback files yet</div>'}
    </div>
  `;
  const el = document.getElementById('signalCoverageContent');
  if (el) el.innerHTML = html;
}

function renderSignalFreshness(freshness) {
  const el = document.getElementById('signalFreshnessContent');
  if (!el) return;
  const reports = freshness.reports || [];
  if (!reports.length) {
    el.innerHTML = '<div style="color:var(--muted)">No report inventory yet</div>';
    return;
  }
  const rows = reports.map(r => {
    const age = r.age_hours === null || r.age_hours === undefined ? '--' : `${Number(r.age_hours).toFixed(1)}h`;
    const path = r.path ? `<div class="signal-mini-path">${_srEscape(r.path)}</div>` : '';
    return `
      <div class="signal-diagnostic-row">
        <div>
          <strong>${_srEscape(r.label)}</strong>
          ${path}
        </div>
        <div style="text-align:right">
          ${_srStatusLabel(r.status)}
          <div class="signal-mini-path">${age}</div>
        </div>
      </div>
    `;
  }).join('');
  el.innerHTML = `
    <div style="margin-bottom:10px">${_srStatusLabel(freshness.overall_status || 'ok')} <span style="margin-left:6px">Market ${_srEscape(freshness.market || currentMarket)}</span></div>
    <div class="signal-diagnostic-list">${rows}</div>
  `;
}

function renderVcpNearMiss(vcp) {
  const el = document.getElementById('vcpNearMissContent');
  if (!el) return;
  const funnel = vcp.funnel || {};
  const rows = vcp.near_misses || [];
  const note = (vcp.notes || []).map(n => `<div class="signal-note">${_srEscape(n)}</div>`).join('');
  const funnelHtml = `
    <div class="signal-mini-grid">
      <div><span>Pre-filter</span><strong>${_srNum(funnel.pre_filter_passed)}</strong></div>
      <div><span>Trend</span><strong>${_srNum(funnel.trend_template_passed)}</strong></div>
      <div><span>VCP</span><strong>${_srNum(funnel.vcp_candidates)}</strong></div>
    </div>
  `;
  if (!rows.length) {
    el.innerHTML = `${funnelHtml}${note || '<div class="signal-note">No near-miss details in the latest VCP report yet.</div>'}`;
    return;
  }
  const tableRows = rows.slice(0, 6).map(r => `
    <tr>
      <td><strong style="color:var(--text)">${_srEscape(r.symbol || '--')}</strong></td>
      <td>${r.composite_score === null || r.composite_score === undefined ? '--' : Number(r.composite_score).toFixed(1)}</td>
      <td>${r.distance_from_pivot_pct === null || r.distance_from_pivot_pct === undefined ? '--' : `${Number(r.distance_from_pivot_pct).toFixed(1)}%`}</td>
      <td>${(r.reasons || []).map(_srEscape).join('; ')}</td>
    </tr>
  `).join('');
  el.innerHTML = `
    ${funnelHtml}
    ${note}
    <div style="overflow-x:auto;margin-top:10px">
      <table class="signal-table signal-near-table">
        <thead><tr><th>Symbol</th><th>Score</th><th>Dist</th><th>Why missed</th></tr></thead>
        <tbody>${tableRows}</tbody>
      </table>
    </div>
  `;
}

function renderAutoPaperGate(autoPaper) {
  const el = document.getElementById('autoPaperGateContent');
  if (!el) return;
  const diag = autoPaper.diagnostics || {};
  const config = autoPaper.config || {};
  const replacement = autoPaper.replacement_review || {};
  const selected = diag.selected || autoPaper.candidates || [];
  const skipped = diag.skipped || [];
  const selectedRows = selected.slice(0, 3).map(r => `
    <div class="signal-diagnostic-row">
      <div><strong>${_srEscape(r.symbol)}</strong><div class="signal-mini-path">${_srEscape(r.source_skill)} · score ${r.raw_score ?? '--'}</div></div>
      <div style="text-align:right"><strong style="color:var(--text)">${r.entry ?? '--'}</strong><div class="signal-mini-path">entry</div></div>
    </div>
  `).join('');
  const skippedRows = skipped.slice(0, 4).map(r => `
    <div class="signal-diagnostic-row">
      <div><strong>${_srEscape(r.symbol)}</strong><div class="signal-mini-path">${_srEscape(r.source_skill)} · score ${r.raw_score ?? '--'}</div></div>
      <div style="text-align:right;color:var(--muted)">${(r.reasons || []).map(_srEscape).join('; ')}</div>
    </div>
  `).join('');
  const replacementRows = (replacement.proposals || []).map(p => `
    <div class="signal-diagnostic-row">
      <div><strong>${_srEscape(p.candidate?.symbol || '--')}</strong><div class="signal-mini-path">score ${p.candidate?.raw_score ?? '--'} | blocked by capacity</div></div>
      <div style="text-align:right"><strong style="color:var(--gold)">Review ${_srEscape(p.review_position?.symbol || '--')}</strong><div class="signal-mini-path">score ${p.review_position?.source_score ?? '--'} | ${Number(p.review_position?.unrealized_r || 0).toFixed(2)}R</div></div>
    </div>
  `).join('');
  el.innerHTML = `
    <div class="signal-mini-grid">
      <div><span>Eligible</span><strong>${_srNum(autoPaper.eligible || 0)}</strong></div>
      <div><span>Gate pass</span><strong>${_srNum(diag.passed_before_position_limit || selected.length)}</strong></div>
      <div><span>New / Open cap</span><strong>${_srNum(config.max_new_positions)} / ${_srNum(config.max_open_positions)}</strong></div>
    </div>
    <div class="signal-note">Risk sizing: ${_srNum(config.risk_per_trade_pct)}% per trade | max position ${_srNum(config.max_position_pct)}% | portfolio heat ${_srNum(config.max_portfolio_heat_pct)}%.</div>
    <div class="signal-note">High-score override: score ${_srNum(config.high_score_override_min)}+ can expand open cap to ${_srNum(config.max_open_positions_with_override)}.</div>
    <div style="margin-top:10px"><strong style="color:var(--text);font-size:.8rem">Selected</strong>${selectedRows || '<div class="signal-note">No selected auto-paper candidates.</div>'}</div>
    <div style="margin-top:12px"><strong style="color:var(--text);font-size:.8rem">Replacement Review</strong>${replacementRows || '<div class="signal-note">No replacement review is required. This panel never closes a position automatically.</div>'}</div>
    <div style="margin-top:12px"><strong style="color:var(--text);font-size:.8rem">Skipped</strong>${skippedRows || '<div class="signal-note">No skipped rows in the diagnostic window.</div>'}</div>
  `;
}

function renderSignalSourceRows(rows) {
  const body = document.getElementById('signalSourceRows');
  if (!body) return;
  if (!rows.length) {
    body.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--muted);padding:28px">ยังไม่มี source ให้ประเมิน</td></tr>';
    return;
  }
  body.innerHTML = rows.map(r => `
    <tr>
      <td><strong style="color:var(--text)">${_srEscape(r.source)}</strong></td>
      <td>${_srNum(r.signals)}</td>
      <td>${_srNum(r.paper_trades)}</td>
      <td>${_srNum(r.closed_trades)}</td>
      <td>${_srPct(r.win_rate)}</td>
      <td style="color:${(r.expectancy_r || r.horizons?.['5']?.avg_return_pct || 0) >= 0 ? 'var(--green)' : 'var(--red)'}">${r.expectancy_r === null || r.expectancy_r === undefined ? _srSignedPct(r.horizons?.['5']?.avg_return_pct) : _srR(r.expectancy_r)}</td>
      <td>${_srStageLabel(r.stage)}</td>
      <td style="min-width:220px;color:var(--muted)">${_srEscape(r.guidance)}</td>
    </tr>
  `).join('');
}

function renderSignalThesisRows(rows) {
  const body = document.getElementById('signalThesisRows');
  if (!body) return;
  if (!rows.length) {
    body.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--muted);padding:28px">ยังไม่มี thesis candidates</td></tr>';
    return;
  }
  body.innerHTML = rows.map(r => `
    <tr>
      <td><strong style="color:var(--text)">${_srEscape(r.ticker || '--')}</strong></td>
      <td>${_srEscape(r.source || '--')}</td>
      <td>${_srStageLabel((r.status || 'UNKNOWN').toLowerCase() === 'idea' ? 'needs_outcomes' : 'collecting')} <span style="margin-left:6px">${_srEscape(r.status || '--')}</span></td>
      <td>${r.score === null || r.score === undefined ? '--' : Number(r.score).toFixed(1)}</td>
      <td>${_srEscape(r.grade || '--')}</td>
      <td>${_srEscape(r.next_review_date || '--')}</td>
    </tr>
  `).join('');
}

window.onload = async () => {
  loadSettings();
  // Sync market toggle button visual state with loaded currentMarket
  document.querySelectorAll('.mkt-btn').forEach(b => b.classList.remove('active'));
  const activeBtn = document.getElementById('mkt-' + currentMarket);
  if (activeBtn) activeBtn.classList.add('active');
  initTradingGuide();

  // Pre-fetch benchmark data for the market
  await fetchBenchmarkData(currentMarket);

  await refreshHistoryList();
  await loadData();
  await paperRefresh();
  const savedTab = localStorage.getItem('dashboardTab') || 'main';
  if (savedTab === 'results' || savedTab === 'decisions' || savedTab === 'edge') setDashboardTab(savedTab);
  else loadSignalResults();
};

async function openPatternScreener() {
  document.getElementById('patternScreenerModal').classList.add('open');
  const content = document.getElementById('patternScreenerContent');
  content.innerHTML = 'กำลังโหลดและวิเคราะห์สถิติจาก /api/patterns...';
  try {
    const res = await fetch('/api/patterns');
    const data = await res.json();
    if (data.error) {
      content.innerHTML = `<span style="color:var(--red)">Error: ${data.error}</span>`;
      return;
    }

    let html = '<div style="max-height:70vh; overflow-y:auto; padding-right:8px;">';
    const categories = [
      { key: 'Oversold', title: '🟢 Oversold (ลุ้นเด้งหลังราคาลงติดกัน)', color: 'var(--green)' },
      { key: 'Overbought', title: '🔴 Overbought (ระวังย่อหลังราคาพุ่งติดกัน)', color: 'var(--red)' }
    ];

    categories.forEach(c => {
      const items = data[c.key] || [];
      // Sort by consecutive days descending, then win_rate descending
      items.sort((a, b) => b.consecutive - a.consecutive || b.win_rate - a.win_rate);

      html += `<h3 style="color:${c.color};margin-top:16px;margin-bottom:8px">${c.title} (${items.length} หุ้น)</h3>`;
      if (items.length === 0) {
        html += '<div style="color:var(--muted)">ไม่มีหุ้นที่เข้าเงื่อนไข (Win Rate > 50%)</div>';
      } else {
        html += `<table class="table" style="width:100%; font-size:0.9em; text-align:right;">
          <thead>
            <tr>
              <th style="text-align:left">Symbol</th>
              <th title="จำนวนวันที่เกิดรูปแบบติดกัน">Days</th>
              <th title="ราคาล่าสุด">Close</th>
              <th title="ความน่าจะเป็นที่จะเด้ง/ย่อ ในวันพรุ่งนี้">Win Rate</th>
              <th title="ผลตอบแทนเฉลี่ย">Avg Return</th>
              <th title="จำนวนครั้งในอดีตที่เกิดรูปแบบนี้">Occurrences</th>
            </tr>
          </thead>
          <tbody>`;
        items.forEach(item => {
          html += `<tr>
            <td style="text-align:left; font-weight:bold">${item.symbol}</td>
            <td>${item.consecutive}</td>
            <td title="O: ${item.latest.open} H: ${item.latest.high} L: ${item.latest.low}">${item.latest.close.toFixed(2)}</td>
            <td style="color:${item.win_rate >= 60 ? 'var(--green)' : 'inherit'}">${item.win_rate.toFixed(1)}%</td>
            <td style="color:${item.avg_return >= 0 ? 'var(--green)' : 'var(--red)'}">${item.avg_return > 0 ? '+' : ''}${item.avg_return.toFixed(2)}%</td>
            <td>${item.occurrences}</td>
          </tr>`;
        });
        html += `</tbody></table>`;
      }
    });

    html += '</div>';
    content.innerHTML = html;
  } catch (err) {
    content.innerHTML = `<span style="color:var(--red)">Failed to load data: ${err.message}</span>`;
  }
}

function closePatternScreener() {
  document.getElementById('patternScreenerModal').classList.remove('open');
}
