from dataclass import dataclass

@dataclass
class SafetyCar:
    """
    Probabilistic safety car model, represented as a two-state Markov chain (safety car active vs. safety car inactive).
    
    Attributes:
        p_start (float): probability, on any given lap where the safety car is not currently active, that it starts on this lap.
        p_end (float): probability, on any given lap where the safety car is currently active, that it ends on this lap.
        sc_laptime (float): the lap time, in seconds, when the safety car is active.
        sc_pit_stop_loss (float): the time penalty, in seconds, for a pit stop when the safety car is active.
    """
    p_start: float
    p_end: float
    sc_laptime: float = 110.0
    sc_pit_stop_loss: float = 14.0