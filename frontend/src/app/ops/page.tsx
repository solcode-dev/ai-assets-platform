'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  Activity, 
  Cpu, 
  Database, 
  HardDrive, 
  ShieldCheck, 
  AlertCircle,
  RefreshCcw,
  ExternalLink
} from 'lucide-react';

interface QuotaInfo {
  metric: string;
  limit: number;
  usage: number;
  unit: string;
}

interface SystemQuota {
  project_id: string;
  quotas: QuotaInfo[];
}

const fetchQuota = async (): Promise<SystemQuota> => {
  const res = await fetch('/api/system/quota');
  if (!res.ok) throw new Error('Failed to fetch system quota');
  return res.json();
};

export default function OpsDashboardPage() {
  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ['system-quota'],
    queryFn: fetchQuota,
    refetchInterval: 30000, // 30초마다 자동 갱신
  });

  return (
    <div className="min-h-screen bg-gray-50/50 p-8">
      {/* 헤더 */}
      <div className="max-w-7xl mx-auto mb-10 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight flex items-center gap-3">
            <Activity className="text-blue-600" size={32} />
            Operations Dashboard
          </h1>
          <p className="text-gray-500 mt-2 font-medium">Real-time GCP Resource Monitoring & System Health</p>
        </div>
        
        <button 
          onClick={() => refetch()}
          disabled={isFetching}
          className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-xl shadow-sm text-sm font-bold text-gray-700 hover:bg-gray-50 transition-all active:scale-95 disabled:opacity-50"
        >
          <RefreshCcw size={16} className={isFetching ? 'animate-spin' : ''} />
          Refresh Stats
        </button>
      </div>

      <div className="max-w-7xl mx-auto space-y-8">
        {/* 프로젝트 정보 카드 */}
        <div className="bg-linear-to-r from-gray-900 to-gray-800 rounded-2xl p-6 text-white shadow-xl flex items-center justify-between border border-white/10">
          <div className="flex items-center gap-5">
            <div className="w-12 h-12 bg-white/10 rounded-xl flex items-center justify-center backdrop-blur-md">
              <ShieldCheck className="text-blue-400" size={24} />
            </div>
            <div>
              <p className="text-gray-400 text-xs font-bold uppercase tracking-widest">Active Google Cloud Project</p>
              <h2 className="text-xl font-mono font-bold mt-1">{data?.project_id || 'Detecting...'}</h2>
            </div>
          </div>
          <div className="hidden md:block px-4 py-2 bg-green-500/20 border border-green-500/30 rounded-full text-green-400 text-xs font-bold">
            SYSTEM STATUS: ONLINE
          </div>
        </div>

        {/* 할당량 그리드 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {isLoading ? (
            Array(6).fill(0).map((_, i) => (
              <div key={i} className="bg-white rounded-2xl p-6 h-48 animate-pulse shadow-sm border border-gray-100" />
            ))
          ) : isError ? (
            <div className="col-span-full bg-red-50 border border-red-100 p-8 rounded-2xl flex flex-col items-center justify-center text-red-600 gap-4">
              <AlertCircle size={48} />
              <div className="text-center">
                <p className="text-lg font-bold">Failed to load system metrics</p>
                <p className="text-sm opacity-80 mt-1">Please check if your GCP credentials have enough permissions.</p>
              </div>
            </div>
          ) : (
            data?.quotas.map((quota, idx) => {
              const usagePercent = Math.min(100, (quota.usage / quota.limit) * 100);
              const isHigh = usagePercent > 80;
              
              return (
                <div key={idx} className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow group">
                  <div className="flex items-center justify-between mb-4">
                    <div className="p-3 rounded-xl bg-gray-50 group-hover:bg-blue-50 transition-colors">
                      {quota.metric.includes('cpu') ? <Cpu className="text-blue-600" size={20} /> :
                       quota.metric.includes('storage') ? <HardDrive className="text-blue-600" size={20} /> :
                       <Database className="text-blue-600" size={20} />}
                    </div>
                    <span className={`text-xs font-bold px-2 py-1 rounded-md ${isHigh ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'}`}>
                      {isHigh ? 'High Usage' : 'Healthy'}
                    </span>
                  </div>
                  
                  <h3 className="text-sm font-bold text-gray-900 mb-1 truncate" title={quota.metric}>
                    {quota.metric.split('/').pop()?.replace(/_/g, ' ')}
                  </h3>
                  <p className="text-xs text-gray-500 font-medium mb-4">{quota.metric}</p>
                  
                  <div className="space-y-3">
                    <div className="flex justify-between text-xs font-bold">
                      <span className="text-gray-400">Usage</span>
                      <span className="text-gray-900">{quota.usage.toLocaleString()} / {quota.limit.toLocaleString()} {quota.unit}</span>
                    </div>
                    <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div 
                        className={`h-full rounded-full transition-all duration-1000 ${isHigh ? 'bg-red-500' : 'bg-blue-600'}`}
                        style={{ width: `${usagePercent}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* 푸터 / 링크 */}
        <div className="pt-8 border-t border-gray-200 flex flex-col md:flex-row justify-between items-center gap-4 text-gray-500 text-sm font-medium">
          <p>© 2026 AI Asset Platform Operations</p>
          <div className="flex gap-6">
            <a href="https://console.cloud.google.com" target="_blank" rel="noreferrer" className="flex items-center gap-1 hover:text-blue-600 transition-colors">
              GCP Console <ExternalLink size={14} />
            </a>
            <a href="/docs" target="_blank" className="flex items-center gap-1 hover:text-blue-600 transition-colors">
              API Docs <ExternalLink size={14} />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
