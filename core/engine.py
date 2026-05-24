import mido
import threading
import time
from collections import deque

class MixensiaEngine:
    def __init__(self, gm_instruments):
        self.inport = None
        self.outport = None
        self.running = False
        self.current_preset_name = "None"
        self.preset_index = 0 
        self.disable_splits = False
        self.notifications = deque(maxlen=5) 
        self.midi_monitor = deque(maxlen=10)
        self.show_monitor = False
        self.show_help = False
        self.show_editor = False
        self.editor_layer_idx = 0
        self.editor_field_idx = 0
        self.last_key_name = ""
        self.last_key_time = 0
        
        self.layers = []
        for i in range(16):
            self.layers.append(self._default_layer_config(i, gm_instruments))
        
        self.active_notes_physically_held = {}
        self.notes_sent_to_layers = {}
        self.sustain_active = False
        self.gm_instruments = gm_instruments

        # Extended States
        self.auto_panic = True
        self.global_fixed_vel = False
        self.sustain_enabled = True
        self.master_transpose = 0
        self.selected_layer_idx = 0
        
        self.arp_running = True
        self.arp_tempo = 120
        self.arp_thread = threading.Thread(target=self._arp_loop, daemon=True)
        self.arp_thread.start()
        
        self.last_in_name = None
        self.last_out_name = None
        self.reconnect_thread = threading.Thread(target=self._auto_reconnect_loop, daemon=True)
        self.reconnect_thread.start()

    def _auto_reconnect_loop(self):
        while True:
            if self.running and (self.last_in_name or self.last_out_name):
                # Check if ports are still available
                try:
                    in_names = mido.get_input_names()
                    out_names = mido.get_output_names()
                    
                    needs_reconnect = False
                    if self.last_in_name and self.last_in_name not in in_names: needs_reconnect = True
                    if self.last_out_name and self.last_out_name not in out_names: needs_reconnect = True
                    
                    if needs_reconnect:
                        self.add_notification("Connection Lost! Attempting reconnect...")
                        self._do_reconnect(in_names, out_names)
                except: pass
            time.sleep(2.0)

    def _arp_loop(self):
        # Basic Arpeggiator Loop
        step = 0
        while True:
            if self.running and self.arp_running:
                interval = 60.0 / self.arp_tempo
                # Logic to play notes would go here
                # For now, just maintain the thread and timing
                pass
            time.sleep(0.1)

    def _do_reconnect(self, in_names, out_names):
        try:
            if self.inport: self.inport.close()
            if self.outport: self.outport.close()
            
            if self.last_in_name in in_names and self.last_out_name in out_names:
                self.inport = mido.open_input(self.last_in_name)
                self.outport = mido.open_output(self.last_out_name)
                self.add_notification("Reconnected successfully.")
                self.update_all_layer_parameters()
        except: pass

    def _default_layer_config(self, i, gm_instruments):
        return {
            'name': gm_instruments[0] if gm_instruments else f'Layer {i+1}', 
            'active': (i == 0), 'channel': i, 'program': 0,
            'bank_msb': 0, 'bank_lsb': 0, 'volume': 100, 'transpose': 0, 'hold_mode': 'normal',
            'min_note': 0, 'max_note': 127, 'min_vel': 0, 'max_vel': 127,
            'fade_in_start': 0, 'fade_in_end': 0, 
            'fade_out_start': 127, 'fade_out_end': 127,
            'vel_curve': 'linear',
            'ensemble_mode': 'off',
            'chord_mode': 'off', # 'off', 'octave', 'major', 'minor', 'power'
            'arp_mode': 'off', # 'off', 'up', 'down', 'random'
            'arp_rate': 0.25 # 1/4, 0.125 for 1/8, etc.
        }

    def add_notification(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        self.notifications.append(f"[{timestamp}] {msg}")

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
            self.last_in_name = in_name
            self.last_out_name = out_name
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
                # Core note
                self.outport.send(msg.copy(channel=layer['channel'], note=target_note, velocity=calculated_vel))
                sent_list.append((i, target_note))
                
                # Smart Chords
                chord = layer.get('chord_mode', 'off')
                intervals = []
                if chord == 'octave': intervals = [12]
                elif chord == 'major': intervals = [4, 7]
                elif chord == 'minor': intervals = [3, 7]
                elif chord == 'power': intervals = [7, 12]
                
                for interval in intervals:
                    extra_note = target_note + interval
                    if 0 <= extra_note <= 127:
                        self.outport.send(msg.copy(channel=layer['channel'], note=extra_note, velocity=calculated_vel))
                        sent_list.append((i, extra_note))
                        
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
