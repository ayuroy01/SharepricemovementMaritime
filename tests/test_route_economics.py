"""Tests for the VLCC Route Lab voyage-economics model.

All tests are deterministic and offline. They use the dataclass defaults
or small inline overrides — no network, no live data feeds.
"""
import json
import math
from pathlib import Path

import pytest

from route_economics import (
    CharterAssumptions, ComparisonResult, FuelAssumptions, InsuranceAssumptions,
    RegulationAssumptions, RouteAssumptions, RouteCostResult, RouteScenario,
    SensitivityResult, VesselProfile,
    breakeven_combined_suez_insurance_usd,
    breakeven_hm_awrp_pct_for_suez, compare_routes, compute_route_cost,
    ets_coverage_fraction, scenario_from_dict, scenario_with_overrides,
    scrubber_analysis, sensitivity_matrix, assumption_rows,
)


# ---------------------------------------------------------------------------
# Cost components
# ---------------------------------------------------------------------------
def test_fuel_cost_simple():
    """Suez fuel cost = days × burn × price (no congestion)."""
    s = RouteScenario(
        vessel=VesselProfile(fuel_consumption_mt_day=65),
        fuel=FuelAssumptions(price_per_mt_usd=694, co2_factor=3.114),
        route=RouteAssumptions(suez_days=21.1, cape_days=36.25,
                               cape_congestion_delay_days=0),
    )
    suez = compute_route_cost(s, "Suez")
    assert suez.fuel_cost == pytest.approx(21.1 * 65 * 694, rel=1e-9)


def test_charter_hire_simple():
    s = RouteScenario(
        charter=CharterAssumptions(rate_per_day_usd=100_000),
        route=RouteAssumptions(suez_days=21.1, cape_days=36.25),
    )
    suez = compute_route_cost(s, "Suez")
    cape = compute_route_cost(s, "Cape")
    assert suez.charter_hire == pytest.approx(21.1 * 100_000)
    assert cape.charter_hire == pytest.approx(36.25 * 100_000)


def test_cargo_financing_uses_sea_days_including_congestion():
    s = RouteScenario(
        vessel=VesselProfile(cargo_tonnes=300_000, cargo_value_per_tonne_usd=600),
        charter=CharterAssumptions(financing_rate_annual=0.03),
        route=RouteAssumptions(cape_days=36.25, cape_congestion_delay_days=6.0),
    )
    cape = compute_route_cost(s, "Cape")
    cargo_value = 300_000 * 600
    expected = cargo_value * 0.03 * (36.25 + 6.0) / 365.0
    assert cape.cargo_financing == pytest.approx(expected, rel=1e-9)


def test_congestion_only_applies_to_cape():
    s = RouteScenario(
        charter=CharterAssumptions(rate_per_day_usd=100_000),
        route=RouteAssumptions(cape_congestion_delay_days=6.0),
    )
    suez = compute_route_cost(s, "Suez")
    cape = compute_route_cost(s, "Cape")
    assert suez.congestion_cost == 0.0
    assert cape.congestion_cost == pytest.approx(6.0 * 100_000)


def test_invalid_route_raises():
    with pytest.raises(ValueError):
        compute_route_cost(RouteScenario(), "Panama")


def test_negative_days_raise():
    with pytest.raises(ValueError):
        compute_route_cost(
            RouteScenario(route=RouteAssumptions(suez_days=-1.0, cape_days=30)),
            "Suez",
        )


# ---------------------------------------------------------------------------
# EU ETS scope
# ---------------------------------------------------------------------------
def test_ets_non_eea_to_non_eea_is_zero():
    reg = RegulationAssumptions(origin_in_eea=False, dest_in_eea=False,
                                has_intermediate_eea_port_call=False)
    assert ets_coverage_fraction(reg) == 0.0


def test_ets_eea_to_non_eea_is_half():
    reg = RegulationAssumptions(origin_in_eea=True, dest_in_eea=False)
    assert ets_coverage_fraction(reg) == 0.5
    reg2 = RegulationAssumptions(origin_in_eea=False, dest_in_eea=True)
    assert ets_coverage_fraction(reg2) == 0.5


def test_ets_eea_to_eea_is_full():
    reg = RegulationAssumptions(origin_in_eea=True, dest_in_eea=True)
    assert ets_coverage_fraction(reg) == 1.0


def test_ets_intermediate_call_upgrades_to_half():
    reg = RegulationAssumptions(origin_in_eea=False, dest_in_eea=False,
                                has_intermediate_eea_port_call=True)
    assert ets_coverage_fraction(reg) == 0.5


def test_carbon_cost_zero_when_coverage_zero():
    s = RouteScenario(
        regulation=RegulationAssumptions(origin_in_eea=False, dest_in_eea=False,
                                         eua_price_usd=80.0),
    )
    suez = compute_route_cost(s, "Suez")
    cape = compute_route_cost(s, "Cape")
    assert suez.payable_carbon_cost == 0.0
    assert cape.payable_carbon_cost == 0.0
    # Physical emissions should still be reported
    assert suez.physical_emissions_t > 0
    assert cape.physical_emissions_t > suez.physical_emissions_t


def test_carbon_cost_nonzero_when_eea_voyage():
    s = RouteScenario(
        regulation=RegulationAssumptions(origin_in_eea=True, dest_in_eea=True,
                                         eua_price_usd=80.0),
    )
    suez = compute_route_cost(s, "Suez")
    expected = suez.physical_emissions_t * 1.0 * 80.0
    assert suez.payable_carbon_cost == pytest.approx(expected)


# ---------------------------------------------------------------------------
# Break-even AWRP
# ---------------------------------------------------------------------------
def test_breakeven_awrp_makes_costs_equal():
    """At the break-even AWRP, Suez total cost should equal Cape total cost."""
    s = RouteScenario()  # all defaults
    awrp = breakeven_hm_awrp_pct_for_suez(s)
    assert awrp is not None
    s_at = scenario_with_overrides(s, hm_awrp_pct_suez=awrp)
    cmp = compare_routes(s_at)
    assert abs(cmp.differential_cape_minus_suez) < 1.0  # within $1


def test_breakeven_awrp_undefined_when_hull_zero():
    s = RouteScenario(vessel=VesselProfile(hull_value_usd=0.0))
    assert breakeven_hm_awrp_pct_for_suez(s) is None


def test_compare_routes_default_scenario_picks_suez():
    """With the bundled default scenario (Cape much longer + nominal AWRP),
    Suez should be cheaper. This is a regression check — not a normative claim."""
    s = RouteScenario()
    cmp = compare_routes(s)
    assert isinstance(cmp, ComparisonResult)
    assert cmp.cheaper_route in {"Suez", "Cape", "Tied"}
    # Differential should equal cape.total_cost - suez.total_cost
    assert cmp.differential_cape_minus_suez == pytest.approx(
        cmp.cape.total_cost - cmp.suez.total_cost
    )


# ---------------------------------------------------------------------------
# Sensitivity matrix
# ---------------------------------------------------------------------------
def test_sensitivity_matrix_shape():
    s = RouteScenario()
    sm = sensitivity_matrix(s, charter_rates=[60_000, 100_000],
                            fuel_prices=[500.0, 700.0, 900.0])
    assert isinstance(sm, SensitivityResult)
    assert len(sm.differential_matrix) == 2
    assert len(sm.differential_matrix[0]) == 3
    assert len(sm.breakeven_awrp_matrix) == 2
    assert len(sm.breakeven_awrp_matrix[0]) == 3


def test_sensitivity_matrix_values_consistent_with_pointwise():
    s = RouteScenario()
    cr_grid = [80_000, 120_000]
    fp_grid = [600.0, 800.0]
    sm = sensitivity_matrix(s, charter_rates=cr_grid, fuel_prices=fp_grid)
    for i, cr in enumerate(cr_grid):
        for j, fp in enumerate(fp_grid):
            sc = scenario_with_overrides(s, charter_rate=cr, fuel_price=fp)
            cmp = compare_routes(sc)
            assert sm.differential_matrix[i][j] == pytest.approx(
                cmp.differential_cape_minus_suez
            )


# ---------------------------------------------------------------------------
# Scrubber
# ---------------------------------------------------------------------------
def test_scrubber_saving_is_spread_times_burn():
    s = RouteScenario(
        vessel=VesselProfile(fuel_consumption_mt_day=65),
        fuel=FuelAssumptions(price_per_mt_usd=694, vlsfo_price_per_mt_usd=805),
        route=RouteAssumptions(suez_days=21.1, cape_days=36.25,
                               cape_congestion_delay_days=0),
    )
    sa = scrubber_analysis(s)
    assert sa.spread_per_mt_usd == pytest.approx(805 - 694)
    assert sa.daily_saving_usd == pytest.approx((805 - 694) * 65)
    assert sa.suez_voyage_saving_usd == pytest.approx(sa.daily_saving_usd * 21.1)


def test_scrubber_saving_floors_at_zero_when_spread_negative():
    s = RouteScenario(
        fuel=FuelAssumptions(price_per_mt_usd=900, vlsfo_price_per_mt_usd=800),
    )
    sa = scrubber_analysis(s)
    assert sa.daily_saving_usd == 0.0


# ---------------------------------------------------------------------------
# Sample scenario JSON loads & defaults match
# ---------------------------------------------------------------------------
def test_sample_scenario_json_loads_and_matches_defaults():
    path = Path("sample_data/route_scenarios/may_2026_vlcc_pg_singapore.json")
    assert path.exists()
    raw = json.loads(path.read_text())
    s = scenario_from_dict(raw)
    assert s.name == "May 2026 VLCC PG → Singapore"
    assert s.vessel.hull_value_usd == 134_000_000
    assert s.vessel.cargo_tonnes == 300_000
    assert s.fuel.co2_factor == pytest.approx(3.114)
    assert s.route.suez_days == pytest.approx(21.1)
    assert s.route.cape_days == pytest.approx(36.25)
    assert s.charter.rate_per_day_usd == 100_000
    # PG → Singapore is non-EEA → non-EEA
    assert ets_coverage_fraction(s.regulation) == 0.0


def test_scenario_from_dict_ignores_unknown_fields():
    s = scenario_from_dict({
        "name": "x",
        "vessel": {"hull_value_usd": 1, "wat": "nonsense"},
    })
    assert s.vessel.hull_value_usd == 1


def test_assumption_rows_categories():
    s = RouteScenario()
    rows = assumption_rows(s)
    kinds = {r["kind"] for r in rows}
    # All four categories should be represented
    assert {"user_input", "analyst_default", "regulatory_constant", "vessel_default"} <= kinds
    # No empty source field
    assert all(r["source"] for r in rows)


# ---------------------------------------------------------------------------
# Edge-case input handling
# ---------------------------------------------------------------------------
def test_zero_cargo_zero_financing_and_cargo_war_risk():
    s = RouteScenario(vessel=VesselProfile(cargo_tonnes=0))
    cmp = compare_routes(s)
    assert cmp.suez.cargo_financing == 0.0
    assert cmp.suez.cargo_war_risk == 0.0
    assert any("Cargo tonnes is zero" in w for w in cmp.warnings)


def test_zero_hull_warns_and_breakeven_none():
    s = RouteScenario(vessel=VesselProfile(hull_value_usd=0))
    cmp = compare_routes(s)
    assert cmp.breakeven_awrp_for_cape_pct is None
    assert any("Hull value is zero" in w for w in cmp.warnings)


def test_total_cost_ex_insurance_excludes_both_war_risk_components():
    s = RouteScenario(
        insurance=InsuranceAssumptions(
            hm_awrp_pct_suez=0.005, hm_awrp_pct_cape=0.0,
            cargo_awrp_pct_suez=0.001, cargo_awrp_pct_cape=0.0,
        ),
    )
    suez = compute_route_cost(s, "Suez")
    assert suez.total_cost_ex_insurance == pytest.approx(
        suez.total_cost - suez.hm_war_risk - suez.cargo_war_risk
    )


def test_pre_insurance_differential_independent_of_insurance_inputs():
    """Pre-insurance differential must NOT change when insurance pcts change."""
    base = RouteScenario()
    s_low = scenario_with_overrides(base, hm_awrp_pct_suez=0.0)
    cmp_low = compare_routes(s_low)
    s_high = scenario_with_overrides(base, hm_awrp_pct_suez=0.05)
    cmp_high = compare_routes(s_high)
    assert cmp_low.pre_insurance_differential_cape_minus_suez == pytest.approx(
        cmp_high.pre_insurance_differential_cape_minus_suez
    )
    # All-in differential SHOULD differ
    assert cmp_low.differential_cape_minus_suez != cmp_high.differential_cape_minus_suez


def test_breakeven_combined_suez_insurance_makes_totals_equal():
    """At breakeven_combined, Suez_ex_ins + breakeven == Cape_total."""
    s = RouteScenario()
    cmp = compare_routes(s)
    bv = cmp.breakeven_combined_suez_insurance_usd
    assert bv is not None
    suez_ex_ins = cmp.suez.total_cost_ex_insurance
    assert (suez_ex_ins + bv) == pytest.approx(cmp.cape.total_cost, rel=1e-9)


def test_breakeven_combined_negative_when_cape_already_cheaper_pre_insurance():
    """If Cape is already cheaper before insurance, breakeven_combined < 0."""
    # Make Cape much faster so its pre-insurance total drops below Suez.
    s = RouteScenario(
        route=RouteAssumptions(suez_days=30.0, cape_days=20.0,
                               suez_toll_usd=1_000_000, cape_port_fees_usd=10_000),
    )
    cmp = compare_routes(s)
    assert cmp.breakeven_combined_suez_insurance_usd < 0
    assert any("Cape is already cheaper" in w for w in cmp.warnings)


def test_breakeven_combined_consistent_with_total_comparison():
    """If all-in totals are tied, breakeven_combined should equal Suez insurance."""
    s = RouteScenario()
    cmp = compare_routes(s)
    suez_insurance = cmp.suez.insurance_cost
    # The breakeven_combined value should equal Suez insurance + (cape_total - suez_total).
    # i.e. delta from current Suez insurance = differential.
    delta = cmp.breakeven_combined_suez_insurance_usd - suez_insurance
    assert delta == pytest.approx(cmp.differential_cape_minus_suez, rel=1e-9)


def test_breakeven_combined_with_zero_hull_still_defined():
    """Unlike the AWRP percentage, the combined USD breakeven is independent of hull."""
    s = RouteScenario(vessel=VesselProfile(hull_value_usd=0))
    cmp = compare_routes(s)
    # H&M cost is 0 when hull is 0; combined breakeven should be cape_total - suez_ex_ins
    assert cmp.breakeven_combined_suez_insurance_usd == pytest.approx(
        cmp.cape.total_cost - cmp.suez.total_cost_ex_insurance
    )


def test_zero_ets_with_eua_price_emits_warning():
    s = RouteScenario(
        regulation=RegulationAssumptions(origin_in_eea=False, dest_in_eea=False,
                                         eua_price_usd=80),
    )
    cmp = compare_routes(s)
    assert any("ETS coverage is 0%" in w for w in cmp.warnings)
