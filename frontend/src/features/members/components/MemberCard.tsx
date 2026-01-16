/**
 * Member Card Component
 * Card view for displaying member information
 */

import React from 'react';
import { Card, CardContent } from '@/components/DataDisplay/Card';
import { Avatar } from '@/components/DataDisplay/Avatar';
import { Badge } from '@/components/DataDisplay/Badge';
import type { Member } from '@/services/membersService';
import { Phone, Mail, MapPin, Calendar } from 'lucide-react';
import { formatDate } from '@/utils/helpers';

interface MemberCardProps {
  member: Member;
  onClick?: () => void;
}

export function MemberCard({ member, onClick }: MemberCardProps) {
  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { variant: 'success' | 'warning' | 'error' | 'info' | 'default'; label: string }> = {
      active: { variant: 'success', label: 'Active' },
      pending: { variant: 'warning', label: 'Pending' },
      suspended: { variant: 'error', label: 'Suspended' },
      inactive: { variant: 'info', label: 'Inactive' },
    };
    const config = statusConfig[status] || { variant: 'default', label: status };
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  return (
    <div onClick={onClick} className={onClick ? 'cursor-pointer' : ''}>
      <Card hover={!!onClick}>
        <CardContent className="flex items-start space-x-4">
          <Avatar
            src={member.photo_url}
            name={`${member.first_name} ${member.last_name || ''}`}
            size="lg"
          />
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-gray-900 truncate">
                {member.first_name} {member.last_name || ''}
              </h3>
              {getStatusBadge(member.status)}
            </div>
            <p className="text-sm text-gray-500">{member.membership_number}</p>
            
            <div className="mt-3 space-y-1">
              <a href={`tel:${member.phone}`} className="flex items-center text-sm text-gray-600 hover:text-gray-900">
                <Phone size={14} className="mr-2" />
                {member.phone}
              </a>
              {member.email && (
                <a href={`mailto:${member.email}`} className="flex items-center text-sm text-gray-600 hover:text-gray-900">
                  <Mail size={14} className="mr-2" />
                  {member.email}
                </a>
              )}
              {(member.city || member.district) && (
                <div className="flex items-center text-sm text-gray-600">
                  <MapPin size={14} className="mr-2" />
                  {[member.city, member.district].filter(Boolean).join(', ')}
                </div>
              )}
              <div className="flex items-center text-sm text-gray-600">
                <Calendar size={14} className="mr-2" />
                Joined: {formatDate(member.joined_at)}
              </div>
            </div>

            {member.tags && member.tags.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1">
                {member.tags.slice(0, 3).map((tag, index) => (
                  <Badge key={index} variant="default" size="sm">{tag}</Badge>
                ))}
                {member.tags.length > 3 && (
                  <Badge variant="default" size="sm">+{member.tags.length - 3}</Badge>
                )}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default MemberCard;
