"""Termination / numerical-health reporting tests (CG3D-CONVERGENCE-DIAG-003).

Deterministic pure-Python tests for the additive reporting layer around
`cg3d.protocol.run_hold`:

  row["termination"]       why the rung stopped — process completion, the
                           legacy reason, and the converged / step-limit /
                           safety-limit statements as separate flags;
  row["numerical_health"]  which sampled diagnostics were ever NaN/Inf.

The fake system below implements only the members `run_hold` touches
(s.step / set_ladder / measure / pore_cells), so the rung loop runs for
real with no LBM step, no Taichi kernel and no GPU.  What is under test is
the REPORTING, not the convergence policy: the quasi-steady threshold,
window, minimum-step, qs_mode and umax-cap rules are the accepted ones and
are exercised here, never re-derived.

`scenario_specs()` keeps the four cases as data so that the same scenarios
can be replayed against a pre-change copy of run_hold to show the stopping
behaviour is untouched (see the published evidence bundle).

Run:  python tests/test_termination_diagnostics.py   (exit 0 = pass)
"""
import json
import os
import sys
from types import SimpleNamespace

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cg3d.diagnostics import (  # noqa: E402
    QUASI_STEADY, MAX_STEPS, UMAX_CAP, NumericalHealthTracker,
    termination_record)
from cg3d.protocol import run_hold  # noqa: E402

FAIL = []

# The row `run_hold` returned before this task; the new records must be
# additive on top of exactly this set.
LEGACY_ROW_KEYS = {'d', 'pc_nominal', 'pc_measured', 'rho_in_mean',
                   'rho_out_mean', 'p_in_mean', 'p_out_mean', 'u_rms',
                   'u_bulk_x', 'flux_r_rate', 'flux_b_rate', 'steps',
                   'reason', 's_nw', 's_nw_binary', 'convergence',
                   'umax_last', 'wall_s'}
ADDED_ROW_KEYS = {'termination', 'numerical_health'}

RUNG_D = 0.06


def check(name, cond):
    print(('PASS ' if cond else 'FAIL ') + name)
    if not cond:
        FAIL.append(name)


def _json_ok(obj, **kw):
    try:
        json.dumps(obj, **kw)
        return True
    except (TypeError, ValueError):
        return False


# --------------------------------------------------------------------------
# fake system


def sample_flat(_step, _n):
    """All-finite, all-flat diagnostics — the shape OpenSystem.measure()
    returns, carrying every field run_hold / eval_convergence read."""
    return dict(s_nw=0.42, s_nw_binary=0.40, umax=1e-3,
                rho_in_mean=1.0, rho_out_mean=1.0,
                p_in_mean=1 / 3.0, p_out_mean=1 / 3.0,
                pc_band_in=0.35, pc_band_out=0.32, pc_measured=0.03,
                u_rms=1e-3, u_bulk_x=0.0,
                inj_r=0.0, inj_b=0.0, inj_m=0.0)


def sample_drift(step, _n):
    """s_nw drifts 1e-2/step, far above qs_tol=1e-3: the saturation slope
    never qualifies, so the rung must burn the whole step budget."""
    return dict(sample_flat(step, _n), s_nw=0.30 + 0.01 * step)


def sample_umax_spike(step, _n):
    """Every metric stays finite and flat; only umax crosses the safety cap
    (at step 3, i.e. before a 9-sample quasi-steady window can exist)."""
    return dict(sample_flat(step, _n), umax=0.5 if step >= 3 else 1e-3)


def sample_nonfinite(step, _n):
    """pc_measured (a pressure indicator, not the sat-mode criterion) goes
    NaN from step 2, u_bulk_x goes +Inf from step 4, saturation stays flat:
    the sat-mode rung still exits quasi-steady."""
    m = sample_flat(step, _n)
    if step >= 2:
        m['pc_measured'] = float('nan')
    if step >= 4:
        m['u_bulk_x'] = float('inf')
    return m


class FakeSolver:
    """run_hold only ever calls step() on the solver."""

    def __init__(self):
        self.n = 0

    def step(self):
        self.n += 1


class FakeSystem:
    """Minimal OpenSystem stand-in: the four members run_hold uses.
    `sample_fn(step, sample_index) -> dict` scripts the measurements."""

    def __init__(self, sample_fn):
        self.s = FakeSolver()
        self.pore_cells = 1000.0
        self._sample_fn = sample_fn
        self.n_samples = 0
        self.ladders = []

    def set_ladder(self, d):
        self.ladders.append(d)

    def measure(self):
        self.n_samples += 1
        return self._sample_fn(self.s.n, self.n_samples)


def ns(**over):
    """Config namespace with run_hold's fields.  These values make a flat
    fake reach the quasi-steady test at step 9 (every=1, qs_window=10,
    min_steps=5, window span 8 >= 10*0.8)."""
    cfg = dict(every=1, min_steps=5, max_steps=30, qs_window=10, qs_tol=1e-3,
               qs_mode='sat', pc_drift_tol=0.01, flux_tol=1e-6,
               u_rel_tol=0.05, umax_cap=0.1, dump_every=0)
    cfg.update(over)
    return SimpleNamespace(**cfg)


def scenario_specs():
    """The four required semantic cases as data: name -> (config, sample_fn,
    description)."""
    return {
        'quasi_steady': (
            ns(), sample_flat,
            'saturation slope within qs_tol, sat mode: configured criterion '
            'reached at step 9; all sampled diagnostics finite'),
        'max_steps': (
            ns(max_steps=25), sample_drift,
            's_nw drifts 1e-2/step (> qs_tol=1e-3): criterion not reached '
            'inside max_steps=25; all sampled diagnostics finite'),
        'umax_cap': (
            ns(), sample_umax_spike,
            'umax=0.5 crosses umax_cap=0.1 at step 3 while every metric stays '
            'finite: safety-limit exit, not a numerical-health failure'),
        'nonfinite_observation': (
            ns(), sample_nonfinite,
            'pc_measured=NaN from step 2 and u_bulk_x=Inf from step 4; the '
            'sat-mode criterion (saturation only) is still satisfied, so the '
            'rung exits quasi-steady while numerical health is not finite'),
    }


def run_scenario(name, qs_mode=None, runner=None):
    """Run one scenario through `run_hold` (or `runner`, e.g. a pre-change
    copy of run_hold, for the A/B stopping comparison)."""
    cfg, fn, _desc = scenario_specs()[name]
    if qs_mode is not None:
        cfg = ns(**dict(vars(cfg), qs_mode=qs_mode))
    return (runner or run_hold)(cfg, FakeSystem(fn), RUNG_D, name)


def example_records():
    """The four scenarios in the shape published as evidence.  Only finite
    values are kept, so the result is strict JSON."""
    out = {}
    for name, (_cfg, _fn, desc) in scenario_specs().items():
        row = run_scenario(name)
        out[name] = dict(description=desc, steps=row['steps'],
                         reason=row['reason'],
                         convergence_exit=row['convergence']['exit'],
                         termination=row['termination'],
                         numerical_health=row['numerical_health'])
    return out


# --------------------------------------------------------------------------
# required semantic cases


def test_quasi_steady_exit():
    for mode in ('sat', 'multi'):
        row = run_scenario('quasi_steady', qs_mode=mode)
        term = row['termination']
        check(f'[{mode}] rung exits quasi-steady at step 9',
              row['reason'] == QUASI_STEADY and row['steps'] == 9)
        check(f'[{mode}] termination.converged is True',
              term['converged'] is True)
        check(f'[{mode}] no step limit and no safety limit reported',
              term['step_limit_reached'] is False
              and term['safety_limit_triggered'] is False)
        check(f'[{mode}] process_completed is True and qs_mode is echoed',
              term['process_completed'] is True and term['qs_mode'] == mode)
        check(f'[{mode}] numerical health is finite over 9 samples',
              row['numerical_health']['finite'] is True
              and row['numerical_health']['sample_count'] == 9
              and row['numerical_health']['nonfinite_fields'] == []
              and row['numerical_health']['first_nonfinite_step'] is None)


def test_max_steps_exit():
    row = run_scenario('max_steps')
    term = row['termination']
    check('max-steps: rung ran the full budget of 25 steps',
          row['reason'] == MAX_STEPS and row['steps'] == 25)
    check('max-steps: converged is False', term['converged'] is False)
    check('max-steps: step_limit_reached is True',
          term['step_limit_reached'] is True)
    check('max-steps: no safety limit reported',
          term['safety_limit_triggered'] is False)
    check('max-steps: process_completed is True',
          term['process_completed'] is True)
    check('max-steps: finite metrics are not a numerical failure',
          row['numerical_health']['finite'] is True
          and row['numerical_health']['nonfinite_fields'] == [])


def test_umax_cap_exit():
    row = run_scenario('umax_cap')
    term = row['termination']
    check('umax-cap: rung exits at step 3',
          row['reason'] == UMAX_CAP and row['steps'] == 3)
    check('umax-cap: converged is False', term['converged'] is False)
    check('umax-cap: safety_limit_triggered is True',
          term['safety_limit_triggered'] is True)
    check('umax-cap: no step limit reported',
          term['step_limit_reached'] is False)
    check('umax-cap: finite umax=0.5 keeps numerical health finite',
          row['numerical_health']['finite'] is True
          and row['numerical_health']['nonfinite_fields'] == []
          and row['numerical_health']['first_nonfinite_step'] is None)
    check('umax-cap: last sampled umax is the finite excursion',
          row['umax_last'] == 0.5)


def test_nonfinite_observation():
    row = run_scenario('nonfinite_observation')
    health = row['numerical_health']
    check('non-finite: both bad fields reported by name',
          health['finite'] is False
          and health['nonfinite_fields'] == ['pc_measured', 'u_bulk_x'])
    check('non-finite: first bad step and its fields recorded',
          health['first_nonfinite_step'] == 2
          and health['first_nonfinite_fields'] == ['pc_measured'])
    check('non-finite: per-field sample counts recorded',
          health['nonfinite_counts'] == {'pc_measured': 8, 'u_bulk_x': 6}
          and health['sample_count'] == 9)
    check('non-finite: a non-finite sample does not change the exit rule',
          row['steps'] == 9 and row['reason'] == QUASI_STEADY)


def test_convergence_and_health_are_independent():
    row = run_scenario('nonfinite_observation')
    check('converged=True and finite=False coexist in one record',
          row['termination']['converged'] is True
          and row['numerical_health']['finite'] is False)
    row = run_scenario('max_steps')
    check('converged=False with finite=True is reported too',
          row['termination']['converged'] is False
          and row['numerical_health']['finite'] is True)


def test_legacy_fields_stay_consistent():
    for name in scenario_specs():
        row = run_scenario(name)
        term = row['termination']
        check(f'[{name}] row reason == convergence exit == termination reason',
              row['reason'] == term['reason']
              and row['convergence']['exit']['reason'] == term['reason'])
        check(f'[{name}] convergence exit mode == termination qs_mode',
              row['convergence']['exit']['mode'] == term['qs_mode'] == 'sat')
        flags = (term['converged'], term['step_limit_reached'],
                 term['safety_limit_triggered'])
        check(f'[{name}] at most one stopping statement is true',
              sum(1 for f in flags if f) <= 1)
        check(f'[{name}] row keys = legacy set + two additive records',
              set(row) == LEGACY_ROW_KEYS | ADDED_ROW_KEYS)
        check(f'[{name}] convergence record keeps its existing fields',
              set(row['convergence']) >= {'criteria_passed', 'thresholds',
                                          'exit'}
              and 'reason' in row['convergence']['exit'])
        # the non-finite row carries NaN/Inf metrics by construction (Python
        # json writes them as NaN/Infinity); the others must be strict JSON
        check(f'[{name}] row stays JSON-serializable',
              _json_ok(row, allow_nan=name == 'nonfinite_observation'))
        check(f'[{name}] both new records are strict JSON',
              _json_ok(row['termination'])
              and _json_ok(row['numerical_health']))


def test_helper_units():
    """The helpers themselves, including values that are not real scalars."""
    unknown = termination_record('some-future-reason', 'multi')
    check('termination_record: unknown reason reports no flag but the reason',
          unknown['process_completed'] is True
          and unknown['reason'] == 'some-future-reason'
          and unknown['qs_mode'] == 'multi'
          and unknown['converged'] is False
          and unknown['step_limit_reached'] is False
          and unknown['safety_limit_triggered'] is False)
    check('termination_record: every required key is present',
          set(unknown) == {'process_completed', 'reason', 'converged',
                           'step_limit_reached', 'safety_limit_triggered',
                           'qs_mode'})

    tr = NumericalHealthTracker()
    empty = tr.record()
    check('tracker: no samples reports finite with sample_count 0',
          empty['finite'] is True and empty['sample_count'] == 0
          and empty['nonfinite_fields'] == []
          and empty['first_nonfinite_step'] is None)

    tr.observe(7, dict(ok=1.0, missing=None, text='n/a',
                       vect=np.array([1.0, 2.0]), boxed=np.float32(np.inf),
                       flag=True))
    rec = tr.record()
    check('tracker: unavailable values ignored, NaN/Inf caught',
          rec['nonfinite_fields'] == ['boxed']
          and rec['first_nonfinite_step'] == 7
          and rec['first_nonfinite_fields'] == ['boxed']
          and rec['sample_count'] == 1
          and rec['fields_observed'] == ['boxed', 'flag', 'ok'])
    tr.observe(9, dict(ok=float('-inf')))
    rec = tr.record()
    check('tracker: first bad step stays the first, counts accumulate',
          rec['nonfinite_fields'] == ['boxed', 'ok']
          and rec['first_nonfinite_step'] == 7
          and rec['first_nonfinite_fields'] == ['boxed']
          and rec['nonfinite_counts'] == {'boxed': 1, 'ok': 1}
          and rec['sample_count'] == 2)
    check('tracker: record is strict JSON', _json_ok(rec))


def main():
    test_helper_units()
    test_quasi_steady_exit()
    test_max_steps_exit()
    test_umax_cap_exit()
    test_nonfinite_observation()
    test_convergence_and_health_are_independent()
    test_legacy_fields_stay_consistent()
    if FAIL:
        print(f'FAIL: {FAIL}')
        sys.exit(1)
    print('ALL PASS')


if __name__ == '__main__':
    main()
