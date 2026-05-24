# PyMixensia-MIDI (Extended Edition)

PyMixensia-MIDI adalah engine MIDI berbasis Python yang dirancang untuk pengolahan MIDI real-time tingkat lanjut. Proyek ini berfokus pada fleksibilitas live performance dengan dukungan multi-layer, zona keyboard (splits), kurva ekspresi, dan manajemen preset yang intuitif langsung dari terminal.

## Fitur Utama

- **16 Layer Independen**: Konfigurasi mandiri untuk channel MIDI, patch instrumen (GM), volume, dan transpose.
- **Preset Editor (F2)**: Edit seluruh parameter 16 layer secara real-time melalui antarmuka visual tanpa perlu menyentuh file JSON.
- **Smart Instrument Naming**: Nama layer secara otomatis mengikuti instrumen MIDI yang dipilih.
- **Velocity Dynamics**:
    - **Velocity Curves**: Pilihan kurva `soft`, `hard`, atau `fixed` untuk menyesuaikan respon ekspresi tuts.
    - **Global Fixed Velocity (F)**: Paksa semua output ke velocity tetap (110) secara instan.
- **Live Performance Controls**:
    - **Master Transpose**: Menaikkan/menurunkan nada seluruh engine secara global.
    - **Sustain Toggle (O)**: Mengaktifkan atau menonaktifkan deteksi pedal sustain (CC 64).
    - **Layer Mixer**: Pilih layer aktif dengan `TAB` dan sesuaikan volume dengan `+`/`-`.
- **MIDI Monitoring (M)**: Overlay monitor pesan MIDI yang masuk untuk kemudahan debugging.
- **Panic Protection**: Tombol Panic instan dan fitur Auto-Panic saat engine dihentikan.

## Instalasi

Aplikasi ini berjalan di Linux (optimal di ThinkPad X131e) menggunakan virtual environment untuk memastikan kestabilan dependensi.

1. Beri izin eksekusi pada skrip run:
   ```bash
   chmod +x run.sh run_extended.sh
   ```
2. Jalankan versi Extended (Sangat Direkomendasikan):
   ```bash
   ./run_extended.sh
   ```

## Panduan Keyboard Shortcuts

### Navigasi Utama
- **[F1]**: Membuka/Menutup menu Bantuan.
- **[S]**: Start atau Stop MIDI Engine.
- **[L]**: Membuka daftar Preset yang tersimpan.
- **[Q]**: Keluar dari aplikasi.
- **[UP / DN]**: Ganti preset secara cepat (Quick Cycle).

### Kontrol Performa
- **[TAB]**: Memilih layer aktif (ditandai dengan `>>`).
- **[ + ] / [ - ]**: Mengatur volume layer yang sedang dipilih.
- **[ [ ] / [ ] ]**: Master Transpose (Naik/Turun nada secara global).
- **[O]**: Aktifkan/Matikan fungsi Pedal Sustain.
- **[F]**: Aktifkan/Matikan Global Fixed Velocity (Semua nada dipaksa ke velocity 110).
- **[X]**: Aktifkan/Matikan Keyboard Splits (Zona nada).
- **[M]**: Tampilkan/Sembunyikan MIDI Monitor.
- **[P]**: PANIC! (Kirim *All Notes Off* ke semua channel).

### Management Preset & Editor
- **[F2]**: Masuk ke Preset Editor (Selalu mulai dari Layer 1).
- **[F3]**: Buat Preset Baru (Reset semua layer ke kondisi bersih).
- **Di dalam Editor**:
    - **[Arrows]**: Navigasi parameter dan ubah nilai.
    - **[TAB]**: Pindah ke layer berikutnya.
    - **[S]**: **Smart Save** (Menimpa file jika sedang mengedit, atau minta nama baru jika preset baru).
    - **[A]**: **Save As** (Selalu minta nama baru).
    - **[ESC / F2]**: Tutup Editor.

## Struktur Proyek

- `mixensia_engine_extended.py`: Logic engine utama dengan fitur lengkap.
- `presets/`: Folder penyimpanan konfigurasi `.cfg` (format JSON).
- `run_extended.sh`: Script peluncur otomatis versi Extended.
- `mixensia_engine.py`: Versi standar (legacy).
- `README.md`: Dokumentasi proyek.

---
*Dibuat untuk musisi yang membutuhkan kontrol MIDI yang cepat, ringan, dan powerful.*
