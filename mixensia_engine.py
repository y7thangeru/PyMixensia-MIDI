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

    def _default_layer_config(self, i):
        return {
            'name': f'Layer {i+1}', 'active': False, 'channel': i, 'program': 0,
            'bank_msb': 0, 'bank_lsb': 0, 'volume': 100, 'transpose': 0, 'hold_mode': 'normal',
            'min_note': 0, 'max_note': 127, 'min_vel': 0, 'max_vel': 127,
            'fade_in_start': 0, 'fade_in_end': 0, 
            'fade_out_start': 127, 'fade_out_end': 127,
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
            self.panic()
            self.outport.close()
        self.add_notification("Engine STOPPED")

    def _loop(self):
        for msg in self.inport:
            if not self.running: break
            self.process_message(msg)

    def process_message(self, msg):
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

            if not (layer['min_vel'] <= velocity <= layer['max_vel']): continue
            if calculated_vel <= 0: continue

            target_note = physical_note + layer['transpose']
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
        stdscr.clear()
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

        stdscr.addstr(4, 2, "1. Input Port:  " + (in_ports[in_idx] if in_ports else "N/A"))
        stdscr.addstr(5, 2, "2. Output Port: " + (out_ports[out_idx] if out_ports else "N/A"))
        
        stdscr.addstr(7, 2, "Active Layers:", curses.A_UNDERLINE)
        row = 8
        for layer in engine.layers:
            if layer['active']:
                if row < h - 10:
                    ens_tag = f" [{layer['ensemble_mode'].upper()}]" if layer['ensemble_mode'] != 'off' else ""
                    stdscr.addstr(row, 4, f"- {layer['name']}{ens_tag} (Ch:{layer['channel']+1} PGM:{layer['program']} Vol:{layer['volume']})")
                    row += 1
        
        if time.time() - engine.last_key_time < 0.2:
            anim_text = f" KEY PRESSED: [{engine.last_key_name}] "
            stdscr.addstr(2, w - len(anim_text) - 2, anim_text, curses.color_pair(4) | curses.A_REVERSE)

        stdscr.addstr(h-9, 2, "Log / Notifications:", curses.A_DIM)
        for i, note in enumerate(engine.notifications):
            stdscr.addstr(h-8+i, 4, note, curses.A_DIM)

        instr = "[S] Start  [L] List  [X] Splits  [P] Panic  [UP/DN] Quick Preset  [Q] Quit"
        stdscr.addstr(h-2, 2, instr, curses.A_REVERSE)

        stdscr.refresh()
        k = stdscr.getch()

        if k != -1:
            engine.last_key_time = time.time()
            engine.last_key_name = curses.keyname(k).decode()

        if k == ord('q'):
            engine.stop()
            break
        elif k == ord('s'):
            if engine.running:
                engine.stop()
            else:
                in_ports = mido.get_input_names()
                out_ports = mido.get_output_names()
                if in_ports and out_ports:
                    engine.start(in_ports[in_idx], out_ports[out_idx])
                else:
                    engine.add_notification("Error: No MIDI ports found")
        elif k == ord('p'):
            engine.panic()
        elif k == ord('l'):
            presets = sorted([f for f in os.listdir("presets") if f.endswith('.cfg')])
            if presets:
                p_idx = engine.preset_index
                if p_idx >= len(presets): p_idx = 0
                while True:
                    stdscr.clear()
                    h, w = stdscr.getmaxyx()
                    max_rows = h - 10
                    stdscr.addstr(2, 2, "Select Preset (Enter to confirm, Esc to cancel):", curses.A_BOLD)
                    start_idx = max(0, p_idx - max_rows // 2)
                    end_idx = min(len(presets), start_idx + max_rows)
                    for i in range(start_idx, end_idx):
                        p = presets[i]
                        attr = curses.A_REVERSE if i == p_idx else curses.A_NORMAL
                        if 4 + (i - start_idx) < h - 2:
                            stdscr.addstr(4 + (i - start_idx), 4, f" {p} "[:w-10], attr)
                    stdscr.refresh()
                    pk = stdscr.getch()
                    if pk == curses.KEY_UP: p_idx = (p_idx - 1) % len(presets)
                    elif pk == curses.KEY_DOWN: p_idx = (p_idx + 1) % len(presets)
                    elif pk == 10:
                        engine.preset_index = p_idx
                        engine.load_preset(presets[p_idx])
                        break
                    elif pk == 27: break
        elif k == ord('1'):
            in_ports = mido.get_input_names()
            if in_ports: in_idx = (in_idx + 1) % len(in_ports)
            engine.add_notification(f"Input Port selected: {in_ports[in_idx]}")
        elif k == ord('2'):
            out_ports = mido.get_output_names()
            if out_ports: out_idx = (out_idx + 1) % len(out_ports)
            engine.add_notification(f"Output Port selected: {out_ports[out_idx]}")
        elif k == ord('x'):
            engine.disable_splits = not engine.disable_splits
            state = "DISABLED (Full)" if engine.disable_splits else "ENABLED (Zones)"
            engine.add_notification(f"Keyboard Splits {state}")
        elif k == curses.KEY_UP or k == curses.KEY_DOWN:
            presets = sorted([f for f in os.listdir("presets") if f.endswith('.cfg')])
            if presets:
                if k == curses.KEY_UP:
                    engine.preset_index = (engine.preset_index - 1) % len(presets)
                else:
                    engine.preset_index = (engine.preset_index + 1) % len(presets)
                engine.load_preset(presets[engine.preset_index])
            
        time.sleep(0.01)

if __name__ == "__main__":
    engine = MixensiaEngine()
    engine.load_preset("01_Klasik_Piano_12L.cfg")
    curses.wrapper(draw_menu, engine)
