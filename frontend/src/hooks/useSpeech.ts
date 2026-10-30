import { useState, useCallback, useEffect, useRef } from "react";

export function useSpeech(initialRate: number = 1.0) {
  const [speaking, setSpeaking] = useState(false);
  const [rate, setRate] = useState(initialRate);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  const cancel = useCallback(() => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      setSpeaking(false);
    }
  }, []);

  const speak = useCallback(
    (text: string, customRate?: number) => {
      if (typeof window === "undefined" || !("speechSynthesis" in window)) {
        console.warn("Speech Synthesis is not supported in this browser.");
        return;
      }

      window.speechSynthesis.cancel();

      if (!text || text.trim() === "") {
        setSpeaking(false);
        return;
      }

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = customRate ?? rate;
      utterance.pitch = 1.0;

      utterance.onstart = () => setSpeaking(true);
      utterance.onend = () => setSpeaking(false);
      utterance.onerror = () => setSpeaking(false);
      utterance.onpause = () => setSpeaking(false);
      utterance.onresume = () => setSpeaking(true);

      utteranceRef.current = utterance;
      setSpeaking(true);
      window.speechSynthesis.speak(utterance);
    },
    [rate]
  );

  useEffect(() => {
    return () => {
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  return {
    speak,
    cancel,
    stop: cancel,
    isSpeaking: speaking,
    speaking,
    rate,
    setRate,
  };
}
