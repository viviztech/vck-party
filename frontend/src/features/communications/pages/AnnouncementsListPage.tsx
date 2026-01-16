/**
 * Announcements List Page
 * Displays all announcements with filtering and search capabilities
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { communicationsService, Announcement, AnnouncementFilters } from '../../../services/communicationsService';
import { Button } from '../../../components/Form';
import { Input } from '../../../components/Form';
import { Select } from '../../../components/Form';
import { Card } from '../../../components/DataDisplay';
import { Table, Column } from '../../../components/DataDisplay';
import { Badge } from '../../../components/DataDisplay';
import { Avatar } from '../../../components/DataDisplay';
import { Pagination } from '../../../components/Navigation';
import { Spinner } from '../../../components/Feedback';
import { PageHeader } from '@/components/Layout/PageHeader';

const AnnouncementsListPage: React.FC = () => {
  const navigate = useNavigate();
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(10);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [priority, setPriority] = useState('');

  const fetchAnnouncements = useCallback(async () => {
    setLoading(true);
    try {
      const filters: AnnouncementFilters = {
        page,
        limit,
        search: search || undefined,
        category: category ? [category] as ('general' | 'event' | 'campaign' | 'policy' | 'alert' | 'update')[] : undefined,
        priority: priority ? [priority] as ('low' | 'medium' | 'high' | 'urgent')[] : undefined,
      };
      
      const response = await communicationsService.getAnnouncements(filters);
      setAnnouncements(response.announcements);
      setTotal(response.total);
    } catch (error) {
      console.error('Failed to load announcements:', error);
    } finally {
      setLoading(false);
    }
  }, [page, limit, search, category, priority]);

  useEffect(() => {
    fetchAnnouncements();
  }, [fetchAnnouncements]);

  const handleFilter = () => {
    setPage(1);
    fetchAnnouncements();
  };

  const handleClearFilters = () => {
    setSearch('');
    setCategory('');
    setPriority('');
    setPage(1);
  };

  const handleViewAnnouncement = (announcement: Announcement) => {
    navigate(`/communications/announcements/${announcement.id}`);
  };

  const handleCreateAnnouncement = () => {
    navigate('/communications/announcements/create');
  };

  const getPriorityBadge = (priority: string) => {
    const colors: Record<string, 'default' | 'primary' | 'success' | 'warning' | 'error' | 'info'> = {
      low: 'default',
      medium: 'info',
      high: 'warning',
      urgent: 'error',
    };
    return <Badge variant={colors[priority] || 'default'}>{priority}</Badge>;
  };

  const getCategoryBadge = (category: string) => {
    return <Badge variant="primary">{category}</Badge>;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const columns: Column<Announcement>[] = [
    {
      key: 'title',
      header: 'Title',
      render: (announcement) => (
        <div className="flex items-center gap-3">
          {announcement.is_pinned && (
            <span className="text-yellow-500" title="Pinned">
              📌
            </span>
          )}
          <div>
            <div className="font-medium text-gray-900">{announcement.title}</div>
            <div className="text-sm text-gray-500 truncate max-w-md">
              {announcement.content.substring(0, 100)}...
            </div>
          </div>
        </div>
      ),
    },
    {
      key: 'category',
      header: 'Category',
      render: (announcement) => getCategoryBadge(announcement.category),
    },
    {
      key: 'priority',
      header: 'Priority',
      render: (announcement) => getPriorityBadge(announcement.priority),
    },
    {
      key: 'author',
      header: 'Author',
      render: (announcement) => (
        <div className="flex items-center gap-2">
          <Avatar name={announcement.author_name} size="sm" />
          <span className="text-sm">{announcement.author_name}</span>
        </div>
      ),
    },
    {
      key: 'published_at',
      header: 'Published',
      render: (announcement) => (
        <span className="text-sm text-gray-600">
          {announcement.published_at ? formatDate(announcement.published_at) : 'Not published'}
        </span>
      ),
    },
    {
      key: 'views',
      header: 'Views',
      render: (announcement) => (
        <span className="text-sm text-gray-600">{announcement.views_count}</span>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Announcements"
        description="Manage and view all announcements"
        actions={
          <Button variant="primary" onClick={handleCreateAnnouncement}>
            Create Announcement
          </Button>
        }
      />

      <Card>
        <div className="p-4 border-b border-gray-200">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <Input
                placeholder="Search announcements..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <div className="w-48">
              <Select
                placeholder="Category"
                options={[
                  { value: '', label: 'All Categories' },
                  { value: 'general', label: 'General' },
                  { value: 'event', label: 'Event' },
                  { value: 'campaign', label: 'Campaign' },
                  { value: 'policy', label: 'Policy' },
                  { value: 'alert', label: 'Alert' },
                  { value: 'update', label: 'Update' },
                ]}
                value={category}
                onChange={(value) => setCategory(value as string)}
              />
            </div>
            <div className="w-40">
              <Select
                placeholder="Priority"
                options={[
                  { value: '', label: 'All Priorities' },
                  { value: 'low', label: 'Low' },
                  { value: 'medium', label: 'Medium' },
                  { value: 'high', label: 'High' },
                  { value: 'urgent', label: 'Urgent' },
                ]}
                value={priority}
                onChange={(value) => setPriority(value as string)}
              />
            </div>
            <Button variant="secondary" onClick={handleFilter}>
              Filter
            </Button>
            <Button variant="outline" onClick={handleClearFilters}>
              Clear
            </Button>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center items-center p-8">
            <Spinner size="lg" />
          </div>
        ) : announcements.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No announcements found
          </div>
        ) : (
          <>
            <Table
              data={announcements}
              columns={columns}
              keyExtractor={(announcement) => announcement.id}
              onRowClick={handleViewAnnouncement}
            />
            <div className="p-4 border-t border-gray-200">
              <Pagination
                currentPage={page}
                totalPages={Math.ceil(total / limit)}
                onPageChange={setPage}
              />
            </div>
          </>
        )}
      </Card>
    </div>
  );
};

export default AnnouncementsListPage;
