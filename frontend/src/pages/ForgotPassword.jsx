import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';
import { Loader2, Leaf, ArrowLeft, MailCheck } from 'lucide-react';
import { toast } from 'sonner';
import api from '../api/api';

export default function ForgotPassword() {
    const [loading, setLoading] = useState(false);
    const [email, setEmail] = useState('');
    const [submitted, setSubmitted] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);

        try {
            await api.post('/auth/forgot-password', { email });
            setSubmitted(true);
            toast.success('Reset instructions sent!');
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Something went wrong. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-background p-4">
            <div className="w-full max-w-md">
                <div className="text-center mb-8">
                    <div className="flex items-center justify-center gap-2 mb-4">
                        <div className="w-12 h-12 bg-green-800 rounded-full flex items-center justify-center">
                            <Leaf className="w-7 h-7 text-white" />
                        </div>
                    </div>
                    <h1 className="text-4xl font-bold tracking-tight">Kisan Vani AI</h1>
                    <p className="text-muted-foreground mt-2">Voice Advisory Platform for Farmers</p>
                </div>

                <Card className="p-8 border border-border/60 shadow-lg">
                    {submitted ? (
                        <div className="text-center space-y-4">
                            <div className="w-16 h-16 bg-green-50 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                                <MailCheck className="w-8 h-8" />
                            </div>
                            <h2 className="text-2xl font-semibold text-green-900">Check your email</h2>
                            <p className="text-muted-foreground">
                                We've sent a password reset link to <span className="font-medium text-slate-900">{email}</span>.
                            </p>
                            <div className="pt-4">
                                <Button asChild className="w-full rounded-full bg-green-700 hover:bg-green-800">
                                    <Link to="/login">Return to Login</Link>
                                </Button>
                            </div>
                        </div>
                    ) : (
                        <>
                            <h2 className="text-2xl font-semibold mb-2 text-green-900">Forgot Password?</h2>
                            <p className="text-sm text-muted-foreground mb-6">
                                Enter your email address and we'll send you a link to reset your password.
                            </p>

                            <form onSubmit={handleSubmit} className="space-y-4">
                                <div className="space-y-2">
                                    <Label htmlFor="email" className="text-green-800">Email Address</Label>
                                    <Input
                                        id="email"
                                        type="email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        required
                                        placeholder="Enter your registered email"
                                        className="border-green-100 focus-visible:ring-green-600"
                                    />
                                </div>

                                <Button
                                    type="submit"
                                    className="w-full rounded-full font-medium bg-green-800 hover:bg-green-900 h-11"
                                    disabled={loading}
                                >
                                    {loading ? (
                                        <>
                                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                            Sending instructions...
                                        </>
                                    ) : (
                                        'Send Reset Link'
                                    )}
                                </Button>
                            </form>

                            <div className="mt-6 text-center">
                                <Link
                                    to="/login"
                                    className="inline-flex items-center text-sm text-green-800 hover:text-green-900 font-medium hover:underline gap-1"
                                >
                                    <ArrowLeft className="w-4 h-4" />
                                    Back to Login
                                </Link>
                            </div>
                        </>
                    )}
                </Card>
            </div>
        </div>
    );
}
