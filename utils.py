import json

# A dummy in device that contains nothing
class dummy_in(object):
    def __init__(self):
        pass
    def __enter__(self):
        return self
    def __exit__(self, type, value, traceback):
        pass
    def __iter__(self):
        return self
    def __next__(self):
        raise StopIteration
    def iter_pending(self):
        return []
    def close():
        pass

# A dummy out device that does nothing
class dummy_out(object):
    def __init__(self):
        pass
    def __enter__(self):
        return self
    def __exit__(self, type, value, traceback):
        pass
    def __iter__(self):
        return self
    def __next__(self):
        raise StopIteration
    def send(a, b, **argv):
        pass
    def close():
        pass

def get_osc_parameters(n: int):
            l = [f"/avatar/parameters/Key{n}", f"/avatar/parameters/VP/Notes/Note{n}"]
            notes = [["C", ""], ["C", "up"], ["D", ""], ["D", "up"], ["E", ""], ["F", ""], ["F", "up"], ["G", ""], ["G", "up"], ["A", ""], ["A", "up"], ["B", ""]]
            quotient = (n - 12) // 12
            remainder = n % 12
            l.append(f"/avatar/parameters/{notes[remainder][0]}{quotient}{notes[remainder][1]}")
            return l

def load_config():
    with open("config.json", "r") as f:
        config = json.load(f)
    return config

def save_config(config):
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def send_osc(msg, client):
    if msg.type == "note_on":
        for param in get_osc_parameters(msg.note):
            client.send_message(param, True)
    elif msg.type == "note_off":
        for param in get_osc_parameters(msg.note):
            client.send_message(param, False)
    elif msg.type == 'control_change' and msg.control in (64, 66, 67):
        pedal_param = {64: '/avatar/parameters/PedalRight', 66: '/avatar/parameters/PedalCenter', 67: '/avatar/parameters/PedalLeft'}[msg.control]
        client.send_message(pedal_param, msg.value >= 64)