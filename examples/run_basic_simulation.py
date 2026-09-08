from tires import tire_compounds
from strategy import Stint, Strategy
from simulation import simulate_race


def main():
    """
    Basic example: simulate a single fixed strategy and print the result.
    This is the simplest possible use of the simulator, showing how
    simulate_race works before any search or optimization is involved.
    """
    strategy = Strategy(stints=[
        Stint(compound="soft", laps=15),
        Stint(compound="medium", laps=35),
    ])

    race_length = sum(stint.laps for stint in strategy.stints)
    total_time = simulate_race(strategy, tire_compounds, pit_stop_loss=22.0, fuel_burn_gain_per_lap=0.05)

    print(f"Strategy: {strategy}")
    print(f"Race length: {race_length} laps")
    print(f"Total race time: {total_time:.2f}s")


if __name__ == "__main__":
    main()