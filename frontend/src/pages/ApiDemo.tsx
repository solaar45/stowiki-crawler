import { useState } from 'react';

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
  type: string | null;
  released: string | null;
  device_slots: number | null;
  weapons: ShipWeapons | null;
  stats: ShipStats | null;
  bridge_officers: string | null;
  console_slots: string | null;
}

export function ApiDemo() {
  const [ships, setShips] = useState<ShipData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scrapedCount, setScrapedCount] = useState(0);

  const fetchDominionShips = async () => {
    setLoading(true);
    setError(null);
    setShips([]);
    setScrapedCount(0);

    try {
      // Call scrape endpoint (without saving)
      const response = await fetch('http://localhost:5000/scrape/dominion');
      const data = await response.json();

      if (data.success) {
        setShips(data.ships || []);
        setScrapedCount(data.count || 0);
      } else {
        setError(data.error || 'Failed to fetch ships');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            🚀 MediaWiki API Demo
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Live API Test - Dominion Ships ohne Speicherung
          </p>
        </div>

        {/* Fetch Button */}
        <div className="mb-6">
          <button
            onClick={fetchDominionShips}
            disabled={loading}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition-colors flex items-center gap-3 text-lg font-semibold"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent" />
                Scraping Dominion Ships...
              </>
            ) : (
              <>
                <span>🎯</span>
                Fetch Dominion Ships (API)
              </>
            )}
          </button>
        </div>

        {/* Stats */}
        {scrapedCount > 0 && (
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4 mb-6">
            <p className="text-green-800 dark:text-green-300 font-semibold">
              ✅ Successfully fetched {scrapedCount} Dominion ships via MediaWiki API!
            </p>
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
              Fetching ships from MediaWiki API...
            </p>
          </div>
        )}

        {/* Ships Table */}
        {ships.length > 0 && !loading && (
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
                  {ships.map((ship, index) => (
                    <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                        {ship.name}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {ship.faction || '-'}
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
                  {JSON.stringify(ships, null, 2)}
                </pre>
              </div>
            </details>
          </div>
        )}

        {/* Info Box */}
        <div className="mt-8 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-300 mb-2">
            ℹ️ API Demo Info
          </h3>
          <ul className="text-blue-800 dark:text-blue-400 space-y-1 text-sm">
            <li>• Nutzt <code className="bg-blue-100 dark:bg-blue-900 px-1 rounded">GET /scrape/dominion</code> Endpoint</li>
            <li>• Scrapt <strong>live</strong> von stowiki.net via MediaWiki API</li>
            <li>• <strong>Keine Speicherung</strong> - Daten nur im Browser</li>
            <li>• Transformiert automatisch mit ShipTransformer</li>
            <li>• Zeigt strukturierte Felder: Weapons, Stats, etc.</li>
            <li>• ~1 Sekunde für 43 Ships (10x parallele Requests)</li>
          </ul>
        </div>
      </div>
    </div>
  );
}