import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
  type ColumnFiltersState,
} from '@tanstack/react-table';
import { useState, useMemo } from 'react';
import { ArrowUpDown, ChevronLeft, ChevronRight, Check, X, ExternalLink } from 'lucide-react';
import { cn } from '../lib/utils';
import type { Ship } from '../lib/api';

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
      },
      {
        accessorKey: 'factionlede',
        header: 'Faction',
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
      },
      {
        accessorKey: 'tier',
        header: ({ column }) => (
          <button
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
            className="flex items-center gap-2 font-semibold hover:text-blue-600 dark:hover:text-blue-400"
          >
            TIER
            <ArrowUpDown className="h-4 w-4" />
          </button>
        ),
        cell: ({ row }) => {
          const tier = row.getValue('tier') as number | undefined;
          return tier ? tier : <span className="text-gray-400">N/A</span>;
        },
      },
      {
        accessorKey: 'type',
        header: 'Type',
        cell: ({ row }) => {
          const types = row.getValue('type') as string[];
          if (!types || types.length === 0) return <span className="text-gray-400">N/A</span>;
          return types.join(', ');
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
      },

      // Defense
      {
        accessorKey: 'hull',
        header: ({ column }) => (
          <button
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
            className="flex items-center gap-2 font-semibold hover:text-blue-600 dark:hover:text-blue-400"
          >
            HULL
            <ArrowUpDown className="h-4 w-4" />
          </button>
        ),
        cell: ({ row }) => {
          const hull = row.getValue('hull') as number | undefined;
          return hull ? hull.toLocaleString() : <span className="text-gray-400">-</span>;
        },
      },
      {
        accessorKey: 'hullmod',
        header: 'Hull Mod',
        cell: ({ row }) => {
          const mod = row.getValue('hullmod') as number | undefined;
          return mod ? mod.toFixed(2) : <span className="text-gray-400">-</span>;
        },
      },
      {
        accessorKey: 'shieldmod',
        header: 'Shield Mod',
        cell: ({ row }) => {
          const mod = row.getValue('shieldmod') as number | undefined;
          return mod ? mod.toFixed(2) : <span className="text-gray-400">-</span>;
        },
      },

      // Weapons
      {
        accessorKey: 'can_use_cannons',
        header: 'DHC',
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
      },
      {
        accessorKey: 'fore',
        header: 'Fore',
        cell: ({ row }) => {
          const fore = row.getValue('fore') as number | undefined;
          return fore ? fore : <span className="text-gray-400">-</span>;
        },
      },
      {
        accessorKey: 'aft',
        header: 'Aft',
        cell: ({ row }) => {
          const aft = row.getValue('aft') as number | undefined;
          return aft ? aft : <span className="text-gray-400">-</span>;
        },
      },

      // Mobility
      {
        accessorKey: 'turnrate',
        header: 'Turn',
        cell: ({ row }) => {
          const rate = row.getValue('turnrate') as number | undefined;
          return rate ? rate.toFixed(1) : <span className="text-gray-400">-</span>;
        },
      },
      {
        accessorKey: 'impulse',
        header: 'Imp',
        cell: ({ row }) => {
          const impulse = row.getValue('impulse') as number | undefined;
          return impulse ? impulse.toFixed(2) : <span className="text-gray-400">-</span>;
        },
      },
      {
        accessorKey: 'inertia',
        header: 'Inrt',
        cell: ({ row }) => {
          const inertia = row.getValue('inertia') as number | undefined;
          return inertia ? inertia : <span className="text-gray-400">-</span>;
        },
      },

      // Consoles
      {
        accessorKey: 'consolestac',
        header: 'TAC',
        cell: ({ row }) => {
          const tac = row.getValue('consolestac') as number | undefined;
          return tac || <span className="text-gray-400">-</span>;
        },
      },
      {
        accessorKey: 'consoleseng',
        header: 'ENG',
        cell: ({ row }) => {
          const eng = row.getValue('consoleseng') as number | undefined;
          return eng || <span className="text-gray-400">-</span>;
        },
      },
      {
        accessorKey: 'consolessci',
        header: 'SCI',
        cell: ({ row }) => {
          const sci = row.getValue('consolessci') as number | undefined;
          return sci || <span className="text-gray-400">-</span>;
        },
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
      },

      // Admiralty
      {
        accessorKey: 'admiraltyeng',
        header: 'Eng',
        cell: ({ row }) => {
          const eng = row.getValue('admiraltyeng') as number | undefined;
          return eng || <span className="text-gray-400">-</span>;
        },
      },
      {
        accessorKey: 'admiraltytac',
        header: 'Tac',
        cell: ({ row }) => {
          const tac = row.getValue('admiraltytac') as number | undefined;
          return tac || <span className="text-gray-400">-</span>;
        },
      },
      {
        accessorKey: 'admiraltysci',
        header: 'Sci',
        cell: ({ row }) => {
          const sci = row.getValue('admiraltysci') as number | undefined;
          return sci || <span className="text-gray-400">-</span>;
        },
      },

      {
        accessorKey: 'has_hangar',
        header: 'Hangar',
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
        <input
          type="text"
          value={globalFilter ?? ''}
          onChange={(e) => setGlobalFilter(e.target.value)}
          placeholder="Search ships..."
          className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
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
