import React, { useEffect, useState } from 'react';
import { Loader2, RefreshCw } from 'lucide-react';
import { getDashboard, refreshDashboard } from '../../services/api';
import type { DashboardData, FileInfo } from '../../types';
import { KPIGrid } from './KPIGrid';
import { ChartGrid } from './ChartGrid';

interface DashboardProps {
  fileInfo: FileInfo | null;
}

export const Dashboard: React.FC<DashboardProps> = ({ fileInfo }) => {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (fileInfo) {
      loadDashboard();
    }
  }, [fileInfo]);

  const loadDashboard = async () => {
    if (!fileInfo) return;

    setLoading(true);
    setError(null);

    try {
      const data = await getDashboard(fileInfo.file_id);
      setDashboard(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load dashboard');
      console.error('Dashboard error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    if (!fileInfo) return;

    setLoading(true);
    setError(null);

    try {
      const data = await refreshDashboard(fileInfo.file_id);
      setDashboard(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to refresh dashboard');
      console.error('Refresh error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!fileInfo) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <p className="text-lg text-gray-600 dark:text-gray-400">
            Upload a file to view dashboard
          </p>
        </div>
      </div>
    );
  }

  if (loading && !dashboard) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4 text-primary-600" />
          <p className="text-lg text-gray-600 dark:text-gray-400">
            Generating dashboard...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center max-w-md">
          <p className="text-lg text-red-600 dark:text-red-400 mb-4">{error}</p>
          <button
            onClick={loadDashboard}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!dashboard) {
    return null;
  }

  return (
    <div className="h-full overflow-y-auto bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              Dashboard
            </h1>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {fileInfo.filename} • {fileInfo.row_count.toLocaleString()} rows
            </p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {/* KPIs */}
        {dashboard.kpis.length > 0 && <KPIGrid kpis={dashboard.kpis} />}

        {/* Charts */}
        {dashboard.charts.length > 0 && <ChartGrid charts={dashboard.charts} />}
      </div>
    </div>
  );
};

