import json
import os

def load_config(path='config.json'):
    with open(path, 'r') as f:
        return json.load(f)

def get_signal_config(signal_id, config):
    return config['signals'].get(signal_id, {})
