import json
import os
import mido
import threading
import time
import sys
import curses
from collections import deque

class MixensiaEngine:
    def __init__(self):
        self.inport = None
        self.outport = None
        self.running = False
        self.preset_dir = "presets"
        self.current_preset_name = "None"
        self.preset_index = 0 
        self.disable_splits = False # Global split toggle
        self.notifications = deque(maxlen=5) 
        self.midi_monitor = deque(maxlen=10) # Raw MIDI messages
        self.show_monitor = False
        self.show_help = False
        self.show_editor = False
        self.editor_layer_idx = 0
        self.editor_field_idx = 0
        self.auto_panic = True # Panic when engine stops
        self.global_fixed_vel = False # Force fixed velocity globally
        self.sustain_enabled = True # Toggle pedal detection
        self.master_transpose = 0
        self.selected_layer_idx = 0
        self.last_key_name = ""
        self.last_key_time = 0
        
        if not os.path.exists(self.preset_dir):
            os.makedirs(self.preset_dir)
        
        self.layers = []
        for i in range(16):
            self.layers.append(self._default_layer_config(i))
        
        self.active_notes_physically_held = {} # physical_note -> velocity
        self.notes_sent_to_layers = {} # physical_note -> list of (layer_index, sent_note)
        self.sustain_active = False
        self.gm_instruments = [
            "Acoustic Grand Piano", "Bright Acoustic Piano", "Electric Grand Piano", "Honky-tonk Piano",
            "Electric Piano 1", "Electric Piano 2", "Harpsichord", "Clavi",
            "Celesta", "Glockenspiel", "Music Box", "Vibraphone", "Marimba", "Xylophone", "Tubular Bells", "Dulcimer",
            "Drawbar Organ", "Percussive Organ", "Rock Organ", "Church Organ", "Reed Organ", "Accordion", "Harmonica", "Tango Accordion",
            "Acoustic Guitar (nylon)", "Acoustic Guitar (steel)", "Electric Guitar (jazz)", "Electric Guitar (clean)",
            "Electric Guitar (muted)", "Overdriven Guitar", "Distortion Guitar", "Guitar harmonics",
            "Acoustic Bass", "Electric Bass (finger)", "Electric Bass (pick)", "Fretless Bass", "Slap Bass 1", "Slap Bass 2", "Synth Bass 1", "Synth Bass 2",
            "Violin", "Viola", "Cello", "Contrabass", "Tremolo Strings", "Pizzicato Strings", "Orchestral Harp", "Timpani",
            "String Ensemble 1", "String Ensemble 2", "SynthStrings 1", "SynthStrings 2", "Choir Aahs", "Voice Oohs", "Synth Voice", "Orchestra Hit",
            "Trumpet", "Trombone", "Tuba", "Muted Trumpet", "French Horn", "Brass Section", "SynthBrass 1", "SynthBrass 2",
            "Soprano Sax", "Alto Sax", "Tenor Sax", "Baritone Sax", "Oboe", "English Horn", "Bassoon", "Clarinet",
            "Piccolo", "Flute", "Recorder", "Pan Flute", "Blown Bottle", "Shakuhachi", "Whistle", "Ocarina",
            "Lead 1 (square)", "Lead 2 (sawtooth)", "Lead 3 (calliope)", "Lead 4 (chiff)", "Lead 5 (charang)", "Lead 6 (voice)", "Lead 7 (fifths)", "Lead 8 (bass + lead)",
            "Pad 1 (new age)", "Pad 2 (warm)", "Pad 3 (polysynth)", "Pad 4 (choir)", "Pad 5 (bowed)", "Pad 6 (metallic)", "Pad 7 (halo)", "Pad 8 (sweep)",
            "FX 1 (rain)", "FX 2 (soundtrack)", "FX 3 (crystal)", "FX 4 (atmosphere)", "FX 5 (brightness)", "FX 6 (goblins)", "FX 7 (echoes)", "FX 8 (sci-fi)",
            "Sitar", "Banjo", "Shamisen", "Koto", "Kalimba", "Bag pipe", "Fiddle", "Shanai",
            "Tinkle Bell", "Agogo", "Steel Drums", "Woodblock", "Taiko Drum", "Melodic Tom", "Synth Drum", "Reverse Cymbal",
            "Guitar Fret Noise", "Breath Noise", "Seashore", "Bird Tweet", "Telephone Ring", "Helicopter", "Applause", "Gunshot"
        ]

    def _default_layer_config(self, i):
        return {
            'name': f'Layer {i+1}', 'active': (i == 0), 'channel': i, 'program': 0,
            'bank_msb': 0, 'bank_lsb': 0, 'volume': 100, 'transpose': 0, 'hold_mode': 'normal',
            'min_note': 0, 'max_note': 127, 'min_vel': 0, 'max_vel': 127,
            'fade_in_start': 0, 'fade_in_end': 0, 
            'fade_out_start': 127, 'fade_out_end': 127,
            'vel_curve': 'linear', # 'linear', 'soft', 'hard', 'fixed'
            'ensemble_mode': 'off' # 'off', 'top', 'bottom', 'middle'
        }

    def add_notification(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        self.notifications.append(f"[{timestamp}] {msg}")

    def save_preset(self, filename):
        if not filename.endswith('.cfg'): filename += '.cfg'
        filepath = os.path.join(self.preset_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(self.layers, f, indent=4)
        self.add_notification(f"Preset saved: {filename}")

    def load_preset(self, filename):
        filepath = os.path.join(self.preset_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                loaded_layers = json.load(f)
                for i, layer in enumerate(loaded_layers):
                    default = self._default_layer_config(i)
                    for key, val in default.items():
                        if key not in layer: layer[key] = val
                    
                    # Forcefully sync layer name with the loaded program to ensure old generic presets are updated
                    # Only do this if the name looks like a generic 'Layer X' or we just want strict GM names
                    # For a consistent experience, we will sync it to the GM instrument name.
                    if 'program' in layer:
                        pgm = layer['program']
                        if 0 <= pgm < len(self.gm_instruments):
                            # If the name is generic, update it. If user made a very specific custom name, we might overwrite it here, 
                            # but to solve the user's issue, enforcing the instrument name is best.
                            if layer.get('name', '').startswith('Layer ') or layer.get('name') == 'Acoustic Grand Piano':
                                layer['name'] = self.gm_instruments[pgm]

                self.layers = loaded_layers
            self.current_preset_name = filename
            if self.running:
                self.update_all_layer_parameters()
            self.add_notification(f"Preset loaded: {filename}")
            return True
        return False

    def update_all_layer_parameters(self):
        if not self.outport: return
        for layer in self.layers:
            if layer['active']:
                ch = layer['channel']
                self.outport.send(mido.Message('control_change', channel=ch, control=0, value=layer.get('bank_msb', 0)))
                self.outport.send(mido.Message('control_change', channel=ch, control=32, value=layer.get('bank_lsb', 0)))
                self.outport.send(mido.Message('program_change', channel=ch, program=layer['program']))
                self.outport.send(mido.Message('control_change', channel=ch, control=7, value=layer['volume']))

    def panic(self):
        if self.outport:
            for ch in range(16):
                self.outport.send(mido.Message('control_change', channel=ch, control=123, value=0))
                self.outport.send(mido.Message('control_change', channel=ch, control=64, value=0))
            self.add_notification("PANIC: All notes off")

    def start(self, in_name, out_name):
        try:
            self.inport = mido.open_input(in_name)
            self.outport = mido.open_output(out_name)
            self.running = True
            self.update_all_layer_parameters()
            threading.Thread(target=self._loop, daemon=True).start()
            self.add_notification(f"Engine STARTED on {in_name}")
            return True
        except Exception as e:
            self.add_notification(f"Error starting: {str(e)}")
            return False

    def stop(self):
        self.running = False
        if self.inport: self.inport.close()
        if self.outport: 
            if self.auto_panic: self.panic()
            self.outport.close()
        self.add_notification("Engine STOPPED")

    def _loop(self):
        for msg in self.inport:
            if not self.running: break
            self.process_message(msg)

    def process_message(self, msg):
        # MIDI Monitor
        self.midi_monitor.append(f"CH{msg.channel if hasattr(msg, 'channel') else '-'}: {msg.type.upper()} {str(msg).split(' ', 1)[1] if ' ' in str(msg) else ''}")

        if msg.type == 'note_on' and msg.velocity > 0:
            self.handle_note_on(msg)
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            self.handle_note_off(msg)
        elif msg.type == 'control_change' and msg.control == 64:
            self.handle_sustain(msg)
        elif msg.type in ['pitchwheel', 'aftertouch', 'control_change']:
            for layer in self.layers:
                if layer['active']:
                    self.outport.send(msg.copy(channel=layer['channel']))

    def handle_note_on(self, msg):
        physical_note = msg.note
        velocity = msg.velocity
        
        if self.sustain_active:
            notes_to_kill = [n for n in self.notes_sent_to_layers if n not in self.active_notes_physically_held]
            if len(notes_to_kill) > 4: 
                for note in notes_to_kill: self.kill_note_on_layers(note, smart_only=True)

        self.active_notes_physically_held[physical_note] = velocity
        sorted_notes = sorted(self.active_notes_physically_held.keys())
        
        sent_list = []
        for i, layer in enumerate(self.layers):
            if not layer['active']: continue
            
            note_match = self.disable_splits or (layer['min_note'] <= physical_note <= layer['max_note'])
            if not note_match: continue
            
            mode = layer.get('ensemble_mode', 'off')
            if mode == 'top' and physical_note != sorted_notes[-1]: continue
            if mode == 'bottom' and physical_note != sorted_notes[0]: continue
            if mode == 'middle' and (physical_note == sorted_notes[0] or physical_note == sorted_notes[-1]) and len(sorted_notes) > 2: continue

            calculated_vel = velocity
            fi_s, fi_e = layer.get('fade_in_start', 0), layer.get('fade_in_end', 0)
            fo_s, fo_e = layer.get('fade_out_start', 127), layer.get('fade_out_end', 127)
            
            if fi_e > fi_s and velocity < fi_e:
                factor = (velocity - fi_s) / (fi_e - fi_s)
                calculated_vel = int(velocity * max(0, min(1, factor)))
            if fo_e > fo_s and velocity > fo_s:
                factor = (fo_e - velocity) / (fo_e - fo_s)
                calculated_vel = int(velocity * max(0, min(1, factor)))

            # Velocity Curves
            curve = layer.get('vel_curve', 'linear')
            if curve == 'soft':
                calculated_vel = int(127 * (calculated_vel / 127)**1.5)
            elif curve == 'hard':
                calculated_vel = int(127 * (calculated_vel / 127)**0.5)
            elif curve == 'fixed':
                calculated_vel = 100

            if self.global_fixed_vel:
                calculated_vel = 110

            if not (layer['min_vel'] <= velocity <= layer['max_vel']): continue
            if calculated_vel <= 0: continue
            if calculated_vel > 127: calculated_vel = 127

            target_note = physical_note + layer['transpose'] + self.master_transpose
            if 0 <= target_note <= 127:
                self.outport.send(msg.copy(channel=layer['channel'], note=target_note, velocity=calculated_vel))
                sent_list.append((i, target_note))
        self.notes_sent_to_layers[physical_note] = sent_list

    def handle_note_off(self, msg):
        physical_note = msg.note
        if physical_note in self.active_notes_physically_held:
            del self.active_notes_physically_held[physical_note]
        if not self.sustain_active:
            self.kill_note_on_layers(physical_note)

    def handle_sustain(self, msg):
        if not self.sustain_enabled: return
        self.sustain_active = msg.value >= 64
        for layer in self.layers:
            if layer['active']: self.outport.send(msg.copy(channel=layer['channel']))
        if not self.sustain_active:
            notes_to_kill = [n for n in self.notes_sent_to_layers if n not in self.active_notes_physically_held]
            for note in notes_to_kill: self.kill_note_on_layers(note)

    def kill_note_on_layers(self, physical_note, smart_only=False):
        if physical_note in self.notes_sent_to_layers:
            remaining = []
            for layer_idx, sent_note in self.notes_sent_to_layers[physical_note]:
                layer = self.layers[layer_idx]
                if not smart_only or layer['hold_mode'] == 'smart':
                    self.outport.send(mido.Message('note_off', channel=layer['channel'], note=sent_note, velocity=0))
                else:
                    remaining.append((layer_idx, sent_note))
            if not remaining: del self.notes_sent_to_layers[physical_note]
            else: self.notes_sent_to_layers[physical_note] = remaining

def draw_menu(stdscr, engine):
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

        title = " PyMixensia MIDI Engine (CLI Mode) "
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
                ('vel_curve', 'Velocity Curve', ['linear', 'soft', 'hard', 'fixed']),
                ('hold_mode', 'Hold Mode', ['normal', 'smart']),
                ('ensemble_mode', 'Ensemble Mode', ['off', 'top', 'bottom', 'middle']),
                ('min_note', 'Min Note', list(range(128))),
                ('max_note', 'Max Note', list(range(128))),
                ('min_vel', 'Min Velocity', list(range(128))),
                ('max_vel', 'Max Velocity', list(range(128))),
            ]
            for i, (key, label, options) in enumerate(fields):
                attr = curses.A_REVERSE if i == engine.editor_field_idx else curses.A_NORMAL
                val = layer.get(key, "-")
                disp_val = "ON" if val is True else ("OFF" if val is False else str(val))
                if key == 'channel': disp_val = str(val + 1)
                if key == 'program':
                    instr_name = engine.gm_instruments[val] if val < len(engine.gm_instruments) else "Unknown"
                    disp_val = f"{val} ({instr_name})"
                stdscr.addstr(4 + i, 4, f"{label:<20} : {disp_val}", attr)
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
                    if engine.running: engine.update_all_layer_parameters()
            elif ek == ord('s'):
                # SMART SAVE: If it's an existing preset, overwrite. If new, ask for filename.
                if engine.current_preset_name not in ["None", "New Preset"]:
                    engine.save_preset(engine.current_preset_name)
                    engine.show_editor = False
                else:
                    stdscr.addstr(h-2, 2, "Save New Preset As (filename): ", curses.A_BOLD)
                    stdscr.refresh()
                    curses.echo(); curses.curs_set(1); stdscr.nodelay(0)
                    fname_bytes = stdscr.getstr(h-2, 33, 40)
                    stdscr.nodelay(1); curses.noecho(); curses.curs_set(0)
                    fname = fname_bytes.decode('utf-8').strip()
                    if fname:
                        if not fname.endswith('.cfg'): fname += '.cfg'
                        engine.save_preset(fname)
                        engine.current_preset_name = fname
                        engine.show_editor = False
            elif ek == ord('a'):
                # EXPLICIT SAVE AS: Always ask for filename
                stdscr.addstr(h-2, 2, "Save Copy As (filename): ", curses.A_BOLD)
                stdscr.refresh()
                curses.echo(); curses.curs_set(1); stdscr.nodelay(0)
                fname_bytes = stdscr.getstr(h-2, 27, 40)
                stdscr.nodelay(1); curses.noecho(); curses.curs_set(0)
                fname = fname_bytes.decode('utf-8').strip()
                if fname:
                    if not fname.endswith('.cfg'): fname += '.cfg'
                    engine.save_preset(fname)
                    engine.current_preset_name = fname
                    engine.show_editor = False
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
        if k == ord('q'): engine.stop(); break
        elif k == curses.KEY_F1: engine.show_help = not engine.show_help
        elif k == curses.KEY_F2:
            engine.show_editor = not engine.show_editor
            if engine.show_editor:
                engine.editor_layer_idx = 0
                engine.editor_field_idx = 0
        elif k == curses.KEY_F3:
            for i in range(16): 
                engine.layers[i] = engine._default_layer_config(i)
                engine.layers[i]['name'] = engine.gm_instruments[0]
            engine.current_preset_name = "New Preset"
            engine.editor_layer_idx = 0
            engine.editor_field_idx = 0
            engine.add_notification("Clean Preset Initialized")
            engine.show_editor = True
        elif engine.show_help and k != -1: engine.show_help = False
        elif k == ord('m'): engine.show_monitor = not engine.show_monitor
        elif k == ord('a'): engine.auto_panic = not engine.auto_panic; engine.add_notification(f"Auto-Panic: {'ON' if engine.auto_panic else 'OFF'}")
        elif k == ord('f'): engine.global_fixed_vel = not engine.global_fixed_vel; engine.add_notification(f"Global Fixed Velocity: {'ON' if engine.global_fixed_vel else 'OFF'}")
        elif k == ord('o'): engine.sustain_enabled = not engine.sustain_enabled; engine.add_notification(f"Sustain: {'ON' if engine.sustain_enabled else 'OFF'}")
        elif k == ord('['): engine.master_transpose -= 1; engine.add_notification(f"Transpose: {engine.master_transpose}")
        elif k == ord(']'): engine.master_transpose += 1; engine.add_notification(f"Transpose: {engine.master_transpose}")
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
                    elif pk == 10: engine.preset_index = p_idx; engine.load_preset(presets[p_idx]); break
                    elif pk == 27: break
        elif k == ord('1'):
            in_p = mido.get_input_names()
            if in_p: in_idx = (in_idx + 1) % len(in_p); engine.add_notification(f"In: {in_p[in_idx]}")
        elif k == ord('2'):
            out_p = mido.get_output_names()
            if out_p: out_idx = (out_idx + 1) % len(out_p); engine.add_notification(f"Out: {out_p[out_idx]}")
        elif k == ord('x'):
            engine.disable_splits = not engine.disable_splits; engine.add_notification(f"Splits {'OFF' if engine.disable_splits else 'ON'}")
        elif k in [curses.KEY_UP, curses.KEY_DOWN]:
            presets = sorted([f for f in os.listdir("presets") if f.endswith('.cfg')])
            if presets:
                engine.preset_index = (engine.preset_index + (1 if k == curses.KEY_DOWN else -1)) % len(presets)
                engine.load_preset(presets[engine.preset_index])
        time.sleep(0.03)

if __name__ == "__main__":
    engine = MixensiaEngine()
    engine.load_preset("01_Klasik_Piano_6L.cfg")
    curses.wrapper(draw_menu, engine)


if __name__ == "__main__":
    engine = MixensiaEngine()
    engine.load_preset("01_Klasik_Piano_6L.cfg")
    curses.wrapper(draw_menu, engine)
