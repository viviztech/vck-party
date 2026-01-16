import React from 'react';
import { cn } from '@/utils/helpers';
import { ChevronRight, Home } from 'lucide-react';
import { NavLink } from 'react-router-dom';

interface BreadcrumbItem {
  label: string;
  href?: string;
  icon?: React.ReactNode;
}

interface PageHeaderProps {
  title: string;
  description?: string;
  breadcrumbs?: BreadcrumbItem[];
  actions?: React.ReactNode;
  className?: string;
}

export function PageHeader({
  title,
  description,
  breadcrumbs,
  actions,
  className,
}: PageHeaderProps) {
  const defaultBreadcrumbs: BreadcrumbItem[] = [
    { label: 'Home', href: '/', icon: <Home size={14} /> },
  ];

  const allBreadcrumbs = breadcrumbs || defaultBreadcrumbs;

  return (
    <div className={cn('mb-6', className)}>
      {/* Breadcrumbs */}
      {breadcrumbs && (
        <nav className="flex items-center space-x-1 text-sm text-gray-500 mb-2">
          {allBreadcrumbs.map((item, index) => (
            <React.Fragment key={item.label}>
              {index > 0 && <ChevronRight size={14} />}
              {item.href ? (
                <NavLink
                  to={item.href}
                  className="hover:text-gray-700 flex items-center space-x-1"
                >
                  {item.icon}
                  <span>{item.label}</span>
                </NavLink>
              ) : (
                <span className={cn(index === allBreadcrumbs.length - 1 && 'text-gray-900 font-medium')}>
                  {item.label}
                </span>
              )}
            </React.Fragment>
          ))}
        </nav>
      )}

      {/* Title & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-display font-semibold text-gray-900">{title}</h1>
          {description && (
            <p className="text-gray-500 mt-1">{description}</p>
          )}
        </div>
        {actions && <div className="flex items-center space-x-2">{actions}</div>}
      </div>
    </div>
  );
}
