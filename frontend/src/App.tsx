import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { HomePage } from './pages/HomePage';
import { HistoryPage } from './pages/HistoryPage';
import { ApiDemo } from './pages/ApiDemo';
import { ThemeToggle } from './components/ThemeToggle';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
          {/* Navigation */}
          <nav className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm">
            <div className="container mx-auto px-4">
              <div className="flex items-center justify-between h-16">
                <div className="flex items-center gap-8">
                  <Link to="/" className="text-xl font-bold text-gray-900 dark:text-white">
                    🚀 STO Wiki Database
                  </Link>
                  <div className="flex gap-4">
                    <Link
                      to="/"
                      className="text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                    >
                      Ships
                    </Link>
                    <Link
                      to="/history"
                      className="text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                    >
                      History
                    </Link>
                    <Link
                      to="/api-demo"
                      className="text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                    >
                      API Demo
                    </Link>
                  </div>
                </div>
                <ThemeToggle />
              </div>
            </div>
          </nav>

          {/* Routes */}
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/api-demo" element={<ApiDemo />} />
          </Routes>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
