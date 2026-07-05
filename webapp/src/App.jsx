import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate, useParams } from 'react-router-dom';
import { Settings, Bell, BellOff, Users, ChevronRight, Trophy, Search, PlusCircle } from 'lucide-react';

// Mock Data
const mockTeams = [
  { id: 1, name: "Manchester City", type: "DOMESTIC", league: "Premier League", logo: "https://upload.wikimedia.org/wikipedia/en/thumb/e/eb/Manchester_City_FC_badge.svg/1200px-Manchester_City_FC_badge.svg.png" },
  { id: 2, name: "Real Madrid", type: "DOMESTIC", league: "La Liga", logo: "https://upload.wikimedia.org/wikipedia/en/thumb/5/56/Real_Madrid_CF.svg/1200px-Real_Madrid_CF.svg.png" },
  { id: 3, name: "France", type: "INTERNATIONAL", league: "World Cup", logo: "https://upload.wikimedia.org/wikipedia/en/thumb/8/8c/French_Football_Federation_logo.svg/1200px-French_Football_Federation_logo.svg.png" }
];

const mockMatches = [
  { id: 101, home: mockTeams[0], away: mockTeams[1], time: "20:45", is_knockout: false, probs: { home: 45, draw: 25, away: 30 } },
  { id: 102, home: mockTeams[2], away: { name: "Argentina", logo: "" }, time: "16:00", is_knockout: true, probs: { home: 55, draw: 0, away: 45 } }
];

const mockSquads = [
  { id: 1, name: "Office Pool", muted: false, members: [{ name: "Alice", points: 45 }, { name: "You", points: 30 }] },
  { id: 2, name: "Friends Group", muted: true, members: [{ name: "You", points: 15 }, { name: "Bob", points: 10 }] }
];

// Reusable Components
function MatchCard({ match }) {
  const navigate = useNavigate();
  return (
    <div className="glass-panel match-card" style={{ padding: '16px' }} onClick={() => navigate(`/match/${match.id}`)}>
      {match.is_knockout && <div style={{ fontSize: '10px', color: '#ef4444', fontWeight: 'bold', marginBottom: '8px' }}>KNOCKOUT STAGE</div>}
      <div className="match-teams">
        <div className="match-team">
          <img src={match.home.logo || "https://via.placeholder.com/60"} alt={match.home.name} className="team-logo" />
          <span style={{ fontSize: '14px', textAlign: 'center' }}>{match.home.name}</span>
        </div>
        <div className="match-vs">VS<br/><span style={{ fontSize: '12px' }}>{match.time}</span></div>
        <div className="match-team">
          <img src={match.away.logo || "https://via.placeholder.com/60"} alt={match.away.name} className="team-logo" />
          <span style={{ fontSize: '14px', textAlign: 'center' }}>{match.away.name}</span>
        </div>
      </div>
    </div>
  );
}

// Routes
function Dashboard() {
  const navigate = useNavigate();

  return (
    <div className="glass-panel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>My Dashboard</h1>
      </div>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '24px', marginBottom: '12px' }}>
        <h2>My Teams (Squads)</h2>
      </div>
      <div className="team-list" style={{ marginBottom: '24px' }}>
        {mockSquads.map(squad => (
          <div key={squad.id} className="team-item" onClick={() => navigate(`/squad/${squad.id}`)} style={{ cursor: 'pointer' }}>
            <div className="team-info">
              <Users size={20} color="var(--accent)" />
              <span>{squad.name}</span>
            </div>
            {squad.muted ? <BellOff size={18} color="var(--text-secondary)" /> : <Bell size={18} color="var(--text-primary)" />}
          </div>
        ))}
      </div>

      <h2>Aggregated Matches Feed</h2>
      <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '12px' }}>
        Distinct matches from all your active squads.
      </p>
      {mockMatches.map(match => <MatchCard key={match.id} match={match} />)}
    </div>
  );
}

function SquadDetails() {
  const navigate = useNavigate();
  const { id } = useParams();
  
  const [squad, setSquad] = useState(mockSquads.find(s => s.id == id));
  
  if (!squad) return <div>Squad not found</div>;

  return (
    <div className="glass-panel">
      <h2 onClick={() => navigate('/')} style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <ChevronRight style={{ transform: 'rotate(180deg)' }} /> Back
      </h2>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1>{squad.name}</h1>
        <div onClick={() => setSquad({...squad, muted: !squad.muted})} style={{ cursor: 'pointer', padding: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '50%' }}>
          {squad.muted ? <BellOff color="#ef4444" /> : <Bell color="#10b981" />}
        </div>
      </div>
      
      <button className="btn" onClick={() => navigate(`/squad/${squad.id}/teams`)} style={{ marginBottom: '24px', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}>
        <PlusCircle size={18} /> Manage Tracked Teams
      </button>

      <h3><Trophy size={20} style={{ verticalAlign: 'bottom', marginRight: '8px' }} color="#fbbf24"/> Leaderboard</h3>
      <div className="team-list">
        {squad.members.sort((a,b) => b.points - a.points).map((member, idx) => (
          <div key={idx} className="team-item">
            <div className="team-info">
              <span style={{ fontWeight: 'bold', width: '20px' }}>#{idx + 1}</span>
              <span>{member.name}</span>
            </div>
            <span style={{ fontWeight: 'bold', color: 'var(--accent)' }}>{member.points} pts</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function TeamSelection() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [activeTab, setActiveTab] = useState("DOMESTIC");

  return (
    <div className="glass-panel">
      <h2 onClick={() => navigate(-1)} style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <ChevronRight style={{ transform: 'rotate(180deg)' }} /> Back
      </h2>
      <h1>Track Teams</h1>
      
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        <button className="btn" style={{ background: activeTab === "DOMESTIC" ? "var(--accent)" : "rgba(255,255,255,0.1)", flex: 1 }} onClick={() => setActiveTab("DOMESTIC")}>Domestic</button>
        <button className="btn" style={{ background: activeTab === "INTERNATIONAL" ? "var(--accent)" : "rgba(255,255,255,0.1)", flex: 1 }} onClick={() => setActiveTab("INTERNATIONAL")}>International</button>
      </div>
      
      <input 
        type="text" 
        placeholder="Search teams or leagues..." 
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      
      <div className="team-list">
        {mockTeams.filter(t => t.type === activeTab && (t.name.toLowerCase().includes(search.toLowerCase()) || t.league.toLowerCase().includes(search.toLowerCase()))).map(team => (
          <div key={team.id} className="team-item">
            <div className="team-info">
              <img src={team.logo || "https://via.placeholder.com/40"} alt={team.name} className="team-logo" />
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span>{team.name}</span>
                <span style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>{team.league}</span>
              </div>
            </div>
            <input type="checkbox" style={{ width: '20px', height: '20px', margin: 0 }} />
          </div>
        ))}
      </div>
    </div>
  );
}

function MatchDetails() {
  const navigate = useNavigate();
  const { id } = useParams();
  const match = mockMatches.find(m => m.id == id);

  if (!match) return <div>Match not found</div>;

  return (
    <div className="glass-panel">
       <h2 onClick={() => navigate(-1)} style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <ChevronRight style={{ transform: 'rotate(180deg)' }} /> Back
      </h2>
      
      {match.is_knockout && <div style={{ textAlign: 'center', color: '#ef4444', fontWeight: 'bold', marginTop: '12px' }}>KNOCKOUT PHASE</div>}
      
      <div className="match-teams" style={{ marginTop: '20px' }}>
        <div className="match-team">
          <img src={match.home.logo || "https://via.placeholder.com/60"} alt={match.home.name} className="team-logo" style={{ width: '60px', height: '60px' }}/>
          <span style={{ fontWeight: 'bold', textAlign: 'center' }}>{match.home.name}</span>
        </div>
        <div className="match-vs">VS</div>
        <div className="match-team">
          <img src={match.away.logo || "https://via.placeholder.com/60"} alt={match.away.name} className="team-logo" style={{ width: '60px', height: '60px' }}/>
          <span style={{ fontWeight: 'bold', textAlign: 'center' }}>{match.away.name}</span>
        </div>
      </div>

      <div className="probabilities">
        <div className="prob-bar" style={{ width: `${match.probs.home}%`, background: '#2563eb' }}>{match.probs.home}%</div>
        {!match.is_knockout && <div className="prob-bar" style={{ width: `${match.probs.draw}%`, background: '#64748b' }}>{match.probs.draw}%</div>}
        <div className="prob-bar" style={{ width: `${match.probs.away}%`, background: '#dc2626' }}>{match.probs.away}%</div>
      </div>
      
      {match.is_knockout && <p style={{ fontSize: '12px', textAlign: 'center', color: 'var(--text-secondary)', marginTop: '8px' }}>Draw prediction unavailable for knockout stages.</p>}

      <h3 style={{ marginTop: '24px' }}>Pitch Lineup</h3>
      <div className="mini-pitch">
        <div className="pitch-line center-line"></div>
        <div className="pitch-line center-circle"></div>
        <div className="player-dot" style={{ left: '10%', top: '50%', background: '#2563eb' }}></div>
        <div className="player-dot" style={{ right: '10%', top: '50%', background: '#dc2626' }}></div>
      </div>
    </div>
  );
}

function App() {
  return (
    <Router>
      <div className="app-container">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/squad/:id" element={<SquadDetails />} />
          <Route path="/squad/:id/teams" element={<TeamSelection />} />
          <Route path="/match/:id" element={<MatchDetails />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
