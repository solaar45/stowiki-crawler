import { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { ShipsTable } from '../components/ShipsTable';
import { MetadataDisplay } from '../components/MetadataDisplay';

export function HomePage() {
  const [selectedFaction, setSelectedFaction] = useState<string | undefined>();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const queryClient = useQueryClient();

  // Load ships
  const {
    data: shipsData,
    isLoading: shipsLoading,
    error: shipsError,
  } = useQuery({
    queryKey: ['ships', selectedFaction],
    queryFn: () => api.getShips(selectedFaction),
  });

  // Load metadata
  const { data: metadata, refetch: refetchMetadata } = useQuery({
    queryKey: ['ships-metadata'],
    queryFn: () => api.getShipsMetadata(),
    refetchInterval: 10000, // Check every 10 seconds
  });

  // Load factions
  const { data: factionsData } = useQuery({
    queryKey: ['factions'],
    queryFn: () => api.getFactions(),
  });

  // Auto-refresh on mount if needed
  useEffect(() => {
    if (metadata?.needs_refresh && !metadata.is_scraping && !isRefreshing) {
      handleAutoRefresh();
    }
  }, [metadata?.needs_refresh]);

  // Handle auto-refresh
  const handleAutoRefresh = async () => {
    setIsRefreshing(true);
    
    try {
      const result = await api.autoRefresh(24);
      
      if (result.refreshing) {
        // Poll for completion
        const pollInterval = setInterval(async () => {
          const newMetadata = await api.getShipsMetadata();
          
          if (!newMetadata.is_scraping) {
            clearInterval(pollInterval);
            setIsRefreshing(false);
            // Refresh ships data
            queryClient.invalidateQueries({ queryKey: ['ships'] });
            refetchMetadata();
          }
        }, 5000); // Check every 5 seconds
      } else {
        setIsRefreshing(false);
      }
    } catch (error) {
      console.error('Auto-refresh failed:', error);
      setIsRefreshing(false);
    }
  };

  // Manual scrape
  const handleManualScrape = async () => {
    setIsRefreshing(true);
    
    try {
      await api.scrapeAllFactions();
      queryClient.invalidateQueries({ queryKey: ['ships'] });
      refetchMetadata();
    } catch (error) {
      console.error('Manual scrape failed:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleDownload = () => {
    api.downloadShips(selectedFaction);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <header className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
          Star Trek Online Ship Database
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          MediaWiki API · Auto-Refresh · Stored Data
        </p>
      </header>

      {/* Metadata Display */}
      <MetadataDisplay metadata={metadata} isRefreshing={isRefreshing} />

      {/* Controls */}
      <div className="mb-6 flex flex-wrap gap-4 items-center justify-between">
        <div className="flex gap-3">
          {/* Faction Filter */}
          <select
            value={selectedFaction || ''}
            onChange={(e) => setSelectedFaction(e.target.value || undefined)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
            disabled={shipsLoading || isRefreshing}
          >
            <option value="">All Factions</option>
            {factionsData?.factions.map((faction) => (
              <option key={faction.key} value={faction.name}>
                {faction.name}
              </option>
            ))}
          </select>

          {/* Download Button */}
          <button
            onClick={handleDownload}
            disabled={!shipsData?.ships?.length}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-lg transition-colors flex items-center gap-2"
          >
            <span>📥</span>
            Download JSON
          </button>
        </div>

        {/* Manual Scrape Button */}
        <button
          onClick={handleManualScrape}
          disabled={isRefreshing || metadata?.is_scraping}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition-colors flex items-center gap-2"
        >
          {isRefreshing || metadata?.is_scraping ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
              Scraping...
            </>
          ) : (
            <>
              <span>🔄</span>
              Manual Refresh
            </>
          )}
        </button>
      </div>

      {/* Loading State */}
      {shipsLoading && (
        <div className="flex flex-col items-center justify-center py-20">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-600 border-t-transparent mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading ships...</p>
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
      {!shipsLoading && shipsData && shipsData.count === 0 && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-8 text-center">
          <div className="text-6xl mb-4">🚀</div>
          <h3 className="text-xl font-semibold text-yellow-800 dark:text-yellow-300 mb-2">
            No Ship Data Available
          </h3>
          <p className="text-yellow-600 dark:text-yellow-400 mb-4">
            {isRefreshing || metadata?.is_scraping
              ? 'First-time setup in progress... This takes ~1-2 minutes.'
              : 'Click "Manual Refresh" to scrape ship data from the wiki.'}
          </p>
          {isRefreshing || metadata?.is_scraping ? (
            <div className="flex items-center justify-center space-x-2">
              <div className="animate-spin rounded-full h-6 w-6 border-2 border-yellow-600 border-t-transparent" />
              <span className="text-yellow-700 dark:text-yellow-300 font-medium">
                Scraping in progress...
              </span>
            </div>
          ) : null}
        </div>
      )}

      {/* Ships Table */}
      {!shipsLoading && shipsData && shipsData.count > 0 && (
        <ShipsTable ships={shipsData.ships} />
      )}
    </div>
  );
}