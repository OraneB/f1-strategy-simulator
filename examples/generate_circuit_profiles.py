"""
Regenerate src/circuit_profiles.py from live FastF1 calibration, reusing the same calibration logic as 
calibrate_tires.py, calibrate_safety_car.py, and calibrate_pit_stop.py, for every circuit defined in circuit_groups.py.

Run this whenever you want to refresh the calibrated circuit profiles.
"""

import os

from calibrate_tires import calibrate_circuit as calibrate_tires_circuit, COMPOUNDS, CIRCUIT_GROUPS
from calibrate_sc import calibrate_circuit_group
from calibrate_pit_stop import calibrate_circuit as calibrate_pit_stop_circuit
from external_factors import SC_PIT_LOSS_FACTOR

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "..", "src", "circuit_profiles.py")

HEADER = '''

from tires import Tire
from external_factors import SafetyCar

CIRCUIT_PROFILES = {
'''

FOOTER = '''}


def get_circuit_profile(circuit_name):
    """
    Look up a calibrated circuit profile by name.

    Args:
        circuit_name (str): one of the keys in CIRCUIT_PROFILES (e.g. "Monza").

    Returns:
        dict: with keys "race_length", "tire_compounds",
            "fuel_burn_gain_per_lap", "pit_stop_loss", and "safety_car".

    Raises:
        KeyError: if circuit_name is not a known profile, with a message
            listing the available options.
    """
    if circuit_name not in CIRCUIT_PROFILES:
        available = ", ".join(CIRCUIT_PROFILES.keys())
        raise KeyError(f"Unknown circuit '{circuit_name}'. Available profiles: {available}")
    return CIRCUIT_PROFILES[circuit_name]
'''


def format_circuit_block(circuit_name, tire_params, fuel_burn_gain_per_lap, race_length, p_start, p_end, pit_stop_loss):
    lines = [f'    "{circuit_name}": {{']
    lines.append(f'        "race_length": {race_length},')
    lines.append('        "tire_compounds": {')
    for compound in COMPOUNDS:
        params = tire_params[compound]
        lines.append(
            f'            "{compound}": Tire("{compound}", base_laptime={params["base_laptime"]:.3f}, '
            f'degradation_rate={params["degradation_rate"]:.4f}),'
        )
    lines.append('        },')
    lines.append(f'        "fuel_burn_gain_per_lap": {fuel_burn_gain_per_lap:.4f},')
    lines.append(f'        "pit_stop_loss": {pit_stop_loss:.2f},')
    lines.append(f'        "safety_car": SafetyCar(p_start={p_start:.4f}, p_end={p_end:.4f}, sc_pit_stop_loss={pit_stop_loss * SC_PIT_LOSS_FACTOR:.2f}),')
    lines.append('    },')
    return "\n".join(lines)


def main():
    circuit_blocks = []

    for circuit_name, races in CIRCUIT_GROUPS.items():
        print(f"=== {circuit_name} ===")

        tire_result = calibrate_tires_circuit(races)
        if tire_result is None:
            print(f"  Skipping {circuit_name}: no usable tire/fuel data.")
            continue
        tire_params, fuel_burn_gain_per_lap, race_length = tire_result

        p_start, p_end, n_start_obs, n_end_obs = calibrate_circuit_group(races)

        pit_result = calibrate_pit_stop_circuit(races)
        if pit_result is None:
            print(f"  Skipping {circuit_name}: no usable pit stop data.")
            continue
        pit_stop_loss, n_pit_obs = pit_result

        circuit_blocks.append(format_circuit_block(
            circuit_name, tire_params, fuel_burn_gain_per_lap, race_length,
            p_start, p_end, pit_stop_loss
        ))
        print(f"  Done: race_length={race_length}, fuel={fuel_burn_gain_per_lap:.4f}, "
              f"pit_stop_loss={pit_stop_loss:.2f} ({n_pit_obs} obs), "
              f"p_start={p_start:.4f} ({n_start_obs} obs), p_end={p_end:.4f} ({n_end_obs} obs)")

    content = HEADER + "\n".join(circuit_blocks) + "\n" + FOOTER

    with open(OUTPUT_PATH, "w") as f:
        f.write(content)

    print(f"\nWrote {len(circuit_blocks)} circuit profile(s) to {os.path.abspath(OUTPUT_PATH)}")


if __name__ == "__main__":
    main()