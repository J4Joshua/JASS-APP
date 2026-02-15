"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";

type ChordMsg = {
  type: "chord";
  chord: { name: string | null; notes: string[]; chroma: number[] };
  suggestions: { name: string; notes: string[]; chroma: number[]; tension: number }[];
};

const NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];

export default function Home() {
  const [status, setStatus] = useState<"disconnected" | "connecting" | "connected">("disconnected");
  const [chord, setChord] = useState<ChordMsg["chord"] | null>(null);
  const [suggestions, setSuggestions] = useState<ChordMsg["suggestions"]>([]);
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

  const statusColor =
    status === "connected" ? "bg-green-500" : status === "connecting" ? "bg-yellow-500" : "bg-red-500";

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-8 font-[family-name:var(--font-geist-mono)]">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">JASS - MIDI WebSocket Test</h1>
        <Link href="/history" className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded transition text-sm">
          View History →
        </Link>
      </div>

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
        <button onClick={endSession} className="px-4 py-1.5 bg-emerald-600 rounded hover:bg-emerald-700 text-sm">
          End Session
        </button>
      </div>

      {/* Current Chord */}
      <div className="mb-8">
        <h2 className="text-sm text-zinc-400 mb-2 uppercase tracking-wide">Current Chord</h2>
        <div className="bg-zinc-900 rounded-lg p-6 border border-zinc-800">
          {chord && chord.notes.length > 0 ? (
            <>
              <p className="text-4xl font-bold mb-2">{chord.name ?? "?"}</p>
              <p className="text-zinc-400">Notes: {chord.notes.join(" - ")}</p>
              {/* Piano-style chroma display */}
              <div className="flex gap-1 mt-4">
                {chord.chroma.map((v, i) => (
                  <div
                    key={i}
                    className={`flex flex-col items-center gap-1 ${
                      v ? "text-white" : "text-zinc-600"
                    }`}
                  >
                    <div
                      className={`w-8 h-10 rounded ${
                        v ? "bg-blue-500" : "bg-zinc-800"
                      }`}
                    />
                    <span className="text-xs">{NOTE_NAMES[i]}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="text-zinc-500 italic">Play some notes on your MIDI keyboard...</p>
          )}
        </div>
      </div>

      {/* Suggestions */}
      {suggestions.length > 0 && (
        <div className="mb-8">
          <h2 className="text-sm text-zinc-400 mb-2 uppercase tracking-wide">Suggestions</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {suggestions.map((s, i) => (
              <div key={i} className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
                <p className="font-bold text-lg">{s.name}</p>
                <p className="text-sm text-zinc-400">{s.notes.join(" - ")}</p>
                <p className="text-xs text-zinc-500 mt-1">tension: {s.tension}</p>
                <div className="flex gap-0.5 mt-2">
                  {s.chroma.map((v, j) => (
                    <div
                      key={j}
                      className={`w-5 h-6 rounded-sm ${v ? "bg-emerald-500" : "bg-zinc-800"}`}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

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
