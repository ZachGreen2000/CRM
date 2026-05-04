import { useState, useEffect } from "react";
import { clientPalette } from "./Theme";

function getInitials(name) {
  return name.split(" ").map((w) => w[0]).join("").toUpperCase().slice(0, 2);
}

function PlusIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path d="M8 3v10M3 8h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function ChevronDownIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
      <path d="M3 5l4 4 4-4" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function XIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
      <path d="M12 4L4 12M4 4l8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

// Section presets
const SECTION_PRESETS = [
  { id: "email-threads", label: "Email Threads", icon: "✉️" },
  { id: "ai-overview", label: "AI Overview", icon: "🤖" },
  { id: "key-interests", label: "Key Interests", icon: "⭐" },
  { id: "current-projects", label: "Current Projects", icon: "📋" },
];

function SectionPresetPicker({ onSelect, onClose, existingSectionIds }) {
  const [customName, setCustomName] = useState("");

  const availablePresets = SECTION_PRESETS.filter(
    (p) => !existingSectionIds.includes(p.id)
  );

  const handleAddCustom = () => {
    if (customName.trim()) {
      onSelect({
        id: `custom-${Date.now()}`,
        label: customName,
        icon: "📝",
        isCustom: true,
      });
      setCustomName("");
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="bg-bg-surface rounded-lg shadow-lg p-6 w-96 max-h-96 overflow-y-auto">
        <h3 className="text-lg font-semibold text-text-primary mb-4">Add Section</h3>

        {/* Presets */}
        <div className="mb-4">
          <p className="text-xs font-medium text-text-muted mb-2 uppercase">Presets</p>
          <div className="space-y-2">
            {availablePresets.length === 0 ? (
              <p className="text-sm text-text-secondary">All preset sections added</p>
            ) : (
              availablePresets.map((preset) => (
                <button
                  key={preset.id}
                  onClick={() => {
                    onSelect(preset);
                    onClose();
                  }}
                  className="w-full flex items-center gap-3 p-3 rounded-lg bg-bg-subtle hover:bg-bg-hover text-text-primary transition-colors"
                >
                  <span className="text-lg">{preset.icon}</span>
                  <span className="text-sm font-medium">{preset.label}</span>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Custom Section */}
        <div className="border-t border-border-default pt-4">
          <p className="text-xs font-medium text-text-muted mb-2 uppercase">Custom</p>
          <div className="flex gap-2">
            <input
              type="text"
              value={customName}
              onChange={(e) => setCustomName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleAddCustom();
              }}
              placeholder="Section name..."
              className="flex-1 px-3 py-2 rounded-lg bg-bg-hover border border-border-default text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <button
              onClick={handleAddCustom}
              disabled={!customName.trim()}
              className="px-3 py-2 rounded-lg bg-primary text-text-inverse text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Add
            </button>
          </div>
        </div>

        {/* Close button */}
        <button
          onClick={onClose}
          className="mt-4 w-full py-2 text-sm text-text-secondary hover:text-text-primary"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

function ContactSummarySection({ contact }) {
  return (
    <div className="bg-bg-surface rounded-lg border border-border-default p-6 mb-4">
      <div className="flex gap-4">
        {/* Avatar */}
        <div className="flex-shrink-0">
          <div
            className="w-20 h-20 rounded-lg flex items-center justify-center text-2xl font-semibold text-text-inverse"
            style={{
              background: clientPalette[0]?.bg || "#6366f1",
              color: clientPalette[0]?.text || "#ffffff",
            }}
          >
            {getInitials(contact.name)}
          </div>
        </div>

        {/* Info */}
        <div className="flex-1">
          <h2 className="text-2xl font-semibold text-text-primary">{contact.name}</h2>
          
          <div className="mt-2 space-y-1">
            {contact.title && (
              <p className="text-sm font-medium text-text-secondary">{contact.title}</p>
            )}
            {contact.company && (
              <p className="text-sm text-text-secondary">{contact.company}</p>
            )}
          </div>

          <div className="mt-4 space-y-2 text-sm">
            {contact.email && (
              <p className="text-text-secondary">
                <span className="font-medium">Email:</span>{" "}
                <a href={`mailto:${contact.email}`} className="text-primary hover:underline">
                  {contact.email}
                </a>
              </p>
            )}
            {contact.phone && (
              <p className="text-text-secondary">
                <span className="font-medium">Phone:</span> {contact.phone}
              </p>
            )}
            {contact.location && (
              <p className="text-text-secondary">
                <span className="font-medium">Location:</span> {contact.location}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function Section({ section, onRemove, isCustom }) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [content, setContent] = useState(section.content || "");
  const [isEditing, setIsEditing] = useState(false);

  return (
    <div className="bg-bg-surface rounded-lg border border-border-default mb-4 overflow-hidden">
      {/* Header */}
      <div
        className="flex items-center justify-between p-4 bg-bg-subtle hover:bg-bg-hover cursor-pointer transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <span className="text-lg">{section.icon || "📄"}</span>
          <h3 className="font-medium text-text-primary">{section.label}</h3>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onRemove();
            }}
            className="p-1.5 rounded text-text-muted hover:text-text-primary hover:bg-bg-hover transition-colors"
            title="Remove section"
          >
            <XIcon />
          </button>

          <button
            className={`p-1.5 rounded text-text-muted hover:text-text-primary hover:bg-bg-hover transition-all ${
              isExpanded ? "rotate-180" : ""
            }`}
          >
            <ChevronDownIcon />
          </button>
        </div>
      </div>

      {/* Content */}
      {isExpanded && (
        <div className="p-4 border-t border-border-default">
          {isCustom && isEditing ? (
            <div className="space-y-2">
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Add your notes here..."
                className="w-full px-3 py-2 rounded-lg bg-bg-subtle border border-border-default text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                rows={4}
              />
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    section.content = content;
                    setIsEditing(false);
                  }}
                  className="px-3 py-1.5 rounded text-sm font-medium bg-primary text-text-inverse hover:bg-primary/90 transition-colors"
                >
                  Save
                </button>
                <button
                  onClick={() => setIsEditing(false)}
                  className="px-3 py-1.5 rounded text-sm font-medium bg-bg-subtle text-text-primary hover:bg-bg-hover transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : isCustom ? (
            <div>
              <p className="text-sm text-text-secondary whitespace-pre-wrap mb-2">
                {content || <span className="italic text-text-muted">No content yet</span>}
              </p>
              <button
                onClick={() => setIsEditing(true)}
                className="px-3 py-1.5 rounded text-sm font-medium bg-bg-subtle text-text-primary hover:bg-bg-hover transition-colors"
              >
                Edit
              </button>
            </div>
          ) : (
            <div className="text-sm text-text-secondary">
              <p className="italic">This preset section would display data from your backend.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function ContactProfile({ contact }) {
  const [sections, setSections] = useState([
    {
      id: "contact-summary",
      label: "Contact Summary",
      icon: "👤",
      isFixed: true,
    },
  ]);
  const [showSectionPicker, setShowSectionPicker] = useState(false);

  const handleAddSection = (preset) => {
    setSections((prev) => [
      ...prev,
      {
        ...preset,
        content: "",
      },
    ]);
  };

  const handleRemoveSection = (id) => {
    setSections((prev) => prev.filter((s) => s.id !== id));
  };

  const existingSectionIds = sections.map((s) => s.id);

  return (
    <div className="flex-1 overflow-auto">
      <div className="max-w-4xl mx-auto p-6">
        {/* Contact Summary - Always at top */}
        <ContactSummarySection contact={contact} />

        {/* Add Section Button */}
        <button
          onClick={() => setShowSectionPicker(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-text-inverse text-sm font-medium hover:bg-primary/90 transition-colors mb-6"
        >
          <PlusIcon />
          Add Section
        </button>

        {/* Sections */}
        {sections.slice(1).map((section) => (
          <Section
            key={section.id}
            section={section}
            onRemove={() => handleRemoveSection(section.id)}
            isCustom={section.isCustom}
          />
        ))}

        {/* Section Picker Modal */}
        {showSectionPicker && (
          <SectionPresetPicker
            onSelect={handleAddSection}
            onClose={() => setShowSectionPicker(false)}
            existingSectionIds={existingSectionIds}
          />
        )}
      </div>
    </div>
  );
}
