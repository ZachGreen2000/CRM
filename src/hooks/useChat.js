import { useState } from "react";

export function useChat() {
  const [history, setHistory] = useState([]);

  async function sendMessage(text) {
    const updatedHistory = [...history, { role: "user", content: text }];

    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, history }),
    });

    const data = await res.json();
    const reply = data.reply;

    setHistory([...updatedHistory, { role: "assistant", content: reply }]);
    return reply; // FloatingChat expects onSend to return the reply string
  }

  return { sendMessage };
}