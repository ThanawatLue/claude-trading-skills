import json
import os

def load_config(skill_root_path: str = "skills/market-breadth-analyzer/") -> dict:
    """Loads the configuration from config.json."""
    config_path = os.path.join(skill_root_path, "config.json")
    if not os.path.exists(config_path):
        # Create a default config.json if it doesn't exist
        default_config = {
            "data_path": "data/market_breadth_data.csv",
            "output_path": "reports/",
            "history_file": "history/market_breadth_history.json",
            "scoring_weights": {
                "breadth_level_trend": 0.25,
                "ma_crossover": 0.20,
                "cycle_position": 0.20,
                "bearish_signal": 0.15,
                "historical_percentile": 0.10,
                "divergence": 0.10
            },
            "calculator_params": {
                "ma_crossover_calculator": {
                    "short_period": 8,
                    "long_period": 200
                },
                "peak_trough_calculator": {
                    "lookback_period": 60
                },
                "divergence_calculator": {
                    "short_window": 20,
                    "long_window": 60
                }
            },
            "report_generator": {
                "recent_days_summary": 5
            },
            "market_breadth_analyzer": {
                "required_columns": ["Date", "Symbol", "Close", "Volume"]
            }
        }
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        return default_config
    
    with open(config_path, 'r') as f:
        return json.load(f)

