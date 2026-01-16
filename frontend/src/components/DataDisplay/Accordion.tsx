import React, { useState } from 'react';
import { cn } from '@/utils/helpers';
import { ChevronDown } from 'lucide-react';

interface AccordionItemProps {
  title: string;
  children: React.ReactNode;
  isOpen?: boolean;
  onToggle?: () => void;
  variant?: 'default' | 'bordered';
  className?: string;
}

const itemVariants = {
  default: {
    container: 'border-b border-gray-200',
    content: '',
  },
  bordered: {
    container: 'border border-gray-200 rounded-lg',
    content: 'px-4',
  },
};

export function AccordionItem({
  title,
  children,
  isOpen = false,
  onToggle,
  variant = 'default',
  className,
}: AccordionItemProps) {
  const styles = itemVariants[variant];

  return (
    <div className={cn(styles.container, className)}>
      <button
        onClick={onToggle}
        className={cn(
          'w-full flex items-center justify-between py-4 text-left',
          variant === 'bordered' && 'px-4',
          'focus:outline-none'
        )}
      >
        <span className="text-sm font-medium text-gray-900">{title}</span>
        <ChevronDown
          size={20}
          className={cn(
            'text-gray-400 transition-transform',
            isOpen && 'rotate-180'
          )}
        />
      </button>
      <div
        className={cn(
          'overflow-hidden transition-all duration-200',
          isOpen ? 'max-h-96 pb-4' : 'max-h-0'
        )}
      >
        <div className={cn('text-sm text-gray-600', styles.content)}>
          {children}
        </div>
      </div>
    </div>
  );
}

interface AccordionProps {
  items: Array<{
    key: string;
    title: string;
    content: React.ReactNode;
  }>;
  openItem?: string | null;
  onChange?: (key: string | null) => void;
  variant?: 'default' | 'bordered';
  allowMultiple?: boolean;
  className?: string;
}

export function Accordion({
  items,
  openItem,
  onChange,
  variant = 'default',
  allowMultiple = false,
  className,
}: AccordionProps) {
  const [openItems, setOpenItems] = useState<Set<string>>(new Set());

  const isOpen = (key: string) => {
    if (allowMultiple) {
      return openItems.has(key);
    }
    return openItem === key;
  };

  const handleToggle = (key: string) => {
    if (allowMultiple) {
      const newOpenItems = new Set(openItems);
      if (newOpenItems.has(key)) {
        newOpenItems.delete(key);
      } else {
        newOpenItems.add(key);
      }
      setOpenItems(newOpenItems);
      onChange?.(key);
    } else {
      onChange?.(openItem === key ? null : key);
    }
  };

  return (
    <div className={cn('space-y-1', className)}>
      {items.map((item) => (
        <AccordionItem
          key={item.key}
          title={item.title}
          isOpen={isOpen(item.key)}
          onToggle={() => handleToggle(item.key)}
          variant={variant}
        >
          {item.content}
        </AccordionItem>
      ))}
    </div>
  );
}
