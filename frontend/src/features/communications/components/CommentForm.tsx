/**
 * Comment Form Component
 * Form to add comments to posts
 */

import { useState } from 'react';
import { communicationsService, CommentCreate, Comment } from '../../../services/communicationsService';
import { Button } from '../../../components/Form';
import { Textarea } from '../../../components/Form';

interface CommentFormProps {
  postId: string;
  parentId?: string;
  onCommentAdded: (comment: Comment) => void;
}

export default function CommentForm({ postId, parentId, onCommentAdded }: CommentFormProps) {
  const [content, setContent] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!content.trim()) return;

    setSubmitting(true);
    try {
      const comment = await communicationsService.createComment(postId, {
        content: content.trim(),
        parent_id: parentId,
      } as CommentCreate);
      onCommentAdded(comment);
      setContent('');
    } catch (error) {
      console.error('Failed to add comment:', error);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-3">
      <Textarea
        placeholder="Write a comment..."
        value={content}
        onChange={(e) => setContent(e.target.value)}
        className="flex-1"
        rows={2}
      />
      <Button type="submit" variant="primary" loading={submitting} disabled={!content.trim()}>
        Post
      </Button>
    </form>
  );
}
