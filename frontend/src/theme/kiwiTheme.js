import { createTheme } from "@mui/material/styles";

// Kiwi palette: 028174, 0AB68B, 92DE8B, FFE3B3
export const palette = {
  primary: "#028174",
  primaryDark: "#02403A",
  accent: "#0AB68B",
  light: "#92DE8B",
  cream: "#FFE3B3",
  bg: "#FAFBF8",
  surface: "#FFFFFF",
  surfaceAlt: "#F0F5F2",
  text: "#0E2A26",
  textMuted: "#5C746F",
  border: "#E2EBE6",
  danger: "#D04A4A",
  warning: "#E3A24C",
};

export const chartPalette = [
  "#028174",
  "#0AB68B",
  "#92DE8B",
  "#FFE3B3",
  "#5DBFB0",
  "#057F70",
  "#C2EBC0",
  "#F4C57A",
];

export const kiwiTheme = createTheme({
  palette: {
    mode: "light",
    primary: { main: palette.primary, contrastText: "#fff" },
    secondary: { main: palette.accent, contrastText: "#fff" },
    background: { default: palette.bg, paper: palette.surface },
    text: { primary: palette.text, secondary: palette.textMuted },
    divider: palette.border,
    success: { main: palette.accent },
    warning: { main: palette.warning },
    error: { main: palette.danger },
  },
  shape: { borderRadius: 14 },
  typography: {
    fontFamily: "'DM Sans', system-ui, sans-serif",
    h1: { fontFamily: "'Sora', sans-serif", fontWeight: 700, letterSpacing: "-0.02em" },
    h2: { fontFamily: "'Sora', sans-serif", fontWeight: 700, letterSpacing: "-0.02em" },
    h3: { fontFamily: "'Sora', sans-serif", fontWeight: 700, letterSpacing: "-0.015em" },
    h4: { fontFamily: "'Sora', sans-serif", fontWeight: 700, letterSpacing: "-0.01em" },
    h5: { fontFamily: "'Sora', sans-serif", fontWeight: 600 },
    h6: { fontFamily: "'Sora', sans-serif", fontWeight: 600 },
    button: { textTransform: "none", fontWeight: 600 },
    overline: { letterSpacing: "0.12em", fontWeight: 600 },
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: "none",
          border: `1px solid ${palette.border}`,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          border: `1px solid ${palette.border}`,
          boxShadow: "0 2px 24px -12px rgba(2, 129, 116, 0.18)",
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 999,
          paddingLeft: 18,
          paddingRight: 18,
          transition: "transform 160ms ease, background-color 160ms ease, box-shadow 160ms ease",
          "&:hover": { transform: "translateY(-1px)" },
        },
        containedPrimary: {
          background: `linear-gradient(135deg, ${palette.primary} 0%, ${palette.accent} 100%)`,
          boxShadow: "0 6px 20px -10px rgba(2, 129, 116, 0.6)",
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { fontWeight: 600 },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          fontWeight: 700,
          color: palette.textMuted,
          textTransform: "uppercase",
          letterSpacing: "0.08em",
          fontSize: 11,
          backgroundColor: palette.surfaceAlt,
        },
      },
    },
  },
});
