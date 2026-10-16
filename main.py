import hashlib
import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder


SECRET = "A85D4ECE998948D0AA0B792A919985581049EF42C5524C87BCA0E9A"

KV = """
BoxLayout:
    orientation: "vertical"
    padding: "16dp"
    spacing: "10dp"

    Label:
        text: "MD5 PIN Checker"
        font_size: "24sp"
        size_hint_y: None
        height: "48dp"

    TextInput:
        id: base_input
        hint_text: "Base string or AMX string"
        multiline: False
        size_hint_y: None
        height: "48dp"

    TextInput:
        id: hash_input
        hint_text: "Target MD5 (optional)"
        multiline: False
        size_hint_y: None
        height: "48dp"

    Button:
        text: "Start"
        size_hint_y: None
        height: "48dp"
        on_release: app.start_check()

    Label:
        id: status
        text: "Ready"
        size_hint_y: None
        height: "40dp"

    ScrollView:
        Label:
            id: result
            text: ""
            size_hint_y: None
            height: self.texture_size[1]
            text_size: self.width, None
            halign: "left"
"""


class PinCheckerApp(App):
    def build(self):
        return Builder.load_string(KV)

    def start_check(self):
        if getattr(self, "running", False):
            return

        raw = self.root.ids.base_input.text.strip()
        supplied_hash = self.root.ids.hash_input.text.strip().lower()

        if not raw:
            self.root.ids.status.text = "Enter a base string."
            return

        if raw.startswith("amx "):
            raw = raw[4:]

        parts = raw.split(":")

        if len(parts) == 4 and not supplied_hash:
            base = parts[0] + SECRET + parts[2]
            target = parts[3].lower()
        else:
            base = raw
            target = supplied_hash

        if (
            len(target) != 32
            or any(c not in "0123456789abcdef" for c in target)
        ):
            self.root.ids.status.text = "Invalid MD5 hash."
            return

        self.running = True
        self.root.ids.result.text = ""
        self.root.ids.status.text = "Checking..."

        threading.Thread(
            target=self.check_hash,
            args=(base, target),
            daemon=True,
        ).start()

    def check_hash(self, base, target):
        if hashlib.md5(base.encode("utf-8")).hexdigest() == target:
            Clock.schedule_once(
                lambda dt: self.finish("Match found: no PIN suffix."),
                0,
            )
            return

        for number in range(1_000_000):
            suffix = f"{number:06d}"
            full_string = base + suffix
            digest = hashlib.md5(
                full_string.encode("utf-8")
            ).hexdigest()

            if number % 5000 == 0:
                Clock.schedule_once(
                    lambda dt, n=number: self.update_status(n),
                    0,
                )

            if digest == target:
                message = (
                    f"Match found!\n"
                    f"Number: {suffix}\n"
                    f"Full string: {full_string}\n"
                    f"MD5: {digest}"
                )
                Clock.schedule_once(
                    lambda dt, msg=message: self.finish(msg),
                    0,
                )
               
