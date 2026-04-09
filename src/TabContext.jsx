import { createContext, useContext, useState, useCallback } from "react";

const TabContext = createContext(null);

export function TabProvider({ children }) {
  const [tabs, setTabs] = useState([
    { id: "home", label: "Home", icon: "home", closeable: false },
  ]);
  const [activeTabId, setActiveTabId] = useState("home");

  const openTab = useCallback((id, label, icon = "page") => {
    setTabs((prev) => {
      if (prev.find((t) => t.id === id)) return prev;
      return [...prev, { id, label, icon, closeable: true }];
    });
    setActiveTabId(id);
  }, []);

  const closeTab = useCallback((id, e) => {
    e?.stopPropagation();
    setTabs((prev) => {
      const idx = prev.findIndex((t) => t.id === id);
      const next = prev.filter((t) => t.id !== id);
      if (activeTabId === id && next.length > 0) {
        const newActive = next[Math.min(idx, next.length - 1)];
        setActiveTabId(newActive.id);
      }
      return next;
    });
  }, [activeTabId]);

  return (
    <TabContext.Provider value={{ tabs, activeTabId, setActiveTabId, openTab, closeTab }}>
      {children}
    </TabContext.Provider>
  );
}

export function useTabs() {
  const ctx = useContext(TabContext);
  if (!ctx) throw new Error("useTabs must be used inside TabProvider");
  return ctx;
}
