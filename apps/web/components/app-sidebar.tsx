'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import {
  LayoutDashboard,
  BookOpen,
  Network,
  Search,
  Settings,
  Sparkles,
  LogOut,
} from 'lucide-react'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarSeparator,
} from '@/components/ui/sidebar'
import { Button } from '@/components/ui/button'
import { useMock } from '@/lib/mock/hooks'

const navItems = [
  { title: 'Dashboard',       href: '/dashboard',       icon: LayoutDashboard },
  { title: 'Resources',       href: '/resources',       icon: BookOpen },
  { title: 'Knowledge Graph', href: '/knowledge-graph', icon: Network },
  { title: 'Search',          href: '/search',          icon: Search },
  { title: 'Settings',        href: '/settings',        icon: Settings },
]

interface AppSidebarProps {
  onToggleChat: () => void
  isChatOpen: boolean
}

export function AppSidebar({ onToggleChat, isChatOpen }: AppSidebarProps) {
  const pathname = usePathname()
  const router = useRouter()
  const isMock = useMock()

  const handleSignOut = () => {
    if (!isMock) {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user_info')
    }
    router.push('/login')
  }

  return (
    <Sidebar collapsible="icon" className="border-r border-sidebar-border">
      <SidebarHeader className="px-4 py-4">
        <Link href="/dashboard" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="h-4 w-4"
            >
              <path d="M12 2L2 7l10 5 10-5-10-5Z" />
              <path d="M2 17l10 5 10-5" />
              <path d="M2 12l10 5 10-5" />
            </svg>
          </div>
          <span className="text-lg font-semibold text-sidebar-foreground group-data-[collapsible=icon]:hidden">
            Learning Space
          </span>
        </Link>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Main Menu
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.href}>
                  <SidebarMenuButton
                    asChild
                    isActive={pathname === item.href || pathname.startsWith(item.href + '/')}
                    tooltip={item.title}
                  >
                    <Link href={item.href}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="p-3">
        <SidebarSeparator className="mb-3" />

        {/* AI Chat Button */}
        <Button
          onClick={onToggleChat}
          className={`h-10 w-full rounded-xl transition-all flex items-center justify-center group-data-[collapsible=icon]:w-10 ${
            isChatOpen
              ? 'bg-primary/20 text-primary ring-2 ring-primary/50'
              : 'bg-primary text-primary-foreground hover:bg-primary/90'
          }`}
          aria-label="Toggle AI Chat"
        >
          <Sparkles className="h-5 w-5" />
        </Button>

        <SidebarSeparator className="my-3" />

        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              onClick={handleSignOut}
              tooltip="Sign out"
              className="cursor-pointer text-muted-foreground hover:text-foreground"
            >
              <LogOut className="h-4 w-4" />
              <span>Sign out</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  )
}
