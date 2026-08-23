import { useState } from 'react';
import Header from './components/layout/Header';
import Sidebar from './components/layout/Sidebar';
import ChatContainer from './components/chat/ChatContainer';
import AnalyticsView from './views/AnalyticsView';
import B2BView from './views/B2BView';
import BlueprintsView from './views/BlueprintsView';
import SettingsView from './views/SettingsView';
import RightPanel from './components/RightPanel';
import LoginView from './views/LoginView';
import { useAuth } from './auth/AuthContext';

export default function App() {
  const { isAuthenticated, user, logout } = useAuth();
  const [activeView,   setActiveView]   = useState('chat');
  const [activeCenter, setActiveCenter] = useState('DAMBULLA');
  const [panelOpen,    setPanelOpen]    = useState(false);
  const [artifact,     setArtifact]     = useState(null);

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

  const renderView = () => {
    switch (activeView) {
      case 'analytics':  return <AnalyticsView  activeCenter={activeCenter} />;
      case 'b2b':        return <B2BView />;
      case 'blueprints': return <BlueprintsView />;
      case 'settings':   return <SettingsView />;
      default:           return <ChatContainer activeCenter={activeCenter} onArtifact={handleArtifact} />;
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

      {/* Sidebar */}
      <Sidebar
        activeView={activeView}
        onViewChange={setActiveView}
        activeCenter={activeCenter}
        onCenterChange={setActiveCenter}
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
