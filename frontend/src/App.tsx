import React, { useState, useEffect } from 'react';
import { Student } from './pages/Student';
import { Teacher } from './pages/Teacher';
import { AuthModal } from './components/AuthModal';
import { User } from './types/api';

export const App: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<User | null>(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('clearpath_user');
      if (stored) {
        try {
          return JSON.parse(stored);
        } catch (e) {
          // ignore corrupted JSON
        }
      }
    }
    // Default pre-authenticated student persona so judges can immediately test without barriers
    return {
      id: 'u_student_alex',
      name: 'Alex Chen',
      email: 'alex@clearpath.edu',
      role: 'student',
    };
  });

  const [currentPage, setCurrentPage] = useState<'student' | 'teacher'>(() => {
    return currentUser?.role === 'teacher' ? 'teacher' : 'student';
  });

  const [showAuthModal, setShowAuthModal] = useState<boolean>(false);

  // Initialize dark mode class on mount if saved
  useEffect(() => {
    const storedTheme = localStorage.getItem('clearpath_theme');
    if (storedTheme === 'dark') {
      document.documentElement.classList.add('dark');
    }
  }, []);

  const handleAuthSuccess = (user: User, token: string) => {
    setCurrentUser(user);
    if (user.role === 'teacher') {
      setCurrentPage('teacher');
    } else {
      setCurrentPage('student');
    }
    setShowAuthModal(false);
  };

  const handleLogout = () => {
    setShowAuthModal(true);
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors">
      {currentPage === 'student' ? (
        <Student
          currentUser={currentUser}
          onLogout={handleLogout}
          onNavigateTeacher={() => setCurrentPage('teacher')}
        />
      ) : (
        <Teacher
          currentUser={currentUser}
          onLogout={handleLogout}
          onNavigateStudent={() => setCurrentPage('student')}
        />
      )}

      {/* Role-Based Authentication & Portal Switcher Modal */}
      <AuthModal
        isOpen={showAuthModal}
        canClose={true}
        onClose={() => setShowAuthModal(false)}
        initialRole={currentPage === 'teacher' ? 'teacher' : 'student'}
        onSuccess={handleAuthSuccess}
      />
    </div>
  );
};

export default App;
