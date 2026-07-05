"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart2, Radio, Settings, Zap } from "lucide-react";
import clsx from "clsx";

const nav = [
  { href: "/", label: "Dashboard", icon: BarChart2 },
  { href: "/signals", label: "Sinais", icon: Zap },
  { href: "/settings", label: "Configurações", icon: Settings },
];

export default function Sidebar() {
  const path = usePathname();
  return (
    <aside className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col py-6 px-3 gap-2">
      <div className="flex items-center gap-2 px-3 mb-6">
        <Radio className="text-indigo-400" size={22} />
        <span className="font-bold text-lg tracking-tight">Signal Bot</span>
      </div>
      {nav.map(({ href, label, icon: Icon }) => (
        <Link
          key={href}
          href={href}
          className={clsx(
            "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
            path === href
              ? "bg-indigo-600 text-white"
              : "text-gray-400 hover:bg-gray-800 hover:text-white"
          )}
        >
          <Icon size={16} />
          {label}
        </Link>
      ))}
    </aside>
  );
}
