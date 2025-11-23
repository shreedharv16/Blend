import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Code } from 'lucide-react';
import type { QueryData } from '../../types';

interface DataTableProps {
  data: QueryData;
}

export const DataTable: React.FC<DataTableProps> = ({ data }) => {
  const [showSql, setShowSql] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  if (!data.results || data.results.length === 0) {
    return null;
  }

  const columns = Object.keys(data.results[0]);
  const displayedRows = data.results.slice(0, 20);

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-50 dark:bg-gray-750 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
          >
            {collapsed ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronUp className="w-4 h-4" />
            )}
          </button>
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {data.count} rows
          </span>
        </div>

        {data.sql && (
          <button
            onClick={() => setShowSql(!showSql)}
            className="flex items-center gap-1 text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300"
          >
            <Code className="w-4 h-4" />
            {showSql ? 'Hide' : 'Show'} SQL
          </button>
        )}
      </div>

      {/* SQL */}
      {showSql && data.sql && (
        <div className="px-4 py-3 bg-gray-900 border-b border-gray-700">
          <pre className="text-xs text-gray-300 overflow-x-auto">
            <code>{data.sql}</code>
          </pre>
        </div>
      )}

      {/* Table */}
      {!collapsed && (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-750">
              <tr>
                {columns.map((col) => (
                  <th
                    key={col}
                    className="px-4 py-2 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wider"
                  >
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {displayedRows.map((row, rowIndex) => (
                <tr key={rowIndex}>
                  {columns.map((col) => (
                    <td
                      key={col}
                      className="px-4 py-2 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100"
                    >
                      {row[col] !== null && row[col] !== undefined
                        ? String(row[col])
                        : '-'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>

          {data.count > 20 && (
            <div className="px-4 py-2 bg-gray-50 dark:bg-gray-750 text-center text-sm text-gray-600 dark:text-gray-400">
              Showing first 20 of {data.count} rows
            </div>
          )}
        </div>
      )}
    </div>
  );
};

