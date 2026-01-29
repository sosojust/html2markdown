import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';

const Dashboard = () => {
  const { user, api, logout } = useAuth();
  const [keys, setKeys] = useState([]);
  const [newKeyName, setNewKeyName] = useState('');
  const [createdKey, setCreatedKey] = useState(null);
  
  // Integration Config State
  const [notionConfig, setNotionConfig] = useState({ token: '', pageId: '' });
  const [configSaved, setConfigSaved] = useState(false);

  const fetchKeys = async () => {
    try {
      const res = await api.get('/auth/keys');
      setKeys(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchKeys();
    
    // Load configs from user preferences
    if (user && user.preferences) {
        try {
            const prefs = JSON.parse(user.preferences);
            if (prefs.notion) setNotionConfig(prefs.notion);
        } catch (e) {
            console.error("Failed to parse preferences", e);
        }
    }
  }, [user]); // Add user dependency

  const createKey = async () => {
    try {
      const res = await api.post('/auth/keys', { name: newKeyName || 'Untitled Key' });
      setCreatedKey(res.data);
      setNewKeyName('');
      fetchKeys();
    } catch (err) {
      alert("Failed to create key");
    }
  };

  const deleteKey = async (id) => {
    if (!confirm("Are you sure?")) return;
    try {
      await api.delete(`/auth/keys/${id}`);
      fetchKeys();
    } catch (err) {
      alert("Failed to delete key");
    }
  };
  
  const handleSaveConfig = async () => {
      const preferences = JSON.stringify({
          notion: notionConfig
      });
      
      try {
          await api.patch('/auth/me', { preferences });
          setConfigSaved(true);
          setTimeout(() => setConfigSaved(false), 2000);
          
          // Refresh user info might be good, but AuthContext usually caches it. 
          // For now, local state is already updated.
      } catch (err) {
          alert("Failed to save configuration: " + (err.response?.data?.detail || err.message));
      }
  };

  return (
    <div className="min-h-screen bg-base-200 p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex justify-between items-center">
           <h1 className="text-3xl font-bold">Dashboard</h1>
           <button onClick={logout} className="btn btn-ghost">Logout</button>
        </div>
        
        <div className="card bg-base-100 shadow-xl">
          <div className="card-body">
            <h2 className="card-title">User Info</h2>
            <p><strong>Email:</strong> {user?.email}</p>
            <p><strong>Tier:</strong> <span className="badge badge-primary">{user?.tier}</span></p>
          </div>
        </div>

        <div className="card bg-base-200 shadow-xl">
          <div className="card-body">
            <h2 className="card-title">API Keys</h2>
            
            <div className="flex gap-2 my-4">
               <input 
                 type="text" 
                 placeholder="Key Name (e.g. My App)" 
                 className="input input-bordered w-full max-w-xs" 
                 value={newKeyName}
                 onChange={(e) => setNewKeyName(e.target.value)}
               />
               <button onClick={createKey} className="btn btn-neutral">Create Key</button>
            </div>

            {createdKey && (
              <div className="alert alert-success">
                <div className="w-full">
                  <h3 className="font-bold">Key Created!</h3>
                  <div className="text-xs">Copy this key now, you won't see it again:</div>
                  <div className="flex gap-2 mt-2 items-center">
                    <div className="font-mono bg-base-300 p-2 rounded flex-1 select-all break-all">{createdKey.key}</div>
                    <button 
                      className="btn btn-sm"
                      onClick={() => {
                        navigator.clipboard.writeText(createdKey.key);
                        alert('Copied to clipboard!');
                      }}
                    >
                      Copy
                    </button>
                  </div>
                </div>
                <button onClick={() => setCreatedKey(null)} className="btn btn-sm btn-circle btn-ghost self-start">✕</button>
              </div>
            )}

            <div className="overflow-x-auto">
              <table className="table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Prefix</th>
                    <th>Created</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {keys.map(k => (
                    <tr key={k.id}>
                      <td>{k.name}</td>
                      <td className="font-mono">{k.prefix}</td>
                      <td>{new Date(k.created_at).toLocaleDateString()}</td>
                      <td>
                        <button onClick={() => deleteKey(k.id)} className="btn btn-xs btn-error">Revoke</button>
                      </td>
                    </tr>
                  ))}
                  {keys.length === 0 && <tr><td colSpan="4" className="text-center opacity-50">No API keys found</td></tr>}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Integration Settings Section */}
        <div className="card bg-base-100 shadow-xl">
          <div className="card-body">
            <h2 className="card-title">Integration Settings</h2>
            <p className="text-sm text-base-content/70">Configure your export destinations.</p>
            
            <div className="divider">Notion</div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="form-control">
                <label className="label"><span className="label-text">Notion Token</span></label>
                <input 
                  type="password" 
                  className="input input-bordered" 
                  placeholder="secret_..."
                  value={notionConfig.token}
                  onChange={(e) => setNotionConfig({...notionConfig, token: e.target.value})}
                />
              </div>
              <div className="form-control">
                <label className="label"><span className="label-text">Page ID</span></label>
                <input 
                  type="text" 
                  className="input input-bordered" 
                  placeholder="Page ID"
                  value={notionConfig.pageId}
                  onChange={(e) => setNotionConfig({...notionConfig, pageId: e.target.value})}
                />
              </div>
            </div>

            <div className="mt-6 flex items-center gap-4">
               <button 
                 className="btn btn-primary"
                 onClick={handleSaveConfig}
               >
                 Save Configuration
               </button>
               {configSaved && <span className="text-success text-sm">Saved locally!</span>}
            </div>

          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
