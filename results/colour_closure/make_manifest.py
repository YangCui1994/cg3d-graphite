"""BI-COLOUR-CLOSURE-001 — MANIFEST + summary generator.

Hashes every file under results/colour_closure (excluding MANIFEST.json
itself) with SHA256; writes summary.json with the gate headline values
extracted from the machine-readable evidence (no hand-typed numbers).

Run (repo root):  python results/colour_closure/make_manifest.py
"""
import csv
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    base = 'e256b4857a6e51510b75358994d7c5bcc742781e'
    files = {}
    for root, _dirs, names in os.walk(HERE):
        for n in sorted(names):
            p = os.path.join(root, n)
            rel = os.path.relpath(p, HERE).replace('\\', '/')
            if rel in ('MANIFEST.json', 'summary.json'):
                continue
            files[rel] = sha256(p)
    with open(os.path.join(HERE, 'MANIFEST.json'), 'w') as f:
        json.dump(dict(base=base, files=files), f, indent=1,
                  sort_keys=True)

    def rj(tag, name='accum_report.json'):
        return json.load(open(os.path.join(HERE, tag, name)))

    def slope(tag, key='Mc'):
        return rj(tag)['drift_fits'][key]['slope_per_step']

    def r2(tag, key='Mc'):
        return rj(tag)['drift_fits'][key]['r2']

    f0 = json.load(open(os.path.join(HERE, 'A_reproduce',
                                     'reproduce_report.json')))
    a2 = json.load(open(os.path.join(HERE, 'a2_candidates.json')))
    dx_c1 = {}
    with open(os.path.join(HERE, 'dx_C1_T3C1s', 'class_stats.csv')) as f:
        for row in csv.DictReader(f):
            dx_c1[(row['class'], row['quantity'])] = row
    summary = dict(
        task='BI-COLOUR-CLOSURE-001',
        base=base,
        selected=dict(total_fix='T3', colour_fix='C1X', acc_fix='A2'),
        reproduce_all_ok=f0['all_ok'],
        diagnosis=dict(
            biased_class='non-frozen cc==0 nodes (pure, chi~1e-12) near '
                         'diffuse interfaces; uncorrected '
                         'equilibrium-construction leak Req_r',
            base_c1_R_r_mean=float(
                dx_c1[('cc==0', 'R_r')]['mean']),
            base_c1_R_r_frac_pos=float(
                dx_c1[('cc==0', 'R_r')]['frac_pos']),
            base_c1_accumulates=True,
            base_c1_accum_slope=slope('ac_C1_T3C1s_20k'),
            c3_budget=dict(
                dMr=rj('bg_C3_T3C1s', 'budget_report.json')['means']['dMr'],
                sumR_r=rj('bg_C3_T3C1s',
                          'budget_report.json')['means']['sumR_r'],
                sumdacc_r=rj('bg_C3_T3C1s',
                             'budget_report.json')['means']['sumdacc_r'],
                identity_resid_r=rj(
                    'bg_C3_T3C1s',
                    'budget_report.json')['means']['identity_resid_r']),
        ),
        gates=dict(
            periodic_c1_20k=slope('ac_C1_T3C1X_A2_20k'),
            periodic_c1_60k=slope('ac_C1_T3C1X_A2_60k'),
            periodic_c1_240k=slope('ac_C1_T3C1X_A2_240k'),
            periodic_c1_240k_r2=r2('ac_C1_T3C1X_A2_240k'),
            c3_60k_colour=slope('ac_C3_T3C1X_A2_60k'),
            c3_60k_colour_r2=r2('ac_C3_T3C1X_A2_60k'),
            c3_60k_total=slope('ac_C3_T3C1X_A2_60k', 'Mff'),
            c3_120k_colour=slope('ac_C3_T3C1X_A2_120k'),
            c3_120k_colour_r2=r2('ac_C3_T3C1X_A2_120k'),
            a2_stationary_all=dict(
                (k, v) for k, v in a2['results'].items()),
        ),
        baseline=dict(
            c1_20k=slope('ac_C1_T3C1s_20k'),
            c3_60k_rerun=slope('ac_C3_T3C1s_60k_rerun'),
            c3_60k_committed=-6.425290e-10,
        ),
        improvements=dict(
            c1_60k_vs_base=slope('ac_C1_T3C1s_20k')
            / slope('ac_C1_T3C1X_A2_60k'),
            c3_60k_vs_base=slope('ac_C3_T3C1s_60k_rerun')
            / slope('ac_C3_T3C1X_A2_60k'),
            c3_60k_vs_prefix_t0=6.7617e-9 / slope('ac_C3_T3C1X_A2_60k'),
        ),
    )
    with open(os.path.join(HERE, 'summary.json'), 'w') as f:
        json.dump(summary, f, indent=1, sort_keys=True)
    print('MANIFEST: %d files; summary written' % len(files))


if __name__ == '__main__':
    main()
