"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Background } from "@/components/Background/Background";

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

type Song = {
  title: string;
  artists: string;
  album: string;
  image_url: string | null;
  spotify_url: string | null;
  original_query: string;
};

export default function History() {
  const [status, setStatus] = useState<"disconnected" | "connecting" | "connected">("disconnected");
  const [chordHistory, setChordHistory] = useState<ChordEvent[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedSession, setSelectedSession] = useState<SessionData | null>(null);
  const [recommendedSongs, setRecommendedSongs] = useState<Song[]>([]);
  const [isLoadingSongs, setIsLoadingSongs] = useState(false);
  const [songsError, setSongsError] = useState<string | null>(null);
  const [chordProgression, setChordProgression] = useState<string | null>(null);
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
      setRecommendedSongs([]);
      setSongsError(null);
      setChordProgression(null);
    } catch (err) {
      console.error("Failed to load session:", err);
    }
  }

  async function fetchRecommendedSongs() {
    if (!selectedSession) return;
    
    // Find the filename from the selected session timestamp
    const sessionFile = sessions.find(s => s.timestamp === selectedSession.timestamp);
    if (!sessionFile) {
      setSongsError("Could not find session file");
      return;
    }

    setIsLoadingSongs(true);
    setSongsError(null);
    setRecommendedSongs([]);

    try {
      const response = await fetch(`http://localhost:8000/recommend-songs/${sessionFile.filename}`);
      const data = await response.json();

      if (data.error) {
        setSongsError(data.error);
      } else {
        setRecommendedSongs(data.songs || []);
        setChordProgression(data.chord_progression);
      }
    } catch (err) {
      setSongsError(err instanceof Error ? err.message : "Failed to fetch recommendations");
      console.error("Failed to fetch recommendations:", err);
    } finally {
      setIsLoadingSongs(false);
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

  const statusDotColor =
    status === "connected" ? "#7868c0" : status === "connecting" ? "#a890c8" : "#a898a8";

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

  const cardStyle = {
    background: "linear-gradient(145deg, rgba(248, 244, 252, 0.95) 0%, rgba(236, 228, 248, 0.9) 100%)",
    backdropFilter: "blur(12px)",
    border: "1px solid rgba(196, 184, 208, 0.5)",
    boxShadow: "0 4px 20px rgba(168, 140, 200, 0.12), 0 1px 3px rgba(0,0,0,0.04), inset 0 1px 0 rgba(255,255,255,0.6)",
  };

  return (
    <div className="min-h-screen relative p-8 font-[family-name:var(--font-patrick-hand)]">
      <Background />

      {/* Header */}
      <div
        className="relative z-10 flex items-center justify-between mb-8 px-5 py-3 rounded-xl"
        style={cardStyle}
      >
        <div className="flex items-center gap-3">
          <span
            className="w-2.5 h-2.5 rounded-full ring-2 ring-white/60"
            style={{ backgroundColor: statusDotColor }}
          />
          <h1 className="text-2xl font-bold" style={{ color: "#5c4a6c" }}>
            Chord History
          </h1>
        </div>
        <Link
          href="/"
          className="px-4 py-2 rounded-lg text-white text-sm font-medium transition-all hover:brightness-110"
          style={{
            background: "linear-gradient(160deg, #9080d8 0%, #7868c0 100%)",
            boxShadow: "0 2px 8px rgba(120, 104, 192, 0.35), inset 0 1px 0 rgba(255,255,255,0.2)",
          }}
        >
          ← Back to Live
        </Link>
      </div>

      <div className="relative z-10 grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-1 space-y-6">

          {/* Sessions List */}
          <div className="rounded-xl p-4" style={cardStyle}>
            <h2 className="text-sm mb-3 uppercase tracking-wide" style={{ color: "#7c6c8c" }}>
              Sessions
            </h2>
            <div className="space-y-1 max-h-96 overflow-y-auto">
              {sessions.length === 0 ? (
                <p className="text-xs" style={{ color: "#9c8ca8" }}>No sessions yet</p>
              ) : (
                sessions.map((session) => {
                  const isSelected = selectedSession?.timestamp === session.timestamp;
                  return (
                    <button
                      key={session.filename}
                      onClick={() => loadSession(session.filename)}
                      className="w-full text-left px-3 py-2 rounded-lg text-xs transition-all hover:ring-1 hover:ring-[#a898b8]/50"
                      style={{
                        background: isSelected
                          ? "linear-gradient(160deg, #9080d8 0%, #7868c0 100%)"
                          : "rgba(220, 212, 232, 0.5)",
                        color: isSelected ? "white" : "#5c4a6c",
                        boxShadow: isSelected ? "0 2px 8px rgba(120, 104, 192, 0.3), inset 0 1px 0 rgba(255,255,255,0.2)" : "none",
                      }}
                    >
                      <div className="font-bold text-sm">Session {session.session_number}</div>
                      <div className="text-xs opacity-80">
                        {session.node_count} nodes • depth {session.total_depth}
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Right Panel: Graph Visualization */}
        <div className="lg:col-span-3">
          {selectedSession ? (
            <div className="space-y-4">
              {/* Song Recommendations */}
              <div className="rounded-xl p-4" style={cardStyle}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xs uppercase tracking-wide" style={{ color: "#7c6c8c" }}>Similar Songs</h3>
                  <button
                    onClick={fetchRecommendedSongs}
                    disabled={isLoadingSongs}
                    className="px-3 py-1 rounded-lg text-xs font-medium text-white transition-all hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed"
                    style={{
                      background: "linear-gradient(160deg, #9080d8 0%, #7868c0 100%)",
                      boxShadow: "0 2px 8px rgba(120, 104, 192, 0.35), inset 0 1px 0 rgba(255,255,255,0.2)",
                    }}
                  >
                    {isLoadingSongs ? "Loading..." : "Get Recommendations"}
                  </button>
                </div>

                {chordProgression && (
                  <p className="text-xs mb-3" style={{ color: "#5c4a6c" }}>
                    <span style={{ color: "#7c6c8c" }}>Progression:</span> {chordProgression}
                  </p>
                )}

                {songsError && (
                  <p className="text-xs mb-3 text-red-500">{songsError}</p>
                )}

                {recommendedSongs.length > 0 ? (
                  <div className="space-y-3">
                    {recommendedSongs.map((song, idx) => (
                      <div
                        key={idx}
                        className="rounded-lg p-3 cursor-pointer transition-all hover:shadow-md"
                        style={{
                          background: "rgba(220, 212, 232, 0.3)",
                          border: "1px solid rgba(196, 184, 208, 0.3)",
                        }}
                        onClick={() => song.spotify_url && window.open(song.spotify_url, "_blank")}
                      >
                        <div className="flex gap-3">
                          {song.image_url ? (
                            <img
                              src={song.image_url}
                              alt={song.title}
                              className="w-14 h-14 rounded object-cover flex-shrink-0"
                            />
                          ) : (
                            <div
                              className="w-14 h-14 rounded flex items-center justify-center flex-shrink-0"
                              style={{ background: "rgba(168, 140, 200, 0.2)" }}
                            >
                              <span style={{ color: "#9c8ca8" }}>♪</span>
                            </div>
                          )}
                          <div className="flex-1 min-w-0">
                            <div className="text-sm font-medium" style={{ color: "#5c4a6c" }}>
                              {song.title}
                            </div>
                            {song.artists && (
                              <div className="text-xs mt-0.5" style={{ color: "#7c6c8c" }}>
                                {song.artists}
                              </div>
                            )}
                            {song.album && (
                              <div className="text-xs mt-0.5 opacity-75" style={{ color: "#9c8ca8" }}>
                                {song.album}
                              </div>
                            )}
                            {song.spotify_url && (
                              <div className="text-xs mt-1">
                                <span style={{ color: "#7868c0" }}>▶ Open on Spotify</span>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : !isLoadingSongs && !songsError && !chordProgression && (
                  <p className="text-xs" style={{ color: "#9c8ca8" }}>Click "Get Recommendations" to find similar songs</p>
                )}
              </div>

              {/* Graph */}
              <div className="rounded-xl p-6 overflow-auto" style={{ ...cardStyle, maxHeight: "600px" }}>
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
                        stroke={targetWasPlayed ? "#7868c0" : "#a898b8"}
                        strokeWidth={targetWasPlayed ? "3" : "1.5"}
                        opacity={targetWasPlayed ? "0.85" : "0.45"}
                        markerEnd={targetWasPlayed ? "url(#arrowhead-played)" : "url(#arrowhead)"}
                      />
                    );
                  })}

                  {/* Arrow markers */}
                  <defs>
                    <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
                      <polygon points="0 0, 10 3, 0 6" fill="#a898b8" />
                    </marker>
                    <marker id="arrowhead-played" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
                      <polygon points="0 0, 10 3, 0 6" fill="#7868c0" />
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
                          fill={wasPlayed ? "#9080d8" : "#b8a8c8"}
                          stroke={wasPlayed ? "#a890e8" : "#c8b8d8"}
                          strokeWidth={wasPlayed ? "2" : "1"}
                          opacity={wasPlayed ? "1" : "0.7"}
                        />
                        {/* Node label */}
                        <text
                          x={x}
                          y={y}
                          textAnchor="middle"
                          dy="0.3em"
                          fill={wasPlayed ? "white" : "#5c4a6c"}
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
                          fill="#7c6c8c"
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
                <div className="rounded-xl p-4" style={cardStyle}>
                  <p className="text-xs mb-1" style={{ color: "#7c6c8c" }}>Total Nodes</p>
                  <p className="text-xl font-bold" style={{ color: "#5c4a6c" }}>{deduplicatedNodes.nodes.length}</p>
                </div>
                <div className="rounded-xl p-4" style={cardStyle}>
                  <p className="text-xs mb-1" style={{ color: "#7c6c8c" }}>Total Edges</p>
                  <p className="text-xl font-bold" style={{ color: "#5c4a6c" }}>{dedupedRelations.length}</p>
                </div>
                <div className="rounded-xl p-4" style={cardStyle}>
                  <p className="text-xs mb-1" style={{ color: "#7c6c8c" }}>Total Depth</p>
                  <p className="text-xl font-bold" style={{ color: "#5c4a6c" }}>{selectedSession.total_depth}</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-xl p-6 h-96 flex items-center justify-center" style={cardStyle}>
              <p style={{ color: "#9c8ca8" }}>Select a session to view its chord progression graph</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
