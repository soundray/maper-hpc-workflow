#!/usr/bin/env python3
"""Write regional volumes in the 2024 NeumRA deliverable format.

Run inside the MAPER container (needs nibabel/numpy), e.g. via `mcx` with 4 CPUs.

Inputs (one file per scan, named <iid>.nii.gz, all on the same grid):
  FINAL/seg120-tcsep/  MAPER tissue-separated labels (value = 121 * tc3crisp + seg120 label)
  FINAL/tc3crisp/      MAPER crisp tissue classes (1 CSF, 2 GM, 3 WM; 0 outside)
  FINAL/icv/           ICV mask (non-zero = inside); not needed with --icv-table
  TARGETS              TSV with header: iid, pid, baseline, is_patient, has_followup
                       (TRUE/FALSE strings, written through unchanged)

Outputs in OUT:
  vols_<set>-<date>.csv.gz            set,pid,iid,baseline,cclass,name,labelno,vol_mm3,vol_mm3_corr
                                      one row per tcsep value present (labelno 0-483)
  <set>-tc3-volumes-<date>.csv.gz     set,iid,label_no,cclass,vol_mm3,vol_mm3_corr
  <set>-gmwm_ratios-<date>.csv.gz     set,iid,gmwm,icv,gmwm_ratio,pid,is_patient,is_followup,has_followup

ICV correction (as in the 2024 NeumRA export): vol_mm3_corr = vol_mm3 / icv_mm3 * ICVMEAN.
By default icv_mm3 is measured on FINAL/icv/<iid>.nii.gz. With --icv-table it is taken from a TSV instead (for targets
without an ICV mask, e.g. numeric estimates from HD-BET masks, runbook 12.3). Header columns: an id column (iid,
target_id or id) and the ICV as icv_mm3, or icv_est_mL / icv_mL (converted to mm3). Every target must have a row.
The default ICVMEAN is the 2024 NeumRA + IXI reference mean, recovered from the 2024 export:
vol_mm3_corr / vol_mm3 = 15.38343889550265 / 14.0625 for scan 31aug0907, whose ICV is 1354466.6 mm3.

Region names come from the 2023/2024 NeumRA files where available (keeps their spellings for joins),
otherwise from the Hammers r120 LUT. Region 0 is "Background" in every class.
"""
import argparse, csv, gzip, os
import numpy as np, nibabel as nib

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, '..', 'reference')
ICVMEAN_2024 = 15.38343889550265 / 14.0625 * 1354466.6
CNAME = {0: 'BG', 1: 'CSF', 2: 'GM', 3: 'WM'}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--final', required=True, help='directory with seg120-tcsep/, tc3crisp/ and (unless --icv-table) icv/')
    ap.add_argument('--targets', required=True, help='TSV: iid, pid, baseline, is_patient, has_followup')
    ap.add_argument('--set', required=True, dest='setname', help='value of the "set" column, also used in file names')
    ap.add_argument('--date', required=True, help='date stamp for file names, e.g. 20261003')
    ap.add_argument('--out', required=True)
    ap.add_argument('--icv-table', dest='icv_table', default=None,
                    help='TSV with numeric ICV per target (id column iid|target_id|id; icv_mm3, icv_est_mL or icv_mL); replaces the ICV masks')
    ap.add_argument('--icvmean', type=float, default=ICVMEAN_2024, help='reference mean ICV in mm3 (default: 2024 NeumRA + IXI)')
    ap.add_argument('--names', default=os.path.join(REF, 'neumra-2023-region-names.csv'))
    ap.add_argument('--lut', default=os.path.join(REF, 'hammers-r120.lut'))
    a = ap.parse_args()

    lut = {0: 'Background'}
    for line in open(a.lut):
        f = line.split()
        if f:
            lut[int(f[0])] = ' '.join(f[4:])
    old = {int(r['labelno']): r['name'] for r in csv.DictReader(open(a.names))}

    def region_name(v):
        return old.get(int(v), lut[int(v) % 121])

    def load(f):
        i = nib.load(f)
        return i, np.rint(np.asanyarray(i.dataobj).reshape(i.shape[:3])).astype(np.int64)

    def r(x):
        return repr(float(x))  # full double precision, like readr::write_csv

    icv_tab = None
    if a.icv_table:
        icv_tab = {}
        rows = list(csv.DictReader(open(a.icv_table), delimiter='\t'))
        idc = next((c for c in ('iid', 'target_id', 'id') if rows and c in rows[0]), None)
        vc = next(((c, k) for c, k in (('icv_mm3', 1.0), ('icv_est_mL', 1000.0), ('icv_mL', 1000.0)) if rows and c in rows[0]), None)
        if idc is None or vc is None:
            raise SystemExit(f'{a.icv_table}: need an id column (iid|target_id|id) and an ICV column (icv_mm3|icv_est_mL|icv_mL)')
        for row in rows:
            icv_tab[row[idc]] = float(row[vc[0]]) * vc[1]

    targets = list(csv.DictReader(open(a.targets), delimiter='\t'))
    vol_rows, tc3_rows, ratio_rows = [], [], []
    for t in targets:
        iid = t['iid']
        ti, T = load(f'{a.final}/seg120-tcsep/{iid}.nii.gz')
        ci, C = load(f'{a.final}/tc3crisp/{iid}.nii.gz')
        others = [ci]
        if icv_tab is None:
            ii, I = load(f'{a.final}/icv/{iid}.nii.gz')
            others.append(ii)
        for other in others:
            assert other.shape[:3] == ti.shape[:3] and np.allclose(other.get_qform(), ti.get_qform(), atol=1e-4), iid
        assert np.array_equal(C, T // 121), f'{iid}: tc3crisp != tcsep class part'
        # header zooms are float32 (e.g. 0.75 stored as 0.75000006); round to recover the nominal voxel size
        vox = float(np.prod(np.round(np.asarray(ti.header.get_zooms()[:3], dtype=np.float64), 6)))
        if icv_tab is None:
            icv = (I > 0).sum() * vox
        else:
            if iid not in icv_tab:
                raise SystemExit(f'{a.icv_table}: no ICV for target {iid}')
            icv = icv_tab[iid]
            if not icv > 0:
                raise SystemExit(f'{a.icv_table}: non-positive ICV for target {iid}')
        vals, cnt = np.unique(T, return_counts=True)
        assert vals.min() >= 0 and vals.max() <= 483, iid
        for v, n in zip(vals, cnt):
            vol = n * vox
            vol_rows.append([a.setname, t['pid'], iid, t['baseline'], CNAME[v // 121], region_name(v), int(v),
                             r(vol), r(vol / icv * a.icvmean)])
        cv, cc = np.unique(C, return_counts=True)
        cvol = dict(zip(cv.tolist(), (cc * vox).tolist()))
        for lab in (1, 2, 3):
            vol = cvol.get(lab, 0.0)
            tc3_rows.append([a.setname, iid, lab, CNAME[lab], r(vol), r(vol / icv * a.icvmean)])
        gmwm = cvol.get(2, 0.0) + cvol.get(3, 0.0)
        is_followup = 'FALSE' if t['baseline'] == 'TRUE' else 'TRUE'
        ratio_rows.append([a.setname, iid, r(gmwm), r(icv), r(gmwm / icv), t['pid'], t['is_patient'], is_followup, t['has_followup']])

    def write(name, hdr, rows):
        with gzip.open(os.path.join(a.out, name), 'wt', newline='') as fh:
            w = csv.writer(fh, lineterminator='\n')
            w.writerow(hdr)
            w.writerows(rows)

    os.makedirs(a.out, exist_ok=True)
    write(f'vols_{a.setname}-{a.date}.csv.gz', ['set', 'pid', 'iid', 'baseline', 'cclass', 'name', 'labelno', 'vol_mm3', 'vol_mm3_corr'], vol_rows)
    write(f'{a.setname}-tc3-volumes-{a.date}.csv.gz', ['set', 'iid', 'label_no', 'cclass', 'vol_mm3', 'vol_mm3_corr'], tc3_rows)
    write(f'{a.setname}-gmwm_ratios-{a.date}.csv.gz', ['set', 'iid', 'gmwm', 'icv', 'gmwm_ratio', 'pid', 'is_patient', 'is_followup', 'has_followup'], ratio_rows)
    print(f'icvmean {a.icvmean:.4f} mm3; ICV from {"table " + a.icv_table if icv_tab is not None else "masks"}; rows: vols {len(vol_rows)}, tc3 {len(tc3_rows)}, ratios {len(ratio_rows)}')


if __name__ == '__main__':
    main()
