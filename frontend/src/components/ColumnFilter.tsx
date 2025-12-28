import { useState, useMemo, useRef, useEffect } from 'react';
import { Filter, X, Check } from 'lucide-react';
import { Column } from '@tanstack/react-table';
import { cn } from '../lib/utils';
import { createPortal } from 'react-dom';

interface ColumnFilterProps<TData> {
  column: Column<TData, unknown>;
  title: string;
}

export function ColumnFilter<TData>({
  column,
  title,
}: ColumnFilterProps<TData>) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const buttonRef = useRef<HTMLButtonElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Update position when opening
  useEffect(() => {
    if (isOpen && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      const scrollY = window.scrollY;
      const scrollX = window.scrollX;
      
      // Calculate position (align right edge of dropdown with right edge of button if possible, else left)
      // Default to bottom-left alignment
      let left = rect.left + scrollX;
      
      // Check if dropdown would go off-screen to the right (assuming ~256px width)
      if (left + 256 > window.innerWidth) {
        left = (rect.right + scrollX) - 256; // Align right edge
      }
      
      // Ensure it doesn't go off-screen to the left
      if (left < 10) left = 10;

      setPosition({
        top: rect.bottom + scrollY + 4,
        left: left,
      });
    }
  }, [isOpen]);

  // Get unique values from the column
  const uniqueValues = useMemo(() => {
    const facetedValues = column.getFacetedUniqueValues();
    const valuesMap = new Map<string, number>();

    facetedValues.forEach((count, value) => {
      // Handle special cases
      let displayValue = String(value);
      
      // Handle null/undefined
      if (value === null || value === undefined) {
        displayValue = 'N/A';
      }
      // Handle boolean values (specifically for DHC)
      else if (typeof value === 'boolean' || value === 'true' || value === 'false') {
        displayValue = (value === true || value === 'true') ? 'Yes' : 'No';
      }
      // Handle Hangar values (remove true/false artifacts if any, keep 0, 1, 2)
      else if (title === 'Hangar') {
         if (value === 'true' || value === true || value === 'false' || value === false) {
             return; // Skip boolean artifacts in Hangar
         }
      }

      // Normalize string values to handle case differences (e.g. BATTLECRUISER vs Battlecruiser)
      // But keep the first encountered casing as the display key
      const normalizedKey = displayValue.trim();
      
      const currentCount = valuesMap.get(normalizedKey) || 0;
      valuesMap.set(normalizedKey, currentCount + count);
    });

    const values = Array.from(valuesMap.entries()).map(([value, count]) => ({
      value,
      count,
    }));

    // Sort values alphabetically
    return values.sort((a, b) => a.value.localeCompare(b.value));
  }, [column, title]);

  // Filter values based on search term
  const filteredValues = useMemo(() => {
    if (!searchTerm) return uniqueValues;
    return uniqueValues.filter((item) =>
      item.value.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [uniqueValues, searchTerm]);

  // Get current filter value
  const filterValue = (column.getFilterValue() as string[]) || [];
  const hasActiveFilter = filterValue.length > 0;

  // Toggle filter value
  const toggleValue = (value: string) => {
    const currentFilter = filterValue;
    // Handle Yes/No conversion back to original values if needed, 
    // but the filter function in ShipsTable handles string comparison, so passing "Yes"/"No" is fine 
    // provided the filter function expects it.
    
    // For Type column specifically, we need to handle case-insensitivity in the filter function,
    // so here we just pass the display value.
    
    const newFilter = currentFilter.includes(value)
      ? currentFilter.filter((v) => v !== value)
      : [...currentFilter, value];

    column.setFilterValue(newFilter.length > 0 ? newFilter : undefined);
  };

  // Select all visible values
  const selectAll = () => {
    const allValues = filteredValues.map((item) => item.value);
    // Merge with existing selected values that might be filtered out
    const uniqueNewFilter = Array.from(new Set([...filterValue, ...allValues]));
    column.setFilterValue(uniqueNewFilter);
  };

  // Clear all filters
  const clearAll = () => {
    column.setFilterValue(undefined);
    setSearchTerm('');
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
    const handleScroll = () => {
      if (isOpen) setIsOpen(false);
    };
    
    // Only add scroll listener to window if open
    if (isOpen) {
        window.addEventListener('scroll', handleScroll, true); // true for capture phase to catch all scrolls
    }
    
    return () => {
        window.removeEventListener('scroll', handleScroll, true);
    };
  }, [isOpen]);

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
          <span className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-blue-600 dark:bg-blue-500 text-white text-xs flex items-center justify-center">
            {filterValue.length}
          </span>
        )}
      </button>

      {/* Dropdown Portal */}
      {isOpen && createPortal(
        <div 
          ref={dropdownRef}
          style={{ 
            top: position.top, 
            left: position.left,
            maxHeight: 'calc(100vh - 100px)' 
          }}
          className="fixed w-64 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 z-[9999]"
        >
          {/* Search */}
          <div className="p-2 border-b border-gray-200 dark:border-gray-700">
            <div className="relative">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search..."
                className="w-full px-3 py-1.5 pr-8 text-sm rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                autoFocus
              />
              {searchTerm && (
                <button
                  onClick={() => setSearchTerm('')}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="p-2 flex gap-2 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
            <button
              onClick={selectAll}
              className="flex-1 px-2 py-1 text-xs rounded bg-blue-500 hover:bg-blue-600 text-white transition-colors"
            >
              Select All
            </button>
            <button
              onClick={clearAll}
              className="flex-1 px-2 py-1 text-xs rounded bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 transition-colors"
            >
              Clear
            </button>
          </div>

          {/* Values List */}
          <div className="max-h-64 overflow-y-auto p-1 custom-scrollbar">
            {filteredValues.length === 0 ? (
              <div className="p-4 text-sm text-gray-500 dark:text-gray-400 text-center">
                No values found
              </div>
            ) : (
              <div className="space-y-0.5">
                {filteredValues.map((item) => {
                  const isChecked = filterValue.includes(item.value);
                  return (
                    <label
                      key={item.value}
                      className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer transition-colors select-none"
                    >
                      <div
                        className={cn(
                          'flex-shrink-0 h-4 w-4 rounded border flex items-center justify-center transition-colors',
                          isChecked
                            ? 'bg-blue-600 border-blue-600'
                            : 'bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-600 group-hover:border-gray-400'
                        )}
                      >
                        {isChecked && <Check className="h-3 w-3 text-white" />}
                      </div>
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => toggleValue(item.value)}
                        className="sr-only"
                      />
                      <span className="flex-1 text-sm text-gray-700 dark:text-gray-300 truncate" title={item.value}>
                        {item.value}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400 tabular-nums">
                        ({item.count})
                      </span>
                    </label>
                  );
                })}
              </div>
            )}
          </div>
        </div>,
        document.body
      )}
    </>
  );
}
