import { create } from 'zustand';

export interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  description?: string;
  duration?: number;
}

interface UIStore {
  // Mobile bottom sheet state
  bottomSheetOpen: boolean;
  bottomSheetTab: 'filters' | 'routing' | 'analytics';

  // Toast notifications
  toasts: Toast[];

  // Actions
  setBottomSheetOpen: (open: boolean) => void;
  setBottomSheetTab: (tab: 'filters' | 'routing' | 'analytics') => void;
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
}

export const useUIStore = create<UIStore>((set) => ({
  // Initial state
  bottomSheetOpen: false,
  bottomSheetTab: 'filters',
  toasts: [],

  // Actions
  setBottomSheetOpen: (open) => set({ bottomSheetOpen: open }),

  setBottomSheetTab: (tab) => set({ bottomSheetTab: tab }),

  addToast: (toast) =>
    set((state) => ({
      toasts: [
        ...state.toasts,
        {
          ...toast,
          id: crypto.randomUUID(),
        },
      ],
    })),

  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    })),
}));
