import { useState, useEffect, useCallback, useRef } from "react";
import { EventResponse } from "../types/api";

export interface SignalFeatures {
  idle_time: number;
  edit_count: number;
  retries: number;
  backspace_rate: number;
  focus_lost_count: number;
  dwell_time_ms?: number;
  pause_duration_ms?: number;
}

export function useSignals(
  sessionId?: string,
  questionId?: string,
  onTickResponse?: (res: EventResponse) => void
) {
  const [signals, setSignals] = useState<SignalFeatures>({
    idle_time: 0,
    edit_count: 0,
    retries: 0,
    backspace_rate: 0,
    focus_lost_count: 0,
    dwell_time_ms: 0,
    pause_duration_ms: 0,
  });

  const idleSecondsRef = useRef(0);
  const totalKeystrokesRef = useRef(0);
  const backspaceCountRef = useRef(0);
  const editCountRef = useRef(0);
  const retriesRef = useRef(0);
  const focusLostRef = useRef(0);
  const questionStartTimeRef = useRef(Date.now());
  const lastActivityTimeRef = useRef(Date.now());
  const maxPauseMsRef = useRef(0);

  // Active question references to avoid stale closures
  const activeSessionIdRef = useRef(sessionId);
  const activeQuestionIdRef = useRef(questionId);

  useEffect(() => {
    activeSessionIdRef.current = sessionId;
  }, [sessionId]);

  useEffect(() => {
    activeQuestionIdRef.current = questionId;
  }, [questionId]);

  // Activity reset helper
  const registerActivity = useCallback(() => {
    const now = Date.now();
    const pause = now - lastActivityTimeRef.current;
    if (pause > maxPauseMsRef.current) {
      maxPauseMsRef.current = pause;
    }
    lastActivityTimeRef.current = now;
    idleSecondsRef.current = 0;
  }, []);

  // Idle and Dwell timers
  useEffect(() => {
    const interval = setInterval(() => {
      idleSecondsRef.current += 1;
      const now = Date.now();
      const dwell = now - questionStartTimeRef.current;
      const currentPause = now - lastActivityTimeRef.current;
      if (currentPause > maxPauseMsRef.current) {
        maxPauseMsRef.current = currentPause;
      }

      const backspaceRate =
        totalKeystrokesRef.current > 0
          ? backspaceCountRef.current / totalKeystrokesRef.current
          : 0;

      setSignals({
        idle_time: idleSecondsRef.current,
        edit_count: editCountRef.current,
        retries: retriesRef.current,
        backspace_rate: Math.round(backspaceRate * 100) / 100,
        focus_lost_count: focusLostRef.current,
        dwell_time_ms: dwell,
        pause_duration_ms: maxPauseMsRef.current,
      });
    }, 1000);

    const handleKeyDown = (e: KeyboardEvent) => {
      registerActivity();

      // Only count edits and keystrokes if the user is typing into the math answer field
      // Do NOT count keystrokes from the follow-up AI tutor chat box or search boxes!
      const target = e.target as HTMLElement | null;
      const isChat = target?.closest("form") || target?.getAttribute("data-chat-input") === "true";
      if (isChat) {
        return;
      }

      totalKeystrokesRef.current += 1;

      if (e.key === "Backspace") {
        backspaceCountRef.current += 1;
      }

      if (e.key.length === 1 || e.key === "Backspace" || e.key === "Delete") {
        editCountRef.current += 1;
        setSignals((prev) => ({ ...prev, edit_count: editCountRef.current }));
      }
    };

    const handleClick = () => {
      registerActivity();
    };

    const handleBlur = () => {
      focusLostRef.current += 1;
    };

    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("click", handleClick);
    window.addEventListener("blur", handleBlur);

    return () => {
      clearInterval(interval);
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("click", handleClick);
      window.removeEventListener("blur", handleBlur);
    };
  }, [registerActivity]);

  // Periodic passive background tick (every 8 seconds when active session exists)
  useEffect(() => {
    if (!sessionId || !questionId) return;

    const tickInterval = setInterval(async () => {
      try {
        const features = getFeatures();
        const res = await fetch("/api/events", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            session_id: sessionId,
            question_id: questionId,
            type: "tick",
            features,
          }),
        });
        if (res.ok && onTickResponse) {
          const data = await res.json();
          onTickResponse(data);
        }
      } catch (err) {
        // Passive telemetry tick errors are non-blocking
      }
    }, 8000);

    return () => clearInterval(tickInterval);
  }, [sessionId, questionId, onTickResponse]);

  const getFeatures = useCallback((): SignalFeatures => {
    const dwell = Date.now() - questionStartTimeRef.current;
    const backspaceRate =
      totalKeystrokesRef.current > 0
        ? backspaceCountRef.current / totalKeystrokesRef.current
        : 0;

    return {
      idle_time: idleSecondsRef.current,
      edit_count: editCountRef.current,
      retries: retriesRef.current,
      backspace_rate: Math.round(backspaceRate * 100) / 100,
      focus_lost_count: focusLostRef.current,
      dwell_time_ms: dwell,
      pause_duration_ms: maxPauseMsRef.current,
    };
  }, []);

  const sendEvent = useCallback(
    async (
      typeOrSessionId: string,
      questionIdOrAnswer?: string,
      typeArg?: string,
      answerArg?: string
    ) => {
      // Handle both sendEvent(type, answer) and sendEvent(sessionId, questionId, type, answer)
      let sId = activeSessionIdRef.current || "";
      let qId = activeQuestionIdRef.current || "";
      let eventType = typeOrSessionId;
      let eventAnswer: string | undefined = questionIdOrAnswer;

      if (typeArg !== undefined) {
        sId = typeOrSessionId;
        qId = questionIdOrAnswer || "";
        eventType = typeArg;
        eventAnswer = answerArg;
      }

      const features = getFeatures();
      const payload: Record<string, any> = {
        session_id: sId,
        question_id: qId,
        type: eventType,
        features,
      };
      if (eventAnswer !== undefined && eventAnswer !== "") {
        payload.answer = eventAnswer;
      }

      const res = await fetch("/api/events", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error(`Event API returned ${res.status}`);
      }
      return (await res.json()) as EventResponse;
    },
    [getFeatures]
  );

  const resetForNewQuestion = useCallback(() => {
    idleSecondsRef.current = 0;
    totalKeystrokesRef.current = 0;
    backspaceCountRef.current = 0;
    editCountRef.current = 0;
    retriesRef.current = 0;
    focusLostRef.current = 0;
    questionStartTimeRef.current = Date.now();
    lastActivityTimeRef.current = Date.now();
    maxPauseMsRef.current = 0;

    setSignals({
      idle_time: 0,
      edit_count: 0,
      retries: 0,
      backspace_rate: 0,
      focus_lost_count: 0,
      dwell_time_ms: 0,
      pause_duration_ms: 0,
    });
  }, []);

  const recordEdit = useCallback(() => {
    registerActivity();
    editCountRef.current += 1;
    setSignals((prev) => ({ ...prev, edit_count: editCountRef.current }));
  }, [registerActivity]);

  const recordOptionSwitch = useCallback(() => {
    registerActivity();
    retriesRef.current += 1;
    setSignals((prev) => ({ ...prev, retries: retriesRef.current }));
  }, [registerActivity]);

  const recordHint = useCallback(() => {
    registerActivity();
  }, [registerActivity]);

  const recordLost = useCallback(() => {
    registerActivity();
  }, [registerActivity]);

  const recordClick = useCallback(() => {
    registerActivity();
  }, [registerActivity]);

  const incrementRetries = useCallback(() => {
    retriesRef.current += 1;
    setSignals((prev) => ({ ...prev, retries: retriesRef.current }));
  }, []);

  return {
    signals,
    dwellTimeMs: signals.dwell_time_ms || 0,
    pauseDurationMs: signals.pause_duration_ms || 0,
    getFeatures,
    sendEvent,
    resetSignals: resetForNewQuestion,
    resetForNewQuestion,
    incrementRetries,
    recordEdit,
    recordOptionSwitch,
    recordHint,
    recordLost,
    recordClick,
  };
}
