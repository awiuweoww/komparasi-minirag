#!/usr/bin/env python3
"""
Pembangun Lapisan 1 (struktur dan relasi antar-regulasi) sesuai skema_relasi_regulasi.yaml v1.1.

v1.1: relasi BPK dengan catatan/sasaran_efektif, "Ditetapkan dengan", relasi_manual
(menyesuaikan_pidana UU 1/2026), butir amar uji materi, label versi Perpu yang ditetapkan UU,
berlaku_sampai pada pencabutan omnibus.

Masukan:
  --metadata metadata_regulasi.json         instans metadata (blok METADATA + STATUS PERATURAN BPK)
  --teks ID=PATH                            teks peraturan (Markdown hasil OCR/MinerU), boleh berulang:
                                            ID peraturan induk  -> versi asli tiap pasal
                                            ID peraturan pengubah -> peristiwa perubahan + versi baru
  --induk uu/2004/31                        ID undang-undang induk yang pasalnya diubah
Keluaran (folder --out):
  lapisan1.graphml   graf Lapisan 1 (node: Peraturan, Pasal, VersiPasal, PeristiwaPerubahan, PutusanPengadilan)
  lapisan1.json      node dan edge dalam JSON
  jangkar.json       peta label <-> ID untuk chunker dan penautan Lapisan 2
  laporan.txt        hasil validasi

Contoh:
  python3 bangun_lapisan1.py --metadata metadata_regulasi.json \
      --teks "uu/2009/45=UU Nomor 45 Tahun 2009.md" --induk uu/2004/31 --out keluaran/
"""
import argparse
import collections
import json
import os
import re

import datetime

import networkx as nx

INVERS = {"mengubah": "diubah_dengan", "diubah_dengan": "mengubah", "mencabut": "dicabut_dengan",
          "dicabut_dengan": "mencabut", "mencabut_sebagian": "dicabut_sebagian_dengan",
          "dicabut_sebagian_dengan": "mencabut_sebagian", "menetapkan": "ditetapkan_dengan",
          "ditetapkan_dengan": "menetapkan", "melaksanakan": "dilaksanakan_dengan", "menguji": "diuji_dengan",
          "menyesuaikan_pidana": "disesuaikan_pidananya_oleh",
          "disesuaikan_pidananya_oleh": "menyesuaikan_pidana"}
RUJUKAN_BERTINGKAT = re.compile(r"Pasal\s+(\d+[A-Z]?)(?:\s+ayat\s+\((\w+)\))?(?:\s+huruf\s+([a-z]))?\s+dalam\s+"
                                r"Pasal\s+(\d+)\s+angka\s+(\d+)(?:\s+Lampiran)?", re.I)


def hari_sebelum(tgl):
    return (datetime.date.fromisoformat(tgl) - datetime.timedelta(days=1)).isoformat()

ROMAN = {"I", "II", "III", "IV", "V"}

# --------------------------------------------------------------------------- pola teks
CATCHWORD = re.compile(r"^[^\n]{0,60}?\s\.\s\.\s\.\s*$")
HEADING = re.compile(r"^Pasal\s+(\d+[A-Z]?|[IVX]+)\s*$")
ANGKA_PREFIX = re.compile(r"^(\d+)\.\s+")
UBAH = re.compile(r"Ketentuan\s+(?:ayat\s+\((\w+)\)\s+)?Pasal\s+(\d+[A-Z]?)((?:\s*(?:,|dan)?\s*angka\s+\d+)*)"
                  r"(?:\s+ayat\s+\(\w+\))?\s+.*?(?:diubah|ditambah|dihapus\s+sehingga)", re.I)
SISIP = re.compile(r"(?:Di\s+antara|Diantara)\s+.*?disisipkan\s+.*?(?:yakni|yaitu)\s+(.+?)(?:,?\s+yang\s+berbunyi|\s+sehingga|:|$)", re.I)
HAPUS = re.compile(r"^(?:Ketentuan\s+)?Pasal\s+(\d+[A-Z]?)\s+dihapus\.?$", re.I)
AYAT = re.compile(r"^\((\d+[a-z]?)\)\s+")
REF_OTHER = re.compile(r"sebagaimana\s+dimaksud\s+dalam\s+Pasal\s+(\d+[A-Z]?)(?:\s+ayat\s+\((\d+[a-z]?)\))?(?:\s+huruf\s+([a-z]))?", re.I)
REF_SAME = re.compile(r"sebagaimana\s+dimaksud\s+pada\s+ayat\s+\((\d+[a-z]?)\)", re.I)
STOP = re.compile(r"^(PENJELASAN|Pasal\s+II|Undang-Undang\s+ini\s+mulai\s+berlaku|Agar\s+setiap\s+orang)", re.I)


def paragraphs(path):
    raw = open(path, encoding="utf-8").read().replace("\r\n", "\n")
    out = []
    for p in raw.split("\n\n"):
        p = re.sub(r"\s+", " ", p.replace("**", "").replace("#", "")).strip()
        if p and not CATCHWORD.match(p):
            out.append(p)
    return out


# --------------------------------------------------------------------------- ID & label
def work_id(induk, nomor, ayat=None, angka=None, huruf=None):
    s = f"{induk}/pasal/{nomor}"
    if ayat:
        s += f"/ayat/{ayat}"
    if huruf:
        s += f"/huruf/{huruf}"
    if angka:
        s += f"/angka/{angka}"
    return s


def work_label(alias, nomor, ayat=None, angka=None, huruf=None):
    s = f"Pasal {nomor}"
    if ayat:
        s += f" ayat ({ayat})"
    if huruf:
        s += f" huruf {huruf}"
    if angka:
        s += f" angka {angka}"
    return f"{s} {alias}"


class Lapisan1:
    def __init__(self, meta, induk):
        self.G = nx.MultiDiGraph()
        self.meta = {p["id"]: p for p in meta["peraturan"]}
        self.induk = induk
        self.alias = self.meta[induk].get("induk_alias") or self.meta[induk]["label"]
        self.issues = []
        for p in meta["peraturan"]:
            props = {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v)
                     for k, v in p.items() if k not in ("relasi", "relasi_manual") and not k.startswith("_") and v is not None}
            self.node(p["id"], "Peraturan", diambil_pada=meta.get("diambil_pada"), **props)
        for p in meta["peraturan"]:
            for blok, src in (("relasi", "bpk"), ("relasi_manual", "manual")):
                for rel, targets in (p.get(blok) or {}).items():
                    for t in targets:
                        tid = t["id"] if isinstance(t, dict) else t
                        extra = {k: (", ".join(v) if isinstance(v, list) else v) for k, v in t.items() if k != "id"} if isinstance(t, dict) else {}
                        if tid not in self.G:
                            self.node(tid, "Peraturan", label=tid, status_verifikasi="perlu_cek")
                            self.issues.append(f"peraturan {tid} dirujuk oleh {p['id']} ({rel}) tetapi tidak ada di metadata")
                        self.edge(p["id"], tid, rel, sumber=src, **extra)
        self.amar = []          # (butir_id, sasaran_teks) untuk dipetakan setelah versi dibangun
        for d in meta.get("putusan", []):
            self.node(d["id"], "PutusanPengadilan", label=d["label"], lembaga=d.get("lembaga"),
                      relevan_perikanan=d.get("relevan_perikanan"))
            for k, t in enumerate(d.get("menguji", []), 1):
                t = t if isinstance(t, dict) else {"id": t}
                self.edge(d["id"], t["id"], "menguji", sumber="bpk")
                if t.get("sasaran") or t.get("jenis_amar"):
                    bid = f"{d['id']}/amar/{k}"
                    self.node(bid, "ButirAmar", label=f"{d['label']} amar {k}", putusan=d["id"], nomor=str(k),
                              sasaran_teks=t.get("sasaran"), jenis_amar=t.get("jenis_amar"), tafsir=t.get("tafsir"),
                              peraturan_diuji=t["id"])
                    self.edge(d["id"], bid, "memuat_amar", sumber="bpk")
                    self.amar.append((bid, t["id"], t.get("sasaran") or ""))
        self.add_inverses()

    # ----------------------------------------------------------------- helpers
    def node(self, nid, kelas, **attrs):
        if nid in self.G:
            self.G.nodes[nid].update({k: v for k, v in attrs.items() if v is not None})
        else:
            self.G.add_node(nid, kelas=kelas, **{k: v for k, v in attrs.items() if v is not None})
        return nid

    def edge(self, a, b, rel, **attrs):
        for _, t, d in self.G.out_edges(a, data=True):
            if t == b and d.get("relasi") == rel:
                return
        self.G.add_edge(a, b, relasi=rel, **{k: v for k, v in attrs.items() if v is not None})

    def add_inverses(self):
        inv = INVERS
        for a, b, d in list(self.G.edges(data=True)):
            r = d.get("relasi")
            if r in inv:
                had = any(t == a and dd.get("relasi") == inv[r] for _, t, dd in self.G.out_edges(b, data=True))
                if not had:
                    keep = {k: d[k] for k in ("catatan", "berlaku") if k in d}
                    self.edge(b, a, inv[r], sumber="turunan", **keep)
                    if d.get("sumber") == "bpk" and inv[r] in ("mengubah", "diubah_dengan", "mencabut", "dicabut_dengan"):
                        self.issues.append(f"invers tidak tercatat di metadata: {b} {inv[r]} {a} (ditambahkan otomatis)")

    def work(self, nomor, ayat=None, angka=None, huruf=None):
        wid = work_id(self.induk, nomor, ayat, angka, huruf)
        self.node(wid, "Pasal", label=work_label(self.alias, nomor, ayat, angka, huruf), induk=self.induk,
                  nomor=nomor, ayat=ayat, angka=angka, huruf=huruf)
        if ayat or angka or huruf:
            parent = self.work(nomor)
            self.edge(wid, parent, "bagian_dari_pasal", sumber="parser")
        else:
            self.edge(self.induk, wid, "memuat_pasal", sumber="parser")
        return wid

    def penetap(self, sumber):
        """UU yang menetapkan Perpu `sumber` (relasi ditetapkan_dengan), atau None."""
        for _, t, d in self.G.out_edges(sumber, data=True):
            if d.get("relasi") == "ditetapkan_dengan":
                return t
        return None

    def version(self, wid, sumber, jenis, teks):
        vid = f"{wid}@{sumber}"
        base = self.G.nodes[wid]['label']
        lab, alias = f"{base} versi {self.meta[sumber]['label']}", None
        u = self.penetap(sumber)
        if u:                                   # Perpu yang ditetapkan: label memakai UU penetapan
            alias, lab = lab, f"{base} versi {self.meta[u]['label']}"
        self.node(vid, "VersiPasal", label=lab, alias_label=alias, pasal=wid, sumber=sumber, jenis=jenis, teks=teks,
                  berlaku_sejak=self.meta[sumber].get("tanggal_berlaku"), status_verifikasi="otomatis")
        self.edge(vid, wid, "versi_dari", sumber="parser")
        self.edge(sumber, vid, "menetapkan_versi", sumber="parser")
        return vid

    def references(self, vid, nomor, teks):
        pidana = "dipidana" in teks
        for m in REF_OTHER.finditer(teks):
            tgt = self.work(m.group(1).upper(), m.group(2), None, m.group(3))
            self.edge(vid, tgt, "merujuk", sumber="parser", jenis="sanksi_atas_norma" if pidana else "norma", frasa=m.group(0))
        for m in REF_SAME.finditer(teks):
            tgt = self.work(nomor, m.group(1))
            self.edge(vid, tgt, "merujuk", sumber="parser", jenis="norma", frasa=m.group(0))

    # ----------------------------------------------------------------- teks peraturan pengubah
    def parse_amending(self, sumber, path):
        paras = paragraphs(path)
        pasal_pengubah = "Pasal I" if self.meta[sumber].get("jenis_perubahan") == "perubahan" else \
            (self.meta[sumber].get("pasal_pengubah") or {}).get(self.induk, "Pasal ?")
        i, n_event, last_angka = 0, 0, 0
        stats = collections.Counter()
        while i < len(paras):
            p = paras[i]
            if STOP.match(p):
                break
            body = ANGKA_PREFIX.sub("", p)
            angka_m = ANGKA_PREFIX.match(p)
            angka = angka_m.group(1) if angka_m else str(last_angka + 1)   # nomor butir hilang di OCR
            kind, targets, angka_def = None, [], []
            m_h = HAPUS.match(body)
            m_u = UBAH.search(body) if body.lower().startswith(("ketentuan",)) else None
            m_s = SISIP.search(body) if re.match(r"(?i)di\s*antara", body) else None
            if m_h:
                kind, targets = "hapus", [m_h.group(1).upper()]
            elif m_u:
                kind, targets = "ubah", [m_u.group(2).upper()]
                angka_def = re.findall(r"angka\s+(\d+)", m_u.group(3) or "")
            elif m_s:
                # sisipan pasal ("yakni Pasal 15A") atau sisipan bagian/paragraf berisi pasal-pasal baru
                kind, targets = "sisip", [t.upper() for t in re.findall(r"Pasal\s+(\d+[A-Z]?)", m_s.group(1))]
            if not kind:
                i += 1
                continue
            n_event += 1
            if not angka_m:
                self.issues.append(f"butir tanpa nomor dianggap angka {angka}: {p[:80]}")
            last_angka = int(angka)
            eid = f"{sumber}/pasal/{pasal_pengubah.split()[-1]}/angka/{angka}"
            works = [self.work(t) for t in targets]
            u = self.penetap(sumber)
            alias_id = f"{u}/lampiran/pasal/{pasal_pengubah.split()[-1]}/angka/{angka}" if u else None
            self.node(eid, "PeristiwaPerubahan", label=f"{self.meta[sumber]['label']} {pasal_pengubah} angka {angka}",
                      pengubah=sumber, pasal_pengubah=pasal_pengubah, angka=angka, jenis=kind, kalimat=p, alias_id=alias_id)
            self.edge(eid, sumber, "bagian_dari", sumber="parser")
            for w in works:
                self.edge(eid, w, "menyasar", sumber="parser")
            stats[kind] += 1
            if kind == "hapus":
                for w in works:
                    self.edge(sumber, w, "menghapus_pasal", sumber="parser")
                    self.G.nodes[w]["dihapus"] = True
                i += 1
                continue
            # kumpulkan teks pasal baru sampai kalimat perubahan berikutnya
            i += 1
            pending = list(targets)
            current, buf = None, collections.OrderedDict()
            while i < len(paras):
                q = paras[i]
                qb = ANGKA_PREFIX.sub("", q)
                if STOP.match(q) or HAPUS.match(qb) or re.match(r"(?i)(ketentuan\s+(ayat\s+\(\w+\)\s+)?pasal\s+\d+\w*\b.*(diubah|ditambah|dihapus)|di\s*antara\s+(pasal|bagian|paragraf)\b.*disisipkan)", qb):
                    break
                h = HEADING.match(q)
                if h and h.group(1) not in ROMAN:
                    current = h.group(1).upper()
                    pending = [t for t in pending if t != current]
                elif current is None and pending:
                    current = pending.pop(0)          # judul pasal hilang di hasil OCR (mis. Pasal 94A)
                    self.issues.append(f"{eid}: judul Pasal {current} tidak ditemukan; teks dianggap milik Pasal {current}")
                if not h and current:
                    buf.setdefault(current, []).append(q)
                i += 1
            for nomor, lines in buf.items():
                jenis = "diubah" if kind == "ubah" else "disisipkan"
                w = self.work(nomor)
                self.edge(eid, w, "menyasar", sumber="parser")
                full = " ".join(lines)
                v = self.version(w, sumber, jenis, full)
                self.edge(eid, v, "menghasilkan_versi", sumber="parser")
                self.references(v, nomor, full)
                stats["versi_pasal"] += 1
                for ln in lines:
                    a = AYAT.match(ln)
                    d = ANGKA_PREFIX.match(ln) if nomor == "1" else None
                    if a:
                        va = self.version(self.work(nomor, ayat=a.group(1)), sumber, jenis, ln)
                        self.edge(eid, va, "menghasilkan_versi", sumber="parser")
                        self.edge(va, v, "bagian_dari_versi", sumber="parser")
                        self.references(va, nomor, ln)
                        stats["versi_ayat"] += 1
                    elif d and (not angka_def or d.group(1) in angka_def):
                        vd = self.version(self.work(nomor, angka=d.group(1)), sumber, jenis, ln)
                        self.edge(eid, vd, "menghasilkan_versi", sumber="parser")
                        self.edge(vd, v, "bagian_dari_versi", sumber="parser")
                        stats["versi_angka"] += 1
            if not buf:
                self.issues.append(f"{eid}: peristiwa '{kind}' tanpa teks pasal baru")
        return stats

    # ----------------------------------------------------------------- turunan & validasi
    def derive_versions(self):
        by_work = collections.defaultdict(list)
        for n, d in self.G.nodes(data=True):
            if d.get("kelas") == "VersiPasal":
                by_work[d["pasal"]].append(n)
        for w, vs in by_work.items():
            vs.sort(key=lambda v: (self.G.nodes[v].get("berlaku_sejak") or "0000", v))
            for old, new in zip(vs, vs[1:]):
                self.edge(new, old, "menggantikan_versi", sumber="turunan")
                if self.G.nodes[new].get("berlaku_sejak"):
                    self.G.nodes[old]["berlaku_sampai"] = hari_sebelum(self.G.nodes[new]["berlaku_sejak"])
            # pencabutan omnibus: versi terakhir yang sumbernya dicabut, tanpa versi pengganti
            last = vs[-1]
            src = self.G.nodes[last]["sumber"]
            pencabut = sorted((self.meta[r]["tanggal_berlaku"], r) for _, r, d in self.G.out_edges(src, data=True)
                              if d.get("relasi") == "dicabut_dengan" and self.meta.get(r, {}).get("tanggal_berlaku"))
            if pencabut and not self.G.nodes[last].get("berlaku_sampai"):
                tgl, r = pencabut[0]            # pencabut paling awal (Perpu 2/2022, bukan UU 6/2023)
                self.G.nodes[last]["berlaku_sampai"] = hari_sebelum(tgl)
                self.G.nodes[last]["status_verifikasi"] = "perlu_cek"
                self.G.nodes[last]["catatan_verifikasi"] = (f"sumber dicabut {r} sejak {tgl}; belum ada versi dari {r} - "
                                                            "pencabutan tidak menghidupkan rumusan lama")
                self.issues.append(f"{last}: sumber dicabut oleh {r} tanpa versi pengganti (perlu_cek)")

    def apply_penyesuaian_pidana(self):
        """UU penyesuaian umum (menyesuaikan_pidana -> UU induk): tandai versi pidana yang berlaku saat itu."""
        for a, b, d in list(self.G.edges(data=True)):
            if d.get("relasi") != "menyesuaikan_pidana" or b != self.induk:
                continue
            t = d.get("berlaku") or self.meta[a].get("tanggal_berlaku")
            n = 0
            for v, vd in list(self.G.nodes(data=True)):
                if vd.get("kelas") != "VersiPasal" or "dipidana" not in (vd.get("teks") or ""):
                    continue
                if vd.get("berlaku_sejak", "0000") <= t and (not vd.get("berlaku_sampai") or vd["berlaku_sampai"] >= t):
                    self.edge(a, v, "menyesuaikan_pidana", sumber="turunan", berlaku=t)
                    self.edge(v, a, "disesuaikan_pidananya_oleh", sumber="turunan", berlaku=t)
                    vd["status_verifikasi"] = "perlu_cek"
                    vd.setdefault("catatan_verifikasi", f"ancaman pidana disesuaikan {a} sejak {t}; cek Lampiran {a}")
                    n += 1
            self.issues.append(f"{a}: {n} versi pidana yang berlaku pada {t} ditandai disesuaikan (perlu_cek)")

    def map_amar(self):
        """Petakan butir amar bertingkat ('Pasal X dalam Pasal Y angka N Lampiran') ke Work/versi UU induk."""
        for bid, diuji, teks in self.amar:
            m = RUJUKAN_BERTINGKAT.search(teks)
            if not m:
                continue
            nomor, ayat, huruf, pasal_y, angka = m.groups()
            src = self.meta.get(diuji, {}).get("isi_lampiran") or diuji
            peta = self.meta.get(src, {}).get("pasal_pengubah") or {}
            if peta.get(self.induk) != f"Pasal {pasal_y}":
                continue                        # pasal pengubah untuk UU lain: di luar lingkup
            w = self.work(nomor.upper(), ayat, None, huruf)
            v = f"{w}@{src}"
            self.edge(bid, v if v in self.G else w, "menafsirkan", sumber="parser")

    def validate(self):
        for n, d in self.G.nodes(data=True):
            if d.get("kelas") == "VersiPasal":
                outs = [dd["relasi"] for _, _, dd in self.G.out_edges(n, data=True)]
                ins = [dd["relasi"] for _, _, dd in self.G.in_edges(n, data=True)]
                if outs.count("versi_dari") != 1 or ins.count("menetapkan_versi") != 1:
                    self.issues.append(f"{n}: versi_dari/menetapkan_versi tidak tepat satu")
            if d.get("kelas") == "PeristiwaPerubahan" and d.get("jenis") != "hapus":
                if not any(dd["relasi"] == "menghasilkan_versi" for _, _, dd in self.G.out_edges(n, data=True)):
                    self.issues.append(f"{n}: tidak menghasilkan versi")
            if d.get("kelas") == "Pasal":
                has_ver = any(dd["relasi"] == "versi_dari" for _, _, dd in self.G.in_edges(n, data=True))
                if not has_ver and not d.get("dihapus"):
                    d["status_verifikasi"] = "perlu_cek"   # dirujuk/disasar tetapi teks versinya belum di-index

    def export(self, out):
        os.makedirs(out, exist_ok=True)
        H = nx.MultiDiGraph()
        for n, d in self.G.nodes(data=True):
            H.add_node(n, **{k: (v if isinstance(v, (str, int, float, bool)) else str(v)) for k, v in d.items() if v is not None})
        for a, b, d in self.G.edges(data=True):
            H.add_edge(a, b, **{k: str(v) for k, v in d.items()})
        nx.write_graphml(H, os.path.join(out, "lapisan1.graphml"))
        data = {"nodes": [{"id": n, **d} for n, d in self.G.nodes(data=True)],
                "edges": [{"dari": a, "ke": b, **d} for a, b, d in self.G.edges(data=True)]}
        json.dump(data, open(os.path.join(out, "lapisan1.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        jangkar = {d["label"]: n for n, d in self.G.nodes(data=True) if d.get("kelas") in ("Pasal", "VersiPasal", "Peraturan")}
        jangkar.update({d["alias_label"]: n for n, d in self.G.nodes(data=True) if d.get("alias_label")})
        json.dump(jangkar, open(os.path.join(out, "jangkar.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metadata", required=True)
    ap.add_argument("--teks", action="append", default=[])
    ap.add_argument("--induk", default="uu/2004/31")
    ap.add_argument("--out", default="keluaran")
    a = ap.parse_args()
    L = Lapisan1(json.load(open(a.metadata, encoding="utf-8")), a.induk)
    report = []
    for spec in a.teks:
        sid, path = spec.split("=", 1)
        if sid == a.induk:
            report.append(f"{sid}: teks induk (versi asli) - parser versi asli belum diaktifkan pada contoh ini")
            continue
        st = L.parse_amending(sid, path)
        report.append(f"{sid}: " + ", ".join(f"{k}={v}" for k, v in sorted(st.items())))
    L.derive_versions()
    L.apply_penyesuaian_pidana()
    L.map_amar()
    L.validate()
    L.export(a.out)
    kelas = collections.Counter(d.get("kelas") for _, d in L.G.nodes(data=True))
    rel = collections.Counter(d.get("relasi") for _, _, d in L.G.edges(data=True))
    pasal_perlu_cek = sum(1 for _, d in L.G.nodes(data=True) if d.get('status_verifikasi') == 'perlu_cek' and d.get('kelas') == 'Pasal')
    lines = [
        "# Laporan Validasi Lapisan 1 (Versi Asli Mentor)",
        "",
        "## 1. Pemrosesan Dokumen",
    ] + [f"- {r}" for r in report] + [
        "",
        "## 2. Statistik Topologi Graf",
        f"- **Node per kelas:** `{dict(kelas)}`",
        f"- **Edge per relasi:** `{dict(rel)}`",
        f"- **Pasal berstatus `perlu_cek` (dirujuk/disasar, teks versinya belum di-index):** {pasal_perlu_cek}",
        "",
        "## 3. Catatan Validasi",
    ] + ([f"- [ ] {iss}" for iss in L.issues] if L.issues else ["- *(Tidak ada catatan)*"])
    rep_path = os.path.join(a.out, "laporan_validasi_lapisan1.md")
    open(rep_path, "w", encoding="utf-8").write("\n".join(lines))
    print("\n".join(report[:8]))
    print(f"catatan validasi: {len(L.issues)} (lihat {rep_path})")


if __name__ == "__main__":
    main()
