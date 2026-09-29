# V3 — Finite Liquid-Buffer and Closed-Wall Sensitivity

## Objective

Determine whether the synthetic bilateral result is materially controlled by finite liquid-buffer size or reflected closed-wall disturbances before any real porous-media geometry is attempted.

## Base case

Use the accepted V2 implementation and physics.

Do not change wetting, surface tension, viscosity, channel geometry, or active central length while varying the liquid-buffer thickness.

## Required sweep

Run at least three symmetric buffer thicknesses.

Suggested nondimensional set relative to the accepted V2 baseline buffer B:

- 0.5 B
- 1.0 B
- 2.0 B

If 0.5 B is too small to contain the initialized liquid region cleanly, use 1 B / 2 B / 4 B and state why.

The absolute buffer values must be recorded.

## Required observables

For each buffer size:

- left/right front trajectories;
- time to central-pocket isolation;
- gas connectivity state;
- trapped-cluster volume at comparable post-isolation states;
- cluster mean rho/p;
- global colour-mass drift;
- outer-wall density/pressure oscillation amplitude/time history;
- collision-region velocity extrema;
- any liquid depletion or interface approach to outer BB walls.

Use comparable event-based states where possible rather than comparing only equal absolute timestep.

## Provisional v0.1 promotion rule

The purpose is to detect large first-order buffer artefacts, not to claim continuum convergence.

PASS requires:

1. all V2 hard stability/mass/symmetry gates remain satisfied for all sweep cases;
2. the 1 B and 2 B cases produce pre-isolation front trajectories that differ by <= 5% in the selected normalized front-position metric over their common comparison interval;
3. time to central-pocket isolation differs by <= 5% between 1 B and 2 B;
4. no case shows the active liquid/gas interface interacting with the outer closed wall before the central isolation event;
5. no unexplained reflected-wave feature materially changes the invasion trajectory;
6. trapped-volume and pocket-pressure differences are reported but are not required to agree within a hard tolerance in v0.1.

The 5% values are project engineering gates used to decide whether a larger complex simulation is worthwhile. They are not literature-derived validity thresholds.

If 1 B and 2 B fail the 5% gates but 2 B and a newly added 4 B case converge, the reviewer may request one bounded rework adding 4 B. Do not silently expand the sweep indefinitely.

## Reviewer emphasis

- Confirm only buffer size changed.
- Compare event-aligned states.
- Inspect outer-wall density/pressure histories for reflection signatures.
- Separate front-dynamics sensitivity from trapped-pocket sensitivity.
- Do not demand trapped-pocket convergence when the model interpretation itself remains diagnostic.
- Decide whether remaining buffer dependence would contaminate a porous-media result.

## Promotion

PASS -> mandatory CHECKPOINT_READY.

V3 PASS must never auto-start the real graphite/PCS episode.
