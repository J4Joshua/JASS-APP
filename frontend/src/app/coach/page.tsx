"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Background } from "@/components/Background/Background";

type Message = {
  id: string;
  type: "user" | "coach";
  content: string;
  timestamp: number;
  chord?: string;
  suggestions?: Array<{ name: string; tension: number }>;
  pattern?: string;
  difficulty?: number;
};

export default function Coach() {
  const [sessionId, setSessionId] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [inputChord, setInputChord] = useState("");
  const [currentDifficulty, setCurrentDifficulty] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize session ID
  useEffect(() => {
    const newSessionId = crypto.randomUUID();
    setSessionId(newSessionId);
    
    // Add welcome message
    setMessages([
      {
        id: "welcome",
        type: "coach",
        content: "👋 Welcome to the AI Coaching Session! I'll help you master chord progressions and voice leading.",
        timestamp: Date.now(),
      },
      {
        id: "start",
        type: "coach",
        content: "Try playing a chord to get started. Type the chord name (e.g., 'Dm7') or press keys on your keyboard.",
        timestamp: Date.now() + 100,
      },
    ]);
  }, []);

  // Scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendChord = useCallback(async (chordName: string) => {
    if (!chordName.trim() || !sessionId) return;

    setError(null);
    setIsLoading(true);

    // Add user message
    const userMsg: Message = {
      id: `user-${Date.now()}`,
      type: "user",
      content: chordName,
      timestamp: Date.now(),
      chord: chordName,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInputChord("");

    try {
      // Get modal endpoint from env or use default
      const modalUrl = process.env.NEXT_PUBLIC_MODAL_ENDPOINT || "http://localhost:8000";

      const response = await fetch(`${modalUrl}/process_turn`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          chord_name: chordName,
          chroma: new Array(12).fill(0), // Placeholder: could parse actual chord
          key: "C",
        }),
      });

      if (!response.ok) {
        throw new Error(`Coach error: ${response.statusText}`);
      }

      const data = await response.json();

      // Add coach response
      const coachMsg: Message = {
        id: `coach-${Date.now()}`,
        type: "coach",
        content: data.exercise || data.feedback || "Great chord choice!",
        timestamp: Date.now(),
        pattern: data.pattern_detected,
        suggestions: data.suggestions?.slice(0, 3).map((s: any) => ({
          name: s.name,
          tension: s.tension,
        })),
        difficulty: data.difficulty,
      };
      setMessages((prev) => [...prev, coachMsg]);
      setCurrentDifficulty(data.difficulty || 1);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Connection error. Make sure Modal is running: `modal serve backend/modal_app.py`"
      );
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputChord.trim()) {
      sendChord(inputChord);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  const resetSession = async () => {
    try {
      const modalUrl = process.env.NEXT_PUBLIC_MODAL_ENDPOINT || "http://localhost:8000";
      await fetch(`${modalUrl}/reset_session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId }),
      });

      const newSessionId = crypto.randomUUID();
      setSessionId(newSessionId);
      setMessages([]);
      setCurrentDifficulty(1);
      setError(null);
    } catch (err) {
      setError("Failed to reset session");
    }
  };

  return (
    <div className="relative w-screen h-screen overflow-hidden">
      <Background />

      {/* Header */}
      <div
        className="absolute top-0 left-0 right-0 z-10 px-8 py-4 flex items-center justify-between border-b"
        style={{
          background: "linear-gradient(180deg, rgba(248, 244, 252, 0.95) 0%, rgba(244, 240, 252, 0.9) 100%)",
          borderBottom: "1px solid rgba(196, 184, 208, 0.6)",
        }}
      >
        <h1 className="text-2xl font-bold" style={{ color: "#5c4a6c" }}>
          ♪ Chord Coaching
        </h1>
        <div className="flex gap-3">
          <Link
            href="/"
            className="px-3 py-1.5 rounded-lg text-white text-sm font-medium transition-all hover:brightness-110"
            style={{
              background: "linear-gradient(160deg, #9080d8 0%, #7868c0 100%)",
              boxShadow: "0 2px 8px rgba(120, 104, 192, 0.35), inset 0 1px 0 rgba(255,255,255,0.2)",
            }}
          >
            ← Play
          </Link>
          <Link
            href="/history"
            className="px-3 py-1.5 rounded-lg text-white text-sm font-medium transition-all hover:brightness-110"
            style={{
              background: "linear-gradient(160deg, #9080d8 0%, #7868c0 100%)",
              boxShadow: "0 2px 8px rgba(120, 104, 192, 0.35), inset 0 1px 0 rgba(255,255,255,0.2)",
            }}
          >
            History →
          </Link>
        </div>
      </div>

      {/* Main Content */}
      <div className="absolute top-20 left-0 right-0 bottom-0 flex flex-col">
        {/* Messages Container */}
        <div
          className="flex-1 overflow-y-auto px-8 py-6"
          style={{
            background: "linear-gradient(180deg, rgba(248, 244, 252, 0.5) 0%, rgba(240, 236, 252, 0.3) 100%)",
          }}
        >
          <div className="max-w-2xl mx-auto space-y-4">
            {messages.length === 0 ? (
              <div
                className="text-center py-12 rounded-lg p-6"
                style={{
                  background: "rgba(248, 244, 252, 0.6)",
                  border: "1px solid rgba(196, 184, 208, 0.4)",
                  color: "#5c4a6c",
                }}
              >
                <p className="text-lg font-medium mb-2">No messages yet</p>
                <p className="text-sm opacity-70">Type a chord name or play a chord to get started!</p>
              </div>
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.type === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-xl rounded-lg px-4 py-3 ${
                      msg.type === "user"
                        ? "text-white rounded-br-none"
                        : "rounded-bl-none"
                    }`}
                    style={{
                      background:
                        msg.type === "user"
                          ? "linear-gradient(135deg, #9080d8 0%, #7868c0 100%)"
                          : "rgba(248, 244, 252, 0.8)",
                      color: msg.type === "user" ? "white" : "#5c4a6c",
                      boxShadow:
                        msg.type === "user"
                          ? "0 2px 8px rgba(120, 104, 192, 0.3)"
                          : "0 2px 4px rgba(196, 184, 208, 0.2)",
                    }}
                  >
                    <p className="text-sm">{msg.content}</p>

                    {/* Pattern indicator */}
                    {msg.pattern && (
                      <div className="mt-2 pt-2 border-t border-current border-opacity-20">
                        <span className="text-xs opacity-75 font-medium">
                          🎵 Pattern: {msg.pattern}
                        </span>
                      </div>
                    )}

                    {/* Difficulty indicator */}
                    {msg.difficulty && msg.type === "coach" && (
                      <div className="mt-1">
                        <div className="text-xs opacity-70">
                          Difficulty: {"⭐".repeat(msg.difficulty)}
                        </div>
                      </div>
                    )}

                    {/* Suggestions */}
                    {msg.suggestions && msg.suggestions.length > 0 && (
                      <div className="mt-3 pt-2 border-t border-current border-opacity-20 space-y-1">
                        <div className="text-xs opacity-75 font-medium">Try next:</div>
                        <div className="flex flex-wrap gap-2">
                          {msg.suggestions.map((sug) => (
                            <button
                              key={sug.name}
                              onClick={() => sendChord(sug.name)}
                              className="text-xs px-2 py-1 rounded bg-black bg-opacity-10 hover:bg-opacity-20 transition-all"
                            >
                              {sug.name}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="text-xs opacity-50 mt-2">
                      {new Date(msg.timestamp).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </div>
                  </div>
                </div>
              ))
            )}
            {isLoading && (
              <div className="flex justify-start">
                <div
                  className="rounded-lg px-4 py-3 rounded-bl-none"
                  style={{
                    background: "rgba(248, 244, 252, 0.8)",
                    color: "#5c4a6c",
                  }}
                >
                  <div className="flex gap-2">
                    <div
                      className="w-2 h-2 rounded-full animate-bounce"
                      style={{ background: "#9080d8" }}
                    ></div>
                    <div
                      className="w-2 h-2 rounded-full animate-bounce"
                      style={{ background: "#9080d8", animationDelay: "0.1s" }}
                    ></div>
                    <div
                      className="w-2 h-2 rounded-full animate-bounce"
                      style={{ background: "#9080d8", animationDelay: "0.2s" }}
                    ></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Error display */}
        {error && (
          <div
            className="mx-8 mb-4 p-3 rounded-lg text-sm"
            style={{
              background: "rgba(239, 68, 68, 0.1)",
              border: "1px solid rgba(239, 68, 68, 0.3)",
              color: "#991b1b",
            }}
          >
            {error}
          </div>
        )}

        {/* Input area */}
        <div className="px-8 py-4 border-t" style={{ borderColor: "rgba(196, 184, 208, 0.6)" }}>
          <div className="max-w-2xl mx-auto">
            <form onSubmit={handleSubmit} className="flex gap-3">
              <input
                type="text"
                value={inputChord}
                onChange={(e) => setInputChord(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Enter chord name (e.g., Dm7, G7, Cmaj7)"
                disabled={isLoading}
                className="flex-1 px-4 py-2 rounded-lg border text-sm font-mono"
                style={{
                  background: "rgba(248, 244, 252, 0.9)",
                  borderColor: "rgba(196, 184, 208, 0.4)",
                  color: "#5c4a6c",
                }}
              />
              <button
                type="submit"
                disabled={isLoading || !inputChord.trim()}
                className="px-4 py-2 rounded-lg text-white text-sm font-medium transition-all hover:brightness-110 disabled:opacity-50"
                style={{
                  background: "linear-gradient(160deg, #9080d8 0%, #7868c0 100%)",
                  boxShadow: "0 2px 8px rgba(120, 104, 192, 0.35), inset 0 1px 0 rgba(255,255,255,0.2)",
                }}
              >
                Send
              </button>
              <button
                type="button"
                onClick={resetSession}
                disabled={isLoading}
                className="px-4 py-2 rounded-lg text-white text-sm font-medium transition-all hover:brightness-110 disabled:opacity-50"
                style={{
                  background: "linear-gradient(160deg, #8878b0 0%, #7060a0 100%)",
                  boxShadow: "0 2px 8px rgba(112, 96, 160, 0.35), inset 0 1px 0 rgba(255,255,255,0.2)",
                }}
              >
                Reset
              </button>
            </form>
            <div className="mt-3 text-xs text-center" style={{ color: "rgba(92, 74, 108, 0.7)" }}>
              Difficulty: {"⭐".repeat(currentDifficulty)}
              {currentDifficulty < 5 && "☆".repeat(5 - currentDifficulty)} | Session ID:{" "}
              <code style={{ fontSize: "0.75rem" }}>{sessionId?.slice(0, 8)}...</code>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
