"""CG3D bilateral-episode A0-R1/R2 generic-engine tests (offline).

  python tests/test_episode_runner_generic.py      (exit 0 = pass)

Exercises the SAME generic orchestration path (start_stage / run_round
/ run_episode / publish_round / approve_a0_from_text) that the real
smoke and V0-V3 use, with stubbed ZCode sessions (no GLM, no GPU,
fully deterministic).  Scenario coverage maps to the A0 external
review acceptance lists:

  A0_EXTERNAL_REVIEW.md (R1) — validation-only unchanged-source review,
  CHANGES_REQUESTED attempt increment, rework consumes the immediately
  prior review, fresh reviewer sessions, failed/timed-out/stale
  sessions never advance, PASS auto-promotes without start-stage, max
  attempts -> HUMAN_REQUIRED, HUMAN_REQUIRED stop, terminal stage stops
  at CHECKPOINT_READY, durable publication produced, explicit A0
  authorization required.

  A0_EXTERNAL_REVIEW_R2.md — product-branch push at every publication
  boundary (B9), frozen contract snapshot with live-drift inertness and
  tamper refusal (B10), A0 approval requires a full candidate binding
  (B11), failed executor session that committed -> terminal orphan,
  never silently reused (B12), failed reviewer retries on the SAME
  frozen candidate without rerunning the executor (B13), worktree
  identity/expected-HEAD enforcement at attach (H4), persisted ERROR
  terminates run-episode deterministically (H5).

  A0_EXTERNAL_REVIEW_R3.md — publication-safe promotion: a decided
  round publishes BEFORE the PASS/promotion is applied, a publication
  failure leaves ERROR/publish_pending with no promotion exposed, and
  recovery re-publishes without rerunning sessions (B14); a valid
  executor session that leaves a dirty tree is a terminal orphan whose
  unreviewed state is never pushed (B15); approve-a0 freezes the
  approved runner blob and every real entry point refuses a changed
  runner (B16).
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0,
                str(REPO / ".agent" / "episodes" / "bilateral-imbibition-v0.1"
                   / "runner"))
import episode_runner as er                                # noqa: E402

FAIL = []
TOKEN = er.SMOKE_TOKEN


def check(name, cond, detail=''):
    print(('PASS ' if cond else 'FAIL ') + name
          + ('  ' + detail if detail else ''), flush=True)
    if not cond:
        FAIL.append(name)


def git(wt, *args, check=True):
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0')
    p = subprocess.run(['git', '-C', str(wt), *args], text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       env=env)
    if check and p.returncode != 0:
        raise AssertionError(f"git {args}: {p.stderr}")
    return p.stdout.strip()


class StubLauncher:
    """Deterministic stand-in for headless ZCode sessions.  Implements
    the marker/validation-only task semantics from prompt text, with a
    queue of per-call failure overrides for B5/B12/B13 scenarios.
    `skip_artifact=True` makes the session leave NO side effects at all
    (clean failure); by default a failing session still commits the
    marker first (the B12 orphan shape)."""

    def __init__(self, wt):
        self.wt = wt
        self.calls = []            # dicts(prompt, resume, session_id, role)
        self.n = 0
        self.failures = []         # queued dicts applied to executor/reviewer

    def _fail_override(self, role):
        for i, f in enumerate(self.failures):
            if f.get('_role', 'executor') == role:
                return self.failures.pop(i)
        return {}

    def __call__(self, worktree, prompt, *, resume, timeout_s, log_path):
        self.n += 1
        sid = f'stub-sess-{self.n:03d}'
        role = ('executor' if 'ZCode EXECUTOR' in prompt else 'reviewer')
        ov = self._fail_override(role)
        self.calls.append(dict(prompt=prompt, resume=resume,
                               session_id=sid, role=role))
        result = dict(command=['stub'], prompt=prompt, resume=resume,
                      started_at='', finished_at='', elapsed_s=0.0,
                      exit_code=ov.get('exit_code', 0),
                      timed_out=ov.get('timed_out', False),
                      stdout=json.dumps({'sessionId': sid
                                         if not ov.get('no_session_id')
                                         else None}),
                      stderr='')
        if role == 'executor':
            self._executor(prompt, ov)
        else:
            self._reviewer(prompt, ov)
        return er.SessionResult(result)

    def _report_path(self, prompt):
        m = re.search(r'execution report to (\S+?) ', prompt) or \
            re.search(r'execution report to (\S+)', prompt)
        return Path(m.group(1))

    def _review_path(self, prompt):
        m = re.search(r'Write your review to (\S+?) ', prompt) or \
            re.search(r'Write your review to (\S+)', prompt)
        return Path(m.group(1))

    def _executor(self, prompt, ov):
        if ov.get('skip_artifact'):
            return
        rep = self._report_path(prompt)
        rep.parent.mkdir(parents=True, exist_ok=True)
        if 'VALIDATION-ONLY stage' in prompt:
            sha = git(self.wt, 'rev-parse', 'HEAD')
            rep.write_text(
                '# EXECUTION REPORT\n\n- stage/attempt: see prompt\n'
                f'- candidate: validation-only, unchanged {sha}\n',
                encoding='utf-8')
            return
        marker = self.wt / 'smoke' / 'marker.md'
        marker.parent.mkdir(exist_ok=True)
        att_m = re.search(r'attempt (\d+)', prompt)
        att = att_m.group(1) if att_m else '?'
        if 'WITHOUT the required token' in prompt:      # planted defect
            marker.write_text('# marker\n\nround-1 placeholder without '
                              f'token (attempt {att})\n', encoding='utf-8')
        else:
            marker.write_text(f'# marker\n\n{TOKEN}\nfixed round '
                              f'(attempt {att})\n', encoding='utf-8')
        git(self.wt, 'add', 'smoke/marker.md')
        git(self.wt, 'commit', '-m', f'stub executor marker round {att}')
        if ov.get('dirty_extra'):
            (self.wt / 'smoke' / 'leftover.txt').write_text(
                'uncommitted', encoding='utf-8')
        rep.write_text('# EXECUTION REPORT\n\n- candidate committed\n',
                       encoding='utf-8')

    def _reviewer(self, prompt, ov):
        if ov.get('skip_artifact'):
            return
        rev = self._review_path(prompt)
        rev.parent.mkdir(parents=True, exist_ok=True)
        stage = re.search(r'stage: (\S+)', prompt).group(1)
        attempt = re.search(r'attempt: (\d+)', prompt).group(1)
        sha = re.search(r'candidate: ([0-9a-f]{40})', prompt).group(1)
        rep = re.search(r'execution_report: (\S+)', prompt).group(1)
        marker = git(self.wt, 'show', f'{sha}:smoke/marker.md',
                     check=False)
        ok = TOKEN in (marker or '')
        force = ov.get('decision')
        decision = force or ('PASS' if ok else 'CHANGES_REQUESTED')
        extra = ('\nRESET_CONTEXT: NO\n' if decision ==
                 'CHANGES_REQUESTED' else '')
        rev.write_text(
            f'stage: {stage}\nattempt: {attempt}\ncandidate: {sha}\n'
            f'execution_report: {rep}\n\n# REVIEW\n\n'
            f'Decision: {decision}\n{extra}', encoding='utf-8')


class Harness:
    def __init__(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='ep-runner-test-'))
        self.wt = self.tmp / 'worktree'
        self.wt.mkdir()
        git(self.wt, 'init', '-q', '-b', 'test-episode-branch')
        git(self.wt, 'config', 'user.email', 'stub@test.local')
        git(self.wt, 'config', 'user.name', 'Stub')
        (self.wt / 'smoke').mkdir()
        (self.wt / 'smoke' / 'marker.md').write_text(
            '# base marker\n', encoding='utf-8')
        git(self.wt, 'add', 'smoke/marker.md')
        git(self.wt, 'commit', '-q', '-m', 'base')
        self.control = self.tmp / 'control'
        self.control.mkdir()
        self.base = git(self.wt, 'rev-parse', 'HEAD')
        self.cfg = dict(
            mode='smoke',
            state_path=self.tmp / 'state.json',
            branch='test-episode-branch',
            base=self.base,
            worktree=self.wt,
            stages=[
                dict(name='SMOKE-1',
                     contract=er.EPISODE_DIR / 'runner'
                     / 'SMOKE_CONTRACT.md',
                     task='marker', planted_defect=True,
                     validation_only=False),
                dict(name='SMOKE-2',
                     contract=er.EPISODE_DIR / 'runner'
                     / 'SMOKE_VALIDATION_CONTRACT.md',
                     task='validation-only', validation_only=True),
            ],
            evidence_subdir='TEST', run_root=self.tmp / 'runtime',
            timeout_s=60,
        )
        self.state = er.fresh_state(self.cfg, episode_id='TEST')
        self.state['episode_status'] = 'RUNNING'
        self.state['runner_commit'] = self.base
        self.launcher = StubLauncher(self.wt)
        self.pub_calls = []
        self.prod_pushes = []      # (branch, expected_sha) per publication
        self.fail_pub = set()      # {(stage, attempt)}: publication raises
        self.fail_push = set()     # {(stage, attempt)}: product push fails

    def publisher(self, s, c, cs, a):
        self.pub_calls.append((cs['name'], a))
        if (cs['name'], a) in self.fail_pub:
            raise er.RunnerError('stub: control-side publication failure')

        def pp(cfg, expected):
            self.prod_pushes.append((cfg['branch'], expected))
            if (cs['name'], a) in self.fail_push:
                raise er.RunnerError('stub: product push rejected')
            return dict(branch=cfg['branch'], remote_ref=expected,
                        pushed_sha=expected, stub=True)
        return er.publish_round(s, c, cs, a, control_repo=self.control,
                                push=False, product_push=pp)

    def save(self, s):
        er.save_state_at(self.cfg['state_path'], s)

    def run_episode(self):
        return er.run_episode(self.state, self.cfg, launcher=self.launcher,
                              publisher=self.publisher, save=self.save)

    def record_path(self, stage):
        return (self.control / '.agent' / 'evidence' / er.EPISODE_ID
                / 'TEST' / stage / 'stage_record.json')


# ---------------------------------------------------------------- S1
def scenario_happy_path():
    h = Harness()
    outcome = h.run_episode()
    st1, st2 = h.state['stages']['SMOKE-1'], h.state['stages']['SMOKE-2']
    check('S1a episode reaches CHECKPOINT_READY at terminal stage',
          outcome == 'CHECKPOINT_READY'
          and h.state['episode_status'] == 'CHECKPOINT_READY')
    check('S1b CHANGES_REQUESTED incremented to a NEW attempt (B1)',
          st1['attempts'] == 2 and
          [c['attempt'] for c in st1['candidates']] == [1, 2])
    prev_review = h.cfg['run_root'] / 'smoke' / 'SMOKE-1' / 'round-01' \
        / 'review.md'
    rework_call = [c for c in h.launcher.calls
                   if c['role'] == 'executor'][1]
    check('S1c rework consumed the immediately prior review (prompt '
          'references round-01 review)',
          prev_review.as_posix() in rework_call['prompt'])
    exe_calls = [c for c in h.launcher.calls if c['role'] == 'executor']
    rev_calls = [c for c in h.launcher.calls if c['role'] == 'reviewer']
    check('S1d rework executor resumed the original executor session '
          '(engine passes --resume of attempt-1 session)',
          exe_calls[1]['resume'] == exe_calls[0]['session_id'])
    check('S1e every reviewer session is fresh (never resumed, distinct)',
          all(c['resume'] is None for c in rev_calls)
          and len({c['session_id'] for c in rev_calls}) == len(rev_calls)
          and len(rev_calls) == 3)
    check('S1f validation-only stage: candidate bound to UNCHANGED sha',
          st2['candidates'][0]['validation_only'] is True
          and st2['candidates'][0]['sha'] == st2['candidates'][0]['base']
          and st2['candidates'][0]['sha'] ==
          st1['candidates'][-1]['sha'])
    check('S1g validation-only review binds to the unchanged SHA',
          'candidate: ' + st2['candidates'][0]['sha'] in
          (h.cfg['run_root'] / 'smoke' / 'SMOKE-2' / 'round-01'
           / 'review.md').read_text(encoding='utf-8'))
    check('S1h PASS auto-promoted without any manual start-stage call',
          st1['status'] == 'PASS' and st2['attempts'] == 1
          and h.state['current_stage'] == 'SMOKE-2')
    ev = h.control / '.agent' / 'evidence' / er.EPISODE_ID / 'TEST'
    s1ev = ev / 'SMOKE-1'
    rec = json.loads((s1ev / 'stage_record.json').read_text(
        encoding='utf-8'))
    check('S1i durable publication produced (B8)',
          (s1ev / 'contract_snapshot.md').exists()
          and (s1ev / 'round-01' / 'review.md').exists()
          and (s1ev / 'round-02' / 'diff_stat.txt').exists()
          and (ev / 'SMOKE-2' / 'round-01' / 'review.md').exists()
          and rec['decisions'][0]['decision'] == 'CHANGES_REQUESTED'
          and len(rec['executor_sessions']) == 2)
    snap1 = Path(st1['contract_snapshot'])
    check('S1j contract frozen into an immutable snapshot; prompts cite '
          'the snapshot + hash (H3/B10)',
          bool(st1['contract_sha256'])
          and st1['contract_sha256'] == er.sha256_file(snap1)
          and snap1.as_posix() in exe_calls[0]['prompt']
          and 'snapshot sha256 ' + st1['contract_sha256'] in
          exe_calls[0]['prompt'])
    check('S1k role contracts delivered by absolute path (B6)',
          all(er.CONTROL_DOCS['plan'].as_posix() in c['prompt']
              and er.CONTROL_DOCS['agents'].as_posix() in c['prompt']
              for c in h.launcher.calls)
          and er.CONTROL_DOCS['executor'].as_posix() in
          exe_calls[0]['prompt']
          and er.CONTROL_DOCS['reviewer'].as_posix() in
          rev_calls[0]['prompt'])


# ------------------------------------------------- S2 A0 authorization
def scenario_a0_gate():
    h = Harness()
    h.cfg = dict(h.cfg, mode='real')
    h.state['episode_status'] = 'A0_REVIEW'
    try:
        h.run_episode()
        check('S2a real loop refuses before A0 approval', False,
              'no RunnerError')
    except er.RunnerError:
        check('S2a real loop refuses before A0 approval', True)
    rc = h.state['runner_commit']
    # mirror what cmd_run_smoke records on the real main state
    h.state['smoke'] = dict(runner_commit=rc)
    cr_text = (f'stage: A0\nattempt: 1\ncandidate: {rc}\n\n'
               f'Decision: CHANGES_REQUESTED\n')
    try:
        er.approve_a0_from_text(h.state, cr_text, 'fake.md')
        check('S2b approve-a0 rejects a non-PASS review', False)
    except er.RunnerError:
        check('S2b approve-a0 rejects a non-PASS review', True)
    try:
        er.approve_a0_from_text(
            h.state,
            f'candidate: {"f" * 40}\n\nDecision: PASS\n', 'fake.md')
        check('S2c approve-a0 rejects wrong candidate binding', False)
    except er.RunnerError:
        check('S2c approve-a0 rejects wrong candidate binding', True)
    er.approve_a0_from_text(h.state,
                            f'candidate: {rc}\n\nDecision: PASS\n',
                            'fake.md')
    check('S2d approve-a0 accepts PASS bound to the runner commit',
          h.state['episode_status'] == 'A0_APPROVED')
    outcome = h.run_episode()
    check('S2e approved episode runs to CHECKPOINT_READY',
          outcome == 'CHECKPOINT_READY')


# ------------------------------------------------- S3-S8 failure modes
def failure_scenario(name, override, *, role='executor',
                     expect_event=None, n_candidates=0):
    h = Harness()
    h.launcher.failures.append({**override, '_role': role})
    er.start_stage(h.state, h.cfg, 'SMOKE-1')
    outcome = er.run_round(h.state, h.cfg, 'SMOKE-1',
                           launcher=h.launcher, publisher=h.publisher,
                           save=h.save)
    st = h.state['stages']['SMOKE-1']
    ok = (outcome == 'ERROR' and st['status'] == 'ERROR'
          and st['attempts'] == 1
          and len(st['candidates']) == n_candidates
          and st['decisions'] == [])
    if expect_event:
        ok = ok and any(e['event'] == expect_event
                        for e in h.state['history'])
    check(name, ok,
          f'outcome={outcome} status={st["status"]} '
          f'attempts={st["attempts"]} '
          f'cands={len(st["candidates"])} '
          f'decisions={len(st["decisions"])}')
    return h


def scenario_failures():
    # clean failures: the stub session leaves NO source change
    failure_scenario('S3 failed executor session (exit!=0, source '
                     'untouched) -> ERROR, no advance',
                     dict(exit_code=1, skip_artifact=True),
                     expect_event='executor-session-invalid')
    failure_scenario('S4 timed-out executor session -> ERROR, no advance',
                     dict(timed_out=True, skip_artifact=True),
                     expect_event='executor-session-invalid')
    failure_scenario('S5 executor wrote no report -> ERROR, no advance',
                     dict(skip_artifact=True),
                     expect_event='executor-session-invalid')
    h = Harness()
    d = h.cfg['run_root'] / 'smoke' / 'SMOKE-1' / 'round-01'
    d.mkdir(parents=True)
    (d / 'execution_report.md').write_text('STALE', encoding='utf-8')
    h.launcher.failures.append(dict(_role='executor', skip_artifact=True))
    er.start_stage(h.state, h.cfg, 'SMOKE-1')
    outcome = er.run_round(h.state, h.cfg, 'SMOKE-1', launcher=h.launcher,
                           publisher=h.publisher, save=h.save)
    check('S6 stale artifact from a crashed attempt -> ERROR (never '
          'parsed)', outcome == 'ERROR'
          and h.state['stages']['SMOKE-1']['candidates'] == []
          and any(e['event'] == 'executor-session-invalid'
                  for e in h.state['history']))
    h7 = failure_scenario('S7 executor wrote no session id -> ERROR, no '
                          'advance', dict(no_session_id=True, skip_artifact=True),
                          expect_event='executor-session-invalid')
    h8 = failure_scenario('S8 failed reviewer session -> ERROR review-'
                          'pending, executor candidate frozen intact',
                          dict(exit_code=3), role='reviewer',
                          expect_event='review-session-invalid',
                          n_candidates=1)
    st8 = h8.state['stages']['SMOKE-1']
    check('S8b reviewer ERROR recorded as review_pending (B13) and the '
          'frozen candidate was published (B9 crash checkpoint)',
          st8['error_phase'] == 'review_pending'
          and h8.prod_pushes
          and h8.prod_pushes[-1] ==
          ('test-episode-branch', st8['candidates'][-1]['sha']))


# ------------------------------------------------- S9/S10 limits
def scenario_limits():
    h = Harness()
    h.launcher.failures = [dict(_role='reviewer',
                                decision='CHANGES_REQUESTED')
                           for _ in range(10)]
    outcome = h.run_episode()
    st = h.state['stages']['SMOKE-1']
    check('S9 max attempts: 3 candidates then HUMAN_REQUIRED stop',
          outcome == 'HUMAN_REQUIRED' and st['attempts'] == 3
          and len(st['candidates']) == 3
          and h.state['episode_status'] == 'HUMAN_REQUIRED')
    h2 = Harness()
    h2.launcher.failures = [dict(_role='reviewer', decision='HUMAN_REQUIRED')]
    outcome = h2.run_episode()
    check('S10 reviewer HUMAN_REQUIRED stops immediately',
          outcome == 'HUMAN_REQUIRED'
          and h2.state['episode_status'] == 'HUMAN_REQUIRED'
          and len(h2.state['stages']['SMOKE-1']['candidates']) == 1)


# ------------------------------------------------- S11 parse_review
def scenario_parse_review():
    tmp = Path(tempfile.mkdtemp(prefix='ep-review-'))
    sha = 'a' * 40
    hdr = f'stage: V0\nattempt: 1\ncandidate: {sha}\n' \
          f'execution_report: x.md\n'
    cases = [
        ('valid_pass', hdr + '\nDecision: PASS\n', 'PASS', False, False),
        ('valid_cr', hdr + '\nDecision: CHANGES_REQUESTED\n'
         'RESET_CONTEXT: NO\n', 'CHANGES_REQUESTED', False, False),
        ('valid_cr_reset', hdr + '\nDecision: CHANGES_REQUESTED\n'
         'RESET_CONTEXT: YES\n', 'CHANGES_REQUESTED', False, True),
        ('human', hdr + '\nDecision: HUMAN_REQUIRED\n', 'HUMAN_REQUIRED',
         False, False),
        ('lowercase_dot', hdr + '\nDecision: pass.\n', 'PASS', False,
         False),
        ('bad_sha', hdr.replace(sha, 'b' * 40) + '\nDecision: PASS\n',
         None, True, False),
        ('bad_stage', hdr.replace('stage: V0', 'stage: V1')
         + '\nDecision: PASS\n', None, True, False),
        ('bad_attempt', hdr.replace('attempt: 1', 'attempt: 2')
         + '\nDecision: PASS\n', None, True, False),
        ('no_decision', hdr + '\nnothing\n', None, True, False),
        ('unknown_decision', hdr + '\nDecision: MAYBE\n', None, True,
         False),
        ('two_decisions', hdr + '\nDecision: PASS\n'
         'Decision: HUMAN_REQUIRED\n', None, True, False),
        ('decision_word_in_body', hdr + '\nrationale: could PASS.\n'
         'Decision: PASS\n', 'PASS', False, False),
    ]
    for i, (name, text, want, exc, reset) in enumerate(cases):
        p = tmp / f'r{i}.md'
        p.write_text(text, encoding='utf-8')
        try:
            d, rc = er.parse_review(p, 'V0', 1, sha)
            good = (not exc and d == want and rc == reset)
        except er.RunnerError:
            good = exc
        check(f'S11 parse_review: {name}', good)


# ------------------------------------------------- S12 product push (B9)
def scenario_product_push():
    h = Harness()
    outcome = h.run_episode()
    st1, st2 = h.state['stages']['SMOKE-1'], h.state['stages']['SMOKE-2']
    c1, c2 = st1['candidates'][0]['sha'], st1['candidates'][1]['sha']
    check('S12a product branch pushed at EVERY publication boundary '
          'with the exact candidate sha (B9)',
          outcome == 'CHECKPOINT_READY'
          and h.prod_pushes == [('test-episode-branch', c1),
                                ('test-episode-branch', c2),
                                ('test-episode-branch', c2)])
    rec = json.loads(h.record_path('SMOKE-2').read_text(encoding='utf-8'))
    check('S12b stage_record.json records the product push '
          '(branch/ref/sha)',
          rec['product_push']['branch'] == 'test-episode-branch'
          and rec['product_push']['remote_ref'] == c2
          and rec['product_push']['pushed_sha'] == c2)


# ------------------------------------- S13 frozen contract snapshot (B10)
def scenario_contract_freeze():
    # (a) live contract mutated after freeze -> inert
    h = Harness()
    original = (er.EPISODE_DIR / 'runner' / 'SMOKE_CONTRACT.md'
                ).read_text(encoding='utf-8')
    tmpc = h.tmp / 'contract_mut.md'
    tmpc.write_text(original, encoding='utf-8')
    h.cfg = dict(h.cfg, stages=[dict(h.cfg['stages'][0], contract=tmpc),
                                h.cfg['stages'][1]])
    h.state = er.fresh_state(h.cfg, episode_id='TEST')
    h.state['episode_status'] = 'RUNNING'
    h.state['runner_commit'] = h.base
    er.start_stage(h.state, h.cfg, 'SMOKE-1')
    frozen_sha = h.state['stages']['SMOKE-1']['contract_sha256']
    tmpc.write_text(original + '\nMUTATED AFTER FREEZE\n',
                    encoding='utf-8')
    outcome = er.run_round(h.state, h.cfg, 'SMOKE-1',
                           launcher=h.launcher, publisher=h.publisher,
                           save=h.save)
    exe_prompt = h.launcher.calls[0]['prompt']
    ev = h.control / '.agent' / 'evidence' / er.EPISODE_ID / 'TEST' \
        / 'SMOKE-1'
    pub_snap = (ev / 'contract_snapshot.md').read_text(encoding='utf-8')
    rec = json.loads((ev / 'stage_record.json').read_text(
        encoding='utf-8'))
    check('S13a live-contract drift after freeze is inert (B10): '
          'sessions read the snapshot, publication copies frozen bytes, '
          'drift recorded',
          outcome == 'CHANGES_REQUESTED'
          and Path(h.state['stages']['SMOKE-1']
                   ['contract_snapshot']).as_posix() in exe_prompt
          and pub_snap == original
          and er.sha256_file(ev / 'contract_snapshot.md') == frozen_sha
          and rec['contract_drift'])
    # (b) snapshot tampered after freeze -> refuse before any session
    h2 = Harness()
    er.start_stage(h2.state, h2.cfg, 'SMOKE-1')
    snap2 = Path(h2.state['stages']['SMOKE-1']['contract_snapshot'])
    snap2.write_text('TAMPERED', encoding='utf-8')
    n_before = h2.launcher.n
    try:
        er.run_round(h2.state, h2.cfg, 'SMOKE-1',
                     launcher=h2.launcher, publisher=h2.publisher,
                     save=h2.save)
        ok = False
    except er.RunnerError:
        ok = True
    check('S13b tampered snapshot hash -> refuse before any session (B10)',
          ok and h2.launcher.n == n_before)


# ------------------------------------------- S14 A0 binding required (B11)
def scenario_a0_binding():
    h = Harness()
    h.state['episode_status'] = 'A0_REVIEW'
    h.state['smoke'] = dict(runner_commit=h.base)
    cases = [
        ('PASS with no candidate binding',
         'stage: A0\nattempt: 1\n\nDecision: PASS\n'),
        ('PASS with short candidate binding',
         f'candidate: {h.base[:12]}\n\nDecision: PASS\n'),
    ]
    for name, text in cases:
        try:
            er.approve_a0_from_text(h.state, text, 'fake.md')
            check(f'S14 {name} -> rejected', False)
        except er.RunnerError:
            check(f'S14 {name} -> rejected', True)
    check('S14 rejections did not flip the episode status',
          h.state['episode_status'] == 'A0_REVIEW')
    h2 = Harness()
    h2.state['episode_status'] = 'A0_REVIEW'    # no smoke runner_commit
    try:
        er.approve_a0_from_text(
            h2.state, f'candidate: {h2.base}\n\nDecision: PASS\n',
            'fake.md')
        check('S14 missing smoke runner_commit in state -> rejected',
              False)
    except er.RunnerError:
        check('S14 missing smoke runner_commit in state -> rejected', True)


# --------------------------------- S15 orphan commit protection (B12)
def scenario_orphan_commit():
    h = Harness()
    # stub executor COMMITS the marker, then the session reports exit!=0
    h.launcher.failures.append(dict(_role='executor', exit_code=1))
    er.start_stage(h.state, h.cfg, 'SMOKE-1')
    base0 = er.head_sha(h.wt)
    outcome = er.run_round(h.state, h.cfg, 'SMOKE-1',
                           launcher=h.launcher, publisher=h.publisher,
                           save=h.save)
    st = h.state['stages']['SMOKE-1']
    orphan_head = er.head_sha(h.wt)
    check('S15a failed session that committed -> terminal HUMAN_REQUIRED '
          'orphan, never a silent candidate (B12)',
          outcome == 'HUMAN_REQUIRED'
          and st['status'] == 'HUMAN_REQUIRED'
          and h.state['episode_status'] == 'HUMAN_REQUIRED'
          and st['candidates'] == [] and st['decisions'] == []
          and orphan_head != base0
          and st.get('orphan', {}).get('head') == orphan_head
          and st['orphan']['base'] == base0
          and any(e['event'] == 'orphan-after-failed-executor-session'
                  for e in h.state['history']))
    rec = json.loads(h.record_path('SMOKE-1').read_text(encoding='utf-8'))
    check('S15b orphan publication is evidence-only (product branch NOT '
          'pushed from an ambiguous tree)',
          rec['product_push'] == dict(skipped=True,
                                      reason='evidence-only')
          and h.prod_pushes == [])
    try:
        er.run_round(h.state, h.cfg, 'SMOKE-1', launcher=h.launcher,
                     publisher=h.publisher, save=h.save)
        ok = False
    except er.RunnerError:
        ok = True
    check('S15c no silent reuse: retry refused while HUMAN_REQUIRED',
          ok and st['candidates'] == [])


# ------------------------------- S16 reviewer retry on frozen candidate (B13)
def scenario_reviewer_retry():
    h = Harness()
    h.launcher.failures = [
        dict(_role='reviewer', decision='CHANGES_REQUESTED'),
        dict(_role='reviewer', exit_code=3),
    ]
    outcome = h.run_episode()
    st = h.state['stages']['SMOKE-1']
    check('S16a reviewer failure after a frozen candidate -> ERROR '
          'review-pending, candidate intact (B13)',
          outcome == 'ERROR' and st['status'] == 'ERROR'
          and st.get('error_phase') == 'review_pending'
          and len(st['candidates']) == 2 and st['attempts'] == 2
          and st['decisions'][0]['decision'] == 'CHANGES_REQUESTED')
    n_exe = len([c for c in h.launcher.calls if c['role'] == 'executor'])
    cand_sha = st['candidates'][-1]['sha']
    outcome2 = er.run_round(h.state, h.cfg, 'SMOKE-1',
                            launcher=h.launcher, publisher=h.publisher,
                            save=h.save)
    n_exe2 = len([c for c in h.launcher.calls if c['role'] == 'executor'])
    rev_calls = [c for c in h.launcher.calls if c['role'] == 'reviewer']
    check('S16b retry reruns ONLY a fresh reviewer on the SAME frozen '
          'candidate — no executor call, identical sha, PASS',
          outcome2 == 'PASS' and n_exe2 == n_exe == 2
          and rev_calls[-1]['resume'] is None
          and rev_calls[-1]['session_id'] not in
          {r['session_id'] for r in rev_calls[:-1]}
          and st['candidates'][-1]['sha'] == cand_sha
          and st['status'] == 'PASS'
          and h.state['stages']['SMOKE-2']['status'] == 'READY')


# ------------------------------------------ S17 worktree identity (H4/H1)
def scenario_worktree_identity():
    h = Harness()
    head0 = er.head_sha(h.wt)
    (h.wt / 'smoke' / 'extra.md').write_text('x', encoding='utf-8')
    git(h.wt, 'add', 'smoke/extra.md')
    git(h.wt, 'commit', '-q', '-m', 'extra')
    head1 = er.head_sha(h.wt)
    try:
        er.make_worktree(h.cfg, expected_head=head0)
        check('S17a branch-correct, clean worktree at the WRONG head '
              'is refused (H4/H1)', False)
    except er.RunnerError:
        check('S17a branch-correct, clean worktree at the WRONG head '
              'is refused (H4/H1)', True)
    check('S17b the state-implied head is accepted',
          er.make_worktree(h.cfg, expected_head=head1) == h.wt)
    cfgv = dict(h.cfg, mode='real',
                stages=[dict(name='V0'), dict(name='V1')])
    st = dict(V0=dict(status='PASS', candidates=[dict(sha='a' * 40)]),
              V1=dict(status='READY', candidates=[]))
    check('S17c _expected_product_head = latest started candidate (H4)',
          er._expected_product_head(dict(stages=st), cfgv) == 'a' * 40)
    st2 = dict(V0=dict(status='LOCKED', candidates=[]),
               V1=dict(status='LOCKED', candidates=[]))
    check('S17d no started stages -> declared product base',
          er._expected_product_head(dict(stages=st2), cfgv)
          == h.cfg['base'])


# --------------------------------------- S18 persisted ERROR terminal (H5)
def scenario_error_terminal():
    h = Harness()
    h.launcher.failures.append(dict(_role='executor', exit_code=1,
                                    skip_artifact=True))
    er.start_stage(h.state, h.cfg, 'SMOKE-1')
    out1 = er.run_round(h.state, h.cfg, 'SMOKE-1', launcher=h.launcher,
                        publisher=h.publisher, save=h.save)
    n = h.launcher.n
    out2 = h.run_episode()
    check('S18 persisted ERROR terminates run-episode deterministically '
          '(no busy loop, no extra sessions) (H5)',
          out1 == 'ERROR' and out2 == 'ERROR'
          and h.launcher.n == n
          and any(e['event'] == 'episode-stopped-error-persisted'
                  for e in h.state['history']))


# --------------------------- S19 publication-safe promotion (B14)
def scenario_publication_failure():
    # (a) product push fails on the round-2 PASS publication
    h = Harness()
    h.fail_push = {('SMOKE-1', 2)}
    outcome = h.run_episode()
    st1 = h.state['stages']['SMOKE-1']
    n_after_fail = h.launcher.n
    check('S19a product-push failure after PASS -> ERROR publish_pending, '
          'NO promotion/decision applied, next stage stays LOCKED',
          outcome == 'ERROR' and st1['status'] == 'ERROR'
          and st1.get('error_phase') == 'publish_pending'
          and [x['decision'] for x in st1['decisions']]
          == ['CHANGES_REQUESTED']
          and st1['pending']['decision'] == 'PASS'
          and h.state['stages']['SMOKE-2']['status'] == 'LOCKED'
          and h.state['current_stage'] == 'SMOKE-1'
          and h.state['episode_status'] == 'RUNNING'
          and any(e['event'] == 'publication-failed'
                  for e in h.state['history']))
    out2 = h.run_episode()
    check('S19b persisted restart after a publication failure stops '
          'deterministically (no silent continuation, no new sessions)',
          out2 == 'ERROR' and h.launcher.n == n_after_fail)
    h.fail_push = set()
    outcome3 = er.run_round(h.state, h.cfg, 'SMOKE-1',
                            launcher=h.launcher, publisher=h.publisher,
                            save=h.save)
    check('S19c retry re-publishes WITHOUT rerunning sessions, then '
          'applies PASS + promotion',
          outcome3 == 'PASS'
          and h.launcher.n == n_after_fail
          and h.state['stages']['SMOKE-1']['status'] == 'PASS'
          and h.state['stages']['SMOKE-2']['status'] == 'READY'
          and h.state['current_stage'] == 'SMOKE-2'
          and [x['decision'] for x in
               h.state['stages']['SMOKE-1']['decisions']]
          == ['CHANGES_REQUESTED', 'PASS'])
    # (d) total (control-side) publication failure — same guarantees
    h2 = Harness()
    h2.fail_pub = {('SMOKE-1', 2)}
    outcome = h2.run_episode()
    check('S19d control-publication failure after PASS -> same ERROR '
          'publish_pending guarantees',
          outcome == 'ERROR'
          and h2.state['stages']['SMOKE-1'].get('error_phase')
          == 'publish_pending'
          and h2.state['stages']['SMOKE-2']['status'] == 'LOCKED'
          and h2.state['episode_status'] == 'RUNNING')
    # (e) terminal-stage PASS publication failure: no CHECKPOINT_READY
    h3 = Harness()
    h3.launcher.failures = [dict(_role='reviewer', decision='PASS')]
    er.start_stage(h3.state, h3.cfg, 'SMOKE-1')
    er.run_round(h3.state, h3.cfg, 'SMOKE-1', launcher=h3.launcher,
                 publisher=h3.publisher, save=h3.save)
    er.start_stage(h3.state, h3.cfg, 'SMOKE-2')
    h3.fail_push = {('SMOKE-2', 1)}
    outcome = er.run_round(h3.state, h3.cfg, 'SMOKE-2',
                           launcher=h3.launcher, publisher=h3.publisher,
                           save=h3.save)
    check('S19e terminal-stage publication failure -> episode NOT '
          'CHECKPOINT_READY',
          outcome == 'ERROR'
          and h3.state['episode_status'] == 'RUNNING'
          and h3.state['stages']['SMOKE-2']['status'] == 'ERROR')


# ------------------------- S20 valid-session dirty tree orphan (B15)
def scenario_dirty_orphan():
    h = Harness()
    # executor COMMITS the candidate but leaves an extra dirty file
    h.launcher.failures.append(dict(_role='executor', dirty_extra=True))
    er.start_stage(h.state, h.cfg, 'SMOKE-1')
    outcome = er.run_round(h.state, h.cfg, 'SMOKE-1',
                           launcher=h.launcher, publisher=h.publisher,
                           save=h.save)
    st = h.state['stages']['SMOKE-1']
    head_after = er.head_sha(h.wt)
    check('S20a valid executor + dirty tree -> terminal orphan '
          'HUMAN_REQUIRED, no candidate frozen (B15)',
          outcome == 'HUMAN_REQUIRED'
          and st['status'] == 'HUMAN_REQUIRED'
          and h.state['episode_status'] == 'HUMAN_REQUIRED'
          and st['candidates'] == [] and st['decisions'] == []
          and st.get('orphan', {}).get('kind')
          == 'dirty-worktree-before-review'
          and st['orphan']['head'] == head_after
          and any(e['event'] == 'orphan-dirty-worktree-before-review'
                  for e in h.state['history']))
    rec = json.loads(h.record_path('SMOKE-1').read_text(encoding='utf-8'))
    check('S20b the unreviewed ambiguous product state is NOT pushed '
          '(evidence-only publication)',
          rec['product_push'] == dict(skipped=True,
                                      reason='evidence-only')
          and h.prod_pushes == [])
    try:
        er.run_round(h.state, h.cfg, 'SMOKE-1', launcher=h.launcher,
                     publisher=h.publisher, save=h.save)
        ok = False
    except er.RunnerError:
        ok = True
    check('S20c retry refused: the unreviewed commit/dirty tree can '
          'never silently become the next round base', ok)


# ----------------------------- S21 approved-runner enforcement (B16)
def scenario_runner_identity():
    h = Harness()
    h.cfg = dict(h.cfg, mode='real')
    h.state['episode_status'] = 'A0_REVIEW'
    h.state['smoke'] = dict(runner_commit=h.base)
    er.approve_a0_from_text(h.state, f'candidate: {h.base}\n\n'
                            f'Decision: PASS\n', 'fake.md')
    ap = h.state['approved_runner']
    # offline: the reviewed commit lives in the temp harness repo, so
    # the identity pins the EXECUTING file (recorded as such)
    check('S21a approve-a0 freezes the approved runner identity (B16)',
          h.state['episode_status'] == 'A0_APPROVED'
          and ap['commit'] == h.base
          and ap['runner_blob'] == er._runner_blob_sha()
          and ap['runner_blob_source'] == 'executing-file')
    outcome = h.run_episode()
    rec = json.loads(h.record_path('SMOKE-1').read_text(encoding='utf-8'))
    check('S21b approved runner unchanged -> real loop allowed; stage '
          'records carry the approved identity',
          outcome == 'CHECKPOINT_READY'
          and rec['approved_runner']['commit'] == h.base)
    h2 = Harness()
    h2.cfg = dict(h2.cfg, mode='real')
    h2.state['episode_status'] = 'A0_REVIEW'
    h2.state['smoke'] = dict(runner_commit=h2.base)
    er.approve_a0_from_text(h2.state, f'candidate: {h2.base}\n\n'
                            f'Decision: PASS\n', 'fake.md')
    h2.state['approved_runner']['runner_blob'] = '0' * 40   # "changed"
    try:
        h2.run_episode()
        check('S21c runner source changed after approval -> real loop '
              'refused', False)
    except er.RunnerError:
        check('S21c runner source changed after approval -> real loop '
              'refused', True)


if __name__ == '__main__':
    scenario_happy_path()
    scenario_a0_gate()
    scenario_failures()
    scenario_limits()
    scenario_parse_review()
    scenario_product_push()
    scenario_contract_freeze()
    scenario_a0_binding()
    scenario_orphan_commit()
    scenario_reviewer_retry()
    scenario_worktree_identity()
    scenario_error_terminal()
    scenario_publication_failure()
    scenario_dirty_orphan()
    scenario_runner_identity()
    print(('ALL PASS' if not FAIL else f'FAILURES: {FAIL}'))
    sys.exit(1 if FAIL else 0)
