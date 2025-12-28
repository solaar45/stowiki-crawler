import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { ShipsTable } from '../components/ShipsTable';

export function HomePage() {
  const [selectedFaction, setSelectedFaction] = useState<string | undefined>();
  const [selectedTier, setSelectedTier] = useState<number | undefined>();

  // Load ships with filters
  const {
    data: ships,
    isLoading: shipsLoading,
    error: shipsError,
  } = useQuery({
    queryKey: ['ships', selectedFaction, selectedTier],
    queryFn: () => api.getShips({
      faction: selectedFaction,
      tier: selectedTier,
      // No limit - load all ships
    }),
  });

  // Load factions summary
  const { data: factions } = useQuery({
    queryKey: ['factions'],
    queryFn: () => api.getFactions(),
  });

  // Calculate total count from factions
  const totalShips = factions?.reduce((sum, f) => sum + f.count, 0) || 0;
  
  // Get current ship count (from loaded ships or total)
  const currentCount = ships?.length || 0;

  return (
    <div className="w-[95vw] max-w-[95vw] mx-auto px-4 py-8">
      {/* Header */}
      <header className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
          Star Trek Online Ship Database
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          {totalShips} Ships
        </p>
      </header>

      {/* Faction Stats Cards */}
      {factions && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          {factions.map((faction) => (
            <div
              key={faction.key}
              className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 border-2 border-transparent hover:border-blue-500 transition-colors cursor-pointer"
              onClick={() => setSelectedFaction(faction.key === selectedFaction ? undefined : faction.key)}
            >
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                {faction.name}
              </div>
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                {faction.count}
              </div>
              {faction.key === selectedFaction && (
                <div className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                  ✓ Selected
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Controls */}
      <div className="mb-6 flex flex-wrap gap-4 items-center justify-between">
        <div className="flex gap-3">
          {/* Faction Filter */}
          <select
            value={selectedFaction || ''}
            onChange={(e) => setSelectedFaction(e.target.value || undefined)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
            disabled={shipsLoading}
          >
            <option value="">All Factions</option>
            {factions?.map((faction) => (
              <option key={faction.key} value={faction.key}>
                {faction.name} ({faction.count})
              </option>
            ))}
          </select>

          {/* Tier Filter */}
          <select
            value={selectedTier || ''}
            onChange={(e) => setSelectedTier(e.target.value ? parseInt(e.target.value) : undefined)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
            disabled={shipsLoading}
          >
            <option value="">All Tiers</option>
            <option value="6">Tier 6</option>
            <option value="5">Tier 5</option>
            <option value="4">Tier 4</option>
            <option value="3">Tier 3</option>
            <option value="2">Tier 2</option>
            <option value="1">Tier 1</option>
          </select>

          {/* Clear Filters */}
          {(selectedFaction || selectedTier) && (
            <button
              onClick={() => {
                setSelectedFaction(undefined);
                setSelectedTier(undefined);
              }}
              className="px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-lg transition-colors"
            >
              Clear Filters
            </button>
          )}
        </div>
      </div>

      {/* Loading State */}
      {shipsLoading && (
        <div className="flex flex-col items-center justify-center py-20">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-600 border-t-transparent mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading ships from Cargo database...</p>
        </div>
      )}

      {/* Error State */}
      {shipsError && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 mb-6">
          <h3 className="text-red-800 dark:text-red-300 font-semibold mb-2">
            ⚠️ Error Loading Ships
          </h3>
          <p className="text-red-600 dark:text-red-400">
            {shipsError instanceof Error ? shipsError.message : 'Unknown error'}
          </p>
        </div>
      )}

      {/* Empty State */}
      {!shipsLoading && ships && ships.length === 0 && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-8 text-center">
          <div className="text-6xl mb-4">🚀</div>
          <h3 className="text-xl font-semibold text-yellow-800 dark:text-yellow-300 mb-2">
            No Ships Found
          </h3>
          <p className="text-yellow-600 dark:text-yellow-400 mb-4">
            Try adjusting your filters or select a different faction.
          </p>
        </div>
      )}

      {/* Ships Table */}
      {!shipsLoading && ships && ships.length > 0 && (
        <>
          <div className="mb-4 text-gray-600 dark:text-gray-400">
            Showing {currentCount} ships
            {selectedFaction && ` from ${factions?.find(f => f.key === selectedFaction)?.name}`}
            {selectedTier && ` (Tier ${selectedTier})`}
          </div>
          <ShipsTable ships={ships} />
        </>
      )}
    </div>
  );
}