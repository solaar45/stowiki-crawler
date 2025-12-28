import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { formatDistanceToNow } from 'date-fns';

interface Change {
  id: number;
  ship_name: string;
  change_type: 'created' | 'updated' | 'deleted';
  changed_fields?: string[];
  old_values?: Record<string, any>;
  new_values?: Record<string, any>;
  timestamp: string;
}

export function HistoryPage() {
  const [selectedShip, setSelectedShip] = useState<string>('');
  const [limit, setLimit] = useState(100);

  // Load change history
  const { data: history, isLoading } = useQuery({
    queryKey: ['history', selectedShip, limit],
    queryFn: async () => {
      const response = await fetch(
        `http://localhost:5000/api/history?limit=${limit}${selectedShip ? `&ship=${selectedShip}` : ''}`
      );
      const data = await response.json();
      return data.changes as Change[];
    },
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  const getChangeIcon = (type: string) => {
    switch (type) {
      case 'created':
        return '✨';
      case 'updated':
        return '🔄';
      case 'deleted':
        return '🗑️';
      default:
        return '📝';
    }
  };

  const getChangeBadgeColor = (type: string) => {
    switch (type) {
      case 'created':
        return 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200';
      case 'updated':
        return 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200';
      case 'deleted':
        return 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200';
      default:
        return 'bg-gray-100 dark:bg-gray-900 text-gray-800 dark:text-gray-200';
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <header className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
          📜 Change History
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Track all changes to ship data over time
        </p>
      </header>

      {/* Filters */}
      <div className="mb-6 flex flex-wrap gap-4 items-center">
        <input
          type="text"
          value={selectedShip}
          onChange={(e) => setSelectedShip(e.target.value)}
          placeholder="Filter by ship name..."
          className="flex-1 min-w-[200px] px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
        />

        <select
          value={limit}
          onChange={(e) => setLimit(parseInt(e.target.value))}
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
        >
          <option value="50">Last 50 changes</option>
          <option value="100">Last 100 changes</option>
          <option value="200">Last 200 changes</option>
          <option value="500">Last 500 changes</option>
        </select>

        {selectedShip && (
          <button
            onClick={() => setSelectedShip('')}
            className="px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-lg transition-colors"
          >
            Clear Filter
          </button>
        )}
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex flex-col items-center justify-center py-20">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-600 border-t-transparent mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading history...</p>
        </div>
      )}

      {/* History Timeline */}
      {!isLoading && history && (
        <div className="space-y-4">
          {history.length === 0 ? (
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-8 text-center">
              <div className="text-6xl mb-4">📭</div>
              <h3 className="text-xl font-semibold text-yellow-800 dark:text-yellow-300 mb-2">
                No Changes Found
              </h3>
              <p className="text-yellow-600 dark:text-yellow-400">
                {selectedShip
                  ? `No changes found for ship "${selectedShip}"`
                  : 'No changes have been recorded yet.'}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {history.map((change) => (
                <div
                  key={change.id}
                  className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-5 border border-gray-200 dark:border-gray-700 hover:border-blue-500 dark:hover:border-blue-400 transition-colors"
                >
                  <div className="flex items-start gap-4">
                    {/* Icon */}
                    <div className="text-3xl flex-shrink-0">
                      {getChangeIcon(change.change_type)}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      {/* Header */}
                      <div className="flex items-center gap-3 mb-2">
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-semibold uppercase ${getChangeBadgeColor(
                            change.change_type
                          )}`}
                        >
                          {change.change_type}
                        </span>

                        <a
                          href={`https://stowiki.net/wiki/${encodeURIComponent(change.ship_name)}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-lg font-bold text-blue-600 dark:text-blue-400 hover:underline"
                        >
                          {change.ship_name}
                        </a>
                      </div>

                      {/* Timestamp */}
                      <div className="text-sm text-gray-500 dark:text-gray-400 mb-3">
                        {formatDistanceToNow(new Date(change.timestamp), { addSuffix: true })}
                        {' • '}
                        {new Date(change.timestamp).toLocaleString()}
                      </div>

                      {/* Changed Fields */}
                      {change.changed_fields && change.changed_fields.length > 0 && (
                        <div className="mb-3">
                          <div className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                            Changed Fields:
                          </div>
                          <div className="flex flex-wrap gap-2">
                            {change.changed_fields.map((field) => (
                              <span
                                key={field}
                                className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded text-xs font-mono"
                              >
                                {field}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Value Changes */}
                      {change.change_type === 'updated' &&
                        change.old_values &&
                        change.new_values && (
                          <div className="space-y-2">
                            {Object.keys(change.new_values).slice(0, 5).map((key) => (
                              <div
                                key={key}
                                className="grid grid-cols-[auto,1fr,auto,1fr] gap-3 items-center text-sm"
                              >
                                <span className="font-mono text-gray-600 dark:text-gray-400 text-xs">
                                  {key}:
                                </span>
                                <span className="text-red-600 dark:text-red-400 line-through truncate">
                                  {JSON.stringify(change.old_values[key])}
                                </span>
                                <span className="text-gray-400">→</span>
                                <span className="text-green-600 dark:text-green-400 font-semibold truncate">
                                  {JSON.stringify(change.new_values[key])}
                                </span>
                              </div>
                            ))}
                            {Object.keys(change.new_values).length > 5 && (
                              <div className="text-xs text-gray-500 dark:text-gray-400 italic">
                                ... and {Object.keys(change.new_values).length - 5} more fields
                              </div>
                            )}
                          </div>
                        )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
