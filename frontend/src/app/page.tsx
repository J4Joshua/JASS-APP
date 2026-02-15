"use client";

import { useEffect, useRef, useState } from "react";
import ChordKeyboard from "@/components/ChordKeyboard";

type ChordMsg = {
  type: "chord";
  chord: { name: string | null; notes: string[]; chroma: number[] };
  suggestions: { name: string; notes: string[]; chroma: number[]; tension: number }[];
};


export default function Home() {
  const [status, setStatus] = useState<"disconnected" | "connecting" | "connected">("disconnected");
  const [chord, setChord] = useState<ChordMsg["chord"] | null>(null);
  const [lastChord, setLastChord] = useState<ChordMsg["chord"] | null>(null);
  const [suggestions, setSuggestions] = useState<ChordMsg["suggestions"]>([]);
  const [lastSuggestions, setLastSuggestions] = useState<ChordMsg["suggestions"]>([]);
  const [log, setLog] = useState<string[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const logRef = useRef<HTMLDivElement>(null);

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
      addLog("Connected!");
    };

    ws.onmessage = (e) => {
      try {
        const data: ChordMsg = JSON.parse(e.data);
        if (data.type === "chord") {
          setChord(data.chord);
          setSuggestions(data.suggestions);
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
        }
      } catch {
        addLog(`raw: ${e.data}`);
      }
    };

    ws.onclose = () => {
      setStatus("disconnected");
      addLog("Disconnected");
    };

    ws.onerror = () => {
      addLog("WebSocket error");
    };
  }

  function disconnect() {
    wsRef.current?.close();
  }

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [log]);

  useEffect(() => {
    return () => wsRef.current?.close();
  }, []);

  const statusColor =
    status === "connected" ? "bg-green-500" : status === "connecting" ? "bg-yellow-500" : "bg-red-500";

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-8 font-[family-name:var(--font-geist-mono)]">
      <h1 className="text-2xl font-bold mb-6">JASS - MIDI WebSocket Test</h1>

      {/* Connection */}
      <div className="flex items-center gap-4 mb-8">
        <span className={`w-3 h-3 rounded-full ${statusColor}`} />
        <span className="text-sm">{status}</span>
        {status === "disconnected" ? (
          <button onClick={connect} className="px-4 py-1.5 bg-blue-600 rounded hover:bg-blue-500 text-sm">
            Connect
          </button>
        ) : (
          <button onClick={disconnect} className="px-4 py-1.5 bg-zinc-700 rounded hover:bg-zinc-600 text-sm">
            Disconnect
          </button>
        )}
      </div>

      {/* Current Chord */}
      <div className="mb-8">
        <h2 className="text-sm text-zinc-400 mb-2 uppercase tracking-wide">Current Chord</h2>
        {(() => {
          const active = chord && chord.notes.length > 0;
          const display = active ? chord : lastChord;
          if (display) {
            return (
              <div className={`max-w-xs ${!active ? "opacity-50" : ""}`}>
                <ChordKeyboard
                  name={display.name ?? "?"}
                  notes={display.notes}
                  color="#3B82F6"
                  description={`Notes: ${display.notes.join(" - ")}`}
                />
              </div>
            );
          }
          return (
            <div className="bg-zinc-900 rounded-lg p-6 border border-zinc-800">
              <p className="text-zinc-500 italic">Play some notes on your MIDI keyboard...</p>
            </div>
          );
        })()}
      </div>

      {/* Suggestions */}
      {(() => {
        const active = suggestions.length > 0;
        const display = active ? suggestions : lastSuggestions;
        if (display.length === 0) return null;
        return (
          <div className="mb-8">
            <h2 className="text-sm text-zinc-400 mb-2 uppercase tracking-wide">Suggestions</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {display.map((s, i) => (
                <ChordKeyboard
                  key={i}
                  name={s.name}
                  notes={s.notes}
                  color={["#4ECDC4", "#FF6B6B", "#9B59B6"][i % 3]}
                  description={`tension: ${s.tension}`}
                />
              ))}
            </div>
          </div>
        );
      })()}

      {/* Log */}
      <div>
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
