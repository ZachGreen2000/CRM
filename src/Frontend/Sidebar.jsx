import { useState } from "react";
import { useTabs } from "./TabContext";
import { clientPalette } from "./Theme.js";
 
const clients = [
  { id: "acme", name: "Acme Corp", initials: "AC", contacts: [
    { id: "alice", name: "Alice Martin" },
    { id: "bob", name: "Bob Lee" },
    { id: "clara", name: "Clara Singh" },
  ]},
  { id: "globex", name: "Globex Inc", initials: "GX", contacts: [
    { id: "david", name: "David Park" },
    { id: "ella", name: "Ella James" },
  ]},
  { id: "umbrella", name: "Umbrella Ltd", initials: "UL", contacts: [
    { id: "frank", name: "Frank Moore" },
    { id: "grace", name: "Grace Kim" },
    { id: "hiro", name: "Hiro Tanaka" },
  ]},
  { id: "initech", name: "Initech", initials: "IT", contacts: [
    { id: "jack", name: "Jack White" },
    { id: "karen", name: "Karen Chen" },
  ]},
];
 
function getInitials(name) {
  return name.split(" ").map((w) => w[0]).join("").toUpperCase().slice(0, 2);
}
 
export default function Sidebar() {
  const { openTab, activeTabId } = useTabs();
  const [openClients, setOpenClients] = useState({});
 
  function handleNav(id, label, icon) { openTab(id, label, icon); }
  function toggleClient(id) { setOpenClients((prev) => ({ ...prev, [id]: !prev[id] })); }
  function openClient(client) { openTab(`client-${client.id}`, client.name, "client"); }
  function openContact(contact) { openTab(`contact-${contact.id}`, contact.name, "contact"); }
 
  return (
    <aside className="w-64 h-full bg-bg-surface border-r border-border-default flex flex-col">
 
      {/* Profile */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-border-default">
        <div className="w-9 h-9 rounded-full bg-primary flex items-center justify-center text-text-inverse text-sm font-medium flex-shrink-0">
          JC
        </div>
        <div className="min-w-0">
          <p className="text-sm font-medium text-text-primary truncate">Jane Cooper</p>
          <p className="text-xs text-text-secondary">Administrator</p>
        </div>
      </div>
 
      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-2 py-3">
 
        <SectionLabel>Main Menu</SectionLabel>
 
        <NavItem icon={<HomeIcon />}  label="Home"      active={activeTabId === "home"}      onClick={() => handleNav("home", "Home", "home")} />
        <NavItem icon={<GridIcon />}  label="Dashboard" active={activeTabId === "dashboard"} onClick={() => handleNav("dashboard", "Dashboard", "page")} />
        <NavItem icon={<ClockIcon />} label="Activity"  active={activeTabId === "activity"}  onClick={() => handleNav("activity", "Activity", "page")} badge={5} />
        <NavItem icon={<ListIcon />}  label="Tasks"     active={activeTabId === "tasks"}     onClick={() => handleNav("tasks", "Tasks", "page")} />
 
        <SectionLabel>Clients</SectionLabel>
 
        {clients.map((client, idx) => {
          const style = clientPalette[idx % clientPalette.length];
          const isOpen = !!openClients[client.id];
          const clientTabId = `client-${client.id}`;
 
          return (
            <div key={client.id}>
              <button
                onClick={() => { toggleClient(client.id); openClient(client); }}
                className={`w-full flex items-center gap-2.5 px-2 py-1.5 rounded-lg text-sm transition-colors
                  ${activeTabId === clientTabId
                    ? "bg-bg-subtle text-text-primary"
                    : "text-text-secondary hover:bg-bg-subtle hover:text-text-primary"}`}
              >
                <span
                  className="w-7 h-7 rounded-md flex items-center justify-center text-[11px] font-medium flex-shrink-0"
                  style={{ background: style.bg, color: style.text }}
                >
                  {client.initials}
                </span>
                <span className="flex-1 text-left truncate">{client.name}</span>
                <svg
                  className={`w-3.5 h-3.5 text-text-muted flex-shrink-0 transition-transform duration-150 ${isOpen ? "rotate-90" : ""}`}
                  viewBox="0 0 14 14" fill="none"
                >
                  <path d="M5 3l4 4-4 4" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
 
              {isOpen && (
                <div className="mt-0.5 mb-1">
                  {client.contacts.map((contact) => {
                    const tabId = `contact-${contact.id}`;
                    return (
                      <button
                        key={contact.id}
                        onClick={() => openContact(contact)}
                        className={`w-full flex items-center gap-2 pl-11 pr-2 py-1.5 rounded-lg text-sm transition-colors
                          ${activeTabId === tabId
                            ? "bg-bg-subtle text-text-primary"
                            : "text-text-secondary hover:bg-bg-subtle hover:text-text-primary"}`}
                      >
                        <span
                          className="w-5 h-5 rounded-full flex items-center justify-center text-[9px] font-medium flex-shrink-0"
                          style={{ background: style.bg, color: style.text }}
                        >
                          {getInitials(contact.name)}
                        </span>
                        <span className="truncate">{contact.name}</span>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
 
        <SectionLabel>General</SectionLabel>
 
        <NavItem icon={<SettingsIcon />} label="Settings"     active={activeTabId === "settings"}     onClick={() => handleNav("settings", "Settings", "page")} />
        <NavItem icon={<UserIcon />}     label="Users"        active={activeTabId === "users"}        onClick={() => handleNav("users", "Users", "page")} />
        <NavItem icon={<PlugIcon />}     label="Integrations" active={activeTabId === "integrations"} onClick={() => handleNav("integrations", "Integrations", "page")} />
 
      </nav>
    </aside>
  );
}
 
function SectionLabel({ children }) {
  return (
    <p className="text-[11px] font-medium uppercase tracking-wider text-text-muted px-2 pt-4 pb-1">
      {children}
    </p>
  );
}
 
function NavItem({ icon, label, active, badge, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-2.5 px-2 py-1.5 rounded-lg text-sm transition-colors
        ${active ? "bg-bg-subtle text-text-primary" : "text-text-secondary hover:bg-bg-subtle hover:text-text-primary"}`}
    >
      <span className={`w-4 h-4 flex-shrink-0 ${active ? "opacity-100" : "opacity-50"}`}>{icon}</span>
      <span className="flex-1 text-left">{label}</span>
      {badge && (
        <span className="text-[10px] font-medium bg-primary text-text-inverse px-1.5 py-0.5 rounded-full leading-none">
          {badge}
        </span>
      )}
    </button>
  );
}
 
function HomeIcon() {
  return <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4"><path d="M2 6.5L8 2l6 4.5V14a.5.5 0 01-.5.5h-4v-3H6.5v3h-4A.5.5 0 012 14V6.5z" stroke="currentColor" strokeWidth="1.2"/></svg>;
}
function GridIcon() {
  return <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4"><rect x="2" y="2" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.2"/><rect x="9" y="2" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.2"/><rect x="2" y="9" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.2"/><rect x="9" y="9" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.2"/></svg>;
}
function ClockIcon() {
  return <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4"><circle cx="8" cy="8" r="5.5" stroke="currentColor" strokeWidth="1.2"/><path d="M8 5v3.5l2 2" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/></svg>;
}
function ListIcon() {
  return <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4"><path d="M13 11.5H3M13 8H3M13 4.5H3" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/></svg>;
}
function SettingsIcon() {
  return <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4"><circle cx="8" cy="8" r="2.5" stroke="currentColor" strokeWidth="1.2"/><path d="M8 1v2M8 13v2M1 8h2M13 8h2M3.05 3.05l1.41 1.41M11.54 11.54l1.41 1.41M3.05 12.95l1.41-1.41M11.54 4.46l1.41-1.41" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/></svg>;
}
function UserIcon() {
  return <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4"><path d="M8 9.5A3.5 3.5 0 108 2.5a3.5 3.5 0 000 7z" stroke="currentColor" strokeWidth="1.2"/><path d="M2 14c0-2.21 2.686-4 6-4s6 1.79 6 4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/></svg>;
}
function PlugIcon() {
  return <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4"><path d="M6 2v3M10 2v3M4 5h8v2a4 4 0 01-8 0V5zM8 11v3" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/></svg>;
}