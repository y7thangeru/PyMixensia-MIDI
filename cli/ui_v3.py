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

class LiveDropdownList(DropdownList):
    def __init__(self, options, label=None, name=None, on_change=None, **kwargs):
        super(LiveDropdownList, self).__init__(options, label, name, on_change, **kwargs)
        self._parent_frame = None
    def process_event(self, event):
        res = super(LiveDropdownList, self).process_event(event)
        if self._parent_frame: self._parent_frame._update_help()
        return res

class MIDIVisualizer(Effect):
    def __init__(self, screen, engine, **kwargs):
        super(MIDIVisualizer, self).__init__(screen, **kwargs)
        self._engine = engine
        self._local_particles = []
    @property
    def stop_frame(self): return 0
    def _update(self, frame_no):
        h, w = self._screen.dimensions
        while self._engine.particles: self._local_particles.append(self._engine.particles.pop(0))
        remaining = []
        for p in self._local_particles:
            color_map = {1: Screen.COLOUR_GREEN, 2: Screen.COLOUR_RED, 3: Screen.COLOUR_CYAN, 4: Screen.COLOUR_YELLOW, 5: Screen.COLOUR_MAGENTA, 6: Screen.COLOUR_BLUE}
            color = color_map.get(p.get('color', 1), Screen.COLOUR_WHITE)
            if p['type'] == 'firework':
                p['x'] += p['vx']; p['y'] += p['vy']; p['vy'] += 0.1; p['life'] -= 0.02
                if p['life'] > 0 and 0 <= p['x'] < w and 0 <= p['y'] < h:
                    self._screen.print_at(p.get('char', '*'), int(p['x']), int(p['y']), color)
                    remaining.append(p)
            elif p['type'] == 'falling':
                p['y'] += 0.5
                if p['y'] < h:
                    for i in range(int(p['len'])):
                        yy = int(p['y'] - i)
                        if 0 <= yy < h: self._screen.print_at("█", int(p['x']), yy, color)
                    remaining.append(p)
        self._local_particles = remaining
    def process_event(self, event):
        if hasattr(event, 'key_code'):
            if event.key_code in [ord('q'), 27, Screen.KEY_F4]: raise NextScene("Main")
        return event
    def reset(self): self._local_particles = []

class MainMenu(Frame):
    def __init__(self, screen, engine, config):
        super(MainMenu, self).__init__(screen, screen.height, screen.width, has_border=True, title=" 🎹 PyMixensia V3 Dashboard 🎹 ")
        self._engine, self._config = engine, config
        layout = Layout([1, 1, 1], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(Label("--- ENGINE ---"), 0)
        self._status = Label("STOPPED")
        layout.add_widget(self._status, 0)
        layout.add_widget(Button("START/STOP (S)", self._toggle_engine), 0)
        layout.add_widget(Divider(), 0)
        self._splits = CheckBox("Splits", on_change=self._update_settings)
        self._sustain = CheckBox("Sustain", on_change=self._update_settings)
        layout.add_widget(self._splits, 0)
        layout.add_widget(self._sustain, 0)
        layout.add_widget(Label("--- PRESET ---"), 1)
        self._preset = Label("None")
        layout.add_widget(self._preset, 1)
        layout.add_widget(Button("LOAD (L)", self._open_presets), 1)
        layout.add_widget(Divider(), 1)
        self._master_t = Text("Transpose:", readonly=True)
        layout.add_widget(self._master_t, 1)
        layout.add_widget(Button("PANIC (P)", self._panic), 1)
        layout.add_widget(Label("--- PORTS ---"), 2)
        self._in_port = DropdownList([("No Ports", 0)], label="IN :")
        self._out_port = DropdownList([("No Ports", 0)], label="OUT:")
        layout.add_widget(self._in_port, 2)
        layout.add_widget(self._out_port, 2)
        layout.add_widget(Divider(), 2)
        layout.add_widget(Button("EDITOR (F2)", self._open_editor), 2)
        layout.add_widget(Button("VISUAL (F4)", self._open_visual), 2)
        layout.add_widget(Button("QUIT (Q)", self._quit), 2)
        self.fix()
        self._sync()

    def _panic(self):
        self._engine.panic()

    def _sync(self):
        self._status.text = "RUNNING" if self._engine.running else "STOPPED"
        self._preset.text = self._engine.current_preset_name
        self._splits.value = not self._engine.disable_splits
        self._sustain.value = self._engine.sustain_enabled
        self._master_t.value = f"{self._engine.master_transpose:+d}"
        in_p = self._engine.available_in_ports
        out_p = self._engine.available_out_ports
        if in_p: self._in_port.options = [(p, i) for i, p in enumerate(in_p)]
        if out_p: self._out_port.options = [(p, i) for i, p in enumerate(out_p)]

    def _update_settings(self):
        self._engine.disable_splits = not self._splits.value
        self._engine.sustain_enabled = self._sustain.value
        self._config.save_settings()

    def _toggle_engine(self):
        if self._engine.running: self._engine.stop()
        else:
            in_p, out_p = self._engine.available_in_ports, self._engine.available_out_ports
            if in_p and out_p:
                in_idx = self._in_port.value if self._in_port.value is not None else 0
                out_idx = self._out_port.value if self._out_port.value is not None else 0
                self._engine.start(in_p[in_idx], out_p[out_idx])
        self._sync()

    def _open_presets(self): raise NextScene("Presets")
    def _open_editor(self): raise NextScene("Editor")
    def _open_visual(self): raise NextScene("Visualizer")
    def _open_help(self): raise NextScene("Help")
    def _open_monitor(self): raise NextScene("Monitor")
    def _quit(self): self._config.save_settings(); self._engine.stop(); raise StopApplication("Quit")

    def process_event(self, event):
        if hasattr(event, 'key_code'):
            if event.key_code == ord('s'): self._toggle_engine()
            elif event.key_code == ord('l'): self._open_presets()
            elif event.key_code == ord('p'): self._panic()
            elif event.key_code == ord('q'): self._quit()
            elif event.key_code == ord('1'): self.switch_focus(self._layouts[2], 0, 0)
            elif event.key_code == ord('2'): self.switch_focus(self._layouts[2], 0, 1)
            elif event.key_code == ord('m'): self._open_monitor()
            elif event.key_code == Screen.KEY_F1: self._open_help()
            elif event.key_code == Screen.KEY_F2: self._open_editor()
            elif event.key_code == Screen.KEY_F4: self._open_visual()
        self._sync()
        return super(MainMenu, self).process_event(event)

class HelpDialog(Frame):
    def __init__(self, screen):
        super(HelpDialog, self).__init__(screen, 12, 50, has_border=True, title=" 📘 SHORTCUT LIST 📘 ")
        layout = Layout([1], fill_frame=True)
        self.add_layout(layout)
        helps = [
            "[S] Start/Stop Engine", "[L] Load Preset List", "[P] Panic (Kill All Notes)",
            "[1] Select Input Port", "[2] Select Output Port", "[M] MIDI Monitor",
            "[[] Transpose Down", "[]] Transpose Up", "[F1] This Help",
            "[F2] Preset Editor", "[F4] Visualizer", "[Q] Quit Application"
        ]
        for h in helps: layout.add_widget(Label(h))
        layout.add_widget(Divider())
        layout.add_widget(Button("CLOSE", self._back))
        self.fix()
    def _back(self): raise NextScene("Main")

class MIDIMonitor(Frame):
    def __init__(self, screen, engine):
        super(MIDIMonitor, self).__init__(screen, 15, 60, has_border=True, title=" 🔍 MIDI MONITOR 🔍 ")
        self._engine = engine
        layout = Layout([1], fill_frame=True)
        self.add_layout(layout)
        self._log = ListBox(10, [("Waiting for MIDI...", 0)])
        layout.add_widget(self._log)
        layout.add_widget(Divider())
        layout.add_widget(Button("BACK", self._back))
        self.fix()
    def _back(self): raise NextScene("Main")
    def _update(self, frame_no):
        super(MIDIMonitor, self)._update(frame_no)
        # Snapshot of midi log
        messages = list(self._engine.midi_log)[-10:]
        if messages:
            self._log.options = [(str(m), i) for i, m in enumerate(messages)]

class PresetSelector(Frame):
    def __init__(self, screen, engine, config):
        super(PresetSelector, self).__init__(screen, screen.height // 2, screen.width // 2, has_border=True, title=" PRESETS ")
        self._engine, self._config = engine, config
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
        if self._list.value: self._config.load_preset(self._list.value); self._config.save_settings(); self._back()
    def _back(self): raise NextScene("Main")

class FilenameDialog(Frame):
    def __init__(self, screen, on_ok):
        super(FilenameDialog, self).__init__(screen, 7, 40, has_border=True, title=" SAVE PRESET AS ")
        self._on_ok = on_ok
        layout = Layout([1], fill_frame=True)
        self.add_layout(layout)
        self._text = Text("Filename:", name="fname")
        layout.add_widget(self._text)
        layout.add_widget(Divider())
        layout2 = Layout([1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("OK", self._ok), 0)
        layout2.add_widget(Button("CANCEL", self._back), 1)
        self.fix()
    def _ok(self): self._on_ok(self._text.value); self._back()
    def _back(self): raise NextScene("Editor")

class LayerEditor(Frame):
    def __init__(self, screen, engine, config):
        super(LayerEditor, self).__init__(screen, screen.height, screen.width, has_border=True, title=" LAYER EDITOR ")
        self._engine, self._config, self._layer_idx, self._updating = engine, config, 0, False
        layout = Layout([1, 2], fill_frame=True)
        self.add_layout(layout)
        
        layout.add_widget(Label("--- LAYERS ---"), 0)
        self._layer_list = ListBox(16, self._get_options(), on_change=self._on_layer_change)
        layout.add_widget(self._layer_list, 0)
        layout.add_widget(Divider(), 0)
        layout.add_widget(Button("SAVE", self._save), 0)
        layout.add_widget(Button("SAVE AS", self._open_save_as), 0)
        layout.add_widget(Button("EXIT", self._back), 0)
        
        layout.add_widget(Label("--- PARAMETERS ---"), 1)
        self._active = CheckBox("Active Status", label="STATUS   :", on_change=self._on_change)
        self._pgm = LiveDropdownList([(f"{i}: {n}", i) for i, n in enumerate(engine.gm_instruments)], label="PROGRAM  :", on_change=self._on_change)
        self._vol = Text(label="VOLUME   :", on_change=self._on_change)
        self._trans = Text(label="TRANSPOSE:", on_change=self._on_change)
        self._chord = LiveDropdownList([('Off', 'off'), ('Octave', 'octave'), ('Major', 'major'), ('Minor', 'minor'), ('Power', 'power')], label="CHORD    :", on_change=self._on_change)
        self._arp = LiveDropdownList([('Off', 'off'), ('Up', 'up'), ('Down', 'down'), ('Random', 'random')], label="ARP      :", on_change=self._on_change)
        self._curve = LiveDropdownList([('Linear', 'linear'), ('Soft', 'soft'), ('Hard', 'hard'), ('Fixed', 'fixed')], label="CURVE    :", on_change=self._on_change)
        self._hold = LiveDropdownList([('Normal', 'normal'), ('Smart', 'smart')], label="HOLD     :", on_change=self._on_change)
        self._ensemble = LiveDropdownList([('Off', 'off'), ('Top', 'top'), ('Bottom', 'bottom'), ('Middle', 'middle')], label="ENSEMBLE :", on_change=self._on_change)
        self._min_n = Text(label="MIN NOTE :", on_change=self._on_change)
        self._max_n = Text(label="MAX NOTE :", on_change=self._on_change)
        self._min_v = Text(label="MIN VEL  :", on_change=self._on_change)
        self._max_v = Text(label="MAX VEL  :", on_change=self._on_change)
        
        for w in [self._active, self._pgm, self._vol, self._trans, self._chord, self._arp, self._curve, self._hold, self._ensemble, self._min_n, self._max_n, self._min_v, self._max_v]:
            if isinstance(w, LiveDropdownList): w._parent_frame = self
            layout.add_widget(w, 1)
            
        layout.add_widget(Divider(), 1)
        layout.add_widget(Label("--- MANUAL GUIDE ---"), 1)
        self._help_desc = Label("")
        self._help_opts = [Label("") for _ in range(5)]
        layout.add_widget(self._help_desc, 1)
        for l in self._help_opts: layout.add_widget(l, 1)
        layout.add_widget(Divider(), 1)
        layout.add_widget(Label("[F2] Close | [S] Quick Save | [A] Save As"), 1)
        
        self.fix()
        self._on_layer_change()
        
    def _get_options(self): return [(f"{i+1:02d} {'[ON]' if l['active'] else '[..]'} {l['name'][:15]}", i) for i, l in enumerate(self._engine.layers)]
    
    def _on_layer_change(self):
        self._updating = True
        self._layer_idx = self._layer_list.value or 0
        l = self._engine.layers[self._layer_idx]
        self._active.value, self._pgm.value, self._vol.value, self._trans.value = l['active'], l['program'], str(l['volume']), str(l['transpose'])
        self._chord.value, self._arp.value, self._curve.value = l.get('chord_mode', 'off'), l.get('arp_mode', 'off'), l.get('vel_curve', 'linear')
        self._hold.value, self._ensemble.value = l.get('hold_mode', 'normal'), l.get('ensemble_mode', 'off')
        self._min_n.value, self._max_n.value = str(l.get('min_note', 0)), str(l.get('max_note', 127))
        self._min_v.value, self._max_v.value = str(l.get('min_vel', 0)), str(l.get('max_vel', 127))
        self._updating = False
        self._update_help()

    def _on_change(self):
        if self._updating: return
        l = self._engine.layers[self._layer_idx]
        l['active'], l['program'] = self._active.value, self._pgm.value
        l['chord_mode'], l['arp_mode'], l['vel_curve'] = self._chord.value, self._arp.value, self._curve.value
        l['hold_mode'], l['ensemble_mode'] = self._hold.value, self._ensemble.value
        l['name'] = self._engine.gm_instruments[l['program']]
        try:
            l['volume'], l['transpose'] = int(self._vol.value), int(self._trans.value)
            l['min_note'], l['max_note'] = int(self._min_n.value), int(self._max_n.value)
            l['min_vel'], l['max_vel'] = int(self._min_v.value), int(self._max_v.value)
        except: pass
        self._layer_list.options = self._get_options()
        if self._engine.running: self._engine.update_all_layer_parameters()
        self._update_help()

    def _update_help(self):
        h_data = {
            "STATUS": {"desc": "Aktifkan/matikan layer MIDI ini.", "opts": ["OFF: Layer tidak bunyi.", "ON: Layer aktif."]},
            "PROGRAM": {"desc": "Instrumen General MIDI.", "opts": [f"HASIL: {self._engine.gm_instruments[self._pgm.value or 0]}"]},
            "VOLUME": {"desc": "Level volume layer (0-127).", "opts": ["TIPS: Volume 40-60 untuk pengiring."]},
            "TRANSPOSE": {"desc": "Geser nada dasar.", "opts": ["+12: Naik 1 oktav.", "-12: Turun 1 oktav."]},
            "CHORD": {"desc": "Smart Chord Mode:", "opts": ["OFF: Nada tunggal.", "OCT: Tambah oktav.", "MAJOR: Chord Mayor (1-3-5).", "MINOR: Chord Minor (1-3b-5).", "POWER: Power Chord (1-5-8)."]},
            "ARP": {"desc": "Arpeggiator Mode:", "opts": ["OFF: Normal.", "UP: Rendah ke tinggi.", "DOWN: Tinggi ke rendah.", "RANDOM: Urutan acak."]},
            "CURVE": {"desc": "Velocity Curve:", "opts": ["LINEAR: Standar.", "SOFT: Lembut.", "HARD: Berat/Rock.", "FIXED: Rata (100)."]},
            "HOLD": {"desc": "Logika Sustain:", "opts": ["NORMAL: Standar.", "SMART: Hemat CPU."]},
            "ENSEMBLE": {"desc": "Voice Splitting:", "opts": ["OFF: Semua bunyi.", "TOP: Melodi saja.", "BOTTOM: Bass saja.", "MIDDLE: Nada tengah."]},
            "MIN NOTE": {"desc": "Batas nada bawah.", "opts": ["Layer hanya bunyi di atas nada ini."]},
            "MAX NOTE": {"desc": "Batas nada atas.", "opts": ["Layer hanya bunyi di bawah nada ini."]},
            "MIN VEL": {"desc": "Velocity minimal.", "opts": ["Hanya bunyi jika ditekan kuat."]},
            "MAX VEL": {"desc": "Velocity maksimal.", "opts": ["Hanya bunyi jika ditekan lembut."]}
        }
        f = self.focussed_widget
        if f and hasattr(f, 'label') and f.label:
            lbl = f.label.replace(":", "").strip()
            self._help_desc.text = ""
            for l in self._help_opts: l.text = ""
            if lbl in h_data:
                d = h_data[lbl]
                self._help_desc.text = f"💡 {lbl}: {d['desc']}"
                for i, opt in enumerate(d.get("opts", [])):
                    if i < len(self._help_opts): self._help_opts[i].text = f"  - {opt}"

    def _save(self):
        if self._engine.current_preset_name not in ["None", "New Preset"]: self._config.save_preset(self._engine.current_preset_name)
        else: self._open_save_as()
    def _open_save_as(self): raise NextScene("SaveAs")
    def _back(self): raise NextScene("Main")
    def reset(self):
        self.title = f" 🛠️ EDITOR: {self._engine.current_preset_name} 🛠️ "
        self._layer_list.options = self._get_options()
        self._on_layer_change()
        super(LayerEditor, self).reset()
    def process_event(self, event):
        if hasattr(event, 'key_code'):
            if event.key_code == Screen.KEY_F2: self._back()
            elif event.key_code == ord('s'): self._save()
            elif event.key_code == ord('a'): self._open_save_as()
        res = super(LayerEditor, self).process_event(event)
        self._update_help()
        return res

def draw_menu_v3(screen, engine, config):
    if not hasattr(engine, '_original_handle_note_on'):
        engine._original_handle_note_on = engine.handle_note_on
        def v_on(msg):
            h, w = screen.dimensions
            x = int((msg.note / 127) * (w - 6)) + 3
            if engine.visualizer_mode == 0:
                for _ in range(5): engine.particles.append({'type': 'firework', 'x': float(x), 'y': float(h-4), 'vx': random.uniform(-1,1), 'vy': random.uniform(-2,-1), 'life': 1.0, 'color': random.randint(1,6)})
            engine._original_handle_note_on(msg)
        engine.handle_note_on = v_on
    main = MainMenu(screen, engine, config)
    presets = PresetSelector(screen, engine, config)
    editor = LayerEditor(screen, engine, config)
    save_as = FilenameDialog(screen, lambda n: (config.save_preset(n), setattr(engine, 'current_preset_name', n)))
    visual = MIDIVisualizer(screen, engine)
    help_dialog = HelpDialog(screen)
    monitor = MIDIMonitor(screen, engine)
    
    scenes = [
        Scene([main], -1, name="Main"),
        Scene([presets], -1, name="Presets"),
        Scene([editor], -1, name="Editor"),
        Scene([save_as], -1, name="SaveAs"),
        Scene([visual], -1, name="Visualizer"),
        Scene([help_dialog], -1, name="Help"),
        Scene([monitor], -1, name="Monitor")
    ]
    screen.play(scenes, stop_on_resize=True)
