// Design tokens for consistent styling - Modern Minimalist aesthetic
export const DESIGN_TOKENS = {
  // Spacing scale (generous whitespace for Modern Minimalist)
  spacing: {
    xs: '0.25rem',    // 4px
    sm: '0.5rem',     // 8px
    md: '1rem',       // 16px
    lg: '1.5rem',     // 24px
    xl: '2rem',       // 32px
    '2xl': '3rem',    // 48px
    '3xl': '4rem',    // 64px
  },

  // Z-index layering system
  zIndex: {
    base: 0,
    dropdown: 10,
    filterPanel: 20,
    header: 30,
    modal: 40,
    popup: 50,
    toast: 60,
  },

  // Layout dimensions
  layout: {
    headerHeight: '5rem',        // 80px - standardized
    filterPanelWidth: '26rem',   // 416px - desktop
    filterPanelMobile: '100%',
    mapOffset: '5rem',           // Match headerHeight
  },

  // Border radius (subtle, clean)
  radius: {
    sm: '0.5rem',   // 8px
    md: '0.75rem',  // 12px
    lg: '1rem',     // 16px
    xl: '1.5rem',   // 24px
    full: '9999px',
  },

  // Shadows (subtle depth for Modern Minimalist)
  shadow: {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1)',
    xl: '0 20px 25px -5px rgb(0 0 0 / 0.1)',
  },
} as const;

// Color palette using Tailwind token names
export const COLORS = {
  primary: {
    50: 'blue-50',
    100: 'blue-100',
    500: 'blue-500',
    600: 'blue-600',
    700: 'blue-700',
  },
  success: {
    50: 'emerald-50',
    500: 'emerald-500',
    600: 'emerald-600',
  },
  danger: {
    50: 'red-50',
    500: 'red-500',
    600: 'red-600',
  },
  warning: {
    50: 'amber-50',
    500: 'amber-500',
    600: 'amber-600',
  },
  transit: {
    500: 'violet-500',
  },
  neutral: {
    50: 'gray-50',
    100: 'gray-100',
    200: 'gray-200',
    300: 'gray-300',
    500: 'gray-500',
    600: 'gray-600',
    700: 'gray-700',
    800: 'gray-800',
    900: 'gray-900',
  },
} as const;

// POI type colors
export const POI_COLORS = {
  schools: 'blue-500',
  kindergartens: 'emerald-500',
  clinics: 'red-500',
  bus_stops: 'amber-500',
  job_center: 'red-600',
} as const;
