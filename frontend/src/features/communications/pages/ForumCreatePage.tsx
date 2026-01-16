/**
 * Forum Create Page
 * Form to create a new forum
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { communicationsService, ForumCreate } from '../../../services/communicationsService';
import { Button } from '../../../components/Form';
import { Input } from '../../../components/Form';
import { Textarea } from '../../../components/Form';
import { Select } from '../../../components/Form';
import { Card } from '../../../components/DataDisplay';
import { Checkbox } from '../../../components/Form';

// Form schema
const createForumSchema = z.object({
  title: z.string().min(1, 'Title is required').max(200, 'Title must be less than 200 characters'),
  description: z.string().min(1, 'Description is required'),
  category: z.enum(['general', 'discussion', 'feedback', 'suggestion', 'announcement', 'support']),
  is_moderated: z.boolean(),
  requires_approval: z.boolean(),
});

type CreateForumFormData = z.infer<typeof createForumSchema>;

export default function ForumCreatePage() {
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    control,
  } = useForm<CreateForumFormData>({
    resolver: zodResolver(createForumSchema),
    defaultValues: {
      category: 'general',
      is_moderated: false,
      requires_approval: false,
    },
  });

  const onSubmit = async (data: CreateForumFormData) => {
    setSaving(true);
    try {
      const forum = await communicationsService.createForum(data);
      navigate(`/communications/forums/${forum.id}`);
    } catch (error) {
      console.error('Failed to create forum:', error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" onClick={() => navigate('/communications/forums')}>
          ← Back to Forums
        </Button>
      </div>

      <Card>
        <div className="p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">Create Forum</h1>
          
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Title *
              </label>
              <Input
                placeholder="Enter forum title"
                error={errors.title?.message}
                {...register('title')}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description *
              </label>
              <Textarea
                placeholder="Enter forum description"
                rows={4}
                error={errors.description?.message}
                {...register('description')}
              />
            </div>

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
                      { value: 'discussion', label: 'Discussion' },
                      { value: 'feedback', label: 'Feedback' },
                      { value: 'suggestion', label: 'Suggestion' },
                      { value: 'announcement', label: 'Announcement' },
                      { value: 'support', label: 'Support' },
                    ]}
                    error={errors.category?.message}
                    {...field}
                    onChange={(value) => field.onChange(value)}
                  />
                )}
              />
            </div>

            <div className="space-y-4">
              <Controller
                name="is_moderated"
                control={control}
                render={({ field }) => (
                  <Checkbox
                    checked={field.value}
                    onChange={field.onChange}
                    label="Moderate this forum (posts require approval before publishing)"
                  />
                )}
              />
              <Controller
                name="requires_approval"
                control={control}
                render={({ field }) => (
                  <Checkbox
                    checked={field.value}
                    onChange={field.onChange}
                    label="Require approval for new posts"
                  />
                )}
              />
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate('/communications/forums')}
              >
                Cancel
              </Button>
              <Button type="submit" variant="primary" loading={saving || isSubmitting}>
                Create Forum
              </Button>
            </div>
          </form>
        </div>
      </Card>
    </div>
  );
}
