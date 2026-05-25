# PyMixensia-MIDI: Evolusi Engine MIDI CLI (V1 - V3)

PyMixensia-MIDI adalah engine MIDI berbasis Python yang dirancang untuk pengolahan MIDI real-time tingkat lanjut. Proyek ini berevolusi dari skrip sederhana menjadi workstation MIDI berbasis terminal yang sangat powerful.

---

## 💎 PyMixensia-MIDI V3: The Asciimatics Edition (LATEST)

Versi V3 adalah lompatan besar dalam sisi visual dan stabilitas UI, menggantikan `curses` standar dengan library **Asciimatics**.

### ✨ Fitur Unggulan V3
- **Modern UI Framework**: Menggunakan sistem widget (Frame, Layout, Dropdown, Checkbox) yang jauh lebih stabil dan interaktif.
- **Dynamic Manual Guide**: Editor F2 kini dilengkapi dengan panel bantuan "Live". Setiap Anda menyorot parameter, penjelasan lengkap mengenai fungsi dan setiap opsinya akan muncul secara otomatis.
- **Hybrid Visualizer (F4)**: Animasi yang lebih halus dengan dukungan 5 mode asli (Fireworks, Stars, Ripples, Falling, Tetris) ditambah **Demo Mode [D]** untuk melihat animasi tanpa perangkat MIDI.
- **Robust Engine**: Penanganan error tingkat hardware (ALSA resource busy) yang mencegah terminal *hang* atau membeku.

### 🛠️ Problem & Solusi di V3
Selama pengembangan V3, kami menghadapi beberapa tantangan teknis:
1.  **IndexError: No live widgets**: Terjadi karena sistem layout mencoba memberi fokus pada label statis. **Fix**: Re-arsitektur layout menjadi sistem kolom yang stabil dan penempatan jangkar fokus yang tepat.
2.  **Circular Update Bug**: Saat berpindah layer, data lama menimpa data baru. **Fix**: Implementasi `_updating` flag untuk memutus loop event UI.
3.  **ALSA Hang**: Terminal membeku saat MIDI port sibuk. **Fix**: Implementasi *clean-up* otomatis dan *exception handling* pada level engine port opening.

### 🚀 Menjalankan V3
```bash
./run_v3.sh
```

---

## 🚀 PyMixensia-MIDI V2: Advanced CLI Edition (Stable Legacy)

V2 memperkenalkan arsitektur **MVC (Model-View-Controller)** dan fitur musikalitas yang sangat lengkap.

### Fitur Utama V2
- **Arsitektur Terpisah**: Pemisahan total antara `core/engine.py` (logika) dan `cli/ui.py` (tampilan).
- **Smart Musicality**:
    - **Smart Chord**: Harmoni otomatis (Octave, Mayor, Minor, Power Chord).
    - **Ensemble Modes**: Pemisah suara otomatis (Top/Bottom/Middle) untuk melodi dan bass.
    - **Velocity Dynamics**: Kurva respon sentuhan (Soft, Hard, Fixed).
- **Preset Management**: Sistem load/save `.cfg` yang sangat cepat dengan dukungan 16 layer suara.
- **Auto-Reconnect**: Deteksi otomatis kabel MIDI yang terputus di tengah sesi.

### 📘 Buku Manual: Parameter Preset Editor
| Parameter | Deskripsi |
| :--- | :--- |
| **STATUS** | Aktifkan/matikan layer (ON/OFF). |
| **CHANNEL** | Saluran MIDI output (1-16). |
| **PROGRAM** | Pilih suara instrumen GM (0-127). |
| **CHORD** | Mode harmoni: Single, Octave, Major, Minor, Power. |
| **ARP** | Arpeggiator: Up, Down, Random. |
| **ENSEMBLE** | Splitting cerdas: Top (Melodi), Bottom (Bass). |
| **RANGE** | Batas wilayah nada (Min Note - Max Note). |

---

## 📜 PyMixensia-MIDI V1: The Genesis

Versi awal yang membuktikan bahwa Python mampu menangani MIDI dengan latensi sangat rendah langsung di CLI.

### Karakteristik V1
- **Monolithic Script**: Seluruh kode berada dalam satu file `mixensia_engine.py`.
- **Dasar Visual**: Menggunakan karakter ASCII sederhana untuk memantau aktivitas nada.
- **Fokus Utama**: Latensi rendah dan kompatibilitas dengan VST eksternal.
- **Legacy**: Menjadi fondasi algoritma pemrosesan MIDI yang digunakan hingga V3.

---

## 🎹 Featured Song Presets
Preset yang dirancang khusus menggunakan seluruh kekuatan engine PyMixensia:
- **Jadi Kekasihku Saja (Keisya)**: Piano ekspresif + Megah Strings.
- **City of Stars (La La Land)**: Jazz intim dengan simulasi siulan dan night strings.

---

## ⌨️ Daftar Shortcut Global (V2 & V3)
- **[F1]**: Bantuan Lengkap / Shortcut List.
- **[F2]**: Buka/Tutup Preset Editor.
- **[F4]**: Buka/Tutup Visualizer Animasi.
- **[S]**: Start/Stop Engine MIDI.
- **[L]**: Memuat Daftar Preset.
- **[P]**: Panic Button (Matikan semua nada).
- **[M]**: MIDI Monitor (Log data real-time).
- **[D]**: Demo Mode (Hanya di Visualizer F4).
- **[[] / []]**: Master Transpose (Naik/Turun nada dasar).
- **[Q]**: Keluar dari Aplikasi.

---
*PyMixensia-MIDI - Dari skrip sederhana hingga workstation MIDI CLI profesional.*
