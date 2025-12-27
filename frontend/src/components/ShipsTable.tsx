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
import { cn, formatDate, formatNumber } from '../lib/utils';
import type { Ship } from '../types/ship';

interface ShipsTableProps {
  ships: Ship[];
  selectedFaction: string | null;
}

export function ShipsTable({ ships, selectedFaction }: ShipsTableProps) {
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
            className="flex items-center gap-2 font-semibold hover:text-primary-600 dark:hover:text-primary-400"
          >
            Ship Name
            <ArrowUpDown className="h-4 w-4" />
          </button>
        ),
        cell: ({ row }) => (
          <a
            href={row.original.link}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-primary-600 dark:text-primary-400 hover:underline font-medium"
          >
            {row.getValue('name')}
            <ExternalLink className="h-3 w-3" />
          </a>
        ),
      },
      {
        accessorKey: 'faction',
        header: 'Faction',
        cell: ({ row }) => (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
            {row.getValue('faction') || 'N/A'}
          </span>
        ),
      },
      {
        accessorKey: 'tier',
        header: ({ column }) => (
          <button
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
            className="flex items-center gap-2 font-semibold hover:text-primary-600 dark:hover:text-primary-400"
          >
            Tier
            <ArrowUpDown className="h-4 w-4" />
          </button>
        ),
        cell: ({ row }) => formatNumber(row.getValue('tier')),
      },
      {
        accessorKey: 'type',
        header: 'Type',
      },
      {
        accessorKey: 'weapons.fore',
        header: 'Fore',
        cell: ({ row }) => formatNumber(row.original.weapons?.fore || null),
      },
      {
        accessorKey: 'weapons.aft',
        header: 'Aft',
        cell: ({ row }) => formatNumber(row.original.weapons?.aft || null),
      },
      {
        accessorKey: 'weapons.can_equip_dual_cannons',
        header: 'Dual Cannons',
        cell: ({ row }) => {
          const canEquip = row.original.weapons?.can_equip_dual_cannons;
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
        accessorKey: 'stats.max_hull',
        header: ({ column }) => (
          <button
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
            className="flex items-center gap-2 font-semibold hover:text-primary-600 dark:hover:text-primary-400"
          >
            Max Hull
            <ArrowUpDown className="h-4 w-4" />
          </button>
        ),
        cell: ({ row }) => formatNumber(row.original.stats?.max_hull || null),
      },
      {
        accessorKey: 'stats.turn_rate',
        header: 'Turn Rate',
        cell: ({ row }) => {
          const rate = row.original.stats?.turn_rate;
          return rate ? rate.toFixed(1) : 'N/A';
        },
      },
      {
        accessorKey: 'released',
        header: ({ column }) => (
          <button
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
            className="flex items-center gap-2 font-semibold hover:text-primary-600 dark:hover:text-primary-400"
          >
            Released
            <ArrowUpDown className="h-4 w-4" />
          </button>
        ),
        cell: ({ row }) => formatDate(row.getValue('released')),
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
          className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
      </div>

      {/* Table */}
      <div className="rounded-lg border border-gray-200 dark:border-gray-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-900">
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <th
                      key={header.id}
                      className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
                    >
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody className="bg-white dark:bg-gray-950 divide-y divide-gray-200 dark:divide-gray-800">
              {table.getRowModel().rows.map((row) => (
                <tr
                  key={row.id}
                  className="hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors"
                >
                  {row.getVisibleCells().map((cell) => (
                    <td
                      key={cell.id}
                      className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100"
                    >
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </td>
                  ))}
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
