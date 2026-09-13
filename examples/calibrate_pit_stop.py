"""
Calibrate pit_stop_loss (the time cost of a normal-conditions pit stop), per circuit, using real race data from FastF1.

Method: for each pit stop, compare the sum of the in-lap and out-lap times to twice the circuit's typical racing 
lap time (average over clean laps). The excess is attributed to the stop itself (slowing for pit entry, transit through 
the pit lane at reduced speed, the stationary time, and accelerating back to pace).

Pit stops that occurred under a safety car, VSC, or red flag are excluded.
"""

import numpy as np
import fastf1

from calibrate_tires import CIRCUIT_GROUPS

fastf1.set_log_level("ERROR")

import logging
logging.disable(logging.WARNING)

fastf1.Cache.enable_cache("fastf1_cache")

DISRUPTIVE_STATUS_CODES = {"4", "5", "6", "7"}

# Sanity bounds: a measured loss outside this range is almost certainly an artifact (e.g. a red flag stoppage not 
# fully caught by the track status filter, or a drive-through penalty) rather than a normal pit stop.
MIN_PLAUSIBLE_LOSS = 5.0
MAX_PLAUSIBLE_LOSS = 60.0


def pd_isna(value):
    """Small local helper to avoid importing pandas just for isna()."""
    return value != value or value is None


def is_clean_status(track_status):
    return not any(code in str(track_status) for code in DISRUPTIVE_STATUS_CODES)


def get_pit_stop_losses(year, event_name):
    """
    Load a race session and return a list of estimated pit stop time
    losses (in seconds), one per valid pit stop found in that race.
    """
    session = fastf1.get_session(year, event_name, "R")
    session.load(telemetry=False, weather=False, messages=False)
    laps = session.laps

    reference_laps = laps.pick_wo_box().pick_accurate()
    reference_laps = reference_laps[reference_laps["TrackStatus"].apply(is_clean_status)]
    reference_laptimes = [
        lap_time.total_seconds()
        for lap_time in reference_laps["LapTime"]
        if not pd_isna(lap_time)
    ]
    if not reference_laptimes:
        return []
    avg_laptime = float(np.mean(reference_laptimes))

    losses = []
    for driver in laps["Driver"].unique():
        driver_laps = laps[laps["Driver"] == driver].sort_values("LapNumber")

        for _, in_lap in driver_laps.iterrows():
            if pd_isna(in_lap["PitInTime"]):
                continue

            next_lap_number = in_lap["LapNumber"] + 1
            candidates = driver_laps[driver_laps["LapNumber"] == next_lap_number]
            if candidates.empty:
                continue
            out_lap = candidates.iloc[0]

            if pd_isna(out_lap["PitOutTime"]):
                continue
            if pd_isna(in_lap["LapTime"]) or pd_isna(out_lap["LapTime"]):
                continue
            if not is_clean_status(in_lap["TrackStatus"]) or not is_clean_status(out_lap["TrackStatus"]):
                continue

            in_time = in_lap["LapTime"].total_seconds()
            out_time = out_lap["LapTime"].total_seconds()
            loss = (in_time + out_time) - 2 * avg_laptime

            if MIN_PLAUSIBLE_LOSS < loss < MAX_PLAUSIBLE_LOSS:
                losses.append(loss)

    return losses


def calibrate_circuit(races):
    """
    Pool pit stop loss estimates across all given editions of a circuit.

    Returns:
        tuple: (avg_pit_stop_loss, n_observations), or None if no usable
            data was collected.
    """
    all_losses = []

    for year, event_name in races:
        print(f"  Loading {year} {event_name}...")
        try:
            losses = get_pit_stop_losses(year, event_name)
        except Exception as e:
            print(f"    Skipped ({e})")
            continue
        print(f"    {len(losses)} pit stop observations")
        all_losses.extend(losses)

    if not all_losses:
        return None

    return float(np.mean(all_losses)), len(all_losses)


def main():
    print(f"{'Circuit':<15}{'pit_stop_loss (s)':<20}{'observations'}")
    print("-" * 50)

    for circuit_name, races in CIRCUIT_GROUPS.items():
        print(f"\n{circuit_name}:")
        result = calibrate_circuit(races)
        if result is None:
            print("  No usable data collected.")
            continue
        avg_loss, n_obs = result
        print(f"{circuit_name:<15}{avg_loss:<20.2f}{n_obs}")


if __name__ == "__main__":
    main()