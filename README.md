# F1 Strategy Simulator

> Simulation and optimisation of Formula 1 pit stop strategy under tire degradation and fuel load.
 
> Personal project | 2026

## Overview

This project investigates how pit stop strategy affects total race time in Formula 1, and how that optimal strategy changes as the underlying model is made more realistic.

A simplified race is represented as a sequence of laps driven on a chosen tire compound, with each compound defined by a base lap time and a degradation profile. Different pit stop strategies are compared according to total race time, and increasingly capable search algorithms are used to find the fastest one as the space of possible strategies grows.

The project progresses from exhaustive search to dynamic programming, and finally to stochastic dynamic programming. In the stochastic model, safety car periods are represented as a two-state Markov process, introducing uncertainty into the optimisation problem and requiring decisions to be evaluated in terms of expected remaining race time. Model parameters are then calibrated per circuit from real race data.

## Objective

The objective is to determine, for a given race length and tire model, the pit stop strategy that minimises total race time, and to study how this optimum shifts as degradation becomes non-linear and fuel load and external factors are taken into account.

Three search approaches are compared:

- an exhaustive (brute-force) search
- a dynamic programming approach
- a stochastic dynamic programming approach

## Data and Assumptions

No real telemetry data were used in the early version of this project. Tire behaviour (base lap time, degradation rate, cliff threshold) and race parameters (pit stop loss, fuel effect) were manually defined assumptions intended to represent plausible race conditions, informed by publicly available knowledge of Formula 1 tire compounds.

In later stages of the project, the model is calibrated by analysing data from the FastF1 library and using it to refine the model parameters.

Four main modelling assumptions are used:

### Tire degradation
 
Each compound (soft, medium, hard) is assigned a base lap time and a degradation rate. Degradation is linear up to a compound-specific "cliff" lap, after which it switches to a steeper linear rate, representing the sudden performance drop-off observed on real tires past their optimal window.
 
### Fuel effect
 
Lap times decrease slightly over the course of the race as the car burns fuel and gets lighter, modelled as a fixed time gain per lap already completed, independent of tire compound.
 
### Pit stop cost
 
A fixed time penalty is applied for each pit stop.

### Safety car

A safety car period is modelled as a two-state Markov process rather than a fixed occurrence: on any given lap where the safety car is not active, it starts with probability `p_start`; on any given lap where it is active, it ends with probability `p_end` (implying an average duration of `1 / p_end` laps). While active, lap times are set to a fixed value (`sc_laptime`), independent of tire compound, and the pit stop cost is reduced (`sc_pit_stop_loss`). Tire wear is assumed negligible while the safety car is active, so tire age does not increase during those laps.

The datasets and constants used are model assumptions rather than measured values. Results should therefore be interpreted within the limits of the model.

## Methodology
 
### 1. Race and tire modelling
 
A race is represented as a sequence of laps driven across one or more stints, each defined by a tire compound and a number of laps. `simulate_race` computes the total time for a given strategy by summing lap times (compound base time + degradation, adjusted for fuel burn) and adding the pit stop penalty for each stint change.
 
### 2. Exhaustive strategy search
 
For a fixed number of pit stops, every valid combination of compounds and stint lengths is generated — subject to a minimum stint length and the regulatory requirement of using at least two different compounds — and simulated to find the fastest one.

The minimum stint length is an arbitrary parameter used to limit the number of combinations to be evaluated and reduce the computational time required for the exhaustive search.

This approach is correct by construction but does not scale: on a 50-lap race, the number of candidate strategies grows from 246 (1 stop) to over 5.7 million (4 stops), with computation time going from milliseconds to over a minute.
 
### 3. Non-linear degradation and fuel effect
 
The tire model is extended with the cliff degradation and fuel effects described above. Tire degradation and fuel burn are modelled as independent effects: in reality, a heavier (fuller) car increases tire wear, but this coupling is not represented here, in order to keep the tire model tractable.
 
### 4. Dynamic programming optimisation
 
A dynamic programming approach is used to search for the optimal race strategy. The problem is formulated in terms of race states, defined by the current lap, tyre compound, tyre age, and compounds used so far. At each lap, the algorithm evaluates the two possible decisions: continuing on the current set of tyres or making a pit stop to switch compounds. Previously evaluated states are stored and reused to avoid redundant computations.

### 5. Stochastic dynamic programming: safety car risk

The dynamic programming approach is extended to account for the safety car model described above. Race states now also include whether the safety car is currently active. At each lap, the algorithm minimises the *expected* remaining race time rather than a certain one: each decision (continue or pit) is evaluated across both possible outcomes for the next lap (safety car starts/ends, or not), weighted by their respective probabilities. The reconstructed strategy follows the higher-probability branch at each such split.

Note: this stochastic formulation does not enforce a minimum stint length (unlike the deterministic search in steps 2 and 4), which can occasionally produce a very short final stint used purely to satisfy the two-compound rule at minimal cost — see [Limitations](#limitations).

### 6. Calibration from real race data

Tire degradation, fuel burn, pit stop cost, and safety car transition probabilities are calibrated per circuit from real FastF1 telemetry (`examples/calibrate_tires.py`, `examples/calibrate_sc.py`, `examples/calibrate_pit_stop.py`), rather than left as illustrative constants, for three circuits chosen to span a range of safety car risk: Monza (low), Canada (moderate), and Singapore (historically the highest on the calendar).

Tire degradation and fuel burn are fit jointly via a linear regression across all clean laps (excluding in/out laps, inaccurate laps, and laps under a safety car, VSC, or red flag), constrained so that degradation_rate cannot be negative — a tire cannot get faster with age. Pit stop cost is estimated by comparing the combined in-lap and out-lap time to twice the circuit's typical racing lap time, excluding stops that occurred under a safety car, VSC, or red flag. Safety car start/end probabilities are estimated as a two-state Markov chain (see [Data and Assumptions](#safety-car)) by counting transitions across several editions of each circuit, pooled together since a single race rarely has enough safety car occurrences to estimate this reliably on its own.

When a compound's degradation_rate cannot be reliably measured (the constrained fit lands exactly on the 0 boundary — usually too few high-tire-age laps in the sample), it is instead interpolated from the nearest reliably-measured compound at the same circuit, assuming an approximate 4:2:1 (soft:medium:hard) relative degradation ratio. This is an illustrative assumption, not an empirically derived one.

Two safety-car-specific parameters were *not* calibrated directly, after dedicated attempts found too little usable data: `sc_pit_stop_loss` (a pit stop coinciding with an already-rare safety car/VSC period is a very rare intersection of two rare events) and `sc_laptime` (too few SC/VSC laps observed at some circuits to estimate pace reliably). Both are instead derived from already-calibrated, well-measured quantities using a fixed factor: `sc_pit_stop_loss = pit_stop_loss * SC_PIT_LOSS_FACTOR` (0.5, a simplifying assumption) and `sc_laptime = average(compound base_laptime) * SC_LAP_TIME_FACTOR` (1.35, informed by commonly reported Virtual Safety Car pace deltas of roughly 30-40% slower than normal racing pace). Both factors are defined once in `src/external_factors.py`.

Calibrated profiles are collected in `src/circuit_profiles.py`, which is auto-generated by `examples/generate_circuit_profiles.py` — it should never be hand-edited. Re-running that script (e.g. after adding a new season's edition to `CIRCUIT_GROUPS` in `calibrate_tires.py`) refreshes all three circuits' profiles in one go. Day-to-day use of the simulator (e.g. `run_circuits.py`) only reads this generated file and never needs FastF1, network access, or the calibration scripts themselves.

## Installation & Usage
 
```bash
pip install -r requirements.txt
```
 
Run any example from the project root:
 
```bash
PYTHONPATH=src python3 examples/run_basic_simulation.py
PYTHONPATH=src python3 examples/compare_algorithms.py
PYTHONPATH=src python3 examples/compare_sc_scenarios.py
PYTHONPATH=src python3 examples/run_circuits.py
```

`run_basic_simulation.py` prints, for a given strategy, the strategy, the race length, and the total race time.

`compare_algorithms.py` prints, for a given race length, the best strategy and computation time found by exhaustive search (for a range of pit stop counts) alongside the dynamic programming approach, together with a consistency check between the two.

`compare_sc_scenarios.py` prints, for a given race length, the expected race time and resulting strategy under several safety car risk levels, compared against the no-risk baseline.

`run_circuits.py` prints, for each calibrated circuit profile, the best strategy ignoring safety car risk alongside the best strategy accounting for that circuit's own calibrated safety car risk.

To refresh the calibrated circuit profiles from live FastF1 data (requires `fastf1`, `numpy`, `scipy`, and network access):

```bash
PYTHONPATH=src python3 examples/generate_circuit_profiles.py
```

## Testing
 
The project includes a unit test suite (`tests/`), covering the tire model, strategy validation, race simulation, and both search approaches — including a consistency check between exhaustive search and dynamic programming, and between the stochastic and deterministic dynamic programming approaches under zero safety car risk.
 
This last check caught a genuine bug during development: the stochastic model computes an expected time by weighting each possible outcome (safety car starts/ends, or not) by its probability, some of which are legitimately zero (e.g. a safety car risk of exactly 0). A branch with zero probability that also happened to be mathematically infinite (an unreachable, invalid strategy) produced `0 * inf = nan` under standard floating-point arithmetic, silently propagating through the recursion. The fix was to skip computing a branch's contribution entirely whenever its probability is zero, rather than relying on multiplying by zero to cancel it out.

The tests were also used to detect and correct several implementation errors and oversights.

## Results
 
On a 50-lap race with three compounds, both exhaustive search and dynamic programming converge to the same optimal race time, achieved with two pit stops, with the dynamic programming approach finding it in a fraction of the time required by exhaustive search as the number of candidate pit stops grows.
 
The two methods return strategies with a different stint order for an identical total time — expected, since nothing in the current (linear) degradation model favours one ordering of otherwise identical stints over another.

Under increasing safety car risk, the expected race time rises accordingly, and the optimal strategy shifts slightly, with pit stops occurring marginally earlier as safety car risk increases.

Calibrating against real FastF1 data (2018-2024 editions) produced the following circuit-specific profiles:
 
| Circuit | Race length | SOFT (base / degr.) | MEDIUM (base / degr.) | HARD (base / degr.) | Fuel gain | Pit stop loss | SC p_start / p_end | SC lap time* | SC pit stop loss* |
|---|---|---|---|---|---|---|---|---|---|
| Monza | 53 laps | 87.09 / 0.105† | 87.21 / 0.053 | 86.81 / 0.061 | 0.057 s/lap | 26.96 s | 0.008 / 0.077 | 121.85 s | 13.48 s |
| Canada | 70 laps | 78.03 / 0.047 | 79.30 / 0.024† | 79.00 / 0.001 | 0.027 s/lap | 21.43 s | 0.013 / 0.172 | 110.29 s | 10.72 s |
| Singapore | 61 laps | 106.76 / 0.017 | 103.49 / 0.008† | 102.49 / 0.004† | 0.010 s/lap | 29.88 s | 0.022 / 0.241 | 145.95 s | 14.94 s |
 
†Interpolated from a nearby compound rather than directly measured (see [Methodology](#6-calibration-from-real-race-data)).
*Derived from other calibrated values using a fixed factor, not independently calibrated (see [Methodology](#6-calibration-from-real-race-data)).
 
The resulting safety car risk ordering (Monza < Canada < Singapore) matches expectations for these circuits, as does the pit stop loss ordering — Singapore's pit lane is known to be one of the longest on the calendar, while Canada's is comparatively short. Monza's SOFT/HARD degradation_rate values do not follow the expected ordering relative to MEDIUM (see [Limitations](#limitations)).

Running the calibrated profiles through the stochastic search (`run_circuits.py`) illustrates the `min_stint_length` limitation noted in [Methodology](#5-stochastic-dynamic-programming-safety-car-risk): at circuits where a compound degrades very little, the search can propose a token final stint of just 1-2 laps used purely to satisfy the two-compound rule, rather than a genuine second stint.

## Limitations
 
- **Modelling assumptions**: tire degradation parameters and pit stop cost are manually defined rather than derived from real telemetry data, unless a calibrated circuit profile (`src/circuit_profiles.py`) is used.
- **Decoupled degradation and fuel effects**: fuel load is assumed not to affect tire degradation, which is a simplification of real tire behaviour.
- **`min_stint_length` as a uniform constraint, and absent from the stochastic search**: this pruning threshold is applied uniformly throughout the race in the exhaustive and deterministic DP searches, to keep the search space tractable. It is not derived from an official regulation. The stochastic search (step 5) does not enforce it at all, which can occasionally produce a token stint of just 1-2 laps purely to satisfy the two-compound rule (see [Results](#results)).
- **No opponent modelling**: strategies are evaluated in isolation; race dynamics such as undercut/overcut relative to a competitor are not yet modelled.
- **No relative ordering constraint between compounds**: calibrated degradation_rate values are only constrained to be non-negative, not to follow the expected soft >= medium >= hard ordering. On circuits with low overall degradation and a noisy sample (e.g. Monza), this can occasionally produce a mild inconsistency (a harder compound measured as degrading faster than a softer one) — flagged by the calibration script rather than corrected.
- **Linear degradation only, when calibrated from data**: the calibration only fits a single linear degradation_rate per compound; cliff_lap and cliff_degradation_rate (used elsewhere in the model) are not calibrated and are left at their defaults for calibrated circuit profiles.
- **`sc_laptime` and `sc_pit_stop_loss` are not independently calibrated**: dedicated calibration was attempted for both, but the relevant events (a pit stop or a lap coinciding with a safety car/VSC period) were too rare to yield a trustworthy per-circuit sample. Both are instead derived from other, well-calibrated quantities using a fixed factor (see [Methodology](#6-calibration-from-real-race-data)) — a documented simplifying assumption, not a measured value.
- **Small sample sizes elsewhere**: safety car start/end probabilities and pit stop cost are each estimated from a fairly small number of observed events per circuit (a few dozen at most, across 4-5 editions) — treat the calibrated values as rough estimates rather than precise figures.

These limitations provide potential directions for improving the model.
 
## Technologies & Methods
 
- Python
- Dynamic Programming
- Stochastic Optimisation
- Markov Processes

## Repository Structure
 
```text
.
├── src/
│   ├── tires.py                 # Tire model (degradation, cliff effect)
│   ├── strategy.py              # Stint / Strategy data structures + validation
│   ├── simulation.py            # simulate_race: total time for a given strategy
│   ├── brute_force.py           # Exhaustive search over strategies
│   ├── dynamic_programming.py   # DP-based optimizer
│   ├── external_factors.py      # SafetyCar model + SC_PIT_LOSS_FACTOR / SC_LAP_TIME_FACTOR
│   ├── stochastic_dp.py         # DP optimizer accounting for safety car risk
│   └── circuit_profiles.py      # Calibrated per-circuit profiles (auto-generated, do not edit)
├── examples/
│   ├── run_basic_simulation.py
│   ├── compare_algorithms.py    # Brute-force vs. dynamic programming
│   ├── compare_sc_scenarios.py  # Stochastic DP under different safety car risk levels
│   ├── run_circuits.py          # Applies the calibrated profiles across all circuits
│   ├── calibrate_tires.py       # Also defines the shared CIRCUIT_GROUPS
│   ├── calibrate_sc.py
│   ├── calibrate_pit_stop.py
│   └── generate_circuit_profiles.py  # Regenerates src/circuit_profiles.py
├── tests/
│   ├── test_tires.py
│   ├── test_strategy.py
│   ├── test_simulation.py
│   ├── test_brute_force.py
│   ├── test_dynamic_programming.py
│   └── test_stochastic_dp.py
└── README.md
```