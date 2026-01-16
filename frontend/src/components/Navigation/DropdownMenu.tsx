import React, { Fragment } from 'react';
import { cn } from '@/utils/helpers';
import { Menu, Transition } from '@headlessui/react';
import { ChevronDown } from 'lucide-react';

export interface DropdownItem {
  label: string;
  onClick: () => void;
  icon?: React.ReactNode;
  danger?: boolean;
  disabled?: boolean;
}

interface DropdownMenuProps {
  trigger: React.ReactNode;
  items: DropdownItem[];
  align?: 'left' | 'right';
  className?: string;
}

export function DropdownMenu({
  trigger,
  items,
  align = 'right',
  className,
}: DropdownMenuProps) {
  return (
    <Menu as="div" className={cn('relative inline-block text-left', className)}>
      <Menu.Button as={Fragment}>{trigger}</Menu.Button>
      <Transition
        as={Fragment}
        enter="transition ease-out duration-100"
        enterFrom="transform opacity-0 scale-95"
        enterTo="transform opacity-100 scale-100"
        leave="transition ease-in duration-75"
        leaveFrom="transform opacity-100 scale-100"
        leaveTo="transform opacity-0 scale-95"
      >
        <Menu.Items
          className={cn(
            'absolute z-10 mt-2 w-48 origin-top-right rounded-lg bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none',
            align === 'right' ? 'right-0' : 'left-0'
          )}
        >
          <div className="py-1">
            {items.map((item, index) => (
              <Menu.Item key={index} disabled={item.disabled}>
                {({ active }) => (
                  <button
                    onClick={item.onClick}
                    disabled={item.disabled}
                    className={cn(
                      'w-full flex items-center space-x-2 px-4 py-2 text-sm',
                      active && 'bg-gray-100',
                      item.danger
                        ? 'text-error-600'
                        : 'text-gray-700',
                      item.disabled && 'opacity-50 cursor-not-allowed'
                    )}
                  >
                    {item.icon}
                    <span>{item.label}</span>
                  </button>
                )}
              </Menu.Item>
            ))}
          </div>
        </Menu.Items>
      </Transition>
    </Menu>
  );
}

interface DropdownButtonProps {
  label: string;
  items: DropdownItem[];
  variant?: 'primary' | 'secondary';
  className?: string;
}

export function DropdownButton({
  label,
  items,
  variant = 'primary',
  className,
}: DropdownButtonProps) {
  return (
    <DropdownMenu
      trigger={
        <button
          className={cn(
            'inline-flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors',
            variant === 'primary'
              ? 'bg-primary-600 text-white hover:bg-primary-700'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200',
            className
          )}
        >
          <span>{label}</span>
          <ChevronDown size={18} />
        </button>
      }
      items={items}
    />
  );
}
