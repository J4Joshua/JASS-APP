export type ChordId = string;

export interface ChordNode {
  id: string;
  chordId: ChordId;
  probability?: number;
}

export interface ChordGraphState {
  current: ChordNode;
  previous: ChordNode[];
  next: ChordNode[];
}

export interface HistoryEntry {
  current: ChordNode;
  next: ChordNode[];
  chosenIndex: number;
  timestamp: number;
}

export interface SavedSong {
  id: string;
  name: string;
  history: HistoryEntry[];
  createdAt: number;
  updatedAt: number;
}

export type ChordEvent =
  | { type: 'CHORD_CHANGE'; payload: ChordGraphState }
  | { type: 'RESET' };

export type HistorySeed = {
  current: { id: string; chordId: string };
  previous: { id: string; chordId: string }[];
  next: { id: string; chordId: string; probability?: number }[];
  notesMap: Record<string, string[]>;
};
