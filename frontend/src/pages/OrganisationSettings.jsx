// Organisation Admin Settings Page
import React from 'react';
import { Settings, User, Lock, Bell, Shield } from 'lucide-react';
import PasswordUpdateForm from '../components/PasswordUpdateForm';

const OrganisationSettings = () => {
  return (
    <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex items-center gap-4">
        <div className="p-3 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-lg">
          <Settings className="h-8 w-8 text-white" />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600 mt-1">Manage your account and preferences</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Settings Navigation */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl shadow-lg overflow-hidden">
            <div className="p-4 bg-gradient-to-r from-indigo-500 to-purple-600">
              <h2 className="text-white font-semibold text-lg">Settings Menu</h2>
            </div>
            <nav className="p-2">
              <a 
                href="#security" 
                className="flex items-center gap-3 p-3 rounded-lg hover:bg-indigo-50 text-indigo-600 bg-indigo-50 font-medium transition-all"
              >
                <Lock className="h-5 w-5" />
                Security
              </a>
              <a 
                href="#profile" 
                className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 text-gray-700 transition-all"
              >
                <User className="h-5 w-5" />
                Profile
              </a>
              <a 
                href="#notifications" 
                className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 text-gray-700 transition-all"
              >
                <Bell className="h-5 w-5" />
                Notifications
              </a>
              <a 
                href="#privacy" 
                className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 text-gray-700 transition-all"
              >
                <Shield className="h-5 w-5" />
                Privacy
              </a>
            </nav>
          </div>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-2">
          <div id="security" className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Security Settings</h2>
            <PasswordUpdateForm />
          </div>

          <div id="profile" className="mb-8">
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4">Profile Information</h3>
              <p className="text-gray-600">Profile settings coming soon...</p>
            </div>
          </div>

          <div id="notifications" className="mb-8">
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4">Notification Preferences</h3>
              <p className="text-gray-600">Notification settings coming soon...</p>
            </div>
          </div>

          <div id="privacy" className="mb-8">
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4">Privacy Settings</h3>
              <p className="text-gray-600">Privacy settings coming soon...</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OrganisationSettings;
