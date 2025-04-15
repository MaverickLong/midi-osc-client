from pythonosc.udp_client import SimpleUDPClient
import mido
import mido.backends.rtmidi
from utils import load_config, save_config, get_osc_parameters, send_osc, dummy_out

config = load_config()

def ask_for_number(n) -> int:
    while True:
        user_input = input()
        try:
            value = int(user_input)
            if 1 <= value <= n:
                return value
            else:
                print(f"Invalid input: number not in range 1 to {n}. Please try again.")
        except ValueError:
            print("Invalid input: not an integer. Please try again.")

def setup_midi():
    in_devices = mido.get_input_names()
    if in_devices:
        print(f"Please select a MIDI input device by entering a number between 1 and {len(in_devices)}: ")
        for n, in_device in enumerate(in_devices):
            print(f"{n + 1}. {in_device}")
        config["midi_in_device"] = in_devices[ask_for_number(len(in_device)) - 1]
        save_config(config)
    else:
        print("You don't seem to have any MIDI input device available. Connect your MIDI device and try again.")
        exit()
    
    # There will be at least one output device (disabled)
    out_devices = mido.get_output_names()
    out_devices.append("None (disabled)")

    print(f"Please select a MIDI output device (that the program forwards the signals to) by entering a number between 1 and {len(out_devices)}: ")
    for n, out_device in enumerate(out_devices):
        print(f"{n + 1}. {out_device}")
    config["midi_out_device"] = out_devices[ask_for_number(len(out_device)) - 1]
    save_config(config)

# For reusability the dispatch function doesnot itself loop.
# Wrap a indefinite loop outside of it to make the dispatcher continuously run.
# This function assumes both in / out exists (possibly dummy devices).
def dispatch(in_device, out_device, client):
    for msg in in_device.iter_pending():
        out_device.send(msg)
        send_osc(msg, client)

def main():
    while True:
        try:
            in_device = mido.open_input(config["midi_in_device"])
            if config["midi_out_device"] == "None (disabled)":
                out_device = dummy_out()
            else:
                out_device = mido.open_output(config["midi_out_device"])
            break
        except:
            print("MIDI device bind failed, running MIDI device setup now.")
            setup_midi()
    
    client = SimpleUDPClient(config["vrchat_receive_address"], config["vrchat_receive_port"])

    print("Now sending OSC messages")

    while True:
        dispatch(in_device, out_device, client)
    

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        exit()
