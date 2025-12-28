import { useState, useMemo, useRef, useEffect } from 'react';
import { Filter, X } from 'lucide-react';
import { Column, Table } from '@tanstack/react-table';
import { cn } from '../lib/utils';
import { createPortal } from 'react-dom';

interface RangeSliderProps<TData> {
  column: Column<TData, unknown>;
  table: Table<TData>;
  title: string;
}

export function RangeSlider<TData>({
  column,
  table,
  title,
}: RangeSliderProps<TData>) {
  const [isOpen, setIsOpen] = useState(false);
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const buttonRef = useRef<HTMLButtonElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Get min and max values by MANUALLY filtering rows, excluding this column's filter
  const [minValue, maxValue, hasData] = useMemo(() => {
    const currentColumnId = column.id;
    const allRows = table.getCoreRowModel().rows;

    // Get all filters except the current column
    const otherFilters = table.getState().columnFilters.filter((f) => f.id !== currentColumnId);

    // Apply all OTHER filters (not this column's filter)
    let filteredRows = allRows;

    // Robustly resolve filter functions like ColumnFilter does
    otherFilters.forEach((filter) => {
      const filterColumn = table.getColumn(filter.id);
      if (!filterColumn) return;

      const resolvedFn: any = (filterColumn as any).getFilterFn ? (filterColumn as any).getFilterFn() : undefined;
      let filterFn = resolvedFn;
      if (!filterFn) {
        const maybe = filterColumn.columnDef.filterFn;
        if (typeof maybe === 'function') filterFn = maybe as any;
      }
      if (!filterFn) return;

      filteredRows = filteredRows.filter((row) => {
        try {
          return filterFn(row, filter.id, filter.value);
        } catch (e) {
          return true;
        }
      });
    });

    // Apply global filter (simple fallback)
    const globalFilter = table.getState().globalFilter;
    if (globalFilter && String(globalFilter).trim()) {
      filteredRows = filteredRows.filter((row) => {
        return Object.values(row.original as object).some((value) =>
          String(value).toLowerCase().includes(String(globalFilter).toLowerCase())
        );
      });
    }

    // Calculate min/max from filtered rows
    const values: number[] = [];
    filteredRows.forEach((row) => {
      const value = row.getValue(currentColumnId) as number | undefined;
      if (value !== null && value !== undefined && !isNaN(value)) {
        values.push(value);
      }
    });

    if (values.length === 0) {
      return [0, 100, false] as const;
    }

    const min = Math.min(...values);
    const max = Math.max(...values);

    return [min, max, true] as const;
  }, [column, table, table.getState().columnFilters, table.getState().globalFilter]);

  // Get current filter value
  const filterValue = (column.getFilterValue() as [number, number]) || [
    minValue,
    maxValue,
  ];
  const hasActiveFilter =
    filterValue[0] !== minValue || filterValue[1] !== maxValue;

  const [localMin, setLocalMin] = useState(filterValue[0]);
  const [localMax, setLocalMax] = useState(filterValue[1]);

  // Update local state when min/max values change
  useEffect(() => {
    if (isOpen && hasData) {
      const currentFilter = column.getFilterValue() as [number, number] | undefined;
      if (currentFilter) {
        setLocalMin(Math.max(currentFilter[0], minValue));
        setLocalMax(Math.min(currentFilter[1], maxValue));
      } else {
        setLocalMin(minValue);
        setLocalMax(maxValue);
      }
    }
  }, [isOpen, minValue, maxValue, hasData]);

  // Update position when opening
  useEffect(() => {
    if (isOpen && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      const scrollY = window.scrollY;
      const scrollX = window.scrollX;
      
      let left = rect.left + scrollX;
      
      if (left + 288 > window.innerWidth) {
        left = (rect.right + scrollX) - 288;
      }
      
      if (left < 10) left = 10;

      setPosition({
        top: rect.bottom + scrollY + 4,
        left: left,
      });
    }
  }, [isOpen]);

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

  // Handle scroll to close dropdown
  useEffect(() => {
    const handleScroll = (e: Event) => {
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
        onClick={(e) => {
          e.stopPropagation();
          if (hasData) {
            setIsOpen(!isOpen);
          }
        }}
        disabled={!hasData}
        className={cn(
          'p-1 rounded transition-colors relative',
          hasData
            ? 'hover:bg-gray-200 dark:hover:bg-gray-700'
            : 'opacity-40 cursor-not-allowed',
          hasActiveFilter && hasData && 'text-blue-600 dark:text-blue-400'
        )}
        title={hasData ? `Filter ${title}` : `No data available for ${title}`}
      >
        <Filter className="h-3.5 w-3.5" />
        {hasActiveFilter && hasData && (
          <span className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-blue-600 dark:bg-blue-500 text-white text-xs flex items-center justify-center">
            1
          </span>
        )}
      </button>

      {/* Dropdown Portal */}
      {isOpen && hasData && createPortal(
        <div 
          ref={dropdownRef}
          style={{ 
            top: position.top, 
            left: position.left,
            pointerEvents: 'auto',
          }}
          className="fixed w-72 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 z-[9999]"
          onClick={(e) => e.stopPropagation()}
          onMouseDown={(e) => e.stopPropagation()}
        >
          <div className="p-4">
            {/* Title */}
            <div className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex justify-between items-center">
              <span>Filter by {title}</span>
              <button 
                onClick={(e) => {
                  e.stopPropagation();
                  setIsOpen(false);
                }}
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
                  step={Math.max((maxValue - minValue) / 100, 0.01)}
                  value={localMin}
                  onChange={(e) => {
                    const value = Number(e.target.value);
                    setLocalMin(Math.min(value, localMax));
                  }}
                  onMouseDown={(e) => e.stopPropagation()}
                  onTouchStart={(e) => e.stopPropagation()}
                  className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
                  style={{
                    accentColor: '#2563eb',
                  }}
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
                  step={Math.max((maxValue - minValue) / 100, 0.01)}
                  value={localMax}
                  onChange={(e) => {
                    const value = Number(e.target.value);
                    setLocalMax(Math.max(value, localMin));
                  }}
                  onMouseDown={(e) => e.stopPropagation()}
                  onTouchStart={(e) => e.stopPropagation()}
                  className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
                  style={{
                    accentColor: '#2563eb',
                  }}
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
                    const value = e.target.value;
                    if (value === '') {
                      setLocalMin(minValue);
                      return;
                    }
                    const numValue = Number(value);
                    if (!isNaN(numValue)) {
                      setLocalMin(Math.max(minValue, Math.min(numValue, localMax)));
                    }
                  }}
                  onFocus={(e) => e.target.select()}
                  onClick={(e) => e.stopPropagation()}
                  onMouseDown={(e) => e.stopPropagation()}
                  className="w-full px-2 py-1.5 text-sm rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <input
                  type="number"
                  value={localMax}
                  onChange={(e) => {
                    const value = e.target.value;
                    if (value === '') {
                      setLocalMax(maxValue);
                      return;
                    }
                    const numValue = Number(value);
                    if (!isNaN(numValue)) {
                      setLocalMax(Math.min(maxValue, Math.max(numValue, localMin)));
                    }
                  }}
                  onFocus={(e) => e.target.select()}
                  onClick={(e) => e.stopPropagation()}
                  onMouseDown={(e) => e.stopPropagation()}
                  className="w-full px-2 py-1.5 text-sm rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  applyFilter();
                }}
                className="flex-1 px-3 py-1.5 text-sm rounded bg-blue-500 hover:bg-blue-600 text-white transition-colors"
              >
                Apply
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  resetFilter();
                }}
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
