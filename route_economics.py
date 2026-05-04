"""VLCC Route Lab — Cape of Good Hope vs Suez Canal voyage economics.

This module is a deterministic *calculator*. It takes user-editable
scenario inputs and returns a per-route cost breakdown plus a
sensitivity matrix and break-even AWRP. It does NOT prescribe routing,
investment, or insurance decisions.

Default scenario values reflect a teammate's analytical brief for
"Persian Gulf → Singapore VLCC, May 2026". They are explicitly labelled
in `sample_data/route_scenarios/...` as "editable analyst scenario"
with source placeholders. None of the values are pulled from a live
market feed — see provider placeholders in `providers.paid_provider_status()`.

EU ETS scope rules implemented per the European Commission's maritime
ETS framework: 100% emissions for EEA ↔ EEA voyages, 50% for EEA ↔
non-EEA, 0% for non-EEA ↔ non-EEA. Citations are listed in the README
and `sample_data/route_scenarios/.../sources`.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------
@dataclass
class VesselProfile:
    hull_value_usd: float = 134_000_000.0
    cargo_tonnes: float = 300_000.0
    cargo_value_per_tonne_usd: float = 600.0   # → ~180m USD cargo at $600/t (editable)
    fuel_consumption_mt_day: float = 65.0
    scrubber_equipped: bool = False

    @property
    def cargo_value_usd(self) -> float:
        return self.cargo_tonnes * self.cargo_value_per_tonne_usd


@dataclass
class FuelAssumptions:
    grade: str = "IFO380"            # IFO380/HSFO | VLSFO | LSMGO
    price_per_mt_usd: float = 694.0
    # Used for scrubber spread analysis: VLSFO price reference
    vlsfo_price_per_mt_usd: float = 805.0
    # Tonnes CO2 per tonne fuel — IPCC defaults; configurable.
    co2_factor: float = 3.114        # IFO380/HSFO; VLSFO/LSMGO ≈ 3.151


@dataclass
class CharterAssumptions:
    rate_per_day_usd: float = 100_000.0
    financing_rate_annual: float = 0.03   # 3% APR on cargo value


@dataclass
class InsuranceAssumptions:
    # Hull & Machinery Additional War Risk Premium, applied to hull value.
    hm_awrp_pct_suez: float = 0.005   # 0.5% per voyage
    hm_awrp_pct_cape: float = 0.0
    # Cargo war-risk applied to cargo value.
    cargo_awrp_pct_suez: float = 0.001
    cargo_awrp_pct_cape: float = 0.0


@dataclass
class RouteAssumptions:
    suez_days: float = 21.1
    cape_days: float = 36.25
    suez_toll_usd: float = 640_000.0
    cape_port_fees_usd: float = 13_333.0    # bunkering / pilotage stop
    cape_congestion_delay_days: float = 0.0  # stress test: try 6 days


@dataclass
class RegulationAssumptions:
    origin_in_eea: bool = False
    dest_in_eea: bool = False
    has_intermediate_eea_port_call: bool = False
    eua_price_usd: float = 80.0       # per tonne CO2; only relevant if coverage > 0


@dataclass
class RouteScenario:
    name: str = "May 2026 VLCC PG → Singapore"
    label: str = "Editable analyst scenario, not live market data"
    last_reviewed: str = "2026-05-02"
    vessel: VesselProfile = field(default_factory=VesselProfile)
    fuel: FuelAssumptions = field(default_factory=FuelAssumptions)
    charter: CharterAssumptions = field(default_factory=CharterAssumptions)
    insurance: InsuranceAssumptions = field(default_factory=InsuranceAssumptions)
    route: RouteAssumptions = field(default_factory=RouteAssumptions)
    regulation: RegulationAssumptions = field(default_factory=RegulationAssumptions)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RouteCostResult:
    route: str               # "Suez" | "Cape"
    voyage_days: float
    fuel_cost: float
    tolls_or_fees: float
    charter_hire: float
    congestion_cost: float
    cargo_financing: float
    hm_war_risk: float
    cargo_war_risk: float
    physical_emissions_t: float   # tonnes CO2 emitted
    regulated_emissions_t: float  # tonnes CO2 in scope of EU ETS
    payable_carbon_cost: float    # USD (regulated_emissions × EUA × phase-in if any)
    total_cost: float
    components: Dict[str, float] = field(default_factory=dict)

    @property
    def insurance_cost(self) -> float:
        return self.hm_war_risk + self.cargo_war_risk

    @property
    def total_cost_ex_insurance(self) -> float:
        """Total cost MINUS H&M war-risk MINUS cargo war-risk.

        Useful for comparing routes before applying insurance/risk
        premiums — i.e. "how much extra Suez risk-cost can be tolerated
        before Cape wins on price?"
        """
        return self.total_cost - self.insurance_cost

    def as_row(self) -> Dict[str, Any]:
        return {
            "route": self.route,
            "voyage_days": self.voyage_days,
            "fuel": self.fuel_cost,
            "tolls/port fees": self.tolls_or_fees,
            "charter hire": self.charter_hire,
            "congestion": self.congestion_cost,
            "cargo financing": self.cargo_financing,
            "H&M war-risk": self.hm_war_risk,
            "cargo war-risk": self.cargo_war_risk,
            "carbon (ETS payable)": self.payable_carbon_cost,
            "total": self.total_cost,
            "total ex-insurance": self.total_cost_ex_insurance,
        }


@dataclass
class ComparisonResult:
    suez: RouteCostResult
    cape: RouteCostResult
    # All-in totals (current assumptions, including insurance entered).
    differential_cape_minus_suez: float
    cheaper_route: str           # "Suez" | "Cape" | "Tied" — based on all-in totals
    # Pre-insurance comparison (excludes H&M and cargo war-risk on both sides).
    pre_insurance_differential_cape_minus_suez: float
    cheaper_route_ex_insurance: str
    # Break-even thresholds:
    #   _pct  : H&M AWRP on Suez (% of hull) at which all-in Suez = all-in Cape
    #   _usd  : combined Suez insurance/risk cost (USD) at which Suez_ex_ins +
    #           that cost = Cape_total. ≈ teammate brief's break-even framing.
    breakeven_awrp_for_cape_pct: Optional[float]
    breakeven_combined_suez_insurance_usd: Optional[float]
    warnings: List[str] = field(default_factory=list)


@dataclass
class SensitivityResult:
    charter_rates: List[float]
    fuel_prices: List[float]
    differential_matrix: List[List[float]]   # shape: charter_rates × fuel_prices, Cape − Suez
    breakeven_awrp_matrix: List[List[Optional[float]]]


# ---------------------------------------------------------------------------
# EU ETS scope validator
# ---------------------------------------------------------------------------
def ets_coverage_fraction(reg: RegulationAssumptions) -> float:
    """Fraction (0..1) of voyage emissions in scope of EU ETS.

    Rules (per EC maritime ETS scope):
      - EEA ↔ EEA           : 1.0
      - EEA ↔ non-EEA       : 0.5
      - non-EEA ↔ non-EEA   : 0.0
    An intermediate EEA port call upgrades the voyage to ≥ 0.5 coverage.
    Berth emissions inside an EEA port are 100% in scope (handled via
    `has_intermediate_eea_port_call` for simplicity in this model).

    NOTE: The ETS phase-in (40% of regulated emissions in 2024, 70% in
    2025, 100% from 2026) is *not* applied here — the EUA price input
    multiplies the full regulated tonnage. From 2026 onwards this matches
    the regulatory regime; for earlier years, scale `eua_price_usd`
    accordingly.
    """
    o, d, mid = reg.origin_in_eea, reg.dest_in_eea, reg.has_intermediate_eea_port_call
    if o and d:
        return 1.0
    if o or d or mid:
        return 0.5
    return 0.0


# ---------------------------------------------------------------------------
# Per-route cost computation
# ---------------------------------------------------------------------------
def _safe_pct(v: Optional[float]) -> float:
    return float(v) if v is not None else 0.0


def _scrubber_adjusted_fuel_price(fuel: FuelAssumptions, vessel: VesselProfile) -> float:
    """If the vessel is scrubber-equipped, it burns HSFO/IFO380 instead of
    the more expensive VLSFO. The "scrubber spread" saving is captured
    only when the chosen grade is HSFO/IFO380. We do NOT alter physical
    emissions — both fuels emit similarly per tonne.
    """
    if vessel.scrubber_equipped and fuel.grade.upper() in {"HSFO", "IFO380"}:
        return fuel.price_per_mt_usd
    return fuel.price_per_mt_usd


def compute_route_cost(
    scenario: RouteScenario, route: str,
) -> RouteCostResult:
    """Compute a full cost breakdown for one route ('Suez' or 'Cape')."""
    if route not in {"Suez", "Cape"}:
        raise ValueError(f"route must be 'Suez' or 'Cape', got {route!r}")

    days = scenario.route.suez_days if route == "Suez" else scenario.route.cape_days
    if days < 0:
        raise ValueError("voyage days must be non-negative")
    congestion_days = scenario.route.cape_congestion_delay_days if route == "Cape" else 0.0
    congestion_days = max(congestion_days, 0.0)

    fuel_price = _scrubber_adjusted_fuel_price(scenario.fuel, scenario.vessel)
    sea_days = days + congestion_days
    fuel_cost = sea_days * scenario.vessel.fuel_consumption_mt_day * fuel_price

    tolls_or_fees = scenario.route.suez_toll_usd if route == "Suez" else scenario.route.cape_port_fees_usd
    charter_hire = days * scenario.charter.rate_per_day_usd
    congestion_cost = congestion_days * scenario.charter.rate_per_day_usd

    cargo_value = scenario.vessel.cargo_value_usd
    cargo_financing = (
        cargo_value * scenario.charter.financing_rate_annual * sea_days / 365.0
        if cargo_value > 0 else 0.0
    )

    if route == "Suez":
        hm_pct = _safe_pct(scenario.insurance.hm_awrp_pct_suez)
        cargo_pct = _safe_pct(scenario.insurance.cargo_awrp_pct_suez)
    else:
        hm_pct = _safe_pct(scenario.insurance.hm_awrp_pct_cape)
        cargo_pct = _safe_pct(scenario.insurance.cargo_awrp_pct_cape)
    hm_war_risk = scenario.vessel.hull_value_usd * hm_pct
    cargo_war_risk = cargo_value * cargo_pct

    physical_emissions_t = sea_days * scenario.vessel.fuel_consumption_mt_day * scenario.fuel.co2_factor
    coverage = ets_coverage_fraction(scenario.regulation)
    regulated_emissions_t = physical_emissions_t * coverage
    payable_carbon = regulated_emissions_t * scenario.regulation.eua_price_usd

    total = (
        fuel_cost + tolls_or_fees + charter_hire + congestion_cost
        + cargo_financing + hm_war_risk + cargo_war_risk + payable_carbon
    )

    return RouteCostResult(
        route=route,
        voyage_days=days,
        fuel_cost=fuel_cost,
        tolls_or_fees=tolls_or_fees,
        charter_hire=charter_hire,
        congestion_cost=congestion_cost,
        cargo_financing=cargo_financing,
        hm_war_risk=hm_war_risk,
        cargo_war_risk=cargo_war_risk,
        physical_emissions_t=physical_emissions_t,
        regulated_emissions_t=regulated_emissions_t,
        payable_carbon_cost=payable_carbon,
        total_cost=total,
        components={
            "fuel": fuel_cost,
            "tolls_or_fees": tolls_or_fees,
            "charter_hire": charter_hire,
            "congestion": congestion_cost,
            "cargo_financing": cargo_financing,
            "hm_war_risk": hm_war_risk,
            "cargo_war_risk": cargo_war_risk,
            "carbon": payable_carbon,
        },
    )


# ---------------------------------------------------------------------------
# Comparison + break-even AWRP
# ---------------------------------------------------------------------------
def breakeven_hm_awrp_pct_for_suez(scenario: RouteScenario) -> Optional[float]:
    """The H&M AWRP on Suez at which total Suez cost equals total Cape cost.

    Solve:  cost_suez(awrp) = cost_cape
            cost_suez_base + hull_value × awrp = cost_cape
            awrp = (cost_cape - cost_suez_base) / hull_value

    Returns None if hull value is zero. Negative values mean Cape is
    already more expensive even at zero AWRP — Suez wins unconditionally.
    """
    if scenario.vessel.hull_value_usd <= 0:
        return None
    cape = compute_route_cost(scenario, "Cape")
    # Suez cost without the H&M AWRP component (set to 0 just for the base).
    base = scenario_with_overrides(scenario, hm_awrp_pct_suez=0.0)
    suez_base = compute_route_cost(base, "Suez").total_cost
    return (cape.total_cost - suez_base) / scenario.vessel.hull_value_usd


def breakeven_combined_suez_insurance_usd(scenario: RouteScenario) -> Optional[float]:
    """Total combined Suez insurance/risk cost (USD) at which Suez ties Cape.

    Defined as:
        breakeven_combined = cape.total_cost − suez.total_cost_ex_insurance

    i.e. "given everything else, how much risk-related cost can be loaded
    onto the Suez voyage before Cape becomes cheaper than Suez?"

    A NEGATIVE return value means Cape is already cheaper than Suez even
    BEFORE any Suez insurance is applied — Suez cannot justify any
    insurance load. UI should surface this as a special case.

    Returns None if the comparison cannot be made.
    """
    cape = compute_route_cost(scenario, "Cape")
    suez = compute_route_cost(scenario, "Suez")
    return cape.total_cost - suez.total_cost_ex_insurance


def compare_routes(scenario: RouteScenario) -> ComparisonResult:
    suez = compute_route_cost(scenario, "Suez")
    cape = compute_route_cost(scenario, "Cape")
    diff = cape.total_cost - suez.total_cost
    if abs(diff) < 1.0:
        cheaper = "Tied"
    else:
        cheaper = "Suez" if diff > 0 else "Cape"

    pre_ins_diff = cape.total_cost_ex_insurance - suez.total_cost_ex_insurance
    if abs(pre_ins_diff) < 1.0:
        cheaper_pre_ins = "Tied"
    else:
        cheaper_pre_ins = "Suez" if pre_ins_diff > 0 else "Cape"

    breakeven_pct = breakeven_hm_awrp_pct_for_suez(scenario)
    breakeven_usd = breakeven_combined_suez_insurance_usd(scenario)

    warnings: List[str] = []
    if scenario.vessel.cargo_tonnes <= 0:
        warnings.append("Cargo tonnes is zero — financing and cargo-war-risk components will be zero.")
    if scenario.vessel.hull_value_usd <= 0:
        warnings.append("Hull value is zero — break-even AWRP (% of hull) is undefined.")
    cov = ets_coverage_fraction(scenario.regulation)
    if cov == 0 and scenario.regulation.eua_price_usd > 0:
        warnings.append(
            "EU ETS coverage is 0% for this voyage. The EUA price input "
            "does not affect payable carbon cost. (Physical emissions are "
            "still reported in the Regulation tab.)"
        )
    if breakeven_usd is not None and breakeven_usd < 0:
        warnings.append(
            "Cape is already cheaper than Suez BEFORE any Suez insurance — "
            "no Suez risk-cost can be tolerated under current assumptions."
        )
    return ComparisonResult(
        suez=suez, cape=cape,
        differential_cape_minus_suez=diff,
        cheaper_route=cheaper,
        pre_insurance_differential_cape_minus_suez=pre_ins_diff,
        cheaper_route_ex_insurance=cheaper_pre_ins,
        breakeven_awrp_for_cape_pct=breakeven_pct,
        breakeven_combined_suez_insurance_usd=breakeven_usd,
        warnings=warnings,
    )


# ---------------------------------------------------------------------------
# Sensitivity matrix
# ---------------------------------------------------------------------------
def sensitivity_matrix(
    scenario: RouteScenario,
    charter_rates: Optional[List[float]] = None,
    fuel_prices: Optional[List[float]] = None,
) -> SensitivityResult:
    """Compute Cape-minus-Suez differential and break-even AWRP for each
    (charter_rate, fuel_price) pair.
    """
    charter_rates = charter_rates or [60_000, 90_000, 100_000, 120_000]
    fuel_prices = fuel_prices or [535.0, 694.0, 900.0]

    diff: List[List[float]] = []
    awrp: List[List[Optional[float]]] = []
    for cr in charter_rates:
        diff_row: List[float] = []
        awrp_row: List[Optional[float]] = []
        for fp in fuel_prices:
            sc = scenario_with_overrides(scenario, charter_rate=cr, fuel_price=fp)
            cmp = compare_routes(sc)
            diff_row.append(cmp.differential_cape_minus_suez)
            awrp_row.append(cmp.breakeven_awrp_for_cape_pct)
        diff.append(diff_row)
        awrp.append(awrp_row)
    return SensitivityResult(
        charter_rates=list(charter_rates),
        fuel_prices=list(fuel_prices),
        differential_matrix=diff,
        breakeven_awrp_matrix=awrp,
    )


# ---------------------------------------------------------------------------
# Scrubber economics
# ---------------------------------------------------------------------------
@dataclass
class ScrubberAnalysis:
    daily_saving_usd: float
    suez_voyage_saving_usd: float
    cape_voyage_saving_usd: float
    spread_per_mt_usd: float
    note: str = (
        "Scrubber saving = (VLSFO − HSFO) × daily consumption. "
        "Assumes scrubber operating cost is negligible at this aggregation level."
    )


def scrubber_analysis(scenario: RouteScenario) -> ScrubberAnalysis:
    spread = scenario.fuel.vlsfo_price_per_mt_usd - scenario.fuel.price_per_mt_usd
    daily = max(spread, 0.0) * scenario.vessel.fuel_consumption_mt_day
    return ScrubberAnalysis(
        daily_saving_usd=daily,
        suez_voyage_saving_usd=daily * scenario.route.suez_days,
        cape_voyage_saving_usd=daily * (scenario.route.cape_days
                                        + max(scenario.route.cape_congestion_delay_days, 0.0)),
        spread_per_mt_usd=spread,
    )


# ---------------------------------------------------------------------------
# Scenario override helper (immutable-style)
# ---------------------------------------------------------------------------
def scenario_with_overrides(
    base: RouteScenario,
    *,
    charter_rate: Optional[float] = None,
    fuel_price: Optional[float] = None,
    hm_awrp_pct_suez: Optional[float] = None,
    cape_congestion_days: Optional[float] = None,
) -> RouteScenario:
    """Return a shallow-cloned scenario with the given fields overridden.

    Avoids mutating the base scenario so the dashboard can re-use it.
    """
    sc = RouteScenario(
        name=base.name, label=base.label, last_reviewed=base.last_reviewed,
        vessel=VesselProfile(**asdict(base.vessel)),
        fuel=FuelAssumptions(**asdict(base.fuel)),
        charter=CharterAssumptions(**asdict(base.charter)),
        insurance=InsuranceAssumptions(**asdict(base.insurance)),
        route=RouteAssumptions(**asdict(base.route)),
        regulation=RegulationAssumptions(**asdict(base.regulation)),
        notes=list(base.notes),
    )
    if charter_rate is not None:
        sc.charter.rate_per_day_usd = float(charter_rate)
    if fuel_price is not None:
        sc.fuel.price_per_mt_usd = float(fuel_price)
    if hm_awrp_pct_suez is not None:
        sc.insurance.hm_awrp_pct_suez = float(hm_awrp_pct_suez)
    if cape_congestion_days is not None:
        sc.route.cape_congestion_delay_days = float(cape_congestion_days)
    return sc


# ---------------------------------------------------------------------------
# Scenario loader
# ---------------------------------------------------------------------------
def scenario_from_dict(d: Dict[str, Any]) -> RouteScenario:
    """Construct a RouteScenario from a JSON-style dict.

    Unknown fields are ignored; missing fields take dataclass defaults.
    """
    def _sub(cls, key):
        raw = d.get(key, {}) or {}
        valid = {f.name for f in cls.__dataclass_fields__.values()}
        clean = {k: v for k, v in raw.items() if k in valid}
        return cls(**clean)

    return RouteScenario(
        name=d.get("name", "Custom scenario"),
        label=d.get("label", "Editable analyst scenario, not live market data"),
        last_reviewed=d.get("last_reviewed", ""),
        vessel=_sub(VesselProfile, "vessel"),
        fuel=_sub(FuelAssumptions, "fuel"),
        charter=_sub(CharterAssumptions, "charter"),
        insurance=_sub(InsuranceAssumptions, "insurance"),
        route=_sub(RouteAssumptions, "route"),
        regulation=_sub(RegulationAssumptions, "regulation"),
        notes=list(d.get("notes", [])),
    )


# ---------------------------------------------------------------------------
# Source/assumption registry — for the Assumptions & Sources sub-tab
# ---------------------------------------------------------------------------
def assumption_rows(scenario: RouteScenario) -> List[Dict[str, Any]]:
    """Flatten the scenario into a (key, value, kind, source) table.

    `kind` is one of:
      - "user_input"            : user-editable on the dashboard
      - "analyst_default"       : provisional default from the brief
      - "regulatory_constant"   : sourced from a regulator (EU ETS rules)
      - "vessel_default"        : engineering / accounting default
    """
    rows: List[Dict[str, Any]] = [
        # Vessel
        {"section": "Vessel", "key": "hull_value_usd",
         "value": scenario.vessel.hull_value_usd, "kind": "analyst_default",
         "source": "Analyst brief — verify against newbuild/sale comparables"},
        {"section": "Vessel", "key": "cargo_tonnes",
         "value": scenario.vessel.cargo_tonnes, "kind": "vessel_default",
         "source": "Typical VLCC dwt ~300,000 mt"},
        {"section": "Vessel", "key": "cargo_value_per_tonne_usd",
         "value": scenario.vessel.cargo_value_per_tonne_usd, "kind": "user_input",
         "source": "User-editable; placeholder reflects mid-2026 crude indication"},
        {"section": "Vessel", "key": "fuel_consumption_mt_day",
         "value": scenario.vessel.fuel_consumption_mt_day, "kind": "vessel_default",
         "source": "Typical VLCC laden burn at ~13kn; ship-specific"},
        {"section": "Vessel", "key": "scrubber_equipped",
         "value": scenario.vessel.scrubber_equipped, "kind": "user_input",
         "source": "Vessel-specific"},

        # Fuel
        {"section": "Fuel", "key": "grade",
         "value": scenario.fuel.grade, "kind": "user_input", "source": "User-editable"},
        {"section": "Fuel", "key": "price_per_mt_usd",
         "value": scenario.fuel.price_per_mt_usd, "kind": "analyst_default",
         "source": "Bunker price source NOT configured — see provider placeholders"},
        {"section": "Fuel", "key": "vlsfo_price_per_mt_usd",
         "value": scenario.fuel.vlsfo_price_per_mt_usd, "kind": "analyst_default",
         "source": "Bunker price source NOT configured"},
        {"section": "Fuel", "key": "co2_factor",
         "value": scenario.fuel.co2_factor, "kind": "regulatory_constant",
         "source": "IPCC default emission factor for HFO ≈ 3.114 t CO2 / t fuel"},

        # Charter
        {"section": "Charter", "key": "rate_per_day_usd",
         "value": scenario.charter.rate_per_day_usd, "kind": "analyst_default",
         "source": "Analyst brief — verify against TCE feed (not configured)"},
        {"section": "Charter", "key": "financing_rate_annual",
         "value": scenario.charter.financing_rate_annual, "kind": "user_input",
         "source": "User-editable; trade-finance benchmark"},

        # Insurance
        {"section": "Insurance", "key": "hm_awrp_pct_suez",
         "value": scenario.insurance.hm_awrp_pct_suez, "kind": "user_input",
         "source": "Underwriter quote — placeholder; varies materially by hull and risk"},
        {"section": "Insurance", "key": "hm_awrp_pct_cape",
         "value": scenario.insurance.hm_awrp_pct_cape, "kind": "user_input",
         "source": "Cape route AWRP often nominal/zero; verify with broker"},
        {"section": "Insurance", "key": "cargo_awrp_pct_suez",
         "value": scenario.insurance.cargo_awrp_pct_suez, "kind": "user_input",
         "source": "Cargo war-risk premium — verify with broker"},
        {"section": "Insurance", "key": "cargo_awrp_pct_cape",
         "value": scenario.insurance.cargo_awrp_pct_cape, "kind": "user_input",
         "source": "Cargo war-risk premium — verify with broker"},

        # Route
        {"section": "Route", "key": "suez_days",
         "value": scenario.route.suez_days, "kind": "analyst_default",
         "source": "Analyst brief — verify with routing/AIS feed (not configured)"},
        {"section": "Route", "key": "cape_days",
         "value": scenario.route.cape_days, "kind": "analyst_default",
         "source": "Analyst brief — verify with routing/AIS feed (not configured)"},
        {"section": "Route", "key": "suez_toll_usd",
         "value": scenario.route.suez_toll_usd, "kind": "analyst_default",
         "source": "SCA toll circular — verify SCNT calculation"},
        {"section": "Route", "key": "cape_port_fees_usd",
         "value": scenario.route.cape_port_fees_usd, "kind": "analyst_default",
         "source": "Cape Town / Saldanha bunker stop estimate"},
        {"section": "Route", "key": "cape_congestion_delay_days",
         "value": scenario.route.cape_congestion_delay_days, "kind": "user_input",
         "source": "User-editable stress test"},

        # Regulation
        {"section": "Regulation", "key": "origin_in_eea",
         "value": scenario.regulation.origin_in_eea, "kind": "user_input",
         "source": "Voyage-specific"},
        {"section": "Regulation", "key": "dest_in_eea",
         "value": scenario.regulation.dest_in_eea, "kind": "user_input",
         "source": "Voyage-specific"},
        {"section": "Regulation", "key": "has_intermediate_eea_port_call",
         "value": scenario.regulation.has_intermediate_eea_port_call, "kind": "user_input",
         "source": "Voyage-specific"},
        {"section": "Regulation", "key": "eua_price_usd",
         "value": scenario.regulation.eua_price_usd, "kind": "analyst_default",
         "source": "EUA reference — actual price depends on EU ETS market"},
    ]
    return rows
