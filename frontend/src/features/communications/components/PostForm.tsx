/**
 * Post Form Component
 * Form for creating and editing forum posts
 */

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import type { ForumPostCreate, ForumPost } from '../../../services/communicationsService';
import { Button } from '../../../components/Form';
import { Input } from '../../../components/Form';
import { Textarea } from '../../../components/Form';

const postSchema = z.object({
  title: z.string().optional(),
  content: z.string().min(1, 'Content is required'),
  is_anonymous: z.boolean(),
  tags: z.string().optional(),
});

type PostFormData = z.infer<typeof postSchema>;

interface PostFormProps {
  post?: ForumPost;
  onSubmit: (data: ForumPostCreate) => Promise<void>;
  onCancel: () => void;
}

export default function PostForm({ post, onSubmit, onCancel }: PostFormProps) {
  const isEditing = !!post;

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<PostFormData>({
    resolver: zodResolver(postSchema),
    defaultValues: {
      title: post?.title || '',
      content: post?.content || '',
      is_anonymous: post?.is_anonymous || false,
      tags: post?.tags?.join(', ') || '',
    },
  });

  const onFormSubmit = async (data: PostFormData) => {
    const submitData: ForumPostCreate = {
      title: data.title || undefined,
      content: data.content,
      is_anonymous: data.is_anonymous,
      tags: data.tags ? data.tags.split(',').map(t => t.trim()).filter(Boolean) : undefined,
    };
    await onSubmit(submitData);
  };

  return (
    <form onSubmit={handleSubmit(onFormSubmit)}>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
          <Input
            placeholder="Enter post title (optional)"
            error={errors.title?.message}
            {...register('title')}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Content *</label>
          <Textarea
            placeholder="Write your post content"
            rows={6}
            error={errors.content?.message}
            {...register('content')}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Tags</label>
          <Input
            placeholder="Enter tags separated by commas"
            {...register('tags')}
          />
          <p className="text-sm text-gray-500 mt-1">Separate tags with commas</p>
        </div>

        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="is_anonymous"
            className="h-4 w-4 text-blue-600 border-gray-300 rounded"
            {...register('is_anonymous')}
          />
          <label htmlFor="is_anonymous" className="text-sm text-gray-700">
            Post anonymously
          </label>
        </div>

        <div className="flex justify-end gap-3 pt-4">
          <Button type="button" variant="outline" onClick={onCancel}>Cancel</Button>
          <Button type="submit" variant="primary" loading={isSubmitting}>
            {isEditing ? 'Update' : 'Create'} Post
          </Button>
        </div>
      </div>
    </form>
  );
}
