/**
 * Document Upload Component
 * Upload component for member documents
 */

import React, { useState } from 'react';
import { Button } from '@/components/Form/Button';
import { Select } from '@/components/Form/Select';
import { Progress } from '@/components/DataDisplay/Progress';
import { Upload, File, X, CheckCircle } from 'lucide-react';

interface DocumentUploadProps {
  onUpload: (file: File, documentType: string) => Promise<void>;
  uploading: boolean;
  progress: number;
  documentTypes: { value: string; label: string }[];
}

export function DocumentUpload({ onUpload, uploading, progress, documentTypes }: DocumentUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [documentType, setDocumentType] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
    }
  };

  const handleUpload = async () => {
    if (!file || !documentType) return;
    await onUpload(file, documentType);
    setFile(null);
    setDocumentType('');
  };

  const handleRemove = () => {
    setFile(null);
  };

  return (
    <div className="space-y-4">
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-primary-400 transition-colors">
        <input type="file" accept=".png,.jpg,.jpeg,.gif,.pdf,.doc,.docx" onChange={handleFileChange} className="hidden" id="document-upload" />
        <label htmlFor="document-upload" className="cursor-pointer">
          <Upload size={32} className="mx-auto text-gray-400 mb-2" />
          {file ? (
            <div className="flex items-center justify-center space-x-2">
              <File size={20} className="text-gray-500" />
              <span className="font-medium">{file.name}</span>
              <button onClick={(e) => { e.preventDefault(); handleRemove(); }} className="text-gray-400 hover:text-gray-600">
                <X size={16} />
              </button>
            </div>
          ) : (
            <div>
              <p className="font-medium">Click to select a file</p>
              <p className="text-sm text-gray-500 mt-1">Supports: PNG, JPG, PDF, DOC, DOCX</p>
            </div>
          )}
        </label>
      </div>

      <Select
        label="Document Type"
        placeholder="Select document type"
        options={documentTypes}
        value={documentType}
        onChange={(value) => setDocumentType(value as string)}
      />

      {uploading && (
        <div className="space-y-2">
          <Progress value={progress} max={100} />
          <p className="text-sm text-gray-500 text-center">Uploading... {progress}%</p>
        </div>
      )}

      <Button
        onClick={handleUpload}
        disabled={!file || !documentType || uploading}
        loading={uploading}
        leftIcon={<CheckCircle size={16} />}
        fullWidth
      >
        Upload Document
      </Button>
    </div>
  );
}

export default DocumentUpload;
