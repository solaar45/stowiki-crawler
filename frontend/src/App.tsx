import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from './lib/api';
import { Header } from './components/Header';
import { ShipsTable } from './components/ShipsTable';
import { LoadingSpinner } from './components/LoadingSpinner';
import { ErrorMessage } from './components/ErrorMessage';
import type { Ship } from './types/ship';

function App() {
  const [selectedFaction, setSelectedFaction] = useState<string | null>(null);
  const [darkMode, setDarkMode] = useState(true);

  // Toggle dark mode
  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    document.documentElement.classList.toggle('dark');
  };

  // Fetch factions
  const { data: factionsData } = useQuery({
    queryKey: ['factions'],
    queryFn: () => api.getFactions(),
  });

  // Fetch ships
  const {
    data: shipsData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['ships', selectedFaction],
    queryFn: () => api.getShips(selectedFaction || undefined),
  });

  const ships: Ship[] = shipsData?.ships || [];

  return (
    <div className={darkMode ? 'dark' : ''}>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
        <Header
          darkMode={darkMode}
          onToggleDarkMode={toggleDarkMode}
          factions={factionsData?.factions || []}
          selectedFaction={selectedFaction}
          onFactionChange={setSelectedFaction}
          onRefresh={refetch}
          shipCount={ships.length}
        />

        <main className="container mx-auto px-4 py-8">
          {isLoading && (
            <div className="flex items-center justify-center h-64">
              <LoadingSpinner size="lg" />
            </div>
          )}

          {error && (
            <ErrorMessage
              message="Failed to load ships data"
              error={error}
              onRetry={refetch}
            />
          )}

          {!isLoading && !error && (
            <ShipsTable
              ships={ships}
              selectedFaction={selectedFaction}
            />
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
