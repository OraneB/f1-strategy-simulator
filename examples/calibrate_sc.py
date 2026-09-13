"""
Calibrate SafetyCar(p_start, p_end) parameters per circuit "profile" using real race data from FastF1.

For each circuit, several past editions are pooled together (a single race rarely has more than 0-1 safety car periods, 
so per-race estimates would be far too noisy). For every race, each lap is marked as safety-car-active or not (FastF1 
track status code '4' = Safety Car), then consecutive laps are used to count Markov chain transitions:
    - p_start: P(safety car starts this lap | it was not active last lap)
    - p_end:   P(safety car ends this lap | it was active last lap)
"""

import fastf1

fastf1.set_log_level("ERROR")
fastf1.Cache.enable_cache("fastf1_cache")

# A handful of past editions per circuit, chosen to give enough laps to estimate stable transition probabilities. 
# Same circuit groups and editions as calibrate_safety_car.py, so that the tire and safety car profiles for a given 
# circuit are calibrated on the same underlying races.
CIRCUIT_GROUPS = {
    "Canada (permanent circuit, moderate SC risk)": [
        (2018, "Canada"), (2019, "Canada"),
        (2022, "Canada"), (2023, "Canada"), (2024, "Canada"),
    ],
    "Singapore (street circuit, historically highest SC rate)": [
        (2018, "Singapore"), (2019, "Singapore"),
        (2022, "Singapore"), (2023, "Singapore"), (2024, "Singapore"),
    ],
    "Monza (permanent circuit, low SC risk)": [
        (2018, "Italy"), (2019, "Italy"), (2021, "Italy"),
        (2022, "Italy"), (2023, "Italy"), (2024, "Italy"),
    ],
}


def get_safety_car_laps(year, event_name):
    """
    Load a race session and return a boolean pandas Series indexed by lap
    number, True where the safety car was active at some point during that
    lap for at least one driver, sorted by lap number.
    """
    session = fastf1.get_session(year, event_name, "R")
    session.load(laps=True, telemetry=False, weather=False, messages=False)
    laps = session.laps

    def lap_has_safety_car(track_status_values):
        return any("4" in str(code) for code in track_status_values.dropna())

    sc_by_lap = laps.groupby("LapNumber")["TrackStatus"].apply(lap_has_safety_car)
    return sc_by_lap.sort_index()


def count_transitions(sc_by_lap):
    """
    Count (start_transitions, start_opportunities, end_transitions,
    end_opportunities) for a single race's lap-by-lap safety car sequence.
    """
    start_transitions = 0
    start_opportunities = 0
    end_transitions = 0
    end_opportunities = 0

    lap_numbers = sorted(sc_by_lap.index)
    prev_active = None
    for lap_number in lap_numbers:
        curr_active = bool(sc_by_lap[lap_number])
        if prev_active is not None:
            if not prev_active:
                start_opportunities += 1
                if curr_active:
                    start_transitions += 1
            else:
                end_opportunities += 1
                if not curr_active:
                    end_transitions += 1
        prev_active = curr_active

    return start_transitions, start_opportunities, end_transitions, end_opportunities


def calibrate_circuit_group(races):
    """
    Pool transition counts across several races and return the empirical
    (p_start, p_end) estimates for that group.
    """
    total_start_transitions = 0
    total_start_opportunities = 0
    total_end_transitions = 0
    total_end_opportunities = 0

    for year, event_name in races:
        print(f"  Loading {year} {event_name}...")
        try:
            sc_by_lap = get_safety_car_laps(year, event_name)
        except Exception as e:
            print(f"    Skipped ({e})")
            continue

        st, so, et, eo = count_transitions(sc_by_lap)
        total_start_transitions += st
        total_start_opportunities += so
        total_end_transitions += et
        total_end_opportunities += eo

    p_start = total_start_transitions / total_start_opportunities if total_start_opportunities else 0.0
    p_end = total_end_transitions / total_end_opportunities if total_end_opportunities else 0.0

    return p_start, p_end, total_start_opportunities, total_end_opportunities


def main():
    print(f"{'Circuit group':<45}{'p_start':<12}{'p_end':<12}{'avg SC duration (laps)'}")
    print("-" * 100)

    for label, races in CIRCUIT_GROUPS.items():
        print(f"\n{label}:")
        p_start, p_end, n_start_obs, n_end_obs = calibrate_circuit_group(races)
        avg_duration = (1 / p_end) if p_end > 0 else float("inf")
        print(f"{label:<45}{p_start:<12.4f}{p_end:<12.4f}{avg_duration:.1f}")
        print(f"  (based on {n_start_obs} green-flag laps and {n_end_obs} safety-car laps observed)")


if __name__ == "__main__":
    main()