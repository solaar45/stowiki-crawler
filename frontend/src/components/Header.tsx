import { Moon, Sun, RefreshCw, Download, Rocket } from 'lucide-react';
import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api } from '../lib/api';
import { downloadBlob } from '../lib/utils';
import { LoadingSpinner } from './LoadingSpinner';
import type { Faction } from '../types/ship';

interface HeaderProps {
  darkMode: boolean;
  onToggleDarkMode: () => void;
  factions: Faction[];
  selectedFaction: string | null;
  onFactionChange: (faction: string | null) => void;
  onRefresh: () => void;
  shipCount: number;
}

export function Header({
  darkMode,
  onToggleDarkMode,
  factions,
  selectedFaction,
  onFactionChange,
  onRefresh,
  shipCount,
}: HeaderProps) {
  const [isScraping, setIsScraping] = useState(false);

  // Scrape mutation
  const scrapeMutation = useMutation({
    mutationFn: async () => {
      if (selectedFaction) {
        return await api.scrapeFaction(selectedFaction);
      }
      return await api.scrapeAllFactions();
    },
    onSuccess: () => {
      onRefresh();
      setIsScraping(false);
    },
    onError: (error) => {
      console.error('Scrape failed:', error);
      setIsScraping(false);
    },
  });

  const handleScrape = () => {
    setIsScraping(true);
    scrapeMutation.mutate();
  };

  const handleDownload = async () => {
    try {
      const blob = await api.downloadShips(selectedFaction || undefined);
      const filename = selectedFaction
        ? `${selectedFaction}_ships.json`
        : 'all_ships.json';
      downloadBlob(blob, filename);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  return (
    <header className="sticky top-0 z-50 border-b border-gray-200 dark:border-gray-800 bg-white/80 dark:bg-gray-950/80 backdrop-blur-sm">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between gap-4">
          {/* Logo and Title */}
          <div className="flex items-center gap-3">
            <Rocket className="h-8 w-8 text-primary-600 dark:text-primary-400" />
            <div>
              <h1 className="text-xl font-bold text-gray-900 dark:text-gray-50">
                STO Wiki Crawler
              </h1>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {shipCount} ships loaded
              </p>
            </div>
          </div>

          {/* Controls */}
          <div className="flex items-center gap-3">
            {/* Faction Filter */}
            <select
              value={selectedFaction || ''}
              onChange={(e) => onFactionChange(e.target.value || null)}
              className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">All Factions</option>
              {factions.map((faction) => (
                <option key={faction.key} value={faction.name}>
                  {faction.name}
                </option>
              ))}
            </select>

            {/* Scrape Button */}
            <button
              onClick={handleScrape}
              disabled={isScraping}
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-400 text-white rounded-lg transition-colors"
            >
              {isScraping ? (
                <>
                  <LoadingSpinner size="sm" className="text-white" />
                  Scraping...
                </>
              ) : (
                <>
                  <RefreshCw className="h-4 w-4" />
                  Scrape
                </>
              )}
            </button>

            {/* Download Button */}
            <button
              onClick={handleDownload}
              className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
            >
              <Download className="h-4 w-4" />
              Download
            </button>

            {/* Dark Mode Toggle */}
            <button
              onClick={onToggleDarkMode}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              aria-label="Toggle dark mode"
            >
              {darkMode ? (
                <Sun className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              ) : (
                <Moon className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              )}
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
