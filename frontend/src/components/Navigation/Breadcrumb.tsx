import React from 'react';
import { cn } from '@/utils/helpers';
import { ChevronRight, Home } from 'lucide-react';
import { NavLink } from 'react-router-dom';

export interface BreadcrumbItem {
  label: string;
  href?: string;
  icon?: React.ReactNode;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
  className?: string;
  separator?: React.ReactNode;
}

export function Breadcrumb({ items, className, separator }: BreadcrumbProps) {
  return (
    <nav aria-label="Breadcrumb" className={className}>
      <ol className="flex items-center space-x-1 text-sm">
        {items.map((item, index) => {
          const isLast = index === items.length - 1;

          return (
            <li key={item.label} className="flex items-center">
              {index > 0 && (
                <span className="mx-2 text-gray-400">
                  {separator || <ChevronRight size={14} />}
                </span>
              )}
              {isLast || !item.href ? (
                <span
                  className={cn(
                    'flex items-center',
                    isLast
                      ? 'text-gray-900 font-medium'
                      : 'text-gray-500 hover:text-gray-700'
                  )}
                  aria-current={isLast ? 'page' : undefined}
                >
                  {item.icon}
                  {item.icon && <span className="ml-1">{item.label}</span>}
                  {!item.icon && item.label}
                </span>
              ) : (
                <NavLink
                  to={item.href}
                  className="flex items-center text-gray-500 hover:text-gray-700"
                >
                  {item.icon}
                  {item.icon && <span className="ml-1">{item.label}</span>}
                  {!item.icon && item.label}
                </NavLink>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

// Common breadcrumb with home
export function BreadcrumbWithHome({
  items,
  className,
  homeHref = '/',
}: {
  items: BreadcrumbItem[];
  className?: string;
  homeHref?: string;
}) {
  return (
    <Breadcrumb
      items={[
        { label: 'Home', href: homeHref, icon: <Home size={14} /> },
        ...items,
      ]}
      className={className}
    />
  );
}
