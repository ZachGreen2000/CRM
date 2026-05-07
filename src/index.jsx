import React from 'react';
import ReactDOM from 'react-dom/client';
import './Frontend/index.css';
import { useState } from "react";
import { TabProvider, useTabs } from "./Frontend/TabContext.jsx";
import TabBar from "./Frontend/TabBar.jsx";
import Sidebar from "./Frontend/Sidebar.jsx";
import ContactProfile from "./Frontend/ContactProfile.jsx";
import TasksUI from "./Frontend/tasksUI.jsx"; // <-- ADDED IMPORT
import { injectCSSVariables } from "./Frontend/Theme.js";
import Floatingchat from "./Frontend/Floatingchat.jsx";
import { useChat } from "./hooks/useChat";


injectCSSVariables(); // injects CSS variables based on Theme.js colors, fonts, etc.

// ── Placeholder page content — replace with your real views ──
function PageContent() {
  const { activeTabId, tabs } = useTabs();

  // Find the current tab to get its data
  const currentTab = tabs.find(t => t.id === activeTabId);

  // 1. Handle Tasks Tab (New Logic)
  if (activeTabId === "tasks") {
    return <TasksUI />;
  }

  // 2. Check if this is a contact tab (Existing Logic)
  if (activeTabId && activeTabId.startsWith("contact-") && currentTab?.data) {
    return <ContactProfile contact={currentTab.data} />;
  }

  const titles = {
    home: "Welcome home",
    dashboard: "Dashboard",
    activity: "Recent Activity",
    tasks: "My Tasks",
    settings: "Settings",
    users: "Users",
    integrations: "Integrations",
  };

  // Determine label for other tabs
  const label = titles[activeTabId]
    ?? (activeTabId && typeof activeTabId === 'string'
        ? (activeTabId.startsWith("contact-")
            ? activeTabId.replace("contact-", "").replace(/-/g, " ")
            : activeTabId.replace("client-", "").replace(/-/g, " "))
        : "Unknown");

  // Fallback for other tabs
  return (
    <div className="flex-1 flex flex-col items-center justify-center text-text-muted">
      <p className="text-2xl font-medium text-text-primary">{label}</p>
      <p className="text-sm mt-1">Tab ID: {activeTabId}</p>
    </div >
  );
}

function AppContent() {
  const { activeTabId, tabs } = useTabs();
  const { sendMessage } = useChat();

  const uiContext = {
    current_tab_id: activeTabId,
    active_tab_id: activeTabId,
    tabs,
    user: "Jane Cooper, Administrator",
    sidebar_items: "Clients, General, Settings",
  };
  return (
    <>
      <Floatingchat onSend={async (message) => {
        const result = await sendMessage(message, uiContext);
        if (result?.tool_used === "add_contact" || result?.tool_used === "add_client") {
          window.dispatchEvent(new CustomEvent('clientsUpdated'));
        }
        return result.reply;
      }} />
      <div className="flex h-screen overflow-hidden bg-bg-page">

        {/* Sidebar */}
        <Sidebar />

        {/* Main area */}
        <div className="flex-1 flex flex-col min-w-0">

          {/* Tab bar */}
          <TabBar />

          {/* Page content */}
          <main className="flex-1 overflow-auto">
            <PageContent />
          </main>

        </div>
      </div>
    </>
  );
}

export default function App() {
  return (
    <TabProvider>
      <AppContent />
    </TabProvider>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
