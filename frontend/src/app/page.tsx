"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Background } from "@/components/Background/Background";
import { ChordGraph } from "@/components/ChordGraph/ChordGraph";
import type { ChordGraphState, HistorySeed } from "@/types/chord";
import { KEY_TO_MIDI, midiNotesToNames } from "@/utils/keyboardToMidi";

const HISTORY_SEED_KEY = "historySeed";

type ChordMsg = {
  type: "chord";
  chord: { name: string | null; notes: string[]; chroma: number[] };
  suggestions: { name: string; notes: string[]; chroma: number[]; tension: number }[];
};

export default function Home() {
  const [status, setStatus] = useState<"disconnected" | "connecting" | "connected">("disconnected");
  const [historyBannerChord, setHistoryBannerChord] = useState<string | null>(null);
  const [chord, setChord] = useState<ChordMsg["chord"] | null>(null);
  const [lastChord, setLastChord] = useState<ChordMsg["chord"] | null>(null);
  const [suggestions, setSuggestions] = useState<ChordMsg["suggestions"]>([]);
  const [lastSuggestions, setLastSuggestions] = useState<ChordMsg["suggestions"]>([]);
  const [log, setLog] = useState<string[]>([]);
  const [difficulty, setDifficulty] = useState<"easy" | "hard">("easy");
  const wsRef = useRef<WebSocket | null>(null);
  const logRef = useRef<HTMLDivElement>(null);
  const playAreaRef = useRef<HTMLDivElement>(null);

  const [keyboardHeldNotes, setKeyboardHeldNotes] = useState<Set<number>>(new Set());
  /** Live notes from physical piano (backend MIDI) - for real-time visual feedback */
  const [livePianoNotes, setLivePianoNotes] = useState<string[] | null>(null);
  const liveNotesThrottleRef = useRef<{ timer: ReturnType<typeof setTimeout> | null; pending: string[] | null }>({
    timer: null,
    pending: null,
  });

  // Live chord graph state — starts empty until user plays a chord or clicks Demo
  const [chordGraphState, setChordGraphState] = useState<ChordGraphState | null>(null);
  const [notesMap, setNotesMap] = useState<Record<string, string[]>>({});

  const prevChordGraphStateRef = useRef<ChordGraphState | null>(null);
  useEffect(() => {
    prevChordGraphStateRef.current = chordGraphState;
  });

  // Hydrate from history seed when navigating from History page ("play from here")
  useEffect(() => {
    try {
      const raw = sessionStorage.getItem(HISTORY_SEED_KEY);
      if (!raw) return;
      const seed: HistorySeed = JSON.parse(raw);
      sessionStorage.removeItem(HISTORY_SEED_KEY);
      setChordGraphState({
        current: seed.current,
        previous: seed.previous ?? [],
        next: seed.next,
      });
      setNotesMap(seed.notesMap);
      setHistoryBannerChord(seed.current.chordId);
      demoModeRef.current = false; // Allow WebSocket to take over when user plays
      const t = setTimeout(() => setHistoryBannerChord(null), 3000);
      return () => clearTimeout(t);
    } catch {
      // Ignore parse errors or missing key
    }
  }, []);

  // Transform WebSocket data to ChordGraphState format
  function transformToChordGraphState(chordMsg: ChordMsg): ChordGraphState | null {
    // If no chord name, return null (no visualization)
    if (!chordMsg.chord.name) {
      return null;
    }

    // Create current chord node
    const current = {
      id: `current-${Date.now()}`,
      chordId: chordMsg.chord.name,
    };

    // Transform suggestions to next nodes
    // Convert tension to probability: lower tension = higher probability
    const maxTension = Math.max(...chordMsg.suggestions.map(s => s.tension), 0.01);
    const next = chordMsg.suggestions.slice(0, 3).map((suggestion, i) => ({
      id: `next-${i}-${Date.now()}`,
      chordId: suggestion.name,
      // Invert tension: lower tension = better = higher probability
      probability: 1 - (suggestion.tension / maxTension),
    }));

    return {
      current,
      previous: [], // Not using previous for now
      next,
    };
  }

  // Create notes map from WebSocket data
  function createNotesMap(chordMsg: ChordMsg): Record<string, string[]> {
    const notesMap: Record<string, string[]> = {};

    // Add current chord notes
    if (chordMsg.chord.name) {
      notesMap[chordMsg.chord.name] = chordMsg.chord.notes;
    }

    // Add suggestion notes
    chordMsg.suggestions.forEach(suggestion => {
      notesMap[suggestion.name] = suggestion.notes;
    });

    return notesMap;
  }

  function sendDifficulty(diff: "easy" | "hard") {
    setDifficulty(diff);
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "set_difficulty", difficulty: diff }));
    }
  }

  function addLog(msg: string) {
    setLog((prev) => [...prev.slice(-99), `${new Date().toLocaleTimeString()} ${msg}`]);
  }

  function connect() {
    if (wsRef.current) {
      wsRef.current.close();
    }
    setStatus("connecting");
    addLog("Connecting to ws://localhost:8000/ws ...");

    const ws = new WebSocket("ws://localhost:8000/ws");
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus("connected");
      demoModeRef.current = false; // Switch to live mode when connected
      addLog("Connected!");
      console.log("✅ WebSocket CONNECTED");
      ws.send(JSON.stringify({ type: "set_difficulty", difficulty }));
    };

    ws.onmessage = (e) => {
      console.log("📨 Raw WebSocket message received:", e.data);
      try {
        const data = JSON.parse(e.data) as ChordMsg | { type: "live_notes"; notes: string[] };
        console.log("📦 Parsed data:", data);

        if (data.type === "live_notes") {
          const notes = data.notes as string[];
          const throttle = liveNotesThrottleRef.current;
          throttle.pending = notes;
          if (throttle.timer === null) {
            setLivePianoNotes(notes);
            throttle.timer = setTimeout(() => {
              if (throttle.pending !== null) {
                setLivePianoNotes(throttle.pending);
                throttle.pending = null;
              }
              throttle.timer = null;
            }, 50);
          }
          return;
        }

        if (data.type === "chord") {
          setChord(data.chord);
          setSuggestions(data.suggestions);
          if (data.chord.notes.length === 0) setKeyboardHeldNotes(new Set());
          if (data.chord.notes.length > 0) {
            setLastChord(data.chord);
          }
          if (data.suggestions.length > 0) {
            setLastSuggestions(data.suggestions);
          }
          const sugStr = data.suggestions.length
            ? data.suggestions.map((s) => `${s.name} [${s.chroma.join("")}] (t:${s.tension})`).join(", ")
            : "none";
          addLog(`chord: ${data.chord.name ?? "(none)"} | notes: [${data.chord.notes.join(", ")}] | suggestions: ${sugStr}`);

          // Transform and update visualization
          const baseState = transformToChordGraphState(data);
          const transformedNotesMap = createNotesMap(data);
          console.log("🎹 WebSocket Message Received:");
          console.log("  Original:", data);
          console.log("  Base State:", baseState);
          console.log("  Notes Map:", transformedNotesMap);

          if (baseState && !demoModeRef.current) {
            // New chord: add old current to front of history; only drop the oldest (tail) when over max
            // Skip when demoMode is true so Demo state isn't overwritten by live chords
            setChordGraphState((prev) => {
              if (!prev) return baseState;
              const chordChanged =
                baseState.current.chordId &&
                prev.current.chordId &&
                baseState.current.chordId !== prev.current.chordId;
              const newPrevious = chordChanged
                ? [
                    { id: `prev-${Date.now()}`, chordId: prev.current.chordId },
                    ...prev.previous,
                  ].slice(0, 5) // keep newest 5, drop only the oldest
                : prev.previous;
              return { ...baseState, previous: newPrevious };
            });
            setNotesMap((prevMap) => ({ ...prevMap, ...transformedNotesMap }));
          }
        }
      } catch {
        addLog(`raw: ${e.data}`);
      }
    };

    ws.onclose = () => {
      setStatus("disconnected");
      setLivePianoNotes(null);
      const t = liveNotesThrottleRef.current;
      if (t.timer) clearTimeout(t.timer);
      t.timer = null;
      t.pending = null;
      addLog("Disconnected");
    };

    ws.onerror = () => {
      addLog("WebSocket error");
    };
  }

  function disconnect() {
    wsRef.current?.close();
  }

  const sendNotesToBackend = useCallback((notes: number[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "notes", notes }));
    }
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable) return;
      const midi = KEY_TO_MIDI[e.key.toLowerCase()];
      if (midi === undefined || e.repeat) return;
      e.preventDefault();
      setKeyboardHeldNotes((prev) => new Set(prev).add(midi));
    };
    const handleKeyUp = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable) return;
      const midi = KEY_TO_MIDI[e.key.toLowerCase()];
      if (midi === undefined || e.repeat) return;
      e.preventDefault();
      setKeyboardHeldNotes((prev) => {
        const next = new Set(prev);
        next.delete(midi);
        return next;
      });
    };
    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
    };
  }, []);

  useEffect(() => {
    if (status !== "connected") return;
    const notes = Array.from(keyboardHeldNotes).sort((a, b) => a - b);
    sendNotesToBackend(notes);
  }, [keyboardHeldNotes, status, sendNotesToBackend]);

  useEffect(() => {
    if (status === "connected" && playAreaRef.current) {
      playAreaRef.current.focus({ preventScroll: true });
    }
  }, [status]);

  const endSession = async () => {
    try {
      const response = await fetch("http://localhost:8000/end-session", {
        method: "POST",
      });
      const data = await response.json();
      if (data.status === "session_ended") {
        addLog("Session saved and reset");
      }
    } catch (err) {
      console.error("Failed to end session:", err);
      addLog("Error ending session");
    }
  };

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [log]);

  useEffect(() => {
    return () => wsRef.current?.close();
  }, []);

  const statusDotColor =
    status === "connected"
      ? "#7868c0"
      : status === "connecting"
        ? "#a890c8"
        : "#a898a8";

  // Fallback when chordGraphState is cleared (e.g. Release with no name)
  const fallbackChordGraphState: ChordGraphState = {
    current: { id: "fallback-current", chordId: "?" },
    previous: [],
    next: [],
  };

  const fallbackNotesMap = { "?": [] };

  // Demo mode: 0→1→2→3→4→5, then sticks at 5 and add-one-drop-earliest
  const DEMO_STATES: { state: ChordGraphState; notesMap: Record<string, string[]> }[] = [
    {
      state: {
        current: { id: "d1-c", chordId: "C" },
        previous: [], // Start: no history yet
        next: [
          { id: "d1-n0", chordId: "F", probability: 0.8 },
          { id: "d1-n1", chordId: "G", probability: 0.75 },
          { id: "d1-n2", chordId: "Am", probability: 0.85 },
        ],
      },
      notesMap: { C: ["C", "E", "G"], F: ["F", "A", "C"], G: ["G", "B", "D"], Am: ["A", "C", "E"] },
    },
    {
      state: {
        current: { id: "d2-c", chordId: "F" },
        previous: [{ id: "d2-p0", chordId: "C" }],
        next: [
          { id: "d2-n0", chordId: "G", probability: 0.9 },
          { id: "d2-n1", chordId: "Am", probability: 0.7 },
          { id: "d2-n2", chordId: "C", probability: 0.65 },
        ],
      },
      notesMap: { F: ["F", "A", "C"], G: ["G", "B", "D"], Am: ["A", "C", "E"], C: ["C", "E", "G"] },
    },
    {
      state: {
        current: { id: "d3-c", chordId: "Am" },
        previous: [
          { id: "d3-p0", chordId: "F" },
          { id: "d3-p1", chordId: "C" },
        ],
        next: [
          { id: "d3-n0", chordId: "F", probability: 0.88 },
          { id: "d3-n1", chordId: "G", probability: 0.72 },
          { id: "d3-n2", chordId: "Em", probability: 0.6 },
        ],
      },
      notesMap: { Am: ["A", "C", "E"], F: ["F", "A", "C"], G: ["G", "B", "D"], Em: ["E", "G", "B"] },
    },
    {
      state: {
        current: { id: "d4-c", chordId: "G" },
        previous: [
          { id: "d4-p0", chordId: "Am" },
          { id: "d4-p1", chordId: "F" },
          { id: "d4-p2", chordId: "C" },
        ],
        next: [
          { id: "d4-n0", chordId: "C", probability: 0.95 },
          { id: "d4-n1", chordId: "Am", probability: 0.8 },
          { id: "d4-n2", chordId: "D", probability: 0.5 },
        ],
      },
      notesMap: { G: ["G", "B", "D"], C: ["C", "E", "G"], Am: ["A", "C", "E"], D: ["D", "F#", "A"], F: ["F", "A", "C"] },
    },
    {
      state: {
        current: { id: "d5-c", chordId: "C" },
        previous: [
          { id: "d5-p0", chordId: "G" },
          { id: "d5-p1", chordId: "Am" },
          { id: "d5-p2", chordId: "F" },
          { id: "d5-p3", chordId: "C" },
        ],
        next: [
          { id: "d5-n0", chordId: "F", probability: 0.95 },
          { id: "d5-n1", chordId: "G", probability: 0.8 },
          { id: "d5-n2", chordId: "Am", probability: 0.6 },
        ],
      },
      notesMap: { C: ["C", "E", "G"], F: ["F", "A", "C"], G: ["G", "B", "D"], Am: ["A", "C", "E"] },
    },
    {
      state: {
        current: { id: "d6-c", chordId: "F" },
        previous: [
          { id: "d6-p0", chordId: "C" },
          { id: "d6-p1", chordId: "G" },
          { id: "d6-p2", chordId: "Am" },
          { id: "d6-p3", chordId: "F" },
          { id: "d6-p4", chordId: "C" },
        ],
        next: [
          { id: "d6-n0", chordId: "G", probability: 0.9 },
          { id: "d6-n1", chordId: "Am", probability: 0.7 },
          { id: "d6-n2", chordId: "C", probability: 0.65 },
        ],
      },
      notesMap: { F: ["F", "A", "C"], G: ["G", "B", "D"], Am: ["A", "C", "E"], C: ["C", "E", "G"] },
    },
  ];
  const [demoIndex, setDemoIndex] = useState(0);
  const demoModeRef = useRef(false); // When true, WebSocket chord updates are ignored (Demo takes over)
  const CHORD_CYCLE = ["C", "F", "Am", "G"] as const;
  const DEMO_NEXT: Record<string, ChordGraphState["next"]> = {
    C: [
      { id: "next-0", chordId: "F", probability: 0.8 },
      { id: "next-1", chordId: "G", probability: 0.75 },
      { id: "next-2", chordId: "Am", probability: 0.85 },
    ],
    F: [
      { id: "next-0", chordId: "G", probability: 0.9 },
      { id: "next-1", chordId: "Am", probability: 0.7 },
      { id: "next-2", chordId: "C", probability: 0.65 },
    ],
    Am: [
      { id: "next-0", chordId: "F", probability: 0.88 },
      { id: "next-1", chordId: "G", probability: 0.72 },
      { id: "next-2", chordId: "Em", probability: 0.6 },
    ],
    G: [
      { id: "next-0", chordId: "C", probability: 0.95 },
      { id: "next-1", chordId: "Am", probability: 0.8 },
      { id: "next-2", chordId: "D", probability: 0.5 },
    ],
  };
  const cycleDemo = () => {
    demoModeRef.current = true; // Take over from live state when user clicks Demo
    const n = DEMO_STATES.length;
    const maxIdx = n - 1; // 5

    if (demoIndex < maxIdx) {
      // 0→1→2→3→4→5: advance to next state
      const nextIndex = demoIndex + 1;
      const next = DEMO_STATES[nextIndex];
      setDemoIndex(nextIndex);
      setChordGraphState(next.state);
      setNotesMap(next.notesMap);
    } else {
      // Sticks at 5: add one to history, drop the earliest
      setChordGraphState((prev) => {
        if (!prev) return DEMO_STATES[maxIdx].state;
        const cycleIdx = CHORD_CYCLE.indexOf(prev.current.chordId as (typeof CHORD_CYCLE)[number]);
        const nextChordId = CHORD_CYCLE[(cycleIdx + 1) % CHORD_CYCLE.length];
        const newPrevious = [
          { id: `prev-${Date.now()}`, chordId: prev.current.chordId },
          ...prev.previous,
        ].slice(0, 5);
        return {
          current: { id: `current-${Date.now()}`, chordId: nextChordId },
          previous: newPrevious,
          next: DEMO_NEXT[nextChordId] ?? prev.next,
        };
      });
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 font-[family-name:var(--font-patrick-hand)]">
      {/* Bubble Visualization - each sphere has its keyboard directly below it */}
      <div className="relative w-full h-screen">
        <Background />

        {/* Connection controls overlay — 2.5d cool pastel theme */}
        <div
          className="absolute top-4 left-4 z-10 flex items-center gap-3 px-4 py-2.5 rounded-xl shadow-lg"
          style={{
            background: 'linear-gradient(145deg, rgba(248, 244, 252, 0.92) 0%, rgba(236, 228, 248, 0.88) 100%)',
            backdropFilter: 'blur(12px)',
            border: '1px solid rgba(196, 184, 208, 0.5)',
            boxShadow: `
              0 4px 20px rgba(168, 140, 200, 0.15),
              0 1px 3px rgba(0,0,0,0.06),
              inset 0 1px 0 rgba(255,255,255,0.6)
            `,
          }}
        >
          <span
            className="w-2.5 h-2.5 rounded-full ring-2 ring-white/60 shadow-sm"
            style={{ backgroundColor: statusDotColor }}
          />
          <span className="text-sm font-medium" style={{ color: '#5c4a6c' }}>{status}</span>
          {status === "disconnected" ? (
            <button
              onClick={connect}
              className="px-3 py-1.5 rounded-lg text-white text-sm font-medium transition-all hover:brightness-110"
              style={{
                background: 'linear-gradient(160deg, #9080d8 0%, #7868c0 100%)',
                boxShadow: '0 2px 8px rgba(120, 104, 192, 0.35), inset 0 1px 0 rgba(255,255,255,0.2)',
              }}
            >
              Connect
            </button>
          ) : (
            <button
              onClick={disconnect}
              className="px-3 py-1.5 rounded-lg text-white text-sm font-medium transition-all hover:brightness-110"
              style={{
                background: 'linear-gradient(160deg, #8878b0 0%, #7060a0 100%)',
                boxShadow: '0 2px 8px rgba(112, 96, 160, 0.35), inset 0 1px 0 rgba(255,255,255,0.2)',
              }}
            >
              Disconnect
            </button>
          )}
          <Link
            href="/history"
            className="px-3 py-1.5 rounded-lg text-white text-sm font-medium transition-all hover:brightness-110"
            style={{
              background: 'linear-gradient(160deg, #9080d8 0%, #7868c0 100%)',
              boxShadow: '0 2px 8px rgba(120, 104, 192, 0.35), inset 0 1px 0 rgba(255,255,255,0.2)',
            }}
          >
            View History →
          </Link>
          <button
            onClick={endSession}
            className="px-3 py-1.5 rounded-lg text-white text-sm font-medium transition-all hover:brightness-110"
            style={{
              background: 'linear-gradient(160deg, #9878c8 0%, #8068b0 100%)',
              boxShadow: '0 2px 8px rgba(128, 104, 176, 0.35), inset 0 1px 0 rgba(255,255,255,0.2)',
            }}
          >
            End Session
          </button>
          <button
            onClick={cycleDemo}
            className="px-3 py-1.5 rounded-lg text-white text-sm font-medium transition-all hover:brightness-110"
            style={{
              background: 'linear-gradient(160deg, #a888d8 0%, #9070c8 100%)',
              boxShadow: '0 2px 8px rgba(144, 112, 216, 0.35), inset 0 1px 0 rgba(255,255,255,0.2)',
            }}
            title="Cycle chord states to test animations (no keyboard needed)"
          >
            Demo
          </button>

          {/* Difficulty toggle */}
          <div
            className="flex rounded-lg overflow-hidden"
            style={{
              border: '1px solid rgba(196, 184, 208, 0.5)',
              boxShadow: '0 2px 6px rgba(168, 140, 200, 0.15)',
            }}
          >
            <button
              onClick={() => sendDifficulty("easy")}
              className="px-3 py-1.5 text-sm font-medium transition-all"
              style={
                difficulty === "easy"
                  ? {
                      background: 'linear-gradient(160deg, #9080d8 0%, #7868c0 100%)',
                      color: '#fff',
                      boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.2)',
                    }
                  : {
                      background: 'rgba(248, 244, 252, 0.4)',
                      color: '#8878a0',
                    }
              }
            >
              Easy
            </button>
            <button
              onClick={() => sendDifficulty("hard")}
              className="px-3 py-1.5 text-sm font-medium transition-all"
              style={
                difficulty === "hard"
                  ? {
                      background: 'linear-gradient(160deg, #d87888 0%, #c06078 100%)',
                      color: '#fff',
                      boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.2)',
                    }
                  : {
                      background: 'rgba(248, 244, 252, 0.4)',
                      color: '#8878a0',
                    }
              }
            >
              Hard
            </button>
          </div>
        </div>

        {historyBannerChord && (
          <div
            className="absolute top-16 left-1/2 -translate-x-1/2 z-20 px-4 py-2 rounded-lg text-sm font-medium"
            style={{
              background: 'linear-gradient(145deg, rgba(248, 244, 252, 0.95) 0%, rgba(236, 228, 248, 0.9) 100%)',
              border: '1px solid rgba(196, 184, 208, 0.6)',
              color: '#5c4a6c',
              boxShadow: '0 4px 12px rgba(168, 140, 200, 0.2)',
            }}
          >
            Playing from {historyBannerChord} in session
          </div>
        )}

        <div className="absolute inset-0 z-[1]" tabIndex={0} ref={playAreaRef}>
          <ChordGraph
            state={chordGraphState}
            previousState={prevChordGraphStateRef.current}
            keyboardMode={true}
            notesMap={notesMap || fallbackNotesMap}
            activeNotes={
              livePianoNotes !== null
                ? livePianoNotes
                : keyboardHeldNotes.size > 0
                  ? midiNotesToNames(Array.from(keyboardHeldNotes))
                  : (chord?.notes ?? [])
            }
          />
        </div>
      </div>

      {/* Log */}
      <div className="p-8">
        <h2 className="text-sm text-zinc-400 mb-2 uppercase tracking-wide">Event Log</h2>
        <div
          ref={logRef}
          className="bg-zinc-900 rounded-lg p-4 border border-zinc-800 h-48 overflow-y-auto text-xs font-mono"
        >
          {log.length === 0 ? (
            <p className="text-zinc-600">No events yet</p>
          ) : (
            log.map((entry, i) => (
              <p key={i} className="text-zinc-400">
                {entry}
              </p>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
