# PyMixensia-MIDI V2 (Advanced CLI Edition)

PyMixensia-MIDI adalah engine MIDI berbasis Python yang dirancang untuk pengolahan MIDI real-time tingkat lanjut. Versi V2 ini membawa arsitektur **MVC (Model-View-Controller)** yang lebih stabil, latensi sangat rendah, dan fitur musikalitas yang cerdas untuk kebutuhan panggung (*live performance*).

---

## 🚀 Fitur Utama & Progress V2

### 1. Arsitektur & Performa
- **MVC Refactoring**: Pemisahan total antara Engine Inti (`core/`) dan Antarmuka Pengguna (`cli/`) untuk memastikan stabilitas.
- **Ultra-Low Latency**: Operasi berbasis terminal murni menjamin respon MIDI instan (sub-millisecond overhead).
- **Auto-Reconnect (QoL)**: Deteksi otomatis kabel USB MIDI. Jika terputus, engine akan otomatis menyambung kembali saat kabel dicolokkan tanpa perlu restart aplikasi.
- **Settings Memory**: Menyimpan otomatis setelan global (Port, Transpose, dll) ke `settings.json`.

### 2. Fitur Musikalitas Lanjutan
- **Smart Chord**: Menghasilkan harmoni otomatis (Octave, Mayor, Minor, Power Chord) hanya dengan menekan satu jari.
- **Arpeggiator Infrastructure**: Dukungan pola nada Up, Down, dan Random untuk tekstur suara yang ritmis.
- **Velocity Dynamics**: Kurva sensitivitas (Soft, Hard, Fixed) untuk kontrol ekspresi yang presisi.
- **Ensemble Modes**: Pemisah suara cerdas (Top, Bottom, Middle) untuk aransemen multi-layer yang rapi.

---

## 📘 Panduan Teknis & Struktur Kode

Aplikasi ini dibangun dengan prinsip modularitas tinggi agar engine musik tidak terganggu oleh aktivitas antarmuka (UI).

### Struktur Folder
```text
PyMixensia-MIDI/
├── core/                   # Logika Inti (The Model)
│   ├── engine.py           # Pemrosesan sinyal MIDI, Threading, Arp, & Logic.
│   └── config.py           # Manajemen file .cfg (Preset) & settings.json.
├── cli/                    # Antarmuka Pengguna (The View/Controller)
│   └── ui.py               # Render tampilan Curses & Penanganan Shortcut.
├── presets/                # Database konfigurasi suara (.cfg).
├── mixensia_engine_extended.py # Entry Point (Penghubung utama).
├── run_extended.sh         # Launch script (Linux).
└── settings.json           # Penyimpanan state global otomatis.
```

### Analisis Kode Inti
1. **`MixensiaEngine` (core/engine.py)**: Jantung aplikasi. Berjalan di thread terpisah. Menggunakan *callback-like architecture* untuk memproses pesan masuk tanpa memblokir input lainnya. Mendukung manipulasi nota (transposisi, chord generation) secara real-time.
2. **`ConfigManager` (core/config.py)**: Menangani sinkronisasi antara memori RAM dan penyimpanan disk. Memastikan data preset lama tetap kompatibel dengan fitur baru melalui skema *default-value injection*.
3. **`draw_menu` (cli/ui.py)**: Menggunakan library `curses` dengan optimasi `erase()` untuk menghilangkan *flickering*. Mengimplementasikan sistem *state-machine* sederhana untuk beralih antara menu Utama, Editor, dan Help.

---

## 🎹 Buku Manual: Referensi Parameter Preset Editor

Di dalam **Preset Editor (F2)**, terdapat berbagai parameter yang bisa dikonfigurasi per-layer (maksimal 16 layer):

| Parameter | Deskripsi & Contoh Penggunaan |
| :--- | :--- |
| **Active Status** | `ON/OFF`. Menentukan apakah layer berbunyi. Gunakan banyak layer untuk suara tebal (Piano + Strings). |
| **MIDI Channel** | `1-16`. Saluran output. Pastikan sama dengan instrumen di VST/Synthesizer Anda. |
| **Program Change** | Memilih jenis suara (0-127). Disertai nama instrumen GM otomatis (0: Piano, 19: Organ, dll). |
| **Volume** | `0-127`. Mengatur balance. Kecilkan Strings agar tidak menutupi kejelasan nada Piano. |
| **Transpose** | Menggeser nada dalam semitone. Set `+12` untuk menaikkan suara 1 oktav. |
| **Smart Chord** | **Off**: Nada tunggal. **Octave**: Tambah nada 1 oktav di atas. **Major/Minor**: Chord otomatis 3 nada. |
| **Arpeggiator** | Memainkan nada yang ditahan secara bergantian (Up/Down/Random). Bagus untuk Synth Pad. |
| **Velocity Curve** | **Soft**: Respon ringan (untuk Ballad). **Hard**: Respon berat (untuk Rock). **Fixed**: Velocity dikunci di 110. |
| **Hold Mode** | **Normal**: Sustain standar. **Smart**: Mencegah nota "menumpuk" terlalu banyak (hemat CPU). |
| **Ensemble Mode** | **Top**: Ambil nada tertinggi. **Bottom**: Ambil nada terendah. Cocok untuk memisahkan melodi dan bass. |
| **Note Range** | `Min/Max Note`. Batas area keyboard. Set `Min:60` agar layer hanya bunyi dari nada C3 ke atas. |
| **Vel Range** | `Min/Max Velocity`. Layer hanya bunyi jika Anda menekan tuts dengan kekerasan tertentu. |

---

## ⌨️ Daftar Shortcut Keyboard Lengkap

### Menu Utama
- **[F1]**: Bantuan | **[F2]**: Editor | **[F3]**: Preset Baru | **[Q]**: Keluar.
- **[S]**: Start/Stop Engine | **[L]**: Daftar Preset | **[UP/DN]**: Ganti Preset Cepat.
- **[TAB]**: Pilih Layer | **[+/-]**: Volume Layer | **[ [ ] / [ ] ]**: Transpose Global.
- **[O]**: Toggle Sustain | **[F]**: Toggle Fixed Velocity | **[M]**: MIDI Monitor.

### Di Dalam Editor (F2/F3)
- **[Arrows]**: Navigasi & Ubah Nilai | **[TAB]**: Ganti Layer.
- **[S]**: Save (Overwrite) | **[A]**: Save As (Nama Baru) | **[ESC]**: Keluar.

---
*PyMixensia-MIDI V2 - Kecepatan CLI, Kekuatan Profesional.*
