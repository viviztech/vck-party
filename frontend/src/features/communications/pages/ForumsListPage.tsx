/**
 * Forums List Page
 * Displays all forums with filtering and search capabilities
 */

import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { communicationsService, Forum, ForumFilters } from '../../../services/communicationsService';
import { Button } from '../../../components/Form';
import { Input } from '../../../components/Form';
import { Select } from '../../../components/Form';
import { Card } from '../../../components/DataDisplay';
import { Badge } from '../../../components/DataDisplay';
import { Spinner } from '../../../components/Feedback';
import { PageHeader } from '@/components/Layout/PageHeader';

export default function ForumsListPage() {
  const navigate = useNavigate();
  const [forums, setForums] = useState<Forum[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');

  const fetchForums = useCallback(async () => {
    setLoading(true);
    try {
      const filters: ForumFilters = {
        page: 1,
        limit: 20,
        search: search || undefined,
        category: category ? [category] as ('general' | 'discussion' | 'feedback' | 'suggestion' | 'announcement' | 'support')[] : undefined,
      };
      
      const response = await communicationsService.getForums(filters);
      setForums(response.forums);
    } catch (error) {
      console.error('Failed to load forums:', error);
    } finally {
      setLoading(false);
    }
  }, [search, category]);

  useEffect(() => {
    fetchForums();
  }, [fetchForums]);

  const handleViewForum = (forum: Forum) => {
    navigate(`/communications/forums/${forum.id}`);
  };

  const handleCreateForum = () => {
    navigate('/communications/forums/create');
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Forums"
        description="Browse and participate in community discussions"
        actions={
          <Button variant="primary" onClick={handleCreateForum}>
            Create Forum
          </Button>
        }
      />

      <Card>
        <div className="p-4 border-b border-gray-200">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <Input
                placeholder="Search forums..."
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
                  { value: 'discussion', label: 'Discussion' },
                  { value: 'feedback', label: 'Feedback' },
                  { value: 'suggestion', label: 'Suggestion' },
                  { value: 'announcement', label: 'Announcement' },
                  { value: 'support', label: 'Support' },
                ]}
                value={category}
                onChange={(value) => setCategory(value as string)}
              />
            </div>
            <Button variant="secondary" onClick={fetchForums}>
              Filter
            </Button>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center items-center p-8">
            <Spinner size="lg" />
          </div>
        ) : forums.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No forums found
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {forums.map((forum) => (
              <div
                key={forum.id}
                className="p-4 hover:bg-gray-50 cursor-pointer"
                onClick={() => handleViewForum(forum)}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-medium text-gray-900">{forum.title}</h3>
                    <p className="text-sm text-gray-600 mt-1">{forum.description}</p>
                    <div className="flex items-center gap-4 mt-2">
                      <Badge variant="primary">{forum.category}</Badge>
                      {forum.is_moderated && <Badge variant="warning">Moderated</Badge>}
                      <span className="text-sm text-gray-500">
                        {forum.thread_count} threads • {forum.post_count} posts
                      </span>
                      <span className="text-sm text-gray-500">
                        by {forum.created_by_name}
                      </span>
                      {forum.last_activity_at && (
                        <span className="text-sm text-gray-500">
                          Active: {formatDate(forum.last_activity_at)}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
