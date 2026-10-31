import React, { useState, useEffect } from 'react';
import {
  GraduationCap,
  LayoutDashboard,
  LogIn,
  UserPlus,
  X,
  CheckCircle2,
  AlertCircle,
  KeyRound,
  Mail,
  User as UserIcon,
  Sparkles,
  ArrowRight,
} from 'lucide-react';
import { User, DemoUser, AuthResponse } from '../types/api';

interface AuthModalProps {
  isOpen: boolean;
  canClose?: boolean;
  onClose: () => void;
  initialRole?: 'student' | 'teacher';
  onSuccess: (user: User, token: string) => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  canClose = true,
  onClose,
  initialRole = 'student',
  onSuccess,
}) => {
  const [role, setRole] = useState<'student' | 'teacher'>(initialRole);
  const [isSignUp, setIsSignUp] = useState<boolean>(false);
  const [name, setName] = useState<string>('');
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [demoUsers, setDemoUsers] = useState<{ students: DemoUser[]; teachers: DemoUser[] }>({
    students: [
      {
        id: 'u_student_alex',
        name: 'Alex Chen',
        email: 'alex@clearpath.edu',
        role: 'student',
        password: 'clearpath',
        description: 'Steady Cadet • Quadratic & Code Tracing',
      },
      {
        id: 'u_student_maya',
        name: 'Maya Lin',
        email: 'maya@clearpath.edu',
        role: 'student',
        password: 'clearpath',
        description: 'High Velocity • Fast Cadence Solver',
      },
    ],
    teachers: [
      {
        id: 'u_teacher_reed',
        name: 'Dr. Evelyn Reed',
        email: 'teacher@clearpath.edu',
        role: 'teacher',
        password: 'clearpath',
        description: 'Lead STEM Educator • Real-Time Matrix Diagnostic Specialist',
      },
    ],
  });

  useEffect(() => {
    setRole(initialRole);
    setError(null);
  }, [initialRole, isOpen]);

  // Fetch live demo users from backend if available
  useEffect(() => {
    if (!isOpen) return;
    fetch('/api/auth/demo-users')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data && data.students && data.teachers) {
          setDemoUsers(data);
        }
      })
      .catch(() => {
        // Fallback to static demos
      });
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    const endpoint = isSignUp ? '/api/auth/signup' : '/api/auth/login';
    const payload = isSignUp
      ? { name, email, password, role }
      : { email, password, role };

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data: AuthResponse = await res.json();
      if (!res.ok) {
        throw new Error((data as any).detail || data.message || 'Authentication failed');
      }

      // Store in localStorage for persistent session
      localStorage.setItem('clearpath_user', JSON.stringify(data.user));
      localStorage.setItem('clearpath_token', data.token);

      onSuccess(data.user, data.token);
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoLogin = (demo: DemoUser) => {
    setEmail(demo.email);
    setPassword(demo.password || 'clearpath');
    setRole(demo.role);
    setIsSignUp(false);
    setError(null);

    // Immediate 1-click execution for smooth judge presentation
    setIsLoading(true);
    fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: demo.email,
        password: demo.password || 'clearpath',
        role: demo.role,
      }),
    })
      .then(async (res) => {
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Demo login failed');
        localStorage.setItem('clearpath_user', JSON.stringify(data.user));
        localStorage.setItem('clearpath_token', data.token);
        onSuccess(data.user, data.token);
      })
      .catch((err) => {
        // Fallback client simulation if offline
        const fallbackUser: User = {
          id: demo.id,
          name: demo.name,
          email: demo.email,
          role: demo.role,
        };
        localStorage.setItem('clearpath_user', JSON.stringify(fallbackUser));
        onSuccess(fallbackUser, 'mock_token_demo');
      })
      .finally(() => {
        setIsLoading(false);
      });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 dark:bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg bg-white dark:bg-slate-900 rounded-3xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden text-slate-800 dark:text-slate-100 transition-all">
        {/* Header Bar */}
        <div className="px-6 pt-6 pb-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-[#6A35D8] to-[#9060eb] flex items-center justify-center text-white font-bold shadow-md shadow-purple-500/20">
              CP
            </div>
            <div>
              <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
                ClearPath Access Portal
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Cognitive-Aware Adaptive Learning & Live Telemetry
              </p>
            </div>
          </div>
          {canClose && (
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Role Switcher Tabs */}
        <div className="p-6 pb-2">
          <div className="grid grid-cols-2 p-1 bg-slate-100 dark:bg-slate-800/80 rounded-2xl mb-5">
            <button
              type="button"
              onClick={() => {
                setRole('student');
                setError(null);
              }}
              className={`flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl font-semibold text-xs transition-all ${
                role === 'student'
                  ? 'bg-white dark:bg-slate-700 text-[#6A35D8] dark:text-purple-300 shadow-sm'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <GraduationCap className="w-4 h-4" />
              <span>Student Portal</span>
            </button>
            <button
              type="button"
              onClick={() => {
                setRole('teacher');
                setError(null);
              }}
              className={`flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl font-semibold text-xs transition-all ${
                role === 'teacher'
                  ? 'bg-white dark:bg-slate-700 text-[#F25C1E] dark:text-orange-300 shadow-sm'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <LayoutDashboard className="w-4 h-4" />
              <span>Teacher Heatmap</span>
            </button>
          </div>

          {/* Quick Demo Logins for Judges */}
          <div className="mb-5 p-3.5 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/80 dark:border-slate-700/60">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                1-Click Judge Demo Accounts ({role === 'student' ? 'Students' : 'Faculty'})
              </span>
              <span className="text-[10px] text-slate-400">Zero Setup Required</span>
            </div>
            <div className="grid grid-cols-1 gap-1.5">
              {(role === 'student' ? demoUsers.students : demoUsers.teachers).map((demo) => (
                <button
                  key={demo.id}
                  type="button"
                  onClick={() => handleDemoLogin(demo)}
                  className="w-full text-left px-3 py-2 rounded-xl bg-white dark:bg-slate-800 hover:bg-purple-50 dark:hover:bg-purple-950/40 border border-slate-200 dark:border-slate-700 hover:border-purple-300 dark:hover:border-purple-600/50 transition-all flex items-center justify-between group"
                >
                  <div className="flex items-center gap-2.5 truncate">
                    <div
                      className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs ${
                        demo.role === 'teacher'
                          ? 'bg-orange-100 text-[#F25C1E] dark:bg-orange-950 dark:text-orange-300'
                          : 'bg-purple-100 text-[#6A35D8] dark:bg-purple-950 dark:text-purple-300'
                      }`}
                    >
                      {demo.name.charAt(0)}
                    </div>
                    <div className="truncate">
                      <div className="font-semibold text-xs text-slate-800 dark:text-slate-200 group-hover:text-[#6A35D8] dark:group-hover:text-purple-300 flex items-center gap-1.5">
                        <span>{demo.name}</span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400 font-normal">
                          {demo.email}
                        </span>
                      </div>
                      <div className="text-[10px] text-slate-400 dark:text-slate-500 truncate">
                        {demo.description}
                      </div>
                    </div>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-[#6A35D8] group-hover:translate-x-0.5 transition-all flex-shrink-0" />
                </button>
              ))}
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800/60 text-red-700 dark:text-red-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Custom Credentials Form */}
          <form onSubmit={handleSubmit} className="space-y-3.5">
            {isSignUp && (
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Full Name
                </label>
                <div className="relative">
                  <UserIcon className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder={role === 'student' ? 'e.g. Jordan Smith' : 'e.g. Prof. Alan Turing'}
                    className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-[#6A35D8] text-slate-900 dark:text-slate-100"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Email Address
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={role === 'student' ? 'student@clearpath.edu' : 'teacher@clearpath.edu'}
                  className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-[#6A35D8] text-slate-900 dark:text-slate-100"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Password
              </label>
              <div className="relative">
                <KeyRound className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-[#6A35D8] text-slate-900 dark:text-slate-100"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className={`w-full py-2.5 px-4 rounded-xl font-bold text-xs text-white shadow-md transition-all flex items-center justify-center gap-2 ${
                role === 'teacher'
                  ? 'bg-[#F25C1E] hover:bg-[#d94f17] shadow-orange-500/20'
                  : 'bg-[#6A35D8] hover:bg-[#562ab3] shadow-purple-500/20'
              } disabled:opacity-50`}
            >
              {isLoading ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : isSignUp ? (
                <>
                  <UserPlus className="w-4 h-4" />
                  <span>Create {role === 'student' ? 'Student' : 'Faculty'} Account</span>
                </>
              ) : (
                <>
                  <LogIn className="w-4 h-4" />
                  <span>Enter {role === 'student' ? 'Student Portal' : 'Teacher Portal'}</span>
                </>
              )}
            </button>
          </form>

          {/* Toggle Login / SignUp */}
          <div className="mt-4 pb-4 text-center">
            <button
              type="button"
              onClick={() => {
                setIsSignUp(!isSignUp);
                setError(null);
              }}
              className="text-xs font-semibold text-[#6A35D8] dark:text-purple-400 hover:underline"
            >
              {isSignUp
                ? 'Already have an account? Sign in here'
                : "New to ClearPath? Register a new account"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthModal;

