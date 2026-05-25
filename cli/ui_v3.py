import mido
import time
import os
import random
import math
from asciimatics.effects import Effect, Stars, Print, Matrix
from asciimatics.renderers import FigletText, Rainbow, StaticRenderer
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, StopApplication, NextScene
from asciimatics.widgets import Frame, Layout, Label, Divider, ListBox, Text, Button, CheckBox, DropdownList, PopUpDialog

class MIDIVisualizer(Effect):
    """
    Custom Asciimatics Effect that renders MIDI notes as 3D-like falling blocks or particles.
    Replicates V2 Modes: 0: Fireworks, 1: Stars, 2: Ripples, 3: Falling, 4: Tetris
    """
    def __init__(self, screen, engine, **kwargs):
        super(MIDIVisualizer, self).__init__(screen, **kwargs)
        self._engine = engine
        self._local_particles = []

    @property
    def stop_frame(self):
        return 0

    def _update(self, frame_no):
        h, w = self._screen.dimensions
        mode = self._engine.visualizer_mode
        
        # Capture engine particles (spawned by MIDI handler)
        while self._engine.particles:
            self._local_particles.append(self._engine.particles.pop(0))

        remaining = []
        for p in self._local_particles:
            # Color mapping
            color_map = {1: Screen.COLOUR_GREEN, 2: Screen.COLOUR_RED, 3: Screen.COLOUR_CYAN, 4: Screen.COLOUR_YELLOW, 5: Screen.COLOUR_MAGENTA, 6: Screen.COLOUR_BLUE}
            color = color_map.get(p.get('color', 1), Screen.COLOUR_WHITE)
            
            if p['type'] == 'firework':
                p['x'] += p['vx']; p['y'] += p['vy']; p['vy'] += 0.1; p['life'] -= 0.02
                if p['life'] > 0 and 0 <= p['x'] < w and 0 <= p['y'] < h:
                    self._screen.print_at(p.get('char', '*'), int(p['x']), int(p['y']), color)
                    remaining.append(p)
            
            elif p['type'] == 'star':
                p['y'] += p.get('vy', 0.5)
                if p['y'] < h:
                    px, py = int(p['x']), int(p['y'])
                    self._screen.print_at("█", px, py, color, attr=Screen.A_BOLD)
                    if py > 0: self._screen.print_at("│", px, py-1, color)
                    if py < h-1: self._screen.print_at("│", px, py+1, color)
                    if px > 0: self._screen.print_at("─", px-1, py, color)
                    if px < w-1: self._screen.print_at("─", px+1, py, color)
                    remaining.append(p)

            elif p['type'] == 'ripple':
                p['radius'] += 0.8; p['life'] -= 0.03
                if p['life'] > 0:
                    for angle in range(0, 360, 30):
                        rx = int(p['x'] + math.cos(math.radians(angle)) * p['radius'] * 2.5)
                        ry = int(p['y'] + math.sin(math.radians(angle)) * p['radius'])
                        if 0 <= rx < w and 0 <= ry < h: self._screen.print_at("█", rx, ry, color)
                    remaining.append(p)

            elif p['type'] == 'falling':
                p['y'] += 0.5
                if p['y'] < h:
                    for i in range(int(p['len'])):
                        yy = int(p['y'] - i)
                        if 0 <= yy < h: self._screen.print_at("█", int(p['x']), yy, color)
                    remaining.append(p)

            elif p['type'] == 'tetris':
                p['y'] += 0.4
                if p['y'] < h:
                    for dy in range(p['h']):
                        for dx in range(p['w']):
                            if 0 <= int(p['y'])-dy < h and 0 <= int(p['x'])+dx < w:
                                self._screen.print_at("█", int(p['x'])+dx, int(p['y'])-dy, color)
                    remaining.append(p)
        
        self._local_particles = remaining

        # Footer Status for Visualizer
        modes = ["ULTRA FIREWORKS", "GIANT CROSS STARS", "RAINBOW RIPPLES", "HEAVY BLOCKS", "TETRIS COLOSSAL"]
        status_text = f" MODE: {modes[mode]} | [Arrows] Change Mode | [ESC/F4] Exit "
        self._screen.print_at(status_text, (w - len(status_text))//2, h-1, Screen.COLOUR_BLACK, bg=Screen.COLOUR_CYAN)

    def process_event(self, event):
        if hasattr(event, 'key_code'):
            if event.key_code == Screen.KEY_RIGHT:
                self._engine.visualizer_mode = (self._engine.visualizer_mode + 1) % 5
                self._local_particles = []
                return None
            elif event.key_code == Screen.KEY_LEFT:
                self._engine.visualizer_mode = (self._engine.visualizer_mode - 1) % 5
                self._local_particles = []
                return None
            elif event.key_code in [ord('q'), 27, Screen.KEY_F4]:
                raise NextScene("Main")
        return event

    def reset(self):
        self._local_particles = []

class MainMenu(Frame):
    def __init__(self, screen, engine, config):
        super(MainMenu, self).__init__(screen, screen.height, screen.width, has_border=True, title=" 🎹 PyMixensia V3 Dashboard 🎹 ")
        self._engine = engine
        self._config = config
        
        layout = Layout([1, 1, 1], fill_frame=True)
        self.add_layout(layout)
        
        # Col 0: Status & Global Controls
        layout.add_widget(Label("--- ENGINE STATUS ---"), 0)
        self._status = Label("OFFLINE")
        layout.add_widget(self._status, 0)
        layout.add_widget(Button("START/STOP (S)", self._toggle_engine), 0)
        layout.add_widget(Divider(), 0)
        
        layout.add_widget(Label("--- GLOBAL SETTINGS ---"), 0)
        self._splits = CheckBox("MIDI Splits", on_change=self._update_engine_settings)
        self._sustain = CheckBox("Sustain Pedal", on_change=self._update_engine_settings)
        self._fixed_vel = CheckBox("Fixed Velocity", on_change=self._update_engine_settings)
        layout.add_widget(self._splits, 0)
        layout.add_widget(self._sustain, 0)
        layout.add_widget(self._fixed_vel, 0)
        
        # Col 1: Preset & Performance
        layout.add_widget(Label("--- CURRENT PRESET ---"), 1)
        self._preset_name = Label("None")
        layout.add_widget(self._preset_name, 1)
        layout.add_widget(Button("LOAD PRESET (L)", self._open_preset_list), 1)
        layout.add_widget(Divider(), 1)
        
        layout.add_widget(Label("--- PERFORMANCE ---"), 1)
        self._master_t = Text("Master Transpose:", readonly=True)
        layout.add_widget(self._master_t, 1)
        layout.add_widget(Button("PANIC! (P)", self._engine.panic), 1)

        # Col 2: Ports & Navigation
        layout.add_widget(Label("--- MIDI PORTS ---"), 2)
        self._in_port = DropdownList([("Scanning...", 0)], label="IN :")
        self._out_port = DropdownList([("Scanning...", 0)], label="OUT:")
        layout.add_widget(self._in_port, 2)
        layout.add_widget(self._out_port, 2)
        layout.add_widget(Divider(), 2)
        
        layout.add_widget(Label("--- NAVIGATION ---"), 2)
        layout.add_widget(Button("OPEN EDITOR (F2)", self._open_editor), 2)
        layout.add_widget(Button("VISUALIZER (F4)", self._open_visualizer), 2)
        layout.add_widget(Button("QUIT (Q)", self._quit), 2)
        
        self.fix()
        self._update_from_engine()

    def _update_from_engine(self):
        self._status.text = ">>> RUNNING <<<" if self._engine.running else "STOPPED"
        self._preset_name.text = self._engine.current_preset_name
        self._splits.value = not self._engine.disable_splits
        self._sustain.value = self._engine.sustain_enabled
        self._fixed_vel.value = self._engine.global_fixed_vel
        self._master_t.value = f"{self._engine.master_transpose:+d}"
        
        # Ports
        in_p = self._engine.available_in_ports
        out_p = self._engine.available_out_ports
        if in_p: self._in_port.options = [(p, i) for i, p in enumerate(in_p)]
        if out_p: self._out_port.options = [(p, i) for i, p in enumerate(out_p)]

    def _update_engine_settings(self):
        self._engine.disable_splits = not self._splits.value
        self._engine.sustain_enabled = self._sustain.value
        self._engine.global_fixed_vel = self._fixed_vel.value
        self._config.save_settings()

    def _toggle_engine(self):
        if self._engine.running:
            self._engine.stop()
        else:
            in_idx = self._in_port.value if self._in_port.value is not None else 0
            out_idx = self._out_port.value if self._out_port.value is not None else 0
            in_p = self._engine.available_in_ports
            out_p = self._engine.available_out_ports
            if in_p and out_p:
                self._engine.start(in_p[in_idx], out_p[out_idx])
        self._update_from_engine()

    def _open_preset_list(self): raise NextScene("Presets")
    def _open_editor(self): raise NextScene("Editor")
    def _open_visualizer(self): raise NextScene("Visualizer")
    def _quit(self):
        self._config.save_settings()
        self._engine.stop()
        raise StopApplication("User quit")

    def process_event(self, event):
        if hasattr(event, 'key_code'):
            if event.key_code == ord('s'): self._toggle_engine()
            elif event.key_code == ord('l'): self._open_preset_list()
            elif event.key_code == ord('p'): self._engine.panic()
            elif event.key_code == ord('q'): self._quit()
            elif event.key_code == ord('['): self._engine.master_transpose -= 1; self._update_from_engine()
            elif event.key_code == ord(']'): self._engine.master_transpose += 1; self._update_from_engine()
            elif event.key_code == Screen.KEY_F2: self._open_editor()
            elif event.key_code == Screen.KEY_F4: self._open_visualizer()
        
        self._update_from_engine()
        return super(MainMenu, self).process_event(event)

class PresetSelector(Frame):
    def __init__(self, screen, engine, config):
        super(PresetSelector, self).__init__(screen, screen.height // 2, screen.width // 2, has_border=True, title=" LOAD PRESET ")
        self._engine = engine
        self._config = config
        
        layout = Layout([1], fill_frame=True)
        self.add_layout(layout)
        
        presets = sorted([f for f in os.listdir("presets") if f.endswith('.cfg')])
        self._list = ListBox(10, [(p, p) for p in presets], on_select=self._load)
        layout.add_widget(self._list)
        
        layout2 = Layout([1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("LOAD", self._load), 0)
        layout2.add_widget(Button("CANCEL", self._back), 1)
        self.fix()

    def _load(self):
        if self._list.value:
            self._config.load_preset(self._list.value)
            self._config.save_settings()
            self._back()

    def _back(self): raise NextScene("Main")

class LayerEditor(Frame):
    def __init__(self, screen, engine, config):
        super(LayerEditor, self).__init__(screen, screen.height, screen.width, has_border=True, title=" 🛠️ LAYER EDITOR 🛠️ ")
        self._engine = engine
        self._config = config
        self._layer_idx = 0
        
        layout = Layout([1, 3, 1], fill_frame=True)
        self.add_layout(layout)
        
        layout.add_widget(Label("SELECT LAYER"), 0)
        self._layer_list = ListBox(16, [(f"Layer {i+1}", i) for i in range(16)], on_change=self._on_layer_change)
        layout.add_widget(self._layer_list, 0)
        
        self._active = CheckBox("Active Status", label="STATUS  :", on_change=self._update_layer)
        self._channel = Text(label="CHANNEL :", on_change=self._update_layer)
        self._program = Text(label="PROGRAM :", on_change=self._update_layer)
        self._volume = Text(label="VOLUME  :", on_change=self._update_layer)
        self._transpose = Text(label="TRANSPOSE:", on_change=self._update_layer)
        
        layout.add_widget(self._active, 1)
        layout.add_widget(self._channel, 1)
        layout.add_widget(self._program, 1)
        layout.add_widget(self._volume, 1)
        layout.add_widget(self._transpose, 1)
        layout.add_widget(Divider(), 1)
        
        layout.add_widget(Label("HELP & INFO"), 2)
        self._info = Label("Use [TAB] to navigate.")
        layout.add_widget(self._info, 2)
        
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("SAVE PRESET", self._save), 0)
        layout2.add_widget(Button("BACK TO MENU", self._back), 3)
        
        self.fix()
        self._on_layer_change()

    def _on_layer_change(self):
        self._layer_idx = self._layer_list.value if self._layer_list.value is not None else 0
        layer = self._engine.layers[self._layer_idx]
        self._active.value = layer['active']
        self._channel.value = str(layer['channel'] + 1)
        self._program.value = str(layer['program'])
        self._volume.value = str(layer['volume'])
        self._transpose.value = str(layer['transpose'])

    def _update_layer(self):
        layer = self._engine.layers[self._layer_idx]
        layer['active'] = self._active.value
        try:
            layer['channel'] = int(self._channel.value) - 1
            layer['program'] = int(self._program.value)
            layer['volume'] = int(self._volume.value)
            layer['transpose'] = int(self._transpose.value)
        except: pass
        if self._engine.running: self._engine.update_all_layer_parameters()

    def _save(self):
        if self._engine.current_preset_name != "None": self._config.save_preset(self._engine.current_preset_name)
    def _back(self): raise NextScene("Main")

def draw_menu_v3(screen, engine, config):
    # Restore V2 Visualizer particle spawning logic
    def visualizer_note_on(msg):
        h, w = screen.dimensions
        x_pos = int((msg.note / 127) * (w - 6)) + 3
        mode = engine.visualizer_mode
        
        if mode == 0: # FIREWORKS
            color = random.randint(1, 6)
            for _ in range(15):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(1.0, 3.0)
                engine.particles.append({'type': 'firework', 'x': float(x_pos), 'y': float(h-4), 'vx': math.cos(angle)*speed*2, 'vy': math.sin(angle)*speed - 2, 'life': 1.5, 'color': color, 'char': random.choice(['█', '▓', '▒'])})
        elif mode == 1: # STARS
            engine.particles.append({'type': 'star', 'x': float(x_pos), 'y': 0.0, 'vy': random.uniform(0.2, 0.4), 'color': random.randint(1, 6)})
        elif mode == 2: # RIPPLES
            engine.particles.append({'type': 'ripple', 'x': x_pos, 'y': h//2, 'radius': 0.0, 'life': 1.0, 'color': random.randint(1, 6)})
        elif mode == 3: # BLOCKS
            engine.particles.append({'type': 'falling', 'x': x_pos, 'y': 0.0, 'len': max(4, msg.velocity//8), 'color': random.randint(1, 6)})
        elif mode == 4: # TETRIS
            engine.particles.append({'type': 'tetris', 'x': x_pos-2, 'y': 0.0, 'w': 5, 'h': 2, 'color': random.randint(1, 6)})
        
        engine._original_handle_note_on(msg)

    if not hasattr(engine, '_original_handle_note_on'):
        engine._original_handle_note_on = engine.handle_note_on
        engine.handle_note_on = visualizer_note_on

    scenes = [
        Scene([
            Stars(screen, screen.width // 2),
            Print(screen, Rainbow(screen, FigletText("PYMIXENSIA V3", font='slant')), screen.height // 2 - 4, stop_frame=80),
            Print(screen, StaticRenderer(["POWERED BY ASCIIMATICS"]), screen.height // 2 + 3, colour=Screen.COLOUR_CYAN, stop_frame=80)
        ], 80, name="Intro"),
        Scene([MainMenu(screen, engine, config)], -1, name="Main"),
        Scene([PresetSelector(screen, engine, config)], -1, name="Presets"),
        Scene([LayerEditor(screen, engine, config)], -1, name="Editor"),
        Scene([MIDIVisualizer(screen, engine)], -1, name="Visualizer")
    ]
    screen.play(scenes, stop_on_resize=True)
