import React from 'react';
import { cn } from '@/utils/helpers';

export type TabItem = {
  key: string;
  label: string;
  icon?: React.ReactNode;
  disabled?: boolean;
};

interface TabsProps {
  tabs: TabItem[];
  activeTab: string;
  onChange: (key: string) => void;
  variant?: 'default' | 'pills' | 'underline';
  className?: string;
}

const tabStyles = {
  default: {
    container: 'bg-gray-100 p-1 rounded-lg',
    tab: 'px-4 py-2 text-sm font-medium rounded-md',
    active: 'bg-white text-gray-900 shadow-sm',
    inactive: 'text-gray-600 hover:text-gray-900',
  },
  pills: {
    container: '',
    tab: 'px-4 py-2 text-sm font-medium rounded-full',
    active: 'bg-primary-600 text-white',
    inactive: 'text-gray-600 hover:bg-gray-100',
  },
  underline: {
    container: 'border-b border-gray-200',
    tab: 'px-4 py-2 text-sm font-medium border-b-2 border-transparent',
    active: 'text-primary-600 border-primary-600',
    inactive: 'text-gray-500 hover:text-gray-700 border-transparent hover:border-gray-300',
  },
};

export function Tabs({
  tabs,
  activeTab,
  onChange,
  variant = 'default',
  className,
}: TabsProps) {
  const styles = tabStyles[variant];

  return (
    <div className={className}>
      <div className={cn('flex items-center', styles.container)}>
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => !tab.disabled && onChange(tab.key)}
            disabled={tab.disabled}
            className={cn(
              'inline-flex items-center space-x-2 transition-colors',
              styles.tab,
              activeTab === tab.key ? styles.active : styles.inactive,
              tab.disabled && 'opacity-50 cursor-not-allowed'
            )}
          >
            {tab.icon}
            <span>{tab.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

interface TabPanelProps {
  children: React.ReactNode;
  value: string;
  activeValue: string;
  className?: string;
}

export function TabPanel({
  children,
  value,
  activeValue,
  className,
}: TabPanelProps) {
  if (value !== activeValue) {
    return null;
  }

  return <div className={className}>{children}</div>;
}
