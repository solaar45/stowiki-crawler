import { useState, useEffect } from 'react';

interface ShipWeapons {
  fore: number;
  aft: number;
  can_equip_dual_cannons: boolean;
}

interface ShipStats {
  max_hull: number | null;
  hull_modifier: number | null;
  shield_modifier: number | null;
  impulse_modifier: number | null;
  turn_rate: number | null;
  inertia_rating: number | null;
}

interface ShipData {
  name: string;
  link: string;
  tier: number | null;
  faction: string | null;
  factionlede: string | null;
  type: string | null;
  released: string | null;
  device_slots: number | null;
  weapons: ShipWeapons | null;
  stats: ShipStats | null;
  bridge_officers: string | null;
  console_slots: string | null;
}

interface FactionSummary {
  faction: string;
  factionlede: string;
  count: number;
}

export function ApiDemo() {
  const [ships, setShips] = useState<ShipData[]>([]);
  const [filteredShips, setFilteredShips] = useState<ShipData[]>([]);
  const [factions, setFactions] = useState<FactionSummary[]>([]);
  const [selectedFaction, setSelectedFaction] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch all ships on mount
  useEffect(() => {
    fetchAllShips();
    fetchFactions();
  }, []);

  // Filter ships when selection changes
  useEffect(() => {
    if (selectedFaction === null) {
      setFilteredShips(ships);
    } else {
      setFilteredShips(ships.filter(ship => ship.factionlede === selectedFaction));
    }
  }, [selectedFaction, ships]);

  const fetchAllShips = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:5000/api/ships?limit=1000');
      const data = await response.json();

      if (data.success) {
        setShips(data.ships || []);
        setFilteredShips(data.ships || []);
      } else {
        setError(data.error || 'Failed to fetch ships');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const fetchFactions = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/factions');
      const data = await response.json();

      if (data.success) {
        setFactions(data.factions || []);
      }
    } catch (err) {
      console.error('Failed to fetch factions:', err);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            🚀 Cargo API · Real-time Data
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            {ships.length} Ships · SQLite Database · Sub-50ms Response
          </p>
        </div>

        {/* Faction Filters */}
        {factions.length > 0 && (
          <div className="mb-6 flex flex-wrap gap-2">
            <button
              onClick={() => setSelectedFaction(null)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                selectedFaction === null
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              All ({ships.length})
            </button>
            {factions.map((faction) => (
              <button
                key={faction.factionlede}
                onClick={() => setSelectedFaction(faction.factionlede)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  selectedFaction === faction.factionlede
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
                }`}
              >
                {faction.factionlede} ({faction.count})
              </button>
            ))}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
            <p className="text-red-800 dark:text-red-300 font-semibold">
              ❌ Error: {error}
            </p>
          </div>
        )}

        {/* Loading Indicator */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-600 border-t-transparent mb-4" />
            <p className="text-gray-600 dark:text-gray-400 text-lg">
              Loading ships from database...
            </p>
          </div>
        )}

        {/* Ships Table */}
        {filteredShips.length > 0 && !loading && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Ship Name
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Faction
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Tier
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Fore
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Aft
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Dual Cannons
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Max Hull
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Turn Rate
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Released
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Link
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {filteredShips.map((ship, index) => (
                    <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                        {ship.name}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {ship.factionlede || ship.faction || '-'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-center text-gray-500 dark:text-gray-400">
                        {ship.tier || '-'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {ship.type || '-'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-center text-gray-500 dark:text-gray-400">
                        {ship.weapons?.fore ?? '-'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-center text-gray-500 dark:text-gray-400">
                        {ship.weapons?.aft ?? '-'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-center">
                        {ship.weapons?.can_equip_dual_cannons ? (
                          <span className="text-green-600 dark:text-green-400 font-semibold">✓</span>
                        ) : (
                          <span className="text-red-600 dark:text-red-400">✗</span>
                        )}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-500 dark:text-gray-400">
                        {ship.stats?.max_hull?.toLocaleString() || '-'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-500 dark:text-gray-400">
                        {ship.stats?.turn_rate || '-'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {ship.released || '-'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-center">
                        {ship.link ? (
                          <a
                            href={ship.link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 dark:text-blue-400 hover:underline"
                          >
                            Wiki →
                          </a>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Raw Data Section (collapsible) */}
            <details className="border-t border-gray-200 dark:border-gray-700">
              <summary className="px-6 py-3 bg-gray-50 dark:bg-gray-700 cursor-pointer text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600">
                📋 Show Raw API Response (JSON)
              </summary>
              <div className="p-6 bg-gray-900 overflow-x-auto">
                <pre className="text-xs text-green-400 font-mono">
                  {JSON.stringify(filteredShips, null, 2)}
                </pre>
              </div>
            </details>
          </div>
        )}

        {/* Info Box */}
        <div className="mt-8 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-300 mb-2">
            ℹ️ Cargo API Info
          </h3>
          <ul className="text-blue-800 dark:text-blue-400 space-y-1 text-sm">
            <li>• Uses <code className="bg-blue-100 dark:bg-blue-900 px-1 rounded">GET /api/ships</code> endpoint</li>
            <li>• Data from <strong>SQLite database</strong> (ships.db)</li>
            <li>• Sub-50ms response time</li>
            <li>• Background sync every 8 hours</li>
            <li>• Faction filtering with real-time counts</li>
          </ul>
        </div>
      </div>
    </div>
  );
}