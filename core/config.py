import json
import os

class ConfigManager:
    def __init__(self, engine, preset_dir="presets", settings_file="settings.json"):
        self.engine = engine
        self.preset_dir = preset_dir
        self.settings_file = settings_file
        
        if not os.path.exists(self.preset_dir):
            os.makedirs(self.preset_dir)

    def save_preset(self, filename):
        if not filename.endswith('.cfg'): filename += '.cfg'
        filepath = os.path.join(self.preset_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(self.engine.layers, f, indent=4)
        self.engine.add_notification(f"Preset saved: {filename}")

    def load_preset(self, filename):
        filepath = os.path.join(self.preset_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                loaded_layers = json.load(f)
                for i, layer in enumerate(loaded_layers):
                    default = self.engine._default_layer_config(i, self.engine.gm_instruments)
                    for key, val in default.items():
                        if key not in layer: layer[key] = val
                    
                    if 'program' in layer:
                        pgm = layer['program']
                        if 0 <= pgm < len(self.engine.gm_instruments):
                            if layer.get('name', '').startswith('Layer ') or layer.get('name') == 'Acoustic Grand Piano':
                                layer['name'] = self.engine.gm_instruments[pgm]

                self.engine.layers = loaded_layers
            self.engine.current_preset_name = filename
            if self.engine.running:
                self.engine.update_all_layer_parameters()
            self.engine.add_notification(f"Preset loaded: {filename}")
            return True
        return False

    def save_settings(self):
        settings = {
            'master_transpose': self.engine.master_transpose,
            'auto_panic': self.engine.auto_panic,
            'global_fixed_vel': self.engine.global_fixed_vel,
            'sustain_enabled': self.engine.sustain_enabled,
            'current_preset': self.engine.current_preset_name,
            'last_in_port': self.engine.inport.name if self.engine.inport else None,
            'last_out_port': self.engine.outport.name if self.engine.outport else None
        }
        with open(self.settings_file, 'w') as f:
            json.dump(settings, f, indent=4)

    def load_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r') as f:
                s = json.load(f)
                self.engine.master_transpose = s.get('master_transpose', 0)
                self.engine.auto_panic = s.get('auto_panic', True)
                self.engine.global_fixed_vel = s.get('global_fixed_vel', False)
                self.engine.sustain_enabled = s.get('sustain_enabled', True)
                preset = s.get('current_preset', "None")
                if preset != "None":
                    self.load_preset(preset)
                return s
        return {}
