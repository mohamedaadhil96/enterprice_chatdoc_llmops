import React, { useState, useEffect } from 'react';
import Auth from './components/Auth';
import Sidebar from './components/Sidebar';
import Chat from './components/Chat';

function App() {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('mdc_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [activeSession, setActiveSession] = useState(null);

  const handleLogout = () => {
    localStorage.removeItem('mdc_token');
    localStorage.removeItem('mdc_user');
    setUser(null);
    setActiveSession(null);
  };

  if (!user) {
    return <Auth onLogin={setUser} />;
  }

  return (
    <div className="flex bg-white text-slate-50 min-h-screen font-sans selection:bg-indigo-500/30">
      <Sidebar
        user={user}
        onLogout={handleLogout}
        onSessionSelect={setActiveSession}
        activeSessionId={activeSession}
      />
      <main className="flex-1 overflow-hidden relative">
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-slate-800 to-transparent"></div>
        <Chat sessionId={activeSession} />
      </main>
    </div>
  );
}

export default App;
