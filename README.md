# PyMixensia-MIDI V2 (Advanced CLI Edition)

PyMixensia-MIDI adalah engine MIDI berbasis Python yang dirancang untuk pengolahan MIDI real-time tingkat lanjut. Versi V2 ini menghadirkan arsitektur **MVC (Model-View-Controller)** yang stabil, latensi sangat rendah, fitur musikalitas cerdas, dan visualisasi performa yang memukau.

---

## 🚀 Fitur Utama & Progress V2

### 1. Arsitektur & Keandalan
- **MVC Refactoring**: Pemisahan total antara Engine Inti (`core/`) dan Antarmuka Pengguna (`cli/`) untuk stabilitas maksimal.
- **Auto-Connect MIDI**: Aplikasi secara otomatis mendeteksi dan menyambungkan perangkat MIDI favorit Anda saat startup.
- **Auto-Reconnect (QoL)**: Jika kabel terputus, engine akan otomatis menyambung kembali saat kabel dicolokkan tanpa perlu restart.
- **Settings Memory**: Menyimpan otomatis seluruh setelan global ke `settings.json`.

### 2. Fitur Musikalitas & Performa
- **Smart Chord**: Menghasilkan harmoni otomatis (Octave, Mayor, Minor, Power Chord) secara real-time.
- **Arpeggiator**: Pola nada Up, Down, dan Random untuk tekstur suara ritmis.
- **Velocity Dynamics**: Kurva sensitivitas (Soft, Hard, Fixed) untuk kontrol ekspresi presisi.
- **Layer Mixer**: Kontrol volume layer aktif secara instan menggunakan tombol `+`/`-`.

### 3. Visualisasi & Monitoring
- **Fullscreen ASCII Visualizer (F4)**: 5 mode animasi "Colossal" yang merespon nada piano:
    *   **Ultra Fireworks**: Ledakan kembang api blok solid.
    *   **Giant Cross Stars**: Bintang raksasa dengan pendaran cahaya.
    *   **Rainbow Ripples**: Riak air berwarna gradasi pelangi.
    *   **Heavy Blocks**: Balok MIDI jatuh yang masif.
    *   **Tetris Colossal**: Jatuhan balok raksasa ala retro.
- **Enhanced MIDI Monitor (M)**: Monitor lebar (60 kolom) dengan format pesan yang mudah dibaca manusia.

---

## 📘 Panduan Teknis & Struktur Kode

### Struktur Proyek
```text
PyMixensia-MIDI/
├── core/                   # Logika Inti (The Model)
│   ├── engine.py           # Pemrosesan MIDI, Threading, Arp, & Visualizer State.
│   └── config.py           # Manajemen file .cfg (Preset) & settings.json.
├── cli/                    # Antarmuka Pengguna (The View/Controller)
│   └── ui.py               # Render High-Contrast UI & Animation Engine.
├── presets/                # Database konfigurasi suara (.cfg).
├── mixensia_engine_extended.py # Entry Point (Penghubung utama).
└── settings.json           # Penyimpanan state global otomatis.
```

---

## 🎹 Buku Manual: Parameter Preset Editor (F2)

| Parameter | Deskripsi & Contoh Penggunaan |
| :--- | :--- |
| **Active Status** | `ON/OFF`. Gunakan layering untuk suara Hybrid (Piano+Strings). |
| **MIDI Channel** | `1-16`. Saluran output sesuai instrumen VST Anda. |
| **Program Change** | Memilih jenis suara (0-127). Disertai nama instrumen GM otomatis. |
| **Volume** | `0-127`. Mengatur keseimbangan antar layer suara. |
| **Transpose** | Geser nada per semitone. Set `+12` untuk naik 1 oktav. |
| **Smart Chord** | **Octave**: Nada lebar. **Major/Minor**: Chord otomatis 3 nada. |
| **Arpeggiator** | Memainkan nada yang ditahan secara bergantian (Up/Down/Random). |
| **Velocity Curve** | **Soft**: Ballad. **Hard**: Rock. **Fixed**: Velocity dikunci di 110. |
| **Note Range** | `Min/Max Note`. Batas area keyboard (Keyboard Splitting). |

---

## ⌨️ Daftar Shortcut Keyboard Lengkap

### Navigasi & Visual
- **[F1]**: Bantuan | **[F2]**: Editor | **[F3]**: Preset Baru | **[F4]**: Visualizer.
- **[S]**: Start/Stop Engine | **[L]**: Daftar Preset | **[Q]**: Keluar.
- **[UP/DN]**: Ganti Preset Cepat | **[LEFT/RIGHT]**: Ganti Mode Visualizer.

### Kontrol Performa
- **[TAB]**: Pilih Layer | **[+/-]**: Volume Layer | **[ [ ] / [ ] ]**: Transpose Global.
- **[O]**: Toggle Sustain | **[F]**: Toggle Fixed Velocity | **[M]**: MIDI Monitor.

---
*PyMixensia-MIDI V2 - Kecepatan CLI, Kekuatan Profesional, Visual Memukau.*
