import React, { useState } from 'react';
import { BarChart3, MessageSquare, Upload as UploadIcon } from 'lucide-react';
import { FileUpload } from './components/FileUpload';
import { ChatInterface } from './components/Chat/ChatInterface';
import { Dashboard } from './components/Dashboard/Dashboard';
import type { FileInfo } from './types';

type TabType = 'upload' | 'chat' | 'dashboard';

function App() {
  const [activeTab, setActiveTab] = useState<TabType>('upload');
  const [fileInfo, setFileInfo] = useState<FileInfo | null>(null);

  const handleUploadComplete = (info: FileInfo) => {
    setFileInfo(info);
    setActiveTab('chat');
  };

  const tabs = [
    { id: 'upload' as TabType, label: 'Upload', icon: UploadIcon },
    { id: 'chat' as TabType, label: 'Chat', icon: MessageSquare },
    { id: 'dashboard' as TabType, label: 'Dashboard', icon: BarChart3 },
  ];

  return (
    <div className="flex flex-col h-screen bg-gray-900 text-gray-100">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <BarChart3 className="w-8 h-8 text-primary-500" />
            <div>
              <h1 className="text-xl font-bold text-white">
                Retail Insights Assistant
              </h1>
              <p className="text-sm text-gray-400">
                GenAI-powered analytics with multi-agent workflow
              </p>
            </div>
          </div>

          {fileInfo && (
            <div className="text-right">
              <p className="text-sm font-medium text-gray-300">{fileInfo.filename}</p>
              <p className="text-xs text-gray-500">
                {fileInfo.row_count.toLocaleString()} rows •{' '}
                {fileInfo.column_count} columns
              </p>
            </div>
          )}
        </div>
      </header>

      {/* Tabs */}
      <div className="bg-gray-800 border-b border-gray-700 px-6">
        <nav className="flex gap-1">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            const isDisabled = !fileInfo && (tab.id === 'chat' || tab.id === 'dashboard');

            return (
              <button
                key={tab.id}
                onClick={() => !isDisabled && setActiveTab(tab.id)}
                disabled={isDisabled}
                className={`
                  flex items-center gap-2 px-4 py-3 border-b-2 transition-colors
                  ${
                    isActive
                      ? 'border-primary-500 text-primary-400'
                      : isDisabled
                      ? 'border-transparent text-gray-600 cursor-not-allowed'
                      : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-600'
                  }
                `}
              >
                <Icon className="w-4 h-4" />
                <span className="font-medium">{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Content */}
      <main className="flex-1 overflow-hidden">
        {activeTab === 'upload' && (
          <div className="h-full flex items-center justify-center">
            <FileUpload onUploadComplete={handleUploadComplete} />
          </div>
        )}
        {activeTab === 'chat' && <ChatInterface fileInfo={fileInfo} />}
        {activeTab === 'dashboard' && <Dashboard fileInfo={fileInfo} />}
      </main>
    </div>
  );
}

export default App;

