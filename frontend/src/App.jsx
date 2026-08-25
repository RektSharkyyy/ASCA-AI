import { useState, useCallback } from 'react';
import Header from './components/layout/Header';
import Sidebar from './components/layout/Sidebar';
import ChatContainer from './components/chat/ChatContainer';
import AnalyticsView from './views/AnalyticsView';
import B2BView from './views/B2BView';
import BlueprintsView from './views/BlueprintsView';
import SettingsView from './views/SettingsView';
import CultivationView from './views/CultivationView';
import RightPanel from './components/RightPanel';
import LoginView from './views/LoginView';
import { useAuth } from './auth/AuthContext';

export default function App() {
  const { isAuthenticated, user, logout } = useAuth();
  const [activeView,    setActiveView]    = useState('chat');
  const [activeCenter,  setActiveCenter]  = useState('DAMBULLA');
  const [panelOpen,     setPanelOpen]     = useState(false);
  const [artifact,      setArtifact]      = useState(null);

  // Session state — shared between Sidebar and ChatContainer
  const [activeSessionId,    setActiveSessionId]    = useState(null);
  const [sessionsRefreshKey, setSessionsRefreshKey] = useState(0);

  // Auth guard — show login page if not authenticated
  if (!isAuthenticated) return <LoginView />;


  const handleArtifact = (a) => {
    setArtifact(a);
    setPanelOpen(true);
  };

  const handlePanelToggle = () => {
    setPanelOpen(o => !o);
    if (panelOpen) setArtifact(null);
  };

  /** Start a fresh chat — clear active session, switch to chat view */
  const handleNewSession = () => {
    setActiveSessionId(null);
    setActiveView('chat');
  };

  /** Load a specific session from sidebar click */
  const handleSelectSession = (sessionId) => {
    setActiveSessionId(sessionId);
    setActiveView('chat');
  };

  /** Increment the refresh key so Sidebar re-fetches sessions */
  const handleSessionUpdated = useCallback(() => {
    setSessionsRefreshKey(k => k + 1);
  }, []);

  const renderView = () => {
    switch (activeView) {
      case 'analytics':   return <AnalyticsView   activeCenter={activeCenter} />;
      case 'b2b':         return <B2BView          activeCenter={activeCenter} />;
      case 'blueprints':  return <BlueprintsView />;
      case 'cultivation': return <CultivationView  activeCenter={activeCenter} />;
      case 'settings':    return <SettingsView />;
      default:           return (
        <ChatContainer
          activeCenter={activeCenter}
          onArtifact={handleArtifact}
          activeSessionId={activeSessionId}
          onSessionUpdated={handleSessionUpdated}
          onNewSession={handleNewSession}
        />
      );
    }
  };

  return (
    <div className={`app-shell ${panelOpen ? 'panel-open' : ''}`}>
      {/* Header spans full width (grid-column: 1/-1) */}
      <Header
        activeCenter={activeCenter}
        onCenterChange={setActiveCenter}
        panelOpen={panelOpen}
        onPanelToggle={handlePanelToggle}
      />

      {/* Sidebar — now receives session handlers */}
      <Sidebar
        activeView={activeView}
        onViewChange={setActiveView}
        activeCenter={activeCenter}
        onCenterChange={setActiveCenter}
        activeSessionId={activeSessionId}
        onNewSession={handleNewSession}
        onSelectSession={handleSelectSession}
        onSessionDeleted={handleSessionUpdated}
        sessionsRefreshKey={sessionsRefreshKey}
      />

      {/* Main content */}
      <main className="content-area">
        {renderView()}
      </main>

      {/* Conditional right panel */}
      {panelOpen && (
        <RightPanel artifact={artifact} onClose={() => { setPanelOpen(false); setArtifact(null); }} />
      )}
    </div>
  );
}
