/**
 * Announcement Form Component
 * Form for creating and editing announcements
 */

import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { AnnouncementCreate, AnnouncementUpdate, Announcement } from '../../../services/communicationsService';
import { Button } from '../../../components/Form';
import { Input } from '../../../components/Form';
import { Textarea } from '../../../components/Form';
import { Select } from '../../../components/Form';
import { Card } from '../../../components/DataDisplay';

const announcementSchema = z.object({
  title: z.string().min(1, 'Title is required').max(200),
  content: z.string().min(1, 'Content is required'),
  category: z.enum(['general', 'event', 'campaign', 'policy', 'alert', 'update']),
  priority: z.enum(['low', 'medium', 'high', 'urgent']),
  is_pinned: z.boolean(),
  published_at: z.string().optional(),
  expires_at: z.string().optional(),
});

type AnnouncementFormData = z.infer<typeof announcementSchema>;

interface AnnouncementFormProps {
  announcement?: Announcement;
  onSubmit: (data: AnnouncementCreate | AnnouncementUpdate) => Promise<void>;
  onCancel: () => void;
}

export default function AnnouncementForm({ announcement, onSubmit, onCancel }: AnnouncementFormProps) {
  const isEditing = !!announcement;

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    control,
  } = useForm<AnnouncementFormData>({
    resolver: zodResolver(announcementSchema),
    defaultValues: {
      title: announcement?.title || '',
      content: announcement?.content || '',
      category: announcement?.category || 'general',
      priority: announcement?.priority || 'medium',
      is_pinned: announcement?.is_pinned || false,
      published_at: announcement?.published_at?.slice(0, 16) || '',
      expires_at: announcement?.expires_at?.slice(0, 16) || '',
    },
  });

  const onFormSubmit = async (data: AnnouncementFormData) => {
    const submitData = {
      ...data,
      published_at: data.published_at || undefined,
      expires_at: data.expires_at || undefined,
    };
    await onSubmit(submitData as AnnouncementCreate | AnnouncementUpdate);
  };

  return (
    <form onSubmit={handleSubmit(onFormSubmit)}>
      <Card>
        <div className="p-6 space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Title *</label>
            <Input
              placeholder="Enter announcement title"
              error={errors.title?.message}
              {...register('title')}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Content *</label>
            <Textarea
              placeholder="Enter announcement content"
              rows={6}
              error={errors.content?.message}
              {...register('content')}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Category *</label>
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
              <label className="block text-sm font-medium text-gray-700 mb-1">Priority *</label>
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
              className="h-4 w-4 text-blue-600 border-gray-300 rounded"
              {...register('is_pinned')}
            />
            <label htmlFor="is_pinned" className="text-sm text-gray-700">Pin this announcement</label>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Publish Date</label>
              <Input type="datetime-local" {...register('published_at')} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Expiry Date</label>
              <Input type="datetime-local" {...register('expires_at')} />
            </div>
          </div>
        </div>
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end gap-3">
          <Button type="button" variant="outline" onClick={onCancel}>Cancel</Button>
          <Button type="submit" variant="primary" loading={isSubmitting}>
            {isEditing ? 'Update' : 'Create'} Announcement
          </Button>
        </div>
      </Card>
    </form>
  );
}
