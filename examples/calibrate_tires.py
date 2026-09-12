"""
Calibrate tire degradation (base_laptime, degradation_rate per compound) and the shared fuel_burn_gain_per_lap parameter, 
per circuit, using real race data from FastF1.

Lap time is modelled as:
    laptime = base_laptime[compound] + degradation_rate[compound] * tire_age - fuel_burn_gain_per_lap * race_lap_number

Tire age and race lap number are fit jointly (rather than tire age alone) because fuel burn also reduces lap times over 
the race, independently of tire wear. Fitting tire age alone would confound the two effects and underestimate 
degradation_rate.

Laps are kept as "clean" if they are not in/out laps, not flagged inaccurate, and did not occur under a safety car, VSC, 
or red flag (a simple yellow flag is tolerated, since street circuits like Monaco have near-continuous local yellows
that would otherwise leave almost no data).
"""

import numpy as np
from scipy.optimize import lsq_linear
import fastf1

fastf1.set_log_level("ERROR")
fastf1.Cache.enable_cache("fastf1_cache")

# Same circuit groups and editions as calibrate_safety_car.py, so that the
# tire and safety car profiles for a given circuit are calibrated on the
# same underlying races.
CIRCUIT_GROUPS = {
    "Monaco": [
        (2018, "Monaco"), (2019, "Monaco"), (2021, "Monaco"),
        (2022, "Monaco"), (2023, "Monaco"),
    ],
    "Baku": [
        (2019, "Azerbaijan"), (2021, "Azerbaijan"),
        (2022, "Azerbaijan"), (2023, "Azerbaijan"),
    ],
    "Monza": [
        (2018, "Italy"), (2019, "Italy"), (2021, "Italy"),
        (2022, "Italy"), (2023, "Italy"),
    ],
}

# Fixed, global compound order: every race's data is aligned against this
# same list, rather than each race inferring its own list of compounds it
# happened to use. This guarantees a consistent column layout across races
# for the regression, even if a given race yields zero usable laps.
COMPOUNDS = ["SOFT", "MEDIUM", "HARD"]

# Track status codes that disqualify a lap from being "clean": safety car,
# red flag, VSC deployed, VSC ending. A plain yellow flag ('2') is tolerated.
DISRUPTIVE_STATUS_CODES = {"4", "5", "6", "7"}


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


def calibrate_circuit(races):
    """
    Pool clean laps across all given editions of a circuit and fit the
    joint tire degradation / fuel burn regression. Also returns the
    average race length (in laps) across the pooled editions.
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

    # Constrain degradation_rate columns to be >= 0: a tire cannot get
    # faster with age. base_laptime and the shared fuel term are left
    # unconstrained. This prevents the fit itself from ever proposing a
    # physically meaningless negative wear rate, rather than correcting
    # one after the fact.
    n_cols = X.shape[1]
    lower_bounds = np.full(n_cols, -np.inf)
    upper_bounds = np.full(n_cols, np.inf)
    for i in range(len(COMPOUNDS)):
        lower_bounds[2 * i + 1] = 0.0

    result = lsq_linear(X, y, bounds=(lower_bounds, upper_bounds))
    coeffs = result.x
    fuel_burn_gain_per_lap = -coeffs[-1]

    tire_params = {}
    for i, compound in enumerate(COMPOUNDS):
        base_laptime = coeffs[2 * i]
        degradation_rate = coeffs[2 * i + 1]
        if degradation_rate < 1e-6:
            print(f"  Note: constrained fit for {compound} landed exactly at the 0 boundary. "
                  f"This is a sign the sample for this compound is too sparse/noisy to trust, "
                  f"not evidence that this compound truly never degrades — consider pooling more races.")
        tire_params[compound] = {
            "base_laptime": base_laptime,
            "degradation_rate": degradation_rate,
        }

    avg_race_length = round(sum(race_lengths) / len(race_lengths))

    return tire_params, fuel_burn_gain_per_lap, avg_race_length


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