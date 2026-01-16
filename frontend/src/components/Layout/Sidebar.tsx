import React from 'react';
import { cn } from '@/utils/helpers';
import {
  Home,
  Users,
  TreePine,
  Calendar,
  MessageSquare,
  Vote,
  Settings,
  HelpCircle,
  X,
  Menu,
} from 'lucide-react';
import { NavLink } from 'react-router-dom';

interface SidebarProps {
  open: boolean;
  onClose: (() => void) | undefined;
}

interface NavItem {
  label: string;
  icon: React.ReactNode;
  href: string;
  children?: NavItem[];
}

const navItems: NavItem[] = [
  { label: 'Dashboard', icon: <Home size={20} />, href: '/dashboard' },
  { label: 'Members', icon: <Users size={20} />, href: '/members' },
  { label: 'Hierarchy', icon: <TreePine size={20} />, href: '/hierarchy' },
  { label: 'Events', icon: <Calendar size={20} />, href: '/events' },
  { label: 'Communications', icon: <MessageSquare size={20} />, href: '/communications' },
  { label: 'Voting', icon: <Vote size={20} />, href: '/voting' },
];

const bottomNavItems: NavItem[] = [
  { label: 'Settings', icon: <Settings size={20} />, href: '/settings' },
  { label: 'Help', icon: <HelpCircle size={20} />, href: '/help' },
];

export function Sidebar({ open, onClose }: SidebarProps) {
  return (
    <>
      {/* Mobile Overlay */}
      {open && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200 transform transition-transform duration-200 ease-in-out lg:translate-x-0 lg:static lg:z-auto',
          open ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200">
            <NavLink to="/" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">V</span>
              </div>
              <span className="font-display font-semibold text-gray-900 text-lg">VCK</span>
            </NavLink>
            <button
              onClick={onClose}
              className="lg:hidden p-1 rounded-md hover:bg-gray-100"
              aria-label="Close sidebar"
            >
              <X size={20} />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
            {navItems.map((item) => (
              <NavLink
                key={item.href}
                to={item.href}
                className={({ isActive }) =>
                  cn(
                    'flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  )
                }
              >
                {item.icon}
                <span>{item.label}</span>
              </NavLink>
            ))}
          </nav>

          {/* Bottom Navigation */}
          <div className="px-3 py-4 border-t border-gray-200 space-y-1">
            {bottomNavItems.map((item) => (
              <NavLink
                key={item.href}
                to={item.href}
                className={({ isActive }) =>
                  cn(
                    'flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  )
                }
              >
                {item.icon}
                <span>{item.label}</span>
              </NavLink>
            ))}
          </div>
        </div>
      </aside>
    </>
  );
}

export function MobileMenuButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="lg:hidden p-2 rounded-md hover:bg-gray-100"
      aria-label="Open menu"
    >
      <Menu size={20} />
    </button>
  );
}
