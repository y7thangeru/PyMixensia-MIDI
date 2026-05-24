import curses
import time
import os
import mido

def draw_menu(stdscr, engine, config):
    # Initialize high-contrast color pairs
    curses.start_color()
    curses.use_default_colors()
    
    # 1: Green on Black (Active/Success)
    curses.init_pair(1, curses.COLOR_GREEN, -1)
    # 2: Red on Black (Stopped/Error)
    curses.init_pair(2, curses.COLOR_RED, -1)
    # 3: Cyan on Black (Presets/Info)
    curses.init_pair(3, curses.COLOR_CYAN, -1)
    # 4: Yellow on Black (Tutorial/Settings)
    curses.init_pair(4, curses.COLOR_YELLOW, -1)
    # 5: Magenta on Black (Layers)
    curses.init_pair(5, curses.COLOR_MAGENTA, -1)
    # 6: Blue on Black (Ports)
    curses.init_pair(6, curses.COLOR_BLUE, -1)
    # 7: Black on Cyan (Header/Footer - High Contrast)
    curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_CYAN)
    # 8: Black on Yellow (Selected/Cursor - High Contrast)
    curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    
    curses.curs_set(0)
    stdscr.nodelay(1)
    
    in_ports = mido.get_input_names()
    out_ports = mido.get_output_names()
    in_idx = 0
    out_idx = 0
    
    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()

        # Header: Black text on Cyan background for maximum visibility
        title = " 🎹  PyMixensia MIDI Engine V2  🎹 "
        try:
            stdscr.attron(curses.color_pair(7) | curses.A_BOLD)
            stdscr.addstr(0, 0, " " * (w-1)) 
            stdscr.addstr(0, max(0, (w//2)-(len(title)//2)), title)
            stdscr.attroff(curses.color_pair(7) | curses.A_BOLD)
        except: pass

        # Status Section
        status = " RUNNING " if engine.running else " STOPPED "
        st_color = curses.color_pair(1 if engine.running else 2) | curses.A_REVERSE | curses.A_BOLD
        stdscr.addstr(2, 2, "STATUS:", curses.A_BOLD)
        stdscr.addstr(2, 10, status, st_color)
        
        stdscr.addstr(2, 25, "PRESET:", curses.A_BOLD)
        stdscr.addstr(2, 33, f" {engine.current_preset_name} ", curses.color_pair(3) | curses.A_REVERSE)

        # Settings Section
        split_status = "FULL KEYBOARD" if engine.disable_splits else "ZONES ACTIVE"
        stdscr.addstr(3, 2, "SPLITS :", curses.A_DIM)
        stdscr.addstr(3, 11, split_status, curses.color_pair(4) if engine.disable_splits else curses.color_pair(1))

        ap_status = "ON" if engine.auto_panic else "OFF"
        stdscr.addstr(4, 2, "A-PANIC:", curses.A_DIM)
        stdscr.addstr(4, 11, ap_status, curses.color_pair(1 if engine.auto_panic else 2))
        
        fv_status = "FIXED (110)" if engine.global_fixed_vel else "DYNAMIC"
        stdscr.addstr(4, 25, "VELOCITY:", curses.A_DIM)
        stdscr.addstr(4, 35, fv_status, curses.color_pair(5 if engine.global_fixed_vel else 1))

        sust_status = "ENABLED" if engine.sustain_enabled else "DISABLED"
        stdscr.addstr(5, 2, "SUSTAIN:", curses.A_DIM)
        stdscr.addstr(5, 11, sust_status, curses.color_pair(1 if engine.sustain_enabled else 2))
        
        stdscr.addstr(5, 25, "MASTER T:", curses.A_DIM)
        stdscr.addstr(5, 35, f"{engine.master_transpose:+d}", curses.color_pair(4) | curses.A_BOLD if engine.master_transpose != 0 else 0)

        # Ports Section
        stdscr.addstr(7, 2, "IN  PORT:", curses.A_BOLD)
        stdscr.addstr(7, 12, (in_ports[in_idx] if in_ports else "N/A"), curses.color_pair(3))
        stdscr.addstr(8, 2, "OUT PORT:", curses.A_BOLD)
        stdscr.addstr(8, 12, (out_ports[out_idx] if out_ports else "N/A"), curses.color_pair(3))
        
        # Layers Section
        stdscr.addstr(10, 2, "ACTIVE LAYERS (TAB to Select):", curses.A_BOLD | curses.color_pair(5))
        stdscr.addstr(11, 2, "─" * (w-4), curses.A_DIM)
        
        row = 12
        for i, layer in enumerate(engine.layers):
            if layer['active']:
                if row < h - 12:
                    is_selected = (i == engine.selected_layer_idx)
                    cursor = " ➔ " if is_selected else "   "
                    ens_tag = f" [{layer['ensemble_mode'].upper()}]" if layer['ensemble_mode'] != 'off' else ""
                    curv_tag = f" ~{layer.get('vel_curve', 'linear')[:4]}" if layer.get('vel_curve', 'linear') != 'linear' else ""
                    chord_tag = f" +{layer.get('chord_mode', 'off').upper()}" if layer.get('chord_mode', 'off') != 'off' else ""
                    
                    if is_selected:
                        stdscr.attron(curses.color_pair(8))
                        stdscr.addstr(row, 2, " " * (w-4))
                        stdscr.addstr(row, 2, f"{cursor}{layer['name']}{ens_tag}{curv_tag}{chord_tag} (Ch:{layer['channel']+1} PGM:{layer['program']} Vol:{layer['volume']})")
                        stdscr.attroff(curses.color_pair(8))
                    else:
                        stdscr.addstr(row, 2, f"{cursor}{layer['name']}{ens_tag}{curv_tag}{chord_tag} (Ch:{layer['channel']+1} PGM:{layer['program']} Vol:{layer['volume']})")
                    row += 1
        
        # Key Animation
        if time.time() - engine.last_key_time < 0.2:
            anim_text = f" KEY: {engine.last_key_name} "
            stdscr.addstr(2, w - len(anim_text) - 2, anim_text, curses.color_pair(8) | curses.A_BOLD)

        # MIDI Monitor
        if engine.show_monitor:
            stdscr.attron(curses.color_pair(3))
            monitor_w = 40
            stdscr.addstr(4, w - monitor_w - 2, "┌── MIDI MONITOR ────────────────────┐")
            for i, m_msg in enumerate(engine.midi_monitor):
                stdscr.addstr(5+i, w - monitor_w - 2, f"│ {m_msg[:monitor_w-4]:<{monitor_w-4}} │")
            stdscr.addstr(5+len(engine.midi_monitor), w - monitor_w - 2, "└────────────────────────────────────┘")
            stdscr.attroff(curses.color_pair(3))

        # Help Overlay
        if engine.show_help:
            help_w, help_h = 64, 18
            start_y, start_x = (h - help_h)//2, (w - help_w)//2
            stdscr.attron(curses.color_pair(7))
            for i in range(help_h):
                stdscr.addstr(start_y + i, start_x, " " * help_w)
            stdscr.addstr(start_y + 1, start_x + (help_w//2)-10, " PYMIXENSIA USER GUIDE ", curses.A_BOLD | curses.A_UNDERLINE)
            help_lines = [
                "[F1] Help | [F2] Editor | [F3] New | [Q] Quit",
                "─────────────────────────────────────────────",
                "[S] Start/Stop Engine     [L] Load Preset",
                "[X] Toggle Splits         [M] MIDI Monitor",
                "[A] Auto-Panic Toggle     [F] Fixed Velocity",
                "[O] Sustain Toggle        [ [ / ] ] Master Transpose",
                "[TAB] Select Layer        [+/-] Layer Volume",
                "[P] PANIC (All Off)       [UP/DN] Quick Switch",
                "─────────────────────────────────────────────",
                "Press any key to close..."
            ]
            for i, line in enumerate(help_lines):
                stdscr.addstr(start_y + 3 + i, start_x + 4, line)
            stdscr.attroff(curses.color_pair(7))

        # Editor Overlay
        if engine.show_editor:
            stdscr.erase()
            # Editor Header: Black on Cyan
            stdscr.attron(curses.color_pair(7) | curses.A_BOLD)
            stdscr.addstr(0, 0, " " * (w-1))
            stdscr.addstr(0, (w//2)-15, f" 🛠️  EDITOR: LAYER {engine.editor_layer_idx + 1}/16 🛠️ ")
            stdscr.attroff(curses.color_pair(7) | curses.A_BOLD)

            layer = engine.layers[engine.editor_layer_idx]
            fields = [
                ('active', 'ACTIVE STATUS', [True, False]),
                ('channel', 'MIDI CHANNEL', list(range(16))),
                ('program', 'PROGRAM CHANGE', list(range(128))),
                ('volume', 'VOLUME LEVEL', list(range(128))),
                ('transpose', 'TRANSPOSE', list(range(-48, 49))),
                ('chord_mode', 'SMART CHORD', ['off', 'octave', 'major', 'minor', 'power']),
                ('arp_mode', 'ARPEGGIATOR', ['off', 'up', 'down', 'random']),
                ('vel_curve', 'VELOCITY CURVE', ['linear', 'soft', 'hard', 'fixed']),
                ('hold_mode', 'HOLD MODE', ['normal', 'smart']),
                ('ensemble_mode', 'ENSEMBLE MODE', ['off', 'top', 'bottom', 'middle']),
                ('min_note', 'MIN NOTE (KEY)', list(range(128))),
                ('max_note', 'MAX NOTE (KEY)', list(range(128))),
                ('min_vel', 'MIN VELOCITY', list(range(128))),
                ('max_vel', 'MAX VELOCITY', list(range(128))),
            ]
            
            for i, (key, label, options) in enumerate(fields):
                is_selected = (i == engine.editor_field_idx)
                val = layer.get(key, "-")
                disp_val = "ON" if val is True else ("OFF" if val is False else str(val))
                if key == 'channel': disp_val = str(val + 1)
                if key == 'program':
                    instr_name = engine.gm_instruments[val] if val < len(engine.gm_instruments) else "Unknown"
                    disp_val = f"{val} ({instr_name})"
                
                if is_selected:
                    stdscr.attron(curses.color_pair(8))
                    stdscr.addstr(3 + i, 4, f" {label:<20} : {disp_val:<40} ")
                    stdscr.attroff(curses.color_pair(8))
                else:
                    stdscr.addstr(3 + i, 4, f" {label:<20} : ", curses.A_DIM)
                    stdscr.addstr(3 + i, 27, disp_val, curses.color_pair(3) | curses.A_BOLD)

            field_help = {
                'active': "Status Aktif: [ON] Bunyi, [OFF] Senyap. Gunakan layering (Piano+Strings).",
                'channel': "MIDI Channel: Saluran output (1-16). Harus sama dengan instrumen VST Anda.",
                'program': "Program Change: Suara instrumen GM (0-127). Nama instrumen muncul di samping.",
                'volume': "Volume: Level suara layer (0-127). Atur per layer untuk mix seimbang.",
                'transpose': "Transpose: Geser nada per semitone. +12 = naik 1 oktav.",
                'chord_mode': {
                    'off': "Smart Chord [Off]: Main nada tunggal (standar).",
                    'octave': "Smart Chord [Octave]: Menambah 1 nada (+12). Suara jadi lebar.",
                    'major': "Smart Chord [Major]: Chord Mayor otomatis (1-3-5).",
                    'minor': "Smart Chord [Minor]: Chord Minor otomatis (1-3b-5).",
                    'power': "Smart Chord [Power]: Power chord (1-5-8). Cocok untuk Rock."
                },
                'arp_mode': {
                    'off': "Arpeggiator [Off]: Nada dimainkan bersamaan.",
                    'up': "Arpeggiator [Up]: Memainkan nada dari terendah ke tertinggi.",
                    'down': "Arpeggiator [Down]: Memainkan nada dari tertinggi ke terendah.",
                    'random': "Arpeggiator [Random]: Memainkan nada secara acak."
                },
                'vel_curve': {
                    'linear': "Curve [Linear]: Respon standar (apa adanya).",
                    'soft': "Curve [Soft]: Respon ringan. Cocok untuk Ballad.",
                    'hard': "Curve [Hard]: Respon berat. Cocok untuk Rock/Perkusif.",
                    'fixed': "Curve [Fixed]: Velocity dikunci di 100. Untuk Organ/Lead."
                },
                'hold_mode': {
                    'normal': "Hold Mode [Normal]: Pedal sustain bekerja standar.",
                    'smart': "Hold Mode [Smart]: Mencegah penumpukan nota (hemat CPU)."
                },
                'ensemble_mode': {
                    'off': "Ensemble [Off]: Semua jari membunyikan layer ini.",
                    'top': "Ensemble [Top]: Hanya nada tertinggi yang bunyi.",
                    'bottom': "Ensemble [Bottom]: Hanya nada terendah yang bunyi.",
                    'middle': "Ensemble [Middle]: Hanya nada tengah yang bunyi."
                },
                'min_note': "Min Note: Batas bawah tuts (0-127). Set 60 (C3) sebagai split point.",
                'max_note': "Max Note: Batas atas tuts (0-127). Set 59 agar layer hanya bunyi di kiri.",
                'min_vel': "Min Velocity: Tekanan minimal. Set 100 agar bunyi hanya saat ditekan keras.",
                'max_vel': "Max Velocity: Tekanan maksimal agar suara tidak pecah."
            }

            selected_key = fields[engine.editor_field_idx][0]
            help_data = field_help.get(selected_key, "")
            desc_text = help_data.get(layer.get(selected_key), "") if isinstance(help_data, dict) else help_data
            
            stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
            stdscr.addstr(h-5, 4, f"💡 INFO: {desc_text[:w-15]}")
            stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)

            stdscr.attron(curses.color_pair(7) | curses.A_BOLD)
            stdscr.addstr(h-2, 0, " " * (w-1))
            stdscr.addstr(h-2, max(0, (w//2)-30), " [Arrows] Edit   [TAB] Layer   [S] Save   [A] Save As   [F2] Close ")
            stdscr.attroff(curses.color_pair(7) | curses.A_BOLD)
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
                    config.save_preset(engine.current_preset_name); engine.show_editor = False
                else:
                    stdscr.addstr(h-2, 2, " SAVE NEW: ", curses.color_pair(8))
                    stdscr.refresh(); curses.echo(); curses.curs_set(1); stdscr.nodelay(0)
                    fname_bytes = stdscr.getstr(h-2, 13, 20)
                    stdscr.nodelay(1); curses.noecho(); curses.curs_set(0)
                    fname = fname_bytes.decode('utf-8').strip()
                    if fname:
                        if not fname.endswith('.cfg'): fname += '.cfg'
                        config.save_preset(fname); engine.current_preset_name = fname; engine.show_editor = False
            elif ek == ord('a'):
                stdscr.addstr(h-2, 2, " SAVE AS: ", curses.color_pair(8))
                stdscr.refresh(); curses.echo(); curses.curs_set(1); stdscr.nodelay(0)
                fname_bytes = stdscr.getstr(h-2, 11, 20)
                stdscr.nodelay(1); curses.noecho(); curses.curs_set(0)
                fname = fname_bytes.decode('utf-8').strip()
                if fname:
                    if not fname.endswith('.cfg'): fname += '.cfg'
                    config.save_preset(fname); engine.current_preset_name = fname; engine.show_editor = False
            continue

        # Log Area
        stdscr.addstr(h-9, 2, "LOGS:", curses.A_BOLD | curses.color_pair(3))
        for i, note in enumerate(engine.notifications):
            stdscr.addstr(h-8+i, 4, f"• {note}", curses.A_DIM)
            
        # Footer: Black on Cyan for maximum contrast
        try:
            footer = " [F1] Help   [F2] Editor   [F3] New   [S] Start/Stop   [L] Presets   [Q] Quit "
            stdscr.attron(curses.color_pair(7) | curses.A_BOLD)
            stdscr.addstr(h-1, 0, " " * (w-1))
            stdscr.addstr(h-1, max(0, (w//2)-(len(footer)//2)), footer[:w-1])
            stdscr.attroff(curses.color_pair(7) | curses.A_BOLD)
        except: pass
        
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
        elif k == ord('f'): engine.global_fixed_vel = not engine.global_fixed_vel; config.save_settings(); engine.add_notification(f"Fixed Velocity: {'ON' if engine.global_fixed_vel else 'OFF'}")
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
                    stdscr.addstr(2, 2, " SELECT PRESET (Enter to Load, Esc to Cancel) ", curses.color_pair(7) | curses.A_BOLD)
                    for i, p in enumerate(presets):
                        attr = curses.color_pair(8) if i == p_idx else curses.A_NORMAL
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
