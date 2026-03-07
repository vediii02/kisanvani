import React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Shield, Building2, UserCog, User } from 'lucide-react';

export default function TopHeader() {
    const { user } = useAuth();

    const getRoleIcon = () => {
        switch (user?.role) {
            case 'superadmin':
            case 'admin':
                return <Shield className="h-5 w-5 text-secondary" />;
            case 'organisation':
            case 'organisation_admin':
                return <Building2 className="h-5 w-5 text-secondary" />;
            case 'company':
                return <UserCog className="h-5 w-5 text-secondary" />;
            default:
                return <User className="h-5 w-5 text-secondary" />;
        }
    };

    const getRoleLabel = () => {
        switch (user?.role) {
            case 'superadmin':
                return 'Super Admin Portal';
            case 'admin':
                return 'Admin Portal';
            case 'organisation':
            case 'organisation_admin':
                return 'Organisation Portal';
            case 'company':
                return 'Company Portal';
            default:
                return 'User Portal';
        }
    };

    return (
        <header className="h-16 bg-white border-b border-gray-200 fixed top-0 right-0 left-64 z-30 flex items-center justify-between px-8 border-t-4 border-t-secondary">
            <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                    <div className="bg-primary/10 p-1.5 rounded-lg">
                        {getRoleIcon()}
                    </div>
                    <div>
                        <h1 className="text-xl font-bold text-gray-900 leading-tight tracking-tight">Kisan Vani AI</h1>
                        <p className="text-xs text-gray-500 font-medium">Voice Advisory Platform</p>
                    </div>
                </div>
            </div>

            <div className="flex items-center gap-4">
                <div className="h-8 w-px bg-gray-200 mx-2"></div>
                <div className="flex flex-col items-end">
                    <span className="text-sm font-semibold text-gray-900">{user?.full_name || user?.username}</span>
                    <span className="text-[10px] text-gray-500 capitalize">{user?.role?.replace('_', ' ')}</span>
                </div>
                <div className="h-10 w-10 rounded-full bg-secondary/10 flex items-center justify-center border border-secondary/20">
                    <User className="h-6 w-6 text-secondary" />
                </div>
            </div>
        </header>
    );
}
