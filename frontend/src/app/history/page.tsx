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
  session_number: number;
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

  // Deduplicate nodes: merge nodes with same name and depth
  const deduplicatedNodes = selectedSession
    ? (() => {
        const nodesByDepthAndName = new Map<string, Node>();
        const uuidMapping = new Map<string, string>(); // old UUID -> canonical UUID
        
        for (const node of selectedSession.nodes) {
          const key = `${node.depth}:${node.name}`;
          if (!nodesByDepthAndName.has(key)) {
            nodesByDepthAndName.set(key, node);
            uuidMapping.set(node.uuid, node.uuid); // First occurrence is canonical
          } else {
            // Map this duplicate to the canonical UUID
            const canonical = nodesByDepthAndName.get(key)!;
            uuidMapping.set(node.uuid, canonical.uuid);
          }
        }
        
        return {
          nodes: Array.from(nodesByDepthAndName.values()),
          uuidMapping
        };
      })()
    : { nodes: [], uuidMapping: new Map() };

  // Calculate max nodes at any depth for dynamic height
  const maxNodesAtDepth = deduplicatedNodes.nodes.length > 0
    ? Math.max(
        ...Array.from(
          { length: (selectedSession?.total_depth || 0) + 1 },
          (_, depth) => deduplicatedNodes.nodes.filter(n => n.depth === depth).length
        )
      )
    : 0;
  const graphHeight = Math.max(200, maxNodesAtDepth * 60 + 80); // 60px per node + padding

  // Map relations to use deduplicated UUIDs
  const dedupedRelations = selectedSession
    ? selectedSession.relations
        .map((rel) => ({
          ...rel,
          source_node: deduplicatedNodes.uuidMapping.get(rel.source_node) || rel.source_node,
          target_node: deduplicatedNodes.uuidMapping.get(rel.target_node) || rel.target_node,
        }))
        // Remove duplicate edges after UUID mapping
        .filter((rel, idx, arr) => 
          arr.findIndex(r => r.source_node === rel.source_node && r.target_node === rel.target_node) === idx
        )
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
        <div className="lg:col-span-1 space-y-6">

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
                    <div className="font-bold text-sm">Session {session.session_number}</div>
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
              <div className="bg-zinc-900 rounded-lg p-6 border border-zinc-800 overflow-auto" style={{ maxHeight: "600px" }}>
                <svg width={(selectedSession.total_depth + 1) * 120 + 40} height={graphHeight}>
                  {/* Draw edges */}
                  {dedupedRelations.map((rel) => {
                    const source = deduplicatedNodes.nodes.find((n) => n.uuid === rel.source_node);
                    const target = deduplicatedNodes.nodes.find((n) => n.uuid === rel.target_node);
                    if (!source || !target) return null;

                    // Calculate positions
                    const sourceX = source.depth * 120 + 60;
                    const targetX = target.depth * 120 + 60;
                    const sourceY = deduplicatedNodes.nodes.filter((n) => n.depth === source.depth).indexOf(source) * 60 + 40;
                    const targetY = deduplicatedNodes.nodes.filter((n) => n.depth === target.depth).indexOf(target) * 60 + 40;

                    // Check if target node was actually played (has outgoing edges)
                    const targetWasPlayed = dedupedRelations.some(r => r.source_node === target.uuid);

                    return (
                      <line
                        key={rel.uuid}
                        x1={sourceX}
                        y1={sourceY}
                        x2={targetX}
                        y2={targetY}
                        stroke={targetWasPlayed ? "#3b82f6" : "#666"}
                        strokeWidth={targetWasPlayed ? "3" : "1.5"}
                        opacity={targetWasPlayed ? "0.8" : "0.4"}
                        markerEnd={targetWasPlayed ? "url(#arrowhead-played)" : "url(#arrowhead)"}
                      />
                    );
                  })}

                  {/* Arrow markers */}
                  <defs>
                    <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
                      <polygon points="0 0, 10 3, 0 6" fill="#666" />
                    </marker>
                    <marker id="arrowhead-played" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
                      <polygon points="0 0, 10 3, 0 6" fill="#3b82f6" />
                    </marker>
                  </defs>

                  {/* Draw nodes */}
                  {deduplicatedNodes.nodes.map((node) => {
                    const nodesAtDepth = deduplicatedNodes.nodes.filter((n) => n.depth === node.depth);
                    // Calculate position
                    const x = node.depth * 120 + 60;
                    const y = nodesAtDepth.indexOf(node) * 60 + 40;

                    // Check if this node was actually played (has outgoing edges)
                    const wasPlayed = dedupedRelations.some(r => r.source_node === node.uuid);

                    return (
                      <g key={node.uuid}>
                        {/* Node circle */}
                        <circle
                          cx={x}
                          cy={y}
                          r="20"
                          fill={wasPlayed ? "#3b82f6" : "#6b7280"}
                          stroke={wasPlayed ? "#60a5fa" : "#9ca3af"}
                          strokeWidth={wasPlayed ? "2" : "1"}
                          opacity={wasPlayed ? "1" : "0.6"}
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

              {/* Stats */}
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-zinc-900 rounded-lg p-3 border border-zinc-800">
                  <p className="text-xs text-zinc-500 mb-1">Total Nodes</p>
                  <p className="text-xl font-bold">{deduplicatedNodes.nodes.length}</p>
                </div>
                <div className="bg-zinc-900 rounded-lg p-3 border border-zinc-800">
                  <p className="text-xs text-zinc-500 mb-1">Total Edges</p>
                  <p className="text-xl font-bold">{dedupedRelations.length}</p>
                </div>
                <div className="bg-zinc-900 rounded-lg p-3 border border-zinc-800">
                  <p className="text-xs text-zinc-500 mb-1">Total Depth</p>
                  <p className="text-xl font-bold">{selectedSession.total_depth}</p>
                </div>
              </div>

              {/* Legend */}
              <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
                <h3 className="text-xs text-zinc-400 mb-3 uppercase tracking-wide">Legend</h3>
                <div className="grid grid-cols-2 gap-4 text-xs">
                  <div className="flex items-center gap-2">
                    <svg width="24" height="24">
                      <circle cx="12" cy="12" r="8" fill="#3b82f6" stroke="#60a5fa" strokeWidth="2" />
                    </svg>
                    <span className="text-zinc-300">Played chord (has progression)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <svg width="24" height="24">
                      <circle cx="12" cy="12" r="8" fill="#6b7280" stroke="#9ca3af" strokeWidth="1" opacity="0.6" />
                    </svg>
                    <span className="text-zinc-300">Suggested chord (not played)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <svg width="24" height="24">
                      <line x1="2" y1="12" x2="22" y2="12" stroke="#3b82f6" strokeWidth="3" opacity="0.8" />
                    </svg>
                    <span className="text-zinc-300">Played progression</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <svg width="24" height="24">
                      <line x1="2" y1="12" x2="22" y2="12" stroke="#666" strokeWidth="1.5" opacity="0.4" />
                    </svg>
                    <span className="text-zinc-300">Suggested progression</span>
                  </div>
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
