"""Tests for generate_pivots.py — self-contained with inline fixtures."""

from __future__ import annotations

import importlib
import json
import os
import sys

import pytest
import yaml

# Ensure parent directory is on sys.path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import generate_pivots as gp  # noqa: E402

# ---------------------------------------------------------------------------
# Inline Fixture Helpers
# ---------------------------------------------------------------------------


def _make_breakout_draft() -> dict:
    """Draft matching trend_following_breakout archetype."""
    return {
        "id": "my_breakout_v1",
        "concept_id": "concept_001",
        "hypothesis_type": "breakout",
        "mechanism_tag": "behavior",
        "entry_family": "pivot_breakout",
        "regime": "Bull",
        "exit": {
            "stop_loss_pct": 0.08,
            "take_profit_rr": 3.0,
            "time_stop_days": 20,
        },
        "risk": {
            "position_sizing": "fixed_risk",
            "risk_per_trade": 0.01,
            "max_positions": 5,
            "max_sector_exposure": 0.3,
        },
        "entry": {
            "conditions": ["close > high20_prev", "rel_volume >= 1.5"],
            "trend_filter": ["price > sma_200"],
        },
        "thesis": "Breakout with volume confirmation.",
        "invalidation_signals": ["close < sma_200"],
    }


def _make_mean_reversion_draft() -> dict:
    """Draft matching mean_reversion_pullback archetype."""
    return {
        "id": "mean_rev_v1",
        "concept_id": "concept_002",
        "hypothesis_type": "mean_reversion",
        "mechanism_tag": "statistical",
        "entry_family": "research_only",
        "regime": "Neutral",
        "exit": {
            "stop_loss_pct": 0.04,
            "take_profit_rr": 2.0,
            "time_stop_days": 7,
        },
        "risk": {
            "position_sizing": "fixed_risk",
            "risk_per_trade": 0.005,
            "max_positions": 3,
            "max_sector_exposure": 0.3,
        },
        "entry": {
            "conditions": ["rsi_14 < 30", "price > sma_200"],
            "trend_filter": ["sma_50 > sma_200"],
        },
        "thesis": "RSI oversold bounce.",
        "invalidation_signals": [],
    }


def _make_triggers(trigger_ids: list[str]) -> list[dict]:
    """Build a list of trigger dicts from trigger id strings."""
    return [
        {"trigger": t, "severity": "high", "message": f"Trigger {t} fired"} for t in trigger_ids
    ]


def _make_base_draft_for_test() -> dict:
    """Provides a basic, generic draft for testing purposes."""
    return {
        "id": "test_strategy_v1",
        "concept_id": "concept_abc",
        "hypothesis_type": "some_hypothesis",
        "mechanism_tag": "some_mechanism",
        "entry_family": "research_only",
        "regime": "Neutral",
        "exit": {
            "stop_loss_pct": 0.05,
            "take_profit_rr": 2.0,
            "time_stop_days": 15,
        },
        "risk": {
            "position_sizing": "fixed_risk",
            "risk_per_trade": 0.005,
            "max_positions": 5,
            "max_sector_exposure": 0.3,
        },
        "entry": {
            "conditions": ["price_above_ma", "volume_confirm"],
            "trend_filter": ["market_up"],
        },
        "thesis": "A generic test thesis.",
        "invalidation_signals": [],
    }


# ---------------------------------------------------------------------------
# Archetype Identification
# ---------------------------------------------------------------------------


class TestIdentifyArchetype:
    def test_identify_archetype_breakout_behavior(self):
        draft = _make_breakout_draft()
        assert gp.identify_current_archetype(draft) == "trend_following_breakout"

    def test_identify_archetype_mean_reversion_statistical(self):
        draft = _make_mean_reversion_draft()
        assert gp.identify_current_archetype(draft) == "mean_reversion_pullback"

    def test_identify_archetype_unknown_returns_none(self):
        draft = {
            "hypothesis_type": "quantum_flux",
            "mechanism_tag": "alien_signal",
            "entry_family": "warp_drive",
        }
        assert gp.identify_current_archetype(draft) is None


# ---------------------------------------------------------------------------
# Module Set Extraction
# ---------------------------------------------------------------------------


class TestComputeModuleSet:
    def test_compute_module_set_basic(self):
        draft = _make_breakout_draft()
        modules = gp.compute_module_set(draft)
        assert isinstance(modules, set)
        # Must contain (key, value) tuples
        assert all(isinstance(m, tuple) and len(m) == 2 for m in modules)
        # Check a few expected entries
        assert ("hypothesis_type", "breakout") in modules
        assert ("mechanism_tag", "behavior") in modules
        assert ("entry_family", "pivot_breakout") in modules

    def test_compute_module_set_horizon_classification(self):
        # short: time_stop_days=5
        draft_short = {"exit": {"time_stop_days": 5, "stop_loss_pct": 0.06}}
        modules_short = gp.compute_module_set(draft_short)
        assert ("horizon", "short") in modules_short

        # medium: time_stop_days=20
        draft_medium = {"exit": {"time_stop_days": 20, "stop_loss_pct": 0.06}}
        modules_medium = gp.compute_module_set(draft_medium)
        assert ("horizon", "medium") in modules_medium

        # long: time_stop_days=60
        draft_long = {"exit": {"time_stop_days": 60, "stop_loss_pct": 0.06}}
        modules_long = gp.compute_module_set(draft_long)
        assert ("horizon", "long") in modules_long

    def test_compute_module_set_risk_style(self):
        # tight: stop_loss_pct=0.03
        draft_tight = {"exit": {"stop_loss_pct": 0.03, "time_stop_days": 20}}
        modules_tight = gp.compute_module_set(draft_tight)
        assert ("risk_style", "tight") in modules_tight

        # normal: stop_loss_pct=0.06
        draft_normal = {"exit": {"stop_loss_pct": 0.06, "time_stop_days": 20}}
        modules_normal = gp.compute_module_set(draft_normal)
        assert ("risk_style", "normal") in modules_normal

        # wide: stop_loss_pct=0.10
        draft_wide = {"exit": {"stop_loss_pct": 0.10, "time_stop_days": 20}}
        modules_wide = gp.compute_module_set(draft_wide)
        assert ("risk_style", "wide") in modules_wide


# ---------------------------------------------------------------------------
# Novelty Scoring
# ---------------------------------------------------------------------------


class TestNoveltyScoring:
    def test_novelty_identical_strategies_zero(self):
        draft = _make_breakout_draft()
        s = gp.compute_module_set(draft)
        assert gp.score_novelty(s, s) == 0.0

    def test_novelty_completely_different_one(self):
        a = {("a", "1"), ("b", "2")}
        b = {("c", "3"), ("d", "4")}
        assert gp.score_novelty(a, b) == 1.0

    def test_novelty_partial_overlap(self):
        a = {("a", "1"), ("b", "2"), ("c", "3")}
        b = {("a", "1"), ("d", "4"), ("e", "5")}
        # intersection={("a","1")}, union=5 items => 1 - 1/5 = 0.8
        novelty = gp.score_novelty(a, b)
        assert 0.0 < novelty < 1.0
        assert abs(novelty - 0.8) < 1e-9


# ---------------------------------------------------------------------------
# Quality Potential
# ---------------------------------------------------------------------------


class TestQualityPotential:
    def test_quality_table_known_pair(self):
        score = gp.score_quality_potential("cost_defeat", "mean_reversion_pullback")
        assert score == 0.8  # exact match from QUALITY_TABLE

    def test_quality_table_unknown_pair(self):
        score = gp.score_quality_potential("nonexistent_trigger", "fake_archetype")
        assert score == gp.DEFAULT_QUALITY  # should return 0.3


# ---------------------------------------------------------------------------
# Inversion Generation
# ---------------------------------------------------------------------------


class TestGenerateInversions:
    def test_generate_inversions_cost_defeat(self):
        draft = _make_breakout_draft()
        triggers = _make_triggers(["cost_defeat"])
        proposals = gp.generate_inversions(draft, triggers, "trend_following_breakout")
        assert len(proposals) > 0

        # cost_defeat inversions should produce proposals with shortened horizon
        has_short_horizon = any(p["exit"]["time_stop_days"] <= 7 for p in proposals)
        assert has_short_horizon, "cost_defeat should produce at least one short-horizon proposal"

    def test_generate_inversions_tail_risk(self):
        draft = _make_breakout_draft()
        triggers = _make_triggers(["tail_risk"])
        proposals = gp.generate_inversions(draft, triggers, "trend_following_breakout")
        assert len(proposals) > 0

        # tail_risk inversions should produce proposals with tighter risk
        has_tight_risk = any(p["exit"]["stop_loss_pct"] <= 0.04 for p in proposals)
        assert has_tight_risk, "tail_risk should produce at least one tight-risk proposal"


# ---------------------------------------------------------------------------
# Archetype Switch
# ---------------------------------------------------------------------------


class TestGenerateArchetypeSwitches:
    def test_generate_archetype_switches_from_breakout(self):
        draft = _make_breakout_draft()
        triggers = _make_triggers(["improvement_plateau"])
        source_arch = "trend_following_breakout"
        proposals = gp.generate_archetype_switches(draft, source_arch, triggers)
        assert len(proposals) > 0

        # trend_following_breakout's compatible targets
        expected_targets = {
            "mean_reversion_pullback",
            "volatility_contraction",
            "sector_rotation_momentum",
        }
        actual_targets = {p["pivot_metadata"]["target_archetype"] for p in proposals}
        assert actual_targets == expected_targets

    def test_generate_archetype_switches_unknown_archetype(self):
        draft = _make_breakout_draft()
        triggers = _make_triggers(["cost_defeat"])
        proposals = gp.generate_archetype_switches(draft, None, triggers)
        assert proposals == []

        proposals2 = gp.generate_archetype_switches(draft, "nonexistent_arch", triggers)
        assert proposals2 == []


# ---------------------------------------------------------------------------
# Ranking and Selection
# ---------------------------------------------------------------------------


class TestRankAndSelect:
    def test_rank_and_select_top_n(self):
        draft = _make_breakout_draft()
        triggers = _make_triggers(["cost_defeat"])
        source_arch = "trend_following_breakout"

        all_proposals = gp.generate_inversions(draft, triggers, source_arch)
        all_proposals += gp.generate_archetype_switches(draft, source_arch, triggers)
        assert len(all_proposals) > 3  # ensure we have enough to select from

        selected = gp.rank_and_select(all_proposals, draft, triggers, max_pivots=3)
        assert len(selected) <= 3

        # Verify combined scores are in descending order
        scores = [p["pivot_metadata"]["scores"]["combined"] for p in selected]
        assert scores == sorted(scores, reverse=True)

    def test_rank_and_select_diversity_constraint(self):
        """Max 1 per target archetype."""
        draft = _make_breakout_draft()
        triggers = _make_triggers(["cost_defeat"])
        source_arch = "trend_following_breakout"

        all_proposals = gp.generate_inversions(draft, triggers, source_arch)
        all_proposals += gp.generate_archetype_switches(draft, source_arch, triggers)

        selected = gp.rank_and_select(all_proposals, draft, triggers, max_pivots=10)

        archetypes = [p["pivot_metadata"]["target_archetype"] for p in selected]
        assert len(archetypes) == len(set(archetypes)), "Each archetype should appear at most once"

    def test_rank_and_select_tiebreak_deterministic(self):
        """Same combined score -> higher novelty wins; same novelty -> alphabetical id."""
        draft = _make_breakout_draft()

        # Create synthetic proposals with identical combined but different novelty/ids
        p_a = {
            "id": "alpha",
            "hypothesis_type": "breakout",
            "mechanism_tag": "behavior",
            "entry_family": "pivot_breakout",
            "regime": "Bull",
            "exit": {"stop_loss_pct": 0.08, "time_stop_days": 20},
            "pivot_metadata": {
                "target_archetype": "arch_a",
                "targeted_triggers": ["cost_defeat"],
            },
        }
        p_b = {
            "id": "beta",
            "hypothesis_type": "mean_reversion",
            "mechanism_tag": "statistical",
            "entry_family": "research_only",
            "regime": "Neutral",
            "exit": {"stop_loss_pct": 0.04, "time_stop_days": 7},
            "pivot_metadata": {
                "target_archetype": "arch_b",
                "targeted_triggers": ["cost_defeat"],
            },
        }
        p_c = {
            "id": "charlie",
            "hypothesis_type": "mean_reversion",
            "mechanism_tag": "statistical",
            "entry_family": "research_only",
            "regime": "Neutral",
            "exit": {"stop_loss_pct": 0.04, "time_stop_days": 7},
            "pivot_metadata": {
                "target_archetype": "arch_c",
                "targeted_triggers": ["cost_defeat"],
            },
        }

        triggers = _make_triggers(["cost_defeat"])

        # Run selection multiple times — result must be deterministic
        results = []
        for _ in range(5):
            selected = gp.rank_and_select([p_a, p_b, p_c], draft, triggers, max_pivots=10)
            results.append([s["id"] for s in selected])

        # All 5 runs must produce the same order
        assert all(r == results[0] for r in results), "Selection must be deterministic"

        # Verify tiebreak: among those with same combined score, higher novelty wins
        selected = gp.rank_and_select([p_a, p_b, p_c], draft, triggers, max_pivots=10)
        for i in range(len(selected) - 1):
            s_i = selected[i]["pivot_metadata"]["scores"]
            s_j = selected[i + 1]["pivot_metadata"]["scores"]
            if s_i["combined"] == s_j["combined"]:
                if s_i["novelty"] == s_j["novelty"]:
                    assert selected[i]["id"] < selected[i + 1]["id"], (
                        "Same combined and novelty -> alphabetical id order"
                    )
                else:
                    assert s_i["novelty"] >= s_j["novelty"], "Same combined -> higher novelty first"


# ---------------------------------------------------------------------------
# Export Ticket
# ---------------------------------------------------------------------------


class TestBuildExportTicket:
    def test_build_export_ticket_eligible(self):
        draft = {
            "id": "pivot_my_breakout_v1_switch_volatility_contraction",
            "name": "Volatility Contraction (pivoted from my_breakout_v1)",
            "hypothesis_type": "breakout",
            "mechanism_tag": "structural",
            "entry_family": "pivot_breakout",
            "regime": "Bull",
            "entry": {
                "conditions": ["volatility_contraction_detected"],
                "trend_filter": ["price > sma_200"],
            },
            "exit": {
                "stop_loss_pct": 0.05,
                "take_profit_rr": 3.0,
                "time_stop_days": 20,
            },
            "risk": {
                "position_sizing": "fixed_risk",
                "risk_per_trade": 0.005,
                "max_positions": 5,
                "max_sector_exposure": 0.3,
            },
            "pivot_metadata": {
                "source_strategy_id": "my_breakout_v1",
            },
        }
        ticket, errors = gp.build_export_ticket_if_eligible(draft)
        assert ticket is not None
        assert ticket["entry_family"] == "pivot_breakout"
        assert "id" in ticket
        assert ticket["hypothesis_type"] == "breakout"

    def test_build_export_ticket_research_only(self):
        draft = {
            "id": "pivot_test_switch_mean_reversion",
            "name": "Mean Reversion Pullback",
            "hypothesis_type": "mean_reversion",
            "mechanism_tag": "statistical",
            "entry_family": "research_only",
            "exit": {"stop_loss_pct": 0.04, "take_profit_rr": 2.0, "time_stop_days": 7},
            "risk": {},
            "pivot_metadata": {"source_strategy_id": "test"},
        }
        ticket, errors = gp.build_export_ticket_if_eligible(draft)
        assert ticket is None


# ---------------------------------------------------------------------------
# ID Sanitization
# ---------------------------------------------------------------------------


class TestSanitizeIdentifier:
    def test_sanitize_identifier_special_chars(self):
        result = gp.sanitize_identifier("Hello World! @#$%")
        assert result == "hello_world"
        assert " " not in result
        assert all(c.isalnum() or c == "_" for c in result)

    def test_sanitize_identifier_empty_string_returns_pivot(self):
        result = gp.sanitize_identifier("")
        assert result == "pivot"

        result2 = gp.sanitize_identifier("   ")
        assert result2 == "pivot"


# ---------------------------------------------------------------------------
# Objective Reframe Generation
# ---------------------------------------------------------------------------


class TestObjectiveReframes:
    def test_reframe_tail_risk_modifies_exit_and_criteria(self):
        draft = _make_base_draft_for_test()
        triggers = _make_triggers(["tail_risk"])
        source_arch = "trend_following_breakout"  # A valid archetype for reframe processing

        proposals = gp.generate_objective_reframes(draft, triggers, source_arch)

        assert len(proposals) > 0
        reframe_proposal = None
        for p in proposals:
            if "reframe_tail_risk" in p["id"]:
                reframe_proposal = p
                break
        assert reframe_proposal is not None

        # Verify exit adjustments
        assert reframe_proposal["exit"]["stop_loss_pct"] == 0.04
        assert reframe_proposal["exit"]["take_profit_rr"] == 1.5

        # Verify new criteria
        assert reframe_proposal["validation_plan"]["success_criteria"] == [
            "max_drawdown_pct < 25",
            "expected_value_after_costs > 0",
        ]
        assert reframe_proposal["pivot_metadata"]["why"] == (
            "Reframe from return maximization to drawdown minimization"
        )
        assert reframe_proposal["pivot_metadata"]["targeted_triggers"] == ["tail_risk"]

    def test_reframe_cost_defeat_modifies_exit_and_criteria(self):
        draft = _make_base_draft_for_test()
        triggers = _make_triggers(["cost_defeat"])
        source_arch = "mean_reversion_pullback"  # Another valid archetype

        proposals = gp.generate_objective_reframes(draft, triggers, source_arch)

        assert len(proposals) > 0
        reframe_proposal = None
        for p in proposals:
            if "reframe_cost_defeat" in p["id"]:
                reframe_proposal = p
                break
        assert reframe_proposal is not None

        # Verify exit adjustments
        assert reframe_proposal["exit"]["stop_loss_pct"] == 0.03
        assert reframe_proposal["exit"]["take_profit_rr"] == 1.5
        assert reframe_proposal["exit"]["time_stop_days"] == 5

        # Verify new criteria
        assert reframe_proposal["validation_plan"]["success_criteria"] == [
            "win_rate > 55",
            "expected_value_after_costs > 0",
        ]
        assert reframe_proposal["pivot_metadata"]["why"] == (
            "Reframe to win rate maximization with smaller targets"
        )
        assert reframe_proposal["pivot_metadata"]["targeted_triggers"] == ["cost_defeat"]

    def test_reframe_improvement_plateau_modifies_criteria_only(self):
        draft = _make_base_draft_for_test()
        triggers = _make_triggers(["improvement_plateau"])
        source_arch = "earnings_drift_pead"

        proposals = gp.generate_objective_reframes(draft, triggers, source_arch)

        assert len(proposals) > 0
        reframe_proposal = None
        for p in proposals:
            if "reframe_improvement_plateau" in p["id"]:
                reframe_proposal = p
                break
        assert reframe_proposal is not None

        # Verify exit adjustments are NOT applied (empty in REFRAME_MAP)
        # Should retain original values from _make_base_draft_for_test
        assert reframe_proposal["exit"]["stop_loss_pct"] == 0.05
        assert reframe_proposal["exit"]["take_profit_rr"] == 2.0
        assert reframe_proposal["exit"]["time_stop_days"] == 15

        # Verify new criteria
        assert reframe_proposal["validation_plan"]["success_criteria"] == [
            "risk_adjusted_return_per_exposure > 0.5",
            "expected_value_after_costs > 0",
        ]
        assert reframe_proposal["pivot_metadata"]["why"] == (
            "Reframe to risk-adjusted return per unit exposure"
        )
        assert reframe_proposal["pivot_metadata"]["targeted_triggers"] == ["improvement_plateau"]

    def test_no_reframe_if_trigger_not_in_map(self):
        draft = _make_base_draft_for_test()
        triggers = _make_triggers(["non_existent_trigger"])
        source_arch = "trend_following_breakout"

        proposals = gp.generate_objective_reframes(draft, triggers, source_arch)
        assert len(proposals) == 0

    def test_reframe_no_compatible_archetypes_uses_default_set(self):
        # If source_archetype is not in ARCHETYPE_CATALOG and compatible_pivots_from is empty
        # or if ARCHETYPE_CATALOG itself is empty for some reason,
        # it should default to a subset of available archetypes or handle gracefully.
        draft = _make_base_draft_for_test()
        triggers = _make_triggers(["tail_risk"])
        # Use an archetype not explicitly in ARCHETYPE_CATALOG for this draft
        # to test the 'else' branch for target_archetypes
        proposals = gp.generate_objective_reframes(draft, triggers, "unknown_archetype")

        assert len(proposals) > 0  # Should still generate proposals based on default logic
        # Check that proposals are generated and some reframe logic applied
        reframe_proposal = proposals[0]
        assert reframe_proposal["exit"]["stop_loss_pct"] == 0.04
        assert reframe_proposal["validation_plan"]["success_criteria"] == [
            "max_drawdown_pct < 25",
            "expected_value_after_costs > 0",
        ]


# ---------------------------------------------------------------------------
# Cross-Validation with candidate_contract.py
# ---------------------------------------------------------------------------


class TestCrossValidation:
    """Verify generate_pivots constants match candidate_contract.py."""

    @pytest.fixture(autouse=True)
    def _load_candidate_contract(self):
        """Import candidate_contract via importlib for cross-validation."""
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
        )
        contract_path = os.path.join(
            project_root,
            "skills",
            "edge-candidate-agent",
            "scripts",
            "candidate_contract.py",
        )
        if not os.path.exists(contract_path):
            pytest.skip(f"candidate_contract.py not found at {contract_path}")

        spec = importlib.util.spec_from_file_location("candidate_contract", contract_path)
        self.contract_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.contract_mod)

    def test_exportable_families_match_supported_entry_families(self):
        assert gp.DEFAULT_EXPORTABLE_FAMILIES == self.contract_mod.SUPPORTED_ENTRY_FAMILIES

    def test_required_validation_fields_consistent(self):
        """The fields validated by _validate_ticket_minimal must match
        the required string fields in validate_ticket_payload."""
        # candidate_contract checks these as required non-empty strings:
        # ("id", "hypothesis_type", "entry_family")
        # Our minimal validator must check the same set.
        dummy_empty = {"id": "", "hypothesis_type": "", "entry_family": ""}
        our_errors = gp._validate_ticket_minimal(dummy_empty)
        their_errors = self.contract_mod.validate_ticket_payload(dummy_empty)

        # Both should flag all three fields
        our_fields = {e.split(".")[1].split(" ")[0] for e in our_errors if "must be" in e}
        their_fields = {e.split(".")[1].split(" ")[0] for e in their_errors if "must be" in e}
        required = {"id", "hypothesis_type", "entry_family"}
        assert required <= our_fields
        assert required <= their_fields

    def test_validation_method_constraint_consistent(self):
        """Both validators must reject non-full_sample method and non-null oos_ratio."""
        # Bad method
        ticket_bad_method = {
            "id": "t1",
            "hypothesis_type": "breakout",
            "entry_family": "pivot_breakout",
            "validation": {"method": "walk_forward", "oos_ratio": None},
        }
        our_errors = gp._validate_ticket_minimal(ticket_bad_method)
        their_errors = self.contract_mod.validate_ticket_payload(ticket_bad_method)
        assert any("full_sample" in e for e in our_errors)
        assert any("full_sample" in e for e in their_errors)

        # Bad oos_ratio
        ticket_bad_oos = {
            "id": "t2",
            "hypothesis_type": "breakout",
            "entry_family": "pivot_breakout",
            "validation": {"method": "full_sample", "oos_ratio": 0.3},
        }
        our_errors = gp._validate_ticket_minimal(ticket_bad_oos)
        their_errors = self.contract_mod.validate_ticket_payload(ticket_bad_oos)
        assert any("oos_ratio" in e for e in our_errors)
        assert any("oos_ratio" in e for e in their_errors)

        # Valid validation block — no errors from either
        ticket_ok = {
            "id": "t3",
            "hypothesis_type": "breakout",
            "entry_family": "pivot_breakout",
            "validation": {"method": "full_sample"},
        }
        our_errors = gp._validate_ticket_minimal(ticket_ok)
        their_errors = self.contract_mod.validate_ticket_payload(ticket_ok)
        our_val_errors = [e for e in our_errors if "validation" in e]
        their_val_errors = [e for e in their_errors if "validation" in e]
        assert our_val_errors == []
        assert their_val_errors == []


# ---------------------------------------------------------------------------
# Output Functions
# ---------------------------------------------------------------------------


class TestOutputFunctions:
    @pytest.fixture
    def mock_paths(self, mocker):
        """Mocks Path.mkdir and Path.write_text for testing file outputs."""
        mocker.patch("pathlib.Path.mkdir", autospec=True)
        mocker.patch("pathlib.Path.write_text", autospec=True)
        return mocker

    @pytest.fixture
    def dummy_data(self):
        """Provides dummy data for testing output functions."""
        source_draft = _make_breakout_draft()
        source_draft["_source_path"] = "/app/strategy.yaml"

        diagnosis = {
            "strategy_id": "my_breakout_v1",
            "triggers_fired": _make_triggers(["cost_defeat", "tail_risk"]),
            "recommendation": "pivot",
            "score_trajectory": [100, 90, 80],
            "_source_path": "/app/diagnosis.json",
        }

        selected_proposals = [
            {
                "id": "pivot_my_breakout_v1_inv_cost_defeat_mean_reversion_pullback",
                "entry_family": "research_only",
                "exit": {"time_stop_days": 7, "stop_loss_pct": 0.04},
                "pivot_metadata": {
                    "pivot_technique": "assumption_inversion",
                    "source_strategy_id": "my_breakout_v1",
                    "target_archetype": "mean_reversion_pullback",
                    "what_changed": {"signal": "Inversion: horizon -> shorten"},
                    "why": "Reduce friction exposure",
                    "scores": {"combined": 0.7, "quality_potential": 0.8, "novelty": 0.6},
                },
            },
            {
                "id": "pivot_my_breakout_v1_switch_volatility_contraction",
                "entry_family": "pivot_breakout",
                "exit": {"time_stop_days": 20, "stop_loss_pct": 0.05},
                "pivot_metadata": {
                    "pivot_technique": "archetype_switch",
                    "source_strategy_id": "my_breakout_v1",
                    "target_archetype": "volatility_contraction",
                    "what_changed": {"signal": "Architecture switch"},
                    "why": "Structural pivot",
                    "scores": {"combined": 0.8, "quality_potential": 0.9, "novelty": 0.7},
                },
            },
        ]

        # Add `pivot_metadata` for write_outputs to pop and restore
        for proposal in selected_proposals:
            if "pivot_metadata" not in proposal:
                proposal["pivot_metadata"] = {}
            if "scores" not in proposal["pivot_metadata"]:
                proposal["pivot_metadata"]["scores"] = {
                    "combined": 0.5,
                    "quality_potential": 0.5,
                    "novelty": 0.5,
                }
        return source_draft, diagnosis, selected_proposals

    def test_write_outputs_creates_files(self, mock_paths, dummy_data):
        source_draft, diagnosis, selected_proposals = dummy_data
        output_dir = gp.Path("/tmp/reports")

        # Mock datetime to ensure consistent filenames
        mocker = mock_paths
        fake_now = gp.datetime(2023, 10, 26, 10, 30, 0, tzinfo=gp.timezone.utc)
        mocker.patch("generate_pivots.datetime", autospec=True)
        gp.datetime.now.return_value = fake_now
        gp.datetime.strftime = fake_now.strftime  # Mock static method strftime

        manifest = gp.write_outputs(selected_proposals, diagnosis, source_draft, output_dir)

        # Verify directories were created
        mkdir_calls = gp.Path.mkdir.call_args_list
        mkdir_paths = [str(c.args[0]).replace("\\", "/") for c in mkdir_calls]
        assert any(p.endswith("research_only") for p in mkdir_paths)
        assert any(p.endswith("exportable") for p in mkdir_paths)

        # Verify YAML draft files were written
        assert gp.Path.write_text.call_count >= 3  # 2 drafts + 1 manifest + 1 report
        yaml_calls = [
            call_args
            for call_args in gp.Path.write_text.call_args_list
            if str(call_args.args[0]).endswith(".yaml")
        ]
        assert (
            len(yaml_calls) == 3
        )  # Two proposals (one research_only, one exportable) + 1 exportable ticket

        # Check a research_only draft
        research_draft_call = next(
            (c for c in yaml_calls if "research_only" in str(c.args[0])), None
        )
        assert research_draft_call is not None
        assert (
            "pivot_my_breakout_v1_inv_cost_defeat_mean_reversion_pullback_20231026_103000.yaml"
            in str(research_draft_call.args[0])
        )
        assert "exit" in research_draft_call.args[1]  # Check content

        # Check an exportable draft and its ticket
        exportable_draft_call = next(
            (
                c
                for c in yaml_calls
                if "exportable" in str(c.args[0]) and "ticket" not in str(c.args[0])
            ),
            None,
        )
        assert exportable_draft_call is not None
        assert "pivot_my_breakout_v1_switch_volatility_contraction_20231026_103000.yaml" in str(
            exportable_draft_call.args[0]
        )
        assert "exit" in exportable_draft_call.args[1]

        exportable_ticket_call = next((c for c in yaml_calls if "ticket_" in str(c.args[0])), None)
        assert exportable_ticket_call is not None
        assert "ticket_my_breakout_v1_switch_volatility_contraction_20231026_103000.yaml" in str(
            exportable_ticket_call.args[0]
        )
        assert "entry_family" in exportable_ticket_call.args[1]

        # Verify manifest JSON was written
        json_call = next(
            (c for c in gp.Path.write_text.call_args_list if str(c.args[0]).endswith(".json")),
            None,
        )
        assert json_call is not None
        assert "pivot_manifest_my_breakout_v1_20231026_103000.json" in str(json_call.args[0])
        manifest_content = json.loads(json_call.args[1])
        assert manifest_content["strategy_id"] == "my_breakout_v1"
        assert len(manifest_content["drafts"]) == 2
        assert (
            len(manifest_content["errors"]) == 0
        )  # Should be 0 if _validate_ticket_minimal passes

        # Verify report Markdown was written
        report_call = next(
            (c for c in gp.Path.write_text.call_args_list if str(c.args[0]).endswith(".md")),
            None,
        )
        assert report_call is not None
        assert "pivot_report_my_breakout_v1_20231026_103000.md" in str(report_call.args[0])
        assert "## Stagnation Diagnosis" in report_call.args[1]  # Check content

        # Verify manifest return value
        assert manifest["total_pivots_generated"] == 2
        assert manifest["exportable_count"] == 1
        assert manifest["research_only_count"] == 1

    def test_build_report_content(self, dummy_data):
        source_draft, diagnosis, selected_proposals = dummy_data

        manifest = {
            "generated_at_utc": "2023-10-26T10:30:00",
            "strategy_id": "my_breakout_v1",
            "triggers_fired": ["cost_defeat", "tail_risk"],
        }

        report_content = gp._build_report(selected_proposals, diagnosis, source_draft, manifest)

        assert "# Pivot Report: my_breakout_v1" in report_content
        assert "**Generated**: 2023-10-26T10:30:00" in report_content
        assert "**Source Strategy**: my_breakout_v1" in report_content
        assert "**Recommendation**: pivot" in report_content
        assert "## Stagnation Diagnosis" in report_content
        assert "- **cost_defeat** [high]: Trigger cost_defeat fired" in report_content
        assert "- **tail_risk** [high]: Trigger tail_risk fired" in report_content
        assert "## Pivot Proposals" in report_content

        # Check first proposal details
        assert (
            "### 1. pivot_my_breakout_v1_inv_cost_defeat_mean_reversion_pullback" in report_content
        )
        assert "**Technique**: assumption_inversion" in report_content
        assert "**Target Archetype**: mean_reversion_pullback" in report_content
        assert "**Entry Family**: research_only" in report_content
        assert "- signal: Inversion: horizon -> shorten" in report_content
        assert "**Why**: Reduce friction exposure" in report_content
        assert (
            "**Scores**: quality=0.80, novelty=0.60, combined=0.70" in report_content
        )  # Ensure scores are formatted correctly

        # Check second proposal details
        assert "### 2. pivot_my_breakout_v1_switch_volatility_contraction" in report_content
        assert "**Technique**: archetype_switch" in report_content
        assert "**Target Archetype**: volatility_contraction" in report_content
        assert "**Entry Family**: pivot_breakout" in report_content
        assert "- signal: Architecture switch" in report_content
        assert "**Why**: Structural pivot" in report_content
        assert (
            "**Scores**: quality=0.90, novelty=0.70, combined=0.80" in report_content
        )  # Ensure scores are formatted correctly

        # Check summary table
        assert "| Rank | Proposal | Archetype | Combined | Category |" in report_content
        assert "|------|----------|-----------|----------|----------|" in report_content
        assert (
            "| 1 | pivot_my_breakout_v1_inv_cost_defeat_mean_reversion_pullback | mean_reversion_pullback | 0.70 | research_only |"
            in report_content
        )
        assert (
            "| 2 | pivot_my_breakout_v1_switch_volatility_contraction | volatility_contraction | 0.80 | exportable |"
            in report_content
        )


# ---------------------------------------------------------------------------
# _build_base_draft tests
# ---------------------------------------------------------------------------


class TestBuildBaseDraft:
    @pytest.fixture
    def mock_datetime(self, mocker):
        """Mock datetime.now to ensure consistent 'as_of' dates."""
        fake_now = gp.datetime(2023, 1, 1, tzinfo=gp.timezone.utc)
        mocker.patch("generate_pivots.datetime", autospec=True)
        gp.datetime.now.return_value = fake_now
        gp.datetime.strftime = fake_now.strftime
        return fake_now

    def test_build_base_draft_defaults_and_inheritance(self, mock_datetime):
        source_draft = {
            "id": "source_strat_v1",
            "concept_id": "original_concept",
            "regime": "Bear",
            "thesis": "Original thesis",
            "invalidation_signals": ["sig_a", "sig_b"],
        }
        arch_id = "mean_reversion_pullback"
        arch_details = gp.ARCHETYPE_CATALOG[arch_id]
        proposal_id = "test_proposal_id"

        result = gp._build_base_draft(source_draft, arch_id, arch_details, proposal_id)

        assert result["id"] == proposal_id
        assert result["as_of"] == mock_datetime.strftime("%Y-%m-%d")
        assert result["concept_id"] == source_draft["concept_id"]
        assert result["variant"] == "research_probe"
        assert result["name"] == "Mean Reversion Pullback (pivoted from source_strat_v1)"
        assert result["hypothesis_type"] == arch_details["hypothesis_type"]
        assert result["mechanism_tag"] == arch_details["mechanism_tag"]
        assert result["regime"] == source_draft["regime"]
        assert result["entry_family"] == arch_details["entry_family"]

        # Check entry conditions from archetype
        assert result["entry"]["conditions"] == arch_details["default_conditions"]
        assert result["entry"]["trend_filter"] == arch_details["default_trend_filter"]

        # Check exit values from archetype defaults
        assert result["exit"]["stop_loss_pct"] == arch_details["default_stop_loss_pct"]
        assert result["exit"]["take_profit_rr"] == arch_details["default_take_profit_rr"]
        assert result["exit"]["time_stop_days"] == arch_details["default_time_stop_days"]

        # Check risk (hardcoded values in _build_base_draft)
        assert result["risk"]["position_sizing"] == "fixed_risk"
        assert result["risk"]["max_positions"] == 5

        # Check validation plan default criteria
        assert "expected_value_after_costs > 0" in result["validation_plan"]["success_criteria"]

        # Check inherited fields
        assert result["thesis"] == source_draft["thesis"]
        assert result["invalidation_signals"] == source_draft["invalidation_signals"]

    def test_build_base_draft_export_ready_flag(self, mock_datetime):
        source_draft = {"id": "source_strat_v1"}
        proposal_id = "test_proposal_id"

        # Test exportable archetype
        arch_id_exportable = "trend_following_breakout"  # entry_family: pivot_breakout
        arch_details_exportable = gp.ARCHETYPE_CATALOG[arch_id_exportable]
        result_exportable = gp._build_base_draft(
            source_draft, arch_id_exportable, arch_details_exportable, proposal_id
        )
        assert result_exportable["export_ready_v1"] is True

        # Test non-exportable archetype
        arch_id_research_only = "mean_reversion_pullback"  # entry_family: research_only
        arch_details_research_only = gp.ARCHETYPE_CATALOG[arch_id_research_only]
        result_research_only = gp._build_base_draft(
            source_draft, arch_id_research_only, arch_details_research_only, proposal_id
        )
        assert result_research_only["export_ready_v1"] is False

    def test_build_base_draft_validation_plan_hold_days(self, mock_datetime):
        source_draft = {"id": "source_strat_v1"}
        proposal_id = "test_proposal_id"

        # Test short hold days (<=14)
        arch_id_short_hold = "mean_reversion_pullback"  # default_time_stop_days: 7
        arch_details_short_hold = gp.ARCHETYPE_CATALOG[arch_id_short_hold]
        result_short = gp._build_base_draft(
            source_draft, arch_id_short_hold, arch_details_short_hold, proposal_id
        )
        assert result_short["validation_plan"]["hold_days"] == [3, 7, 14]

        # Test long hold days (>14)
        arch_id_long_hold = "regime_conditional_carry"  # default_time_stop_days: 60
        arch_details_long_hold = gp.ARCHETYPE_CATALOG[arch_id_long_hold]
        result_long = gp._build_base_draft(
            source_draft, arch_id_long_hold, arch_details_long_hold, proposal_id
        )
        assert result_long["validation_plan"]["hold_days"] == [5, 20, 60]


# ---------------------------------------------------------------------------
# CLI Integration Tests
# ---------------------------------------------------------------------------


class TestCliIntegration:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path, monkeypatch):
        self.tmp_path = tmp_path
        self.diagnosis_path = tmp_path / "diagnosis.json"
        self.strategy_path = tmp_path / "strategy.yaml"
        self.output_dir = tmp_path / "output"
        self.output_dir.mkdir()
        self.monkeypatch = monkeypatch
        self.monkeypatch.setattr("sys.stdout", open(os.devnull, "w"))  # Suppress stdout

    def _create_diagnosis_file(self, content):
        with open(self.diagnosis_path, "w") as f:
            json.dump(content, f)

    def _create_strategy_file(self, content):
        with open(self.strategy_path, "w") as f:
            yaml.safe_dump(content, f)

    def _run_main(self, extra_args=None):
        args = [
            "generate_pivots.py",
            "--diagnosis",
            str(self.diagnosis_path),
            "--strategy",
            str(self.strategy_path),
            "--output-dir",
            str(self.output_dir),
        ]
        if extra_args:
            args.extend(extra_args)
        self.monkeypatch.setattr("sys.argv", args)
        try:
            return gp.main()
        finally:
            self.monkeypatch.undo()  # Clean up the monkeypatch

    def test_main_missing_diagnosis_file_returns_error(self, capsys):
        self._create_strategy_file(_make_breakout_draft())
        exit_code = self._run_main()
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "diagnosis file not found" in captured.out

    def test_main_missing_strategy_file_returns_error(self, capsys):
        self._create_diagnosis_file({"strategy_id": "test", "triggers_fired": []})
        exit_code = self._run_main()
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "strategy file not found" in captured.out

    def test_main_no_triggers_fired_returns_zero(self):
        self._create_diagnosis_file({"strategy_id": "test", "triggers_fired": []})
        self._create_strategy_file(_make_breakout_draft())
        exit_code = self._run_main()
        assert exit_code == 0
        # No output files should be generated
        assert not any(self.output_dir.iterdir())

    def test_main_successful_execution_generates_files(self):
        self._create_diagnosis_file(
            {
                "strategy_id": "my_breakout_v1",
                "triggers_fired": [{"trigger": "cost_defeat", "severity": "high"}],
            }
        )
        self._create_strategy_file(_make_breakout_draft())
        exit_code = self._run_main()
        assert exit_code == 0
        # Check if output files are generated
        assert any(self.output_dir.glob("pivot_manifest_*.json"))
        assert any(self.output_dir.glob("pivot_report_*.md"))
        assert any(self.output_dir.glob("pivot_drafts/**/*.yaml"))

    def test_main_corrupt_strategy_file_returns_error(self, capsys):
        self._create_diagnosis_file(
            {
                "strategy_id": "my_breakout_v1",
                "triggers_fired": [{"trigger": "cost_defeat", "severity": "high"}],
            }
        )
        with open(self.strategy_path, "w") as f:
            f.write("{broken yaml!!!")
        exit_code = self._run_main()
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "strategy file is not valid YAML" in captured.out
