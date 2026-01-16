/**
 * Member Documents Page
 * Page for managing member documents
 */

import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { PageHeader } from '@/components/Layout/PageHeader';
import { Card, CardHeader, CardContent, CardFooter } from '@/components/DataDisplay/Card';
import { Badge } from '@/components/DataDisplay/Badge';
import { Button } from '@/components/Form/Button';
import { membersService, MemberDocument } from '@/services/membersService';
import { DocumentUpload } from '../components/DocumentUpload';
import { FileText, Download, Trash2, File } from 'lucide-react';
import { formatDate } from '@/utils/helpers';
import { Spinner } from '@/components/Feedback/Spinner';

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export function MemberDocumentsPage() {
  const { id } = useParams<{ id: string }>();
  const [documents, setDocuments] = useState<MemberDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  useEffect(() => {
    if (!id) return;
    fetchDocuments();
  }, [id]);

  const fetchDocuments = async () => {
    try {
      const docs = await membersService.getMemberDocuments(id!);
      setDocuments(docs);
    } catch (error) {
      console.error('Failed to fetch documents:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (file: File, documentType: string) => {
    if (!id) return;
    setUploading(true);
    setUploadProgress(0);
    try {
      await membersService.uploadDocument(id, file, (progress) => { setUploadProgress(progress); });
      fetchDocuments();
    } catch (error) {
      console.error('Failed to upload document:', error);
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleDelete = async (documentId: string) => {
    if (!id || !window.confirm('Are you sure you want to delete this document?')) return;
    try {
      await membersService.deleteMemberDocument(id, documentId);
      fetchDocuments();
    } catch (error) {
      console.error('Failed to delete document:', error);
    }
  };

  const handleDownload = (doc: MemberDocument) => {
    if (doc.file_url) window.open(doc.file_url, '_blank');
  };

  if (loading) {
    return <div className="flex items-center justify-center min-h-[400px]"><Spinner size="lg" /></div>;
  }

  const documentTypes = [
    { value: 'id_proof', label: 'ID Proof' }, { value: 'address_proof', label: 'Address Proof' }, { value: 'photo', label: 'Photo' },
    { value: 'membership_form', label: 'Membership Form' }, { value: 'recommendation_letter', label: 'Recommendation Letter' }, { value: 'other', label: 'Other' },
  ];

  const getDocumentIcon = (mimeType?: string) => {
    if (mimeType?.startsWith('image/')) return <FileText size={24} className="text-primary-500" />;
    return <File size={24} className="text-gray-500" />;
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <PageHeader title="Documents" description="Manage member documents" breadcrumbs={[{ label: 'Members', href: '/members' }, { label: id || '', href: `/members/${id}` }, { label: 'Documents' }]} />
      <Card>
        <CardHeader title="Upload Document" />
        <CardContent><DocumentUpload onUpload={handleUpload} uploading={uploading} progress={uploadProgress} documentTypes={documentTypes} /></CardContent>
      </Card>
      <Card>
        <CardHeader title="All Documents" subtitle={`${documents.length} documents`} />
        <CardContent>
          {documents.length === 0 ? (
            <div className="text-center py-8"><FileText size={48} className="mx-auto text-gray-300 mb-4" /><p className="text-gray-500">No documents uploaded yet</p></div>
          ) : (
            <div className="space-y-3">
              {documents.map((doc) => (
                <div key={doc.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-4">
                    {getDocumentIcon(doc.mime_type)}
                    <div>
                      <p className="font-medium">{doc.file_name}</p>
                      <div className="flex items-center space-x-3 text-sm text-gray-500">
                        <Badge variant="default">{doc.document_type.replace(/_/g, ' ')}</Badge>
                        {doc.file_size && <span>{formatFileSize(doc.file_size)}</span>}
                        <span>Uploaded {formatDate(doc.created_at)}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant={doc.is_verified ? 'success' : 'warning'}>{doc.is_verified ? 'Verified' : 'Pending'}</Badge>
                    <Button variant="ghost" size="sm" onClick={() => handleDownload(doc)}><Download size={16} /></Button>
                    <Button variant="ghost" size="sm" onClick={() => handleDelete(doc.id)}><Trash2 size={16} className="text-error-500" /></Button>
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
export default MemberDocumentsPage;
