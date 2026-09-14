from dataclasses import dataclass

SC_PIT_LOSS_FACTOR = 0.5
SC_LAP_TIME_FACTOR = 1.35

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
    
    def __repr__(self):
        avg_duration = 1 / self.p_end if self.p_end > 0 else float("inf")
        return f"SafetyCar(p_start={self.p_start:.3f}, p_end={self.p_end:.3f}, avg duration={avg_duration:.1f} laps)"