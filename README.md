# PyMixensia-MIDI V2 (Advanced CLI Edition)

PyMixensia-MIDI adalah engine MIDI berbasis Python yang dirancang untuk pengolahan MIDI real-time tingkat lanjut. Versi V2 ini menghadirkan arsitektur **MVC (Model-View-Controller)** yang stabil, latensi sangat rendah, fitur musikalitas cerdas, dan visualisasi performa yang memukau langsung di dalam terminal.

---

## 🚀 Fitur Utama & Progress V2

### 1. Arsitektur & Keandalan (MVC)
- **MVC Refactoring**: Pemisahan total antara **Engine Inti** (`core/`) dan **Antarmuka Pengguna** (`cli/`) untuk memastikan stabilitas dan performa tinggi.
- **Auto-Connect MIDI**: Aplikasi secara otomatis mendeteksi dan menyambungkan perangkat MIDI favorit Anda (`5704PIA-DK`) saat startup.
- **Auto-Reconnect (QoL)**: Jika kabel USB terputus di tengah sesi, engine akan otomatis menyambung kembali saat kabel dicolokkan tanpa perlu restart aplikasi.
- **Settings Memory**: Menyimpan otomatis seluruh setelan global (Port, Transpose, dll) ke `settings.json`.

### 2. Fitur Musikalitas & Performa
- **Smart Chord**: Menghasilkan harmoni otomatis (Octave, Mayor, Minor, Power Chord) secara real-time dari satu nada.
- **Arpeggiator**: Pola nada Up, Down, dan Random untuk tekstur suara ritmis yang dinamis.
- **Velocity Dynamics**: Kurva sensitivitas (Soft, Hard, Fixed) untuk kontrol ekspresi yang presisi.
- **Ensemble Modes**: Pemisah suara cerdas (Top, Bottom, Middle) untuk memisahkan melodi, bass, dan iringan secara otomatis.
- **Global Sustain & Transpose**: Kontrol cepat untuk mematikan pedal sustain atau menggeser nada dasar seluruh lagu.

### 3. Visualisasi & Monitoring
- **Fullscreen ASCII Visualizer (F4)**: 5 mode animasi "Colossal" yang merespon nada piano:
    *   **Ultra Fireworks**: Ledakan kembang api blok solid yang megah.
    *   **Giant Cross Stars**: Bintang raksasa 3x3 dengan pendaran cahaya.
    *   **Rainbow Ripples**: Riak air berwarna gradasi pelangi yang dinamis.
    *   **Heavy Blocks**: Balok MIDI jatuh yang masif dan solid.
    *   **Tetris Colossal**: Jatuhan balok raksasa ala retro.
- **Enhanced MIDI Monitor (M)**: Monitor lebar (60 kolom) dengan format pesan yang mudah dibaca (Channel, Note, Velocity, CC).

---

## 🎹 Featured Song Presets

Tersedia preset yang dirancang khusus untuk lagu populer, menggunakan seluruh kekuatan fitur V2:

### 🎵 Jadi Kekasihku Saja - Keisya Levronka
*   **JadiKekasihkuSaja_Keisya**: Ballad pop manis dengan piano ekspresif dan strings megah.
*   **JadiKekasihkuSaja_Cheerful**: Versi piano klasik yang terang, ceria, dan bertenaga.
*   **JadiKekasihkuSaja_JazzPop**: Nuansa Jazz-Pop "centil" dengan arpeggio vibraphone dan slap bass.

### 🎵 City of Stars - La La Land
*   **CityOfStars_LaLaLand**: Jazz malam yang intim dengan siulan ikonik dan night strings.
*   **CityOfStars_GrandClassical**: Piano konser yang megah dan berbobot dengan resonansi dalam.
*   **CityOfStars_CityPop**: Transformasi retro 80-an dengan synth brass dan funky groove.

---

## 📘 Buku Manual: Parameter Preset Editor (F2)

Gunakan tabel ini sebagai panduan saat meracik suara di dalam Editor:

| Parameter | Deskripsi & Contoh Penggunaan |
| :--- | :--- |
| **Active Status** | `ON/OFF`. Menentukan apakah layer berbunyi. Gunakan layering untuk suara Hybrid (Piano+Strings). |
| **MIDI Channel** | `1-16`. Saluran output data MIDI. Harus sama dengan channel di VST/Synthesizer Anda. |
| **Program Change** | Memilih jenis suara (0-127). Disertai nama instrumen GM otomatis (0: Grand Piano, 40: Violin). |
| **Volume** | `0-127`. Mengatur keseimbangan (mix) antar layer suara. |
| **Transpose** | Menggeser nada per semitone. Set `+12` untuk menaikkan suara layer 1 oktav. |
| **Smart Chord** | **Off**: Nada tunggal. **Octave**: Tambah nada 1 oktav di atas. **Major/Minor**: Chord otomatis. |
| **Arpeggiator** | Memainkan nada yang ditahan secara bergantian (Up/Down/Random). Bagus untuk suara Pad. |
| **Velocity Curve** | **Soft**: Respon ringan (Ballad). **Hard**: Respon berat (Rock). **Fixed**: Velocity dikunci di 110. |
| **Hold Mode** | **Normal**: Sustain standar. **Smart**: Mencegah nota "menumpuk" berlebih (Hemat CPU). |
| **Ensemble Mode** | **Top**: Ambil nada tertinggi. **Bottom**: Ambil nada terendah. Cocok untuk memisahkan melodi. |
| **Note Range** | `Min/Max Note`. Batas area keyboard. Set `Min:60` agar layer hanya bunyi dari nada C3 ke atas. |
| **Vel Range** | `Min/Max Velocity`. Layer hanya bunyi jika ditekan dengan kekerasan tertentu. |

---

## ⚙️ Panduan Teknis & Struktur Kode

### Analisis Arsitektur
1.  **`MixensiaEngine` (core/engine.py)**: Jantung aplikasi. Menangani input MIDI, threading, logika manipulasi nota (Chord/Arp), dan status visualizer.
2.  **`ConfigManager` (core/config.py)**: Mengelola sinkronisasi antara memori RAM dan Disk (Preset `.cfg` & `settings.json`).
3.  **`draw_menu` (cli/ui.py)**: Antarmuka berbasis `curses` dengan optimasi `erase()` untuk anti-flickering dan tutorial kontekstual.

### Struktur Proyek
```text
PyMixensia-MIDI/
├── core/                   # Logika Inti (The Model)
├── cli/                    # Antarmuka Pengguna (The View/Controller)
├── presets/                # Database konfigurasi suara (.cfg)
├── mixensia_engine_extended.py # Entry Point utama
├── run_extended.sh         # Launch script (Versi Lengkap)
├── mixensia_engine.py      # Script standar (Versi Ringan)
└── settings.json           # Penyimpanan state global otomatis
```

---

## ⌨️ Daftar Shortcut Keyboard Lengkap

### Navigasi & Visual
- **[F1]**: Bantuan Lengkap | **[F2]**: Editor (Mulai Tab 1) | **[F3]**: Preset Baru | **[F4]**: Visualizer.
- **[S]**: Start/Stop Engine (Menu Utama) atau Smart Save (Editor).
- **[A]**: Save As (di Editor) | **[L]**: Daftar Preset | **[Q]**: Simpan & Keluar.
- **[UP / DN]**: Ganti Preset Cepat | **[LEFT / RIGHT]**: Ganti Mode Visualizer.

### Kontrol Performa
- **[TAB]**: Pilih Layer Aktif | **[ + ] / [ - ]**: Volume Layer | **[ [ ] / [ ] ]**: Transpose Global.
- **[O]**: Toggle Sustain | **[F]**: Toggle Fixed Velocity | **[M]**: MIDI Monitor.

---
*PyMixensia-MIDI V2 - Kecepatan CLI, Kekuatan Profesional, Visual Memukau.*
