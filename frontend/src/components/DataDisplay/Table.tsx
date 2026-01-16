import React, { useState } from 'react';
import { cn } from '@/utils/helpers';
import { ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react';

export type Column<T> = {
  key: string;
  header: string;
  render?: (row: T) => React.ReactNode;
  sortable?: boolean;
  width?: string;
  align?: 'left' | 'center' | 'right';
};

interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (row: T) => string;
  onRowClick?: (row: T) => void;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  onSort?: (key: string) => void;
  loading?: boolean;
  emptyMessage?: string;
  className?: string;
}

export function Table<T>({
  columns,
  data,
  keyExtractor,
  onRowClick,
  sortBy,
  sortOrder,
  onSort,
  loading = false,
  emptyMessage = 'No data available',
  className,
}: TableProps<T>) {
  const renderSortIcon = (column: Column<T>) => {
    if (!column.sortable || sortBy !== column.key) {
      return <ChevronsUpDown size={14} className="text-gray-400" />;
    }
    return sortOrder === 'asc' ? (
      <ChevronUp size={14} className="text-primary-600" />
    ) : (
      <ChevronDown size={14} className="text-primary-600" />
    );
  };

  const getAlignClass = (align?: 'left' | 'center' | 'right') => {
    switch (align) {
      case 'center':
        return 'text-center';
      case 'right':
        return 'text-right';
      default:
        return 'text-left';
    }
  };

  if (loading) {
    return (
      <div className={cn('bg-white rounded-xl border border-gray-200 overflow-hidden', className)}>
        <div className="animate-pulse">
          <div className="h-12 bg-gray-100 border-b" />
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-16 border-b border-gray-50 bg-gray-50" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={cn('bg-white rounded-xl border border-gray-200 overflow-hidden', className)}>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              {columns.map((column) => (
                <th
                  key={column.key}
                  className={cn(
                    'px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider',
                    getAlignClass(column.align),
                    column.sortable && 'cursor-pointer select-none hover:bg-gray-100'
                  )}
                  style={{ width: column.width }}
                  onClick={() => column.sortable && onSort?.(column.key)}
                >
                  <div className="flex items-center space-x-1">
                    <span>{column.header}</span>
                    {column.sortable && renderSortIcon(column)}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-6 py-12 text-center text-gray-500"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              data.map((row) => (
                <tr
                  key={keyExtractor(row)}
                  className={cn(
                    'bg-white hover:bg-gray-50 transition-colors',
                    onRowClick && 'cursor-pointer'
                  )}
                  onClick={() => onRowClick?.(row)}
                >
                  {columns.map((column) => (
                    <td
                      key={column.key}
                      className={cn(
                        'px-6 py-4 text-sm text-gray-700',
                        getAlignClass(column.align)
                      )}
                    >
                      {column.render
                        ? column.render(row)
                        : (row as Record<string, unknown>)[column.key]?.toString()}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  className?: string;
}

export function Pagination({
  currentPage,
  totalPages,
  onPageChange,
  className,
}: PaginationProps) {
  const pages = Array.from({ length: totalPages }, (_, i) => i + 1);

  return (
    <div className={cn('flex items-center justify-between px-4 py-3', className)}>
      <div className="text-sm text-gray-500">
        Page {currentPage} of {totalPages}
      </div>
      <div className="flex items-center space-x-1">
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className="px-3 py-1 text-sm border border-gray-300 rounded-l-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Previous
        </button>
        {pages.map((page) => (
          <button
            key={page}
            onClick={() => onPageChange(page)}
            className={cn(
              'px-3 py-1 text-sm border-t border-b border-gray-300',
              page === currentPage
                ? 'bg-primary-600 text-white border-primary-600'
                : 'hover:bg-gray-50'
            )}
          >
            {page}
          </button>
        ))}
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="px-3 py-1 text-sm border border-gray-300 rounded-r-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Next
        </button>
      </div>
    </div>
  );
}
