/**
 * Announcement Detail Page
 * Displays full announcement details with comments section
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { communicationsService, Announcement, Comment } from '../../../services/communicationsService';
import { Button } from '../../../components/Form';
import { Card } from '../../../components/DataDisplay';
import { Badge } from '../../../components/DataDisplay';
import { Avatar } from '../../../components/DataDisplay';
import { Spinner } from '../../../components/Feedback';
import { format } from 'date-fns';

const AnnouncementDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [announcement, setAnnouncement] = useState<Announcement | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);

  const fetchAnnouncement = useCallback(async () => {
    if (!id) return;
    
    setLoading(true);
    try {
      const announcementData = await communicationsService.getAnnouncement(id);
      setAnnouncement(announcementData);
    } catch (error) {
      console.error('Failed to load announcement:', error);
      navigate('/communications/announcements');
    } finally {
      setLoading(false);
    }
  }, [id, navigate]);

  useEffect(() => {
    fetchAnnouncement();
  }, [fetchAnnouncement]);

  const handleDelete = async () => {
    if (!id || !announcement) return;
    
    if (!window.confirm('Are you sure you want to delete this announcement?')) {
      return;
    }

    setDeleting(true);
    try {
      await communicationsService.deleteAnnouncement(id);
      navigate('/communications/announcements');
    } catch (error) {
      console.error('Failed to delete announcement:', error);
    } finally {
      setDeleting(false);
    }
  };

  const handleEdit = () => {
    navigate(`/communications/announcements/${id}/edit`);
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
    return format(new Date(dateString), 'MMMM d, yyyy h:mm a');
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!announcement) {
    return (
      <div className="text-center py-8 text-gray-500">
        Announcement not found
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" onClick={() => navigate('/communications/announcements')}>
          ← Back to Announcements
        </Button>
      </div>

      <Card>
        <div className="p-6">
          <div className="flex items-start justify-between gap-4 mb-6">
            <div className="flex items-center gap-3">
              {announcement.is_pinned && (
                <span className="text-2xl" title="Pinned">
                  📌
                </span>
              )}
              <h1 className="text-2xl font-bold text-gray-900">{announcement.title}</h1>
            </div>
            <div className="flex items-center gap-2">
              {getPriorityBadge(announcement.priority)}
              {getCategoryBadge(announcement.category)}
            </div>
          </div>

          <div className="flex items-center gap-4 mb-6 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <Avatar name={announcement.author_name} size="sm" />
              <span>{announcement.author_name}</span>
            </div>
            <span>•</span>
            <span>{formatDate(announcement.created_at)}</span>
            {announcement.published_at && (
              <>
                <span>•</span>
                <span>Published: {formatDate(announcement.published_at)}</span>
              </>
            )}
            <span>•</span>
            <span>{announcement.views_count} views</span>
          </div>

          {announcement.target_audience && announcement.target_audience.length > 0 && (
            <div className="mb-4">
              <span className="text-sm text-gray-600">Target: </span>
              {announcement.target_audience.map((audience, index) => (
                <Badge key={index} variant="default" className="mr-2">
                  {audience}
                </Badge>
              ))}
            </div>
          )}

          {announcement.expires_at && (
            <div className="mb-4 text-sm text-gray-600">
              Expires: {formatDate(announcement.expires_at)}
            </div>
          )}

          <div className="prose max-w-none border-t border-gray-200 pt-6">
            <div className="whitespace-pre-wrap">{announcement.content}</div>
          </div>

          {announcement.attachments && announcement.attachments.length > 0 && (
            <div className="mt-6 border-t border-gray-200 pt-6">
              <h3 className="text-lg font-medium mb-3">Attachments</h3>
              <div className="space-y-2">
                {announcement.attachments.map((attachment) => (
                  <a
                    key={attachment.id}
                    href={attachment.file_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-blue-600 hover:text-blue-800"
                  >
                    <span>📎</span>
                    <span>{attachment.file_name}</span>
                    <span className="text-gray-500 text-sm">
                      ({Math.round(attachment.file_size / 1024)} KB)
                    </span>
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end gap-2">
          <Button variant="outline" onClick={handleEdit}>
            Edit
          </Button>
          <Button variant="danger" onClick={handleDelete} loading={deleting}>
            Delete
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default AnnouncementDetailPage;
