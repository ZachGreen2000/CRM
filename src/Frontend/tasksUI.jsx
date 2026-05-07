import { useState } from "react";

export default function TasksUI() {
  const [tasks, setTasks] = useState({
    backlog: [
      { id: 1, title: "Write API documentation", description: "Cover all v2 endpoints", priority: "MEDIUM", date: "May 14" },
      { id: 2, title: "User interview — 3 sessions", description: "Schedule via Calendly", priority: "LOW", date: "May 20" },
      { id: 3, title: "Migrate to Postgres 16", priority: "LOW", date: "May 18" },
    ],
    todo: [
      { id: 4, title: "Redesign onboarding flow", description: "Focus on mobile-first approach", priority: "HIGH", date: "May 10" },
      { id: 5, title: "Performance audit", description: "Lighthouse + bundle size", priority: "MEDIUM", date: "May 7" },
      { id: 6, title: "Release v2.3.0", description: "Tag + changelog", priority: "CRITICAL", date: "May 7" },
    ],
    inprogress: [
      { id: 7, title: "Fix auth token expiry bug", priority: "CRITICAL", date: "May 8" },
      { id: 8, title: "Deploy staging environment", priority: "HIGH", date: "May 7" },
    ],
    done: [
      { id: 9, title: "Accessibility review", description: "WCAG 2.1 AA", priority: "MEDIUM" },
    ],
  });

  const priorityColors = {
    CRITICAL: { bg: "#FEE2E2", text: "#B91C1C", label: "CRITICAL" },
    HIGH: { bg: "#FEF3C7", text: "#92400E", label: "HIGH" },
    MEDIUM: { bg: "#E0E7FF", text: "#3730A3", label: "MEDIUM" },
    LOW: { bg: "#DCFCE7", text: "#166534", label: "LOW" },
  };

  const columns = [
    { key: "backlog", title: "Backlog", count: tasks.backlog.length },
    { key: "todo", title: "To do", count: tasks.todo.length },
    { key: "inprogress", title: "In progress", count: tasks.inprogress.length },
    { key: "done", title: "Done", count: tasks.done.length },
  ];

  const TaskCard = ({ task }) => {
    const priority = priorityColors[task.priority] || priorityColors.MEDIUM;
    return (
      <div style={styles.taskCard}>
        <div style={styles.taskHeader}>
          <h4 style={styles.taskTitle}>{task.title}</h4>
          <div style={styles.taskActions}>
            <button style={styles.dragHandle} aria-label="Drag task">⋮⋮</button>
            <button style={styles.closeBtn} aria-label="Close task">×</button>
          </div>
        </div>
        {task.description && (
          <p style={styles.taskDescription}>{task.description}</p>
        )}
        <div style={styles.taskFooter}>
          <span style={{ ...styles.priorityBadge, ...priority, background: priority.bg, color: priority.text }}>
            {priority.label}
          </span>
          {task.date && <span style={styles.taskDate}>{task.date}</span>}
        </div>
      </div>
    );
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div>
          <h2 style={styles.title}>Task board</h2>
          <p style={styles.subtitle}>May 7 · 9 tasks · 1 done · 2 critical</p>
        </div>
        <div style={styles.headerActions}>
          <select style={styles.filterSelect}>
            <option>All priorities</option>
            <option>Critical</option>
            <option>High</option>
            <option>Medium</option>
            <option>Low</option>
          </select>
          <button style={styles.newTaskBtn}>+ New task</button>
        </div>
      </div>

      {/* Kanban Board */}
      <div style={styles.board}>
        {columns.map((column) => (
          <div key={column.key} style={styles.column}>
            <div style={styles.columnHeader}>
              <div style={styles.columnTitle}>
                <div style={styles.columnDot}></div>
                <span>{column.title}</span>
                <span style={styles.columnCount}>{column.count}</span>
              </div>
              <button style={styles.addBtn} aria-label={`Add ${column.title}`}>+</button>
            </div>
            <div style={styles.columnTasks}>
              {tasks[column.key].map((task) => (
                <TaskCard key={task.id} task={task} />
              ))}
              <button style={styles.addTaskInColumn}>+ Add</button>
            </div>
          </div>
        ))}
      </div>

      {/* Divider */}
      <div style={styles.divider}></div>

      {/* Today Section */}
      <div style={styles.todaySection}>
        <h3 style={styles.todayTitle}>TODAY — MAY 7</h3>
        <div style={styles.todayTasks}>
          <div style={styles.todayCard}>
            <div style={styles.todayCardHeader}>
              <span style={{ ...priorityColors.HIGH, fontSize: "11px", fontWeight: "600", background: priorityColors.HIGH.bg, color: priorityColors.HIGH.text, padding: "4px 8px", borderRadius: "4px" }}>
                HIGH
              </span>
              <span style={styles.todayCardStatus}>In progress</span>
            </div>
            <h4 style={styles.todayCardTitle}>Deploy staging environment</h4>
            <p style={styles.todayCardDesc}></p>
          </div>

          <div style={styles.todayCard}>
            <div style={styles.todayCardHeader}>
              <span style={{ ...priorityColors.MEDIUM, fontSize: "11px", fontWeight: "600", background: priorityColors.MEDIUM.bg, color: priorityColors.MEDIUM.text, padding: "4px 8px", borderRadius: "4px" }}>
                MEDIUM
              </span>
              <span style={styles.todayCardStatus}>To do</span>
            </div>
            <h4 style={styles.todayCardTitle}>Performance audit</h4>
            <p style={styles.todayCardDesc}>Lighthouse + bundle size</p>
          </div>

          <div style={styles.todayCard}>
            <div style={styles.todayCardHeader}>
              <span style={{ ...priorityColors.CRITICAL, fontSize: "11px", fontWeight: "600", background: priorityColors.CRITICAL.bg, color: priorityColors.CRITICAL.text, padding: "4px 8px", borderRadius: "4px" }}>
                CRITICAL
              </span>
              <span style={styles.todayCardStatus}>To do</span>
            </div>
            <h4 style={styles.todayCardTitle}>Release v2.3.0</h4>
            <p style={styles.todayCardDesc}>Tag + changelog</p>
          </div>
        </div>
      </div>
    </div>
  );
}

const styles = {
  container: {
    padding: "24px",
    background: "#FFFFFF",
    height: "100%",
    overflowY: "auto",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: "24px",
  },
  title: {
    fontSize: "24px",
    fontWeight: "700",
    color: "#111827",
    margin: "0 0 4px 0",
  },
  subtitle: {
    fontSize: "13px",
    color: "#9CA3AF",
    margin: 0,
  },
  headerActions: {
    display: "flex",
    gap: "12px",
    alignItems: "center",
  },
  filterSelect: {
    padding: "8px 12px",
    border: "1.5px solid #E5E7EB",
    borderRadius: "8px",
    fontSize: "13px",
    color: "#111827",
    background: "#FFFFFF",
    cursor: "pointer",
    outline: "none",
  },
  newTaskBtn: {
    padding: "8px 14px",
    background: "linear-gradient(135deg, #C1E899, #55883B)",
    color: "#FFFFFF",
    border: "none",
    borderRadius: "8px",
    fontSize: "13px",
    fontWeight: "600",
    cursor: "pointer",
    transition: "transform 0.15s, box-shadow 0.15s",
  },
  board: {
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    gap: "16px",
    marginBottom: "24px",
  },
  column: {
    background: "#F9FAFB",
    borderRadius: "12px",
    border: "1px solid #E5E7EB",
    padding: "0",
    display: "flex",
    flexDirection: "column",
    maxHeight: "600px",
  },
  columnHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "12px 14px",
    borderBottom: "1px solid #E5E7EB",
    background: "#F3F9EE",
  },
  columnTitle: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    fontSize: "13px",
    fontWeight: "600",
    color: "#111827",
  },
  columnDot: {
    width: "8px",
    height: "8px",
    borderRadius: "50%",
    background: "#55883B",
  },
  columnCount: {
    fontSize: "12px",
    color: "#9CA3AF",
    fontWeight: "500",
  },
  addBtn: {
    width: "24px",
    height: "24px",
    borderRadius: "6px",
    border: "1px solid #E5E7EB",
    background: "transparent",
    color: "#9CA3AF",
    cursor: "pointer",
    fontSize: "14px",
    transition: "background 0.15s, color 0.15s",
  },
  columnTasks: {
    flex: 1,
    overflowY: "auto",
    padding: "8px",
    display: "flex",
    flexDirection: "column",
    gap: "8px",
    scrollbarWidth: "thin",
    scrollbarColor: "#E5E7EB transparent",
  },
  taskCard: {
    background: "#FFFFFF",
    borderRadius: "10px",
    border: "1px solid #E5E7EB",
    padding: "12px",
    boxShadow: "0 1px 2px rgba(0, 0, 0, 0.04)",
    cursor: "grab",
  },
  taskHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: "8px",
  },
  taskTitle: {
    fontSize: "13px",
    fontWeight: "600",
    color: "#111827",
    margin: 0,
    flex: 1,
  },
  taskActions: {
    display: "flex",
    gap: "4px",
    marginLeft: "8px",
  },
  dragHandle: {
    width: "24px",
    height: "24px",
    border: "none",
    background: "transparent",
    color: "#D1D5DB",
    cursor: "grab",
    fontSize: "12px",
    fontWeight: "700",
  },
  closeBtn: {
    width: "24px",
    height: "24px",
    border: "none",
    background: "transparent",
    color: "#D1D5DB",
    cursor: "pointer",
    fontSize: "18px",
  },
  taskDescription: {
    fontSize: "12px",
    color: "#6B7280",
    margin: "0 0 8px 0",
    lineHeight: "1.4",
  },
  taskFooter: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "8px",
  },
  priorityBadge: {
    fontSize: "11px",
    fontWeight: "600",
    padding: "4px 8px",
    borderRadius: "4px",
  },
  taskDate: {
    fontSize: "11px",
    color: "#9CA3AF",
    whiteSpace: "nowrap",
  },
  addTaskInColumn: {
    width: "100%",
    padding: "8px",
    border: "1.5px dashed #E5E7EB",
    background: "transparent",
    color: "#9CA3AF",
    fontSize: "12px",
    fontWeight: "600",
    borderRadius: "8px",
    cursor: "pointer",
    transition: "border-color 0.15s, color 0.15s",
  },
  divider: {
    height: "1px",
    background: "#E5E7EB",
    marginBottom: "20px",
  },
  todaySection: {
    marginTop: "20px",
  },
  todayTitle: {
    fontSize: "12px",
    fontWeight: "700",
    color: "#111827",
    letterSpacing: "0.05em",
    margin: "0 0 12px 0",
    textTransform: "uppercase",
  },
  todayTasks: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
    gap: "12px",
  },
  todayCard: {
    background: "#F9FAFB",
    borderLeft: "3px solid #55883B",
    borderRadius: "8px",
    padding: "12px",
    cursor: "pointer",
    transition: "background 0.15s, box-shadow 0.15s",
  },
  todayCardHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "8px",
  },
  todayCardStatus: {
    fontSize: "11px",
    color: "#6B7280",
    fontWeight: "500",
  },
  todayCardTitle: {
    fontSize: "14px",
    fontWeight: "600",
    color: "#111827",
    margin: "0 0 4px 0",
  },
  todayCardDesc: {
    fontSize: "12px",
    color: "#6B7280",
    margin: 0,
  },
};
