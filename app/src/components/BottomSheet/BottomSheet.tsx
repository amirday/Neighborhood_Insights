'use client';

import { ReactNode, useState } from 'react';

interface BottomSheetProps {
  children: ReactNode;
  title: string;
  defaultExpanded?: boolean;
}

export function BottomSheet({
  children,
  title,
  defaultExpanded = false,
}: BottomSheetProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  return (
    <div
      className={`
        fixed bottom-0 left-0 right-0 bg-white/95 backdrop-blur-sm
        border-t border-gray-200 shadow-2xl rounded-t-2xl
        transition-transform duration-300 ease-out
        ${isExpanded ? 'translate-y-0' : 'translate-y-[calc(100%-4rem)]'}
      `}
      style={{
        zIndex: 'var(--z-filter-panel)',
        maxHeight: '85vh',
      }}
    >
      {/* Handle bar & Header - Larger touch area for mobile */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex flex-col items-center py-6 px-6 touch-manipulation min-h-[60px]"
      >
        {/* Drag handle - increased size for better touch feedback */}
        <div className="w-16 h-2 bg-gray-300 rounded-full mb-3" />

        {/* Title */}
        <div className="w-full flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
          <svg
            className={`w-5 h-5 text-gray-500 transition-transform ${
              isExpanded ? 'rotate-180' : ''
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 15l7-7 7 7"
            />
          </svg>
        </div>
      </button>

      {/* Content */}
      <div
        className="overflow-y-auto overflow-x-hidden px-6 pb-6"
        style={{ maxHeight: 'calc(85vh - 5rem)' }}
      >
        {children}
      </div>
    </div>
  );
}
