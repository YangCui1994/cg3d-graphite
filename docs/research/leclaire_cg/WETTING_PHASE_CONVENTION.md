# Wetting / Phase Convention — Leclaire CG Reference Line

Status: **normative**  
Corrected after Pass-4 fresh review / external review R3.

## 1. Fixed phase identity

~~~text
red  = electrolyte / liquid / wetting phase
blue = gas / non-wetting phase
~~~

\[
\psi = \frac{\rho_{red}-\rho_{blue}}{\rho_{red}+\rho_{blue}}
\]

Therefore positive psi is liquid/red, negative psi is gas/blue, and
\(F=\nabla\psi\) points gas -> liquid.

## 2. Contact-angle definition

Every project-reported contact angle is

\[
\boxed{\theta=\theta_{\rm liquid}}
\]

measured through the red/liquid/electrolyte phase.

If a source or diagnostic uses the gas-side angle, convert explicitly with
\(\theta_{\rm liquid}=180^\circ-\theta_{\rm gas}\).

## 3. R1 solid indicator and wall normal

Use

~~~text
g = 1 in solid
g = 0 in fluid
~~~

R1 Eqs.(34)-(38) define

\[
\boxed{\mathbf n_w=+\nabla g/|\nabla g|}
\]

for the smoothed solid image. With this binary convention the normal points
**fluid -> solid**.

This is the canonical L17_CORE branch. The previous Pass-4 choice
\(-\nabla g/|\nabla g|\) is superseded.

The wall-normal sign is not a physical tuning parameter. A debug override may
exist only as an explicitly non-canonical regression switch.

## 4. Liquid-side sessile-cap relation

For a red/liquid sessile cap occupying the +z side of a flat wall at z=z_w,
with fitted radius R and centre z_c,

\[
\boxed{\cos\theta_{\rm liquid}=-(z_c-z_w)/R}
\]

The previous Pass-4 instrument used the opposite sign and therefore returned
the complementary angle.

## 5. Independent analytic lock

Before any wetting simulation is accepted, analytic tests must independently
verify 30/60/90/120/150 degrees.

The construction must not reuse the measurement formula as its generator.
It must verify:

1. the liquid-side angle is recovered;
2. +grad(g) is the canonical R1 wall-normal branch;
3. flipping the normal produces the complementary branch and is rejected;
4. the R1 secant operator converges to the branch consistent with the phase
   definitions above.

## 6. Rendering convention

All validation renderings use:
- positive psi = liquid/red;
- negative psi = gas/blue;
- psi=0 = fluid-fluid interface;
- solid = neutral distinct material;
- captions explicitly state "contact angle through liquid/red".

Sessile-drop figures must show the wall, interface contour, fitted curve and
liquid-side angle wedge.

## 7. Current scientific consequence

Pass-4 contact-angle PASS is withdrawn.

Pass-4 slit-Pc geometry is valid and produced approximately correct magnitude
with opposite sign, consistent with the superseded complementary-angle
convention.

Pass-4 Jurin geometry passed its reachability precheck but expelled liquid under
the same superseded convention.

The next closure run fixes convention/instrument first and reruns those existing
geometries without redesign unless a separate defect is demonstrated.
