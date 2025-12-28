import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getFacetedUniqueValues,
  getFacetedMinMaxValues,
  flexRender,
  type ColumnDef,
  type SortingState,
  type ColumnFiltersState,
  type FilterFn,
} from '@tanstack/react-table';
import { useState, useMemo } from 'react';
import { ArrowUpDown, ChevronLeft, ChevronRight, Check, X, ExternalLink } from 'lucide-react';
import { cn } from '../lib/utils';
import type { Ship } from '../lib/api';
import { ColumnFilter } from './ColumnFilter';
import { RangeSlider } from './RangeSlider';

interface ShipsTableProps {
  ships: Ship[];
}

// Decode HTML entities (e.g., &amp; -> &)
function decodeHtmlEntities(text: string): string {
  const textarea = document.createElement('textarea');
  textarea.innerHTML = text;
  return textarea.value;
}

// Normalize faction names for display
function normalizeFactionName(faction: string): string {
  const mapping: Record<string, string> = {
    'Romulan Republic': 'Romulan',
    'Klingon Empire': 'Klingon',
  };
  return mapping[faction] || faction;
}

// Format cost field: decode entities and replace ; with space
function formatCost(cost: string): string {
  return decodeHtmlEntities(cost).replace(/;/g, ' ');
}

// Custom filter function for array includes
const arrayIncludesFilter: FilterFn<Ship> = (row, columnId, filterValue: string[]) => {
  const value = row.getValue(columnId);
  if (value === null || value === undefined) return filterValue.includes('N/A');
  return filterValue.includes(String(value));
};

// Custom filter function for boolean (DHC)
const booleanFilter: FilterFn<Ship> = (row, columnId, filterValue: string[]) => {
  const value = row.getValue(columnId) as boolean;
  return filterValue.includes(value ? 'Yes' : 'No');
};

// Custom filter function for hangar count
const hangarFilter: FilterFn<Ship> = (row, columnId, filterValue: string[]) => {
  const hangars = row.original.hangars || 0;
  return filterValue.includes(String(hangars));
};

// Custom filter function for admiralty ranges
const admiraltyRangeFilter: FilterFn<Ship> = (row, columnId, filterValue: string[]) => {
  const value = (row.getValue(columnId) as number) || 0;
  
  return filterValue.some(range => {
    if (range === '0-50') return value >= 0 && value <= 50;
    if (range === '51-100') return value > 50 && value <= 100;
    if (range === '101-150') return value > 100 && value <= 150;
    if (range === '151-200') return value > 150 && value <= 200;
    if (range === '201+') return value > 200;
    return false;
  });
};

// Custom filter function for numeric range
const rangeFilter: FilterFn<Ship> = (row, columnId, filterValue: [number, number]) => {
  const value = row.getValue(columnId) as number | undefined;
  if (value === null || value === undefined) return false;
  return value >= filterValue[0] && value <= filterValue[1];
};

export function ShipsTable({ ships }: ShipsTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [globalFilter, setGlobalFilter] = useState('');

  const columns = useMemo<ColumnDef<Ship>[]>(
    () => [
      {
        accessorKey: 'name',
        header: ({ column }) => (
          <button
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
            className="flex items-center gap-2 font-semibold hover:text-blue-600 dark:hover:text-blue-400"
          >
            SHIP NAME
            <ArrowUpDown className="h-4 w-4" />
          </button>
        ),
        cell: ({ row }) => (
          <a
            href={row.original.wiki_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:underline font-medium"
          >
            {row.getValue('name')}
            <ExternalLink className="h-3 w-3" />
          </a>
        ),
        enableColumnFilter: false,
      },
      {
        accessorKey: 'factionlede',
        header: ({ column }) => (
          <div className="flex items-center gap-2">
            <span>Faction</span>
            <ColumnFilter column={column} title="Faction" />
          </div>
        ),
        cell: ({ row }) => {
          const faction = row.getValue('factionlede') as string | undefined;
          if (!faction) return <span className="text-gray-400">N/A</span>;
          const normalizedFaction = normalizeFactionName(faction);
          return (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
              {normalizedFaction}
            </span>
          );
        },
        filterFn: arrayIncludesFilter,
      },
      {
        accessorKey: 'tier',
        header: ({ column }) => (
          <div className="flex items-center gap-2">
            <button
              onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
              className="flex items-center gap-2 font-semibold hover:text-blue-600 dark:hover:text-blue-400"
            >
              TIER
              <ArrowUpDown className="h-4 w-4" />
            </button>
            <ColumnFilter column={column} title="Tier" />
          </div>
        ),
        cell: ({ row }) => {
          const tier = row.getValue('tier') as number | undefined;
          return tier ? tier : <span className="text-gray-400">N/A</span>;
        },
        filterFn: arrayIncludesFilter,
      },
      {
        accessorKey: 'type',
        header: ({ column }) => (
          <div className="flex items-center gap-2">
            <span>Type</span>
            <ColumnFilter column={column} title="Type" />
          </div>
        ),
        cell: ({ row }) => {
          const types = row.getValue('type') as string[];
          if (!types || types.length === 0) return <span className="text-gray-400">N/A</span>;
          return types.join(', ');
        },
        filterFn: (row, columnId, filterValue: string[]) => {
          const types = row.getValue(columnId) as string[];
          if (!types || types.length === 0) return filterValue.includes('N/A');
          return types.some(type => filterValue.includes(type));
        },
      },
      {
        accessorKey: 'cost',
        header: 'Cost',
        cell: ({ row }) => {
          const cost = row.getValue('cost') as string | undefined;
          if (!cost) return <span className="text-gray-400">-</span>;
          return formatCost(cost);
        },
        enableColumnFilter: false,
      },

      // Defense
      {
        accessorKey: 'hull',
        header: ({ column }) => (
          <div className="flex items-center gap-2">
            <button
              onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
              className="flex items-center gap-2 font-semibold hover:text-blue-600 dark:hover:text-blue-400"
            >
              HULL
              <ArrowUpDown className="h-4 w-4" />
            </button>
            <RangeSlider column={column} title="Hull" />
          </div>
        ),
        cell: ({ row }) => {
          const hull = row.getValue('hull') as number | undefined;
          return hull ? hull.toLocaleString() : <span className="text-gray-400">-</span>;
        },
        filterFn: rangeFilter,
      },
      {
        accessorKey: 'hullmod',
        header: ({ column }) => (
          <div className="flex items-center gap-2">
            <span>Hull Mod</span>
            <RangeSlider column={column} title="Hull Mod" />
          </div>
        ),
        cell: ({ row }) => {
          const mod = row.getValue('hullmod') as number | undefined;
          return mod ? mod.toFixed(2) : <span className="text-gray-400">-</span>;
        },
        filterFn: rangeFilter,
      },
      {
        accessorKey: 'shieldmod',
        header: ({ column }) => (
          <div className="flex items-center gap-2">
            <span>Shield Mod</span>
            <RangeSlider column={column} title="Shield Mod" />
          </div>
        ),
        cell: ({ row }) => {
          const mod = row.getValue('shieldmod') as number | undefined;
          return mod ? mod.toFixed(2) : <span className="text-gray-400">-</span>;
        },
        filterFn: rangeFilter,
      },

      // Weapons
      {
        accessorKey: 'can_use_cannons',
        header: ({ column }) => (
          <div className="flex items-center gap-2">
            <span>DHC</span>
            <ColumnFilter column={column} title="DHC" />
          </div>
        ),
        cell: ({ row }) => {
          const canEquip = row.getValue('can_use_cannons') as boolean;
          return (
            <div className="flex justify-center">
              {canEquip ? (
                <Check className="h-5 w-5 text-green-600 dark:text-green-400" />
              ) : (
                <X className="h-5 w-5 text-red-600 dark:text-red-400" />
              )}
            </div>
          );
        },
        filterFn: booleanFilter,
      },
      {
        accessorKey: 'fore',
        header: ({ column }) => (
          <div className="flex items-center gap-2">
            <span>Fore</span>
            <ColumnFilter column={column} title="Fore" />
          </div>
        ),
        cell: ({ row }) => {
          const fore = row.getValue('fore') as number | undefined;
          return fore ? fore : <span className="text-gray-400">-</span>;
        },
        filterFn: arrayIncludesFilter,
      },
      {
        accessorKey: 'aft',
        header: ({ column }) => (
          <div className="flex items-center gap-2">
            <span>Aft</span>
            <ColumnFilter column={column} title="Aft" />
          </div>
        ),
        cell: ({ row }) => {
          const aft = row.getValue('aft') as number | undefined;
          return aft ? aft : <span className="text-gray-400">-</span>;
        },
        filterFn: arrayIncludesFilter,
      },

      // Mobility
      {
        accessorKey: 'turnrate',
        header: ({ column }) => (
          <div className="flex items-center gap-2">
            <span>Turn</span>
            <RangeSlider column={column} title="Turn Rate" />
          </div>
        ),
        cell: ({ row }) => {
          const rate = row.getValue('turnrate') as number | undefined;
          return rate ? rate.toFixed(1) : <span className="text-gray-400">-</span>;
        },
        filterFn: rangeFilter,
      },
      {
        accessorKey: 'impulse',
        header: ({ column }) => (
          <div className="flex items-center gap-2">
            <span>Imp</span>
            <RangeSlider column={column} title="Impulse" />
          </div>
        ),
        cell: ({ row }) => {
          const impulse = row.getValue('impulse') as number | undefined;
          return impulse ? impulse.toFixed(2) : <span className="text-gray-400">-</span>;
        },
        filterFn: rangeFilter,
      },
      {
        accessorKey: 'inertia',
        header: ({ column }) => (
          <div className="flex items-center gap-2">
            <span>Inrt</span>
            <RangeSlider column={column} title="Inertia" />
          </div>
        ),
        cell: ({ row }) => {
          const inertia = row.getValue('inertia') as number | undefined;
          return inertia ? inertia : <span className="text-gray-400">-</span>;
        },
        filterFn: rangeFilter,
      },

      // Consoles
      {
        accessorKey: 'consolestac',
        header: ({ column }) => (
          <div className="flex items-center gap-2">
            <span>TAC</span>
            <ColumnFilter column={column} title="TAC Consoles" />
          </div>
        ),
        cell: ({ row }) => {
          const tac = row.getValue('consolestac') as number | undefined;
          return tac || <span className="text-gray-400">-</span>;
        },
        filterFn: arrayIncludesFilter,
      },
      {
        accessorKey: 'consoleseng',
        header: ({ column }) => (
          <div className="flex items-center gap-2">
            <span>ENG</span>
            <ColumnFilter column={column} title="ENG Consoles" />
          </div>
        ),
        cell: ({ row }) => {
          const eng = row.getValue('consoleseng') as number | undefined;
          return eng || <span className="text-gray-400">-</span>;
        },
        filterFn: arrayIncludesFilter,
      },
      {
        accessorKey: 'consolessci',
        header: ({ column }) => (
          <div className="flex items-center gap-2">
            <span>SCI</span>
            <ColumnFilter column={column} title="SCI Consoles" />
          </div>
        ),
        cell: ({ row }) => {
          const sci = row.getValue('consolessci') as number | undefined;
          return sci || <span className="text-gray-400">-</span>;
        },
        filterFn: arrayIncludesFilter,
      },

      {
        accessorKey: 'boffs',
        header: 'Bridge Officers',
        cell: ({ row }) => {
          const boffs = row.getValue('boffs') as string | undefined;
          if (!boffs) return <span className="text-gray-400">-</span>;
          return (
            <span className="text-xs" title={boffs}>
              {boffs.length > 30 ? boffs.substring(0, 30) + '...' : boffs}
            </span>
          );
        },
        enableColumnFilter: false,
      },
      {
        accessorKey: 'abilities',
        header: 'Abilities',
        cell: ({ row }) => {
          const abilities = row.getValue('abilities') as string | undefined;
          if (!abilities) return <span className="text-gray-400">-</span>;
          return (
            <span className="text-xs" title={abilities}>
              {abilities.length > 30 ? abilities.substring(0, 30) + '...' : abilities}
            </span>
          );
        },
        enableColumnFilter: false,
      },

      // Admiralty
      {
        accessorKey: 'admiraltyeng',
        header: ({ column }) => (
          <div className="flex items-center gap-2">
            <span>Eng</span>
            <ColumnFilter column={column} title="Admiralty Eng" />
          </div>
        ),
        cell: ({ row }) => {
          const eng = row.getValue('admiraltyeng') as number | undefined;
          return eng || <span className="text-gray-400">-</span>;
        },
        filterFn: admiraltyRangeFilter,
        // Add virtual faceted values for ranges
        accessorFn: (row) => {
          const value = row.admiraltyeng || 0;
          if (value <= 50) return '0-50';
          if (value <= 100) return '51-100';
          if (value <= 150) return '101-150';
          if (value <= 200) return '151-200';
          return '201+';
        },
      },
      {
        accessorKey: 'admiraltytac',
        header: ({ column }) => (
          <div className="flex items-center gap-2">
            <span>Tac</span>
            <ColumnFilter column={column} title="Admiralty Tac" />
          </div>
        ),
        cell: ({ row }) => {
          const tac = row.getValue('admiraltytac') as number | undefined;
          return tac || <span className="text-gray-400">-</span>;
        },
        filterFn: admiraltyRangeFilter,
        accessorFn: (row) => {
          const value = row.admiraltytac || 0;
          if (value <= 50) return '0-50';
          if (value <= 100) return '51-100';
          if (value <= 150) return '101-150';
          if (value <= 200) return '151-200';
          return '201+';
        },
      },
      {
        accessorKey: 'admiraltysci',
        header: ({ column }) => (
          <div className="flex items-center gap-2">
            <span>Sci</span>
            <ColumnFilter column={column} title="Admiralty Sci" />
          </div>
        ),
        cell: ({ row }) => {
          const sci = row.getValue('admiraltysci') as number | undefined;
          return sci || <span className="text-gray-400">-</span>;
        },
        filterFn: admiraltyRangeFilter,
        accessorFn: (row) => {
          const value = row.admiraltysci || 0;
          if (value <= 50) return '0-50';
          if (value <= 100) return '51-100';
          if (value <= 150) return '101-150';
          if (value <= 200) return '151-200';
          return '201+';
        },
      },

      {
        accessorKey: 'has_hangar',
        header: ({ column }) => (
          <div className="flex items-center gap-2">
            <span>Hangar</span>
            <ColumnFilter column={column} title="Hangar" />
          </div>
        ),
        cell: ({ row }) => {
          const hasHangar = row.getValue('has_hangar') as boolean;
          const hangars = row.original.hangars || 0;

          return (
            <div className="flex justify-center">
              {hasHangar ? (
                <span className="text-green-600 dark:text-green-400" title={`${hangars} hangar bay(s)`}>
                  ✓ ({hangars})
                </span>
              ) : (
                <X className="h-5 w-5 text-gray-400" />
              )}
            </div>
          );
        },
        filterFn: hangarFilter,
        accessorFn: (row) => String(row.hangars || 0),
      },
    ],
    []
  );

  const table = useReactTable({
    data: ships,
    columns,
    state: {
      sorting,
      columnFilters,
      globalFilter,
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getFacetedUniqueValues: getFacetedUniqueValues(),
    getFacetedMinMaxValues: getFacetedMinMaxValues(),
    initialState: {
      pagination: {
        pageSize: 20,
      },
    },
  });

  return (
    <div className="space-y-4">
      {/* Search */}
      <div className="flex items-center gap-4">
        <div className="relative w-full max-w-md">
          <input
            type="text"
            value={globalFilter ?? ''}
            onChange={(e) => setGlobalFilter(e.target.value)}
            placeholder="Search ships..."
            className="w-full px-4 py-2 pr-10 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {globalFilter && (
            <button
              onClick={() => setGlobalFilter('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
              aria-label="Clear search"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="rounded-lg border border-gray-200 dark:border-gray-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-900">
              {/* Group header row */}
              <tr>
                {/* Sticky first column placeholder to keep alignment with Ship Name */}
                <th
                  colSpan={1}
                  className="px-4 py-2 text-center text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider sticky left-0 z-20 bg-gray-50 dark:bg-gray-900 border-r-2 border-gray-300 dark:border-gray-700"
                />

                {/* Ungrouped info columns: Faction, Tier, Type, Cost */}
                <th colSpan={4} className="px-4 py-2" />

                <th colSpan={3} className="px-4 py-2 text-center text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider border-x-2 border-gray-300 dark:border-gray-700 bg-blue-50 dark:bg-blue-950/30">
                  Defense
                </th>
                <th colSpan={3} className="px-4 py-2 text-center text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider border-x-2 border-gray-300 dark:border-gray-700 bg-purple-50 dark:bg-purple-950/30">
                  Weapons
                </th>
                <th colSpan={3} className="px-4 py-2 text-center text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider border-x-2 border-gray-300 dark:border-gray-700 bg-green-50 dark:bg-green-950/30">
                  Mobility
                </th>
                <th colSpan={3} className="px-4 py-2 text-center text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider border-x-2 border-gray-300 dark:border-gray-700 bg-orange-50 dark:bg-orange-950/30">
                  Consoles
                </th>

                {/* Bridge Officers + Abilities not grouped */}
                <th colSpan={2} className="px-4 py-2" />

                <th colSpan={3} className="px-4 py-2 text-center text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider border-x-2 border-gray-300 dark:border-gray-700 bg-indigo-50 dark:bg-indigo-950/30">
                  Admiralty
                </th>

                {/* Hangar */}
                <th colSpan={1} className="px-4 py-2" />
              </tr>

              {/* Column header row */}
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header, index) => {
                    // Determine if this column is part of a group for border styling
                    const isFirstOfDefense = index === 5; // hull
                    const isLastOfDefense = index === 7; // shieldmod
                    const isFirstOfWeapons = index === 8; // can_use_cannons
                    const isLastOfWeapons = index === 10; // aft
                    const isFirstOfMobility = index === 11; // turnrate
                    const isLastOfMobility = index === 13; // inertia
                    const isFirstOfConsoles = index === 14; // consolestac
                    const isLastOfConsoles = index === 16; // consolessci
                    const isFirstOfAdmiralty = index === 19; // admiraltyeng
                    const isLastOfAdmiralty = index === 21; // admiraltysci

                    return (
                      <th
                        key={header.id}
                        className={cn(
                          'px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap',
                          index === 0 && 'sticky left-0 z-10 bg-gray-50 dark:bg-gray-900 border-r-2 border-gray-300 dark:border-gray-700',
                          // Defense group
                          isFirstOfDefense && 'border-l-2 border-gray-300 dark:border-gray-700 bg-blue-50 dark:bg-blue-950/30',
                          (index > 5 && index < 8) && 'bg-blue-50 dark:bg-blue-950/30',
                          isLastOfDefense && 'border-r-2 border-gray-300 dark:border-gray-700 bg-blue-50 dark:bg-blue-950/30',
                          // Weapons group
                          isFirstOfWeapons && 'border-l-2 border-gray-300 dark:border-gray-700 bg-purple-50 dark:bg-purple-950/30',
                          (index > 8 && index < 11) && 'bg-purple-50 dark:bg-purple-950/30',
                          isLastOfWeapons && 'border-r-2 border-gray-300 dark:border-gray-700 bg-purple-50 dark:bg-purple-950/30',
                          // Mobility group
                          isFirstOfMobility && 'border-l-2 border-gray-300 dark:border-gray-700 bg-green-50 dark:bg-green-950/30',
                          (index > 11 && index < 14) && 'bg-green-50 dark:bg-green-950/30',
                          isLastOfMobility && 'border-r-2 border-gray-300 dark:border-gray-700 bg-green-50 dark:bg-green-950/30',
                          // Consoles group
                          isFirstOfConsoles && 'border-l-2 border-gray-300 dark:border-gray-700 bg-orange-50 dark:bg-orange-950/30',
                          (index > 14 && index < 17) && 'bg-orange-50 dark:bg-orange-950/30',
                          isLastOfConsoles && 'border-r-2 border-gray-300 dark:border-gray-700 bg-orange-50 dark:bg-orange-950/30',
                          // Admiralty group
                          isFirstOfAdmiralty && 'border-l-2 border-gray-300 dark:border-gray-700 bg-indigo-50 dark:bg-indigo-950/30',
                          (index > 19 && index < 22) && 'bg-indigo-50 dark:bg-indigo-950/30',
                          isLastOfAdmiralty && 'border-r-2 border-gray-300 dark:border-gray-700 bg-indigo-50 dark:bg-indigo-950/30',
                        )}
                      >
                        {header.isPlaceholder
                          ? null
                          : flexRender(header.column.columnDef.header, header.getContext())}
                      </th>
                    );
                  })}
                </tr>
              ))}
            </thead>
            <tbody className="bg-white dark:bg-gray-950 divide-y divide-gray-200 dark:divide-gray-800">
              {table.getRowModel().rows.map((row) => (
                <tr
                  key={row.id}
                  className="hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors"
                >
                  {row.getVisibleCells().map((cell, index) => {
                    // Apply same grouping borders to body cells
                    const isFirstOfDefense = index === 5;
                    const isLastOfDefense = index === 7;
                    const isFirstOfWeapons = index === 8;
                    const isLastOfWeapons = index === 10;
                    const isFirstOfMobility = index === 11;
                    const isLastOfMobility = index === 13;
                    const isFirstOfConsoles = index === 14;
                    const isLastOfConsoles = index === 16;
                    const isFirstOfAdmiralty = index === 19;
                    const isLastOfAdmiralty = index === 21;

                    return (
                      <td
                        key={cell.id}
                        className={cn(
                          'px-4 py-3 text-sm text-gray-900 dark:text-gray-100 whitespace-nowrap',
                          index === 0 && 'sticky left-0 z-10 bg-white dark:bg-gray-950 border-r-2 border-gray-300 dark:border-gray-700',
                          // Defense group
                          isFirstOfDefense && 'border-l-2 border-gray-300 dark:border-gray-700',
                          isLastOfDefense && 'border-r-2 border-gray-300 dark:border-gray-700',
                          // Weapons group
                          isFirstOfWeapons && 'border-l-2 border-gray-300 dark:border-gray-700',
                          isLastOfWeapons && 'border-r-2 border-gray-300 dark:border-gray-700',
                          // Mobility group
                          isFirstOfMobility && 'border-l-2 border-gray-300 dark:border-gray-700',
                          isLastOfMobility && 'border-r-2 border-gray-300 dark:border-gray-700',
                          // Consoles group
                          isFirstOfConsoles && 'border-l-2 border-gray-300 dark:border-gray-700',
                          isLastOfConsoles && 'border-r-2 border-gray-300 dark:border-gray-700',
                          // Admiralty group
                          isFirstOfAdmiralty && 'border-l-2 border-gray-300 dark:border-gray-700',
                          isLastOfAdmiralty && 'border-r-2 border-gray-300 dark:border-gray-700',
                        )}
                      >
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-700 dark:text-gray-300">
          Showing {table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1} to{' '}
          {Math.min(
            (table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize,
            table.getFilteredRowModel().rows.length
          )}{' '}
          of {table.getFilteredRowModel().rows.length} ships
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            className={cn(
              'p-2 rounded-lg border border-gray-300 dark:border-gray-700 transition-colors',
              table.getCanPreviousPage()
                ? 'hover:bg-gray-100 dark:hover:bg-gray-800'
                : 'opacity-50 cursor-not-allowed'
            )}
          >
            <ChevronLeft className="h-5 w-5" />
          </button>
          <span className="text-sm text-gray-700 dark:text-gray-300">
            Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
          </span>
          <button
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            className={cn(
              'p-2 rounded-lg border border-gray-300 dark:border-gray-700 transition-colors',
              table.getCanNextPage()
                ? 'hover:bg-gray-100 dark:hover:bg-gray-800'
                : 'opacity-50 cursor-not-allowed'
            )}
          >
            <ChevronRight className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
