import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import { useState } from "react";
import { TabProvider, useTabs } from "./TabContext";
import TabBar from "./TabBar";
import Sidebar from "./Sidebar";
import { injectCSSVariables } from "./Theme.js";


injectCSSVariables(); // injects CSS variables based on Theme.js colors, fonts, etc.

// ── Placeholder page content — replace with your real views ──
function PageContent() {
  const { activeTabId } = useTabs();

  const titles = {
    home: "Welcome home",
    dashboard: "Dashboard",
    activity: "Recent Activity",
    tasks: "My Tasks",
    settings: "Settings",
    users: "Users",
    integrations: "Integrations",
  };

  const label = titles[activeTabId]
    ?? (activeTabId.startsWith("contact-")
        ? activeTabId.replace("contact-", "").replace(/-/g, " ")
        : activeTabId.replace("client-", "").replace(/-/g, " "));

  return (
    <div className="flex-1 flex flex-col items-center justify-center text-text-muted">
      <p className="text-2xl font-medium text-text-primary">{label}</p>
      <p className="text-sm mt-1">Tab ID: {activeTabId}</p>
    </div>
  );
}

export default function App() {
  return (
    <TabProvider>
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
    </TabProvider>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);