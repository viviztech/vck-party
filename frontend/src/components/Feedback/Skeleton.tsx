import React from 'react';
import { cn } from '@/utils/helpers';

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
}

export function Skeleton({
  className,
  variant = 'text',
  width,
  height,
}: SkeletonProps) {
  const variantStyles = {
    text: 'rounded h-4',
    circular: 'rounded-full',
    rectangular: 'rounded-lg',
  };

  return (
    <div
      className={cn(
        'animate-pulse bg-gray-200',
        variantStyles[variant],
        className
      )}
      style={{
        width: width || (variant === 'text' ? '100%' : undefined),
        height: height || (variant === 'text' ? undefined : undefined),
      }}
    />
  );
}

interface SkeletonTextProps {
  lines?: number;
  className?: string;
  lastLineWidth?: string | number;
}

export function SkeletonText({
  lines = 3,
  className,
  lastLineWidth = '60%',
}: SkeletonTextProps) {
  return (
    <div className={cn('space-y-2', className)}>
      {[...Array(lines)].map((_, i) => (
        <Skeleton
          key={i}
          variant="text"
          className={i === lines - 1 ? lastLineWidth : undefined}
        />
      ))}
    </div>
  );
}

interface SkeletonAvatarProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const avatarSizes = {
  sm: 'w-8 h-8',
  md: 'w-10 h-10',
  lg: 'w-12 h-12',
};

export function SkeletonAvatar({ size = 'md', className }: SkeletonAvatarProps) {
  return (
    <Skeleton
      variant="circular"
      className={cn(avatarSizes[size], className)}
    />
  );
}

interface SkeletonCardProps {
  showAvatar?: boolean;
  showTitle?: boolean;
  showContent?: boolean;
  showFooter?: boolean;
}

export function SkeletonCard({
  showAvatar = true,
  showTitle = true,
  showContent = true,
  showFooter = true,
}: SkeletonCardProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
      {showAvatar && (
        <div className="flex items-center space-x-4">
          <SkeletonAvatar size="lg" />
          <div className="space-y-2 flex-1">
            {showTitle && <Skeleton className="h-5 w-40" />}
            {showTitle && <Skeleton className="h-4 w-24" />}
          </div>
        </div>
      )}
      {showContent && (
        <div className="space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
        </div>
      )}
      {showFooter && (
        <div className="flex justify-end space-x-2 pt-2">
          <Skeleton className="h-8 w-20" />
          <Skeleton className="h-8 w-20" />
        </div>
      )}
    </div>
  );
}

interface SkeletonTableProps {
  rows?: number;
  columns?: number;
  showHeader?: boolean;
}

export function SkeletonTable({
  rows = 5,
  columns = 4,
  showHeader = true,
}: SkeletonTableProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      {showHeader && (
        <div className="bg-gray-50 border-b border-gray-200">
          <div className="flex">
            {[...Array(columns)].map((_, i) => (
              <div key={i} className="flex-1 p-4">
                <Skeleton className="h-4 w-20" />
              </div>
            ))}
          </div>
        </div>
      )}
      <div className="divide-y divide-gray-100">
        {[...Array(rows)].map((_, i) => (
          <div key={i} className="flex">
            {[...Array(columns)].map((_, j) => (
              <div key={j} className="flex-1 p-4">
                <Skeleton className="h-4 w-full" />
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
