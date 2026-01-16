/**
 * Announcement Create Page
 * Form to create a new announcement
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { communicationsService, AnnouncementCreate } from '../../../services/communicationsService';
import { Button } from '../../../components/Form';
import { Input } from '../../../components/Form';
import { Textarea } from '../../../components/Form';
import { Select } from '../../../components/Form';
import { Card } from '../../../components/DataDisplay';
import { Spinner } from '../../../components/Feedback';

// Form schema
const createAnnouncementSchema = z.object({
  title: z.string().min(1, 'Title is required').max(200, 'Title must be less than 200 characters'),
  content: z.string().min(1, 'Content is required'),
  category: z.enum(['general', 'event', 'campaign', 'policy', 'alert', 'update']),
  priority: z.enum(['low', 'medium', 'high', 'urgent']),
  is_pinned: z.boolean(),
  published_at: z.string().optional(),
  expires_at: z.string().optional(),
});

type CreateAnnouncementFormData = z.infer<typeof createAnnouncementSchema>;

export default function AnnouncementCreatePage() {
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    control,
  } = useForm<CreateAnnouncementFormData>({
    resolver: zodResolver(createAnnouncementSchema),
    defaultValues: {
      category: 'general',
      priority: 'medium',
      is_pinned: false,
    },
  });

  const onSubmit = async (data: CreateAnnouncementFormData) => {
    setSaving(true);
    try {
      const announcement = await communicationsService.createAnnouncement(data);
      navigate(`/communications/announcements/${announcement.id}`);
    } catch (error) {
      console.error('Failed to create announcement:', error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" onClick={() => navigate('/communications/announcements')}>
          ← Back to Announcements
        </Button>
      </div>

      <Card>
        <div className="p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">Create Announcement</h1>
          
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Title *
              </label>
              <Input
                placeholder="Enter announcement title"
                error={errors.title?.message}
                {...register('title')}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Content *
              </label>
              <Textarea
                placeholder="Enter announcement content"
                rows={6}
                error={errors.content?.message}
                {...register('content')}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category *
                </label>
                <Controller
                  name="category"
                  control={control}
                  render={({ field }) => (
                    <Select
                      options={[
                        { value: 'general', label: 'General' },
                        { value: 'event', label: 'Event' },
                        { value: 'campaign', label: 'Campaign' },
                        { value: 'policy', label: 'Policy' },
                        { value: 'alert', label: 'Alert' },
                        { value: 'update', label: 'Update' },
                      ]}
                      error={errors.category?.message}
                      {...field}
                      onChange={(value) => field.onChange(value)}
                    />
                  )}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Priority *
                </label>
                <Controller
                  name="priority"
                  control={control}
                  render={({ field }) => (
                    <Select
                      options={[
                        { value: 'low', label: 'Low' },
                        { value: 'medium', label: 'Medium' },
                        { value: 'high', label: 'High' },
                        { value: 'urgent', label: 'Urgent' },
                      ]}
                      error={errors.priority?.message}
                      {...field}
                      onChange={(value) => field.onChange(value)}
                    />
                  )}
                />
              </div>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_pinned"
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                {...register('is_pinned')}
              />
              <label htmlFor="is_pinned" className="text-sm text-gray-700">
                Pin this announcement (will appear at the top)
              </label>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Publish Date
                </label>
                <Input
                  type="datetime-local"
                  {...register('published_at')}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Expiry Date
                </label>
                <Input
                  type="datetime-local"
                  {...register('expires_at')}
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate('/communications/announcements')}
              >
                Cancel
              </Button>
              <Button type="submit" variant="primary" loading={saving || isSubmitting}>
                Create Announcement
              </Button>
            </div>
          </form>
        </div>
      </Card>
    </div>
  );
}
