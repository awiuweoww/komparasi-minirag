#!/usr/bin/env python3
"""
Parser teks halaman Details peraturan.bpk.go.id -> entri metadata (skema v1.1).

Masukan : teks halaman yang disalin/disimpan dari browser (Ctrl+A, Ctrl+C, simpan .txt),
          karena halaman BPK menolak pengambilan otomatis dari server.
Keluaran: JSON satu entri `peraturan` (+ `putusan` dari blok UJI MATERI) untuk metadata_regulasi.json.

Pemakaian:
  python3 parse_bpk.py halaman_uu45.txt --url https://peraturan.bpk.go.id/Details/38790/uu-no-45-tahun-2009 \
      --lingkup uu/2004/31,uu/2009/45,uu/2020/11,perpu/2022/2,uu/2023/6 > uu45.json
  python3 parse_bpk.py halaman_uu45.txt --banding-abstrak keluaran/lapisan1.json --induk uu/2004/31
"""
import argparse
import json
import re
import sys

BULAN = {b: i for i, b in enumerate(["januari", "februari", "maret", "april", "mei", "juni", "juli", "agustus",
                                      "september", "oktober", "november", "desember"], 1)}
FIELDS = ["Tipe Dokumen", "Judul", "T.E.U.", "Nomor", "Bentuk", "Bentuk Singkat", "Tahun", "Tempat Penetapan",
          "Tanggal Penetapan", "Tanggal Pengundangan", "Tanggal Berlaku", "Sumber", "Subjek", "Status", "Bahasa",
          "Lokasi", "Bidang", "Alias"]
KEY = {"Tipe Dokumen": "tipe_dokumen", "Judul": "judul", "T.E.U.": "teu", "Nomor": "nomor", "Bentuk": "bentuk",
       "Bentuk Singkat": "bentuk_singkat", "Tahun": "tahun", "Tempat Penetapan": "tempat_penetapan",
       "Tanggal Penetapan": "tanggal_penetapan", "Tanggal Pengundangan": "tanggal_pengundangan",
       "Tanggal Berlaku": "tanggal_berlaku", "Sumber": "sumber", "Subjek": "subjek", "Status": "status",
       "Bahasa": "bahasa", "Lokasi": "lokasi", "Bidang": "bidang", "Alias": "alias"}
STATUS = {"Diubah dengan": "diubah_dengan", "Mengubah": "mengubah", "Dicabut dengan": "dicabut_dengan",
          "Dicabut sebagian dengan": "dicabut_sebagian_dengan", "Mencabut": "mencabut",
          "Mencabut sebagian": "mencabut_sebagian", "Menetapkan": "menetapkan",
          "Ditetapkan dengan": "ditetapkan_dengan"}
END_STATUS = re.compile(r"^(TENTANG DATABASE PERATURAN|KONTAK)$")
ENTRY = re.compile(r"^(UU|PERPU|Perpu|PP|Perpres|Permen\w*|Perda\w*)\s+No\.\s*(\d+)\s+Tahun\s+(\d{4})\s+tentang\s+(.+)$")
SUMBER = re.compile(r"LN\.?\s*(\d{4})\s*/\s*No\.?\s*(\d+),\s*TLN\s*No\.?\s*(\d+),\s*([^:]+?)\s*:\s*(\d+)\s*hlm", re.I)


def tanggal(s):
    m = re.match(r"(\d{1,2})\s+(\w+)\s+(\d{4})", s or "")
    return f"{m.group(3)}-{BULAN[m.group(2).lower()]:02d}-{int(m.group(1)):02d}" if m and m.group(2).lower() in BULAN else None


def pid(bentuk, nomor, tahun):
    return f"{bentuk.lower()}/{tahun}/{nomor}"


def parse(text, url=None, lingkup=None):
    lines = [l.strip() for l in text.replace("\r", "").split("\n")]
    lines = [l for l in lines if l]
    out, i = {}, 0
    # --- abstrak
    if "Abstrak" in lines:
        k = lines.index("Abstrak") + 1
        out["abstrak"] = lines[k] if k < len(lines) and lines[k] != "METADATA PERATURAN" else None
    # --- metadata: label pada satu baris, nilai pada baris berikutnya (boleh kosong, mis. Bidang)
    if "METADATA PERATURAN" in lines:
        i = lines.index("METADATA PERATURAN") + 1
        while i < len(lines) and not lines[i].startswith("Halaman ini telah diakses"):
            if lines[i] in FIELDS:
                nxt = lines[i + 1] if i + 1 < len(lines) else ""
                val = "" if nxt in FIELDS or nxt.startswith("Halaman ini") else nxt
                out[KEY[lines[i]]] = val
                i += 1 if val == "" else 2
            else:
                i += 1
    for k in ("tanggal_penetapan", "tanggal_pengundangan", "tanggal_berlaku"):
        if out.get(k):
            out[k] = tanggal(out[k])
    if out.get("tahun"):
        out["tahun"] = int(out["tahun"])
    out["subjek"] = [s.strip() for s in out.get("subjek", "").split(" - ") if s.strip()]
    out["bidang"] = [s.strip() for s in out.get("bidang", "").split(" - ") if s.strip()]
    out["alias"] = [s.strip() for s in out.get("alias", "").split("•") if s.strip()]
    m = SUMBER.search(out.get("sumber", ""))
    if m:
        out["sumber_terurai"] = {"ln_tahun": int(m.group(1)), "ln_nomor": int(m.group(2)), "tln": int(m.group(3)),
                                 "penerbit": m.group(4).strip(), "halaman": int(m.group(5))}
    if out.get("bentuk_singkat") and out.get("nomor"):
        out["id"] = pid(out["bentuk_singkat"], out["nomor"], out["tahun"])
        out["label"] = f"{out['bentuk_singkat']} Nomor {out['nomor']} Tahun {out['tahun']}"
    if url:
        out["url_sumber"] = url
        m = re.search(r"/Details/(\d+)", url)
        out["bpk_id"] = int(m.group(1)) if m else None
    # --- uji materi: "PUTUSAN Nomor X" lalu (opsional) satu paragraf amar berisi butir bernomor
    putusan = []
    if "UJI MATERI" in lines:
        j = lines.index("UJI MATERI") + 1
        while j < len(lines) and lines[j] != "FILE-FILE PERATURAN" and lines[j] != "STATUS PERATURAN":
            mp = re.match(r"PUTUSAN Nomor\s+(?:PUTUSAN Nomor\s+)?(\S+)", lines[j])
            if mp:
                nomor = mp.group(1)
                amar_txt = lines[j + 1] if j + 1 < len(lines) and not lines[j + 1].startswith(("PUTUSAN", "FILE-FILE")) else ""
                butir = [b.strip() for b in re.split(r"(?:^|;\s*)\d+\)\.?\s+", amar_txt) if b.strip()] or ([amar_txt] if amar_txt else [])
                menguji = []
                for b in butir:
                    sas = re.match(r"(?:(?:Frasa|Kata)\s+[“\"].+?[”\"]\s+(?:dalam|pada)\s+(?:norma\s+)?)?(.+?)\s+Lampiran", b)
                    jenis = "inkonstitusional_bersyarat" if "sepanjang tidak dimaknai" in b else "tidak_mengikat"
                    taf = re.search(r"sepanjang tidak dimaknai[^“\"]*[“\"](.+?)[”\"]", b)
                    menguji.append({"id": out.get("id"), "sasaran": (sas.group(1) + " Lampiran") if sas else None,
                                    "unsur": "frasa" if b.startswith("Frasa") else "kata" if b.startswith("Kata") else "pasal",
                                    "jenis_amar": jenis, "tafsir": taf.group(1) if taf else None})
                if not menguji:
                    menguji = [{"id": out.get("id"), "sasaran": None, "jenis_amar": None, "tafsir": None}]
                slug = nomor.lower().replace("/", "-")
                putusan.append({"id": f"putusan/mk/{slug}", "label": f"Putusan MK Nomor {nomor}", "lembaga": "MK",
                                "menguji": menguji, "url_sumber": url})
                out.setdefault("uji_materi", []).append(f"putusan/mk/{slug}")
            j += 1
    # --- status peraturan
    rel, luar = {}, []
    if "STATUS PERATURAN" in lines:
        j = lines.index("STATUS PERATURAN") + 1
        cur, last = None, None
        while j < len(lines) and not END_STATUS.match(lines[j]):
            l = lines[j]
            lab = l.rstrip(" :").strip()
            if lab in STATUS and l.endswith(":"):
                cur = STATUS[lab]
            elif cur:
                me = ENTRY.match(l)
                if me:
                    tid = pid(me.group(1), me.group(2), me.group(3))
                    last = {"id": tid, "judul": me.group(4)}
                    if lingkup is None or tid in lingkup:
                        rel.setdefault(cur, []).append(last)
                    else:
                        luar.append(f"{cur}: {tid}")
                elif l.startswith("Staatsblad"):
                    luar.append(f"{cur}: {l[:60]}")
                    last = None
                elif last is not None:                       # baris catatan di bawah entri
                    last["catatan"] = (last.get("catatan", "") + " " + l).strip()
            j += 1
    for k, v in rel.items():   # entri tanpa catatan ditulis sebagai ID saja, seperti metadata_regulasi.json
        rel[k] = [e if e.get("catatan") else e["id"] for e in v]
        for e in rel[k]:
            if isinstance(e, dict):
                e.pop("judul", None)
    out["relasi"] = rel
    if luar:
        out["_di_luar_lingkup"] = luar
    return out, putusan


PASAL_ABSTRAK = re.compile(r"Pasal\s+(\d+[A-Z]?)")


def banding_abstrak(abstrak, lapisan1, induk):
    """Bandingkan pasal yang disebut abstrak BPK dengan Work yang disasar peristiwa hasil parser."""
    teks = re.sub(r"(?i)di\s*antara\s+Pasal\s+\d+[A-Z]?\s+dan\s+Pasal\s+\d+[A-Z]?", " ", abstrak or "")  # tetangga sisipan
    disebut = set(PASAL_ABSTRAK.findall(teks))
    data = json.load(open(lapisan1, encoding="utf-8"))
    disasar = {e["ke"].split("/pasal/")[1].split("/")[0] for e in data["edges"]
               if e["relasi"] == "menyasar" and e["ke"].startswith(induk + "/pasal/")}
    return sorted(disebut - disasar, key=lambda x: (int(re.match(r"\d+", x).group()), x)), \
        sorted(disasar - disebut, key=lambda x: (int(re.match(r"\d+", x).group()), x)), len(disebut), len(disasar)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("teks")
    ap.add_argument("--url")
    ap.add_argument("--lingkup", help="daftar ID dipisah koma; relasi ke peraturan lain dicatat di _di_luar_lingkup")
    ap.add_argument("--banding-abstrak", metavar="LAPISAN1_JSON")
    ap.add_argument("--induk", default="uu/2004/31")
    a = ap.parse_args()
    lingkup = set(a.lingkup.split(",")) if a.lingkup else None
    out, putusan = parse(open(a.teks, encoding="utf-8").read(), a.url, lingkup)
    if a.banding_abstrak:
        hilang, tambahan, n1, n2 = banding_abstrak(out.get("abstrak"), a.banding_abstrak, a.induk)
        print(f"pasal disebut abstrak BPK: {n1}; pasal disasar parser: {n2}")
        print(f"disebut abstrak tetapi tidak disasar parser: {hilang or '-'}")
        print(f"disasar parser tetapi tidak disebut abstrak: {tambahan or '-'}")
        return
    json.dump({"peraturan": out, "putusan": putusan}, sys.stdout, ensure_ascii=False, indent=1)
    print()


if __name__ == "__main__":
    main()
