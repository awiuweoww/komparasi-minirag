#!/usr/bin/env python3
"""
Penautan hasil ekstraksi MiniRAG (Lapisan 2) ke Lapisan 1, sesuai skema_relasi_regulasi.yaml v1.2 (layer2).

Masukan:
  --graf     graph_chunk_entity_relation.graphml hasil MiniRAG (nx.Graph tak berarah, nama huruf kecil)
  --chunks   chunk berjangkar dari kepala_chunk.py (chunk_id -> versi_id)
  --lapisan1 folder keluaran bangun_lapisan1.py (lapisan1.json, jangkar.json)
  --metadata metadata_regulasi.json, --skema skema_relasi_regulasi.yaml
Keluaran (--out):
  gabungan.graphml        Lapisan 1 + Lapisan 2 dalam format MiniRAG (entity_type, description, source_id),
                          ditambah eli_id, versi_id, peraturan_id, relasi, lapisan
  entitas_baru_embed.json node/edge yang perlu di-embed ulang ke vdb MiniRAG (Lapisan 1 dan node yang diganti)
  laporan_penautan.md     metrik penautan dalam format Markdown (metrik intrinsik eksperimen)

Langkah:
  1. struktur -> jangkar.json (tanpa beda huruf, tanpa "(lanjutan)", awalan "Penjelasan " dicatat);
     tidak cocok -> jangkar pertama chunk sumber ("struktur karangan")
  2. dasar_hukum yang merupakan peraturan korpus -> node Peraturan Lapisan 1
  3. kata kunci relasi -> relasi skema; arah ditentukan dari jenis entitas (graf MiniRAG tak berarah)
  4. versi_id tiap norma: jangkar terdekat lewat graf (maks 3 lompatan), cadangan: jangkar chunk sumber
  5. turunan: VersiPasal -mengancamkan-> sanksi
"""
import argparse
import collections
import json
import os
import re

import networkx as nx
import yaml

SEP = "<SEP>"


def low(s):
    return re.sub(r"\s+", " ", str(s).strip().strip('"').lower())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--graf", required=True)
    ap.add_argument("--chunks", required=True)
    ap.add_argument("--lapisan1", required=True)
    ap.add_argument("--metadata", default="metadata_regulasi.json")
    ap.add_argument("--skema", default="skema_relasi_regulasi.yaml")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    sk = yaml.safe_load(open(a.skema, encoding="utf-8"))["layer2"]
    REL = sk["relasi_norma"]
    meta = json.load(open(a.metadata, encoding="utf-8"))
    L1 = json.load(open(os.path.join(a.lapisan1, "lapisan1.json"), encoding="utf-8"))
    N1 = {n["id"]: n for n in L1["nodes"]}
    jangkar = {low(k): v for k, v in json.load(open(os.path.join(a.lapisan1, "jangkar.json"), encoding="utf-8")).items()}
    korpus = {}
    for p in meta["peraturan"]:
        if p["id"] in meta["ruang_lingkup"]["peraturan"]:
            for nm in [p["label"]] + p.get("alias", []) + ([p["induk_alias"]] if p.get("induk_alias") else []):
                korpus[low(nm)] = p["id"]
    chunks = {c["chunk_id"]: c for c in json.load(open(a.chunks, encoding="utf-8"))}
    G = nx.read_graphml(a.graf)
    lower_names = all(n == n.lower() for n in G.nodes)

    st = collections.Counter()
    galat = collections.defaultdict(list)
    peta = {}                      # node MiniRAG -> id Lapisan 1
    bagian = {}

    def chunk_ids(d):
        return [c for c in str(d.get("source_id", "")).split(SEP) if c]

    def chunk_anchors(d):
        out = []
        for c in chunk_ids(d):
            out += chunks.get(c, {}).get("versi_id", [])
        return list(dict.fromkeys(out))

    # ---- 1-2. struktur dan dasar_hukum korpus
    for n, d in G.nodes(data=True):
        t = low(d.get("entity_type", ""))
        d["entity_type"] = t
        if t == "struktur":
            st["struktur"] += 1
            key = re.sub(r"\s*\(lanjutan\)$", "", low(n))
            pen = key.startswith("penjelasan ")
            if pen:
                key = key[len("penjelasan "):]
            if key in jangkar:
                peta[n] = jangkar[key]
                st["struktur_cocok"] += 1
                bagian[n] = "penjelasan" if pen else "batang_tubuh"
            else:
                ca = chunk_anchors(d)
                if ca:
                    peta[n] = ca[0]
                    st["struktur_karangan"] += 1
                    galat["struktur karangan (dipindah ke jangkar chunk)"].append(f"{n} -> {N1[ca[0]]['label']}")
                else:
                    st["struktur_tanpa_jangkar"] += 1
                    galat["struktur tanpa jangkar chunk (dibiarkan)"].append(n)
        elif t == "dasar_hukum" and low(n) in korpus:
            peta[n] = korpus[low(n)]
            st["peraturan_korpus_ditulis"] += 1
            galat["peraturan korpus ditulis LLM (dilebur ke Lapisan 1)"].append(n)

    # ---- graf gabungan: mulai dari Lapisan 1
    H = nx.Graph()
    nm = (lambda s: s.lower()) if lower_names else (lambda s: s)

    def l1_name(i):
        return nm(N1[i]["label"] if i in N1 else i)

    for n in L1["nodes"]:
        desc = [n.get("label", n["id"])]
        if n.get("kelas") == "VersiPasal":
            desc.append(f"berlaku sejak {n.get('berlaku_sejak') or '?'}" + (f" sampai {n['berlaku_sampai']}" if n.get("berlaku_sampai") else " (masih berlaku)"))
            if n.get("status_verifikasi") == "perlu_cek":
                desc.append(f"perlu dicek: {n.get('catatan_verifikasi', '')}")
            if n.get("teks"):
                desc.append("teks: " + n["teks"][:400])
        elif n.get("kelas") == "Peraturan":
            desc += [n.get("judul", ""), f"status {n.get('status', '?')}", f"berlaku {n.get('tanggal_berlaku', '?')}"]
        elif n.get("kelas") == "ButirAmar":
            desc += [n.get("sasaran_teks") or "", n.get("jenis_amar") or "", n.get("tafsir") or ""]
        H.add_node(l1_name(n["id"]), entity_type=low(n.get("kelas", "")), eli_id=n["id"], lapisan=1,
                   description=". ".join(x for x in desc if x), source_id=n.get("sumber") or n["id"])
    for e in L1["edges"]:
        if e["dari"] in N1 and e["ke"] in N1:
            H.add_edge(l1_name(e["dari"]), l1_name(e["ke"]), relasi=e["relasi"], keywords=e["relasi"].replace("_", " "),
                       description=f"{N1[e['dari']]['label']} {e['relasi'].replace('_', ' ')} {N1[e['ke']]['label']}",
                       weight=10.0, lapisan=1, source_id="lapisan1")

    def target(n):
        return l1_name(peta[n]) if n in peta else n

    for n, d in G.nodes(data=True):
        if n in peta:
            continue
        H.add_node(n, **{k: v for k, v in d.items()}, lapisan=2)

    # ---- 3. relasi
    tipe = {n: d.get("entity_type") for n, d in G.nodes(data=True)}
    for n in peta:
        tipe[n] = "struktur" if tipe[n] == "struktur" else "dasar_hukum"

    def fits(kw, tu, tv):
        dd, kk = REL[kw]["dari"], REL[kw]["ke"]
        dd, kk = dd if isinstance(dd, list) else [dd], kk if isinstance(kk, list) else [kk]
        return tu in dd and tv in kk

    for u, v, d in G.edges(data=True):
        st["relasi"] += 1
        kws = [k for k in (low(x) for x in re.split(r"[,;]|<sep>", str(d.get("keywords", "")))) if k]
        kw = next((k for k in kws if k in REL), None)
        a_, b_ = u, v
        if kw is None:
            st["kata_kunci_di_luar_skema"] += 1
            galat["kata kunci di luar skema"].append(f"{d.get('keywords')} ({u} -- {v})")
            rel = "terkait"
        else:
            st["kata_kunci_skema"] += 1
            rel = REL[kw]["relasi"]
            if fits(kw, tipe.get(u), tipe.get(v)):
                st["arah_sah"] += 1
            elif fits(kw, tipe.get(v), tipe.get(u)):
                a_, b_ = v, u
                st["arah_sah"] += 1
            else:
                st["jenis_melanggar_skema"] += 1
                galat["jenis entitas melanggar arah skema"].append(f"'{kw}': {u} [{tipe.get(u)}] -- {v} [{tipe.get(v)}]")
        attrs = dict(d, relasi=rel, lapisan=2, sumber_ke_target=f"{target(a_)} -> {target(b_)}")
        if kw and REL[kw].get("sifat"):
            attrs["sifat"] = REL[kw]["sifat"]
        H.add_edge(target(a_), target(b_), **attrs)

    # ---- 4. versi_id norma
    anchors = {target(n) for n in peta if tipe[n] == "struktur"}
    eli = {d["eli_id"]: n for n, d in H.nodes(data=True) if d.get("eli_id")}
    S = H.subgraph([y for y, dd in H.nodes(data=True) if dd.get("lapisan") == 2] + list(anchors))
    for n, d in G.nodes(data=True):
        if n in peta or tipe.get(n) == "struktur":
            continue
        hn = n
        dist = nx.single_source_shortest_path_length(S, hn, cutoff=3)
        near = [(k, x) for x, k in dist.items() if x in anchors]
        found = [x for k, x in near if k == min(k for k, _ in near)] if near else []
        if found:
            st["versi_lewat_graf"] += 1
            ids = [H.nodes[x]["eli_id"] for x in found]
        else:
            ids = chunk_anchors(d)
            st["versi_cadangan_chunk" if ids else "versi_tidak_ada"] += 1
            if not ids:
                galat["norma tanpa versi"].append(n)
        H.nodes[hn]["versi_id"] = SEP.join(sorted(set(ids)))
        H.nodes[hn]["peraturan_id"] = SEP.join(sorted({N1[i].get("sumber", "") for i in ids if i in N1} - {""}))
        if G.degree(n) == 0:
            st["norma_yatim"] += 1

    # ---- 5. turunan mengancamkan
    for n, d in list(H.nodes(data=True)):
        if d.get("lapisan") == 2 and d.get("entity_type") == "tindak_pidana":
            vs = [x for x in H.neighbors(n) if H.edges[n, x].get("relasi") == "merumuskan"]
            ss = [x for x in H.neighbors(n) if H.edges[n, x].get("relasi") == "diancam"]
            for v in vs:
                for s in ss:
                    if not H.has_edge(v, s):
                        H.add_edge(v, s, relasi="mengancamkan", keywords="mengancamkan", lapisan=2, weight=5.0,
                                   description=f"{v} mengancamkan {s} (turunan)", source_id="turunan")
                        st["turunan_mengancamkan"] += 1

    os.makedirs(a.out, exist_ok=True)
    nx.write_graphml(H, os.path.join(a.out, "gabungan.graphml"))
    embed = {"entitas": [{"nama": n, "entity_type": d.get("entity_type"), "description": d.get("description", "")}
                         for n, d in H.nodes(data=True) if d.get("lapisan") == 1],
             "catatan": "Node Lapisan 1 belum ada di vdb_entities MiniRAG; embed ulang dengan model yang sama (bge-m3)."}
    json.dump(embed, open(os.path.join(a.out, "entitas_baru_embed.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    def pct(x, y):
        return f"{x}/{y} ({100 * x / y:.0f}%)" if y else f"{x}/0"

    md_lines = [
        "# Laporan Penautan Graf Lapisan 2 ke Lapisan 1",
        "",
        "## 1. Ringkasan Topologi Graf Gabungan",
        f"- **Node MiniRAG (Lapisan 2):** {G.number_of_nodes()}",
        f"- **Relasi MiniRAG (Lapisan 2):** {G.number_of_edges()}",
        f"- **Format Nama Huruf Kecil:** `{lower_names}`",
        f"- **Total Graf Gabungan Akhir:** **{H.number_of_nodes()} node**, **{H.number_of_edges()} edge**",
        "",
        "## 2. Metrik Keberhasilan Penautan (Anchoring Metrics)",
        f"- **Struktur Cocok Jangkar:** `{pct(st['struktur_cocok'], st['struktur'])}`",
        f"- **Struktur Karangan (Dipindah ke Jangkar Chunk):** {st['struktur_karangan']}",
        f"- **Struktur Tanpa Jangkar Chunk:** {st['struktur_tanpa_jangkar']}",
        f"- **Peraturan Korpus Ditulis LLM (Dilebur ke Lapisan 1):** {st['peraturan_korpus_ditulis']}",
        f"- **Kata Kunci Relasi Sesuai Skema:** `{pct(st['kata_kunci_skema'], st['relasi'])}`",
        f"- **Arah & Jenis Relasi Sah:** `{pct(st['arah_sah'], st['kata_kunci_skema'])}`",
        f"- **Versi Norma Terhubung Lewat Graf:** {st['versi_lewat_graf']}",
        f"- **Versi Cadangan Chunk:** {st['versi_cadangan_chunk']}",
        f"- **Norma Tanpa Versi:** {st['versi_tidak_ada']}",
        f"- **Norma Yatim (Tanpa Relasi):** {st['norma_yatim']}",
        f"- **Turunan Relasi Mengancamkan:** {st['turunan_mengancamkan']}",
        "",
        "## 3. Rincian Galat & Anomali (Contoh, Maks 15 per Jenis)",
    ]
    if galat:
        for k, v in galat.items():
            md_lines.append(f"### {k} (Total: {len(v)})")
            md_lines += [f"- `{x}`" for x in v[:15]]
            md_lines.append("")
    else:
        md_lines.append("- *(Tidak ditemukan galat penautan; seluruh norma terjangkar 100%)*")
        
    rep_md_path = os.path.join(a.out, "laporan_penautan.md")
    open(rep_md_path, "w", encoding="utf-8").write("\n".join(md_lines))
    print(f"\n[SUKSES] Graf gabungan berhasil dibangun: {H.number_of_nodes()} node, {H.number_of_edges()} edge.")
    print(f"Laporan penautan tersimpan di: {rep_md_path}")


if __name__ == "__main__":
    main()
