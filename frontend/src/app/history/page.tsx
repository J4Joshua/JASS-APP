"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";

const NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];

type Node = {
  uuid: string;
  name: string;
  depth: number;
  chroma: number[];
};

type Relation = {
  uuid: string;
  source_node: string;
  target_node: string;
};

type Session = {
  filename: string;
  timestamp: string;
  total_depth: number;
  node_count: number;
};

type SessionData = {
  timestamp: string;
  nodes: Node[];
  relations: Relation[];
  total_depth: number;
};

type ChordEvent = {
  timestamp: number;
  chord: { name: string | null; notes: string[]; chroma: number[] };
  suggestions: { name: string; notes: string[]; chroma: number[]; tension: number }[];
};

type ChordMsg = {
  type: "chord";
  chord: { name: string | null; notes: string[]; chroma: number[] };
  suggestions: { name: string; notes: string[]; chroma: number[]; tension: number }[];
};

export default function History() {
  const [status, setStatus] = useState<"disconnected" | "connecting" | "connected">("disconnected");
  const [chordHistory, setChordHistory] = useState<ChordEvent[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedSession, setSelectedSession] = useState<SessionData | null>(null);
  const [depthRange, setDepthRange] = useState<[number, number]>([0, 0]);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    fetchSessions();
  }, []);

  async function fetchSessions() {
    try {
      const response = await fetch("http://localhost:8000/sessions");
      const data = await response.json();
      setSessions(data.sessions || []);
    } catch (err) {
      console.error("Failed to fetch sessions:", err);
    }
  }

  async function loadSession(filename: string) {
    try {
      const response = await fetch(`http://localhost:8000/sessions/${filename}`);
      const data: SessionData = await response.json();
      setSelectedSession(data);
      setDepthRange([0, data.total_depth]);
    } catch (err) {
      console.error("Failed to load session:", err);
    }
  }

  function connect() {
    if (wsRef.current) {
      wsRef.current.close();
    }
    setStatus("connecting");

    const ws = new WebSocket("ws://localhost:8000/ws");
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus("connected");
    };

    ws.onmessage = (e) => {
      if (!isRecording) return;
      try {
        const data: ChordMsg = JSON.parse(e.data);
        if (data.type === "chord") {
          setChordHistory((prev) => [
            ...prev,
            {
              timestamp: Date.now(),
              chord: data.chord,
              suggestions: data.suggestions,
            },
          ]);
        }
      } catch (err) {
        console.error("Failed to parse message:", err);
      }
    };

    ws.onerror = () => {
      setStatus("disconnected");
    };

    ws.onclose = () => {
      setStatus("disconnected");
    };
  }

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const exportJSON = () => {
    const export_data = {
      recorded_at: new Date().toISOString(),
      events: chordHistory,
      total_events: chordHistory.length,
    };
    const blob = new Blob([JSON.stringify(export_data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `chord-history-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const clearHistory = () => {
    setChordHistory([]);
  };

  const endSession = async () => {
    try {
      const response = await fetch("http://localhost:8000/end-session", {
        method: "POST",
      });
      const data = await response.json();
      if (data.status === "session_ended") {
        setChordHistory([]);
        fetchSessions();
        alert("Session saved successfully!");
      }
    } catch (err) {
      console.error("Failed to end session:", err);
      alert("Error ending session");
    }
  };

  const statusColor =
    status === "connected" ? "bg-green-500" : status === "connecting" ? "bg-yellow-500" : "bg-red-500";

  // Filter nodes by depth range
  const filteredNodes = selectedSession
    ? selectedSession.nodes.filter((n) => n.depth >= depthRange[0] && n.depth <= depthRange[1])
    : [];

  // Find edges that connect nodes within filtered depth range and have same name
  const filteredRelations = selectedSession
    ? selectedSession.relations.filter((rel) => {
        const source = selectedSession.nodes.find((n) => n.uuid === rel.source_node);
        const target = selectedSession.nodes.find((n) => n.uuid === rel.target_node);
        if (!source || !target) return false;
        const sourceInRange = source.depth >= depthRange[0] && source.depth <= depthRange[1];
        const targetInRange = target.depth >= depthRange[0] && target.depth <= depthRange[1];
        return sourceInRange && targetInRange && source.name === target.name;
      })
    : [];

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-8 font-[family-name:var(--font-geist-mono)]">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold">Chord History</h1>
        <Link href="/" className="px-4 py-1.5 bg-zinc-700 rounded hover:bg-zinc-600 text-sm">
          ← Back to Live
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Panel: Sessions & Recording */}
        <div className="lg:col-span-1 space-y-6">
          {/* Recording Section */}
          <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
            <h2 className="text-sm text-zinc-400 mb-3 uppercase tracking-wide">Live Recording</h2>
            <div className="flex items-center gap-2 mb-3">
              <span className={`w-3 h-3 rounded-full ${statusColor}`} />
              <span className="text-sm">{status}</span>
            </div>
            <label className="flex items-center gap-2 cursor-pointer text-sm mb-4">
              <input
                type="checkbox"
                checked={isRecording}
                onChange={(e) => setIsRecording(e.target.checked)}
                disabled={status !== "connected"}
                className="cursor-pointer"
              />
              <span>Recording</span>
            </label>
            <div className="space-y-2">
              <button
                onClick={exportJSON}
                disabled={chordHistory.length === 0}
                className="w-full px-3 py-1.5 bg-blue-600 rounded hover:bg-blue-500 disabled:bg-zinc-700 disabled:cursor-not-allowed text-xs"
              >
                Export JSON
              </button>
              <button
                onClick={clearHistory}
                disabled={chordHistory.length === 0}
                className="w-full px-3 py-1.5 bg-zinc-700 rounded hover:bg-zinc-600 disabled:cursor-not-allowed text-xs"
              >
                Clear
              </button>
              <button
                onClick={endSession}
                disabled={chordHistory.length === 0}
                className="w-full px-3 py-1.5 bg-emerald-600 rounded hover:bg-emerald-700 disabled:bg-zinc-700 disabled:cursor-not-allowed text-xs"
              >
                End Session
              </button>
            </div>
          </div>

          {/* Sessions List */}
          <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
            <h2 className="text-sm text-zinc-400 mb-3 uppercase tracking-wide">Sessions</h2>
            <div className="space-y-1 max-h-96 overflow-y-auto">
              {sessions.length === 0 ? (
                <p className="text-xs text-zinc-600">No sessions yet</p>
              ) : (
                sessions.map((session) => (
                  <button
                    key={session.filename}
                    onClick={() => loadSession(session.filename)}
                    className={`w-full text-left px-2 py-1 rounded text-xs transition ${
                      selectedSession && 
                      selectedSession.timestamp === session.timestamp
                        ? "bg-blue-600"
                        : "bg-zinc-800 hover:bg-zinc-700"
                    }`}
                  >
                    <div className="font-mono text-xs">{session.timestamp}</div>
                    <div className="text-zinc-400 text-xs">
                      {session.node_count} nodes • depth {session.total_depth}
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right Panel: Graph Visualization */}
        <div className="lg:col-span-3">
          {selectedSession ? (
            <div className="space-y-4">
              {/* Graph */}
              <div className="bg-zinc-900 rounded-lg p-6 border border-zinc-800 overflow-auto" style={{ height: "500px" }}>
                <svg width="100%" height="100%" style={{ minHeight: "500px" }}>
                  {/* Draw edges */}
                  {filteredRelations.map((rel) => {
                    const source = selectedSession.nodes.find((n) => n.uuid === rel.source_node);
                    const target = selectedSession.nodes.find((n) => n.uuid === rel.target_node);
                    if (!source || !target) return null;

                    const sourceX = source.depth * 120 + 60;
                    const targetX = target.depth * 120 + 60;
                    const sourceY = filteredNodes.filter((n) => n.depth === source.depth).indexOf(source) * 60 + 40;
                    const targetY = filteredNodes.filter((n) => n.depth === target.depth).indexOf(target) * 60 + 40;

                    return (
                      <line
                        key={rel.uuid}
                        x1={sourceX}
                        y1={sourceY}
                        x2={targetX}
                        y2={targetY}
                        stroke="#666"
                        strokeWidth="2"
                        markerEnd="url(#arrowhead)"
                      />
                    );
                  })}

                  {/* Arrow marker */}
                  <defs>
                    <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
                      <polygon points="0 0, 10 3, 0 6" fill="#666" />
                    </marker>
                  </defs>

                  {/* Draw nodes */}
                  {filteredNodes.map((node) => {
                    const nodesAtDepth = filteredNodes.filter((n) => n.depth === node.depth);
                    const x = node.depth * 120 + 60;
                    const y = nodesAtDepth.indexOf(node) * 60 + 40;

                    return (
                      <g key={node.uuid}>
                        {/* Node circle */}
                        <circle
                          cx={x}
                          cy={y}
                          r="20"
                          fill={node.name ? "#3b82f6" : "#666"}
                          opacity="0.8"
                        />
                        {/* Node label */}
                        <text
                          x={x}
                          y={y}
                          textAnchor="middle"
                          dy="0.3em"
                          fill="white"
                          fontSize="10"
                          fontWeight="bold"
                        >
                          {node.name.substring(0, 3)}
                        </text>
                        {/* Depth label below */}
                        <text
                          x={x}
                          y={y + 35}
                          textAnchor="middle"
                          fill="#999"
                          fontSize="8"
                        >
                          d:{node.depth}
                        </text>
                      </g>
                    );
                  })}
                </svg>
              </div>

              {/* Depth Slider */}
              <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
                <div className="flex items-center gap-4">
                  <label className="text-xs text-zinc-400">Depth Range:</label>
                  <input
                    type="range"
                    min="0"
                    max={selectedSession.total_depth}
                    value={depthRange[0]}
                    onChange={(e) => setDepthRange([parseInt(e.target.value), depthRange[1]])}
                    className="flex-1"
                  />
                  <span className="text-xs font-mono">{depthRange[0]}</span>
                  <span className="text-xs">to</span>
                  <input
                    type="range"
                    min="0"
                    max={selectedSession.total_depth}
                    value={depthRange[1]}
                    onChange={(e) => setDepthRange([depthRange[0], parseInt(e.target.value)])}
                    className="flex-1"
                  />
                  <span className="text-xs font-mono">{depthRange[1]}</span>
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-zinc-900 rounded-lg p-3 border border-zinc-800">
                  <p className="text-xs text-zinc-500 mb-1">Visible Nodes</p>
                  <p className="text-xl font-bold">{filteredNodes.length}</p>
                </div>
                <div className="bg-zinc-900 rounded-lg p-3 border border-zinc-800">
                  <p className="text-xs text-zinc-500 mb-1">Visible Edges</p>
                  <p className="text-xl font-bold">{filteredRelations.length}</p>
                </div>
                <div className="bg-zinc-900 rounded-lg p-3 border border-zinc-800">
                  <p className="text-xs text-zinc-500 mb-1">Total Depth</p>
                  <p className="text-xl font-bold">{selectedSession.total_depth}</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-zinc-900 rounded-lg p-6 border border-zinc-800 h-96 flex items-center justify-center">
              <p className="text-zinc-600">Select a session to view its chord progression graph</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
