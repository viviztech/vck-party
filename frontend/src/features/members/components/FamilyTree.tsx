/**
 * Family Tree Component
 * Visualizes family relationships in a tree format
 */

import React, { useState } from 'react';
import { Card, CardHeader, CardContent } from '@/components/DataDisplay/Card';
import { Avatar } from '@/components/DataDisplay/Avatar';
import { Badge } from '@/components/DataDisplay/Badge';
import { Button } from '@/components/Form/Button';
import type { MemberFamily } from '@/services/membersService';
import { ZoomIn, ZoomOut, RefreshCw, Users } from 'lucide-react';

interface FamilyTreeProps {
  family: MemberFamily[];
  memberId: string;
}

export function FamilyTree({ family, memberId }: FamilyTreeProps) {
  const [zoom, setZoom] = useState(1);

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.2, 2));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.2, 0.5));
  const handleReset = () => setZoom(1);

  const parents = family.filter(f => ['father', 'mother'].includes(f.relationship_type));
  const siblings = family.filter(f => ['brother', 'sister'].includes(f.relationship_type));
  const spouse = family.find(f => f.relationship_type === 'spouse');
  const children = family.filter(f => ['son', 'daughter'].includes(f.relationship_type));

  if (family.length === 0) {
    return (
      <Card>
        <CardContent className="text-center py-12">
          <Users size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">No family relationships to display</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader
        title="Family Tree"
        action={
          <div className="flex items-center space-x-2">
            <Button variant="ghost" size="sm" onClick={handleZoomOut} disabled={zoom <= 0.5}>
              <ZoomOut size={16} />
            </Button>
            <span className="text-sm text-gray-500">{Math.round(zoom * 100)}%</span>
            <Button variant="ghost" size="sm" onClick={handleZoomIn} disabled={zoom >= 2}>
              <ZoomIn size={16} />
            </Button>
            <Button variant="ghost" size="sm" onClick={handleReset}>
              <RefreshCw size={16} />
            </Button>
          </div>
        }
      />
      <CardContent>
        <div className="overflow-auto" style={{ transform: `scale(${zoom})`, transformOrigin: 'top left' }}>
          <div className="min-w-[600px] p-4">
            <div className="flex flex-col items-center">
              {parents.length > 0 && (
                <div className="flex space-x-8 mb-8">
                  {parents.map((parent) => (
                    <div key={parent.id} className="text-center">
                      <Avatar src={parent.related_member.photo_url} name={`${parent.related_member.first_name} ${parent.related_member.last_name || ''}`} size="lg" />
                      <p className="mt-2 font-medium text-sm">{parent.related_member.first_name} {parent.related_member.last_name || ''}</p>
                      <Badge size="sm">{parent.relationship_type}</Badge>
                    </div>
                  ))}
                </div>
              )}

              {(parents.length > 0 || spouse) && <div className="w-px h-8 bg-gray-300" />}

              <div className="flex items-center space-x-8 mb-8">
                {spouse && (
                  <div className="text-center">
                    <Avatar src={spouse.related_member.photo_url} name={`${spouse.related_member.first_name} ${spouse.related_member.last_name || ''}`} size="lg" />
                    <p className="mt-2 font-medium text-sm">{spouse.related_member.first_name} {spouse.related_member.last_name || ''}</p>
                    <Badge size="sm">{spouse.relationship_type}</Badge>
                  </div>
                )}
                <div className="w-px h-12 bg-gray-300" />
                <div className="text-center border-2 border-primary-500 rounded-lg p-4">
                  <Avatar name="You" size="lg" />
                  <p className="mt-2 font-medium text-sm">You</p>
                </div>
                {siblings.length > 0 && <div className="w-px h-12 bg-gray-300" />}
                {siblings.length > 0 && (
                  <div className="flex space-x-4">
                    {siblings.map((sibling) => (
                      <div key={sibling.id} className="text-center">
                        <Avatar src={sibling.related_member.photo_url} name={`${sibling.related_member.first_name} ${sibling.related_member.last_name || ''}`} size="lg" />
                        <p className="mt-2 font-medium text-sm truncate max-w-[100px]">{sibling.related_member.first_name}</p>
                        <Badge size="sm">{sibling.relationship_type}</Badge>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {children.length > 0 && <div className="w-px h-8 bg-gray-300" />}

              {children.length > 0 && (
                <div className="flex space-x-8">
                  {children.map((child) => (
                    <div key={child.id} className="text-center">
                      <Avatar src={child.related_member.photo_url} name={`${child.related_member.first_name} ${child.related_member.last_name || ''}`} size="lg" />
                      <p className="mt-2 font-medium text-sm">{child.related_member.first_name} {child.related_member.last_name || ''}</p>
                      <Badge size="sm">{child.relationship_type}</Badge>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default FamilyTree;
