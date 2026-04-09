/**
 * theme.js — single source of truth for all design tokens.
 *
 * How it works:
 *  1. CSS variables are injected into :root at app startup (see main.jsx)
 *  2. Tailwind reads these same variables via tailwind.config.js
 *  3. Any component can also import tokens directly for inline styles or JS logic
 *
 * To retheme the entire app: edit the values in `colors` below. Nothing else needs to change.
 */
 
export const colors = {
  // ── Brand ──────────────────────────────────────────────────────
  primary:        "#C1E899",   // green  — buttons, badges, active accents
  primaryHover:   "#55883B",   // green-600
  primaryLight:   "#E6F0DC",   // green-50   — subtle tinted backgrounds
  primaryText:    "#9A6735",   // green-700  — text on primaryLight bg
 
  // ── Neutrals ───────────────────────────────────────────────────
  bgPage:         "#E6F0DC",   // overall page background
  bgSurface:      "#FFFFFF",   // cards, sidebar, modals
  bgSubtle:       "#F3F4F6",   // hover states, selected rows
  bgMuted:        "#E5E7EB",   // dividers, skeleton loaders
 
  borderDefault:  "#E5E7EB",   // gray-200  — standard borders
  borderStrong:   "#D1D5DB",   // gray-300  — emphasis borders
 
  textPrimary:    "#111827",   // gray-900  — headings, strong labels
  textSecondary:  "#4B5563",   // gray-600  — body copy
  textMuted:      "#9CA3AF",   // gray-400  — placeholders, section labels
  textInverse:    "#FFFFFF",   // on dark backgrounds
 
  // ── Semantic ───────────────────────────────────────────────────
  success:        "#10B981",
  successLight:   "#ECFDF5",
  successText:    "#047857",
 
  warning:        "#F59E0B",
  warningLight:   "#FFFBEB",
  warningText:    "#B45309",
 
  danger:         "#EF4444",
  dangerLight:    "#FEF2F2",
  dangerText:     "#B91C1C",
 
  info:           "#8B5CF6",
  infoLight:      "#F5F3FF",
  infoText:       "#7C3AED",
};
 
// ── Client dot palette — cycles when you have more clients than entries ──
export const clientPalette = [
  { bg: colors.primaryLight, text: colors.primaryText  },        // blue
  { bg: colors.infoLight,    text: colors.infoText     },        // violet
  { bg: colors.successLight, text: colors.successText  },        // emerald
  { bg: colors.warningLight, text: colors.warningText  },        // amber
  { bg: colors.dangerLight,  text: colors.dangerText   },        // rose
];
 
// ── Typography ─────────────────────────────────────────────────
export const fonts = {
  sans: '"Inter", ui-sans-serif, system-ui, sans-serif',
  mono: '"JetBrains Mono", ui-monospace, monospace',
};
 
// ── Spacing & radius ───────────────────────────────────────────
export const radius = {
  sm:   "4px",
  md:   "8px",
  lg:   "12px",
  full: "9999px",
};
 
// ── Sidebar ────────────────────────────────────────────────────
export const sidebar = {
  width:      "256px",
  background: colors.bgSurface,
  border:     colors.borderDefault,
};
 
// ── Tab bar ────────────────────────────────────────────────────
export const tabBar = {
  height:          "40px",
  background:      colors.bgSubtle,
  border:          colors.borderDefault,
  activeBackground: colors.bgSurface,
  inactiveText:    colors.textMuted,
  activeText:      colors.textPrimary,
};
 
/**
 * Converts the flat `colors` object into CSS custom properties.
 * Called once in main.jsx:  injectCSSVariables()
 *
 * Produces variables like:
 *   --color-primary: #3B82F6;
 *   --color-bg-page: #F9FAFB;
 *   --color-text-primary: #111827;
 *   etc.
 */
export function injectCSSVariables() {
  const toKebab = (str) =>
    str.replace(/([A-Z])/g, (m) => `-${m.toLowerCase()}`);
 
  const root = document.documentElement;
 
  Object.entries(colors).forEach(([key, value]) => {
    root.style.setProperty(`--color-${toKebab(key)}`, value);
  });
 
  Object.entries(radius).forEach(([key, value]) => {
    root.style.setProperty(`--radius-${key}`, value);
  });
 
  root.style.setProperty("--font-sans", fonts.sans);
  root.style.setProperty("--font-mono", fonts.mono);
  root.style.setProperty("--sidebar-width", sidebar.width);
  root.style.setProperty("--tab-bar-height", tabBar.height);
}
 