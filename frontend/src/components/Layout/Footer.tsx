import React from 'react';

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-white border-t border-gray-200 py-4 px-6">
      <div className="flex flex-col sm:flex-row items-center justify-between gap-2">
        <p className="text-sm text-gray-500">
          © {currentYear} VCK Platform. All rights reserved.
        </p>
        <div className="flex items-center space-x-4 text-sm text-gray-500">
          <a href="/privacy" className="hover:text-gray-700">
            Privacy Policy
          </a>
          <a href="/terms" className="hover:text-gray-700">
            Terms of Service
          </a>
          <a href="/contact" className="hover:text-gray-700">
            Contact
          </a>
        </div>
      </div>
    </footer>
  );
}
