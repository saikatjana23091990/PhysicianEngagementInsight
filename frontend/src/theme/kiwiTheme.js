import { createTheme } from "@mui/material/styles";

// Palette based on the uploaded image: DC8665, 138086, 534666, CD7672, EEB462
export const palette = {
  primary: "#534666",
  primaryDark: "#352B44",
  accent: "#138086",
  light: "#DC8665",
  cream: "#EEB462",
  bg: "#FBF9F6",
  surface: "#FFFFFF",
  surfaceAlt: "#F5ECE8",
  text: "#2B2338",
  textMuted: "#6F6382",
  border: "#EFE6E2",
  danger: "#CD7672",
  warning: "#EEB462",
};

export const chartPalette = [
  "#534666",
  "#138086",
  "#DC8665",
  "#CD7672",
  "#EEB462",
  "#7C6C94",
  "#1CA0A7",
  "#F4AB94",
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
          boxShadow: "0 2px 24px -12px rgba(83, 70, 102, 0.18)",
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
          boxShadow: "0 6px 20px -10px rgba(83, 70, 102, 0.6)",
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