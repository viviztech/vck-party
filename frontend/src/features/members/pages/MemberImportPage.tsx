/**
 * Member Import Page
 * Page for bulk importing members
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageHeader } from '@/components/Layout/PageHeader';
import { Card, CardHeader, CardContent, CardFooter } from '@/components/DataDisplay/Card';
import { Button } from '@/components/Form/Button';
import { Alert } from '@/components/Feedback/Alert';
import { membersService, MemberBulkImportResult } from '@/services/membersService';
import { Upload, Download, FileSpreadsheet, CheckCircle, AlertCircle } from 'lucide-react';

export function MemberImportPage() {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<MemberBulkImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) { setFile(selectedFile); setResult(null); setError(null); }
  };

  const handleImport = async () => {
    if (!file) return;
    setImporting(true);
    setProgress(0);
    setError(null);
    try {
      const importResult = await membersService.bulkImportMembers(file, (p) => { setProgress(p); });
      setResult(importResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to import members');
    } finally {
      setImporting(false);
      setProgress(0);
    }
  };

  const handleDownloadTemplate = () => {
    const templateHeaders = ['first_name', 'last_name', 'phone', 'email', 'date_of_birth', 'gender', 'address_line1', 'city', 'district', 'state', 'pincode', 'voter_id', 'blood_group', 'education', 'occupation'];
    const csvContent = templateHeaders.join(',') + '\n';
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'member_import_template.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const resetImport = () => { setFile(null); setResult(null); setError(null); };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <PageHeader title="Import Members" description="Bulk import members from an Excel or CSV file" breadcrumbs={[{ label: 'Members', href: '/members' }, { label: 'Import' }]} />
      <Card>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-primary-100 rounded-lg"><FileSpreadsheet size={24} className="text-primary-600" /></div>
              <div><h3 className="font-medium">Download Import Template</h3><p className="text-sm text-gray-500">Get the correct format for your import file</p></div>
            </div>
            <Button variant="outline" onClick={handleDownloadTemplate} leftIcon={<Download size={16} />}>Download CSV</Button>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader title="Upload File" />
        <CardContent>
          {!result ? (
            <div>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-primary-400 transition-colors">
                <input type="file" accept=".xlsx,.csv" onChange={handleFileChange} className="hidden" id="import-file" />
                <label htmlFor="import-file" className="cursor-pointer">
                  <Upload size={48} className="mx-auto text-gray-400 mb-4" />
                  {file ? (<div><p className="font-medium">{file.name}</p><p className="text-sm text-gray-500">{(file.size / 1024).toFixed(2)} KB</p></div>) : (<div><p className="font-medium">Click to select a file</p><p className="text-sm text-gray-500 mt-1">Supports .xlsx and .csv files</p></div>)}
                </label>
              </div>
              {error && <Alert variant="error" className="mt-4">{error}</Alert>}
              {importing && (
                <div className="mt-4">
                  <div className="flex items-center justify-between text-sm mb-1"><span>Importing...</span><span>{progress}%</span></div>
                  <div className="w-full bg-gray-200 rounded-full h-2"><div className="bg-primary-600 h-2 rounded-full transition-all" style={{ width: `${progress}%` }} /></div>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-center p-6 bg-gray-50 rounded-lg">
                {result.failed === 0 ? <CheckCircle size={48} className="text-success-500" /> : <AlertCircle size={48} className="text-warning-500" />}
                <div className="ml-4 text-center">
                  <p className="text-lg font-medium">{result.failed === 0 ? 'Import Completed Successfully!' : 'Import Completed with Errors'}</p>
                  <p className="text-gray-500">{result.successful} of {result.total} records imported successfully</p>
                </div>
              </div>
            </div>
          )}
        </CardContent>
        <CardFooter className="flex justify-end space-x-3">
          {result ? (<><Button variant="outline" onClick={resetImport}>Import Another File</Button><Button onClick={() => navigate('/members')}>View Members</Button></>) : (<><Button variant="outline" onClick={() => navigate('/members')}>Cancel</Button><Button onClick={handleImport} loading={importing} disabled={!file} leftIcon={<Upload size={16} />}>Import Members</Button></>)}
        </CardFooter>
      </Card>
      <Card>
        <CardHeader title="Import Instructions" />
        <CardContent>
          <ul className="space-y-2 text-sm text-gray-600">
            <li className="flex items-start"><span className="mr-2">1.</span>Download the import template to ensure correct column names</li>
            <li className="flex items-start"><span className="mr-2">2.</span>Fill in the member data in the template. Required fields: first_name, phone</li>
            <li className="flex items-start"><span className="mr-2">3.</span>Save the file as .xlsx or .csv format</li>
            <li className="flex items-start"><span className="mr-2">4.</span>Upload the file and review the import results</li>
            <li className="flex items-start"><span className="mr-2">5.</span>Members with duplicate phone numbers will not be imported</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
export default MemberImportPage;
