import sounddevice as sd
print('Input devices:')
for i, d in enumerate(sd.query_devices()):
    if d['max_input_channels'] > 0:
        print(f'  {i}: {d["name"]} (sr={d["default_samplerate"]})')
print()
print('Default input:', sd.default.device[0] if isinstance(sd.default.device, tuple) else sd.default.device)