import { useState, useMemo, useRef, useEffect } from 'react';
import { Filter, X } from 'lucide-react';
import { Column } from '@tanstack/react-table';
import { cn } from '../lib/utils';
import { createPortal } from 'react-dom';

interface RangeSliderProps<TData> {
  column: Column<TData, unknown>;
  title: string;
}

export function RangeSlider<TData>({
  column,
  title,
}: RangeSliderProps<TData>) {
  const [isOpen, setIsOpen] = useState(false);
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const buttonRef = useRef<HTMLButtonElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Update position when opening
  useEffect(() => {
    if (isOpen && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      const scrollY = window.scrollY;
      const scrollX = window.scrollX;
      
      // Calculate position
      let left = rect.left + scrollX;
      
      // Check if dropdown would go off-screen to the right (assuming ~288px width for w-72)
      if (left + 288 > window.innerWidth) {
        left = (rect.right + scrollX) - 288;
      }
      
      // Ensure it doesn't go off-screen to the left
      if (left < 10) left = 10;

      setPosition({
        top: rect.bottom + scrollY + 4,
        left: left,
      });
    }
  }, [isOpen]);

  // Get min and max values from the column
  const [minValue, maxValue] = useMemo(() => {
    const facetedValues = column.getFacetedMinMaxValues();
    if (facetedValues) {
      return [facetedValues[0] ?? 0, facetedValues[1] ?? 100];
    }
    return [0, 100];
  }, [column]);

  // Get current filter value
  const filterValue = (column.getFilterValue() as [number, number]) || [
    minValue,
    maxValue,
  ];
  const hasActiveFilter =
    filterValue[0] !== minValue || filterValue[1] !== maxValue;

  const [localMin, setLocalMin] = useState(filterValue[0]);
  const [localMax, setLocalMax] = useState(filterValue[1]);

  // Update local state when filter changes
  useEffect(() => {
    setLocalMin(filterValue[0]);
    setLocalMax(filterValue[1]);
  }, [filterValue]);

  // Apply filter
  const applyFilter = () => {
    if (localMin === minValue && localMax === maxValue) {
      column.setFilterValue(undefined);
    } else {
      column.setFilterValue([localMin, localMax]);
    }
    setIsOpen(false);
  };

  // Reset filter
  const resetFilter = () => {
    setLocalMin(minValue);
    setLocalMax(maxValue);
    column.setFilterValue(undefined);
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current && 
        !dropdownRef.current.contains(event.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  // Handle scroll to close dropdown - only for scrolling OUTSIDE the dropdown
  useEffect(() => {
    const handleScroll = (e: Event) => {
      // Only close if scroll happened outside the dropdown
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    
    if (isOpen) {
      window.addEventListener('scroll', handleScroll, true);
    }
    
    return () => {
      window.removeEventListener('scroll', handleScroll, true);
    };
  }, [isOpen]);

  // Format number for display
  const formatNumber = (num: number) => {
    if (num >= 1000) {
      return num.toLocaleString();
    }
    return num.toFixed(2);
  };

  return (
    <>
      {/* Filter Button */}
      <button
        ref={buttonRef}
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors',
          hasActiveFilter && 'text-blue-600 dark:text-blue-400'
        )}
        title={`Filter ${title}`}
      >
        <Filter className="h-3.5 w-3.5" />
        {hasActiveFilter && (
          <span className="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-blue-600 dark:bg-blue-500" />
        )}
      </button>

      {/* Dropdown Portal */}
      {isOpen && createPortal(
        <div 
          ref={dropdownRef}
          style={{ 
            top: position.top, 
            left: position.left, 
          }}
          className="fixed w-72 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 z-[9999]"
        >
          <div className="p-4">
            {/* Title */}
            <div className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex justify-between items-center">
              <span>Filter by {title}</span>
              <button 
                onClick={() => setIsOpen(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Range Display */}
            <div className="flex items-center justify-between mb-4 text-sm text-gray-600 dark:text-gray-400">
              <span>Min: {formatNumber(minValue)}</span>
              <span>Max: {formatNumber(maxValue)}</span>
            </div>

            {/* Sliders */}
            <div className="space-y-4 mb-4">
              {/* Min Slider */}
              <div>
                <label className="text-xs text-gray-600 dark:text-gray-400 mb-1 block">
                  From: {formatNumber(localMin)}
                </label>
                <input
                  type="range"
                  min={minValue}
                  max={maxValue}
                  step={(maxValue - minValue) / 100}
                  value={localMin}
                  onChange={(e) => {
                    const value = Number(e.target.value);
                    setLocalMin(Math.min(value, localMax));
                  }}
                  className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
              </div>

              {/* Max Slider */}
              <div>
                <label className="text-xs text-gray-600 dark:text-gray-400 mb-1 block">
                  To: {formatNumber(localMax)}
                </label>
                <input
                  type="range"
                  min={minValue}
                  max={maxValue}
                  step={(maxValue - minValue) / 100}
                  value={localMax}
                  onChange={(e) => {
                    const value = Number(e.target.value);
                    setLocalMax(Math.max(value, localMin));
                  }}
                  className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
              </div>
            </div>

            {/* Input Fields */}
            <div className="grid grid-cols-2 gap-2 mb-4">
              <div>
                <input
                  type="number"
                  value={localMin}
                  onChange={(e) => {
                    const value = Number(e.target.value);
                    if (!isNaN(value)) {
                      setLocalMin(Math.max(minValue, Math.min(value, localMax)));
                    }
                  }}
                  className="w-full px-2 py-1.5 text-sm rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <input
                  type="number"
                  value={localMax}
                  onChange={(e) => {
                    const value = Number(e.target.value);
                    if (!isNaN(value)) {
                      setLocalMax(Math.min(maxValue, Math.max(value, localMin)));
                    }
                  }}
                  className="w-full px-2 py-1.5 text-sm rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2">
              <button
                onClick={applyFilter}
                className="flex-1 px-3 py-1.5 text-sm rounded bg-blue-500 hover:bg-blue-600 text-white transition-colors"
              >
                Apply
              </button>
              <button
                onClick={resetFilter}
                className="px-3 py-1.5 text-sm rounded bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 transition-colors"
              >
                Reset
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </>
  );
}
