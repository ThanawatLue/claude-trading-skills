from __future__ import annotations

from pathlib import Path

import yaml

from scripts.sync_automation_config_defaults import sync_config


def test_sync_preserves_state_overrides(tmp_path: Path) -> None:
    template = tmp_path / "template.yaml"
    state = tmp_path / "state.yaml"
    template.write_text(
        """
auto_paper:
  execute: false
  fingerprint_block: true
  source_rules:
    thai-swing-dip:
      min_score: 85
      max_new_per_run: 1
paper_exit_rules:
  thai-swing-dip:
    max_hold_days: 4
""".strip(),
        encoding="utf-8",
    )
    state.write_text(
        """
auto_paper:
  execute: true
  account_size: 30000
  source_rules:
    thai-swing-dip:
      target_r: 1.0
""".strip(),
        encoding="utf-8",
    )

    merged = sync_config(template, state, write=True)

    assert merged["auto_paper"]["execute"] is True
    assert merged["auto_paper"]["account_size"] == 30000
    assert merged["auto_paper"]["fingerprint_block"] is True
    assert merged["auto_paper"]["source_rules"]["thai-swing-dip"]["min_score"] == 85
    assert merged["auto_paper"]["source_rules"]["thai-swing-dip"]["target_r"] == 1.0
    assert merged["paper_exit_rules"]["thai-swing-dip"]["max_hold_days"] == 4
    saved = yaml.safe_load(state.read_text(encoding="utf-8"))
    assert saved["auto_paper"]["execute"] is True
