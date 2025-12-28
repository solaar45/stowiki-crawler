import { useState, useMemo, useRef, useEffect } from 'react';
import { Filter, X, Check } from 'lucide-react';
import { Column, Table } from '@tanstack/react-table';
import { cn } from '../lib/utils';
import { createPortal } from 'react-dom';

interface ColumnFilterProps<TData> {
  column: Column<TData, unknown>;
  table: Table<TData>;
  title: string;
}

export function ColumnFilter<TData>({
  column,
  table,
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
      
      let left = rect.left + scrollX;
      
      if (left + 256 > window.innerWidth) {
        left = (rect.right + scrollX) - 256;
      }
      
      if (left < 10) left = 10;

      setPosition({
        top: rect.bottom + scrollY + 4,
        left: left,
      });
    }
  }, [isOpen]);

  // Get unique values by MANUALLY filtering rows, excluding this column's filter
  const uniqueValues = useMemo(() => {
    const currentColumnId = column.id;

    // Always use manual computation so counts reflect the other active column filters.

    // Fallback: manual computation by applying other filters to the core row model
    const allRows = table.getCoreRowModel().rows;
    // Get all filters except the current column
    const otherFilters = table.getState().columnFilters.filter((f) => f.id !== currentColumnId);

    // Apply all OTHER filters (not this column's filter)
    let filteredRows = allRows;

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

    // Apply global filter (fallback simple search)
    const globalFilter = table.getState().globalFilter;
    if (globalFilter && String(globalFilter).trim()) {
      filteredRows = filteredRows.filter((row) => {
        return Object.values(row.original as object).some((value) =>
          String(value).toLowerCase().includes(String(globalFilter).toLowerCase())
        );
      });
    }

    // Now count unique values from the filtered rows (support arrays)
    const valuesMap = new Map<string, number>();
    filteredRows.forEach((row) => {
      const value = row.getValue(currentColumnId as any);

      const addKey = (raw: unknown) => {
        let displayValue = '';
        if (raw === null || raw === undefined) displayValue = 'N/A';
        else if (typeof raw === 'boolean') displayValue = raw ? 'Yes' : 'No';
        else displayValue = String(raw).trim();
        if (displayValue === '') displayValue = 'N/A';
        const currentCount = valuesMap.get(displayValue) || 0;
        valuesMap.set(displayValue, currentCount + 1);
      };

      if (Array.isArray(value)) {
        value.forEach((v) => addKey(v));
      } else {
        addKey(value);
      }
    });

    const values = Array.from(valuesMap.entries()).map(([value, count]) => ({
      value,
      count,
    }));

    // Sort values alphabetically
    return values.sort((a, b) => a.value.localeCompare(b.value));
  }, [column, table, title]);

  // Filter values based on search term
  const filteredValues = useMemo(() => {
    if (!searchTerm) return uniqueValues;
    return uniqueValues.filter((item) =>
      item.value.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [uniqueValues, searchTerm]);

  // Helper to apply a list of filters (array of {id, value}) to a set of rows
  const applyFiltersToRows = (rows: any[], filters: Array<{ id: string; value: any }>) => {
    let result = rows;

    filters.forEach((filter) => {
      const filterColumn = table.getColumn(filter.id);
      if (!filterColumn) return;

      const resolvedFn: any = (filterColumn as any).getFilterFn ? (filterColumn as any).getFilterFn() : undefined;
      let filterFn = resolvedFn;
      if (!filterFn) {
        const maybe = filterColumn.columnDef.filterFn;
        if (typeof maybe === 'function') filterFn = maybe as any;
      }
      if (!filterFn) return;

      result = result.filter((row) => {
        try {
          return filterFn(row, filter.id, filter.value);
        } catch (e) {
          return true;
        }
      });
    });

    return result;
  };

  // Get current filter value
  const filterValue = (column.getFilterValue() as string[]) || [];
  const hasActiveFilter = filterValue.length > 0;

  // Toggle filter value
  const toggleValue = (value: string) => {
    const currentFilter = filterValue;
    
    const newFilter = currentFilter.includes(value)
      ? currentFilter.filter((v) => v !== value)
      : [...currentFilter, value];

    // Before applying, simulate whether this selection would yield any rows.
    const currentColumnId = column.id;
    const coreRows = table.getCoreRowModel().rows;

    // Build prospective filters: all other filters plus this column's prospective value
    const otherFilters = table.getState().columnFilters.filter((f) => f.id !== currentColumnId);
    const prospectiveFilters = otherFilters.map((f) => ({ id: f.id, value: f.value }));

    if (newFilter.length > 0) {
      prospectiveFilters.push({ id: currentColumnId, value: newFilter });
    }

    const resulting = applyFiltersToRows(coreRows, prospectiveFilters);
    if (resulting.length === 0) {
      // Do not apply a filter that would result in zero rows
      return;
    }

    column.setFilterValue(newFilter.length > 0 ? newFilter : undefined);
  };

  // Select all visible values
  const selectAll = () => {
    const allAvailableValues = uniqueValues.filter((item) => item.count > 0).map((item) => item.value);
    column.setFilterValue(allAvailableValues);
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

  return (
    <>
      {/* Filter Button */}
      <button
        ref={buttonRef}
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors relative',
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

                  // Determine if selecting/toggling this value would produce zero results.
                  const currentColumnId = column.id;
                  const coreRows = table.getCoreRowModel().rows;
                  const otherFilters = table.getState().columnFilters.filter((f) => f.id !== currentColumnId);
                  const prospectiveFilters = otherFilters.map((f) => ({ id: f.id, value: f.value }));

                  // Simulate toggled filter values for this column
                  const currentColFilter = table.getState().columnFilters.find((f) => f.id === currentColumnId);
                  const currentVals = (currentColFilter?.value as string[]) || [];
                  const simulated = isChecked ? currentVals.filter((v) => v !== item.value) : [...currentVals, item.value];
                  if (simulated.length > 0) {
                    prospectiveFilters.push({ id: currentColumnId, value: simulated });
                  }

                  const resulting = applyFiltersToRows(coreRows, prospectiveFilters);
                  const isDisabled = resulting.length === 0;

                  return (
                    <label
                      key={item.value}
                      className={cn(
                        'flex items-center gap-2 px-2 py-1.5 rounded transition-colors select-none',
                        isDisabled
                          ? 'opacity-40 cursor-not-allowed'
                          : 'hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer'
                      )}
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
                        onChange={() => !isDisabled && toggleValue(item.value)}
                        disabled={isDisabled}
                        className="sr-only"
                      />
                      <span className="flex-1 text-sm text-gray-700 dark:text-gray-300 truncate" title={item.value}>
                        {item.value}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400 tabular-nums">
                        ({resulting.length})
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
