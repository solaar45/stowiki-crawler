import { useState, useMemo, useRef, useEffect } from 'react';
import { Filter, X, Check } from 'lucide-react';
import { Column } from '@tanstack/react-table';
import { cn } from '../lib/utils';

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
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Get unique values from the column
  const uniqueValues = useMemo(() => {
    const facetedValues = column.getFacetedUniqueValues();
    const values: Array<{ value: string; count: number }> = [];

    facetedValues.forEach((count, value) => {
      // Convert value to string, handle null/undefined
      const strValue = value === null || value === undefined ? 'N/A' : String(value);
      values.push({ value: strValue, count });
    });

    // Sort values alphabetically
    return values.sort((a, b) => a.value.localeCompare(b.value));
  }, [column]);

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
    const newFilter = currentFilter.includes(value)
      ? currentFilter.filter((v) => v !== value)
      : [...currentFilter, value];

    column.setFilterValue(newFilter.length > 0 ? newFilter : undefined);
  };

  // Select all visible values
  const selectAll = () => {
    const allValues = filteredValues.map((item) => item.value);
    column.setFilterValue(allValues);
  };

  // Clear all filters
  const clearAll = () => {
    column.setFilterValue(undefined);
    setSearchTerm('');
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
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

  return (
    <div className="relative inline-block" ref={dropdownRef}>
      {/* Filter Button */}
      <button
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

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute left-0 mt-2 w-64 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50">
          {/* Search */}
          <div className="p-2 border-b border-gray-200 dark:border-gray-700">
            <div className="relative">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search..."
                className="w-full px-3 py-1.5 pr-8 text-sm rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
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
          <div className="p-2 flex gap-2 border-b border-gray-200 dark:border-gray-700">
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
          <div className="max-h-64 overflow-y-auto">
            {filteredValues.length === 0 ? (
              <div className="p-4 text-sm text-gray-500 dark:text-gray-400 text-center">
                No values found
              </div>
            ) : (
              <div className="p-1">
                {filteredValues.map((item) => {
                  const isChecked = filterValue.includes(item.value);
                  return (
                    <label
                      key={item.value}
                      className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer transition-colors"
                    >
                      <div
                        className={cn(
                          'h-4 w-4 rounded border flex items-center justify-center transition-colors',
                          isChecked
                            ? 'bg-blue-600 border-blue-600'
                            : 'bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-600'
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
                      <span className="flex-1 text-sm text-gray-700 dark:text-gray-300">
                        {item.value}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        ({item.count})
                      </span>
                    </label>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
