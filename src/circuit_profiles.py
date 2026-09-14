

from tires import Tire
from external_factors import SafetyCar

CIRCUIT_PROFILES = {
    "Canada": {
        "race_length": 70,
        "tire_compounds": {
            "SOFT": Tire("SOFT", base_laptime=78.034, degradation_rate=0.0472),
            "MEDIUM": Tire("MEDIUM", base_laptime=79.297, degradation_rate=0.0236),
            "HARD": Tire("HARD", base_laptime=78.995, degradation_rate=0.0005),
        },
        "fuel_burn_gain_per_lap": 0.0271,
        "pit_stop_loss": 21.43,
        "safety_car": SafetyCar(p_start=0.0127, p_end=0.1724, sc_laptime=110.29, sc_pit_stop_loss=10.72),
    },
    "Singapore": {
        "race_length": 61,
        "tire_compounds": {
            "SOFT": Tire("SOFT", base_laptime=106.764, degradation_rate=0.0165),
            "MEDIUM": Tire("MEDIUM", base_laptime=103.492, degradation_rate=0.0083),
            "HARD": Tire("HARD", base_laptime=102.487, degradation_rate=0.0041),
        },
        "fuel_burn_gain_per_lap": 0.0104,
        "pit_stop_loss": 29.88,
        "safety_car": SafetyCar(p_start=0.0221, p_end=0.2414, sc_laptime=145.95, sc_pit_stop_loss=14.94),
    },
    "Monza": {
        "race_length": 53,
        "tire_compounds": {
            "SOFT": Tire("SOFT", base_laptime=87.092, degradation_rate=0.1050),
            "MEDIUM": Tire("MEDIUM", base_laptime=87.208, degradation_rate=0.0525),
            "HARD": Tire("HARD", base_laptime=86.811, degradation_rate=0.0608),
        },
        "fuel_burn_gain_per_lap": 0.0568,
        "pit_stop_loss": 26.96,
        "safety_car": SafetyCar(p_start=0.0082, p_end=0.0769, sc_laptime=121.85, sc_pit_stop_loss=13.48),
    },
}


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
