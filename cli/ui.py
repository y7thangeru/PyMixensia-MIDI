import curses
import time
import os
import mido

def draw_menu(stdscr, engine, config):
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    
    curses.curs_set(0)
    stdscr.nodelay(1)
    
    in_ports = mido.get_input_names()
    out_ports = mido.get_output_names()
    in_idx = 0
    out_idx = 0
    
    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()

        title = " PyMixensia MIDI Engine (V2 MVC) "
        stdscr.attron(curses.A_REVERSE)
        stdscr.addstr(0, (w//2)-(len(title)//2), title)
        stdscr.attroff(curses.A_REVERSE)

        status = "RUNNING" if engine.running else "STOPPED"
        color = curses.color_pair(1 if engine.running else 2) | curses.A_BOLD
        stdscr.addstr(2, 2, f"Status: {status}", color)
        stdscr.addstr(2, 25, f"Preset: {engine.current_preset_name}", curses.color_pair(3))

        split_status = "OFF (Full Keyboard)" if engine.disable_splits else "ON (Use Zones)"
        stdscr.addstr(3, 2, f"Keyboard Splits: {split_status}", curses.color_pair(4) if engine.disable_splits else curses.A_NORMAL)

        ap_status = "ON" if engine.auto_panic else "OFF"
        stdscr.addstr(4, 2, f"Auto-Panic: {ap_status}", curses.color_pair(1 if engine.auto_panic else 2))
        
        fv_status = "ON (110)" if engine.global_fixed_vel else "OFF"
        stdscr.addstr(4, 25, f"Global Fixed Vel: {fv_status}", curses.color_pair(1 if engine.global_fixed_vel else 0))

        sust_status = "ENABLED" if engine.sustain_enabled else "DISABLED"
        stdscr.addstr(5, 2, f"Pedal Sustain: {sust_status}", curses.color_pair(1 if engine.sustain_enabled else 2))
        
        stdscr.addstr(5, 25, f"Master Transpose: {engine.master_transpose:+d}", curses.color_pair(4) if engine.master_transpose != 0 else 0)

        stdscr.addstr(6, 2, "1. Input Port:  " + (in_ports[in_idx] if in_ports else "N/A"))
        stdscr.addstr(7, 2, "2. Output Port: " + (out_ports[out_idx] if out_ports else "N/A"))
        
        stdscr.addstr(9, 2, "Active Layers (TAB to select):", curses.A_UNDERLINE)
        row = 10
        for i, layer in enumerate(engine.layers):
            if layer['active']:
                if row < h - 12:
                    cursor = ">> " if i == engine.selected_layer_idx else " - "
                    ens_tag = f" [{layer['ensemble_mode'].upper()}]" if layer['ensemble_mode'] != 'off' else ""
                    curv_tag = f" ~{layer.get('vel_curve', 'linear')[:4]}" if layer.get('vel_curve', 'linear') != 'linear' else ""
                    attr = curses.A_BOLD if i == engine.selected_layer_idx else curses.A_NORMAL
                    stdscr.addstr(row, 2, f"{cursor}{layer['name']}{ens_tag}{curv_tag} (Ch:{layer['channel']+1} PGM:{layer['program']} Vol:{layer['volume']})", attr)
                    row += 1
        
        if time.time() - engine.last_key_time < 0.2:
            anim_text = f" KEY PRESSED: [{engine.last_key_name}] "
            stdscr.addstr(2, w - len(anim_text) - 2, anim_text, curses.color_pair(4) | curses.A_REVERSE)

        if engine.show_monitor:
            stdscr.attron(curses.color_pair(3))
            stdscr.addstr(4, w - 45, "┌── MIDI MONITOR ───────────────────────┐")
            for i, m_msg in enumerate(engine.midi_monitor):
                stdscr.addstr(5+i, w - 45, f"│ {m_msg[:38]:<38} │")
            stdscr.addstr(5+len(engine.midi_monitor), w - 45, "└───────────────────────────────────────┘")
            stdscr.attroff(curses.color_pair(3))

        if engine.show_help:
            help_w, help_h = 60, 20
            start_y, start_x = (h - help_h)//2, (w - help_w)//2
            stdscr.attron(curses.color_pair(4))
            for i in range(help_h):
                stdscr.addstr(start_y + i, start_x, " " * min(help_w, w-start_x), curses.A_REVERSE)
            help_content = [
                "PyMixensia MIDI Engine - Panduan Pengguna",
                "=========================================",
                "[F1]       : Tampilkan / Tutup bantuan ini",
                "[F2]       : Edit Preset yang sedang aktif",
                "[F3]       : Buat Preset Baru (Reset semua layer)",
                "[S]        : Start / Stop MIDI Engine",
                "[L]        : Pilih Preset dari folder 'presets'",
                "[X]        : Toggle Keyboard Splits (Global)",
                "[M]        : Toggle MIDI Monitor (Real-time)",
                "[A]        : Toggle Auto-Panic (Saat stop)",
                "[F]        : Toggle Global Fixed Velocity (110)",
                "[O]        : Toggle Pedal Sustain Detection",
                "[ [ ] / [ ] ] : Master Transpose (Turun/Naik)",
                "[TAB]      : Pilih Layer aktif",
                "[ + ] / [ - ] : Naik/Turun Volume Layer terpilih",
                "[P]        : PANIC! (Matikan semua nota)",
                "[Q]        : Keluar dari aplikasi"
            ]
            for i, line in enumerate(help_content):
                if start_y + 1 + i < h:
                    stdscr.addstr(start_y + 1 + i, start_x + 3, line[:help_w-6], curses.A_REVERSE)
            stdscr.attroff(curses.color_pair(4))

        if engine.show_editor:
            stdscr.erase()
            stdscr.attron(curses.A_BOLD | curses.color_pair(3))
            stdscr.addstr(1, 2, f" PRESET EDITOR - Layer {engine.editor_layer_idx + 1}/16 ")
            stdscr.attroff(curses.A_BOLD | curses.color_pair(3))
            layer = engine.layers[engine.editor_layer_idx]
            fields = [
                ('active', 'Active Status', [True, False]),
                ('channel', 'MIDI Channel', list(range(16))),
                ('program', 'Program Change', list(range(128))),
                ('volume', 'Volume', list(range(128))),
                ('transpose', 'Transpose', list(range(-48, 49))),
                ('chord_mode', 'Smart Chord', ['off', 'octave', 'major', 'minor', 'power']),
                ('arp_mode', 'Arpeggiator', ['off', 'up', 'down', 'random']),
                ('vel_curve', 'Velocity Curve', ['linear', 'soft', 'hard', 'fixed']),
                ('hold_mode', 'Hold Mode', ['normal', 'smart']),
                ('ensemble_mode', 'Ensemble Mode', ['off', 'top', 'bottom', 'middle']),
                ('min_note', 'Min Note', list(range(128))),
                ('max_note', 'Max Note', list(range(128))),
                ('min_vel', 'Min Velocity', list(range(128))),
                ('max_vel', 'Max Velocity', list(range(128))),
            ]
            # Exhaustive Field Descriptions (Manual V2)
            field_help = {
                'active': "Status Aktif: [ON] Bunyi, [OFF] Senyap. Gunakan untuk layering suara (Piano+Strings).",
                'channel': "MIDI Channel: Saluran output (1-16). Harus sama dengan channel di VST/Synthesizer Anda.",
                'program': "Program Change: Suara instrumen GM. Contoh: 0:Grand Piano, 19:Church Organ, 40:Violin, 52:Choir.",
                'volume': "Volume: Level suara (0-127). Atur volume per layer untuk mendapatkan mix yang seimbang.",
                'transpose': "Transpose: Geser nada per semitone. +12 = naik 1 oktav, -12 = turun 1 oktav.",
                'chord_mode': {
                    'off': "Smart Chord [Off]: Main nada tunggal (standar).",
                    'octave': "Smart Chord [Octave]: Menambah 1 nada (12 semitone di atas). Suara jadi lebih megah/lebar.",
                    'major': "Smart Chord [Major]: Menambah nada ke-3 & ke-5 (Mayor). Tekan C bunyi chord C-E-G.",
                    'minor': "Smart Chord [Minor]: Menambah nada ke-3 minor & ke-5. Tekan C bunyi chord C-Eb-G.",
                    'power': "Smart Chord [Power]: Menambah nada ke-5 & oktav. Cocok untuk Rock Guitar/Lead Synth."
                },
                'arp_mode': {
                    'off': "Arpeggiator [Off]: Nada dimainkan bersamaan (Polyphonic).",
                    'up': "Arpeggiator [Up]: Memainkan nada dari yang terendah ke tertinggi secara berurutan.",
                    'down': "Arpeggiator [Down]: Memainkan nada dari yang tertinggi ke terendah secara berurutan.",
                    'random': "Arpeggiator [Random]: Memainkan nada yang ditahan secara acak."
                },
                'vel_curve': {
                    'linear': "Curve [Linear]: Respon standar. Kekerasan suara sama dengan kekerasan tekanan tuts.",
                    'soft': "Curve [Soft]: Respon ringan. Tekan pelan sudah menghasilkan suara yang cukup jelas (Ballad).",
                    'hard': "Curve [Hard]: Respon berat. Harus ditekan keras untuk suara kencang (Rock/Percussive).",
                    'fixed': "Curve [Fixed]: Velocity dikunci di 100. Cocok untuk suara Organ atau Synth Lead."
                },
                'hold_mode': {
                    'normal': "Hold Mode [Normal]: Pedal sustain bekerja standar seperti keyboard biasa.",
                    'smart': "Hold Mode [Smart]: Mencegah penumpukan nota berlebih saat sustain agar CPU tetap ringan."
                },
                'ensemble_mode': {
                    'off': "Ensemble [Off]: Semua jari yang menekan tuts akan membunyikan layer ini.",
                    'top': "Ensemble [Top]: Hanya nada tertinggi dari akord yang bunyi (untuk Melodi).",
                    'bottom': "Ensemble [Bottom]: Hanya nada terendah dari akord yang bunyi (untuk Bass).",
                    'middle': "Ensemble [Middle]: Hanya nada-nada di tengah (bukan terendah/tertinggi) yang bunyi."
                },
                'min_note': "Min Note: Batas tuts paling kiri (0-127). Contoh: Set 60 (C3) sebagai titik awal split.",
                'max_note': "Max Note: Batas tuts paling kanan (0-127). Contoh: Set 59 agar Bass hanya bunyi di kiri.",
                'min_vel': "Min Velocity: Tekanan minimal agar bunyi. Contoh: Set 100 agar Strings bunyi hanya saat ditekan keras.",
                'max_vel': "Max Velocity: Tekanan maksimal. Contoh: Set 80 agar Piano hilang saat Anda menekan sangat keras."
            }

            for i, (key, label, options) in enumerate(fields):
                attr = curses.A_REVERSE if i == engine.editor_field_idx else curses.A_NORMAL
                val = layer.get(key, "-")
                disp_val = "ON" if val is True else ("OFF" if val is False else str(val))
                if key == 'channel': disp_val = str(val + 1)
                if key == 'program':
                    instr_name = engine.gm_instruments[val] if val < len(engine.gm_instruments) else "Unknown"
                    disp_val = f"{val} ({instr_name})"
                stdscr.addstr(4 + i, 4, f"{label:<20} : {disp_val}", attr)

            # Draw Detailed Description Box
            desc_y = 4 + len(fields) + 1
            selected_key = fields[engine.editor_field_idx][0]
            help_data = field_help.get(selected_key, "")
            
            # If help_data is a dict, get the specific option description
            if isinstance(help_data, dict):
                curr_val = layer.get(selected_key)
                desc_text = help_data.get(curr_val, f"Info untuk {selected_key}")
            else:
                desc_text = help_data

            stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
            stdscr.addstr(desc_y, 4, f"» TUTORIAL: {desc_text[:w-15]}")
            stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)

            stdscr.addstr(h-4, 2, "[Arrows] Navigate/Change  [TAB] Next Layer  [S] Save  [A] Save As  [ESC/F2] Close", curses.A_DIM)
            stdscr.refresh()
            ek = stdscr.getch()
            if ek == curses.KEY_F2 or ek == 27: engine.show_editor = False
            elif ek == 9: engine.editor_layer_idx = (engine.editor_layer_idx + 1) % 16
            elif ek == curses.KEY_UP: engine.editor_field_idx = (engine.editor_field_idx - 1) % len(fields)
            elif ek == curses.KEY_DOWN: engine.editor_field_idx = (engine.editor_field_idx + 1) % len(fields)
            elif ek == curses.KEY_LEFT or ek == curses.KEY_RIGHT:
                key, label, options = fields[engine.editor_field_idx]
                if isinstance(options, list):
                    curr_idx = options.index(layer.get(key))
                    step = 1 if ek == curses.KEY_RIGHT else -1
                    layer[key] = options[(curr_idx + step) % len(options)]
                    if key == 'program': layer['name'] = engine.gm_instruments[layer['program']]
                    if engine.running: engine.update_all_layer_parameters()
            elif ek == ord('s'):
                if engine.current_preset_name not in ["None", "New Preset"]:
                    config.save_preset(engine.current_preset_name)
                    engine.show_editor = False
                else:
                    stdscr.addstr(h-2, 2, "Save New Preset As (filename): ", curses.A_BOLD)
                    stdscr.refresh(); curses.echo(); curses.curs_set(1); stdscr.nodelay(0)
                    fname_bytes = stdscr.getstr(h-2, 33, 40)
                    stdscr.nodelay(1); curses.noecho(); curses.curs_set(0)
                    fname = fname_bytes.decode('utf-8').strip()
                    if fname:
                        if not fname.endswith('.cfg'): fname += '.cfg'
                        config.save_preset(fname); engine.current_preset_name = fname; engine.show_editor = False
            elif ek == ord('a'):
                stdscr.addstr(h-2, 2, "Save Copy As (filename): ", curses.A_BOLD)
                stdscr.refresh(); curses.echo(); curses.curs_set(1); stdscr.nodelay(0)
                fname_bytes = stdscr.getstr(h-2, 27, 40)
                stdscr.nodelay(1); curses.noecho(); curses.curs_set(0)
                fname = fname_bytes.decode('utf-8').strip()
                if fname:
                    if not fname.endswith('.cfg'): fname += '.cfg'
                    config.save_preset(fname); engine.current_preset_name = fname; engine.show_editor = False
            continue

        stdscr.addstr(h-9, 2, "Log / Notifications:", curses.A_DIM)
        for i, note in enumerate(engine.notifications):
            stdscr.addstr(h-8+i, 4, note, curses.A_DIM)
        instr = "[F1] Help  [F2] Editor  [F3] New  [S] Start  [L] List  [X] Splits  [M] Monitor  [P] Panic  [Q] Quit"
        stdscr.addstr(h-2, 2, instr, curses.A_REVERSE)
        stdscr.refresh()
        k = stdscr.getch()
        if k != -1:
            engine.last_key_time = time.time()
            engine.last_key_name = curses.keyname(k).decode()
        if k == ord('q'): config.save_settings(); engine.stop(); break
        elif k == curses.KEY_F1: engine.show_help = not engine.show_help
        elif k == curses.KEY_F2:
            engine.show_editor = not engine.show_editor
            if engine.show_editor: engine.editor_layer_idx = 0; engine.editor_field_idx = 0
        elif k == curses.KEY_F3:
            for i in range(16): engine.layers[i] = engine._default_layer_config(i, engine.gm_instruments); engine.layers[i]['name'] = engine.gm_instruments[0]
            engine.current_preset_name = "New Preset"; engine.editor_layer_idx = 0; engine.editor_field_idx = 0; engine.add_notification("Clean Preset Initialized"); engine.show_editor = True
        elif engine.show_help and k != -1: engine.show_help = False
        elif k == ord('m'): engine.show_monitor = not engine.show_monitor
        elif k == ord('a'): engine.auto_panic = not engine.auto_panic; config.save_settings(); engine.add_notification(f"Auto-Panic: {'ON' if engine.auto_panic else 'OFF'}")
        elif k == ord('f'): engine.global_fixed_vel = not engine.global_fixed_vel; config.save_settings(); engine.add_notification(f"Global Fixed Velocity: {'ON' if engine.global_fixed_vel else 'OFF'}")
        elif k == ord('o'): engine.sustain_enabled = not engine.sustain_enabled; config.save_settings(); engine.add_notification(f"Sustain: {'ON' if engine.sustain_enabled else 'OFF'}")
        elif k == ord('['): engine.master_transpose -= 1; config.save_settings(); engine.add_notification(f"Transpose: {engine.master_transpose}")
        elif k == ord(']'): engine.master_transpose += 1; config.save_settings(); engine.add_notification(f"Transpose: {engine.master_transpose}")
        elif k == 9: # TAB
            idx = [i for i, l in enumerate(engine.layers) if l['active']]
            if idx: engine.selected_layer_idx = idx[(idx.index(engine.selected_layer_idx) + 1) % len(idx)] if engine.selected_layer_idx in idx else idx[0]
        elif k in [ord('+'), ord('=')]:
            l = engine.layers[engine.selected_layer_idx]; l['volume'] = min(127, l['volume'] + 5); engine.update_all_layer_parameters()
        elif k in [ord('-'), ord('_')]:
            l = engine.layers[engine.selected_layer_idx]; l['volume'] = max(0, l['volume'] - 5); engine.update_all_layer_parameters()
        elif k == ord('s'):
            if engine.running: engine.stop()
            else:
                in_p, out_p = mido.get_input_names(), mido.get_output_names()
                if in_p and out_p: engine.start(in_p[in_idx], out_p[out_idx])
                else: engine.add_notification("No MIDI ports")
        elif k == ord('p'): engine.panic()
        elif k == ord('l'):
            presets = sorted([f for f in os.listdir("presets") if f.endswith('.cfg')])
            if presets:
                p_idx = engine.preset_index
                while True:
                    stdscr.erase()
                    stdscr.addstr(2, 2, "Select Preset (Enter to confirm, Esc to cancel):", curses.A_BOLD)
                    for i, p in enumerate(presets):
                        attr = curses.A_REVERSE if i == p_idx else curses.A_NORMAL
                        if 4+i < h-2: stdscr.addstr(4+i, 4, f" {p} ", attr)
                    stdscr.refresh(); pk = stdscr.getch()
                    if pk == curses.KEY_UP: p_idx = (p_idx - 1) % len(presets)
                    elif pk == curses.KEY_DOWN: p_idx = (p_idx + 1) % len(presets)
                    elif pk == 10: engine.preset_index = p_idx; config.load_preset(presets[p_idx]); config.save_settings(); break
                    elif pk == 27: break
        elif k == ord('1'):
            in_p = mido.get_input_names()
            if in_p: in_idx = (in_idx + 1) % len(in_p); engine.add_notification(f"In: {in_p[in_idx]}"); config.save_settings()
        elif k == ord('2'):
            out_p = mido.get_output_names()
            if out_p: out_idx = (out_idx + 1) % len(out_p); engine.add_notification(f"Out: {out_p[out_idx]}"); config.save_settings()
        elif k == ord('x'):
            engine.disable_splits = not engine.disable_splits; engine.add_notification(f"Splits {'OFF' if engine.disable_splits else 'ON'}")
        elif k in [curses.KEY_UP, curses.KEY_DOWN]:
            presets = sorted([f for f in os.listdir("presets") if f.endswith('.cfg')])
            if presets:
                engine.preset_index = (engine.preset_index + (1 if k == curses.KEY_DOWN else -1)) % len(presets)
                config.load_preset(presets[engine.preset_index]); config.save_settings()
        time.sleep(0.03)
