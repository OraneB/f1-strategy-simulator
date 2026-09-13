"""
Calibrate tire degradation (base_laptime, degradation_rate per compound) and the shared fuel_burn_gain_per_lap 
parameter, per circuit, using real race data from FastF1.

Lap time is modelled as:
    laptime = base_laptime[compound] + degradation_rate[compound] * tire_age - fuel_burn_gain_per_lap * race_lap_number

Tire age and race lap number are fit jointly (rather than tire age alone) because fuel burn also reduces lap times over 
the race, independently of tire wear. Fitting tire age alone would confound the two effects.

Known limitation: on circuits with fairly uniform pit stop timing, tire_age and lap number can be highly correlated 
for a given compound, making the two effects hard to separate (collinearity). degradation_rate is constrained to be >= 0 
(a tire cannot get faster with age) to prevent the fit from proposing a physically meaningless negative wear rate; if the
constrained optimum still lands exactly on that 0 boundary, this is flagged as an unreliable measurement for that 
circuit/compound pair.

When a compound's measurement is flagged unreliable, its degradation_rate is instead interpolated from the SINGLE nearest 
reliably-measured compound at the SAME circuit (nearest in the soft/medium/hard ordering), assuming a fixed relative 
ordering (soft degrades fastest, medium in between, hard slowest) with an approximate 4:2:1 ratio — an illustrative 
assumption, not an empirically derived one. Using only the nearest reliable compound, rather than averaging across all 
reliable ones, avoids blending in a second, unrelated source of noise if the reliable compounds themselves don't respect the 
expected ordering. Only if no compound at all is reliable for a circuit does the fit fall back to generic absolute
defaults, clearly flagged as such.

Laps are excluded if they are in/out laps, flagged inaccurate by FastF1, or occurred under a safety car, VSC, or red flag 
(a plain yellow flag is tolerated, since street circuits like Monaco/Singapore have near-continuous local yellows that 
would otherwise leave almost no data). Early-race laps are NOT excluded here, despite track evolution being a known 
confound (see README limitations) — kept simple for now.
"""

import numpy as np
from scipy.optimize import lsq_linear
import fastf1

fastf1.set_log_level("ERROR")
fastf1.Cache.enable_cache("fastf1_cache")

# Same circuit groups and editions as calibrate_safety_car.py, so that the tire and safety car profiles for a given 
# circuit are calibrated on the same underlying races. Chosen to span a spread of safety car risk: Monza (low), 
# Canada (moderate — tight chicanes, "Wall of Champions"), Singapore (high — historically the highest safety car rate 
# on the calendar). Baku and Monaco were both considered but dropped: Baku's own  measured base_laptime ordering came out 
# physically inconsistent (MEDIUM faster than SOFT), and having both Monaco and Singapore would have given two similarly 
# "high risk" profiles rather than a useful spread.

CIRCUIT_GROUPS = {
    "Canada": [
        (2018, "Canada"), (2019, "Canada"),
        (2022, "Canada"), (2023, "Canada"), (2024, "Canada"),
    ],
    "Singapore": [
        (2018, "Singapore"), (2019, "Singapore"),
        (2022, "Singapore"), (2023, "Singapore"), (2024, "Singapore"),
    ],
    "Monza": [
        (2018, "Italy"), (2019, "Italy"), (2021, "Italy"),
        (2022, "Italy"), (2023, "Italy"), (2024, "Italy"),
    ],
}

COMPOUNDS = ["SOFT", "MEDIUM", "HARD"]

# Track status codes that disqualify a lap from being "clean": safety car, red flag, VSC deployed, VSC ending. 
# A plain yellow flag ('2') is tolerated.
DISRUPTIVE_STATUS_CODES = {"4", "5", "6", "7"}

# Illustrative, non-empirical assumption about the relative degradation rate of each compound, used ONLY to interpolate 
# a fallback value for a compound whose own measurement is unreliable, from other reliably measured compounds at the same 
# circuit.
ASSUMED_RELATIVE_DEGRADATION = {"SOFT": 4.0, "MEDIUM": 2.0, "HARD": 1.0}

# Absolute last-resort defaults, used only if NO compound at all could be reliably measured for a given circuit.
ABSOLUTE_FALLBACK_DEGRADATION_RATE = {
    "SOFT": 0.15,
    "MEDIUM": 0.08,
    "HARD": 0.04,
}


def pd_isna(value):
    """Small local helper to avoid importing pandas just for isna()."""
    return value != value or value is None


def is_clean_status(track_status):
    return not any(code in str(track_status) for code in DISRUPTIVE_STATUS_CODES)


def get_clean_laps_and_length(year, event_name):
    """
    Load a race session and return (clean_laps, race_length), where
    clean_laps excludes in/out laps, inaccurate laps, and any lap that
    occurred under a safety car, VSC, or red flag, and race_length is the
    highest lap number reached in the (unfiltered) session.
    """
    session = fastf1.get_session(year, event_name, "R")
    session.load(telemetry=False, weather=False, messages=False)
    laps = session.laps

    race_length = int(laps["LapNumber"].max())
    clean_laps = laps.pick_wo_box().pick_accurate()
    clean_laps = clean_laps[clean_laps["TrackStatus"].apply(is_clean_status)]
    return clean_laps, race_length


def build_regression_data(clean_laps, compound_order):
    """
    Build the design matrix and target vector for the joint regression,
    across all compounds at once, using a FIXED compound_order (shared
    across every race) so that column layout never varies from one race
    to another, even if a race has zero usable laps for some (or all)
    compounds.
    """
    n_cols = 2 * len(compound_order) + 1
    rows = []
    targets = []
    for _, lap in clean_laps.iterrows():
        if lap["Compound"] not in compound_order or pd_isna(lap["LapTime"]) or pd_isna(lap["TyreLife"]):
            continue
        row = [0.0] * n_cols
        compound_index = compound_order.index(lap["Compound"])
        row[2 * compound_index] = 1.0
        row[2 * compound_index + 1] = lap["TyreLife"] - 1
        row[-1] = lap["LapNumber"]
        rows.append(row)
        targets.append(lap["LapTime"].total_seconds())

    if not rows:
        return np.zeros((0, n_cols)), np.zeros((0,))
    return np.array(rows), np.array(targets)


# Position of each compound in the soft/medium/hard ordering, used to find the "nearest" reliable compound when 
# interpolating a fallback value.
COMPOUND_ORDER_INDEX = {"SOFT": 0, "MEDIUM": 1, "HARD": 2}


def fill_unreliable_degradation_rates(tire_params, reliable):
    """
    For any compound flagged unreliable (reliable[compound] is False),
    interpolate its degradation_rate from the SINGLE nearest reliable
    compound at the same circuit (nearest in the soft/medium/hard
    ordering), using ASSUMED_RELATIVE_DEGRADATION. Falls back to
    ABSOLUTE_FALLBACK_DEGRADATION_RATE only if no compound is reliable.

    Using only the nearest reliable compound, rather than averaging
    across all reliable ones, avoids compounding two separate sources of
    unreliability: if the reliable compounds themselves don't respect the
    expected relative ordering (see check_monotonic_degradation_order),
    averaging across them would silently blend that inconsistency into
    the interpolated value instead of minimising its influence.

    Mutates tire_params in place and returns it.
    """
    reliable_compounds = [c for c in COMPOUNDS if reliable[c]]

    for compound in COMPOUNDS:
        if reliable[compound]:
            continue
        if reliable_compounds:
            nearest = min(
                reliable_compounds,
                key=lambda c: abs(COMPOUND_ORDER_INDEX[c] - COMPOUND_ORDER_INDEX[compound]),
            )
            unit = tire_params[nearest]["degradation_rate"] / ASSUMED_RELATIVE_DEGRADATION[nearest]
            fallback_rate = unit * ASSUMED_RELATIVE_DEGRADATION[compound]
            print(f"  Note: {compound} degradation_rate unreliable (0 boundary) — interpolated from "
                  f"nearest reliable compound ({nearest}) at this circuit instead: {fallback_rate:.4f}")
        else:
            fallback_rate = ABSOLUTE_FALLBACK_DEGRADATION_RATE[compound]
            print(f"  Note: {compound} degradation_rate unreliable (0 boundary), and no other compound "
                  f"was reliable at this circuit either — using generic default instead: {fallback_rate:.4f}")
        tire_params[compound]["degradation_rate"] = fallback_rate

    return tire_params


def calibrate_circuit(races):
    """
    Pool clean laps across all given editions of a circuit and fit the
    joint tire degradation / fuel burn regression, constrained so that no
    compound's degradation_rate can be negative. Also returns the average
    race length (in laps) across the pooled editions.
    """
    all_X = []
    all_y = []
    race_lengths = []

    for year, event_name in races:
        print(f"  Loading {year} {event_name}...")
        try:
            clean_laps, race_length = get_clean_laps_and_length(year, event_name)
        except Exception as e:
            print(f"    Skipped ({e})")
            continue

        race_lengths.append(race_length)
        X, y = build_regression_data(clean_laps, COMPOUNDS)
        print(f"    {len(y)} clean laps kept, race length {race_length}")
        all_X.append(X)
        all_y.append(y)

    if not any(len(y) for y in all_y):
        return None

    X = np.vstack(all_X)
    y = np.concatenate(all_y)

    n_cols = X.shape[1]
    lower_bounds = np.full(n_cols, -np.inf)
    upper_bounds = np.full(n_cols, np.inf)
    for i in range(len(COMPOUNDS)):
        lower_bounds[2 * i + 1] = 0.0

    result = lsq_linear(X, y, bounds=(lower_bounds, upper_bounds))
    coeffs = result.x
    fuel_burn_gain_per_lap = -coeffs[-1]

    tire_params = {}
    reliable = {}
    for i, compound in enumerate(COMPOUNDS):
        base_laptime = coeffs[2 * i]
        degradation_rate = coeffs[2 * i + 1]
        reliable[compound] = degradation_rate >= 1e-6
        tire_params[compound] = {
            "base_laptime": base_laptime,
            "degradation_rate": degradation_rate,
        }

    if not all(reliable.values()):
        tire_params = fill_unreliable_degradation_rates(tire_params, reliable)

    check_monotonic_degradation_order(tire_params)

    avg_race_length = round(sum(race_lengths) / len(race_lengths))

    return tire_params, fuel_burn_gain_per_lap, avg_race_length


def check_monotonic_degradation_order(tire_params):
    """
    Print a note (without correcting anything) if degradation_rate does
    not follow the expected soft >= medium >= hard ordering. The fit is
    only constrained to be non-negative (see calibrate_circuit), not to
    respect this relative ordering between compounds — so a circuit with
    little overall degradation and a noisy sample can still occasionally
    produce a mild inconsistency here. Documented as a known limitation
    rather than silently corrected.
    """
    soft = tire_params["SOFT"]["degradation_rate"]
    medium = tire_params["MEDIUM"]["degradation_rate"]
    hard = tire_params["HARD"]["degradation_rate"]
    if not (soft >= medium >= hard):
        print(f"  Note: measured degradation_rate does not follow the expected SOFT >= MEDIUM >= HARD "
              f"ordering (got {soft:.4f} / {medium:.4f} / {hard:.4f}). Left as-is rather than corrected — "
              f"likely measurement noise on a circuit with low overall degradation, but treat these "
              f"specific values with caution.")


def main():
    for circuit_name, races in CIRCUIT_GROUPS.items():
        print(f"\n=== {circuit_name} ===")
        result = calibrate_circuit(races)
        if result is None:
            print("  No usable data collected.")
            continue

        tire_params, fuel_burn_gain_per_lap, avg_race_length = result

        print(f"\n  Average race length: {avg_race_length} laps")
        print(f"  {'Compound':<12}{'base_laptime':<16}{'degradation_rate'}")
        print("  " + "-" * 45)
        for compound, params in tire_params.items():
            print(f"  {compound:<12}{params['base_laptime']:<16.3f}{params['degradation_rate']:.4f}")
        print(f"  fuel_burn_gain_per_lap: {fuel_burn_gain_per_lap:.4f} s/lap")


if __name__ == "__main__":
    main()