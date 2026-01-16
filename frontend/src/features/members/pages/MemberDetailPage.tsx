/**
 * Member Detail Page
 * Displays detailed information about a single member
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { PageHeader } from '@/components/Layout/PageHeader';
import { Card, CardContent, CardFooter } from '@/components/DataDisplay/Card';
import { Avatar } from '@/components/DataDisplay/Avatar';
import { Badge } from '@/components/DataDisplay/Badge';
import { Tabs } from '@/components/DataDisplay/Tabs';
import { Button } from '@/components/Form/Button';
import { membersService, Member, MemberProfile, MemberFamily, MemberDocument, MemberNote, MemberHistory } from '@/services/membersService';
import { Edit, Trash2, Phone, Mail, MapPin, Calendar, User, FileText, Users, History } from 'lucide-react';
import { formatDate } from '@/utils/helpers';

export function MemberDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [member, setMember] = useState<Member | null>(null);
  const [profile, setProfile] = useState<MemberProfile | null>(null);
  const [family, setFamily] = useState<MemberFamily[]>([]);
  const [documents, setDocuments] = useState<MemberDocument[]>([]);
  const [notes, setNotes] = useState<MemberNote[]>([]);
  const [history, setHistory] = useState<MemberHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    if (!id) return;

    const fetchData = async () => {
      setLoading(true);
      try {
        const [memberData, profileData, familyData, documentsData, notesData, historyData] = await Promise.all([
          membersService.getMember(id),
          membersService.getMemberProfile(id).catch(() => null),
          membersService.getMemberFamily(id),
          membersService.getMemberDocuments(id),
          membersService.getMemberNotes(id),
          membersService.getMemberHistory(id),
        ]);
        setMember(memberData);
        setProfile(profileData);
        setFamily(familyData);
        setDocuments(documentsData);
        setNotes(notesData);
        setHistory(historyData);
      } catch (error) {
        console.error('Failed to fetch member:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  const handleDelete = async () => {
    if (!member || !window.confirm('Are you sure you want to delete this member?')) return;
    try {
      await membersService.deleteMember(member.id);
      navigate('/members');
    } catch (error) {
      console.error('Failed to delete member:', error);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse h-8 bg-gray-200 rounded w-1/4"></div>
        <Card>
          <div className="flex items-start space-x-6 p-6">
            <div className="w-24 h-24 bg-gray-200 rounded-full"></div>
            <div className="space-y-3 flex-1">
              <div className="h-6 bg-gray-200 rounded w-1/3"></div>
              <div className="h-4 bg-gray-200 rounded w-1/4"></div>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  if (!member) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-gray-900">Member not found</h2>
        <p className="text-gray-500 mt-2">The member you're looking for doesn't exist.</p>
        <Button variant="outline" className="mt-4" onClick={() => navigate('/members')}>
          Back to Members
        </Button>
      </div>
    );
  }

  const tabs = [
    { key: 'overview', label: 'Overview', icon: <User size={16} /> },
    { key: 'family', label: `Family (${family.length})`, icon: <Users size={16} /> },
    { key: 'documents', label: `Documents (${documents.length})`, icon: <FileText size={16} /> },
    { key: 'notes', label: `Notes (${notes.length})`, icon: <FileText size={16} /> },
    { key: 'history', label: 'History', icon: <History size={16} /> },
  ];

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
    <div className="space-y-6">
      <PageHeader
        title={`${member.first_name} ${member.last_name || ''}`}
        description={`Membership Number: ${member.membership_number}`}
        actions={
          <div className="flex items-center space-x-2">
            <Button variant="outline" leftIcon={<Edit size={16} />} onClick={() => navigate(`/members/${member.id}/edit`)}>
              Edit
            </Button>
            <Button variant="danger" leftIcon={<Trash2 size={16} />} onClick={handleDelete}>
              Delete
            </Button>
          </div>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Card */}
        <div className="lg:col-span-1">
          <Card>
            <CardContent className="text-center">
              <Avatar
                src={member.photo_url}
                name={`${member.first_name} ${member.last_name || ''}`}
                size="xl"
                className="mx-auto mb-4"
              />
              <h2 className="text-xl font-semibold text-gray-900">
                {member.first_name} {member.last_name}
              </h2>
              <p className="text-gray-500">{member.email}</p>
              <div className="mt-4 flex justify-center">
                {getStatusBadge(member.status)}
              </div>
            </CardContent>
            <CardFooter className="flex-col items-stretch space-y-3">
              {member.phone && (
                <a href={`tel:${member.phone}`} className="flex items-center text-gray-600 hover:text-gray-900">
                  <Phone size={16} className="mr-2" />
                  {member.phone}
                </a>
              )}
              {member.email && (
                <a href={`mailto:${member.email}`} className="flex items-center text-gray-600 hover:text-gray-900">
                  <Mail size={16} className="mr-2" />
                  {member.email}
                </a>
              )}
              {(member.city || member.district) && (
                <div className="flex items-start text-gray-600">
                  <MapPin size={16} className="mr-2 mt-0.5" />
                  <span>
                    {[member.address_line1, member.city, member.district, member.state]
                      .filter(Boolean)
                      .join(', ')}
                  </span>
                </div>
              )}
              {member.date_of_birth && (
                <div className="flex items-center text-gray-600">
                  <Calendar size={16} className="mr-2" />
                  DOB: {formatDate(member.date_of_birth)}
                </div>
              )}
            </CardFooter>
          </Card>
        </div>

        {/* Details */}
        <div className="lg:col-span-2">
          <Card padding="none">
            <div className="p-4 border-b border-gray-200">
              <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />
            </div>

            <div className="p-6">
              {activeTab === 'overview' && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h3 className="font-semibold text-gray-900">Personal Information</h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">First Name</span>
                        <p className="font-medium">{member.first_name}</p>
                      </div>
                      {member.last_name && (
                        <div>
                          <span className="text-gray-500">Last Name</span>
                          <p className="font-medium">{member.last_name}</p>
                        </div>
                      )}
                      <div>
                        <span className="text-gray-500">Phone</span>
                        <p className="font-medium">{member.phone}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Email</span>
                        <p className="font-medium">{member.email || '-'}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Gender</span>
                        <p className="font-medium">{member.gender || '-'}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Blood Group</span>
                        <p className="font-medium">{member.blood_group || '-'}</p>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="font-semibold text-gray-900">Address</h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div className="col-span-2">
                        <span className="text-gray-500">Address</span>
                        <p className="font-medium">
                          {[member.address_line1, member.address_line2].filter(Boolean).join(', ') || '-'}
                        </p>
                      </div>
                      <div>
                        <span className="text-gray-500">City</span>
                        <p className="font-medium">{member.city || '-'}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">District</span>
                        <p className="font-medium">{member.district || '-'}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">State</span>
                        <p className="font-medium">{member.state || '-'}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Pincode</span>
                        <p className="font-medium">{member.pincode || '-'}</p>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="font-semibold text-gray-900">Professional</h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Education</span>
                        <p className="font-medium">{member.education || '-'}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Occupation</span>
                        <p className="font-medium">{member.occupation || '-'}</p>
                      </div>
                      {member.organization && (
                        <div className="col-span-2">
                          <span className="text-gray-500">Organization</span>
                          <p className="font-medium">{member.organization}</p>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="font-semibold text-gray-900">Membership</h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Membership Type</span>
                        <p className="font-medium">{member.membership_type}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Joined Date</span>
                        <p className="font-medium">{formatDate(member.joined_at)}</p>
                      </div>
                      {member.voter_id && (
                        <div>
                          <span className="text-gray-500">Voter ID</span>
                          <p className="font-medium">{member.voter_id}</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'family' && (
                <div className="space-y-4">
                  {family.length === 0 ? (
                    <p className="text-gray-500 text-center py-8">No family relationships added</p>
                  ) : (
                    family.map((relation) => (
                      <div key={relation.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                        <div className="flex items-center space-x-4">
                          <Avatar
                            src={relation.related_member.photo_url}
                            name={`${relation.related_member.first_name} ${relation.related_member.last_name || ''}`}
                            size="md"
                          />
                          <div>
                            <Link to={`/members/${relation.related_member_id}`} className="font-medium hover:text-primary-600">
                              {relation.related_member.first_name} {relation.related_member.last_name || ''}
                            </Link>
                            <p className="text-sm text-gray-500">{relation.related_member.phone}</p>
                          </div>
                        </div>
                        <Badge>{relation.relationship_type}</Badge>
                      </div>
                    ))
                  )}
                  <Button variant="outline" className="w-full" onClick={() => navigate(`/members/${member.id}/family`)}>
                    Manage Family Tree
                  </Button>
                </div>
              )}

              {activeTab === 'documents' && (
                <div className="space-y-4">
                  {documents.length === 0 ? (
                    <p className="text-gray-500 text-center py-8">No documents uploaded</p>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {documents.map((doc) => (
                        <div key={doc.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                          <div className="flex items-center space-x-3">
                            <FileText size={20} className="text-gray-400" />
                            <div>
                              <p className="font-medium">{doc.file_name}</p>
                              <p className="text-sm text-gray-500">{doc.document_type}</p>
                            </div>
                          </div>
                          <Badge variant={doc.is_verified ? 'success' : 'warning'}>
                            {doc.is_verified ? 'Verified' : 'Pending'}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  )}
                  <Button variant="outline" className="w-full" onClick={() => navigate(`/members/${member.id}/documents`)}>
                    Manage Documents
                  </Button>
                </div>
              )}

              {activeTab === 'notes' && (
                <div className="space-y-4">
                  {notes.length === 0 ? (
                    <p className="text-gray-500 text-center py-8">No notes added</p>
                  ) : (
                    notes.map((note) => (
                      <div key={note.id} className="p-4 bg-gray-50 rounded-lg">
                        {note.title && <h4 className="font-medium mb-2">{note.title}</h4>}
                        <p className="text-gray-700">{note.content}</p>
                        <p className="text-sm text-gray-500 mt-2">
                          {note.author_name && `By ${note.author_name} • `}
                          {formatDate(note.created_at)}
                        </p>
                      </div>
                    ))
                  )}
                </div>
              )}

              {activeTab === 'history' && (
                <div className="space-y-4">
                  {history.length === 0 ? (
                    <p className="text-gray-500 text-center py-8">No history available</p>
                  ) : (
                    <div className="space-y-3">
                      {history.map((item) => (
                        <div key={item.id} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                          <div className="flex-1">
                            <p className="font-medium">{item.action}</p>
                            {item.action_description && (
                              <p className="text-sm text-gray-600">{item.action_description}</p>
                            )}
                            <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                              {item.performed_by_name && <span>By {item.performed_by_name}</span>}
                              <span>{formatDate(item.created_at)}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default MemberDetailPage;
