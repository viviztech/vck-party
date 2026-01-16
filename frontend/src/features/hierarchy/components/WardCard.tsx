/**
 * Ward Card Component
 * Card view for displaying ward information
 */

import React from 'react';
import { Card, CardContent, CardFooter } from '@/components/DataDisplay/Card';
import { Badge } from '@/components/DataDisplay/Badge';
import { LayoutGrid, Users, MapPin } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import type { Ward } from '@/services/hierarchyService';
import { formatDate } from '@/utils/helpers';
import { cn } from '@/utils/helpers';

interface WardCardProps {
  ward: Ward;
  onClick?: () => void;
  showBooths?: boolean;
  memberCount?: number;
}

export function WardCard({ ward, onClick, showBooths = true, memberCount }: WardCardProps) {
  const navigate = useNavigate();

  const handleClick = () => {
    if (onClick) {
      onClick();
    } else {
      navigate(`/hierarchy/wards/${ward.id}`);
    }
  };

  const getStatusBadge = () => {
    if (ward.is_active) {
      return <Badge variant="success">Active</Badge>;
    }
    return <Badge variant="default">Inactive</Badge>;
  };

  return (
    <div onClick={handleClick} className={cn(onClick ? 'cursor-pointer' : '')}>
      <Card hover={!!onClick || true}>
        <CardContent className="space-y-4">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <LayoutGrid className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">{ward.name}</h3>
                <p className="text-sm text-gray-500">{ward.code}</p>
              </div>
            </div>
            {getStatusBadge()}
          </div>

          {ward.name_ta && (
            <p className="text-sm text-gray-600 font-medium">{ward.name_ta}</p>
          )}

          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center text-gray-500">
              <MapPin size={14} className="mr-1" />
              <span>{ward.booths_count} Booths</span>
            </div>
            {ward.ward_number && (
              <span className="text-gray-400">Ward #{ward.ward_number}</span>
            )}
          </div>

          {memberCount !== undefined && (
            <div className="flex items-center text-sm text-gray-500">
              <Users size={14} className="mr-1" />
              <span>{memberCount.toLocaleString()} Members</span>
            </div>
          )}
        </CardContent>
        <CardFooter className="flex items-center justify-between text-xs text-gray-400">
          <span>Updated: {formatDate(ward.updated_at)}</span>
        </CardFooter>
      </Card>
    </div>
  );
}

export default WardCard;
