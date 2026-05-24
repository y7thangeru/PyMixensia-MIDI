# PyMixensia-MIDI V2 (Advanced CLI Edition)

PyMixensia-MIDI adalah engine MIDI berbasis Python yang dirancang untuk pengolahan MIDI real-time tingkat lanjut. Versi V2 ini menghadirkan arsitektur **MVC (Model-View-Controller)** yang stabil, latensi sangat rendah, fitur musikalitas cerdas, dan visualisasi performa yang memukau.

---

## 🚀 Fitur Utama & Progress V2

### 1. Arsitektur & Keandalan
- **MVC Refactoring**: Pemisahan total antara Engine Inti (`core/`) dan Antarmuka Pengguna (`cli/`) untuk stabilitas maksimal.
- **Auto-Connect MIDI**: Deteksi otomatis perangkat MIDI favorit (`5704PIA-DK`) saat startup.
- **Modern High-Contrast CLI**: Antarmuka tajam (Black on Cyan) untuk keterbacaan maksimal di panggung.
- **Auto-Reconnect (QoL)**: Engine otomatis menyambung kembali jika kabel terputus.

### 2. Fitur Musikalitas & Performa
- **Smart Chord**: Harmoni otomatis (Octave, Mayor, Minor, Power Chord).
- **Arpeggiator**: Pola nada Up, Down, dan Random untuk tekstur ritmis.
- **Velocity Dynamics**: Kurva sensitivitas (Soft, Hard, Fixed) untuk kontrol ekspresi presisi.
- **Ensemble Modes**: Pemisah suara cerdas (Top, Bottom, Middle) untuk aransemen rapi.

### 3. Visualisasi & Monitoring
- **Fullscreen ASCII Visualizer (F4)**: 5 mode animasi "Colossal" (Fireworks, Stars, Ripples, Blocks, Tetris).
- **Enhanced MIDI Monitor (M)**: Monitor lebar dengan format pesan yang mudah dibaca.

---

## 🎹 Featured Song Presets

Kami telah menyediakan berbagai preset siap pakai untuk lagu-lagu populer dengan berbagai nuansa:

### 🎵 Jadi Kekasihku Saja - Keisya Levronka
*   **JadiKekasihkuSaja_Keisya**: Ballad pop yang manis dengan piano ekspresif dan strings megah.
*   **JadiKekasihkuSaja_Cheerful**: Versi piano klasik yang terang, ceria, dan bertenaga.
*   **JadiKekasihkuSaja_JazzPop**: Nuansa Jazz-Pop "centil" dengan arpeggio vibraphone dan slap bass.

### 🎵 City of Stars - La La Land
*   **CityOfStars_LaLaLand**: Jazz malam yang intim dengan siulan ikonik dan night strings.
*   **CityOfStars_GrandClassical**: Piano konser yang megah dan berbobot dengan resonansi dalam.
*   **CityOfStars_CityPop**: Transformasi retro 80-an dengan synth brass dan funky groove.

---

## 📘 Panduan Teknis & Struktur Kode

### Struktur Proyek
```text
PyMixensia-MIDI/
├── core/                   # Logika Inti (The Model)
│   ├── engine.py           # Pemrosesan MIDI, Threading, Arp, & Visualizer.
│   └── config.py           # Manajemen file .cfg & settings.json.
├── cli/                    # Antarmuka Pengguna (The View/Controller)
│   └── ui.py               # Render UI & Animation Engine.
├── presets/                # Koleksi file konfigurasi suara (.cfg).
├── mixensia_engine_extended.py # Entry Point utama.
└── settings.json           # Penyimpanan state global otomatis.
```

---

## ⌨️ Daftar Shortcut Keyboard Lengkap

- **[F1]**: Bantuan | **[F2]**: Editor | **[F3]**: Preset Baru | **[F4]**: Visualizer.
- **[S]**: Start/Stop | **[L]**: Daftar Preset | **[Q]**: Keluar.
- **[TAB]**: Pilih Layer | **[+/-]**: Volume | **[ [ ] / [ ] ]**: Transpose Global.
- **[O]**: Toggle Sustain | **[F]**: Toggle Fixed Velocity | **[M]**: MIDI Monitor.

---
*PyMixensia-MIDI V2 - Kecepatan CLI, Kekuatan Profesional, Visual Memukau.*
