import { useUIStore } from '@/stores/uiStore';

/**
 * Custom hook for showing toast notifications
 *
 * Provides convenient methods for displaying success, error, warning, and info toasts.
 *
 * @example
 * const toast = useToast();
 * toast.success('POIs loaded', 'Successfully loaded 247 locations');
 * toast.error('Failed to load data', 'Please refresh the page');
 */
export function useToast() {
  const addToast = useUIStore((state) => state.addToast);

  return {
    /**
     * Show a success toast
     */
    success: (title: string, description?: string) =>
      addToast({
        type: 'success',
        title,
        description,
        duration: 5000, // 5 seconds
      }),

    /**
     * Show an error toast
     */
    error: (title: string, description?: string) =>
      addToast({
        type: 'error',
        title,
        description,
        duration: 7000, // 7 seconds (longer for errors)
      }),

    /**
     * Show a warning toast
     */
    warning: (title: string, description?: string) =>
      addToast({
        type: 'warning',
        title,
        description,
        duration: 6000, // 6 seconds
      }),

    /**
     * Show an info toast
     */
    info: (title: string, description?: string) =>
      addToast({
        type: 'info',
        title,
        description,
        duration: 5000, // 5 seconds
      }),
  };
}
