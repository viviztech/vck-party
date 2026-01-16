/**
 * Member Family Page
 * Page for viewing and editing member's family tree
 */

import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { PageHeader } from '@/components/Layout/PageHeader';
import { Card, CardHeader, CardContent, CardFooter } from '@/components/DataDisplay/Card';
import { Avatar } from '@/components/DataDisplay/Avatar';
import { Badge } from '@/components/DataDisplay/Badge';
import { Button } from '@/components/Form/Button';
import { Select } from '@/components/Form/Select';
import { Input } from '@/components/Form/Input';
import { membersService, MemberFamily, Member } from '@/services/membersService';
import { Plus, Trash2, Users, Search } from 'lucide-react';
import { Spinner } from '@/components/Feedback/Spinner';

export function MemberFamilyPage() {
  const { id } = useParams<{ id: string }>();
  const [family, setFamily] = useState<MemberFamily[]>([]);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [searchResults, setSearchResults] = useState<Member[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [newRelation, setNewRelation] = useState({ related_member_id: '', relationship_type: 'spouse', notes: '' });

  useEffect(() => {
    if (!id) return;
    fetchFamily();
  }, [id]);

  const fetchFamily = async () => {
    try {
      const familyData = await membersService.getMemberFamily(id!);
      setFamily(familyData);
    } catch (error) {
      console.error('Failed to fetch family:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (query: string) => {
    setSearchQuery(query);
    if (query.length < 2) { setSearchResults([]); return; }
    try {
      const results = await membersService.searchMembers(query);
      setSearchResults(results.filter(m => m.id !== id));
    } catch (error) {
      console.error('Failed to search members:', error);
    }
  };

  const handleAddRelation = async () => {
    if (!id || !newRelation.related_member_id) return;
    setAdding(true);
    try {
      await membersService.addMemberFamily(id, newRelation);
      setNewRelation({ related_member_id: '', relationship_type: 'spouse', notes: '' });
      setSearchQuery('');
      setSearchResults([]);
      fetchFamily();
    } catch (error) {
      console.error('Failed to add relation:', error);
    } finally {
      setAdding(false);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center min-h-[400px]"><Spinner size="lg" /></div>;
  }

  const relationshipTypes = [
    { value: 'spouse', label: 'Spouse' }, { value: 'father', label: 'Father' }, { value: 'mother', label: 'Mother' },
    { value: 'son', label: 'Son' }, { value: 'daughter', label: 'Daughter' }, { value: 'brother', label: 'Brother' },
    { value: 'sister', label: 'Sister' }, { value: 'grandfather', label: 'Grandfather' }, { value: 'grandmother', label: 'Grandmother' },
    { value: 'grandson', label: 'Grandson' }, { value: 'granddaughter', label: 'Granddaughter' }, { value: 'uncle', label: 'Uncle' },
    { value: 'aunt', label: 'Aunt' }, { value: 'nephew', label: 'Nephew' }, { value: 'niece', label: 'Niece' }, { value: 'cousin', label: 'Cousin' },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <PageHeader title="Family Tree" description="Manage family relationships" breadcrumbs={[{ label: 'Members', href: '/members' }, { label: id || '', href: `/members/${id}` }, { label: 'Family' }]} />
      <Card>
        <CardHeader title="Add Family Member" />
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="relative">
              <Input label="Search Member" placeholder="Search by name or phone..." value={searchQuery} onChange={(e) => handleSearch(e.target.value)} leftIcon={<Search size={16} />} />
              {searchResults.length > 0 && (
                <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                  {searchResults.map((member) => (
                    <div key={member.id} className={`flex items-center space-x-3 p-3 cursor-pointer hover:bg-gray-50 ${newRelation.related_member_id === member.id ? 'bg-primary-50' : ''}`} onClick={() => setNewRelation({ ...newRelation, related_member_id: member.id })}>
                      <Avatar src={member.photo_url} name={`${member.first_name} ${member.last_name || ''}`} size="sm" />
                      <div><p className="font-medium">{member.first_name} {member.last_name}</p><p className="text-sm text-gray-500">{member.phone}</p></div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <Select label="Relationship Type" options={relationshipTypes} value={newRelation.relationship_type} onChange={(value) => setNewRelation({ ...newRelation, relationship_type: value as string })} />
          </div>
          <Input label="Notes (optional)" placeholder="Add any notes about this relationship" value={newRelation.notes} onChange={(e) => setNewRelation({ ...newRelation, notes: e.target.value })} />
        </CardContent>
        <CardFooter><Button onClick={handleAddRelation} loading={adding} disabled={!newRelation.related_member_id} leftIcon={<Plus size={16} />}>Add Relationship</Button></CardFooter>
      </Card>
      <Card>
        <CardHeader title="Family Members" subtitle={`${family.length} relationships`} />
        <CardContent>
          {family.length === 0 ? (
            <div className="text-center py-8"><Users size={48} className="mx-auto text-gray-300 mb-4" /><p className="text-gray-500">No family relationships added yet</p></div>
          ) : (
            <div className="space-y-4">
              {family.map((relation) => (
                <div key={relation.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <Avatar src={relation.related_member.photo_url} name={`${relation.related_member.first_name} ${relation.related_member.last_name || ''}`} size="md" />
                    <div>
                      <Link to={`/members/${relation.related_member_id}`} className="font-medium hover:text-primary-600">{relation.related_member.first_name} {relation.related_member.last_name || ''}</Link>
                      <p className="text-sm text-gray-500">{relation.related_member.phone}</p>
                      {relation.notes && <p className="text-sm text-gray-400 mt-1">{relation.notes}</p>}
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <Badge>{relation.relationship_type.replace(/_/g, ' ')}</Badge>
                    <Button variant="ghost" size="sm"><Trash2 size={16} className="text-error-500" /></Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
export default MemberFamilyPage;
