# Literature and Implementation Search — BI-SOLVER-CONSERVATION-FIX-001

Two-pass search executed **before** any solver code change (contract
section 3), on 2026-09-24, from the task worktree. Tools: web search
(Z.ai web_search_prime via WebSearch), HAL API, arXiv PDF retrieval,
and in-repo implementation inspection. This report records exact
queries, sources, what each supports and does NOT support, and whether
any source directly reproduces the repository's
`float32 inv_M column-sum -> linear drift` mechanism.

## Verdict up front

**No source was found that directly documents the exact repository
defect** (stored f32 D3Q19 MRT inverse matrix with
`sum_s inv_M[s,0] = 1 + 2^-26` producing a deterministic linear
~1.5e-8/step total-mass drift). This is consistent with the control
memo's own two-pass search. The repository diagnosis therefore remains
an original, implementation-specific finding (audit
`results/conservation_audit/`, external reviews). No literature
precedence is claimed. No search-derived candidate C2 is proposed (see
section C2 decision).

## Pass A — academic search

Queries (exact strings):

1. `lattice Boltzmann multiple relaxation time conserved moments
   collision invariants mass conservation float32 roundoff`
2. `lattice Boltzmann color gradient recoloring mass conservation
   per-component species drift correction`
3. `GPU lattice Boltzmann single precision mass conservation drift
   float32 accumulation error` /
   `lattice Boltzmann GPU float32 vs double precision mass conservation
   steps per second`
4. (memo-mandated sources inspected — list below)

### Findings

- **Dubois & Philippi 2025**, "Multiple relaxation times lattice
  Boltzmann schemes with projection", Phys. Fluids 37, 037179 (2025),
  DOI 10.1063/5.0255650-family; preprint companion **Dubois & Philippi
  2024**, "Multiresolution relaxation times lattice Boltzmann schemes
  with projection", arXiv:2412.17426 (HAL hal-04852028).
  - Supports: an *additional moment-space projection step* appended to
    MRT collision is a legitimate, published construction; conserved
    moments can be preserved by design while non-conserved moments are
    modified (used there to reduce bulk viscosity).
  - Does NOT support: any floating-point closure repair. Full-text scan
    of the preprint: 0 occurrences of precision/FP32/single-precision/
    mass conservation. Mechanistically unrelated to our defect (it
    changes the *discrete scheme*, not the rounding behaviour). Not a
    precedent for T1/T2; cited only as the closest *name-similar*
    literature family, explicitly distinguished.
  - Downloaded: `literature/dubois2024_mrt_projection_arxiv2412.17426.pdf`
    (source https://arxiv.org/pdf/2412.17426, accessed 2026-09-24).

- **Lehmann et al. 2022** (PRE 106, 015308; arXiv:2202.05643), as in the
  control memo.
  - Supports: FP32 is not inherently disqualified for LBM accuracy in
    benchmarked cases; precision choice is an engineering decision.
  - Does NOT support: any statement about MRT inverse-matrix closure or
    deterministic drift; benchmarks macroscopic accuracy, not
    conservation-identity closure.
  - Downloaded: `literature/lehmann2022_f32_lb_arxiv2202.05643.pdf`
    (accessed 2026-09-24).

- **Latva-Kokko & Rothman 2005** (PRE 71, 056702), **Leclaire et al.
  2012 recoloring operators** (Appl. Math. Modelling 36, 2237),
  **Leclaire et al. 3D color-gradient** (PRE 86, 2012): model-level
  constraints only (recoloring is *designed* to conserve component
  masses; conservation identities are the acceptance object). None
  discusses floating-point closure of those identities. Paywalled;
  stable identifiers recorded (DOIs in the control memo,
  `docs/research/bilateral_imbibition/CONSERVATION_FIX_LITERATURE_NOTE.md`);
  not re-downloaded (publisher paywall; global download rule satisfied
  by DOI record).

- **Zahid et al. 2025 review of color-gradient LBM** (Fluids 10(1):18,
  MDPI): OA but automated PDF retrieval blocked (403/HTML);
  DOI 10.3390/fluids10010018 recorded. Supports: recoloring-step
  formulation survey. Does not address precision closure.

- **Jiang et al. 2026 ternary mass-conservative recoloring preprint**
  (SSRN 10.2139/ssrn.7211143): per the control memo, demonstrates that
  total-mass conservation can hide per-component drift and that local
  conservative repartitioning is legitimate — the model-level
  justification for candidate C1. Ternary/miscible algorithm; its
  conservation logic for the *binary* case reduces to per-colour
  zeroth-moment closure, which is what C1 enforces directly. Not a
  source for the total-channel defect. (SSRN download blocked; DOI
  recorded in the memo.)

- **Mora 2023** (MIT DSpace, convection-diffusion with colour-gradient
  LBM): diffusion behaviour of RK/CG recoloring; no precision-closure
  content. Not pursued further.

- No paper found reporting a **deterministic linear-in-time mass drift
  from an f32-stored MRT inverse matrix**, nor "zeroth-moment
  projection of populations" as a floating-point repair.

## Pass B — targeted implementation search

Queries (exact strings):

1. `"MRT" lattice Boltzmann inverse moment transformation
   implementation "column sum" OR "conservation" matrix double
   precision storage GitHub`
2. `lattice Boltzmann MRT moment transformation matrix implementation
   site:github.com`
3. `"GitHub" MRT lattice Boltzmann moment matrix inverse transformation
   C++ OR CUDA code`
4. in-repo inspection (below)

### Findings

- No open-source MRT implementation surfaced that documents or
  discusses inverse-matrix **column-sum closure under f32 storage**.
  Community answer patterns treat conservation as structural (integer/
  orthogonal moment rows, S[conserved]=0) and are silent on the
  representation error of the stored inverse. Reference implementations
  inspected at search level: Palabos, OpenLB, waLBERla, NREL/marbles,
  lanl/LBM3RT, a D3Q19 `getM.c` gist — none found discussing the stored
  inverse's column sums. (No claim is made that they lack the issue —
  only that none documents it.)

- **In-repo implementation finding (new, this search)**: the 2D
  canonical solver `LBM/source_code/taichi_LBM3D/2phase/lbm_solver_cg.py`
  (D2Q9), from which the 3D solver's structure was ported, builds its
  f32 inverse the same way and exhibits the same defect class:
  `sum_s inv_M_2D[s,0] - 1 = +7.4505806e-09` (2^-27; half the 3D value
  2^-26) with `max |colsum[l>0]| = 5.6e-17`. Reproduced by importing the
  2D module's tables in a CPU process. Implication: the defect is an
  **implementation-family trait** (f64-inverse-cast-to-f32 table
  construction), inherited by the 3D port — supporting T1's premise
  that the table construction itself is the right place to test a
  repair, and out-of-scope-ly implying a ~7.5e-9/step total-channel
  floor exists in the 2D line as well (recorded only; 2D is frozen and
  not part of this task).

- Implementation techniques found in general GPU-LBM practice
  (search-level, no direct sources): periodic global mass
  renormalization, f64 accumulators for statistics only, FMA-friendly
  kernels. None addresses per-collision local closure; none is
  preferable to a local projection for our acceptance object (local
  identity, no one-sided bias).

## C2 decision (search-derived candidate)

No materially different conservative scheme applicable to this **binary
immiscible** color-gradient model was found. The ternary repartitioning
idea (Jiang et al.) reduces here to C1's per-colour zeroth-moment
projection. **C2 = not implemented**, justified by the absence of a
mechanistically distinct, applicable candidate.

## Candidate-list effect

The search confirms the contract's candidate set T0-T4 / C0-C1 without
additions. It additionally motivates measuring T1's device-side closure
explicitly (host-projected column sums do not guarantee device
accumulation closure — contract section 5 T1 note) and warns that the
2D line carries the same defect class (no action in this task).

## Access log

| source | retrieval | status |
|---|---|---|
| arXiv 2412.17426 (Dubois & Philippi 2024) | arxiv.org/pdf | downloaded, verified title |
| arXiv 2202.05643 (Lehmann et al. 2022) | arxiv.org/pdf | downloaded, %PDF-1.5 verified |
| MDPI Fluids 10(1):18 (Zahid 2025) | mdpi.com pdf | blocked (403/HTML); DOI recorded |
| HAL search API | api.archives-ouvertes.fr | used to identify preprint |
| PRE 71,056702 / PRE 86 / AMM 36 / SSRN 7211143 | — | paywalled; DOIs recorded in control memo |
| 2D canonical tables | local file import | executed (CPU process, read-only) |
