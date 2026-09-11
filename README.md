# F1 Strategy Simulator

> Simulation and optimisation of Formula 1 pit stop strategy under tire degradation and fuel load.
 
> Personal project | 2026

## Overview

This project investigates how pit stop strategy affects total race time in Formula 1, and how that optimal strategy changes as the underlying model is made more realistic.

A simplified race is represented as a sequence of laps driven on a chosen tire compound, with each compound defined by a base lap time and a degradation profile. Different pit stop strategies are compared according to total race time, and increasingly capable search algorithms are used to find the fastest one as the space of possible strategies grows.

## Objective

The objective is to determine, for a given race length and tire model, the pit stop strategy that minimises total race time, and to study how this optimum shifts as degradation becomes non-linear and fuel load and external factors are taken into account.

Three search approaches are compared:

- an exhaustive (brute-force) search
- a dynamic programming approach
- a stochastic dynamic programming approach, accounting for the risk of a safety car period

## Data and Assumptions

No real telemetry data were used in the current version of this project. Tire behaviour (base lap time, degradation rate, cliff threshold) and race parameters (pit stop loss, fuel effect) are manually defined assumptions intended to represent plausible race conditions, informed by publicly available knowledge of Formula 1 tire compounds.

Four main modelling assumptions are used:

### Tire degradation
 
Each compound (soft, medium, hard) is assigned a base lap time and a degradation rate. Degradation is linear up to a compound-specific "cliff" lap, after which it switches to a steeper linear rate, representing the sudden performance drop-off observed on real tires past their optimal window.
 
### Fuel effect
 
Lap times decrease slightly over the course of the race as the car burns fuel and gets lighter, modelled as a fixed time gain per lap already completed, independent of tire compound.
 
### Pit stop cost
 
A fixed time penalty is applied for each pit stop.

### Safety car

A safety car period is modelled as a two-state Markov process rather than a fixed occurrence: on any given lap where the safety car is not active, it starts with probability `p_start`; on any given lap where it is active, it ends with probability `p_end` (implying an average duration of `1 / p_end` laps). While active, lap times are set to a fixed value, independent of tire compound, and the pit stop cost is reduced. Tire wear is assumed negligible while the safety car is active, so tire age does not increase during those laps.

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

## Installation & Usage
 
```bash
pip install -r requirements.txt
```
 
Run any example from the project root:
 
```bash
PYTHONPATH=src python3 examples/run_basic_simulation.py
PYTHONPATH=src python3 examples/compare_strategies.py
PYTHONPATH=src python3 examples/compare_sc_scenarios.py
```

`run_basic_simulation.py` prints, for a given strategy, the strategy, the race length, and the total race time.

`compare_strategies.py` prints, for a given race length, the best strategy and computation time found by exhaustive search (for a range of pit stop counts) alongside the dynamic programming approach, together with a consistency check between the two.

`compare_sc_scenarios.py` prints, for a given race length, the expected race time and resulting strategy under several safety car risk levels, compared against the no-risk baseline.

## Results
 
On a 50-lap race with three compounds, both exhaustive search and dynamic programming converge to the same optimal race time (4551.13s), achieved with two pit stops. Exhaustive search requires querying every valid combination of compounds and stint lengths for each candidate number of stops (up to four) for a total of 29s of computation, while the dynamic programming approach finds the same optimum in approximately 0.03 seconds by avoiding redundant recomputation of shared race states.
 
The two methods return strategies with a different stint order for an identical total time — expected, since nothing in the current (linear) degradation model favours one ordering of otherwise identical stints over another.

Under increasing safety car risk, the expected race time rises accordingly (e.g. +12s under an unlikely safety car scenario, up to +160s under a very likely one, on the same 50-lap race), and the optimal strategy shifts slightly, with pit stops occurring marginally earlier as safety car risk increases.
 
## Limitations
 
- **Modelling assumptions**: tire degradation parameters and pit stop cost are manually defined rather than derived from real telemetry data.
- **Decoupled degradation and fuel effects**: fuel load is assumed not to affect tire degradation, which is a simplification of real tire behaviour.
- **`min_stint_length` as a uniform constraint**: this pruning threshold is applied uniformly throughout the race to keep the search space tractable. It is not derived from an official regulation, and there may be race conditions under which a very short stint would in fact be optimal.
- **No opponent modelling**: strategies are evaluated in isolation; race dynamics such as undercut/overcut relative to a competitor are not yet modelled.

These limitations provide potential directions for improving the model.
 
## Technologies
 
- Python

## Repository Structure
 
```text
.
├── src/
│   ├── tires.py                 # Tire model (degradation, cliff effect)
│   ├── strategy.py              # Stint / Strategy data structures + validation
│   ├── simulation.py            # simulate_race: total time for a given strategy
│   ├── brute_force.py           # Exhaustive search over strategies
│   ├── dynamic_programming.py   # DP-based optimizer
│   ├── external_factors.py      # SafetyCar model (probabilistic)
│   └── stochastic_dp.py         # DP optimizer accounting for safety car risk
├── examples/
|   ├── run_basic_simulation.py
|   ├── compare_strategies.py
|   ├── compare_sc_scenarios.py
└── README.md
```