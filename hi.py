import pyaudio
p = pyaudio.PyAudio()
info = p.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')
print("Number of devices:", numdevices)
for i in range(0, numdevices):
    try:
        device_info = p.get_device_info_by_host_api_device_index(0, i)
        print(f"Device {i}:")
        print(f"  Name: {device_info.get('name')}")
        print(f"  Max input channels: {device_info.get('maxInputChannels')}")
        print(f"  Max output channels: {device_info.get('maxOutputChannels')}")
    except OSError as e:
        print(f"  Error getting info: {e}")