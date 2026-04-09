import { useRef, useEffect } from "react";
import { useTabs } from "./TabContext";
 
function TabIcon({ type }) {
  const cls = "w-3.5 h-3.5 flex-shrink-0";
  if (type === "home") return (
    <svg className={cls} viewBox="0 0 16 16" fill="none">
      <path d="M2 6.5L8 2l6 4.5V14a.5.5 0 01-.5.5h-4v-3H6.5v3h-4A.5.5 0 012 14V6.5z" stroke="currentColor" strokeWidth="1.2" />
    </svg>
  );
  if (type === "contact") return (
    <svg className={cls} viewBox="0 0 16 16" fill="none">
      <path d="M8 9.5A3.5 3.5 0 108 2.5a3.5 3.5 0 000 7z" stroke="currentColor" strokeWidth="1.2" />
      <path d="M2 14c0-2.21 2.686-4 6-4s6 1.79 6 4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
    </svg>
  );
  if (type === "client") return (
    <svg className={cls} viewBox="0 0 16 16" fill="none">
      <rect x="2" y="2" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.2" />
      <rect x="9" y="2" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.2" />
      <rect x="2" y="9" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.2" />
      <rect x="9" y="9" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.2" />
    </svg>
  );
  return (
    <svg className={cls} viewBox="0 0 16 16" fill="none">
      <path d="M4 2h6l4 4v8a1 1 0 01-1 1H4a1 1 0 01-1-1V3a1 1 0 011-1z" stroke="currentColor" strokeWidth="1.2" />
      <path d="M10 2v4h4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
    </svg>
  );
}
 
export default function TabBar() {
  const { tabs, activeTabId, setActiveTabId, closeTab } = useTabs();
  const scrollRef = useRef(null);
 
  useEffect(() => {
    const el = scrollRef.current?.querySelector(`[data-tab="${activeTabId}"]`);
    el?.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "nearest" });
  }, [activeTabId]);
 
  return (
    <div className="flex items-end h-10 border-b border-border-default bg-bg-subtle overflow-hidden select-none">
 
      <div
        ref={scrollRef}
        className="flex items-end flex-1 overflow-x-auto overflow-y-hidden gap-0 min-w-0"
        style={{ scrollbarWidth: "none" }}
      >
        {tabs.map((tab) => {
          const isActive = tab.id === activeTabId;
          return (
            <button
              key={tab.id}
              data-tab={tab.id}
              onClick={() => setActiveTabId(tab.id)}
              className={`
                group relative flex items-center gap-1.5 px-3 h-9 text-xs font-medium
                border-t border-l border-r rounded-t-md flex-shrink-0
                transition-colors duration-100 cursor-pointer
                max-w-[180px] min-w-[80px]
                ${isActive
                  ? "bg-bg-surface border-border-default text-text-primary -mb-px z-10"
                  : "bg-transparent border-transparent text-text-muted hover:text-text-secondary hover:bg-bg-muted/60 mb-0"
                }
              `}
            >
              {/* Hides the container's border-b on the active tab */}
              {isActive && (
                <span className="absolute bottom-[-1px] left-0 right-0 h-[1px] bg-bg-surface" />
              )}
 
              <TabIcon type={tab.icon} />
 
              <span className="truncate flex-1 text-left">{tab.label}</span>
 
              {tab.closeable && (
                <span
                  onClick={(e) => closeTab(tab.id, e)}
                  className={`
                    flex-shrink-0 w-4 h-4 rounded flex items-center justify-center
                    opacity-0 group-hover:opacity-100 transition-opacity
                    hover:bg-bg-muted text-text-muted hover:text-text-secondary
                    ${isActive ? "opacity-60" : ""}
                  `}
                >
                  <svg viewBox="0 0 10 10" className="w-2.5 h-2.5" fill="none">
                    <path d="M2 2l6 6M8 2l-6 6" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
                  </svg>
                </span>
              )}
            </button>
          );
        })}
      </div>
 
      {/* Overflow fade — uses an inline style because Tailwind can't compose this gradient from a CSS variable */}
      <div
        className="pointer-events-none absolute right-0 top-0 h-10 w-8"
        style={{ background: "linear-gradient(to left, var(--color-bg-subtle), transparent)" }}
      />
    </div>
  );
}