import React, { useState } from 'react';
import { Student } from './pages/Student';
import { Teacher } from './pages/Teacher';

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<'student' | 'teacher'>('student');

  return (
    <div className="min-h-screen">
      {currentPage === 'student' ? (
        <Student onNavigateTeacher={() => setCurrentPage('teacher')} />
      ) : (
        <Teacher onNavigateStudent={() => setCurrentPage('student')} />
      )}
    </div>
  );
};

export default App;
