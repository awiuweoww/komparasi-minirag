#!/usr/bin/env python3
"""
Mengompilasi seluruh file teks mentah JDIH BPK (data_mentah_bpk/)
menjadi satu berkas utuh metadata_regulasi.json di folder hasil/
"""

import json
import os
import sys
from parsing_link_jdih import parse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data_mentah_bpk")
OUT_FILE = os.path.join(BASE_DIR, "..", "hasil", "metadata_regulasi.json")

LINGKUP = {"uu/2004/31", "uu/2009/45", "uu/2020/11", "perpu/2022/2", "uu/2023/6"}

ENTRI_INPUT = [
    {
        "file": "UU_31_tahun_2004.txt",
        "url": "https://peraturan.bpk.go.id/Details/28551/uu-no-31-tahun-2004",
        "jenis_perubahan": "induk",
        "induk_alias": "UU Perikanan"
    },
    {
        "file": "UU_45_tahun_2009.txt",
        "url": "https://peraturan.bpk.go.id/Details/38790/uu-no-45-tahun-2009",
        "jenis_perubahan": "perubahan"
    },
    {
        "file": "UU_11_tahun_2020.txt",
        "url": "https://peraturan.bpk.go.id/Details/147573/uu-no-11-tahun-2020",
        "jenis_perubahan": "omnibus",
        "pasal_pengubah": {"uu/2004/31": "Pasal 27"}
    },
    {
        "file": "PERPU_2_tahun_2022.txt",
        "url": "https://peraturan.bpk.go.id/Details/219760/perpu-no-2-tahun-2022",
        "jenis_perubahan": "omnibus",
        "pasal_pengubah": {"uu/2004/31": "Pasal 27"}
    },
    {
        "file": "UU_6_tahun_2023.txt",
        "url": "https://peraturan.bpk.go.id/Details/226786/uu-no-6-tahun-2023",
        "jenis_perubahan": "penetapan_perpu",
        "isi_lampiran": "perpu/2022/2",
        "pasal_pengubah": {"uu/2004/31": "Pasal 27"}
    }
]

# Peraturan penyesuaian pidana KUHP baru (manual entry sesuai skema v1.2)
UU_2026_1 = {
    "id": "uu/2026/1",
    "label": "UU Nomor 1 Tahun 2026",
    "bentuk_singkat": "UU",
    "nomor": "1",
    "tahun": 2026,
    "judul": "Penyesuaian Pidana",
    "teu": "Indonesia, Pemerintah Pusat",
    "tanggal_penetapan": "2026-01-02",
    "tanggal_pengundangan": "2026-01-02",
    "tanggal_berlaku": "2026-01-02",
    "status": "Berlaku",
    "jenis_perubahan": "penyesuaian_umum",
    "alias": ["UU Penyesuaian Pidana", "UU 1/2026"],
    "relasi_manual": {
        "menyesuaikan_pidana": [
            {"id": "uu/2004/31", "berlaku": "2026-01-02"}
        ]
    }
}


def main():
    print("=" * 65)
    print("MEMULAI PARSING METADATA JDIH BPK DARI TEKS SALINAN BROWSER")
    print("=" * 65)
    
    daftar_peraturan = []
    daftar_putusan = []
    seen_putusan = set()

    for item in ENTRI_INPUT:
        path = os.path.join(DATA_DIR, item["file"])
        if not os.path.exists(path):
            print(f"[LEWATI] File {item['file']} tidak ditemukan di {DATA_DIR}")
            continue
            
        print(f"-> Memproses {item['file']} ({item['url']})...")
        teks = open(path, encoding="utf-8").read()
        per, put = parse(teks, item["url"], LINGKUP)
        
        # Tambahkan atribut spesifik sesuai skema v1.2
        if item.get("jenis_perubahan"):
            per["jenis_perubahan"] = item["jenis_perubahan"]
        if item.get("induk_alias"):
            per["induk_alias"] = item["induk_alias"]
        if item.get("pasal_pengubah"):
            per["pasal_pengubah"] = item["pasal_pengubah"]
        if item.get("isi_lampiran"):
            per["isi_lampiran"] = item["isi_lampiran"]
            
        daftar_peraturan.append(per)
        
        for pt in put:
            if pt["id"] not in seen_putusan:
                daftar_putusan.append(pt)
                seen_putusan.add(pt["id"])

    # Tambahkan UU 1/2026
    daftar_peraturan.append(UU_2026_1)

    metadata_final = {
        "diambil_pada": "2026-11-10",
        "ruang_lingkup": {
            "induk": "uu/2004/31",
            "peraturan": [p["id"] for p in daftar_peraturan]
        },
        "peraturan": daftar_peraturan,
        "putusan": daftar_putusan
    }

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata_final, f, ensure_ascii=False, indent=1)

    print("=" * 65)
    print("[SUKSES] Kompilasi metadata JDIH BPK selesai!")
    print(f"Total Peraturan: {len(daftar_peraturan)}")
    print(f"Total Putusan  : {len(daftar_putusan)}")
    print(f"File Hasil     : {OUT_FILE}")
    print("=" * 65)


if __name__ == "__main__":
    main()

