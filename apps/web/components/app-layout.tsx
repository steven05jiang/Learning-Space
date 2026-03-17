"use client";

import { useState } from "react";
import { usePathname } from "next/navigation";
import {
  SidebarProvider,
  SidebarInset,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { ChatPanel } from "@/components/chat-panel";
import { Separator } from "@/components/ui/separator";

const PAGE_TITLES: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/resources": "My Resources",
  "/resources/new": "Add Resource",
  "/knowledge-graph": "Knowledge Graph",
  "/search": "Search",
  "/settings": "Settings",
};

function getPageTitle(pathname: string): string {
  if (PAGE_TITLES[pathname]) return PAGE_TITLES[pathname];
  // Handle dynamic sub-routes
  const match = Object.keys(PAGE_TITLES).find((key) =>
    pathname.startsWith(key + "/"),
  );
  return match ? PAGE_TITLES[match] : "Learning Space";
}

export function AppLayout({ children }: { children: React.ReactNode }) {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const pathname = usePathname();
  const title = getPageTitle(pathname);

  return (
    <SidebarProvider>
      <AppSidebar
        onToggleChat={() => setIsChatOpen(!isChatOpen)}
        isChatOpen={isChatOpen}
      />
      <SidebarInset
        className="transition-all duration-300 overflow-hidden"
        style={{ marginRight: isChatOpen ? "28rem" : 0 }}
      >
        <header className="sticky top-0 z-10 flex h-14 items-center gap-4 border-b border-border bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="h-4" />
          <div className="flex flex-1 items-center justify-between min-w-0">
            <h1 className="text-sm font-medium text-foreground truncate">
              {title}
            </h1>
          </div>
        </header>
        <main className="flex-1 overflow-auto">{children}</main>
      </SidebarInset>
      <ChatPanel isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
    </SidebarProvider>
  );
}
