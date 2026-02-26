import { useState, useEffect, useCallback } from 'react'
import { BrowserRouter as Router, Route, Routes, NavLink } from 'react-router-dom';
import { RefreshCw, CheckCircle, AlertCircle } from 'lucide-react'
import { SpeedInsights } from '@vercel/speed-insights/react'
import { Analytics } from '@vercel/analytics/react'
import SystemTestResults from './components/SystemTestResults'
import SystemStatus from './components/SystemStatus'
import Billing from './pages/Billing';

const Home = () => {
  const [health, setHealth] = useState<any>(null)
  const [apiHealth, setApiHealth] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)

  const fetchHealthData = useCallback(async () => {
    const API = import.meta.env.VITE_API_URL || '';
    setIsLoading(true);
    try {
      /**
       * Optimization: Parallel API Calls
       *
       * The health checks for the Node.js server and Python API are independent.
       * By using Promise.all, we can run them in parallel instead of sequentially.
       * This reduces the total time to fetch data, making the UI load faster.
       *
       * Estimated impact: Reduces load time by up to 50% (depending on network latency).
       */
      const results = await Promise.allSettled([
        fetch(`${API}/health`),
        fetch(`${API}/api/v1/health`)
      ]);

      // Handle Node.js server health response
      if (results[0].status === 'fulfilled' && results[0].value.ok) {
        try {
          const healthData = await results[0].value.json();
          setHealth(healthData);
        } catch (e) {
          console.error('Error parsing Node.js health JSON:', e);
          setHealth(null);
        }
      } else {
        console.error('Node.js server error:', results[0].status === 'fulfilled' ? results[0].value.statusText : results[0].reason);
        setHealth(null);
      }

      // Handle Python API health response
      if (results[1].status === 'fulfilled' && results[1].value.ok) {
        try {
          const apiHealthData = await results[1].value.json();
          setApiHealth(apiHealthData);
        } catch (e) {
          console.error('Error parsing Python API health JSON:', e);
          setApiHealth(null);
        }
      } else {
        console.error('Python API error:', results[1].status === 'fulfilled' ? results[1].value.statusText : results[1].reason);
        setApiHealth(null);
      }
    } catch (error) {
      console.error('Error fetching health data:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHealthData();
  }, [fetchHealthData]);

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-4xl font-bold text-center mb-8 text-gray-900">
        🚀 MAIN_FIRE_DOMSIN_WORKSPACE Trading Platform
      </h1>

      <div className="flex justify-end mb-4">
        <button
          onClick={fetchHealthData}
          disabled={isLoading}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          aria-label={isLoading ? 'Refreshing system status' : 'Refresh system status'}
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} aria-hidden="true" />
          <span>{isLoading ? 'Refreshing...' : 'Refresh Status'}</span>
        </button>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-semibold mb-4 text-gray-800">
            Node.js Server Status
          </h2>
          {isLoading ? (
            <div className="space-y-2 animate-pulse" role="status" aria-label="Loading Node.js server status">
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              <div className="h-4 bg-gray-200 rounded w-1/3"></div>
            </div>
          ) : health ? (
            <div className="space-y-2" role="status">
              <div className="flex items-center">
                <CheckCircle className="w-5 h-5 text-green-700 mr-2" aria-hidden="true" />
                <span>Status: {health.status}</span>
              </div>
              <div>Environment: {health.environment}</div>
              <div>Timestamp: {health.timestamp}</div>
            </div>
          ) : (
            <div className="flex items-center" role="alert">
              <AlertCircle className="w-5 h-5 text-red-600 mr-2" aria-hidden="true" />
              <span>Server not responding</span>
            </div>
          )}
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-semibold mb-4 text-gray-800">
            Python API Status
          </h2>
          {isLoading ? (
            <div className="space-y-2 animate-pulse" role="status" aria-label="Loading Python API status">
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              <div className="h-4 bg-gray-200 rounded w-1/3"></div>
            </div>
          ) : apiHealth ? (
            <div className="space-y-2" role="status">
              <div className="flex items-center">
                <CheckCircle className="w-5 h-5 text-green-700 mr-2" aria-hidden="true" />
                <span>Status: {apiHealth.status}</span>
              </div>
              <div>ML Service: {apiHealth.services?.ml_service}</div>
              <div>Data Service: {apiHealth.services?.data_service}</div>
              <div>Timestamp: {apiHealth.timestamp}</div>
            </div>
          ) : (
            <div className="flex items-center" role="alert">
              <AlertCircle className="w-5 h-5 text-red-600 mr-2" aria-hidden="true" />
              <span>API not responding</span>
            </div>
          )}
        </div>
      </div>

      <SystemStatus />
      <SystemTestResults />
    </div>
  )
}

/**
 * The main application component.
 * It fetches and displays the health status of the Node.js server and the Python API.
 * @returns {JSX.Element} The rendered application component.
 */
function App() {
  return (
    <Router>
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded-md focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
      >
        Skip to main content
      </a>
      <div className="min-h-screen bg-gray-100 p-8">
        <nav className="bg-white rounded-lg shadow-md p-4 mb-8">
          <ul className="flex space-x-4">
            <li>
              <NavLink
                to="/"
                end
                className={({ isActive }) =>
                  `px-3 py-2 rounded-md focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-colors ${
                    isActive
                      ? 'text-blue-700 font-bold underline decoration-2 underline-offset-4'
                      : 'text-gray-600 hover:text-blue-700 hover:underline'
                  }`
                }
              >
                Home
              </NavLink>
            </li>
            <li>
              <NavLink
                to="/billing"
                className={({ isActive }) =>
                  `px-3 py-2 rounded-md focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-colors ${
                    isActive
                      ? 'text-blue-700 font-bold underline decoration-2 underline-offset-4'
                      : 'text-gray-600 hover:text-blue-700 hover:underline'
                  }`
                }
              >
                Billing
              </NavLink>
            </li>
          </ul>
        </nav>
        <main id="main-content" tabIndex={-1} className="focus:outline-none">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/billing" element={<Billing />} />
          </Routes>
        </main>
        <Analytics />
        <SpeedInsights />
      </div>
    </Router>
  )
}

export default App
