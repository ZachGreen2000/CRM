import { useState, useRef, useEffect } from "react";
import { colors, radius } from "./theme";

// ── Priority config ────────────────────────────────────────────
const PRIORITY = {
  CRITICAL: { bg: colors.dangerLight,   text: colors.dangerText,   label: "Critical" },
  HIGH:     { bg: colors.warningLight,  text: colors.warningText,  label: "High"     },
  MEDIUM:   { bg: colors.infoLight,     text: colors.infoText,     label: "Medium"   },
  LOW:      { bg: colors.successLight,  text: colors.successText,  label: "Low"      },
};

const COL_KEYS   = ["backlog", "todo", "inprogress", "done"];
const COL_LABELS = { backlog: "Backlog", todo: "To do", inprogress: "In progress", done: "Done" };
const TODAY      = "May 8";

// ── Initial data ───────────────────────────────────────────────
const INITIAL_TASKS = {
  backlog: [
    { id: 1, title: "Write API documentation",     description: "Cover all v2 endpoints",          priority: "MEDIUM", date: "May 14" },
    { id: 2, title: "User interview — 3 sessions", description: "Schedule via Calendly",            priority: "LOW",    date: "May 20" },
    { id: 3, title: "Migrate to Postgres 16",                                                        priority: "LOW",    date: "May 18" },
  ],
  todo: [
    { id: 4, title: "Redesign onboarding flow",    description: "Focus on mobile-first approach",   priority: "HIGH",     date: "May 10" },
    { id: 5, title: "Performance audit",           description: "Lighthouse + bundle size",         priority: "MEDIUM",   date: TODAY    },
    { id: 6, title: "Release v2.3.0",              description: "Tag + changelog",                  priority: "CRITICAL", date: TODAY    },
  ],
  inprogress: [
    { id: 7, title: "Fix auth token expiry bug",                                                     priority: "CRITICAL", date: TODAY },
    { id: 8, title: "Deploy staging environment",                                                    priority: "HIGH",     date: TODAY },
  ],
  done: [
    { id: 9, title: "Accessibility review",        description: "WCAG 2.1 AA",                      priority: "MEDIUM" },
  ],
};

// ── Helpers ────────────────────────────────────────────────────
let _nextId = 10;
const nextId = () => _nextId++;

// ── Sub-components ─────────────────────────────────────────────

function PriorityBadge({ priority }) {
  const p = PRIORITY[priority] ?? PRIORITY.MEDIUM;
  return (
    <span style={{
      fontSize: 11, fontWeight: 600, padding: "3px 8px",
      borderRadius: radius.sm, background: p.bg, color: p.text,
    }}>
      {p.label}
    </span>
  );
}

function TaskCard({ task, colKey, onDelete, onMove, onDragStart, onDragEnd, onDragOver, onDrop }) {
  return (
    <div
      draggable
      onDragStart={(e) => onDragStart(e, task.id, colKey)}
      onDragEnd={onDragEnd}
      onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); }}
      onDrop={(e) => onDrop(e, task.id, colKey)}
      style={{
        background: colors.bgSurface,
        border: `1px solid ${colors.borderDefault}`,
        borderRadius: radius.lg,
        padding: "11px 12px",
        cursor: "grab",
        userSelect: "none",
      }}
    >
      {/* Title row */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 6 }}>
        <span style={{ fontSize: 13, fontWeight: 600, color: colors.textPrimary, flex: 1, lineHeight: 1.4 }}>
          {task.title}
        </span>
        <button
          onClick={() => onDelete(task.id, colKey)}
          aria-label="Delete task"
          style={{ border: "none", background: "transparent", color: colors.textMuted, cursor: "pointer", fontSize: 18, lineHeight: 1, paddingLeft: 6 }}
        >
          ×
        </button>
      </div>

      {/* Description */}
      {task.description && (
        <p style={{ fontSize: 12, color: colors.textSecondary, margin: "0 0 7px", lineHeight: 1.4 }}>
          {task.description}
        </p>
      )}

      {/* Footer */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <PriorityBadge priority={task.priority} />
        {task.date && (
          <span style={{ fontSize: 11, color: colors.textMuted }}>{task.date}</span>
        )}
      </div>

      {/* Move select */}
      <select
        value={colKey}
        onChange={(e) => onMove(task.id, colKey, e.target.value)}
        aria-label="Move task to column"
        style={{
          width: "100%", fontSize: 11, padding: "3px 7px",
          border: `1px solid ${colors.borderDefault}`,
          borderRadius: radius.sm,
          background: colors.bgSubtle,
          color: colors.textSecondary,
          cursor: "pointer",
          fontFamily: "inherit",
        }}
      >
        {COL_KEYS.map((k) => (
          <option key={k} value={k}>{COL_LABELS[k]}</option>
        ))}
      </select>
    </div>
  );
}

function Column({ colKey, tasks, filter, onAdd, onDelete, onMove, onDragStart, onDragEnd, onColDrop }) {
  const [over, setOver] = useState(false);
  const visible = filter === "all" ? tasks : tasks.filter((t) => t.priority === filter);

  return (
    <div
      style={{
        background: over ? colors.primaryLight : colors.bgSubtle,
        border: `1px solid ${colors.borderDefault}`,
        borderRadius: radius.lg,
        display: "flex",
        flexDirection: "column",
        transition: "background 0.15s",
      }}
      onDragOver={(e) => { e.preventDefault(); setOver(true); }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => { setOver(false); onColDrop(e, colKey); }}
    >
      {/* Column header */}
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        padding: "10px 12px",
        borderBottom: `1px solid ${colors.borderDefault}`,
        background: colors.primaryLight,
        borderRadius: `${radius.lg} ${radius.lg} 0 0`,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 7, fontSize: 13, fontWeight: 600, color: colors.textPrimary }}>
          <div style={{ width: 7, height: 7, borderRadius: "50%", background: colors.primaryHover, flexShrink: 0 }} />
          {COL_LABELS[colKey]}
          <span style={{ fontWeight: 400, fontSize: 12, color: colors.textMuted }}>{tasks.length}</span>
        </div>
        <button
          onClick={() => onAdd(colKey)}
          aria-label={`Add task to ${COL_LABELS[colKey]}`}
          style={{
            width: 22, height: 22, border: `1px solid ${colors.borderDefault}`,
            borderRadius: 6, background: "transparent", color: colors.textMuted,
            cursor: "pointer", fontSize: 15, display: "flex", alignItems: "center", justifyContent: "center",
          }}
        >
          +
        </button>
      </div>

      {/* Task list */}
      <div style={{ flex: 1, padding: 8, display: "flex", flexDirection: "column", gap: 7, overflowY: "auto" }}>
        {visible.map((t) => (
          <TaskCard
            key={t.id}
            task={t}
            colKey={colKey}
            onDelete={onDelete}
            onMove={onMove}
            onDragStart={onDragStart}
            onDragEnd={onDragEnd}
            onDrop={(e, targetId, targetCol) => {
              e.preventDefault();
              e.stopPropagation();
              onColDrop(e, colKey, targetId);
            }}
          />
        ))}
        <button
          onClick={() => onAdd(colKey)}
          style={{
            width: "100%", padding: "7px",
            border: `1.5px dashed ${colors.borderDefault}`,
            background: "transparent", color: colors.textMuted,
            fontSize: 12, fontWeight: 600,
            borderRadius: radius.md,
            cursor: "pointer", fontFamily: "inherit",
          }}
        >
          + Add
        </button>
      </div>
    </div>
  );
}

function NewTaskModal({ defaultCol, onSave, onClose }) {
  const [title, setTitle]       = useState("");
  const [desc, setDesc]         = useState("");
  const [priority, setPriority] = useState("MEDIUM");
  const [col, setCol]           = useState(defaultCol);
  const [date, setDate]         = useState("");

  const inputStyle = {
    width: "100%", marginBottom: 10, padding: "7px 10px",
    border: `1px solid ${colors.borderDefault}`,
    borderRadius: radius.md,
    fontSize: 13, color: colors.textPrimary,
    background: colors.bgSurface,
    fontFamily: "inherit", outline: "none",
    boxSizing: "border-box",
  };

  const handleSave = () => {
    if (!title.trim()) return;
    onSave({ id: nextId(), title: title.trim(), description: desc.trim() || undefined, priority, date: date.trim() || undefined, col });
  };

  return (
    <div
      onClick={onClose}
      style={{
        position: "absolute", inset: 0,
        background: "rgba(0,0,0,0.3)",
        display: "flex", alignItems: "center", justifyContent: "center",
        zIndex: 50, borderRadius: radius.lg,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: colors.bgSurface,
          border: `1px solid ${colors.borderDefault}`,
          borderRadius: radius.lg,
          padding: 20, width: 300, maxWidth: "90%",
        }}
      >
        <h3 style={{ fontSize: 15, fontWeight: 600, color: colors.textPrimary, marginBottom: 14 }}>New task</h3>

        <label style={{ fontSize: 12, color: colors.textSecondary, display: "block", marginBottom: 3 }}>Title *</label>
        <input
          autoFocus
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSave()}
          placeholder="Task title"
          style={inputStyle}
        />

        <label style={{ fontSize: 12, color: colors.textSecondary, display: "block", marginBottom: 3 }}>Description</label>
        <textarea
          value={desc}
          onChange={(e) => setDesc(e.target.value)}
          placeholder="Optional"
          rows={2}
          style={{ ...inputStyle, resize: "vertical" }}
        />

        <label style={{ fontSize: 12, color: colors.textSecondary, display: "block", marginBottom: 3 }}>Priority</label>
        <select value={priority} onChange={(e) => setPriority(e.target.value)} style={inputStyle}>
          {Object.entries(PRIORITY).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
        </select>

        <label style={{ fontSize: 12, color: colors.textSecondary, display: "block", marginBottom: 3 }}>Column</label>
        <select value={col} onChange={(e) => setCol(e.target.value)} style={inputStyle}>
          {COL_KEYS.map((k) => <option key={k} value={k}>{COL_LABELS[k]}</option>)}
        </select>

        <label style={{ fontSize: 12, color: colors.textSecondary, display: "block", marginBottom: 3 }}>Due date</label>
        <input value={date} onChange={(e) => setDate(e.target.value)} placeholder="e.g. May 15" style={inputStyle} />

        <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", marginTop: 4 }}>
          <button
            onClick={onClose}
            style={{
              padding: "7px 14px", fontSize: 13, cursor: "pointer",
              border: `1px solid ${colors.borderDefault}`,
              borderRadius: radius.md, background: "transparent",
              color: colors.textPrimary, fontFamily: "inherit",
            }}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            style={{
              padding: "7px 14px", fontSize: 13, fontWeight: 600, cursor: "pointer",
              border: "none", borderRadius: radius.md,
              background: colors.primaryHover, color: "#fff",
              fontFamily: "inherit",
            }}
          >
            Add task
          </button>
        </div>
      </div>
    </div>
  );
}



// ── Main component ─────────────────────────────────────────────
export default function TaskBoard() {
  const [tasks, setTasks] = useState({
  backlog: [],
  todo: [],
  inprogress: [],
  done: []
});
  const [filter, setFilter]     = useState("all");
  const [modal, setModal]       = useState(null); // null | colKey string
  const dragTask                = useRef(null);
  const dragFromCol             = useRef(null);

  useEffect(() => {
  loadTasks();
}, []);

const loadTasks = async () => {
  const res = await fetch("/api/tasks/list", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action: "list_tasks" })
  });

  const data = await res.json();

  if (data.status !== "ok") return;

  const grouped = {
    backlog: [],
    todo: [],
    inprogress: [],
    done: []
  };

  for (const t of data.tasks) {
    const col = t.column;
    if (!grouped[col]) continue;

    grouped[col].push({
      id: t.task_id,
      title: t.title,
      description: t.description,
      priority: t.priority,
      date: t.due_date
    });
  }

  setTasks(grouped);
};

  // ── Derived stats ────────────────────────────────────────────
  const allTasks    = COL_KEYS.flatMap((k) => tasks[k]);
  const todayTasks  = COL_KEYS.flatMap((k) => tasks[k].map((t) => ({ ...t, col: k }))).filter((t) => t.date === TODAY);
  const totalCount  = allTasks.length;
  const doneCount   = tasks.done.length;
  const critCount   = allTasks.filter((t) => t.priority === "CRITICAL").length;

  // ── Mutation helpers ─────────────────────────────────────────
  const addTask = ({ col, ...task }) =>
    setTasks((prev) => ({ ...prev, [col]: [...prev[col], task] }));

  const deleteTask = (id, col) =>
    setTasks((prev) => ({ ...prev, [col]: prev[col].filter((t) => t.id !== id) }));

  const moveTask = (id, fromCol, toCol) => {
    if (fromCol === toCol) return;
    setTasks((prev) => {
      const task = prev[fromCol].find((t) => t.id === id);
      if (!task) return prev;
      return {
        ...prev,
        [fromCol]: prev[fromCol].filter((t) => t.id !== id),
        [toCol]:   [...prev[toCol], task],
      };
    });
  };

  // ── Drag handlers ────────────────────────────────────────────
  const onDragStart = (e, id, col) => {
    dragTask.current    = id;
    dragFromCol.current = col;
    e.dataTransfer.effectAllowed = "move";
  };
  const onDragEnd = () => {
    dragTask.current    = null;
    dragFromCol.current = null;
  };
  const onColDrop = (e, toCol, targetTaskId) => {
    e.preventDefault();
    const id      = dragTask.current;
    const fromCol = dragFromCol.current;
    if (id === null) return;

    setTasks((prev) => {
      const fromArr = [...prev[fromCol]];
      const taskIdx = fromArr.findIndex((t) => t.id === id);
      if (taskIdx === -1) return prev;
      const [task] = fromArr.splice(taskIdx, 1);

      if (fromCol === toCol) {
        if (targetTaskId != null && targetTaskId !== id) {
          const toIdx = fromArr.findIndex((t) => t.id === targetTaskId);
          fromArr.splice(toIdx, 0, task);
        } else {
          fromArr.push(task);
        }
        return { ...prev, [fromCol]: fromArr };
      }

      const toArr = [...prev[toCol]];
      if (targetTaskId != null) {
        const toIdx = toArr.findIndex((t) => t.id === targetTaskId);
        toArr.splice(toIdx >= 0 ? toIdx : toArr.length, 0, task);
      } else {
        toArr.push(task);
      }
      return { ...prev, [fromCol]: fromArr, [toCol]: toArr };
    });
    dragTask.current    = null;
    dragFromCol.current = null;
  };

  // ── Render ───────────────────────────────────────────────────
  return (
    <div style={{ padding: 24, background: colors.bgPage, minHeight: "100vh", fontFamily: "Inter, sans-serif", position: "relative" }}>

      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20, flexWrap: "wrap", gap: 12 }}>
        <div>
          <h2 style={{ fontSize: 22, fontWeight: 700, color: colors.textPrimary, margin: 0 }}>Task board</h2>
          <p style={{ fontSize: 13, color: colors.textMuted, margin: "3px 0 0" }}>
            {TODAY} · {totalCount} task{totalCount !== 1 ? "s" : ""} · {doneCount} done · {critCount} critical
          </p>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            style={{
              padding: "7px 10px", fontSize: 13,
              border: `1.5px solid ${colors.borderDefault}`,
              borderRadius: radius.md,
              background: colors.bgSurface,
              color: colors.textPrimary,
              fontFamily: "inherit", outline: "none",
            }}
          >
            <option value="all">All priorities</option>
            {Object.entries(PRIORITY).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
          </select>
          <button
            onClick={() => setModal("todo")}
            style={{
              padding: "7px 14px", fontSize: 13, fontWeight: 600,
              background: colors.primaryHover, color: "#fff",
              border: "none", borderRadius: radius.md, cursor: "pointer",
              fontFamily: "inherit",
            }}
          >
            + New task
          </button>
        </div>
      </div>

      {/* Kanban board */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 14, marginBottom: 24 }}>
        {COL_KEYS.map((k) => (
          <Column
            key={k}
            colKey={k}
            tasks={tasks[k]}
            filter={filter}
            onAdd={(col) => setModal(col)}
            onDelete={deleteTask}
            onMove={moveTask}
            onDragStart={onDragStart}
            onDragEnd={onDragEnd}
            onColDrop={onColDrop}
          />
        ))}
      </div>

      {/* Divider */}
      <div style={{ height: 1, background: colors.borderDefault, margin: "0 0 20px" }} />

      {/* Today section */}
      <p style={{ fontSize: 11, fontWeight: 700, color: colors.textMuted, letterSpacing: "0.07em", textTransform: "uppercase", marginBottom: 12 }}>
        Today — {TODAY}
      </p>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 10 }}>
        {todayTasks.length > 0 ? todayTasks.map((t) => (
          <div
            key={t.id}
            style={{
              background: colors.bgSubtle,
              borderLeft: `3px solid ${colors.primaryHover}`,
              borderRadius: `0 ${radius.md} ${radius.md} 0`,
              padding: 11,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 7 }}>
              <PriorityBadge priority={t.priority} />
              <span style={{ fontSize: 11, color: colors.textMuted }}>{COL_LABELS[t.col]}</span>
            </div>
            <p style={{ fontSize: 13, fontWeight: 600, color: colors.textPrimary, margin: "0 0 3px" }}>{t.title}</p>
            {t.description && <p style={{ fontSize: 12, color: colors.textSecondary, margin: 0 }}>{t.description}</p>}
          </div>
        )) : (
          <p style={{ fontSize: 13, color: colors.textMuted }}>No tasks due today.</p>
        )}
      </div>

      {/* Modal */}
      {modal && (
        <NewTaskModal
          defaultCol={modal}
          onSave={(task) => { addTask(task); setModal(null); }}
          onClose={() => setModal(null)}
        />
      )}
    </div>
  );
}