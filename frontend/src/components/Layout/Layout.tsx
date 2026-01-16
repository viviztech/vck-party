import React, { ReactNode } from 'react';
import { cn } from '@/utils/helpers';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { Footer } from './Footer';

interface LayoutProps {
  children?: ReactNode;
  className?: string;
  sidebarOpen?: boolean;
  onSidebarToggle?: () => void;
}

export function Layout({
  children,
  className,
  sidebarOpen = true,
  onSidebarToggle,
}: LayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <Sidebar open={sidebarOpen} onClose={onSidebarToggle} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header onMenuClick={onSidebarToggle} />

        {/* Page Content */}
        <main className="flex-1 p-6 overflow-auto">
          <div className={cn('max-w-7xl mx-auto', className)}>
            {children}
          </div>
        </main>

        <Footer />
      </div>
    </div>
  );
}
