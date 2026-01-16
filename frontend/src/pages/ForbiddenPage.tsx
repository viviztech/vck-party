/**
 * Forbidden Page (403)
 * Displayed when user doesn't have permission to access a resource
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { Lock, Home } from 'lucide-react';

export function ForbiddenPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
      <div className="text-center">
        <div className="mb-8">
          <Lock className="w-24 h-24 text-orange-500 mx-auto" />
        </div>
        
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Access Forbidden
        </h1>
        
        <p className="text-lg text-gray-600 mb-8 max-w-md mx-auto">
          You don't have permission to access this page. If you believe this is 
          an error, please contact your administrator.
        </p>
        
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            to="/dashboard"
            className="flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            <Home size={20} />
            Go to Dashboard
          </Link>
          
          <button
            onClick={() => window.history.back()}
            className="flex items-center gap-2 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    </div>
  );
}

export default ForbiddenPage;
