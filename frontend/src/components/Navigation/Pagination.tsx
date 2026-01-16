import React from 'react';
import { cn } from '@/utils/helpers';
import { ChevronLeft, ChevronRight, MoreHorizontal } from 'lucide-react';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  siblingCount?: number;
  className?: string;
  showingText?: string;
}

export function Pagination({
  currentPage,
  totalPages,
  onPageChange,
  siblingCount = 1,
  className,
  showingText,
}: PaginationProps) {
  const getPageNumbers = () => {
    const pages: (number | string)[] = [];
    const leftSiblingIndex = Math.max(currentPage - siblingCount - 1, 1);
    const rightSiblingIndex = Math.min(currentPage + siblingCount, totalPages);
    const shouldShowLeftDots = leftSiblingIndex > 2;
    const shouldShowRightDots = rightSiblingIndex < totalPages - 1;
    const firstPageIndex = 1;
    const lastPageIndex = totalPages;

    if (!shouldShowLeftDots && shouldShowRightDots) {
      const leftItemCount = 2 + 2 * siblingCount;
      for (let i = 0; i < leftItemCount; i++) {
        pages.push(i + 1);
      }
      pages.push('dots', lastPageIndex);
    } else if (shouldShowLeftDots && !shouldShowRightDots) {
      const rightItemCount = 2 + 2 * siblingCount;
      for (let i = 0; i < rightItemCount; i++) {
        pages.push(totalPages - rightItemCount + i + 1);
      }
      pages.unshift(firstPageIndex, 'dots');
    } else if (shouldShowLeftDots && shouldShowRightDots) {
      pages.push(firstPageIndex, 'dots');
      for (let i = leftSiblingIndex; i <= rightSiblingIndex; i++) {
        pages.push(i);
      }
      pages.push('dots', lastPageIndex);
    } else {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    }

    return pages;
  };

  const pageNumbers = getPageNumbers();

  if (totalPages <= 1) {
    return null;
  }

  return (
    <div className={cn('flex flex-col items-center space-y-2', className)}>
      {showingText && (
        <div className="text-sm text-gray-500">{showingText}</div>
      )}
      <nav
      className={cn('flex items-center justify-center space-x-1', className)}
      aria-label="Pagination"
    >
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className={cn(
          'p-2 rounded-lg border border-gray-300',
          'hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed'
        )}
        aria-label="Previous page"
      >
        <ChevronLeft size={18} />
      </button>

      {pageNumbers.map((page, index) => {
        if (page === 'dots') {
          return (
            <span key={`dots-${index}`} className="px-2 text-gray-400">
              <MoreHorizontal size={18} />
            </span>
          );
        }

        return (
          <button
            key={page}
            onClick={() => onPageChange(page as number)}
            className={cn(
              'w-10 h-10 rounded-lg text-sm font-medium',
              currentPage === page
                ? 'bg-primary-600 text-white'
                : 'border border-gray-300 hover:bg-gray-50'
            )}
            aria-label={`Page ${page}`}
            aria-current={currentPage === page ? 'page' : undefined}
          >
            {page}
          </button>
        );
      })}

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className={cn(
          'p-2 rounded-lg border border-gray-300',
          'hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed'
        )}
        aria-label="Next page"
      >
        <ChevronRight size={18} />
      </button>
    </nav>
    </div>
  );
}

interface SimplePaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  className?: string;
}

export function SimplePagination({
  currentPage,
  totalPages,
  onPageChange,
  className,
}: SimplePaginationProps) {
  if (totalPages <= 1) {
    return null;
  }

  return (
    <div className={cn('flex items-center justify-between px-4 py-3', className)}>
      <div className="text-sm text-gray-500">
        Page {currentPage} of {totalPages}
      </div>
      <div className="flex items-center space-x-2">
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className={cn(
            'px-3 py-1 text-sm border border-gray-300 rounded-lg',
            'hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed'
          )}
        >
          Previous
        </button>
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className={cn(
            'px-3 py-1 text-sm border border-gray-300 rounded-lg',
            'hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed'
          )}
        >
          Next
        </button>
      </div>
    </div>
  );
}
