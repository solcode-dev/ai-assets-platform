"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  Rocket,
} from "lucide-react";
import { NotificationCenter } from "./NotificationCenter";

const navItems = [
  { href: "/home", icon: Rocket, label: "소개" },
  { href: "/", icon: Home, label: "AI 생성" },
  // { href: "/?filter=images", icon: Images, label: "이미지" },
  // { href: "/?filter=videos", icon: Video, label: "비디오" },
  // { href: '/ops', icon: Activity, label: '운영' },
  // { href: "/settings", icon: Settings, label: "설정" },
  // { href: "/profile", icon: User, label: "프로필" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <nav className="group/sidebar fixed left-0 top-0 bottom-0 w-16 xl:w-56 bg-gray-900 flex flex-col py-4 gap-2 z-50 transition-all duration-300 ease-in-out overflow-hidden">
      {/* 로고 */}
      <Link
        href="/home"
        className="flex items-center gap-3 px-3 mx-auto xl:mx-0 xl:px-4 mb-4 shrink-0"
      >
        <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg shrink-0 flex items-center justify-center">
          <Rocket size={20} className="text-white" />
        </div>
        <span className="text-white font-bold text-sm whitespace-nowrap opacity-0 xl:opacity-100 transition-opacity duration-300 hidden xl:block">
          FOR KRAFTON
        </span>
      </Link>

      {/* 알림 센터 */}
      <div className="flex justify-center xl:justify-start xl:px-3">
        <NotificationCenter />
      </div>

      {/* 구분선 */}
      <div className="w-8 xl:w-[calc(100%-24px)] h-px bg-gray-800 my-2 mx-auto" />

      {/* 네비게이션 */}
      <div className="flex flex-col gap-1 px-3">
        {navItems.map((item) => {
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href.split("?")[0]) &&
                item.href !== "/";

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`
                flex items-center gap-3 h-10 px-2.5 rounded-lg transition-all duration-200
                ${
                  isActive
                    ? "bg-gray-800 text-white"
                    : "text-gray-400 hover:text-white hover:bg-gray-800/60"
                }
              `}
              aria-label={item.label}
            >
              <item.icon size={20} className="shrink-0" />
              <span className="text-sm font-medium whitespace-nowrap opacity-0 xl:opacity-100 transition-opacity duration-300 hidden xl:block">
                {item.label}
              </span>
              {isActive && (
                <div className="absolute left-0 w-[3px] h-6 bg-blue-500 rounded-r-full" />
              )}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
