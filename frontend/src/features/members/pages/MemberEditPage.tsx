/**
 * Member Edit Page
 * Page for editing an existing member
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { PageHeader } from '@/components/Layout/PageHeader';
import { MemberForm } from '../components/MemberForm';
import { membersService, Member, MemberUpdate } from '@/services/membersService';
import { Spinner } from '@/components/Feedback/Spinner';

export function MemberEditPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [member, setMember] = useState<Member | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;

    const fetchMember = async () => {
      try {
        const memberData = await membersService.getMember(id);
        setMember(memberData);
      } catch (error) {
        console.error('Failed to fetch member:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchMember();
  }, [id]);

  const handleSubmit = async (data: MemberUpdate) => {
    if (!member) return;
    try {
      await membersService.updateMember(member.id, data);
      navigate(`/members/${member.id}`);
    } catch (error) {
      console.error('Failed to update member:', error);
      throw error;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!member) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-gray-900">Member not found</h2>
        <p className="text-gray-500 mt-2">The member you're looking for doesn't exist.</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <PageHeader
        title="Edit Member"
        description={`Editing ${member.first_name} ${member.last_name || ''}`}
      />
      <MemberForm
        member={member}
        onSubmit={handleSubmit}
        onCancel={() => navigate(`/members/${id}`)}
      />
    </div>
  );
}

export default MemberEditPage;
