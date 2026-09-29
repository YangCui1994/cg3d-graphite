# V1 — Single-Front Dynamic Wetting Verification

## Objective

Verify that the current wall-colour wetting implementation produces defensible spontaneous capillary filling dynamics in a simple, well-resolved synthetic geometry before bilateral interaction is introduced.

## Physical problem

One wetting phase invades a straight resolved capillary/slit containing the non-wetting phase.

There is no externally imposed pressure difference across the capillary.

The non-wetting phase must have a defined escape path in this validation so that V1 tests moving-contact-line/capillary dynamics rather than trapped-gas compression.

The implementation may reuse existing phase-selective/open-system infrastructure at equal nominal pressure if that preserves zero imposed pressure difference. Any alternative must be documented.

## Geometry design constraints

- Synthetic smooth geometry only.
- Characteristic channel radius/half-width must be comfortably larger than the approximately 2.2 lu interface width.
- v0.1 design target: at least about six interface widths from wall to centreline. This is a conservative project design choice, not a literature validity threshold.
- Geometry and initialization must be deterministic and reproducible.

## Required implementation

Provide a dedicated validation driver/test that records:

- front position versus time;
- front-position extraction definition;
- liquid and gas colour mass accounting;
- pressure/density summaries;
- umax/u_rms;
- optional dynamic apparent contact-angle diagnostic if robustly measurable;
- exact physical/lattice parameters.

Do not run on real graphite.

## Reference behaviour

Compare the post-transient front evolution with the appropriate Lucas-Washburn relation for the chosen two-phase configuration.

Do not force the early inertial/transient interval into the asymptotic fit.

The fit-window algorithm/rule must be written before interpreting the result and reported with the evidence.

## Provisional v0.1 engineering gates

These are project gates for autonomous promotion, not universal literature truths.

1. No NaN/Inf and no operational stability-cap violation.
2. Correct zero imposed pressure-difference setup.
3. Monotonic capillary advance after initialization.
4. A post-transient interval exists that spans at least 40% of the usable pre-boundary-interaction trajectory.
5. On that interval, x^2 versus t has R-squared >= 0.98.
6. The measured Lucas-Washburn slope/prefactor differs from the chosen analytic relation by <= 10%.
7. Mass accounting closes within the stage's measured numerical floor and shows no systematic drift trend.
8. Repeating one case at a larger resolved channel size does not qualitatively change the conclusion; normalized slope difference should be reported. A hard cross-resolution tolerance is not imposed in v0.1 unless justified by the run.

If gates 4-6 fail but the trajectory is stable, reviewer must decide CHANGES_REQUESTED only if a finite numerical/measurement correction exists. Otherwise use HUMAN_REQUIRED.

## Diagnostics, not hard gates

- early-time departure from Lucas-Washburn;
- local spurious-current peak near the moving contact line;
- dynamic vs static apparent contact angle;
- dependence on channel resolution;
- interface-shape anisotropy.

## Reviewer emphasis

- Confirm that the comparison equation matches the actual BC/viscosity configuration.
- Confirm the fit window was not cherry-picked after seeing the answer.
- Confirm the front extractor is robust to diffuse interface thickness.
- Confirm static contact-angle validation was not treated as dynamic proof.
- Inspect mass and velocity histories, not only the final fit.

## Promotion

PASS -> V2.
