import { ShipsMetadata } from '../lib/api';

interface MetadataDisplayProps {
  metadata: ShipsMetadata | undefined;
  isRefreshing: boolean;
}

export function MetadataDisplay({ metadata, isRefreshing }: MetadataDisplayProps) {
  if (!metadata) return null;

  const getFreshnessColor = (ageHours: number | null) => {
    if (ageHours === null) return 'bg-gray-500';
    if (ageHours < 12) return 'bg-green-500';
    if (ageHours < 24) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getFreshnessText = (ageHours: number | null) => {
    if (ageHours === null) return '⚠️ No data yet';
    if (ageHours < 12) return '✅ Data is fresh';
    if (ageHours < 24) return '⚠️ Data is aging';
    return '❌ Data needs refresh';
  };

  const formatDateTime = (isoString: string | null) => {
    if (!isoString) return 'Never';
    return new Date(isoString).toLocaleString('de-DE', {
      dateStyle: 'medium',
      timeStyle: 'short',
    });
  };

  return (
    <div className="mb-6 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-700 rounded-lg border border-blue-200 dark:border-gray-600 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-4">
            <div>
              <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                Last Updated:
              </span>
              <span className="ml-2 text-sm text-gray-900 dark:text-white font-medium">
                {formatDateTime(metadata.last_scraped)}
              </span>
            </div>
            
            {metadata.age_hours !== null && (
              <div className="text-sm text-gray-600 dark:text-gray-400">
                ({metadata.age_hours.toFixed(1)}h ago)
              </div>
            )}

            <div className="text-sm">
              <span className="font-semibold text-gray-700 dark:text-gray-300">Ships:</span>
              <span className="ml-2 text-gray-900 dark:text-white font-medium">
                {metadata.ship_count}
              </span>
            </div>
          </div>

          {/* Freshness Bar */}
          <div className="mt-3">
            <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2.5">
              <div
                className={`h-2.5 rounded-full transition-all duration-500 ${
                  getFreshnessColor(metadata.age_hours)
                }`}
                style={{
                  width: metadata.age_hours !== null
                    ? `${Math.min(100, (metadata.age_hours / 24) * 100)}%`
                    : '0%',
                }}
              />
            </div>
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
              {getFreshnessText(metadata.age_hours)}
            </p>
          </div>
        </div>

        {/* Scraping Status */}
        <div className="ml-6">
          {isRefreshing || metadata.is_scraping ? (
            <div className="flex items-center space-x-2 px-4 py-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <div className="animate-spin rounded-full h-5 w-5 border-2 border-blue-600 border-t-transparent" />
              <span className="text-sm font-medium text-blue-700 dark:text-blue-300">
                Updating...
              </span>
            </div>
          ) : metadata.needs_refresh ? (
            <div className="px-4 py-2 bg-orange-100 dark:bg-orange-900 rounded-lg">
              <span className="text-sm font-medium text-orange-700 dark:text-orange-300">
                ⚠️ Refresh Needed
              </span>
            </div>
          ) : (
            <div className="px-4 py-2 bg-green-100 dark:bg-green-900 rounded-lg">
              <span className="text-sm font-medium text-green-700 dark:text-green-300">
                ✅ Up to Date
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}