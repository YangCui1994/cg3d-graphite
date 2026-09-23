# V2 — Symmetric Bilateral Spontaneous Imbibition Verification

## Objective

Verify the numerical behaviour of two opposing capillary-driven wetting fronts in a deliberately simple symmetric resolved channel before introducing porous-media complexity.

## Physical problem

A central straight wetting channel/slit is initially filled with the non-wetting phase.

Finite wetting-liquid buffers exist on both x ends.

The outer x ends are explicit solid/bounce-back walls.

Both wetting fronts advance inward under the same wall wettability and surface tension.

No pressure/density reservoir forcing is used.
No imposed pressure gradient is used.

This case intentionally creates a sealed central non-wetting pocket as the fronts advance. It is a numerical stress/verification case, not a claim of realistic air compressibility.

## Symmetry constraints

- Left/right geometry must be exactly mirror-symmetric.
- Initial phase field must be exactly mirror-symmetric.
- Material/wettability field must be exactly mirror-symmetric.
- Outer liquid-buffer thickness must be equal on both sides.
- Any random perturbation is prohibited in the baseline.

## Required observables

Before front interaction:
- x_left(t);
- x_right(t);
- mirrored front-position error;
- individual x^2 versus t behaviour;
- left/right wetting-rate comparison.

During and after isolation/collision:
- minimum gas-gap thickness;
- gas connectivity to each buffer;
- central trapped-cluster volume;
- central cluster mean density and p=rho/3;
- cluster gas-mass proxy and global colour masses;
- binary and continuous phase saturation;
- collision-region umax/u_rms or local velocity extrema;
- minimum |psi| / interface-blend metric across the interaction region;
- cluster count and size with declared connectivity and periodicity.

## Hard gates

1. No NaN/Inf.
2. No operational stability-cap violation unless the reviewer explicitly treats the cap itself as the finding and escalates.
3. Exact geometry/IC symmetry verified programmatically.
4. Before interaction, mirrored front-position error remains <= max(2 lu, 2% of the one-sided travelled distance).
5. Before interaction, left/right fitted wetting-rate constants differ by <= 5%.
6. Global colour-mass accounting shows no unexplained systematic loss/gain.
7. The runner can identify when the central non-wetting phase loses connectivity to both liquid-buffer interfaces.
8. The final review explicitly distinguishes connected gas, trapped gas, and gas located in the liquid-buffer regions.
9. Collision/coalescence distance is reported but is not judged against an invented literature threshold.

Gates 4-5 are v0.1 engineering symmetry gates. They are not universal CG accuracy claims.

## Diagnostic-only findings

No hard pass/fail threshold is imposed for:
- collision distance in units of interface width;
- local spurious-current peak;
- minimum |psi| at interface overlap;
- pocket pressure magnitude;
- pocket compression ratio;
- final trapped volume.

These must be reported.

## Scientific interpretation boundary

Pocket rho/p/volume may be used to assess weak-compressibility/numerical behaviour.

Do not interpret the unit-density CG pocket as quantitatively validated real gas compression.

If promotion would require such an interpretation, return HUMAN_REQUIRED.

## Reviewer emphasis

- Independently verify symmetry and phase initialization.
- Check that apparent symmetry is not produced by averaging away local asymmetry.
- Inspect trajectories before interaction separately from collision behaviour.
- Inspect mass accounting through the moment of topology change.
- Confirm cluster connectivity logic matches the actual periodic axes of the synthetic geometry.
- Treat unexplained premature interface annihilation as a finding even if the run is stable.

## Promotion

PASS -> V3.
