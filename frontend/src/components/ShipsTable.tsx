import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getFacetedUniqueValues,
  getFacetedMinMaxValues,
  flexRender,
  type ColumnDef,
  type SortingState,
  type ColumnFiltersState,
  type FilterFn,
} from '@tanstack/react-table';
import { useState, useMemo } from 'react';
import { ArrowUpDown, Check, X, ExternalLink } from 'lucide-react';
import { cn } from '../lib/utils';
import type { Ship } from '../lib/api';
import { ColumnFilter } from './ColumnFilter';
import { RangeSlider } from './RangeSlider';

interface ShipsTableProps {
  ships: Ship[];
}

interface BoffParsed {
  rank: string; // 1-4
  type: string; // Tac, Sci, Eng, Uni
  specialization: string; // MW, Int, Tmp, Pil, Cmd or empty
}

// Decode HTML entities (e.g., &amp; -> &)
function decodeHtmlEntities(text: string): string {
  const textarea = document.createElement('textarea');
  textarea.innerHTML = text;
  return textarea.value;
}

function splitCommaSeparated(value?: string): string[] {
  if (!value) return [];
  return decodeHtmlEntities(value)
    .split(',')
    .map((v) => v.trim())
    .filter(Boolean);
}

// Parse Bridge Officer text into structured data
// Example: "Lieutenant Commander Tactical-Intelligence" -> { rank: "3", type: "Tac", specialization: "Int" }
function parseBoffText(text: string): BoffParsed {
  if (!text) return { rank: '', type: '', specialization: '' };

  let remaining = text.trim();

  // Extract rank
  let rank = '';
  if (/Lieutenant Commander/i.test(remaining)) {
    rank = '3';
    remaining = remaining.replace(/Lieutenant Commander/gi, '').trim();
  } else if (/Commander/i.test(remaining)) {
    rank = '4';
    remaining = remaining.replace(/Commander/gi, '').trim();
  } else if (/Lieutenant/i.test(remaining)) {
    rank = '2';
    remaining = remaining.replace(/Lieutenant/gi, '').trim();
  } else if (/Ensign/i.test(remaining)) {
    rank = '1';
    remaining = remaining.replace(/Ensign/gi, '').trim();
  }

  // Extract type and specialization
  let type = '';
  let specialization = '';

  // Check for hyphenated specializations (e.g., "Tactical-Intelligence")
  const typeSpecMatch = remaining.match(/(Tactical|Engineering|Science|Universal)[-\s]*(Intelligence|Temporal Operative|Pilot|Miracle Worker|Command)/i);
  if (typeSpecMatch) {
    const typeRaw = typeSpecMatch[1];
    const specRaw = typeSpecMatch[2];

    // Map type
    if (/Tactical/i.test(typeRaw)) type = 'Tac';
    else if (/Engineering/i.test(typeRaw)) type = 'Eng';
    else if (/Science/i.test(typeRaw)) type = 'Sci';
    else if (/Universal/i.test(typeRaw)) type = 'Uni';

    // Map specialization
    if (/Intelligence/i.test(specRaw)) specialization = 'Int';
    else if (/Temporal Operative/i.test(specRaw)) specialization = 'Tmp';
    else if (/Pilot/i.test(specRaw)) specialization = 'Pil';
    else if (/Miracle Worker/i.test(specRaw)) specialization = 'MW';
    else if (/Command/i.test(specRaw)) specialization = 'Cmd';
  } else {
    // No hyphenated specialization, just extract type
    if (/Tactical/i.test(remaining)) type = 'Tac';
    else if (/Engineering/i.test(remaining)) type = 'Eng';
    else if (/Science/i.test(remaining)) type = 'Sci';
    else if (/Universal/i.test(remaining)) type = 'Uni';
  }

  return { rank, type, specialization };
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

// Custom filter function for numeric range
const rangeFilter: FilterFn<Ship> = (row, columnId, filterValue: [number, number]) => {
  const value = row.getValue(columnId) as number | undefined;
  if (value === null || value === undefined) return false;
  return value >= filterValue[0] && value <= filterValue[1];
};

type ColumnGroup = 'defense' | 'weapons' | 'mobility' | 'consoles' | 'boffs' | 'admiralty' | undefined;

const groupHeaderBg: Record<Exclude<ColumnGroup, undefined>, string> = {
  defense: 'bg-blue-50 dark:bg-blue-950/30',
  weapons: 'bg-purple-50 dark:bg-purple-950/30',
  mobility: 'bg-green-50 dark:bg-green-950/30',
  consoles: 'bg-orange-50 dark:bg-orange-950/30',
  boffs: 'bg-teal-50 dark:bg-teal-950/30',
  admiralty: 'bg-indigo-50 dark:bg-indigo-950/30',
};

export function ShipsTable({ ships }: ShipsTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [globalFilter, setGlobalFilter] = useState('');

  const maxBoffSlots = useMemo(() => {
    const max = ships.reduce((acc, ship) => {
      const parts = splitCommaSeparated(ship.boffs);
      return Math.max(acc, parts.length);
    }, 0);
    return Math.max(1, max);
  }, [ships]);

  const columns = useMemo<ColumnDef<Ship>[]>(
    () => {
      const boffColumns: ColumnDef<Ship>[] = [];

      for (let idx = 0; idx < maxBoffSlots; idx++) {
        const boffIndex = idx;

        // Rank column
        boffColumns.push({
          id: `boff_${boffIndex + 1}_rank`,
          header: ({ column }) => (
            <div className="flex items-center justify-center">
              <ColumnFilter column={column} title="Rank" />
            </div>
          ),
          accessorFn: (row) => {
            const parts = splitCommaSeparated(row.boffs);
            const rawText = parts[boffIndex] ?? '';
            const parsed = parseBoffText(rawText);
            return parsed.rank || '';
          },
          cell: ({ getValue }) => {
            const value = getValue() as string;
            return value ? <span className="text-xs">{value}</span> : <span className="text-gray-400">-</span>;
          },
          filterFn: arrayIncludesFilter,
          meta: { group: 'boffs', boffIndex, subColumn: 'rank' } as any,
        });

        // Type column
        boffColumns.push({
          id: `boff_${boffIndex + 1}_type`,
          header: ({ column }) => (
            <div className="flex items-center justify-center">
              <ColumnFilter column={column} title="Type" />
            </div>
          ),
          accessorFn: (row) => {
            const parts = splitCommaSeparated(row.boffs);
            const rawText = parts[boffIndex] ?? '';
            const parsed = parseBoffText(rawText);
            return parsed.type || '';
          },
          cell: ({ getValue }) => {
            const value = getValue() as string;
            return value ? <span className="text-xs">{value}</span> : <span className="text-gray-400">-</span>;
          },
          filterFn: arrayIncludesFilter,
          meta: { group: 'boffs', boffIndex, subColumn: 'type' } as any,
        });

        // Specialization column
        boffColumns.push({
          id: `boff_${boffIndex + 1}_spec`,
          header: ({ column }) => (
            <div className="flex items-center justify-center">
              <ColumnFilter column={column} title="Specialization" />
            </div>
          ),
          accessorFn: (row) => {
            const parts = splitCommaSeparated(row.boffs);
            const rawText = parts[boffIndex] ?? '';
            const parsed = parseBoffText(rawText);
            return parsed.specialization || '';
          },
          cell: ({ getValue }) => {
            const value = getValue() as string;
            return (
              <div className="flex justify-center">
                {value ? (
                  <span className="text-xs">{value}</span>
                ) : (
                  <span className="text-gray-400">-</span>
                )}
              </div>
            );
          },
          filterFn: arrayIncludesFilter,
          meta: { group: 'boffs', boffIndex, subColumn: 'spec' } as any,
        });
      }

      return [
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
            return types.some((type) => filterValue.includes(type));
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
          meta: { group: 'defense' } as any,
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
          meta: { group: 'defense' } as any,
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
          meta: { group: 'defense' } as any,
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
                  <span className="text-gray-400">-</span>
                )}
              </div>
            );
          },
          filterFn: booleanFilter,
          meta: { group: 'weapons' } as any,
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
          meta: { group: 'weapons' } as any,
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
          meta: { group: 'weapons' } as any,
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
          meta: { group: 'mobility' } as any,
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
          meta: { group: 'mobility' } as any,
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
          meta: { group: 'mobility' } as any,
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
          meta: { group: 'consoles' } as any,
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
          meta: { group: 'consoles' } as any,
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
          meta: { group: 'consoles' } as any,
        },

        // Bridge Officers (split into Rank, Type, Spec for each BOFF slot)
        ...boffColumns,

        // Abilities (keep as single column)
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
              <RangeSlider column={column} title="Admiralty Eng" />
            </div>
          ),
          cell: ({ row }) => {
            const eng = row.getValue('admiraltyeng') as number | undefined;
            return eng || <span className="text-gray-400">-</span>;
          },
          filterFn: rangeFilter,
          meta: { group: 'admiralty' } as any,
        },
        {
          accessorKey: 'admiraltytac',
          header: ({ column }) => (
            <div className="flex items-center gap-2">
              <span>Tac</span>
              <RangeSlider column={column} title="Admiralty Tac" />
            </div>
          ),
          cell: ({ row }) => {
            const tac = row.getValue('admiraltytac') as number | undefined;
            return tac || <span className="text-gray-400">-</span>;
          },
          filterFn: rangeFilter,
          meta: { group: 'admiralty' } as any,
        },
        {
          accessorKey: 'admiraltysci',
          header: ({ column }) => (
            <div className="flex items-center gap-2">
              <span>Sci</span>
              <RangeSlider column={column} title="Admiralty Sci" />
            </div>
          ),
          cell: ({ row }) => {
            const sci = row.getValue('admiraltysci') as number | undefined;
            return sci || <span className="text-gray-400">-</span>;
          },
          filterFn: rangeFilter,
          meta: { group: 'admiralty' } as any,
        },

        // Hangar
        {
          accessorKey: 'has_hangar',
          header: ({ column }) => (
            <div className="flex items-center gap-2">
              <span>Hangar</span>
              <ColumnFilter column={column} title="Hangar" />
            </div>
          ),
          cell: ({ row }) => {
            const hangars = row.original.hangars || 0;

            return (
              <div className="flex justify-center">
                {hangars > 0 ? (
                  <span className="text-green-600 dark:text-green-400" title={`${hangars} hangar bay(s)`}>
                    ✓ ({hangars})
                  </span>
                ) : (
                  <span className="text-gray-400">-</span>
                )}
              </div>
            );
          },
          filterFn: hangarFilter,
          accessorFn: (row) => String(row.hangars || 0),
        },
      ];
    },
    [maxBoffSlots]
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
    getFacetedUniqueValues: getFacetedUniqueValues(),
    getFacetedMinMaxValues: getFacetedMinMaxValues(),
  });

  // Count BOFF sub-columns per BOFF slot (3 per slot)
  const totalBoffColumns = maxBoffSlots * 3;

  return (
    <div className="space-y-4">
      {/* Ship Count */}
      <div className="text-sm text-gray-600 dark:text-gray-400">
        Showing {table.getFilteredRowModel().rows.length} of {ships.length} ships
      </div>

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
              {/* Top group header row */}
              <tr>
                {/* Sticky first column placeholder to keep alignment with Ship Name */}
                <th
                  colSpan={1}
                  className="px-4 py-2 text-center text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider sticky left-0 z-20 bg-gray-50 dark:bg-gray-900 border-r-2 border-gray-300 dark:border-gray-700"
                />

                {/* Ungrouped info columns: Faction, Tier, Type, Cost */}
                <th colSpan={4} className="px-4 py-2" />

                <th
                  colSpan={3}
                  className={cn(
                    'px-4 py-2 text-center text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider border-x-2 border-gray-300 dark:border-gray-700',
                    groupHeaderBg.defense
                  )}
                >
                  Defense
                </th>
                <th
                  colSpan={3}
                  className={cn(
                    'px-4 py-2 text-center text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider border-x-2 border-gray-300 dark:border-gray-700',
                    groupHeaderBg.weapons
                  )}
                >
                  Weapons
                </th>
                <th
                  colSpan={3}
                  className={cn(
                    'px-4 py-2 text-center text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider border-x-2 border-gray-300 dark:border-gray-700',
                    groupHeaderBg.mobility
                  )}
                >
                  Mobility
                </th>
                <th
                  colSpan={3}
                  className={cn(
                    'px-4 py-2 text-center text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider border-x-2 border-gray-300 dark:border-gray-700',
                    groupHeaderBg.consoles
                  )}
                >
                  Consoles
                </th>

                {/* Bridge Officers (all BOFF sub-columns) */}
                <th
                  colSpan={totalBoffColumns}
                  className={cn(
                    'px-4 py-2 text-center text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider border-x-2 border-gray-300 dark:border-gray-700',
                    groupHeaderBg.boffs
                  )}
                >
                  Bridge Officers
                </th>

                {/* Abilities (not grouped) */}
                <th colSpan={1} className="px-4 py-2" />

                <th
                  colSpan={3}
                  className={cn(
                    'px-4 py-2 text-center text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider border-x-2 border-gray-300 dark:border-gray-700',
                    groupHeaderBg.admiralty
                  )}
                >
                  Admiralty
                </th>

                {/* Hangar */}
                <th colSpan={1} className="px-4 py-2" />
              </tr>

              {/* BOFF slot header row */}
              <tr>
                {/* Sticky first column + ungrouped columns */}
                <th colSpan={1} className="px-4 py-1 sticky left-0 z-20 bg-gray-50 dark:bg-gray-900 border-r-2 border-gray-300 dark:border-gray-700" />
                <th colSpan={4} className="px-4 py-1" />

                {/* Defense, Weapons, Mobility, Consoles groups */}
                <th colSpan={3} className={cn('px-4 py-1 border-x-2 border-gray-300 dark:border-gray-700', groupHeaderBg.defense)} />
                <th colSpan={3} className={cn('px-4 py-1 border-x-2 border-gray-300 dark:border-gray-700', groupHeaderBg.weapons)} />
                <th colSpan={3} className={cn('px-4 py-1 border-x-2 border-gray-300 dark:border-gray-700', groupHeaderBg.mobility)} />
                <th colSpan={3} className={cn('px-4 py-1 border-x-2 border-gray-300 dark:border-gray-700', groupHeaderBg.consoles)} />

                {/* BOFF #x headers (each spanning 3 sub-columns) */}
                {Array.from({ length: maxBoffSlots }, (_, i) => (
                  <th
                    key={`boff-slot-${i}`}
                    colSpan={3}
                    className={cn(
                      'px-4 py-1 text-center text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider',
                      groupHeaderBg.boffs,
                      i === 0 && 'border-l-2 border-gray-300 dark:border-gray-700',
                      i === maxBoffSlots - 1 && 'border-r-2 border-gray-300 dark:border-gray-700'
                    )}
                  >
                    BOFF #{i + 1}
                  </th>
                ))}

                {/* Abilities */}
                <th colSpan={1} className="px-4 py-1" />

                {/* Admiralty */}
                <th colSpan={3} className={cn('px-4 py-1 border-x-2 border-gray-300 dark:border-gray-700', groupHeaderBg.admiralty)} />

                {/* Hangar */}
                <th colSpan={1} className="px-4 py-1" />
              </tr>

              {/* Column header row */}
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header, index) => {
                    const meta = (header.column.columnDef as any)?.meta;
                    const group = meta?.group as ColumnGroup;
                    const boffIndex = meta?.boffIndex as number | undefined;
                    const subColumn = meta?.subColumn as string | undefined;

                    const prevMeta = (headerGroup.headers[index - 1]?.column.columnDef as any)?.meta;
                    const prevGroup = prevMeta?.group as ColumnGroup;
                    const prevBoffIndex = prevMeta?.boffIndex as number | undefined;

                    const nextMeta = (headerGroup.headers[index + 1]?.column.columnDef as any)?.meta;
                    const nextGroup = nextMeta?.group as ColumnGroup;
                    const nextBoffIndex = nextMeta?.boffIndex as number | undefined;

                    // Determine if this is first/last of a group
                    const isFirstOfGroup = !!group && group !== prevGroup;
                    const isLastOfGroup = !!group && group !== nextGroup;

                    // For BOFF columns, also check if first/last of a BOFF slot
                    const isFirstOfBoffSlot = group === 'boffs' && boffIndex !== prevBoffIndex && subColumn === 'rank';
                    const isLastOfBoffSlot = group === 'boffs' && boffIndex !== nextBoffIndex && subColumn === 'spec';

                    const groupBg = group ? groupHeaderBg[group] : '';

                    // BOFF columns: minimal width
                    const isBoffColumn = group === 'boffs';

                    return (
                      <th
                        key={header.id}
                        className={cn(
                          'py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap',
                          isBoffColumn ? 'px-1' : 'px-4',
                          index === 0 && 'sticky left-0 z-10 bg-gray-50 dark:bg-gray-900 border-r-2 border-gray-300 dark:border-gray-700',
                          group && groupBg,
                          isFirstOfGroup && 'border-l-2 border-gray-300 dark:border-gray-700',
                          isLastOfGroup && 'border-r-2 border-gray-300 dark:border-gray-700',
                          isFirstOfBoffSlot && 'border-l border-gray-300 dark:border-gray-600',
                          isLastOfBoffSlot && 'border-r border-gray-300 dark:border-gray-600'
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
                    const meta = (cell.column.columnDef as any)?.meta;
                    const group = meta?.group as ColumnGroup;
                    const boffIndex = meta?.boffIndex as number | undefined;
                    const subColumn = meta?.subColumn as string | undefined;

                    const prevMeta = (row.getVisibleCells()[index - 1]?.column.columnDef as any)?.meta;
                    const prevGroup = prevMeta?.group as ColumnGroup;
                    const prevBoffIndex = prevMeta?.boffIndex as number | undefined;

                    const nextMeta = (row.getVisibleCells()[index + 1]?.column.columnDef as any)?.meta;
                    const nextGroup = nextMeta?.group as ColumnGroup;
                    const nextBoffIndex = nextMeta?.boffIndex as number | undefined;

                    const isFirstOfGroup = !!group && group !== prevGroup;
                    const isLastOfGroup = !!group && group !== nextGroup;

                    const isFirstOfBoffSlot = group === 'boffs' && boffIndex !== prevBoffIndex && subColumn === 'rank';
                    const isLastOfBoffSlot = group === 'boffs' && boffIndex !== nextBoffIndex && subColumn === 'spec';

                    const isBoffColumn = group === 'boffs';

                    return (
                      <td
                        key={cell.id}
                        className={cn(
                          'py-3 text-sm text-gray-900 dark:text-gray-100 whitespace-nowrap',
                          isBoffColumn ? 'px-1' : 'px-4',
                          index === 0 && 'sticky left-0 z-10 bg-white dark:bg-gray-950 border-r-2 border-gray-300 dark:border-gray-700',
                          isFirstOfGroup && 'border-l-2 border-gray-300 dark:border-gray-700',
                          isLastOfGroup && 'border-r-2 border-gray-300 dark:border-gray-700',
                          isFirstOfBoffSlot && 'border-l border-gray-300 dark:border-gray-600',
                          isLastOfBoffSlot && 'border-r border-gray-300 dark:border-gray-600'
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
    </div>
  );
}
