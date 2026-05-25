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
from asciimatics.widgets import Frame, Layout, Label, Divider, ListBox, Text, Button, CheckBox, DropdownList

class MIDIVisualizer(Effect):
    """
    Custom Asciimatics Effect that renders MIDI notes as 3D-like falling blocks or particles.
    """
    def __init__(self, screen, engine, **kwargs):
        super(MIDIVisualizer, self).__init__(screen, **kwargs)
        self._engine = engine
        self._particles = []

    def _update(self, frame_no):
        # Sync with engine particles or create new ones from engine state
        # For V3, we use asciimatics' own drawing methods
        h, w = self._screen.dimensions
        
        # Draw ground line
        self._screen.print_at("═" * w, 0, h - 3, Screen.COLOUR_CYAN)

        # Process and draw particles
        new_particles = []
        # We capture a snapshot of particles to avoid threading issues
        current_particles = list(self._engine.particles)
        self._engine.particles = [] # Clear them as we consume them into the visualizer's local state

        for p in current_particles:
            self._particles.append(p)

        remaining_particles = []
        for p in self._particles:
            # Map color index to asciimatics colors
            color_map = {
                1: Screen.COLOUR_GREEN,
                2: Screen.COLOUR_RED,
                3: Screen.COLOUR_CYAN,
                4: Screen.COLOUR_YELLOW,
                5: Screen.COLOUR_MAGENTA,
                6: Screen.COLOUR_BLUE
            }
            color = color_map.get(p.get('color'), Screen.COLOUR_WHITE)

            # Type specific rendering
            if p['type'] == 'firework':
                p['x'] += p['vx']
                p['y'] += p['vy']
                p['vy'] += 0.1
                p['life'] -= 0.02
                if p['life'] > 0:
                    char = random.choice(['*', '.', '+', 'x'])
                    color = p.get('color', Screen.COLOUR_WHITE)
                    self._screen.print_at(char, int(p['x']), int(p['y']), color)
                    remaining_particles.append(p)
            
            elif p['type'] == 'falling':
                p['y'] += 0.5
                if p['y'] < h - 3:
                    color = p.get('color', Screen.COLOUR_GREEN)
                    for i in range(int(p['len'])):
                        yy = int(p['y'] - i)
                        if 0 <= yy < h - 3:
                            self._screen.print_at("█", int(p['x']), yy, color)
                    remaining_particles.append(p)
            
            # Add more V3 exclusive types here
        
        self._particles = remaining_particles

    @property
    def stop_frame(self):
        return 0

    def reset(self):
        self._particles = []

    def process_event(self, event):
        return event

class MainMenu(Frame):
    def __init__(self, screen, engine, config):
        super(MainMenu, self).__init__(screen, screen.height, screen.width, has_border=True, title=" PyMixensia V3 ")
        self._engine = engine
        self._config = config
        
        # Create the layout
        layout = Layout([1, 1], fill_frame=True)
        self.add_layout(layout)
        
        # Left side: Status and Settings
        layout.add_widget(Label("ENGINE STATUS"), 0)
        self._status_label = Label("STOPPED")
        layout.add_widget(self._status_label, 0)
        layout.add_widget(Divider(), 0)
        
        layout.add_widget(Label("ACTIVE PRESET:"), 0)
        self._preset_label = Label("None")
        layout.add_widget(self._preset_label, 0)
        
        layout.add_widget(Divider(), 0)
        layout.add_widget(Button("START ENGINE", self._toggle_engine), 0)
        layout.add_widget(Button("PANIC (All Notes Off)", self._engine.panic), 0)
        
        # Right side: Port Selection
        layout.add_widget(Label("MIDI PORTS"), 1)
        self._in_port = DropdownList([("No Ports", 0)], label="IN :")
        self._out_port = DropdownList([("No Ports", 0)], label="OUT:")
        layout.add_widget(self._in_port, 1)
        layout.add_widget(self._out_port, 1)
        
        layout.add_widget(Divider(), 1)
        layout.add_widget(Button("OPEN EDITOR (F2)", self._open_editor), 1)
        layout.add_widget(Button("VISUALIZER (F4)", self._open_visualizer), 1)
        layout.add_widget(Button("QUIT", self._quit), 1)
        
        self.fix()

    def _toggle_engine(self):
        if self._engine.running:
            self._engine.stop()
            self._status_label.text = "STOPPED"
        else:
            # Logic to get selected ports
            # For simplicity in this V3 draft, we'll use first available if not set
            in_p = self._engine.available_in_ports
            out_p = self._engine.available_out_ports
            if in_p and out_p:
                if self._engine.start(in_p[0], out_p[0]):
                    self._status_label.text = "RUNNING"

    def _open_editor(self):
        raise NextScene("Editor")

    def _open_visualizer(self):
        raise NextScene("Visualizer")

    def _quit(self):
        self._config.save_settings()
        self._engine.stop()
        raise StopApplication("User quit")

    def process_event(self, event):
        # Update dynamic labels
        self._preset_label.text = self._engine.current_preset_name
        return super(MainMenu, self).process_event(event)

class LayerEditor(Frame):
    def __init__(self, screen, engine, config):
        super(LayerEditor, self).__init__(screen, screen.height, screen.width, has_border=True, title=" LAYER EDITOR ")
        self._engine = engine
        self._config = config
        self._layer_idx = 0
        
        layout = Layout([1, 3, 1], fill_frame=True)
        self.add_layout(layout)
        
        # Layer Selection
        layout.add_widget(Label("SELECT LAYER"), 0)
        self._layer_list = ListBox(16, [(f"Layer {i+1}", i) for i in range(16)], on_change=self._on_layer_change)
        layout.add_widget(self._layer_list, 0)
        
        # Parameters
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
        
        # Help / Info
        layout.add_widget(Label("HELP & INFO"), 2)
        self._info = Label("Adjust layer parameters here.")
        layout.add_widget(self._info, 2)
        
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("SAVE", self._save), 0)
        layout2.add_widget(Button("BACK", self._back), 3)
        
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
        if self._engine.current_preset_name != "None":
            self._config.save_preset(self._engine.current_preset_name)

    def _back(self):
        raise NextScene("Main")

def draw_menu_v3(screen, engine, config):
    # Wrap note handler for visualizer particles
    original_handle_note_on = engine.handle_note_on
    def visualizer_note_on(msg):
        h, w = screen.dimensions
        x_pos = int((msg.note / 127) * (w - 6)) + 3
        # Add falling block for visualizer
        engine.particles.append({
            'type': 'falling', 'x': x_pos, 'y': 0.0, 
            'len': max(4, msg.velocity // 6), 'color': random.randint(1, 6)
        })
        original_handle_note_on(msg)
    engine.handle_note_on = visualizer_note_on

    scenes = []
    
    # Scene 0: Intro
    intro_effects = [
        Stars(screen, screen.width // 2),
        Print(screen,
              Rainbow(screen, FigletText("PYMIXENSIA V3", font='slant')),
              screen.height // 2 - 4,
              transparent=False,
              speed=1,
              stop_frame=100),
        Print(screen, StaticRenderer(["ADVANCED MIDI ENGINE"]), screen.height // 2 + 3, colour=Screen.COLOUR_CYAN, stop_frame=100)
    ]
    scenes.append(Scene(intro_effects, 100, name="Intro"))

    # Scene 1: Main Menu
    scenes.append(Scene([MainMenu(screen, engine, config)], -1, name="Main"))
    
    # Scene 2: Editor
    scenes.append(Scene([LayerEditor(screen, engine, config)], -1, name="Editor"))
    
    # Scene 3: Visualizer (Stars + Matrix + MIDI)
    visualizer_effects = [
        Stars(screen, screen.width // 2),
        Matrix(screen, stop_frame=0),
        MIDIVisualizer(screen, engine),
        Print(screen, StaticRenderer(["PRESS [ESC] TO RETURN TO MENU"]), screen.height - 1, x=2, colour=Screen.COLOUR_YELLOW)
    ]
    scenes.append(Scene(visualizer_effects, -1, name="Visualizer"))
    
    screen.play(scenes, stop_on_resize=True)

if __name__ == "__main__":
    # This is for testing standalone, normally called from mixensia_v3.py
    from core.engine import MixensiaEngine
    from core.config import ConfigManager
    GM_INSTRUMENTS = ["Piano"] * 128
    engine = MixensiaEngine(GM_INSTRUMENTS)
    config = ConfigManager(engine)
    Screen.wrapper(draw_menu_v3, arguments=[engine, config])
