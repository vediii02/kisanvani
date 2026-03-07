import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';
import { Loader2, Leaf, ShieldCheck, Eye, EyeOff } from 'lucide-react';
import { toast } from 'sonner';
import api from '../api/api';

export default function ResetPassword() {
    const { token } = useParams();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [formData, setFormData] = useState({
        newPassword: '',
        confirmPassword: ''
    });

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (formData.newPassword !== formData.confirmPassword) {
            toast.error('Passwords do not match');
            return;
        }

        setLoading(true);

        try {
            await api.post('/auth/reset-password', {
                token,
                new_password: formData.newPassword
            });

            toast.success('Password reset successfully!');
            setTimeout(() => navigate('/login'), 2000);
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Invalid or expired reset token.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-background p-4">
            <div className="w-full max-w-md">
                <div className="text-center mb-8">
                    <div className="flex items-center justify-center gap-2 mb-4">
                        <div className="w-12 h-12 bg-green-600 rounded-full flex items-center justify-center shadow-md">
                            <Leaf className="w-7 h-7 text-white" />
                        </div>
                    </div>
                    <h1 className="text-4xl font-bold tracking-tight">Kisan Vani AI</h1>
                    <p className="text-muted-foreground mt-2">Voice Advisory Platform for Farmers</p>
                </div>

                <Card className="p-8 border border-border/60 shadow-lg">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="p-2 bg-green-50 text-green-600 rounded-lg">
                            <ShieldCheck className="w-6 h-6" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-semibold text-green-900">Reset Password</h2>
                            <p className="text-xs text-muted-foreground mt-0.5">Enter your new secure password</p>
                        </div>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="newPassword">New Password</Label>
                            <div className="relative">
                                <Input
                                    id="newPassword"
                                    type={showPassword ? "text" : "password"}
                                    value={formData.newPassword}
                                    onChange={(e) => setFormData({ ...formData, newPassword: e.target.value })}
                                    required
                                    placeholder="At least 6 characters"
                                    className="pr-10 border-green-100 focus-visible:ring-green-600"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-green-700 transition-colors"
                                >
                                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                </button>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="confirmPassword">Confirm New Password</Label>
                            <Input
                                id="confirmPassword"
                                type="password"
                                value={formData.confirmPassword}
                                onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                                required
                                placeholder="Re-enter password"
                                className="border-green-100 focus-visible:ring-green-600"
                            />
                        </div>

                        <Button
                            type="submit"
                            className="w-full rounded-full font-medium bg-green-700 hover:bg-green-800 mt-4 h-11 shadow-sm"
                            disabled={loading}
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                    Updating Password...
                                </>
                            ) : (
                                'Reset Password'
                            )}
                        </Button>
                    </form>

                    <div className="mt-6 text-center">
                        <Link
                            to="/login"
                            className="text-sm text-green-700 hover:text-green-800 font-medium hover:underline"
                        >
                            Back to Login
                        </Link>
                    </div>
                </Card>
            </div>
        </div>
    );
}
