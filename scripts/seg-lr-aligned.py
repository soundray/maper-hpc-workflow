#!/usr/bin/env python3
"""Left/right labelled-volume check on PosNorm-aligned seg120 (qc/seg-aligned/<id>.nii.gz). Anatomical sides from label names
(' L'/' R' suffix; NeumRA 2023 names, else Hammers r120 LUT). Outputs: per-image hemisphere ratio (sum of L labels / sum of R labels),
per-pair L/R ratios (TSV, wide), and robust outlier statistics (median/MAD of log ratios across the cohort).
Args: ROOT outprefix id..."""
import sys, os, re, csv, numpy as np, nibabel as nib
ref = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "reference")
names = {}
for line in open(f"{ref}/hammers-r120.lut"):
    f = line.split()
    if len(f) >= 5 and f[0].isdigit(): names[int(f[0])] = " ".join(f[4:])
for r in csv.DictReader(open(f"{ref}/neumra-2023-region-names.csv")): names[int(r["labelno"])] = r["name"]
base = {}
for k, v in names.items():
    m = re.match(r"(.*?)[ _]?([LR])$", v) if 1 <= k <= 120 else None
    if m: base.setdefault(m[1].strip(), {})[m[2]] = k
pairs = {b: d for b, d in base.items() if len(d) == 2}
root, outp, ids = sys.argv[1], sys.argv[2], sys.argv[3:]
V = {}; H = {}
for i in ids:
    im = nib.load(f"{root}/qc/seg-aligned/{i}.nii.gz"); L = np.squeeze(np.asarray(im.dataobj)).astype(int); v = np.prod(im.header.get_zooms()[:3])
    c = np.bincount(L.ravel(), minlength=121)*v/1000
    V[i] = {b: (c[d["L"]], c[d["R"]]) for b, d in pairs.items()}
    H[i] = sum(c[d["L"]] for d in pairs.values())/sum(c[d["R"]] for d in pairs.values())
with open(f"{outp}-pairs.tsv", "w") as f:
    bs = sorted(pairs); f.write("target_id\themisphere_LR\t" + "\t".join(bs) + "\n")
    for i in ids: f.write(i + f"\t{H[i]:.3f}\t" + "\t".join(f"{V[i][b][0]/max(V[i][b][1],1e-9):.3f}" for b in bs) + "\n")
lr = {b: np.array([np.log(V[i][b][0]/max(V[i][b][1], 1e-9)) for i in ids]) for b in bs}
med = {b: np.median(lr[b]) for b in bs}; mad = {b: 1.4826*np.median(np.abs(lr[b]-med[b]))+1e-9 for b in bs}
z = {i: {b: (np.log(V[i][b][0]/max(V[i][b][1], 1e-9))-med[b])/mad[b] for b in bs} for i in ids}
h = np.array([np.log(H[i]) for i in ids]); hm = np.median(h); hs = 1.4826*np.median(np.abs(h-hm))
print(f"{len(pairs)} L/R label pairs; hemisphere L/R: median {np.exp(hm):.3f}, range {np.exp(h.min()):.3f}-{np.exp(h.max()):.3f}, robust sd(log) {hs:.3f}")
with open(f"{outp}-outliers.tsv", "w") as f:
    f.write("target_id\themisphere_LR\themisphere_z\tn_pairs_|z|>4\tworst_pair\tworst_pair_LR\tworst_z\n")
    for k, i in enumerate(ids):
        w = max(bs, key=lambda b: abs(z[i][b])); n4 = sum(abs(z[i][b]) > 4 for b in bs)
        f.write(f"{i}\t{H[i]:.3f}\t{(np.log(H[i])-hm)/hs:+.1f}\t{n4}\t{w}\t{V[i][w][0]/max(V[i][w][1],1e-9):.2f}\t{z[i][w]:+.1f}\n")
