/**
 * Hierarchy Breadcrumb Component
 * Breadcrumb navigation for hierarchy levels
 */

import React from 'react';
import { ChevronRight, Home, MapPin, Building2, LayoutGrid, Users } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { cn } from '@/utils/helpers';
import type { District, Constituency, Ward, Booth } from '@/services/hierarchyService';

interface HierarchyBreadcrumbItem {
  label: string;
  href?: string;
  icon?: React.ReactNode;
}

interface HierarchyBreadcrumbProps {
  district?: District | null;
  constituency?: Constituency | null;
  ward?: Ward | null;
  booth?: Booth | null;
  className?: string;
}

export function HierarchyBreadcrumb({ district, constituency, ward, booth, className }: HierarchyBreadcrumbProps) {
  const items: HierarchyBreadcrumbItem[] = [
    { label: 'Hierarchy', href: '/hierarchy', icon: <Home size={14} /> },
  ];

  if (district) {
    items.push({
      label: district.name,
      href: `/hierarchy/districts/${district.id}`,
      icon: <MapPin size={14} />,
    });
  }

  if (constituency) {
    items.push({
      label: constituency.name,
      href: `/hierarchy/constituencies/${constituency.id}`,
      icon: <Building2 size={14} />,
    });
  }

  if (ward) {
    items.push({
      label: ward.name,
      href: `/hierarchy/wards/${ward.id}`,
      icon: <LayoutGrid size={14} />,
    });
  }

  if (booth) {
    items.push({
      label: booth.name,
      icon: <Users size={14} />,
    });
  }

  return (
    <nav aria-label="Breadcrumb" className={cn('flex items-center space-x-1 text-sm', className)}>
      {items.map((item, index) => {
        const isLast = index === items.length - 1;

        return (
          <React.Fragment key={index}>
            {index > 0 && <ChevronRight size={14} className="text-gray-400" />}
            {isLast || !item.href ? (
              <span
                className={cn(
                  'flex items-center',
                  isLast ? 'text-gray-900 font-medium' : 'text-gray-500 hover:text-gray-700'
                )}
              >
                {item.icon}
                {item.icon && <span className="ml-1">{item.label}</span>}
                {!item.icon && item.label}
              </span>
            ) : (
              <NavLink
                to={item.href || '#'}
                className="flex items-center text-gray-500 hover:text-gray-700"
              >
                {item.icon}
                {item.icon && <span className="ml-1">{item.label}</span>}
                {!item.icon && item.label}
              </NavLink>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
}

export default HierarchyBreadcrumb;
