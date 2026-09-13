"""Test k=1.2x Floor 5.0% with Early Fakeout and Target 2.0R vs 2.2R."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.test_hybrid_champion import load_data


def main():
    signals, bars_by_symbol, atr_by_symbol, set_ret_by_date = load_data()
    print("Testing variations of k=1.2x vs 1.5x with Target 2.0R vs 2.2R...")

    # Let's adjust sim_hybrid with different k
    # We will test directly
    from scripts.simulate_advanced_detectors import AdvancedStrategy, simulate

    for k in [1.2, 1.4, 1.5]:
        for floor in [4.5, 5.0]:
            for target in [2.0, 2.2]:
                for use_fake in [True, False]:
                    name = f"DynATR k={k} Flr={floor}% | Tgt={target}R | Fakeout={use_fake}"
                    strat = AdvancedStrategy(
                        name=name,
                        use_dynamic_atr=True,
                        atr_multiplier=k,
                        fee_floor_pct=floor,
                        target_1_r=target,
                        use_early_fakeout=use_fake,
                        fakeout_vol_ratio=0.40,
                        fakeout_max_mfe=0.20,
                        use_velocity_stall=True,
                        stall_days=4,
                    )
                    r = simulate(strat, signals, bars_by_symbol, atr_by_symbol, set_ret_by_date)
                    print(f"{name:<55} | WR: {r['win_rate']:>4.1f}% | Net R: {r['net_r']:>+5.2f}R | PnL: {r['net_pnl']:>+9.2f} | PF: {r['pf']:>4.2f}")

if __name__ == "__main__":
    main()
