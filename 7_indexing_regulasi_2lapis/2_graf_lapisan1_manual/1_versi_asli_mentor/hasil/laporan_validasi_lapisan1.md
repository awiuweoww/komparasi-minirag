# Laporan Validasi Graf Lapisan 1 (Silsilah Regulasi & Versi Pasal)

## 1. Ringkasan Pemrosesan Naskah
- uu/2009/45: hapus=1, sisip=15, ubah=30, versi_angka=2, versi_ayat=136, versi_pasal=55

## 2. Statistik Topologi Graf
- **Node per kelas:** `{'Peraturan': 6, 'PutusanPengadilan': 4, 'ButirAmar': 24, 'Pasal': 193, 'PeristiwaPerubahan': 46, 'VersiPasal': 188}`
- **Edge per relasi:** `{'diubah_dengan': 7, 'disesuaikan_pidananya_oleh': 11, 'memuat_pasal': 58, 'mengubah': 7, 'menetapkan_versi': 188, 'menghapus_pasal': 1, 'dicabut_dengan': 2, 'diuji_dengan': 4, 'ditetapkan_dengan': 1, 'mencabut': 2, 'menetapkan': 1, 'menyesuaikan_pidana': 11, 'menguji': 4, 'memuat_amar': 24, 'bagian_dari': 46, 'menyasar': 56, 'menghasilkan_versi': 188, 'versi_dari': 188, 'bagian_dari_pasal': 135, 'bagian_dari_versi': 133, 'merujuk': 124}`
- **Pasal berstatus `perlu_cek` (dirujuk/disasar, teks versinya belum di-index):** 4

## 3. Catatan Validasi & Integritas Silsilah
- [ ] butir tanpa nomor dianggap angka 29: Ketentuan Pasal 69 diubah sehingga Pasal 69 berbunyi sebagai berikut:
- [ ] uu/2009/45/pasal/I/angka/41: judul Pasal 94A tidak ditemukan; teks dianggap milik Pasal 94A
- [ ] uu/2026/1: 10 versi pidana yang berlaku pada 2026-01-02 ditandai disesuaikan (perlu_cek)
