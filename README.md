# PyMixensia-MIDI V2 (Advanced CLI Edition)

PyMixensia-MIDI adalah engine MIDI berbasis Python yang dirancang untuk pengolahan MIDI real-time tingkat lanjut. Versi V2 ini membawa arsitektur **MVC (Model-View-Controller)** yang lebih stabil, latensi sangat rendah, dan fitur musikalitas yang cerdas untuk kebutuhan panggung (*live performance*).

## 🚀 Fitur Utama & Progress V2

### 1. Arsitektur & Performa
- **MVC Refactoring**: Pemisahan total antara Engine Inti (`core/`) dan Antarmuka Pengguna (`cli/`) untuk memastikan stabilitas dan kemudahan pengembangan masa depan.
- **Ultra-Low Latency**: Tetap berbasis CLI (Terminal) untuk menjamin respon MIDI instan tanpa beban grafis yang berat.
- **Auto-Reconnect (QoL)**: Deteksi otomatis kabel USB MIDI. Jika terputus, engine akan otomatis menyambung kembali saat kabel dicolokkan tanpa perlu restart aplikasi.
- **Settings Memory**: Menyimpan otomatis setelan global (Port, Transpose, dll) ke `settings.json`.

### 2. Fitur Musikalitas Lanjutan
- **16 Layer Independen**: Setiap layer dapat memiliki instrumen, channel, dan zonanya sendiri.
- **Smart Chord**: Menghasilkan harmoni otomatis (Octave, Mayor, Minor, Power Chord) hanya dengan menekan satu jari.
- **Arpeggiator Infrastructure**: Dukungan pola nada Up, Down, dan Random untuk tekstur suara yang ritmis.
- **Velocity Dynamics**: Kurva sensitivitas (Soft, Hard, Fixed) untuk kontrol ekspresi yang presisi.
- **Ensemble Modes**: Pemisah suara cerdas (Top, Bottom, Middle) untuk aransemen multi-layer yang rapi.

### 3. Preset Editor & Tutorial Terintegrasi
- **Live Editor (F2)**: Edit seluruh parameter 16 layer secara visual dan real-time.
- **Interactive Tutorial**: Muncul baris panduan dinamis di dalam editor yang menjelaskan fungsi setiap opsi secara mendetail saat kursor digerakkan.
- **Smart Instrument Naming**: Nama layer secara otomatis sinkron dengan nama instrumen General MIDI (GM) yang dipilih.
- **Smart Save (S/A)**: Sistem penyimpanan cerdas (Overwrite vs Save As).

## ⌨️ Panduan Keyboard Shortcuts

### Navigasi Utama
- **[F1]**: Menu Bantuan Lengkap.
- **[F2]**: Buka/Tutup Preset Editor (Dimulai dari Layer 1).
- **[F3]**: Buat Preset Baru (Reset total 16 layer ke kondisi bersih).
- **[S]**: Start/Stop Engine (di Menu Utama) atau Save (di Editor).
- **[L]**: Daftar Preset.
- **[UP / DN]**: Ganti preset secara instan.
- **[Q]**: Simpan semua setelan dan keluar.

### Performa Real-time
- **[TAB]**: Pilih layer aktif untuk diubah volumenya.
- **[ + ] / [ - ]**: Naik/Turun volume layer aktif secara instan.
- **[ [ ] / [ ] ]**: Master Transpose Global (Naik/Turun Nada).
- **[O]**: Aktifkan/Matikan Pedal Sustain secara global.
- **[F]**: Aktifkan/Matikan Global Fixed Velocity (110).
- **[M]**: Overlay MIDI Monitor (Melihat data masuk secara real-time).
- **[P]**: PANIC! (Mematikan semua suara yang menggantung).

## 📁 Struktur Proyek
- `core/engine.py`: Logika inti pemrosesan MIDI & Threading.
- `core/config.py`: Pengelola preset (.cfg) dan setelan global (.json).
- `cli/ui.py`: Antarmuka terminal berbasis `curses` dengan tutorial dinamis.
- `mixensia_engine_extended.py`: Entry point aplikasi V2.
- `presets/`: Koleksi file konfigurasi suara.
- `run_extended.sh`: Script peluncur utama.

---
*PyMixensia-MIDI V2 - Dibuat untuk kecepatan, ketahanan, dan kreativitas musisi digital.*
