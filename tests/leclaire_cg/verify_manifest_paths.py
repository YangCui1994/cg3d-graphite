"""Verify every render-manifest raw path exists and is Git-trackable.

Contract E4: "Pass-5 must commit every raw snapshot referenced by a render
manifest. Before evidence commit verify with Git that every source_raw path
exists, is tracked and is reachable from the evidence commit."
"""
import io, json, os, subprocess, sys

root = sys.argv[1]
missing, untracked, ok = [], [], 0
for case in sorted(os.listdir(root)):
    cd = os.path.join(root, case)
    mp = os.path.join(cd, 'render_manifest.json')
    if not os.path.isfile(mp):
        continue
    man = json.load(io.open(mp, encoding='utf-8'))
    for fig in man.get('figures', []):
        src = fig.get('source_raw')
        if not src:
            continue
        p = os.path.join(cd, src)
        if not os.path.isfile(p):
            missing.append(p)
            continue
        r = subprocess.run(['git', 'check-ignore', '-q', p], cwd=root)
        if r.returncode == 0:
            untracked.append(p)
        else:
            ok += 1
print('raw paths referenced :', ok + len(missing) + len(untracked))
print('trackable            :', ok)
print('MISSING on disk      :', len(missing), missing[:3])
print('IGNORED by git       :', len(untracked), untracked[:3])
print('VERDICT:', 'OK' if not missing and not untracked else 'FAIL')
sys.exit(0 if not missing and not untracked else 1)
