import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { KPICard } from '../../types';

interface KPIGridProps {
  kpis: KPICard[];
}

export const KPIGrid: React.FC<KPIGridProps> = ({ kpis }) => {
  const formatValue = (value: any): string => {
    if (typeof value === 'number') {
      return value.toLocaleString();
    }
    return String(value);
  };

  const getTrendIcon = (trend?: string) => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="w-4 h-4 text-green-600" />;
      case 'down':
        return <TrendingDown className="w-4 h-4 text-red-600" />;
      default:
        return <Minus className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {kpis.map((kpi, index) => (
        <div
          key={index}
          className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg transition-shadow"
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                {kpi.title}
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-2">
                {formatValue(kpi.value)}
                {kpi.unit && (
                  <span className="text-sm font-normal text-gray-600 dark:text-gray-400 ml-1">
                    {kpi.unit}
                  </span>
                )}
              </p>
            </div>
            {kpi.trend && (
              <div className="flex items-center gap-1">
                {getTrendIcon(kpi.trend)}
              </div>
            )}
          </div>

          {kpi.change !== undefined && (
            <div className="mt-4 flex items-center gap-1">
              <span
                className={`text-sm font-medium ${
                  kpi.change > 0
                    ? 'text-green-600'
                    : kpi.change < 0
                    ? 'text-red-600'
                    : 'text-gray-600'
                }`}
              >
                {kpi.change > 0 ? '+' : ''}
                {kpi.change}%
              </span>
              {kpi.change_label && (
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {kpi.change_label}
                </span>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

