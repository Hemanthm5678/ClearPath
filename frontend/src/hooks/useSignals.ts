import { useEffect, useRef, useState, useCallback } from 'react';

export interface SignalFeatures {
  dwell_time_ms: number;
  pause_duration_ms: number;
  edit_count: number;
  option_switches: number;
  hint_clicks: number;
  lost_clicks: number;
  rapid_clicks: number;
}

export function useSignals(
  sessionId: string,
  questionId: string,
  onTickResponse?: (data: any) => void
) {
  const [dwellTimeMs, setDwellTimeMs] = useState(0);
  const [pauseDurationMs, setPauseDurationMs] = useState(0);

  const questionStartTimeRef = useRef<number>(Date.now());
  const lastInteractionTimeRef = useRef<number>(Date.now());
  const editCountRef = useRef<number>(0);
  const optionSwitchesRef = useRef<number>(0);
  const hintClicksRef = useRef<number>(0);
  const lostClicksRef = useRef<number>(0);
  const recentClicksRef = useRef<number[]>([]);
  const rapidClicksCountRef = useRef<number>(0);

  // Reset counters for a fresh question
  const resetForNewQuestion = useCallback(() => {
    questionStartTimeRef.current = Date.now();
    lastInteractionTimeRef.current = Date.now();
    editCountRef.current = 0;
    optionSwitchesRef.current = 0;
    hintClicksRef.current = 0;
    lostClicksRef.current = 0;
    recentClicksRef.current = [];
    rapidClicksCountRef.current = 0;
    setDwellTimeMs(0);
    setPauseDurationMs(0);
  }, []);

  // Update timestamps when any user interaction occurs
  const registerActivity = useCallback(() => {
    lastInteractionTimeRef.current = Date.now();
    setPauseDurationMs(0);
  }, []);

  const recordEdit = useCallback(() => {
    editCountRef.current += 1;
    registerActivity();
  }, [registerActivity]);

  const recordOptionSwitch = useCallback(() => {
    optionSwitchesRef.current += 1;
    registerActivity();
  }, [registerActivity]);

  const recordHint = useCallback(() => {
    hintClicksRef.current += 1;
    registerActivity();
  }, [registerActivity]);

  const recordLost = useCallback(() => {
    lostClicksRef.current += 1;
    registerActivity();
  }, [registerActivity]);

  const recordClick = useCallback(() => {
    const now = Date.now();
    registerActivity();
    // Keep clicks from the last 1200ms
    recentClicksRef.current = recentClicksRef.current.filter((t) => now - t < 1200);
    recentClicksRef.current.push(now);
    if (recentClicksRef.current.length >= 3) {
      rapidClicksCountRef.current += 1;
    }
  }, [registerActivity]);

  // Periodic clock update for dwell and pause timers
  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      const dwell = now - questionStartTimeRef.current;
      const pause = now - lastInteractionTimeRef.current;
      setDwellTimeMs(dwell);
      setPauseDurationMs(pause);
    }, 500);

    return () => clearInterval(interval);
  }, []);

  // Construct current feature payload (Strictly timing and counts)
  const getFeatures = useCallback((): SignalFeatures => {
    const now = Date.now();
    return {
      dwell_time_ms: now - questionStartTimeRef.current,
      pause_duration_ms: now - lastInteractionTimeRef.current,
      edit_count: editCountRef.current,
      option_switches: optionSwitchesRef.current,
      hint_clicks: hintClicksRef.current,
      lost_clicks: lostClicksRef.current,
      rapid_clicks: rapidClicksCountRef.current,
    };
  }, []);

  // Periodic background telemetry tick (every 5 seconds)
  useEffect(() => {
    if (!sessionId || !questionId) return;

    const tickInterval = setInterval(async () => {
      try {
        const features = getFeatures();
        // Only tick if dwell > 3s
        if (features.dwell_time_ms < 3000) return;

        const res = await fetch('/api/events', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: sessionId,
            question_id: questionId,
            type: 'tick',
            features,
          }),
        });
        if (res.ok && onTickResponse) {
          const data = await res.json();
          onTickResponse(data);
        }
      } catch (err) {
        // Silent catch for background ticks
      }
    }, 4000);

    return () => clearInterval(tickInterval);
  }, [sessionId, questionId, getFeatures, onTickResponse]);

  return {
    dwellTimeMs,
    pauseDurationMs,
    getFeatures,
    recordEdit,
    recordOptionSwitch,
    recordHint,
    recordLost,
    recordClick,
    resetForNewQuestion,
  };
}
