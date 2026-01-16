/**
 * Member Create Page
 * Page for creating a new member
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { PageHeader } from '@/components/Layout/PageHeader';
import { MemberForm } from '../components/MemberForm';
import { membersService, MemberCreate } from '@/services/membersService';

export function MemberCreatePage() {
  const navigate = useNavigate();

  const handleSubmit = async (data: MemberCreate) => {
    try {
      const member = await membersService.createMember(data);
      navigate(`/members/${member.id}`);
    } catch (error) {
      console.error('Failed to create member:', error);
      throw error;
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <PageHeader
        title="Add New Member"
        description="Enter the member's information to create a new membership"
      />
      <MemberForm onSubmit={handleSubmit} onCancel={() => navigate('/members')} />
    </div>
  );
}

export default MemberCreatePage;
