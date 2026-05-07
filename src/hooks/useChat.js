import { useState } from "react";

export function useChat() {
  const [history, setHistory] = useState([]);

  async function sendMessage(text, context = {}) {
    const updatedHistory = [...history, { role: "user", content: text }];

    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, history, context }),
    });

    const rawText = await res.text();
    console.log("Raw response:", rawText, "Status:", res.status);

    const data = rawText ? JSON.parse(rawText) : {};
    const reply = data.reply || "";

    setHistory([...updatedHistory, { role: "assistant", content: reply }]);
    return {
      reply,
      tool_used: data.tool_used || null,
      tool_result: data.tool_result || null,
    };
  }

  return { sendMessage };
}