/**
 * Constituency Card Component
 * Card view for displaying constituency information
 */

import React from 'react';
import { Card, CardContent, CardFooter } from '@/components/DataDisplay/Card';
import { Badge } from '@/components/DataDisplay/Badge';
import { Building2, Users, MapPin } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import type { Constituency } from '@/services/hierarchyService';
import { formatDate } from '@/utils/helpers';
import { cn } from '@/utils/helpers';

interface ConstituencyCardProps {
  constituency: Constituency;
  onClick?: () => void;
  showWards?: boolean;
  memberCount?: number;
}

export function ConstituencyCard({ constituency, onClick, showWards = true, memberCount }: ConstituencyCardProps) {
  const navigate = useNavigate();

  const handleClick = () => {
    if (onClick) {
      onClick();
    } else {
      navigate(`/hierarchy/constituencies/${constituency.id}`);
    }
  };

  const getStatusBadge = () => {
    if (constituency.is_active) {
      return <Badge variant="success">Active</Badge>;
    }
    return <Badge variant="default">Inactive</Badge>;
  };

  const getTypeBadge = () => {
    const typeConfig: Record<string, { variant: 'info' | 'warning' | 'default'; label: string }> = {
      'assembly': { variant: 'info', label: 'Assembly' },
      'parliamentary': { variant: 'warning', label: 'Parliamentary' },
      'local': { variant: 'default', label: 'Local' },
    };
    const config = typeConfig[constituency.constituency_type] || { variant: 'default', label: constituency.constituency_type };
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  return (
    <div onClick={handleClick} className={cn(onClick ? 'cursor-pointer' : '')}>
      <Card hover={!!onClick || true}>
        <CardContent className="space-y-4">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-indigo-100 rounded-lg">
                <Building2 className="w-5 h-5 text-indigo-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">{constituency.name}</h3>
                <p className="text-sm text-gray-500">{constituency.code}</p>
              </div>
            </div>
            <div className="flex flex-col items-end gap-1">
              {getStatusBadge()}
              {getTypeBadge()}
            </div>
          </div>

          {constituency.name_ta && (
            <p className="text-sm text-gray-600 font-medium">{constituency.name_ta}</p>
          )}

          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="flex items-center text-gray-500">
              <MapPin size={14} className="mr-1" />
              <span>{constituency.wards_count} Wards</span>
            </div>
            {constituency.electorate_count && (
              <div className="flex items-center text-gray-500">
                <Users size={14} className="mr-1" />
                <span>{(constituency.electorate_count).toLocaleString()} Electors</span>
              </div>
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
          <span>Updated: {formatDate(constituency.updated_at)}</span>
        </CardFooter>
      </Card>
    </div>
  );
}

export default ConstituencyCard;
