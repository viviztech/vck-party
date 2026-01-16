import React, { useState } from 'react';
import { cn } from '@/utils/helpers';
import {
  Bell,
  Search,
  ChevronDown,
  User,
  LogOut,
  Settings,
  Moon,
  Sun,
} from 'lucide-react';

interface HeaderProps {
  onMenuClick?: () => void;
}

interface UserMenuItem {
  label: string;
  icon: React.ReactNode;
  onClick: () => void;
  danger?: boolean;
}

export function Header({ onMenuClick }: HeaderProps) {
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [darkMode, setDarkMode] = useState(false);

  const userMenuItems: UserMenuItem[] = [
    { label: 'Profile', icon: <User size={18} />, onClick: () => {} },
    { label: 'Settings', icon: <Settings size={18} />, onClick: () => {} },
    { label: 'Sign out', icon: <LogOut size={18} />, onClick: () => {}, danger: true },
  ];

  const notifications = [
    { id: 1, title: 'New member registered', time: '5 min ago', unread: true },
    { id: 2, title: 'Event reminder: Town Hall', time: '1 hour ago', unread: true },
    { id: 3, title: 'Voting results published', time: '2 hours ago', unread: false },
  ];

  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-4 lg:px-6 sticky top-0 z-30">
      {/* Left side - Mobile menu & Search */}
      <div className="flex items-center space-x-4 flex-1">
        {/* Mobile menu button */}
        {onMenuClick && (
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 rounded-md hover:bg-gray-100"
            aria-label="Open menu"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        )}

        {/* Search */}
        <div className="relative hidden sm:block flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <input
            type="text"
            placeholder="Search..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Right side - Actions */}
      <div className="flex items-center space-x-2">
        {/* Dark mode toggle */}
        <button
          onClick={() => setDarkMode(!darkMode)}
          className="p-2 rounded-lg hover:bg-gray-100 text-gray-600"
          aria-label="Toggle dark mode"
        >
          {darkMode ? <Sun size={20} /> : <Moon size={20} />}
        </button>

        {/* Notifications */}
        <div className="relative">
          <button
            onClick={() => {
              setShowNotifications(!showNotifications);
              setShowUserMenu(false);
            }}
            className="relative p-2 rounded-lg hover:bg-gray-100 text-gray-600"
            aria-label="Notifications"
          >
            <Bell size={20} />
            <span className="absolute top-1 right-1 w-2 h-2 bg-error-500 rounded-full" />
          </button>

          {/* Notifications dropdown */}
          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 py-2 animate-slide-down">
              <div className="px-4 py-2 border-b border-gray-100">
                <h3 className="font-medium text-gray-900">Notifications</h3>
              </div>
              <div className="max-h-80 overflow-y-auto">
                {notifications.map((notification) => (
                  <div
                    key={notification.id}
                    className={cn(
                      'px-4 py-3 hover:bg-gray-50 cursor-pointer',
                      notification.unread && 'bg-primary-50'
                    )}
                  >
                    <p className="text-sm font-medium text-gray-900">{notification.title}</p>
                    <p className="text-xs text-gray-500 mt-1">{notification.time}</p>
                  </div>
                ))}
              </div>
              <div className="px-4 py-2 border-t border-gray-100">
                <button className="text-sm text-primary-600 hover:text-primary-700 font-medium">
                  View all notifications
                </button>
              </div>
            </div>
          )}
        </div>

        {/* User menu */}
        <div className="relative">
          <button
            onClick={() => {
              setShowUserMenu(!showUserMenu);
              setShowNotifications(false);
            }}
            className="flex items-center space-x-2 p-1.5 rounded-lg hover:bg-gray-100"
          >
            <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
              <span className="text-primary-700 font-medium text-sm">JD</span>
            </div>
            <span className="hidden md:block text-sm font-medium text-gray-700">John Doe</span>
            <ChevronDown size={16} className="text-gray-400" />
          </button>

          {/* User dropdown */}
          {showUserMenu && (
            <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 animate-slide-down">
              {userMenuItems.map((item) => (
                <button
                  key={item.label}
                  onClick={item.onClick}
                  className={cn(
                    'w-full flex items-center space-x-2 px-4 py-2 text-sm hover:bg-gray-50',
                    item.danger ? 'text-error-600' : 'text-gray-700'
                  )}
                >
                  {item.icon}
                  <span>{item.label}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
