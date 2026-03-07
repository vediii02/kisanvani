import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';
import { Loader2, Leaf } from 'lucide-react';
import { toast } from 'sonner';

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const result = await login(formData.username, formData.password);

    if (result.success) {
      toast.success('Welcome back!');

      // Debug: Log the user role
      console.log('User role:', result.user?.role);
      console.log('User data:', result.user);

      // Redirect based on user role
      switch (result.user?.role) {
        case 'company':
          navigate('/company/dashboard');
          break;
        case 'organisation':
        case 'organisation_admin':
          navigate('/organisation/dashboard');
          break;
        case 'admin':
        case 'superadmin':
          navigate('/superadmin');
          break;
        default:
          console.log('No specific role found, redirecting to superadmin dashboard');
          navigate('/superadmin');
      }
    } else {
      toast.error(result.error || 'Login failed');
    }

    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-4">
            <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center">
              <Leaf className="w-7 h-7 text-primary-foreground" />
            </div>
          </div>
          <h1 className="text-4xl font-bold tracking-tight" data-testid="login-title">Kisan Vani AI</h1>
          <p className="text-muted-foreground mt-2">Voice Advisory Platform for Farmers</p>
        </div>

        <Card className="p-8 border border-border/60 shadow-lg" data-testid="login-card">
          <h2 className="text-2xl font-semibold mb-6">Sign In</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="username">Username or Email</Label>
              <Input
                id="username"
                data-testid="login-username-input"
                type="text"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                required
                placeholder="Enter your username"
                className="mt-1"
              />
            </div>

            <div>
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                data-testid="login-password-input"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required
                placeholder="Enter your password"
                className="mt-1"
              />
              <div className="flex justify-end mt-1">
                <Link
                  to="/forgot-password"
                  className="text-xs text-green-800 hover:text-green-900 font-medium hover:underline"
                >
                  Forgot password?
                </Link>
              </div>
            </div>

            <Button
              type="submit"
              data-testid="login-submit-btn"
              className="w-full rounded-full font-medium"
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Signing in...
                </>
              ) : (
                'Sign In'
              )}
            </Button>
          </form>

          <div className="mt-6 text-center text-sm">
            <p className="text-muted-foreground">
              Don't have an account?{' '}
              <Link to="/register" className="text-primary font-medium hover:underline" data-testid="register-link">
                Sign up
              </Link>
            </p>
          </div>

          {/* <div className="mt-4 p-3 bg-muted/50 rounded-md text-xs text-muted-foreground">
            <p className="font-medium mb-1">Demo Credentials:</p>
            <p>Username: admin</p>
            <p>Password: admin123</p>
          </div> */}
        </Card>
      </div>
    </div>
  );
}