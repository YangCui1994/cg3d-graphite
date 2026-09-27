# Wetting / Phase Convention — Leclaire CG Reference Line

Status: **normative**
Decision date: 2026-09-27

This convention is fixed for \`L17_CORE\` and all validation artifacts unless a
case explicitly declares a different physical phase mapping.

## 1. Phase identity

\`\`\`text
red  = electrolyte / liquid / wetting phase
blue = gas / non-wetting phase
\`\`\`

Component order parameter:

\[
\psi = \frac{\rho_{red}-\rho_{blue}}{\rho_{red}+\rho_{blue}}.
\]

Therefore:

\`\`\`text
psi = +1  -> liquid/electrolyte
psi = -1  -> gas
F = grad(psi) points from gas/blue toward liquid/red
\`\`\`

## 2. Contact-angle definition

Every reported contact angle is:

\[
\boxed{\theta = \theta_{\rm liquid}}
\]

i.e. **measured through the red/liquid/electrolyte phase**.

Never report an unqualified angle if it is measured through the blue/gas phase.
If an external source uses the opposite convention, convert it explicitly and
record the conversion.

## 3. Solid indicator and wall normal

Use:

\`\`\`text
g = 1 in solid
g = 0 in fluid
\`\`\`

The canonical wall normal for \`L17_CORE\` is the normal pointing **from solid
into fluid**:

\[
\boxed{
\mathbf n_w = -\frac{\nabla g}{|\nabla g|}
}
\]

for the smoothed solid image used by R1.

With the current implementation convention, this corresponds to the historical
\`wetting_sign = -1\` arm.

The sign is no longer a tunable physical parameter of \`L17_CORE\`. A diagnostic
override may exist for regression/debugging, but it must be labelled
non-canonical.

## 4. Required analytic convention lock

Before any wetting simulation is accepted, add a non-LBM geometric unit test
using analytic planar interfaces at:

- 60 deg;
- 90 deg;
- 120 deg.

The test must construct the known wall and interface normals and verify that the
combination of:

- \`g\`;
- \`n_w\`;
- \`F = grad(psi)\`;
- the R1 Eq.(30)-(33) rotation;
- the measurement convention through red/liquid;

returns the requested \(\theta_{\rm liquid}\).

This test is the convention authority. A sessile-droplet simulation must not be
used to choose the sign by calibration.

## 5. Rendering convention

All validation renderings use:

- red/liquid/electrolyte: positive \(\psi\);
- blue/gas: negative \(\psi\);
- interface: \(\psi=0\);
- solid: visually distinct neutral material;
- captions state "contact angle through liquid/red".

For A/B plots, the phase convention and view orientation must be identical.
