import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { ShipsTable } from '../components/ShipsTable';

export function HomePage() {
  // Load all ships without filters
  const {
    data: ships,
    isLoading: shipsLoading,
    error: shipsError,
  } = useQuery({
    queryKey: ['ships'],
    queryFn: () => api.getShips({}),
  });

  return (
    <div className="w-[95vw] max-w-[95vw] mx-auto px-4 py-8">
      {/* Header */}
      <header className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
          Star Trek Online Ship Database
        </h1>
      </header>

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
            No ships available in the database.
          </p>
        </div>
      )}

      {/* Ships Table */}
      {!shipsLoading && ships && ships.length > 0 && (
        <ShipsTable ships={ships} />
      )}
    </div>
  );
}