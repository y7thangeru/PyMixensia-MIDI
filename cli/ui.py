import curses
import time
import os
import mido
import random
import math

def draw_menu(stdscr, engine, config):
    # Initialize high-contrast color pairs
    curses.start_color()
    curses.use_default_colors()
    
    curses.init_pair(1, curses.COLOR_GREEN, -1)
    curses.init_pair(2, curses.COLOR_RED, -1)
    curses.init_pair(3, curses.COLOR_CYAN, -1)
    curses.init_pair(4, curses.COLOR_YELLOW, -1)
    curses.init_pair(5, curses.COLOR_MAGENTA, -1)
    curses.init_pair(6, curses.COLOR_BLUE, -1)
    curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    
    curses.curs_set(0)
    stdscr.nodelay(1)
    
    in_idx = 0
    out_idx = 0
    
    def spawn_particle(note, vel):
        h, w = stdscr.getmaxyx()
        x_pos = int((note / 127) * (w - 6)) + 3
        
        if engine.visualizer_mode == 0: # MEGA FIREWORKS
            color = random.randint(1, 5)
            for _ in range(25): 
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(1.2, 3.5)
                engine.particles.append({
                    'type': 'firework', 'x': float(x_pos), 'y': float(h-4),
                    'vx': math.cos(angle) * speed * 2.5, 'vy': math.sin(angle) * speed - 2.5,
                    'life': 1.8, 'color': color, 'char': random.choice(['█', '▓', '▒'])
                })
        elif engine.visualizer_mode == 1: # GIANT SHINING STARS
            engine.particles.append({
                'type': 'star', 'x': float(x_pos), 'y': -2.0,
                'vy': random.uniform(0.3, 0.5), 'life': 3.0, 
                'color': random.randint(3, 4)
            })
        elif engine.visualizer_mode == 2: # RAINBOW RIPPLES
            engine.particles.append({
                'type': 'ripple', 'x': x_pos, 'y': h//2, 'radius': 0.0, 'life': 1.5,
                'color': random.randint(1, 5)
            })
        elif engine.visualizer_mode == 3: # FALLING BLOCKS
            engine.particles.append({
                'type': 'falling', 'x': x_pos, 'y': 0.0, 
                'len': max(4, vel//6), 'color': random.randint(1, 5)
            })
        elif engine.visualizer_mode == 4: # TETRIS GIANT
            engine.particles.append({
                'type': 'tetris', 'x': x_pos - 1, 'y': 0.0, 
                'w': 5, 'h': 2, 'color': random.randint(1, 5)
            })

    original_handle_note_on = engine.handle_note_on
    def visualizer_note_on(msg):
        spawn_particle(msg.note, msg.velocity)
        original_handle_note_on(msg)
    engine.handle_note_on = visualizer_note_on

    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        
        in_ports = engine.available_in_ports
        out_ports = engine.available_out_ports

        if engine.last_in_name in in_ports: in_idx = in_ports.index(engine.last_in_name)
        if engine.last_out_name in out_ports: out_idx = out_ports.index(engine.last_out_name)
        if in_idx >= len(in_ports): in_idx = 0
        if out_idx >= len(out_ports): out_idx = 0

        if engine.show_visualizer:
            new_particles = []
            for p in engine.particles:
                if p['type'] == 'firework':
                    p['x'] += p['vx']; p['y'] += p['vy']; p['vy'] += 0.07; p['life'] -= 0.012
                    if p['life'] > 0 and 1 < p['x'] < w-2 and 1 < p['y'] < h-2:
                        stdscr.addch(int(p['y']), int(p['x']), p['char'], curses.color_pair(p['color']))
                        new_particles.append(p)
                elif p['type'] == 'star':
                    p['y'] += p['vy']
                    if p['y'] < h-3:
                        px, py = int(p['x']), int(p['y'])
                        color = curses.color_pair(random.randint(1,5))
                        try:
                            stdscr.addstr(py, px, "█", color | curses.A_BOLD)
                            stdscr.addch(py-1, px, '│', color); stdscr.addch(py+1, px, '│', color)
                            stdscr.addch(py, px-1, '─', color); stdscr.addch(py, px+1, '─', color)
                        except: pass
                        new_particles.append(p)
                elif p['type'] == 'ripple':
                    p['radius'] += 0.8; p['life'] -= 0.012
                    if p['life'] > 0:
                        r_color = curses.color_pair((int(p['radius']) % 5) + 1)
                        for angle in range(0, 360, 15):
                            rx = int(p['x'] + math.cos(math.radians(angle)) * p['radius'] * 2.8)
                            ry = int(p['y'] + math.sin(math.radians(angle)) * p['radius'])
                            if 1 < rx < w-2 and 1 < ry < h-2: stdscr.addch(ry, rx, '█', r_color)
                        new_particles.append(p)
                elif p['type'] == 'falling':
                    p['y'] += 0.5
                    if p['y'] < h-1:
                        for i in range(int(p['len'])):
                            yy = int(p['y'] - i)
                            if 1 < yy < h-1: stdscr.addstr(yy, int(p['x']), "█", curses.color_pair(p['color']))
                        new_particles.append(p)
                elif p['type'] == 'tetris':
                    p['y'] += 0.4
                    if p['y'] < h-1:
                        for dy in range(p['h']):
                            for dx in range(p['w']):
                                if 1 < int(p['y'])-dy < h-1 and 1 < int(p['x'])+dx < w-1: stdscr.addch(int(p['y'])-dy, int(p['x'])+dx, '█', curses.color_pair(p['color']))
                        new_particles.append(p)
            engine.particles = new_particles
            modes = ["ULTRA FIREWORKS", "GIANT CROSS STARS", "RAINBOW RIPPLES", "HEAVY BLOCKS", "TETRIS COLOSSAL"]
            stdscr.addstr(h-1, 0, (" " * (w-1)), curses.color_pair(7))
            stdscr.addstr(h-1, 2, f" VISUALIZER: {modes[engine.visualizer_mode]} [Arrows] [F4 Exit] ", curses.color_pair(7) | curses.A_BOLD)
            stdscr.refresh(); k = stdscr.getch()
            if k == curses.KEY_F4 or k == 27: engine.show_visualizer = False
            elif k == curses.KEY_RIGHT: engine.visualizer_mode = (engine.visualizer_mode + 1) % 5; engine.particles = []
            elif k == curses.KEY_LEFT: engine.visualizer_mode = (engine.visualizer_mode - 1) % 5; engine.particles = []
            continue

        # Header
        title = " 🎹  PyMixensia MIDI Engine V2  🎹 "
        try:
            stdscr.attron(curses.color_pair(7) | curses.A_BOLD); stdscr.addstr(0, 0, " " * (w-1)); stdscr.addstr(0, max(0, (w//2)-(len(title)//2)), title); stdscr.attroff(curses.color_pair(7))
        except: pass

        # Status
        status = " RUNNING " if engine.running else " STOPPED "
        st_color = curses.color_pair(1 if engine.running else 2) | curses.A_REVERSE | curses.A_BOLD
        stdscr.addstr(2, 2, "STATUS:", curses.A_BOLD); stdscr.addstr(2, 10, status, st_color)
        stdscr.addstr(2, 25, "PRESET:", curses.A_BOLD); stdscr.addstr(2, 33, f" {engine.current_preset_name} ", curses.color_pair(3) | curses.A_REVERSE)

        # Settings
        stdscr.addstr(3, 2, "SPLITS :", curses.A_DIM); stdscr.addstr(3, 11, "OFF" if engine.disable_splits else "ON", curses.color_pair(4 if engine.disable_splits else 1))
        stdscr.addstr(4, 2, "A-PANIC:", curses.A_DIM); stdscr.addstr(4, 11, "ON" if engine.auto_panic else "OFF", curses.color_pair(1 if engine.auto_panic else 2))
        stdscr.addstr(4, 25, "VELOCITY:", curses.A_DIM); stdscr.addstr(4, 35, "FIXED" if engine.global_fixed_vel else "DYNAMIC", curses.color_pair(5 if engine.global_fixed_vel else 1))
        stdscr.addstr(5, 2, "SUSTAIN:", curses.A_DIM); stdscr.addstr(5, 11, "ON" if engine.sustain_enabled else "OFF", curses.color_pair(1 if engine.sustain_enabled else 2))
        stdscr.addstr(5, 25, "MASTER T:", curses.A_DIM); stdscr.addstr(5, 35, f"{engine.master_transpose:+d}", curses.color_pair(4) if engine.master_transpose != 0 else 0)

        # Ports
        stdscr.addstr(7, 2, "IN  PORT:", curses.A_BOLD); stdscr.addstr(7, 12, (in_ports[in_idx] if in_ports else "N/A"), curses.color_pair(3))
        stdscr.addstr(8, 2, "OUT PORT:", curses.A_BOLD); stdscr.addstr(8, 12, (out_ports[out_idx] if out_ports else "N/A"), curses.color_pair(3))
        
        # Layers (RE-FIXED)
        stdscr.addstr(10, 2, "ACTIVE LAYERS (TAB to Select):", curses.A_BOLD | curses.color_pair(5))
        stdscr.addstr(11, 2, "─" * (w-4), curses.A_DIM)
        row = 12
        for i, layer in enumerate(engine.layers):
            if layer['active'] and row < h - 12:
                is_sel = (i == engine.selected_layer_idx); cursor = " ➔ " if is_sel else "   "
                text = f"{cursor}{layer['name']} (Ch:{layer['channel']+1} PGM:{layer['program']} Vol:{layer['volume']})"
                if is_sel:
                    stdscr.attron(curses.color_pair(8)); stdscr.addstr(row, 2, " " * (w-4)); stdscr.addstr(row, 2, text); stdscr.attroff(curses.color_pair(8))
                else: stdscr.addstr(row, 2, text)
                row += 1
        
        # MIDI Monitor (OUTSIDE LAYER LOOP)
        if engine.show_monitor:
            stdscr.attron(curses.color_pair(3)); monitor_w = 60; stdscr.addstr(4, w-monitor_w-2, "┌── MIDI MONITOR " + "─"*(monitor_w-17) + "┐")
            for i, m_msg in enumerate(engine.midi_monitor): stdscr.addstr(5+i, w-monitor_w-2, f"│ {m_msg[:monitor_w-4]:<{monitor_w-4}} │")
            stdscr.addstr(5+len(engine.midi_monitor), w-monitor_w-2, "└" + "─"*(monitor_w-2) + "┘"); stdscr.attroff(curses.color_pair(3))

        # Help
        if engine.show_help:
            help_w, help_h = 64, 18; start_y, start_x = (h - help_h)//2, (w - help_w)//2
            stdscr.attron(curses.color_pair(7))
            for i in range(help_h): stdscr.addstr(start_y+i, start_x, " "*help_w)
            help_lines = ["[F1] Help | [F2] Editor | [F3] New | [F4] Visual", "─────────────────────────────────────────────", "[S] Start/Stop     [L] Load Preset", "[X] Splits Toggle  [M] MIDI Monitor", "[A] Auto-Panic     [F] Fixed Velocity", "[TAB] Select Layer [+/-] Volume", "[P] PANIC          [UP/DN] Quick Switch", "─────────────────────────────────────────────", "Press any key to close..."]
            for i, line in enumerate(help_lines): stdscr.addstr(start_y+3+i, start_x+4, line)
            stdscr.attroff(curses.color_pair(7))

        # Editor (RESTORED FULL MANUAL)
        if engine.show_editor:
            stdscr.erase(); stdscr.attron(curses.color_pair(7) | curses.A_BOLD); stdscr.addstr(0, 0, " "*(w-1)); stdscr.addstr(0, (w//2)-15, f" 🛠️  EDITOR: LAYER {engine.editor_layer_idx+1}/16 🛠️ "); stdscr.attroff(curses.color_pair(7))
            layer = engine.layers[engine.editor_layer_idx]
            fields = [('active', 'STATUS', [True, False]), ('channel', 'CHANNEL', list(range(16))), ('program', 'PROGRAM', list(range(128))), ('volume', 'VOLUME', list(range(128))), ('transpose', 'TRANSPOSE', list(range(-48, 49))), ('chord_mode', 'CHORD', ['off', 'octave', 'major', 'minor', 'power']), ('arp_mode', 'ARP', ['off', 'up', 'down', 'random']), ('vel_curve', 'CURVE', ['linear', 'soft', 'hard', 'fixed'])]
            for i, (key, label, options) in enumerate(fields):
                is_sel = (i == engine.editor_field_idx); val = layer.get(key, "-"); disp = "ON" if val is True else ("OFF" if val is False else str(val))
                if key == 'channel': disp = str(val+1)
                if key == 'program': disp = f"{val} ({engine.gm_instruments[val]})"
                if is_sel:
                    stdscr.attron(curses.color_pair(8)); stdscr.addstr(3+i, 4, f" {label:<15} : {disp:<40} "); stdscr.attroff(curses.color_pair(8))
                else: stdscr.addstr(3+i, 4, f" {label:<15} : ", curses.A_DIM); stdscr.addstr(3+i, 22, disp, curses.color_pair(3))
            
            # Exhaustive Field Descriptions (Manual V2 - RESTORED)
            field_help = {
                'active': "Status Aktif: [ON] Bunyi, [OFF] Senyap. Gunakan layering (Piano+Strings).",
                'channel': "MIDI Channel: Saluran output (1-16). Harus sama dengan instrumen VST Anda.",
                'program': "Program Change: Suara instrumen GM (0-127). Nama instrumen muncul di samping.",
                'volume': "Volume: Level suara layer (0-127). Atur per layer untuk mix seimbang.",
                'transpose': "Transpose: Geser nada per semitone. +12 = naik 1 oktav.",
                'chord_mode': {'off': "Off: Main nada tunggal.", 'octave': "Octave: Tambah nada (+12).", 'major': "Major: Chord Mayor (1-3-5).", 'minor': "Minor: Chord Minor (1-3b-5).", 'power': "Power: Power chord (1-5)."},
                'arp_mode': {'off': "Off: Normal.", 'up': "Up: Nada rendah ke tinggi.", 'down': "Down: Nada tinggi ke rendah.", 'random': "Random: Nada acak."},
                'vel_curve': {'linear': "Linear: Standar.", 'soft': "Soft: Sensitif/Ballad.", 'hard': "Hard: Berat/Rock.", 'fixed': "Fixed: Dikunci di 100."},
            }
            selected_key = fields[engine.editor_field_idx][0]
            help_data = field_help.get(selected_key, "")
            desc_text = help_data.get(layer.get(selected_key), help_data) if isinstance(help_data, dict) else help_data
            
            stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
            stdscr.addstr(h-5, 4, f"💡 INFO: {desc_text[:w-15]}")
            stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)

            stdscr.attron(curses.color_pair(7) | curses.A_BOLD); stdscr.addstr(h-2, 0, " "*(w-1)); stdscr.addstr(h-2, max(0, (w//2)-25), " [Arrows] Edit  [TAB] Layer  [S] Save  [A] Save As  [F2] Close "); stdscr.attroff(curses.color_pair(7))
            stdscr.refresh(); ek = stdscr.getch()
            if ek == curses.KEY_F2 or ek == 27: engine.show_editor = False
            elif ek == 9: engine.editor_layer_idx = (engine.editor_layer_idx + 1) % 16
            elif ek == curses.KEY_UP: engine.editor_field_idx = (engine.editor_field_idx - 1) % len(fields)
            elif ek == curses.KEY_DOWN: engine.editor_field_idx = (engine.editor_field_idx + 1) % len(fields)
            elif ek in [curses.KEY_LEFT, curses.KEY_RIGHT]:
                key, label, opts = fields[engine.editor_field_idx]
                curr_idx = opts.index(layer.get(key)); step = 1 if ek == curses.KEY_RIGHT else -1; layer[key] = opts[(curr_idx + step) % len(opts)]
                if key == 'program': layer['name'] = engine.gm_instruments[layer['program']]
                if engine.running: engine.update_all_layer_parameters()
            elif ek == ord('s'):
                if engine.current_preset_name not in ["None", "New Preset"]: config.save_preset(engine.current_preset_name); engine.show_editor = False
                else:
                    stdscr.addstr(h-2, 2, " SAVE NEW: ", curses.color_pair(8)); stdscr.refresh(); curses.echo(); curses.curs_set(1); stdscr.nodelay(0)
                    fname = stdscr.getstr(h-2, 13, 20).decode('utf-8').strip(); stdscr.nodelay(1); curses.noecho(); curses.curs_set(0)
                    if fname: 
                        if not fname.endswith('.cfg'): fname += '.cfg'
                        config.save_preset(fname); engine.current_preset_name = fname; engine.show_editor = False
            continue

        # Logs Area
        stdscr.addstr(h-9, 2, "LOGS:", curses.A_BOLD | curses.color_pair(3))
        for i, note in enumerate(engine.notifications): stdscr.addstr(h-8+i, 4, f"• {note}", curses.A_DIM)
            
        # Footer
        try:
            footer = " [F1] Help  [F2] Editor  [F3] New  [F4] Visual  [S] Start/Stop  [L] Presets  [Q] Quit "
            stdscr.attron(curses.color_pair(7) | curses.A_BOLD); stdscr.addstr(h-1, 0, " "*(w-1)); stdscr.addstr(h-1, max(0, (w//2)-(len(footer)//2)), footer[:w-1]); stdscr.attroff(curses.color_pair(7))
        except: pass
        
        stdscr.refresh(); k = stdscr.getch()
        if k != -1: engine.last_key_time = time.time(); engine.last_key_name = curses.keyname(k).decode()
        if k == ord('q'): config.save_settings(); engine.stop(); break
        elif k == curses.KEY_F1: engine.show_help = not engine.show_help
        elif k == curses.KEY_F2:
            engine.show_editor = not engine.show_editor
            if engine.show_editor: engine.editor_layer_idx = 0; engine.editor_field_idx = 0
        elif k == curses.KEY_F3:
            for i in range(16): engine.layers[i] = engine._default_layer_config(i, engine.gm_instruments); engine.layers[i]['name'] = engine.gm_instruments[0]
            engine.current_preset_name = "New Preset"; engine.editor_layer_idx = 0; engine.editor_field_idx = 0; engine.add_notification("Clean Preset Initialized"); engine.show_editor = True
        elif k == curses.KEY_F4: engine.show_visualizer = not engine.show_visualizer; engine.particles = []
        elif engine.show_help and k != -1: engine.show_help = False
        elif k == ord('m'): engine.show_monitor = not engine.show_monitor
        elif k == ord('a'): engine.auto_panic = not engine.auto_panic; config.save_settings()
        elif k == ord('f'): engine.global_fixed_vel = not engine.global_fixed_vel; config.save_settings()
        elif k == ord('o'): engine.sustain_enabled = not engine.sustain_enabled; config.save_settings()
        elif k == ord('['): engine.master_transpose -= 1; config.save_settings()
        elif k == ord(']'): engine.master_transpose += 1; config.save_settings()
        elif k == 9:
            idx = [i for i, l in enumerate(engine.layers) if l['active']]
            if idx: engine.selected_layer_idx = idx[(idx.index(engine.selected_layer_idx)+1)%len(idx)] if engine.selected_layer_idx in idx else idx[0]
        elif k in [ord('+'), ord('=')]:
            l = engine.layers[engine.selected_layer_idx]; l['volume'] = min(127, l['volume']+5); engine.update_all_layer_parameters()
        elif k in [ord('-'), ord('_')]:
            l = engine.layers[engine.selected_layer_idx]; l['volume'] = max(0, l['volume']-5); engine.update_all_layer_parameters()
        elif k == ord('s'):
            if engine.running: engine.stop()
            else:
                in_p, out_p = engine.available_in_ports, engine.available_out_ports
                if in_p and out_p: engine.start(in_p[in_idx], out_p[out_idx])
        elif k == ord('p'): engine.panic()
        elif k == ord('l'):
            presets = sorted([f for f in os.listdir("presets") if f.endswith('.cfg')])
            if presets:
                p_idx = engine.preset_index
                while True:
                    stdscr.erase(); stdscr.addstr(2, 2, " SELECT PRESET (Enter/Esc) ", curses.color_pair(7) | curses.A_BOLD)
                    for i, p in enumerate(presets):
                        attr = curses.color_pair(8) if i == p_idx else curses.A_NORMAL
                        if 4+i < h-2: stdscr.addstr(4+i, 4, f" {p} ", attr)
                    stdscr.refresh(); pk = stdscr.getch()
                    if pk == curses.KEY_UP: p_idx = (p_idx - 1) % len(presets)
                    elif pk == curses.KEY_DOWN: p_idx = (p_idx + 1) % len(presets)
                    elif pk == 10: engine.preset_index = p_idx; config.load_preset(presets[p_idx]); config.save_settings(); break
                    elif pk == 27: break
        elif k == ord('1'):
            in_p = engine.available_in_ports
            if in_p: in_idx = (in_idx + 1) % len(in_p); config.save_settings()
        elif k == ord('2'):
            out_p = engine.available_out_ports
            if out_p: out_idx = (out_idx + 1) % len(out_p); config.save_settings()
        elif k == ord('x'): engine.disable_splits = not engine.disable_splits
        elif k in [curses.KEY_UP, curses.KEY_DOWN]:
            presets = sorted([f for f in os.listdir("presets") if f.endswith('.cfg')])
            if presets:
                engine.preset_index = (engine.preset_index + (1 if k == curses.KEY_DOWN else -1)) % len(presets)
                config.load_preset(presets[engine.preset_index]); config.save_settings()
        time.sleep(0.03)
