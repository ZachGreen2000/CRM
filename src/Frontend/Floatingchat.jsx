/**
 * FloatingChat.jsx
 *
 * A draggable floating chat widget.
 * - Drag the icon anywhere on screen
 * - Click (without dragging) to open/close the chat panel
 * - Pass `onSend` prop to hook into your AI backend
 *
 * Usage:
 *   import FloatingChat from "./FloatingChat";
 *   <FloatingChat onSend={async (msg) => { return await myAI(msg); }} />
 *
 * Props:
 *   onSend(message: string) → Promise<string>   — called with user message, resolves with AI reply
 *   initialPosition?: { x: number, y: number }  — defaults to bottom-right
 */

import { useState, useRef, useEffect, useCallback } from "react";

// ── Sparkle / bot SVG icon ───────────────────────────────────────────────────
function BotIcon({ size = 22, color = "currentColor" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="8" width="18" height="12" rx="3" />
      <path d="M9 8V6a3 3 0 0 1 6 0v2" />
      <circle cx="9" cy="14" r="1.2" fill={color} stroke="none" />
      <circle cx="15" cy="14" r="1.2" fill={color} stroke="none" />
      <path d="M8 18h8" />
    </svg>
  );
}

function SendIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}

// ── Typing indicator ─────────────────────────────────────────────────────────
function TypingDots() {
  return (
    <div style={styles.typingRow}>
      <div style={styles.aiBubble}>
        <span style={styles.typingDot} className="fc-dot fc-dot-1" />
        <span style={styles.typingDot} className="fc-dot fc-dot-2" />
        <span style={styles.typingDot} className="fc-dot fc-dot-3" />
      </div>
    </div>
  );
}

// ── Message bubble ───────────────────────────────────────────────────────────
function Message({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div style={isUser ? styles.userRow : styles.aiRow}>
      <div style={isUser ? styles.userBubble : styles.aiBubble}>
        {msg.content}
      </div>
    </div>
  );
}

// ── Main component ───────────────────────────────────────────────────────────
export default function FloatingChat({
  onSend,
  initialPosition,
}) {
  const defaultPos = initialPosition ?? { x: window.innerWidth - 80, y: window.innerHeight - 80 };

  const [pos, setPos]         = useState(defaultPos);
  const [open, setOpen]       = useState(false);
  const [messages, setMessages] = useState([
    { role: "ai", content: "Hi! How can I help you today?" },
  ]);
  const [input, setInput]     = useState("");
  const [loading, setLoading] = useState(false);
  const [panelSide, setPanelSide] = useState("left"); // panel opens left or right of icon

  const dragging  = useRef(false);
  const moved     = useRef(false);
  const offset    = useRef({ x: 0, y: 0 });
  const posRef    = useRef(pos);
  const messagesEndRef = useRef(null);
  const textareaRef    = useRef(null);

  posRef.current = pos;

  // scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // decide which side panel should open based on icon x position
  useEffect(() => {
    setPanelSide(pos.x > window.innerWidth / 2 ? "left" : "right");
  }, [pos.x]);

  // ── Drag logic ──────────────────────────────────────────────────────────────
  const onPointerDown = useCallback((e) => {
    dragging.current = true;
    moved.current    = false;
    offset.current   = {
      x: e.clientX - posRef.current.x,
      y: e.clientY - posRef.current.y,
    };
    e.currentTarget.setPointerCapture(e.pointerId);
    e.preventDefault();
  }, []);

  const onPointerMove = useCallback((e) => {
    if (!dragging.current) return;
    moved.current = true;
    const ICON = 52;
    const nx = Math.max(0, Math.min(window.innerWidth  - ICON, e.clientX - offset.current.x));
    const ny = Math.max(0, Math.min(window.innerHeight - ICON, e.clientY - offset.current.y));
    setPos({ x: nx, y: ny });
  }, []);

  const onPointerUp = useCallback(() => {
    if (!moved.current) {
      setOpen((o) => !o);
    }
    dragging.current = false;
  }, []);

  // ── Send message ────────────────────────────────────────────────────────────
  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);

    try {
      let reply = "I don't have a response handler connected yet.";
      if (typeof onSend === "function") {
        reply = await onSend(text);
      }
      setMessages((prev) => [...prev, { role: "ai", content: reply }]);
    } catch (err) {
      setMessages((prev) => [...prev, { role: "ai", content: "Something went wrong. Please try again." }]);
    } finally {
      setLoading(false);
      textareaRef.current?.focus();
    }
  }, [input, loading, onSend]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // ── Panel position ──────────────────────────────────────────────────────────
  const ICON_SIZE    = 52;
  const PANEL_W      = 340;
  const PANEL_H      = 480;
  const GAP          = 12;

  const panelStyle = {
    ...styles.panel,
    width:  PANEL_W,
    height: PANEL_H,
    // anchor panel to the icon vertically, flip if near bottom
    top: Math.min(pos.y, window.innerHeight - PANEL_H - 8),
    ...(panelSide === "left"
      ? { left: pos.x - PANEL_W - GAP }
      : { left: pos.x + ICON_SIZE + GAP }),
    opacity:   open ? 1 : 0,
    transform: open ? "scale(1) translateY(0)" : "scale(0.92) translateY(8px)",
    pointerEvents: open ? "all" : "none",
  };

  return (
    <>
      {/* inject keyframe CSS once */}
      <style>{KEYFRAMES}</style>

      {/* ── Chat panel ── */}
      <div style={panelStyle} aria-hidden={!open}>

        {/* Header */}
        <div style={styles.header}>
          <div style={styles.headerLeft}>
            <div style={styles.headerAvatar}><BotIcon size={16} color="#55883B" /></div>
            <div>
              <div style={styles.headerTitle}>AI Assistant</div>
              <div style={styles.headerSub}>Always here to help</div>
            </div>
          </div>
          <button style={styles.closeBtn} onClick={() => setOpen(false)} aria-label="Close chat">
            <CloseIcon />
          </button>
        </div>

        {/* Messages */}
        <div style={styles.messages}>
          {messages.map((msg, i) => <Message key={i} msg={msg} />)}
          {loading && <TypingDots />}
          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div style={styles.inputArea}>
          <textarea
            ref={textareaRef}
            style={styles.textarea}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Message AI…"
            rows={1}
            disabled={loading}
          />
          <button
            style={{
              ...styles.sendBtn,
              opacity: input.trim() && !loading ? 1 : 0.4,
              cursor:  input.trim() && !loading ? "pointer" : "default",
            }}
            onClick={handleSend}
            disabled={!input.trim() || loading}
            aria-label="Send message"
          >
            <SendIcon />
          </button>
        </div>
      </div>

      {/* ── Draggable icon ── */}
      <div
        style={{ ...styles.fab, left: pos.x, top: pos.y }}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        role="button"
        aria-label="Open AI chat"
        tabIndex={0}
      >
        {/* pulse ring when closed */}
        {!open && <span style={styles.pulse} />}
        <BotIcon size={22} color="#fff" />
      </div>
    </>
  );
}

// ── Styles ───────────────────────────────────────────────────────────────────
const styles = {
  fab: {
    position:     "fixed",
    width:        52,
    height:       52,
    borderRadius: "50%",
    background:   "linear-gradient(135deg, #C1E899 0%, #55883B 100%)",
    boxShadow:    "0 4px 20px rgba(85,136,59,0.45), 0 1px 4px rgba(0,0,0,0.15)",
    display:      "flex",
    alignItems:   "center",
    justifyContent: "center",
    cursor:       "grab",
    userSelect:   "none",
    zIndex:       9999,
    transition:   "box-shadow 0.2s ease, transform 0.15s ease",
  },
  pulse: {
    position:     "absolute",
    inset:        -4,
    borderRadius: "50%",
    border:       "2px solid #C1E899",
    animation:    "fc-pulse 2.4s ease-out infinite",
    pointerEvents:"none",
  },
  panel: {
    position:     "fixed",
    zIndex:       9998,
    background:   "#FFFFFF",
    borderRadius: 16,
    boxShadow:    "0 8px 40px rgba(0,0,0,0.14), 0 1px 6px rgba(0,0,0,0.08)",
    display:      "flex",
    flexDirection:"column",
    overflow:     "hidden",
    transition:   "opacity 0.22s ease, transform 0.22s ease",
    border:       "1px solid #E5E7EB",
  },
  header: {
    display:        "flex",
    alignItems:     "center",
    justifyContent: "space-between",
    padding:        "14px 16px",
    borderBottom:   "1px solid #E6F0DC",
    background:     "#F3F9EE",
    flexShrink:     0,
  },
  headerLeft: {
    display:    "flex",
    alignItems: "center",
    gap:        10,
  },
  headerAvatar: {
    width:          34,
    height:         34,
    borderRadius:   "50%",
    background:     "#E6F0DC",
    display:        "flex",
    alignItems:     "center",
    justifyContent: "center",
    border:         "1.5px solid #C1E899",
  },
  headerTitle: {
    fontSize:   13,
    fontWeight: 600,
    color:      "#111827",
    lineHeight: 1.3,
  },
  headerSub: {
    fontSize: 11,
    color:    "#9CA3AF",
  },
  closeBtn: {
    background:   "none",
    border:       "none",
    cursor:       "pointer",
    color:        "#9CA3AF",
    padding:      6,
    borderRadius: 6,
    display:      "flex",
    alignItems:   "center",
    justifyContent: "center",
    transition:   "background 0.15s, color 0.15s",
  },
  messages: {
    flex:       1,
    overflowY:  "auto",
    padding:    "14px 14px 8px",
    display:    "flex",
    flexDirection: "column",
    gap:        8,
    scrollbarWidth: "thin",
    scrollbarColor: "#E5E7EB transparent",
  },
  userRow: {
    display:        "flex",
    justifyContent: "flex-end",
  },
  aiRow: {
    display:        "flex",
    justifyContent: "flex-start",
  },
  typingRow: {
    display:        "flex",
    justifyContent: "flex-start",
  },
  userBubble: {
    maxWidth:     "78%",
    background:   "linear-gradient(135deg, #C1E899, #8dc96b)",
    color:        "#1a3a0f",
    padding:      "9px 13px",
    borderRadius: "14px 14px 4px 14px",
    fontSize:     13.5,
    lineHeight:   1.5,
    fontWeight:   500,
    boxShadow:    "0 1px 3px rgba(85,136,59,0.18)",
  },
  aiBubble: {
    maxWidth:     "82%",
    background:   "#F3F4F6",
    color:        "#111827",
    padding:      "9px 13px",
    borderRadius: "14px 14px 14px 4px",
    fontSize:     13.5,
    lineHeight:   1.5,
    display:      "flex",
    gap:          4,
    alignItems:   "center",
    boxShadow:    "0 1px 2px rgba(0,0,0,0.06)",
  },
  typingDot: {
    width:        7,
    height:       7,
    borderRadius: "50%",
    background:   "#9CA3AF",
    display:      "inline-block",
    animation:    "fc-bounce 1.2s ease-in-out infinite",
  },
  inputArea: {
    display:     "flex",
    alignItems:  "flex-end",
    gap:         8,
    padding:     "10px 12px 12px",
    borderTop:   "1px solid #E6F0DC",
    background:  "#FAFAFA",
    flexShrink:  0,
  },
  textarea: {
    flex:        1,
    resize:      "none",
    border:      "1.5px solid #E5E7EB",
    borderRadius: 10,
    padding:     "8px 11px",
    fontSize:    13.5,
    fontFamily:  "inherit",
    color:       "#111827",
    background:  "#fff",
    outline:     "none",
    lineHeight:  1.5,
    maxHeight:   100,
    overflowY:   "auto",
    transition:  "border-color 0.15s",
  },
  sendBtn: {
    width:          36,
    height:         36,
    flexShrink:     0,
    borderRadius:   10,
    border:         "none",
    background:     "linear-gradient(135deg, #C1E899, #55883B)",
    color:          "#fff",
    display:        "flex",
    alignItems:     "center",
    justifyContent: "center",
    transition:     "opacity 0.15s, transform 0.1s",
    boxShadow:      "0 2px 8px rgba(85,136,59,0.3)",
  },
};

const KEYFRAMES = `
  @keyframes fc-pulse {
    0%   { transform: scale(1);   opacity: 0.7; }
    70%  { transform: scale(1.55); opacity: 0; }
    100% { transform: scale(1.55); opacity: 0; }
  }
  @keyframes fc-bounce {
    0%, 80%, 100% { transform: translateY(0);    opacity: 0.5; }
    40%           { transform: translateY(-5px); opacity: 1;   }
  }
  .fc-dot-1 { animation-delay: 0s;    }
  .fc-dot-2 { animation-delay: 0.18s; }
  .fc-dot-3 { animation-delay: 0.36s; }
`;