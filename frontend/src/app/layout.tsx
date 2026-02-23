import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { QueryProvider } from "@/components/providers/QueryProvider";
import { Sidebar } from "@/components/layout/Sidebar";
import { TaskManager } from "@/components/TaskManager";
import { QuotaManager } from "@/components/layout/QuotaManager";
import { SSEProvider } from '@/components/providers/SSEProvider';
import { Toaster } from 'sonner';
import { HealthCheckManager } from "@/components/system/HealthCheckManager";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "이미지 갤러리 쇼케이스",
  description: "Midjourney 스타일의 이미지 갤러리",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased flex min-h-screen bg-gray-50`}
      >
        <QueryProvider>
          <SSEProvider>
            <Toaster position="top-right" richColors />
            <TaskManager />
            <QuotaManager />
            {/* <HealthCheckManager /> */}
            <Sidebar />
            <main className="flex-1 ml-16 xl:ml-56 transition-all duration-300">{children}</main>
          </SSEProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
