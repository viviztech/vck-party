/**
 * Booth Card Component
 * Card view for displaying booth information
 */

import React from 'react';
import { Card, CardContent, CardFooter } from '@/components/DataDisplay/Card';
import { Badge } from '@/components/DataDisplay/Badge';
import { Users, MapPin, Navigation } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import type { Booth } from '@/services/hierarchyService';
import { formatDate } from '@/utils/helpers';
import { cn } from '@/utils/helpers';

interface BoothCardProps {
  booth: Booth;
  onClick?: () => void;
  memberCount?: number;
}

export function BoothCard({ booth, onClick, memberCount }: BoothCardProps) {
  const navigate = useNavigate();

  const handleClick = () => {
    if (onClick) {
      onClick();
    } else {
      navigate(`/hierarchy/booths/${booth.id}`);
    }
  };

  const getStatusBadge = () => {
    if (booth.is_active) {
      return <Badge variant="success">Active</Badge>;
    }
    return <Badge variant="default">Inactive</Badge>;
  };

  const totalVoters = (booth.male_voters || 0) + (booth.female_voters || 0) + (booth.other_voters || 0);

  return (
    <div onClick={handleClick} className={cn(onClick ? 'cursor-pointer' : '')}>
      <Card hover={!!onClick || true}>
        <CardContent className="space-y-4">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-emerald-100 rounded-lg">
                <MapPin className="w-5 h-5 text-emerald-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">{booth.name}</h3>
                <p className="text-sm text-gray-500">{booth.code}</p>
              </div>
            </div>
            {getStatusBadge()}
          </div>

          {booth.name_ta && (
            <p className="text-sm text-gray-600 font-medium">{booth.name_ta}</p>
          )}

          {booth.address && (
            <p className="text-sm text-gray-500 line-clamp-2">{booth.address}</p>
          )}

          <div className="space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-gray-500">Total Voters</span>
              <span className="font-medium">{totalVoters.toLocaleString()}</span>
            </div>
            {booth.male_voters !== undefined && booth.female_voters !== undefined && (
              <div className="flex items-center justify-between text-xs text-gray-400">
                <span>M: {booth.male_voters.toLocaleString()}</span>
                <span>F: {booth.female_voters.toLocaleString()}</span>
                <span>O: {(booth.other_voters || 0).toLocaleString()}</span>
              </div>
            )}
          </div>

          {booth.polling_location_name && (
            <div className="flex items-start text-sm text-gray-500">
              <Navigation size={14} className="mr-1 mt-0.5 flex-shrink-0" />
              <span>{booth.polling_location_name}</span>
            </div>
          )}

          {memberCount !== undefined && (
            <div className="flex items-center text-sm text-gray-500">
              <Users size={14} className="mr-1" />
              <span>{memberCount.toLocaleString()} Members</span>
            </div>
          )}
        </CardContent>
        <CardFooter className="flex items-center justify-between text-xs text-gray-400">
          <span>Updated: {formatDate(booth.updated_at)}</span>
        </CardFooter>
      </Card>
    </div>
  );
}

export default BoothCard;
