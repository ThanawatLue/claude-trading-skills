# Paper Trading Discipline Rules & Metrics

This reference document outlines the key metrics and rules used to evaluate trading discipline in the Paper Trade Simulator.

## 1. Stop Respect Rate (SRR)

**Formula:**
$$\text{SRR} = \frac{\text{closed\_stop}}{\text{closed\_stop} + \text{closed\_manual\_loss}}$$

- **Target:** $> 80\%$
- **Purpose:** Prevents the trader from overriding stop-losses manually due to fear or hope. A lower respect rate indicates panic selling before the target is reached or widening the stop.

## 2. Patience Score (PS)

**Formula:**
$$\text{PS} = 1 - \frac{\text{early\_cuts}}{\text{eligible\_winners}}$$

- **Target:** $> 70\%$
- **Purpose:** Measures the ability to let winning trades reach their target. An early cut occurs when a position is closed manually with a realized R-multiple that leaves $>0.5R$ unrealized relative to the Maximum Favorable Excursion (MFE).

## 3. Target Hit Rate

**Formula:**
$$\text{Target Hit Rate} = \frac{\text{closed\_target}}{\text{total\_closed}}$$

- **Target:** $> 30\%$ (This is a flexible target and depends heavily on the specific trading strategy. Higher is generally better, but consistent profitability is key.)
- **Purpose:** Measures the effectiveness of the chosen profit targets and the ability to hold trades until they reach those targets. A low hit rate might suggest unrealistic targets or premature exits.

## 4. Average R per Win (Avg R/Win)

**Formula:**
$$\text{Avg R/Win} = \text{Average}(\text{realized\_r } | \text{ realized\_r} > 0)$$

- **Target:** $> 1.5R$ (A higher value indicates that winning trades generate significant profit multiples relative to the initial risk.)
- **Purpose:** Reflects the profitability of winning trades. It's crucial for understanding the upside potential of a strategy and contributes directly to overall expectancy.

## 5. Average R per Loss (Avg R/Loss)

**Formula:**
$$\text{Avg R/Loss} = \text{Average}(\text{realized\_r } | \text{ realized\_r} < 0)$$

- **Target:** Between $-0.8R$ and $-1R$ (Ideally, losses should be capped near $1R$, meaning the entire initial risk is lost. Values significantly below $-1R$ indicate poor risk management, such as widening stops or letting losses run.)
- **Purpose:** Measures the impact of losing trades. Keeping this metric close to $-1R$ is vital for effective risk management and capital preservation.

## 6. Expectancy

**Formula:**
$$\text{Expectancy} = (\text{Win Rate} \times \text{Avg R/Win}) + ( (1 - \text{Win Rate}) \times \text{Avg R/Loss})$$

- **Target:** $> 0.3R$ (A positive expectancy indicates a profitable trading system over the long run. Higher values suggest a more robust and profitable strategy.)
- **Purpose:** The most comprehensive measure of a trading system's profitability, combining win rate and the average size of wins and losses. It answers: "For every dollar risked, how much can I expect to make?"
