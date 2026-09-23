"""CG3D bilateral-episode A0-R1 generic-engine tests (offline).

  python tests/test_episode_runner_generic.py      (exit 0 = pass)

Exercises the SAME generic orchestration path (start_stage / run_round
/ run_episode / publish_round / approve_a0_from_text) that the real
smoke and V0-V3 use, with stubbed ZCode sessions (no GLM, no GPU,
fully deterministic).  Scenario coverage maps to the A0 external
review acceptance list (A0_EXTERNAL_REVIEW.md "Required A0 rework
acceptance"): validation-only unchanged-source review, CHANGES_REQUESTED
attempt increment, rework consumes the immediately prior review, fresh
reviewer sessions, failed/timed-out/stale sessions never advance,
PASS auto-promotes without start-stage, max attempts -> HUMAN_REQUIRED,
HUMAN_REQUIRED stop, terminal stage stops at CHECKPOINT_READY, durable
publication produced, explicit A0 authorization required.
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
    queue of per-call failure overrides for B5 scenarios."""

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

    def publisher(self, s, c, cs, a):
        self.pub_calls.append((cs['name'], a))
        return er.publish_round(s, c, cs, a, control_repo=self.control,
                                push=False)

    def save(self, s):
        er.save_state_at(self.cfg['state_path'], s)

    def run_episode(self):
        return er.run_episode(self.state, self.cfg, launcher=self.launcher,
                              publisher=self.publisher, save=self.save)


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
    check('S1j contract provenance frozen per stage (H3)',
          bool(st1['contract_sha256'])
          and st1['contract_sha256'] == er.sha256_file(
              h.cfg['stages'][0]['contract'])
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
    failure_scenario('S3 failed executor session (exit!=0) -> ERROR, '
                     'no advance', dict(exit_code=1),
                     expect_event='executor-session-invalid')
    failure_scenario('S4 timed-out executor session -> ERROR, no advance',
                     dict(timed_out=True),
                     expect_event='executor-session-invalid')
    failure_scenario('S5 executor wrote no report -> ERROR, no advance',
                     dict(skip_artifact=True),
                     expect_event='executor-session-invalid')
    h = Harness()
    d = h.cfg['run_root'] / 'smoke' / 'SMOKE-1' / 'round-01'
    d.mkdir(parents=True)
    (d / 'execution_report.md').write_text('STALE', encoding='utf-8')
    er.start_stage(h.state, h.cfg, 'SMOKE-1')
    outcome = er.run_round(h.state, h.cfg, 'SMOKE-1', launcher=h.launcher,
                           publisher=h.publisher, save=h.save)
    check('S6 stale artifact from a crashed attempt -> ERROR (never '
          'parsed)', outcome == 'ERROR'
          and h.state['stages']['SMOKE-1']['candidates'] == []
          and any(e['event'] == 'executor-session-invalid'
                  for e in h.state['history']))
    failure_scenario('S7 dirty worktree after executor -> ERROR before '
                     'review', dict(dirty_extra=True),
                     expect_event='dirty-worktree-before-review')
    failure_scenario('S8 failed reviewer session -> ERROR, no decision '
                     '(executor candidate kept, no decision recorded)',
                     dict(exit_code=3), role='reviewer',
                     expect_event='review-session-invalid', n_candidates=1)


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


if __name__ == '__main__':
    scenario_happy_path()
    scenario_a0_gate()
    scenario_failures()
    scenario_limits()
    scenario_parse_review()
    print(('ALL PASS' if not FAIL else f'FAILURES: {FAIL}'))
    sys.exit(1 if FAIL else 0)
