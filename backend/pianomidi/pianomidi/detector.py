#!/usr/bin/env python3
"""Real-time MIDI chord detection.

Listens to a connected MIDI piano and streams JSON Lines to stdout
on every key press and release.
"""

import json
import sys
import time
import threading
import rtmidi
from pychord.analyzer import find_chords_from_notes

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


class ChordDetector:
    def __init__(self):
        self.held_notes = set()  # MIDI note numbers currently held
        # small debounce to allow near-simultaneous note-ons to be grouped
        self._debounce_timer: threading.Timer | None = None
        self._debounce_lock = threading.Lock()

    def midi_callback(self, event, _data=None):
        message, _dt = event
        try:
            # debug: print raw MIDI message to stderr so we can see what's arriving
            sys.stderr.write(f"[detector] raw message: {message}\n")
            sys.stderr.flush()
        except Exception:
            pass
        status = message[0] & 0xF0
        note = message[1]
        velocity = message[2] if len(message) > 2 else 0

        if status == 0x90 and velocity > 0:
            self._note_on(note)
        elif status == 0x80 or (status == 0x90 and velocity == 0):
            self._note_off(note)

    def _note_on(self, note):
        self.held_notes.add(note)
        self._schedule_detect()

    def _note_off(self, note):
        self.held_notes.discard(note)
        self._schedule_detect()

    def _schedule_detect(self, delay: float = 0.03):
        # Use a very small debounce (30ms) to capture simultaneous note-ons
        with self._debounce_lock:
            if self._debounce_timer:
                try:
                    self._debounce_timer.cancel()
                except Exception:
                    pass
            self._debounce_timer = threading.Timer(delay, self._detect)
            self._debounce_timer.daemon = True
            self._debounce_timer.start()

    def _detect(self):
        # cancel pending timer reference
        with self._debounce_lock:
            if self._debounce_timer:
                try:
                    self._debounce_timer.cancel()
                except Exception:
                    pass
                self._debounce_timer = None

        chroma = [1 if i in {n % 12 for n in self.held_notes} else 0 for i in range(12)]
        pitch_classes = sorted({n % 12 for n in self.held_notes})
        names = [NOTE_NAMES[pc] for pc in pitch_classes]

        chord = None
        if len(names) >= 2:
            chords = find_chords_from_notes(names)
            if chords:
                chord = str(chords[0])

        print(json.dumps({"chord": chord, "notes": names, "chroma": chroma}), flush=True)


def main():
    midi_in = rtmidi.MidiIn()
    ports = midi_in.get_ports()

    if not ports:
        print("No MIDI input ports found. Connect a MIDI device and try again.", file=sys.stderr)
        sys.exit(1)

    print(f"Opening: {ports[0]}", file=sys.stderr)
    print("Play some chords! Press Ctrl+C to quit.", file=sys.stderr)

    detector = ChordDetector()
    midi_in.set_callback(detector.midi_callback)
    midi_in.open_port(0)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nBye!", file=sys.stderr)
    finally:
        midi_in.close_port()


if __name__ == "__main__":
    main()
