#!/usr/bin/env python3
"""
02_translate_gpt.py - Penerjemah Dokumen Hukum UNCLOS 1982 Menggunakan GPT (gpt-5.4)
====================================================================================
Menerjemahkan naskah utuh hasil ekstraksi MinerU (output.md) dari bahasa Inggris
ke bahasa Indonesia dengan standar terminologi hukum maritim resmi UU No. 17 Tahun 1985.

Fitur Unggulan:
1. Segmentasi Cerdas: Memecah naskah per Pasal (Article), Bab (Part), dan Seksi (Section).
2. Checkpoint & Resume: Setiap pasal yang berhasil diterjemahkan langsung dicatat ke cache JSON.
   Jika job terhenti atau timeout di HPC, proses akan melanjutkan persis dari pasal terakhir.
3. Asynchronous Concurrency: Menggunakan httpx async pool dengan pembatas rate-limit adaptif.
4. Robust Retry Backoff: Otomatis menangani 429 Rate Limit atau transient network error.

Target Masukan: hasilmineru/output.md
Target Keluaran:
- indonesiaversion/default/unclos_ID_default.md
- indonesiaversion/default/unclos_translation_cache.json
- indonesiaversion/default/unclos_ID_summary.json
"""

import os
import sys
import re
import json
import time
import asyncio
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Load .env manual / via python-dotenv
def load_env(env_path: Path):
    if not env_path.exists():
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k not in os.environ:
                os.environ[k] = v

BASE_DIR = Path(__file__).resolve().parent.parent
load_env(BASE_DIR / ".env")

try:
    import httpx
except ImportError:
    print("[ERROR] Modul 'httpx' belum terpasang. Jalankan: pip install httpx")
    sys.exit(1)

# Konfigurasi OpenAI
OPENAI_API_KEY = re.sub(r"\s+", "", os.getenv("OPENAI_API_KEY", "")).strip()
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4").strip()
TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.0"))
MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "8192"))
CONCURRENCY = int(os.getenv("REQUEST_CONCURRENCY", "4"))
TIMEOUT_SEC = float(os.getenv("TIMEOUT_SECONDS", "180.0"))
MAX_RETRIES = int(os.getenv("RETRY_ATTEMPTS", "5"))

SYSTEM_PROMPT = """Anda adalah penerjemah hukum resmi spesialis Hukum Laut Internasional (UNCLOS 1982 / Konvensi PBB tentang Hukum Laut).
Tugas Anda adalah menerjemahkan naskah konvensi bahasa Inggris berikut ke bahasa Indonesia secara presisi, formal, dan mengikat, sesuai standar terminologi resmi Undang-Undang Republik Indonesia Nomor 17 Tahun 1985 (tentang Pengesahan UNCLOS 1982).

PEDOMAN BAKU TERMINOLOGI HUKUM LAUT INDONESIA:
- United Nations Convention on the Law of the Sea -> Konvensi Perserikatan Bangsa-Bangsa tentang Hukum Laut
- Preamble -> Mukadimah
- Part -> Bagian
- Section -> Seksi
- Article -> Pasal
- Paragraph -> Ayat (misal: 1. -> (1), 2. -> (2) jika dalam pasal)
- Subparagraph -> Huruf
- Territorial Sea -> Laut Teritorial
- Contiguous Zone -> Zona Tambahan
- Exclusive Economic Zone (EEZ) -> Zona Ekonomi Eksklusif (ZEE)
- Continental Shelf -> Landas Kontinen
- High Seas -> Laut Lepas
- The Area -> Kawasan
- International Seabed Authority -> Otoritas Dasar Laut Internasional
- Archipelagic State -> Negara Kepulauan
- Archipelagic Waters -> Perairan Kepulauan
- Internal Waters -> Perairan Pedalaman
- Innocent Passage -> Hak Lintas Damai
- Transit Passage -> Hak Lintas Transit
- Archipelagic Sea Lanes Passage -> Hak Lintas Alur Laut Kepulauan
- Marine Scientific Research -> Riset Ilmiah Kelautan
- Living Resources -> Sumber Daya Hayati
- Non-living Resources -> Sumber Daya Non-Hayati
- Land-locked States -> Negara Tanpa Pantai
- Geographically Disadvantaged States -> Negara yang Secara Geografis Tidak Beruntung
- Enterprise -> Perusahaan (organ operasional Otoritas Dasar Laut)
- Tribunal / Court -> Mahkamah / Pengadilan

ATURAN STRUKTUR & GAYA BAHASA:
1. Pertahankan format Markdown (#, ##, ###, penomoran ayat, poin a/b/c, indentasi) persis seperti naskah aslinya.
2. Jangan menambahkan pembuka/penutup seperti "Berikut terjemahannya:". Keluarkan HANYA teks hasil terjemahan.
3. Terjemahkan dengan gaya bahasa perundang-undangan Indonesia yang baku, cermat, dan tidak ambigu."""


def segment_unclos_markdown(md_text: str) -> List[Dict[str, Any]]:
    """
    Memecah naskah UNCLOS Markdown menjadi unit-unit logis:
    - Preamble
    - Part / Section Heading
    - Article (Pasal) per pasal
    - Annexes (Lampiran)
    """
    lines = md_text.splitlines()
    segments = []
    
    current_title = "Preamble"
    current_type = "preamble"
    current_lines = []
    
    # Pola Heading
    re_part = re.compile(r'^\s*(?:#+\s*)?(?:PART|BAGIAN)\s+[IVXLCDM0-9]+', re.IGNORECASE)
    re_section = re.compile(r'^\s*(?:#+\s*)?(?:SECTION|SEKSI)\s+[IVXLCDM0-9]+', re.IGNORECASE)
    re_article = re.compile(r'^\s*(?:#+\s*)?(?:Article|Pasal)\s+(\d+[a-zA-Z]?)', re.IGNORECASE)
    re_annex = re.compile(r'^\s*(?:#+\s*)?(?:ANNEX|LAMPIRAN)\s+[IVXLCDM0-9]+', re.IGNORECASE)

    def flush_segment():
        nonlocal current_lines, current_title, current_type
        text = "\n".join(current_lines).strip()
        if text:
            segments.append({
                "id": f"seg_{len(segments):04d}",
                "title": current_title,
                "type": current_type,
                "text": text,
                "lines_count": len(current_lines),
                "words": len(text.split())
            })
        current_lines = []

    for line in lines:
        m_art = re_article.match(line)
        m_part = re_part.match(line)
        m_sec = re_section.match(line)
        m_annex = re_annex.match(line)

        if m_art:
            flush_segment()
            current_title = f"Article {m_art.group(1)}"
            current_type = "article"
            current_lines.append(line)
        elif m_part or m_sec or m_annex:
            flush_segment()
            current_title = line.strip("# *_-")
            current_type = "heading"
            current_lines.append(line)
        else:
            current_lines.append(line)

    flush_segment()

    # Jika ukuran segmen terlalu besar (> 1200 kata), pecah lagi berdasarkan sub-paragraf
    final_segments = []
    for seg in segments:
        words = seg["words"]
        if words > 1500 and seg["type"] == "article":
            # Pecah menjadi sub-bagian ayat
            sub_lines = seg["text"].split("\n\n")
            sub_buf = []
            sub_idx = 1
            for p in sub_lines:
                sub_buf.append(p)
                if len("\n\n".join(sub_buf).split()) > 1000:
                    final_segments.append({
                        "id": f"{seg['id']}_p{sub_idx}",
                        "title": f"{seg['title']} (Bagian {sub_idx})",
                        "type": seg["type"],
                        "text": "\n\n".join(sub_buf).strip(),
                        "words": len("\n\n".join(sub_buf).split())
                    })
                    sub_idx += 1
                    sub_buf = []
            if sub_buf:
                final_segments.append({
                    "id": f"{seg['id']}_p{sub_idx}",
                    "title": f"{seg['title']} (Bagian {sub_idx})",
                    "type": seg["type"],
                    "text": "\n\n".join(sub_buf).strip(),
                    "words": len("\n\n".join(sub_buf).split())
                })
        else:
            final_segments.append(seg)

    return final_segments


async def translate_single_segment(
    client: httpx.AsyncClient,
    segment: Dict[str, Any],
    semaphore: asyncio.Semaphore,
    cache: Dict[str, str],
    cache_lock: asyncio.Lock
) -> str:
    seg_id = segment["id"]

    # 1. Cek dari Cache
    async with cache_lock:
        if seg_id in cache and cache[seg_id].strip():
            return cache[seg_id]

    user_content = f"Terjemahkan segmen hukum berikut ke bahasa Indonesia:\n\n{segment['text']}"

    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ],
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS
    }
    # Adaptasi parameter model generasi baru (o1/o3/gpt-5) yang mewajibkan max_completion_tokens
    if any(x in OPENAI_MODEL.lower() for x in ["o1", "o3", "gpt-5"]):
        payload.pop("max_tokens", None)
        payload.pop("temperature", None)
        payload["max_completion_tokens"] = MAX_TOKENS

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    url = f"{OPENAI_BASE_URL}/chat/completions"

    async with semaphore:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                t0 = time.time()
                resp = await client.post(url, json=payload, headers=headers, timeout=TIMEOUT_SEC)
                if resp.status_code == 200:
                    data = resp.json()
                    translated_text = data["choices"][0]["message"]["content"].strip()

                    # Simpan ke Cache
                    async with cache_lock:
                        cache[seg_id] = translated_text

                    dur = time.time() - t0
                    print(f"[OK] [{seg_id}] {segment['title']} diterjemahkan ({segment['words']} kata, {dur:.2f}s)", flush=True)
                    return translated_text

                elif resp.status_code == 401:
                    print(f"[FATAL 401] [{seg_id}] API Key OpenAI TIDAK VALID: {resp.text}", flush=True)
                    raise PermissionError(f"HTTP 401 Unauthorized: API Key tidak valid. {resp.text}")
                elif resp.status_code == 429:
                    wait_sec = attempt * 5
                    print(f"[RATE LIMIT 429] [{seg_id}] Menunggu {wait_sec}s sebelum coba lagi (Attempt {attempt}/{MAX_RETRIES})...", flush=True)
                    await asyncio.sleep(wait_sec)
                elif resp.status_code >= 500:
                    wait_sec = attempt * 3
                    print(f"[SERVER ERROR {resp.status_code}] [{seg_id}] Menunggu {wait_sec}s...", flush=True)
                    await asyncio.sleep(wait_sec)
                else:
                    err_msg = resp.text
                    print(f"[ERROR {resp.status_code}] [{seg_id}]: {err_msg[:200]}", flush=True)
                    if attempt == MAX_RETRIES:
                        raise RuntimeError(f"Gagal menerjemahkan {seg_id}: HTTP {resp.status_code} - {err_msg}")
                    await asyncio.sleep(3)

            except PermissionError:
                raise
            except Exception as e:
                if attempt == MAX_RETRIES:
                    print(f"[FAILED] [{seg_id}] Melebihi batas percobaan: {e}", flush=True)
                    raise e
                await asyncio.sleep(attempt * 2)

    return ""


async def run_translation_pipeline(
    input_md_path: Path,
    output_dir: Path,
    cache_path: Path
):
    global OPENAI_MODEL
    if not input_md_path.exists():
        raise FileNotFoundError(f"Berkas masukan Markdown tidak ditemukan di: {input_md_path}")

    if not OPENAI_API_KEY or OPENAI_API_KEY == "your_openai_api_key_here":
        raise ValueError(
            "OPENAI_API_KEY belum disetel! Harap edit berkas 8_unclos/.env dan masukkan API key Anda."
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70, flush=True)
    print("PENERJEMAHAN UNCLOS 1982: BAHASA INGGRIS -> BAHASA INDONESIA", flush=True)
    print(f"Model LLM        : {OPENAI_MODEL}", flush=True)
    print(f"Base URL         : {OPENAI_BASE_URL}", flush=True)
    print(f"Berkas Masukan   : {input_md_path}", flush=True)
    print(f"Direktori Target : {output_dir}", flush=True)
    print(f"Berkas Cache     : {cache_path}", flush=True)
    print(f"Concurrency      : {CONCURRENCY} worker", flush=True)
    print("=" * 70, flush=True)

    # 0. Pre-flight Check Koneksi & API Key
    print(f"\n[VALIDASI] Menguji koneksi dan autentikasi API Key ke {OPENAI_BASE_URL}...", flush=True)
    async with httpx.AsyncClient(timeout=15.0) as test_client:
        test_payload = {
            "model": OPENAI_MODEL,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 5
        }
        if any(x in OPENAI_MODEL.lower() for x in ["o1", "o3", "gpt-5"]):
            test_payload.pop("max_tokens", None)
            test_payload["max_completion_tokens"] = 5

        try:
            test_resp = await test_client.post(
                f"{OPENAI_BASE_URL}/chat/completions",
                json=test_payload,
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
            )
            if test_resp.status_code == 401:
                print("\n" + "!" * 70, flush=True)
                print("[FATAL ERROR] API KEY OPENAI TIDAK VALID (HTTP 401 Unauthorized)!", flush=True)
                print("OpenAI Error:", test_resp.text, flush=True)
                print("\nLangkah Solusi:", flush=True)
                print("1. Buka https://platform.openai.com/api-keys", flush=True)
                print("2. Buat Secret Key baru (Create new secret key)", flush=True)
                print("3. Tempelkan ke berkas: 8_unclos/.env", flush=True)
                print("4. Jalankan ulang sbatch 02_run_translate.sbatch", flush=True)
                print("!" * 70 + "\n", flush=True)
                sys.exit(1)
            elif test_resp.status_code == 404:
                print(f"[PERINGATAN] Model '{OPENAI_MODEL}' tidak ditemukan (HTTP 404).", flush=True)
                print(f"             Mencoba fallback otomatis ke 'gpt-4o'...", flush=True)
                OPENAI_MODEL = "gpt-4o"
            elif test_resp.status_code == 200:
                print(f"[OK] Autentikasi API Key berhasil & Model '{OPENAI_MODEL}' aktif!\n", flush=True)
            else:
                print(f"[INFO] Pre-flight mengembalikan HTTP {test_resp.status_code}: {test_resp.text[:150]}\n", flush=True)
        except Exception as e:
            print(f"[WARNING] Pre-flight ping network warning: {e}\n", flush=True)

    # 1. Baca Naskah & Segmentasi
    raw_text = input_md_path.read_text(encoding="utf-8")
    segments = segment_unclos_markdown(raw_text)
    total_segments = len(segments)
    total_words = sum(s["words"] for s in segments)

    print(f"[SEGMENTASI] Berhasil memecah naskah menjadi {total_segments} unit segmen/pasal (~{total_words} kata).")

    # 2. Muat Cache Eksisting (jika ada)
    cache = {}
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
            print(f"[RESUME] Menemukan cache sebelumnya: {len(cache)}/{total_segments} segmen telah selesai.")
        except Exception:
            cache = {}

    semaphore = asyncio.Semaphore(CONCURRENCY)
    cache_lock = asyncio.Lock()

    # Fungsi autosave cache periodik
    async def periodic_cache_saver():
        while True:
            await asyncio.sleep(10)
            async with cache_lock:
                cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")

    saver_task = asyncio.create_task(periodic_cache_saver())

    # 3. Jalankan Penerjemahan Async
    async with httpx.AsyncClient(limits=httpx.Limits(max_connections=20, max_keepalive_connections=10)) as client:
        tasks = [
            translate_single_segment(client, seg, semaphore, cache, cache_lock)
            for seg in segments
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    saver_task.cancel()
    # Simpan cache final
    cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")

    # 4. Evaluasi Hasil & Gabungkan Naskah Utuh
    failed_segments = []
    ordered_translated_texts = []

    for seg in segments:
        sid = seg["id"]
        res = cache.get(sid, "")
        if not res:
            failed_segments.append(seg)
        else:
            ordered_translated_texts.append(res)

    if failed_segments:
        print(f"\n[PERINGATAN] Terdapat {len(failed_segments)} segmen yang gagal diterjemahkan.")
        print("Anda dapat menjalankan ulang skrip ini untuk menyelesaikan segmen yang tersisa.")
    else:
        print(f"\n[SUKSES] 100% dari {total_segments} segmen berhasil diterjemahkan!")

    # 5. Tulis Berkas Utuh unclos_ID_default.md
    out_md_file = output_dir / "unclos_ID_default.md"
    final_full_text = "\n\n".join(ordered_translated_texts)
    
    header_info = (
        "# KONVENSI PERSERIKATAN BANGSA-BANGSA TENTANG HUKUM LAUT (UNCLOS 1982)\n"
        "> **Terjemahan Resmi Bahasa Indonesia (Standar UU No. 17 Tahun 1985)**  \n"
        f"> **Model Generator:** {OPENAI_MODEL} | **Waktu Ekstraksi:** {time.strftime('%Y-%m-%d %H:%M:%S')}  \n\n---\n\n"
    )
    out_md_file.write_text(header_info + final_full_text, encoding="utf-8")

    summary = {
        "doc_id": "unclos_1982",
        "doc_title": "Konvensi Perserikatan Bangsa-Bangsa tentang Hukum Laut (UNCLOS 1982)",
        "source_en_file": str(input_md_path),
        "output_id_file": str(out_md_file),
        "model_used": OPENAI_MODEL,
        "total_segments": total_segments,
        "completed_segments": len(ordered_translated_texts),
        "failed_segments_count": len(failed_segments),
        "total_words_original": total_words,
        "total_words_translated": len(final_full_text.split()),
        "waktu_selesai": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    summary_file = output_dir / "unclos_ID_summary.json"
    summary_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "=" * 70)
    print(f"BERKAS TERJEMAHAN DEFAULT TERSIMPAN DI:")
    print(f"  1. Naskah Utuh Markdown : {out_md_file}")
    print(f"  2. Cache Checkpoint     : {cache_path}")
    print(f"  3. Ringkasan Statistik  : {summary_file}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Penerjemahan UNCLOS 1982 Menggunakan GPT")
    parser.add_argument("--input", type=str, default=None, help="Path berkas output.md hasil MinerU")
    parser.add_argument("--out", type=str, default=None, help="Direktori hasil terjemahan default")
    parser.add_argument("--cache", type=str, default=None, help="Path berkas cache checkpoint")
    args = parser.parse_args()

    input_md = Path(args.input) if args.input else BASE_DIR / "hasilmineru" / "output.md"
    out_dir = Path(args.out) if args.out else BASE_DIR / "indonesiaversion" / "default"
    cache_f = Path(args.cache) if args.cache else out_dir / "unclos_translation_cache.json"

    asyncio.run(run_translation_pipeline(input_md, out_dir, cache_f))


if __name__ == "__main__":
    main()

