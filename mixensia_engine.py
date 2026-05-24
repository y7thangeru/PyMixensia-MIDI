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
        self.disable_splits = False
        self.notifications = deque(maxlen=5) 
        self.last_key_name = ""
        self.last_key_time = 0
        
        # Background Port Detection (Anti-Hang)
        self.available_in_ports = []
        self.available_out_ports = []
        threading.Thread(target=self._port_scanner, daemon=True).start()
        
        if not os.path.exists(self.preset_dir):
            os.makedirs(self.preset_dir)
        
        self.layers = []
        for i in range(16):
            self.layers.append(self._default_layer_config(i))
        
        self.active_notes_physically_held = {}
        self.notes_sent_to_layers = {}
        self.sustain_active = False

    def _port_scanner(self):
        while True:
            try:
                self.available_in_ports = mido.get_input_names()
                self.available_out_ports = mido.get_output_names()
            except: pass
            time.sleep(3.0)

    def _default_layer_config(self, i):
        return {
            'name': f'Layer {i+1}', 'active': (i == 0), 'channel': i, 'program': 0,
            'bank_msb': 0, 'bank_lsb': 0, 'volume': 100, 'transpose': 0, 'hold_mode': 'normal',
            'min_note': 0, 'max_note': 127, 'min_vel': 0, 'max_vel': 127
        }

    def add_notification(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        self.notifications.append(f"[{timestamp}] {msg}")

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
            if self.running: self.update_all_layer_parameters()
            self.add_notification(f"Loaded: {filename}")
            return True
        return False

    def update_all_layer_parameters(self):
        if not self.outport: return
        for layer in self.layers:
            if layer['active']:
                ch = layer['channel']
                self.outport.send(mido.Message('program_change', channel=ch, program=layer['program']))
                self.outport.send(mido.Message('control_change', channel=ch, control=7, value=layer['volume']))

    def panic(self):
        if self.outport:
            for ch in range(16):
                self.outport.send(mido.Message('control_change', channel=ch, control=123, value=0))
            self.add_notification("PANIC: All notes off")

    def start(self, in_name, out_name):
        try:
            self.inport = mido.open_input(in_name)
            self.outport = mido.open_output(out_name)
            self.running = True
            self.update_all_layer_parameters()
            threading.Thread(target=self._loop, daemon=True).start()
            self.add_notification(f"STARTED: {in_name}")
            return True
        except Exception as e:
            self.add_notification(f"Error: {str(e)}")
            return False

    def stop(self):
        self.running = False
        if self.inport: self.inport.close()
        if self.outport: self.panic(); self.outport.close()
        self.add_notification("STOPPED")

    def _loop(self):
        for msg in self.inport:
            if not self.running: break
            if msg.type == 'note_on' and msg.velocity > 0:
                self.handle_note_on(msg)
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                self.handle_note_off(msg)
            elif msg.type == 'control_change' and msg.control == 64:
                self.handle_sustain(msg)

    def handle_note_on(self, msg):
        physical_note = msg.note
        velocity = msg.velocity
        self.active_notes_physically_held[physical_note] = velocity
        sent_list = []
        for i, layer in enumerate(self.layers):
            if not layer['active']: continue
            if not (self.disable_splits or (layer['min_note'] <= physical_note <= layer['max_note'])): continue
            if not (layer['min_vel'] <= velocity <= layer['max_vel']): continue
            
            target_note = physical_note + layer['transpose']
            if 0 <= target_note <= 127:
                self.outport.send(msg.copy(channel=layer['channel'], note=target_note))
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
        if not self.sustain_active:
            notes_to_kill = [n for n in self.notes_sent_to_layers if n not in self.active_notes_physically_held]
            for note in notes_to_kill: self.kill_note_on_layers(note)

    def kill_note_on_layers(self, physical_note):
        if physical_note in self.notes_sent_to_layers:
            for layer_idx, sent_note in self.notes_sent_to_layers[physical_note]:
                layer = self.layers[layer_idx]
                self.outport.send(mido.Message('note_off', channel=layer['channel'], note=sent_note, velocity=0))
            del self.notes_sent_to_layers[physical_note]

def draw_menu(stdscr, engine):
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.curs_set(0)
    stdscr.nodelay(1)
    
    in_idx = 0
    out_idx = 0
    
    while True:
        stdscr.erase() # Anti-Flicker fix
        h, w = stdscr.getmaxyx()
        
        in_ports = engine.available_in_ports
        out_ports = engine.available_out_ports

        title = " PyMixensia MIDI Engine (STANDARD) "
        stdscr.addstr(0, (w//2)-(len(title)//2), title, curses.A_REVERSE)

        status = "RUNNING" if engine.running else "STOPPED"
        color = curses.color_pair(1 if engine.running else 2)
        stdscr.addstr(2, 2, f"Status: {status}", color | curses.A_BOLD)
        stdscr.addstr(2, 25, f"Preset: {engine.current_preset_name}", curses.color_pair(3))

        stdscr.addstr(4, 2, f"1. Input Port:  {in_ports[in_idx] if in_ports else 'N/A'}")
        stdscr.addstr(5, 2, f"2. Output Port: {out_ports[out_idx] if out_ports else 'N/A'}")
        
        stdscr.addstr(7, 2, "Active Layers:", curses.A_UNDERLINE)
        row = 8
        for layer in engine.layers:
            if layer['active'] and row < h - 10:
                stdscr.addstr(row, 4, f"- {layer['name']} (Ch:{layer['channel']+1} PGM:{layer['program']} Vol:{layer['volume']})")
                row += 1

        stdscr.addstr(h-8, 2, "Log:", curses.A_DIM)
        for i, note in enumerate(engine.notifications):
            stdscr.addstr(h-7+i, 4, note, curses.A_DIM)

        instr = "[S] Start/Stop  [L] Presets  [P] Panic  [1/2] Switch Ports  [Q] Quit"
        stdscr.addstr(h-1, 0, instr[:w-1], curses.A_REVERSE)

        stdscr.refresh()
        k = stdscr.getch()

        if k == ord('q'): engine.stop(); break
        elif k == ord('s'):
            if engine.running: engine.stop()
            else:
                if in_ports and out_ports: engine.start(in_ports[in_idx], out_ports[out_idx])
        elif k == ord('p'): engine.panic()
        elif k == ord('l'):
            presets = sorted([f for f in os.listdir("presets") if f.endswith('.cfg')])
            if presets:
                p_idx = engine.preset_index
                while True:
                    stdscr.erase()
                    stdscr.addstr(2, 2, "Select Preset (Enter to confirm):", curses.A_BOLD)
                    for i, p in enumerate(presets):
                        attr = curses.A_REVERSE if i == p_idx else curses.A_NORMAL
                        if 4+i < h-2: stdscr.addstr(4+i, 4, f" {p} ", attr)
                    stdscr.refresh()
                    pk = stdscr.getch()
                    if pk == curses.KEY_UP: p_idx = (p_idx - 1) % len(presets)
                    elif pk == curses.KEY_DOWN: p_idx = (p_idx + 1) % len(presets)
                    elif pk == 10: engine.preset_index = p_idx; engine.load_preset(presets[p_idx]); break
                    elif pk == 27: break
        elif k == ord('1') and in_ports: in_idx = (in_idx + 1) % len(in_ports)
        elif k == ord('2') and out_ports: out_idx = (out_idx + 1) % len(out_ports)
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
