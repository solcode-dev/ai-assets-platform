"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Settings,
  ShieldCheck,
  AlertCircle,
  Activity,
  Video,
  Image as ImageIcon,
  RefreshCcw,
} from "lucide-react";
import { motion } from "framer-motion";

interface QuotaModel {
  name: string;
  type: "image" | "video";
  limit: number;
  used: number;
  remaining: number;
  unit: string;
  status: "stable" | "warning" | "critical";
}

interface QuotaResponse {
  success: boolean;
  data: {
    models: QuotaModel[];
    overall_status: string;
    last_updated: string;
  };
}

const fetchQuota = async (): Promise<QuotaResponse> => {
  const url = "http://localhost:8000/api/system/quota";
  console.log(`[Settings] Fetching quota data from: ${url}`);
  const response = await fetch(url);
  console.log("[Settings] Quota response status:", response.status);

  if (!response.ok) {
    throw new Error("Failed to fetch quota data");
  }
  const data = await response.json();
  console.log("Quota data received:", data);
  return data;
};

export default function SettingsPage() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["quota"],
    queryFn: fetchQuota,
    refetchInterval: 30000, // 30초마다 갱신
  });

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen text-white bg-black">
        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-gray-400 font-medium">Loading settings...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen text-white bg-black p-4">
        <AlertCircle size={48} className="text-red-500 mb-4" />
        <h2 className="text-xl font-bold mb-2">데이터를 불러오지 못했습니다</h2>
        <p className="text-gray-400 mb-6 text-center">
          백엔드 서버가 실행 중인지 확인해 주세요.
        </p>
        <button
          onClick={() => refetch()}
          className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors font-medium"
        >
          다시 시도
        </button>
      </div>
    );
  }

  const quota = data?.data;

  return (
    <div className="min-h-screen bg-black text-white p-8 pl-24">
      <div className="max-w-5xl mx-auto">
        {/* 헤더 */}
        <header className="mb-12 flex justify-between items-end">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-blue-500/20 rounded-lg">
                <Settings className="text-blue-500" size={24} />
              </div>
              <h1 className="text-3xl font-bold tracking-tight">
                System Settings
              </h1>
            </div>
            <p className="text-gray-400">
              API 할당량 및 서비스 상태를 모니터링합니다.
            </p>
          </div>

          <button
            onClick={() => refetch()}
            className="flex items-center gap-2 px-4 py-2 bg-gray-900 border border-gray-800 rounded-lg hover:bg-gray-800 transition-all text-sm text-gray-400 hover:text-white"
          >
            <RefreshCcw size={14} />
            새로고침
          </button>
        </header>

        {/* 헬스 체크 섹션 */}
        <section className="mb-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          <StatusCard
            title="Service Status"
            value={data?.success ? "Active" : "System Error"}
            icon={
              data?.success ? (
                <ShieldCheck className="text-emerald-500" />
              ) : (
                <AlertCircle className="text-red-500" />
              )
            }
            color={data?.success ? "emerald" : "red"}
          />
          <StatusCard
            title="API Latency"
            value={data?.success ? "342ms" : "Unknown"}
            icon={
              <Activity
                className={data?.success ? "text-blue-500" : "text-gray-500"}
              />
            }
            color={data?.success ? "blue" : "gray"}
          />
          <StatusCard
            title="Last Updated"
            value={
              data?.success
                ? new Date(quota?.last_updated || "").toLocaleTimeString()
                : "Sync Failed"
            }
            icon={
              <RefreshCcw
                className={data?.success ? "text-purple-500" : "text-red-500"}
              />
            }
            color={data?.success ? "purple" : "red"}
          />
        </section>

        {/* 할당량 대시보드 */}
        <section>
          <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
            <Activity size={20} className="text-blue-500" />
            API Quota Usage
          </h2>

          <div className="grid grid-cols-1 gap-6">
            {!data?.success || !quota?.models ? (
              <div className="bg-gray-900/50 border border-red-900/50 rounded-2xl p-8 backdrop-blur-sm flex flex-col items-center text-center">
                <AlertCircle size={48} className="text-red-500 mb-4" />
                <h3 className="text-lg font-bold text-red-400 mb-2">
                  할당량 정보를 불러올 수 없습니다
                </h3>
                <p className="text-gray-500 max-w-md">
                  GCP 자격 증명을 확인하거나 백엔드 로그를 참조해주세요.
                </p>
              </div>
            ) : (
              quota.models.map((model, index) => (
                <motion.div
                  key={model.name}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6 backdrop-blur-sm"
                >
                  <div className="flex flex-wrap justify-between items-start mb-6 gap-4">
                    <div className="flex items-start gap-4">
                      <div
                        className={`p-3 rounded-xl bg-gray-800 text-white shadow-inner`}
                      >
                        {model.type === "video" ? (
                          <Video size={24} />
                        ) : (
                          <ImageIcon size={24} />
                        )}
                      </div>
                      <div>
                        <h3 className="text-lg font-bold mb-1">{model.name}</h3>
                        <p className="text-sm text-gray-500 uppercase tracking-widest">
                          {model.unit}
                        </p>
                      </div>
                    </div>

                    <div
                      className={`px-4 py-1.5 rounded-full text-xs font-bold border transition-colors
                      ${
                        model.status === "stable"
                          ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-500"
                          : model.status === "warning"
                            ? "bg-amber-500/10 border-amber-500/20 text-amber-500 animate-pulse"
                            : "bg-red-500/10 border-red-500/20 text-red-500 animate-pulse"
                      }`}
                    >
                      {model.status.toUpperCase()}
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-400">Resource Usage</span>
                      <span className="font-mono text-white">
                        <span className="text-blue-400 font-bold">
                          {model.used}
                        </span>{" "}
                        / {model.limit}
                      </span>
                    </div>

                    <div className="h-3 bg-gray-800 rounded-full overflow-hidden shadow-inner uppercase">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{
                          width: `${(model.used / model.limit) * 100}%`,
                        }}
                        transition={{ duration: 1, ease: "easeOut" }}
                        className={`h-full rounded-full shadow-lg ${
                          model.status === "stable"
                            ? "bg-linear-to-r from-blue-600 to-indigo-600"
                            : model.status === "warning"
                              ? "bg-linear-to-r from-amber-500 to-orange-600"
                              : "bg-linear-to-r from-red-500 to-pink-600"
                        }`}
                      />
                    </div>

                    <div className="flex justify-between items-center text-xs pt-2">
                      <p className="text-gray-500">
                        Remaining allowance:{" "}
                        <span className="text-gray-300 font-bold">
                          {model.remaining}
                        </span>{" "}
                        requests
                      </p>
                      {model.status !== "stable" && (
                        <span className="text-amber-500 flex items-center gap-1">
                          <AlertCircle size={12} />
                          Usage limit approaching
                        </span>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))
            )}
          </div>
        </section>
      </div>
    </div>
  );
}

function StatusCard({
  title,
  value,
  icon,
  color,
}: {
  title: string;
  value: string;
  icon: React.ReactNode;
  color: string;
}) {
  return (
    <div className="bg-gray-900/40 border border-gray-800 p-5 rounded-2xl hover:border-gray-700 transition-colors">
      <div className="flex items-center gap-3 mb-3">
        <div className={`p-1.5 rounded-md bg-${color}-500/10`}>{icon}</div>
        <span className="text-sm text-gray-500 font-medium">{title}</span>
      </div>
      <p className="text-2xl font-bold tracking-tight">{value}</p>
    </div>
  );
}
