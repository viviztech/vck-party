/**
 * District Card Component
 * Card view for displaying district information
 */

import React from 'react';
import { Card, CardContent, CardFooter } from '@/components/DataDisplay/Card';
import { Badge } from '@/components/DataDisplay/Badge';
import { MapPin, Building2, Users } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import type { District } from '@/services/hierarchyService';
import { formatDate } from '@/utils/helpers';
import { cn } from '@/utils/helpers';

interface DistrictCardProps {
  district: District;
  onClick?: () => void;
  showConstituencies?: boolean;
  memberCount?: number;
}

export function DistrictCard({ district, onClick, showConstituencies = true, memberCount }: DistrictCardProps) {
  const navigate = useNavigate();

  const handleClick = () => {
    if (onClick) {
      onClick();
    } else {
      navigate(`/hierarchy/districts/${district.id}`);
    }
  };

  const getStatusBadge = () => {
    if (district.is_active) {
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
              <div className="p-2 bg-blue-100 rounded-lg">
                <MapPin className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">{district.name}</h3>
                <p className="text-sm text-gray-500">{district.code}</p>
              </div>
            </div>
            {getStatusBadge()}
          </div>

          {district.name_ta && (
            <p className="text-sm text-gray-600 font-medium">{district.name_ta}</p>
          )}

          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center text-gray-500">
              <Building2 size={14} className="mr-1" />
              <span>{district.constituencies_count} Constituencies</span>
            </div>
            <span className="text-gray-400">{district.state}</span>
          </div>

          {memberCount !== undefined && (
            <div className="flex items-center text-sm text-gray-500">
              <Users size={14} className="mr-1" />
              <span>{memberCount.toLocaleString()} Members</span>
            </div>
          )}
        </CardContent>
        <CardFooter className="flex items-center justify-between text-xs text-gray-400">
          <span>Updated: {formatDate(district.updated_at)}</span>
        </CardFooter>
      </Card>
    </div>
  );
}

export default DistrictCard;
