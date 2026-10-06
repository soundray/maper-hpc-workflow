#!/usr/bin/env python3
"""Per-region seg120 volumes, total and after tc3 separation (CSF/GM/WM/unclassified), raw (ml) and as a fraction of ICV.

Run inside the MAPER container (needs nibabel/numpy), e.g. via `mcx` with 4 CPUs.

Inputs (one file per scan, named <iid>.nii.gz, all on the same grid):
  FINAL/seg120/         fused MAPER labels (1-120)
  FINAL/seg120-tcsep/   tissue-separated labels (value = 121 * tc3crisp + seg120 label); its label part must equal seg120
  FINAL/icv/            ICV mask (non-zero = inside); not needed with --icv-table
  TARGETS               TSV whose header has a column iid (other columns ignored), e.g. the neumra-format-volumes.py targets file
ICV: measured on the ICV mask, or taken from --icv-table (TSV: id column iid|target_id|id and icv_mm3, icv_est_mL or icv_mL;
for targets without an ICV mask, e.g. the numeric HD-BET estimate of runbook 12.3). Every target must have a row.

Outputs in OUT:
  seg120-volumes-raw-ml.csv, seg120-volumes-icv-fraction.csv                 per-region totals, one row per target
  seg120-tcsep-volumes-raw-ml.csv, seg120-tcsep-volumes-icv-fraction.csv     per region and tissue
  seg120-volumes-long.tsv                                                    target_id,label,region,tissue,volume_ml,icv_ml,fraction_of_icv
--extra-columns A,B,... appends those TARGETS columns (e.g. pid,baseline,is_paired,pair_status) to every row of the long TSV
only (the wide CSVs are unchanged).
Volumes are measured on the prepared grid (volume-preserving preparation; no restoration resampling). Region names from the
Hammers r120 LUT. Checks: the tcsep label part equals the labels; tissue parts sum to the totals for every region.
"""
import argparse, csv, os
import numpy as np, nibabel as nib

HERE = os.path.dirname(os.path.abspath(__file__))
TISSUE = {1: 'CSF', 2: 'GM', 3: 'WM', 0: 'unclassified'}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--final', required=True, help='directory with seg120/, seg120-tcsep/ and (unless --icv-table) icv/')
    ap.add_argument('--targets', required=True, help='TSV with a column iid')
    ap.add_argument('--out', required=True)
    ap.add_argument('--extra-columns', dest='extra', default='', help='comma-separated TARGETS columns appended to the long TSV rows')
    ap.add_argument('--icv-table', dest='icv_table', default=None, help='numeric ICV TSV (id column; icv_mm3|icv_est_mL|icv_mL) instead of ICV masks')
    ap.add_argument('--lut', default=os.path.join(HERE, '..', 'reference', 'hammers-r120.lut'))
    a = ap.parse_args()

    names = {}
    for line in open(a.lut):
        f = line.split()
        if f:
            names[int(f[0])] = ' '.join(f[4:])
    assert sorted(names) == list(range(1, 121)), 'LUT must define labels 1-120'
    trows = list(csv.DictReader(open(a.targets), delimiter='\t'))
    ids = [r['iid'] for r in trows]
    tdict = {r['iid']: r for r in trows}
    extra = [c for c in a.extra.split(',') if c]
    for c in extra:
        if not trows or c not in trows[0]:
            raise SystemExit(f'{a.targets}: no column {c} for --extra-columns')

    icv_tab = None
    if a.icv_table:
        rows = list(csv.DictReader(open(a.icv_table), delimiter='\t'))
        idc = next((c for c in ('iid', 'target_id', 'id') if rows and c in rows[0]), None)
        vc = next(((c, k) for c, k in (('icv_mm3', 1e-3), ('icv_est_mL', 1.0), ('icv_mL', 1.0)) if rows and c in rows[0]), None)
        if idc is None or vc is None:
            raise SystemExit(f'{a.icv_table}: need an id column (iid|target_id|id) and an ICV column (icv_mm3|icv_est_mL|icv_mL)')
        icv_tab = {r[idc]: float(r[vc[0]]) * vc[1] for r in rows}

    def load(f):
        i = nib.load(f)
        return i, np.rint(np.asanyarray(i.dataobj).reshape(i.shape[:3])).astype(np.int64)

    long_rows, wide = [], {}
    for t in ids:
        li, L = load(f'{a.final}/seg120/{t}.nii.gz')
        ti, T = load(f'{a.final}/seg120-tcsep/{t}.nii.gz')
        assert li.shape[:3] == ti.shape[:3] and np.allclose(li.get_qform(), ti.get_qform(), atol=1e-4), t
        assert np.array_equal(T % 121, L), f'{t}: tcsep label part != seg120'
        # header zooms are float32 (e.g. 0.75 stored as 0.75000006); round to recover the nominal voxel size
        vox = float(np.prod(np.round(np.asarray(li.header.get_zooms()[:3], dtype=np.float64), 6))) / 1000.0
        if icv_tab is None:
            ii, I = load(f'{a.final}/icv/{t}.nii.gz')
            assert ii.shape[:3] == li.shape[:3] and np.allclose(ii.get_qform(), li.get_qform(), atol=1e-4), t
            icv = (I > 0).sum() * vox
        else:
            if t not in icv_tab:
                raise SystemExit(f'{a.icv_table}: no ICV for target {t}')
            icv = icv_tab[t]
        if not icv > 0:
            raise SystemExit(f'{t}: non-positive ICV')
        cls = T // 121
        tot = np.bincount(L.ravel(), minlength=121) * vox
        by = {c: np.bincount(L[cls == c].ravel(), minlength=121) * vox for c in TISSUE}
        for lab in range(1, 121):
            assert abs(sum(by[c][lab] for c in TISSUE) - tot[lab]) < 1e-9
            for tis, vol in [('all', tot[lab])] + [(TISSUE[c], by[c][lab]) for c in (1, 2, 3, 0)]:
                long_rows.append([t, lab, names[lab], tis, f'{vol:.4f}', f'{icv:.4f}', f'{vol / icv:.7f}'] + [tdict[t][c] for c in extra])
                wide.setdefault(t, {})[(lab, tis)] = (vol, vol / icv)
        wide[t]['_icv'] = icv

    os.makedirs(a.out, exist_ok=True)
    with open(f'{a.out}/seg120-volumes-long.tsv', 'w', newline='') as fh:
        w = csv.writer(fh, delimiter='\t')
        w.writerow(['target_id', 'label', 'region', 'tissue', 'volume_ml', 'icv_ml', 'fraction_of_icv'] + extra)
        w.writerows(long_rows)

    def write_wide(fname, tissues, idx):
        with open(f'{a.out}/{fname}', 'w', newline='') as fh:
            w = csv.writer(fh)
            cols = [(lab, tis) for lab in range(1, 121) for tis in tissues]
            w.writerow(['target_id', 'icv_ml'] + [f'{lab}:{names[lab]}' + ('' if tis == 'all' else f' [{tis}]') for lab, tis in cols])
            fmt = '{:.4f}' if idx == 0 else '{:.7f}'
            for t in ids:
                w.writerow([t, f"{wide[t]['_icv']:.4f}"] + [fmt.format(wide[t][c][idx]) for c in cols])

    write_wide('seg120-volumes-raw-ml.csv', ['all'], 0)
    write_wide('seg120-volumes-icv-fraction.csv', ['all'], 1)
    write_wide('seg120-tcsep-volumes-raw-ml.csv', ['CSF', 'GM', 'WM', 'unclassified'], 0)
    write_wide('seg120-tcsep-volumes-icv-fraction.csv', ['CSF', 'GM', 'WM', 'unclassified'], 1)
    lab = [sum(wide[t][(l, 'all')][0] for l in range(1, 121)) for t in ids]
    print(f'{len(ids)} targets; ICV from {"table " + a.icv_table if icv_tab is not None else "masks"}; '
          f'labelled volume mean {np.mean(lab):.0f} ml (min {min(lab):.0f}, max {max(lab):.0f})')


if __name__ == '__main__':
    main()
