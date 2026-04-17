import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import {
  LayoutDashboard,
  BookOpen,
  BarChart3,
  Brain,
  Flame,
  Briefcase,
} from "lucide-react";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Trade Tracker",
  description: "Trading journal and performance analytics with AI insights",
};

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/trades", label: "Journal", icon: BookOpen },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/positions", label: "Positions", icon: Briefcase },
  { href: "/insights", label: "AI Insights", icon: Brain },
  { href: "/bets", label: "Bets", icon: Flame },
];

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased dark`}
    >
      <body className="min-h-full flex">
        <aside className="w-64 border-r border-border bg-card flex flex-col shrink-0">
          <div className="p-6 border-b border-border">
            <h1 className="text-xl font-bold tracking-tight">Trade Tracker</h1>
            <p className="text-xs text-muted-foreground mt-1">
              Journal &middot; Analytics &middot; AI
            </p>
          </div>
          <nav className="flex-1 p-4 space-y-1">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </Link>
            ))}
          </nav>
        </aside>
        <main className="flex-1 overflow-auto">
          <div className="p-8">{children}</div>
        </main>
      </body>
    </html>
  );
}
