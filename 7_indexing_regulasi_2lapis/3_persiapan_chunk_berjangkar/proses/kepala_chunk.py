#!/usr/bin/env python3
"""
Kepala chunk berjangkar untuk ekstraksi Lapisan 2 (skema_relasi_regulasi.yaml v1.2, layer2.kepala_chunk).

Masukan : chunk hasil rechunk_512_v2.py (kolom header "UU Nomor 45 Tahun 2009 | Pasal 66 ayat (1)-(3), ...")
          + Lapisan 1 hasil bangun_lapisan1.py (lapisan1.json).
Keluaran: chunk yang baris pertamanya diganti kepala berjangkar, mis.
          "UU Nomor 45 Tahun 2009 | jangkar: Pasal 66 ayat (2) UU Perikanan versi UU Nomor 45 Tahun 2009; ..."
          ditambah kolom versi_id, peraturan_id, pasal_pengubah, lapisan2 (False = jangan diekstrak).

Label TIDAK pernah diketik tangan: semuanya label node Lapisan 1, sehingga nama jangkar yang ditulis
LLM bisa dicocokkan kembali ke ID lewat jangkar.json.

Pemakaian:
  python3 kepala_chunk.py --chunks chunks_uu_45_2009.json --lapisan1 keluaran/lapisan1.json \
      --sumber uu/2009/45 --induk uu/2004/31 --out chunks_uu45_berjangkar.json
  # omnibus: --sumber perpu/2022/2 --pasal-pengubah "Pasal 27"
"""
import argparse
import json
import os
import re

SEG = re.compile(r"^(Penjelasan\s+)?Pasal\s+(\d+[A-Z]?)(?:\s+ayat\s+\((\w+)\)(?:-\((\w+)\))?)?"
                 r"(?:\s+angka\s+(\d+)(?:-(\d+))?)?(\s+\(lanjutan\))?$")
TANPA_NORMA = re.compile(r"^(Pembukaan|Penutup|Penjelasan Umum|Konsiderans)", re.I)
MAKS_JANGKAR = 6


def nkey(s):
    m = re.match(r"(\d+)(\w*)", s)
    return (int(m.group(1)), m.group(2)) if m else (10 ** 6, s)


class Jangkar:
    def __init__(self, lapisan1, induk):
        data = json.load(open(lapisan1, encoding="utf-8"))
        self.N = {n["id"]: n for n in data["nodes"]}
        self.induk = induk

    def label(self, nid):
        return self.N[nid]["label"]

    def versi(self, sumber, nomor, ayat=None, angka=None):
        w = f"{self.induk}/pasal/{nomor}" + (f"/ayat/{ayat}" if ayat else "") + (f"/angka/{angka}" if angka else "")
        v = f"{w}@{sumber}"
        return v if v in self.N else None

    def sub(self, sumber, nomor, kind):
        """Semua nomor ayat/angka yang punya VersiPasal sendiri untuk pasal ini."""
        pre = f"{self.induk}/pasal/{nomor}/{kind}/"
        return sorted({k[len(pre):].split("@")[0] for k in self.N if k.startswith(pre) and k.endswith("@" + sumber)}, key=nkey)

    def dihapus(self, nomor):
        w = self.N.get(f"{self.induk}/pasal/{nomor}")
        return bool(w and str(w.get("dihapus")) in ("True", "true"))


def segments(header):
    body = header.split(" | ", 1)[1] if " | " in header else ""
    if TANPA_NORMA.match(body):
        return None
    out, penjelasan = [], body.startswith("Penjelasan")
    for s in body.split(", "):
        s = s.strip()
        if penjelasan and not s.startswith("Penjelasan"):
            s = "Penjelasan " + s
        m = SEG.match(s)
        if m:
            out.append(dict(penjelasan=bool(m.group(1)), nomor=m.group(2).upper(), a_lo=m.group(3), a_hi=m.group(4) or m.group(3),
                            n_lo=m.group(5), n_hi=m.group(6) or m.group(5), lanjutan=bool(m.group(7))))
    return out


def in_range(x, lo, hi):
    return lo is None or nkey(lo) <= nkey(x) <= nkey(hi)


def anchors_for(seg, J, sumber, ringkas):
    nomor = seg["nomor"]
    if J.dihapus(nomor) and not J.versi(sumber, nomor):
        return [(f"{J.label(f'{J.induk}/pasal/{nomor}')} (dihapus)", f"{J.induk}/pasal/{nomor}")]
    pasal_v = J.versi(sumber, nomor)
    if seg["penjelasan"] or ringkas:
        return [("Penjelasan " + J.label(pasal_v) if seg["penjelasan"] else J.label(pasal_v), pasal_v)] if pasal_v else []
    res = []
    ayat = [a for a in J.sub(sumber, nomor, "ayat") if in_range(a, seg["a_lo"], seg["a_hi"])]
    angka = [n for n in J.sub(sumber, nomor, "angka") if in_range(n, seg["n_lo"], seg["n_hi"])]
    for a in ayat:
        v = J.versi(sumber, nomor, ayat=a)
        res.append((J.label(v), v))
    for n in angka:
        v = J.versi(sumber, nomor, angka=n)
        res.append((J.label(v), v))
    if not ayat and pasal_v:
        res.insert(0, (J.label(pasal_v), pasal_v))   # pasal tanpa ayat, atau angka lain di Pasal 1
    return res


def build(chunk, J, sumber, label_sumber, pasal_pengubah):
    header, _, rest = chunk["content"].partition("\n")
    segs = segments(header)
    base = dict(chunk, versi_id=[], peraturan_id=sumber, pasal_pengubah=pasal_pengubah)
    if segs is None:
        return dict(base, lapisan2=False, kepala_jangkar=None)
    pairs = [anchors_for(s, J, sumber, False) for s in segs]
    if sum(len(p) for p in pairs) > MAKS_JANGKAR:          # pasal utuh diringkas ke tingkat pasal
        pairs = [anchors_for(s, J, sumber, not s["lanjutan"]) for s in segs]
    labels, ids = [], []
    for s, p in zip(segs, pairs):
        for i, (lab, vid) in enumerate(p):
            if lab in labels:
                continue
            labels.append(lab + (" (lanjutan)" if s["lanjutan"] and i == 0 else ""))
            ids.append(vid)
    if not labels:
        return dict(base, lapisan2=False, kepala_jangkar=None)
    kepala = " | ".join([label_sumber] + ([pasal_pengubah] if pasal_pengubah else []) + ["jangkar: " + "; ".join(labels)])
    return dict(base, content=kepala + "\n" + rest, versi_id=ids, lapisan2=True, kepala_jangkar=kepala, kepala_lama=header)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunks", required=True)
    ap.add_argument("--lapisan1", required=True)
    ap.add_argument("--sumber", required=True)
    ap.add_argument("--induk", default="uu/2004/31")
    ap.add_argument("--pasal-pengubah", default=None)
    ap.add_argument("--laporan-md", default=None, help="Path output laporan ringkasan injeksi chunk (.md)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    J = Jangkar(a.lapisan1, a.induk)
    label_sumber = J.label(a.sumber)
    chunks = json.load(open(a.chunks, encoding="utf-8"))
    out = [build(c, J, a.sumber, label_sumber, a.pasal_pengubah) for c in chunks]
    json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    n2 = sum(c["lapisan2"] for c in out)
    nj = [len(c["versi_id"]) for c in out if c["lapisan2"]]
    print(f"chunk: {len(out)} | diekstrak Lapisan 2: {n2} | dilewati: {len(out) - n2} | "
          f"jangkar per chunk: rata-rata {sum(nj) / max(1, len(nj)):.1f}, maks {max(nj or [0])}")

    rep_md_path = a.laporan_md or os.path.join(os.path.dirname(os.path.abspath(a.out)), "laporan_injeksi_chunk.md")
    md_lines = [
        "# Laporan Injeksi Header Jangkar Chunk (Persiapan Lapisan 2)",
        "",
        "## Ringkasan Injeksi Chunk",
        f"- **Total Chunk Masukan:** {len(out)}",
        f"- **Chunk Memuat Norma (Diekstrak Lapisan 2):** {n2} ({n2/max(1,len(out)):.1%})",
        f"- **Chunk Dilewati (Non-Substantif: Pembukaan/Konsiderans/Penutup):** {len(out) - n2}",
        f"- **Rata-rata Jangkar per Chunk:** {sum(nj) / max(1, len(nj)):.1f}",
        f"- **Maksimum Jangkar dalam Satu Chunk:** {max(nj or [0])}",
        f"- **File Chunk Berjangkar:** `{os.path.abspath(a.out)}`",
        ""
    ]
    try:
        open(rep_md_path, "w", encoding="utf-8").write("\n".join(md_lines))
        print(f"Laporan injeksi chunk tersimpan di: {rep_md_path}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
