from pythonosc.udp_client import SimpleUDPClient
import json
import mido
import mido.backends.rtmidi

with open("config.json", "r") as f:
    config = json.load(f)

# A dummy out device that does nothing
class dummy_out:
    def send(a, b, **argv):
        pass

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

def save_config():
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def setup_midi():
    in_devices = mido.get_input_names()
    if in_devices:
        print(f"Please select a MIDI input device by entering a number between 1 and {len(in_devices)}: ")
        for n, in_device in enumerate(in_devices):
            print(f"{n + 1}. {in_device}")
        config["midi_in_device"] = in_devices[ask_for_number(len(in_device)) - 1]
        save_config()
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
    save_config()
    
def get_osc_parameters(n: int) -> list[str]:
    l = []
    l.append(f"/avatar/parameters/Key{n}")
    notes = [
        ["C", ""],
        ["C", "up"],
        ["D", ""],
        ["D", "up"],
        ["E", ""],
        ["F", ""],
        ["F", "up"],
        ["G", ""],
        ["G", "up"],
        ["A", ""],
        ["A", "up"],
        ["B", ""]
    ]
    quotient = (n - 12) // 12
    remainder = n % 12
    l.append(f"/avatar/parameters/{notes[remainder][0]}{quotient}{notes[remainder][1]}")
    return l

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
        for msg in in_device.iter_pending():
            out_device.send(msg)
            
            if msg.type == "note_on":
                note_parameters = get_osc_parameters(msg.note)
                for note_parameter in note_parameters:
                    client.send_message(note_parameter, True)
            elif msg.type == "note_off":
                note_parameters = get_osc_parameters(msg.note)
                for note_parameter in note_parameters:
                    client.send_message(note_parameter, False)
            elif msg.type == 'control_change':
                # We only handle piano pedals here
                if msg.control in (64, 66, 67):  # Pedal CC numbers
                    pedal_parameter = {
                        64: '/avatar/parameters/PedalRight',
                        66: '/avatar/parameters/PedalCenter',
                        67: '/avatar/parameters/PedalLeft'
                    }[msg.control]
                    client.send_message(pedal_parameter, msg.value >= 64)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        exit()
