# PyMixensia-MIDI

PyMixensia-MIDI adalah engine MIDI berbasis Python yang dirancang untuk pengolahan MIDI real-time dengan dukungan multi-layer, zona keyboard (splits), dan fitur ensemble. Aplikasi ini menggunakan antarmuka baris perintah (CLI) berbasis `curses` untuk performa yang ringan dan responsif.

## Fitur Utama

- **16 Layer Independen**: Setiap layer dapat dikonfigurasi dengan channel MIDI, program change (patch), bank (MSB/LSB), dan volume yang berbeda.
- **Keyboard Splitting**: Tentukan rentang nota (`min_note` hingga `max_note`) untuk setiap layer untuk membuat pembagian zona pada keyboard MIDI.
- **Velocity Filtering & Fading**: Kontrol sensitivitas nota berdasarkan kecepatan tekan (velocity), termasuk fitur *fade-in* dan *fade-out* velocity.
- **Ensemble Modes**:
    - `Top`: Hanya nota tertinggi yang dimainkan pada layer tersebut.
    - `Bottom`: Hanya nota terendah yang dimainkan.
    - `Middle`: Memainkan nota di antara yang tertinggi dan terendah.
- **Sustain Handling**: Mendukung pedal sustain (CC 64) dengan fitur *smart kill* untuk mencegah penumpukan nota yang tidak diinginkan.
- **Preset Management**: Simpan dan muat konfigurasi layer dengan mudah menggunakan file JSON `.cfg`.
- **Panic Button**: Matikan semua nota yang menggantung secara instan.
- **Antarmuka CLI**: Navigasi cepat menggunakan keyboard tanpa perlu mouse.

## Persyaratan Sistem

- Python 3.12+
- Library MIDI: `mido`, `python-rtmidi`
- Antarmuka: `curses` (bawaan Linux), `customtkinter` (untuk pengembangan GUI mendatang)

## Instalasi

Gunakan skrip `run.sh` untuk melakukan setup otomatis (membuat virtual environment dan menginstal dependensi):

```bash
chmod +x run.sh
./run.sh
```

## Penggunaan (Kontrol CLI)

Setelah menjalankan aplikasi, gunakan tombol berikut untuk mengoperasikannya:

- **[S]**: Start/Stop MIDI Engine.
- **[L]**: Membuka menu daftar Preset. Gunakan panah Atas/Bawah dan Enter untuk memilih.
- **[X]**: Toggle Keyboard Splits (Aktifkan/Nonaktifkan pembagian zona secara global).
- **[P]**: Panic Button (Kirim *All Notes Off* ke semua channel).
- **[1]**: Ganti Input MIDI Port.
- **[2]**: Ganti Output MIDI Port.
- **[Panah Atas/Bawah]**: Pindah preset secara cepat (Quick Switch).
- **[Q]**: Keluar dari aplikasi.

## Struktur Proyek

- `mixensia_engine.py`: Script utama yang menjalankan logika MIDI dan antarmuka CLI.
- `presets/`: Folder tempat penyimpanan file konfigurasi (.cfg).
- `run.sh`: Script pembantu untuk menjalankan aplikasi dalam virtual environment.
- `venv/`: Virtual environment Python (dibuat otomatis).

## Pengembangan Mendatang

Meskipun saat ini berbasis CLI, proyek ini sudah menyiapkan dependensi untuk antarmuka grafis (GUI) menggunakan `customtkinter`.

---
*Dibuat untuk kebutuhan pemrosesan MIDI yang fleksibel dan ringan.*
