import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  Users, ShieldAlert, ShieldCheck, Shield, UserX, UserCheck,
  Trash2, Edit3, X, Check, Crown, BarChart3, Activity,
  AlertTriangle, ChevronDown, ChevronUp, Search, RefreshCw,
  UserCog, Clock, Mail
} from 'lucide-react';

// ─── Small reusable UI pieces ────────────────────────────────────────────────

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${color}`}><Icon size={22} /></div>
      <div>
        <p className="stat-label">{label}</p>
        <p className="stat-value">{value ?? '—'}</p>
      </div>
    </div>
  );
}

function Badge({ type }) {
  const map = {
    active:  { cls: 'badge-active',  label: 'Active'   },
    pending: { cls: 'badge-pending', label: 'Pending'  },
    admin:   { cls: 'badge-admin',   label: 'Admin'    },
    user:    { cls: 'badge-user',    label: 'User'     },
  };
  const { cls, label } = map[type] || map.user;
  return <span className={`badge ${cls}`}>{label}</span>;
}

function ConfirmModal({ isOpen, title, message, onConfirm, onCancel, danger }) {
  if (!isOpen) return null;
  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-box" onClick={e => e.stopPropagation()}>
        <div className={`modal-icon ${danger ? 'modal-icon-danger' : 'modal-icon-warn'}`}>
          <AlertTriangle size={28} />
        </div>
        <h3 className="modal-title">{title}</h3>
        <p className="modal-message">{message}</p>
        <div className="modal-actions">
          <button className="btn-ghost" onClick={onCancel}>Cancel</button>
          <button className={danger ? 'btn-danger' : 'btn-primary'} onClick={onConfirm}>
            Confirm
          </button>
        </div>
      </div>
    </div>
  );
}

function EditUserModal({ user, onClose, onSave }) {
  const [form, setForm] = useState({
    full_name: user.full_name || '',
    affiliation: user.affiliation || '',
    phone_number: user.phone_number || '',
    is_admin: user.is_admin,
    is_active: user.is_active,
  });
  const [saving, setSaving] = useState(false);

  const set = (k, v) => setForm(prev => ({ ...prev, [k]: v }));

  const handleSave = async () => {
    setSaving(true);
    await onSave(user.id, form);
    setSaving(false);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box modal-box-lg" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">Edit User — <span className="text-blue-400">{user.email}</span></h3>
          <button className="icon-btn" onClick={onClose}><X size={18} /></button>
        </div>

        <div className="edit-grid">
          <label className="field-label">Full Name
            <input className="field-input" value={form.full_name} onChange={e => set('full_name', e.target.value)} placeholder="Enter full name" />
          </label>
          <label className="field-label">Affiliation / Organisation
            <input className="field-input" value={form.affiliation} onChange={e => set('affiliation', e.target.value)} placeholder="University / Company" />
          </label>
          <label className="field-label">Phone Number
            <input className="field-input" value={form.phone_number} onChange={e => set('phone_number', e.target.value)} placeholder="+91 00000 00000" />
          </label>
        </div>

        <div className="toggle-row">
          <label className="toggle-label">
            <input type="checkbox" checked={form.is_active} onChange={e => set('is_active', e.target.checked)} />
            <span className="toggle-track"><span className="toggle-thumb" /></span>
            <span>Account Active</span>
          </label>
          <label className="toggle-label">
            <input type="checkbox" checked={form.is_admin} onChange={e => set('is_admin', e.target.checked)} />
            <span className="toggle-track"><span className="toggle-thumb" /></span>
            <span>Admin Privileges</span>
          </label>
        </div>

        <div className="modal-actions">
          <button className="btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn-primary" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving…' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Main Admin Component ─────────────────────────────────────────────────────

export default function Admin() {
  const { api } = useAuth();
  const [users, setUsers]   = useState([]);
  const [stats, setStats]   = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState(null);
  const [search, setSearch] = useState('');
  const [sortField, setSortField] = useState('created_at');
  const [sortAsc, setSortAsc]     = useState(false);
  const [editUser, setEditUser]   = useState(null);
  const [confirm, setConfirm]     = useState(null); // { action, userId, message }
  const [toast, setToast]         = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  // ── Data fetching ───────────────────────────────────────────────────────────
  const fetchData = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    else setRefreshing(true);
    try {
      const [usersRes, statsRes] = await Promise.all([
        api.get('/admin/users'),
        api.get('/admin/stats'),
      ]);
      setUsers(usersRes.data.users);
      setStats(statsRes.data);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load admin data. Ensure you have admin privileges.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [api]);

  useEffect(() => { fetchData(); }, [fetchData]);

  // ── Notifications ──────────────────────────────────────────────────────────
  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3500);
  };

  // ── Actions ────────────────────────────────────────────────────────────────
  const handleDelete = (userId) => {
    const u = users.find(u => u.id === userId);
    setConfirm({
      action: 'delete',
      userId,
      title: 'Delete User',
      message: `Permanently delete "${u?.email}"? This cannot be undone.`,
      danger: true,
    });
  };

  const handleToggleStatus = (userId) => {
    const u = users.find(u => u.id === userId);
    const willActivate = !u.is_active;
    setConfirm({
      action: 'status',
      userId,
      value: willActivate,
      title: willActivate ? 'Activate Account' : 'Suspend Account',
      message: `Are you sure you want to ${willActivate ? 'activate' : 'suspend'} "${u?.email}"?`,
      danger: !willActivate,
    });
  };

  const handleToggleAdmin = (userId) => {
    const u = users.find(u => u.id === userId);
    const willPromote = !u.is_admin;
    setConfirm({
      action: 'role',
      userId,
      value: willPromote,
      title: willPromote ? 'Grant Admin Role' : 'Revoke Admin Role',
      message: `${willPromote ? 'Grant admin privileges to' : 'Remove admin privileges from'} "${u?.email}"?`,
      danger: false,
    });
  };

  const executeConfirm = async () => {
    if (!confirm) return;
    const { action, userId, value } = confirm;
    setConfirm(null);
    try {
      if (action === 'delete') {
        await api.delete(`/admin/users/${userId}`);
        setUsers(prev => prev.filter(u => u.id !== userId));
        showToast('User deleted successfully.');
        fetchData(true);
      } else if (action === 'status') {
        await api.patch(`/admin/users/${userId}/status`, { is_active: value });
        setUsers(prev => prev.map(u => u.id === userId ? { ...u, is_active: value } : u));
        showToast(`Account ${value ? 'activated' : 'suspended'}.`);
      } else if (action === 'role') {
        await api.patch(`/admin/users/${userId}/role`, { is_admin: value });
        setUsers(prev => prev.map(u => u.id === userId ? { ...u, is_admin: value } : u));
        showToast(`Role ${value ? 'promoted to Admin' : 'reverted to User'}.`);
      }
    } catch (err) {
      showToast(err.response?.data?.detail || 'Action failed.', 'error');
    }
  };

  const handleSaveEdit = async (userId, form) => {
    try {
      const res = await api.patch(`/admin/users/${userId}/profile`, form);
      setUsers(prev => prev.map(u => u.id === userId ? res.data.user : u));
      setEditUser(null);
      showToast('User updated successfully.');
    } catch (err) {
      showToast(err.response?.data?.detail || 'Update failed.', 'error');
    }
  };

  // ── Sorting & filtering ────────────────────────────────────────────────────
  const toggleSort = (field) => {
    if (sortField === field) setSortAsc(prev => !prev);
    else { setSortField(field); setSortAsc(true); }
  };

  const SortIcon = ({ field }) => {
    if (sortField !== field) return <ChevronDown size={14} className="text-slate-600" />;
    return sortAsc
      ? <ChevronUp size={14} className="text-blue-400" />
      : <ChevronDown size={14} className="text-blue-400" />;
  };

  const filteredUsers = users
    .filter(u => {
      const q = search.toLowerCase();
      return (
        u.email.toLowerCase().includes(q) ||
        (u.full_name || '').toLowerCase().includes(q) ||
        (u.affiliation || '').toLowerCase().includes(q)
      );
    })
    .sort((a, b) => {
      let av = a[sortField] ?? '';
      let bv = b[sortField] ?? '';
      if (av < bv) return sortAsc ? -1 : 1;
      if (av > bv) return sortAsc ? 1 : -1;
      return 0;
    });

  // ── Render ─────────────────────────────────────────────────────────────────
  if (loading) return (
    <div className="admin-loading">
      <div className="spinner" />
      <p>Loading admin console…</p>
    </div>
  );

  if (error) return (
    <div className="admin-error">
      <ShieldAlert size={64} className="text-red-500" />
      <h2>Access Denied</h2>
      <p>{error}</p>
    </div>
  );

  return (
    <>
      {/* Toast */}
      {toast && (
        <div className={`admin-toast ${toast.type === 'error' ? 'toast-error' : 'toast-success'}`}>
          {toast.type === 'error' ? <X size={16}/> : <Check size={16}/>}
          {toast.message}
        </div>
      )}

      {/* Confirm Modal */}
      <ConfirmModal
        isOpen={!!confirm}
        title={confirm?.title}
        message={confirm?.message}
        danger={confirm?.danger}
        onConfirm={executeConfirm}
        onCancel={() => setConfirm(null)}
      />

      {/* Edit Modal */}
      {editUser && (
        <EditUserModal
          user={editUser}
          onClose={() => setEditUser(null)}
          onSave={handleSaveEdit}
        />
      )}

      <div className="admin-wrap">

        {/* ── Header ──────────────────────────────────────────── */}
        <header className="admin-header">
          <div>
            <div className="admin-header-title">
              <Crown size={28} className="text-amber-400" />
              <h1>Admin Console</h1>
            </div>
            <p className="admin-subtitle">GeoPredict — User &amp; Platform Management</p>
          </div>
          <button
            className={`btn-ghost refresh-btn ${refreshing ? 'spinning' : ''}`}
            onClick={() => fetchData(true)}
            title="Refresh data"
          >
            <RefreshCw size={16} /> Refresh
          </button>
        </header>

        {/* ── Stats ────────────────────────────────────────────── */}
        {stats && (
          <div className="stats-grid">
            <StatCard icon={Users}        label="Total Users"         value={stats.total_users}           color="icon-blue"   />
            <StatCard icon={UserCheck}    label="Active Accounts"     value={stats.active_users}          color="icon-green"  />
            <StatCard icon={Clock}        label="Pending Verification" value={stats.pending_verification} color="icon-amber"  />
            <StatCard icon={ShieldCheck}  label="Admins"              value={stats.admin_count}           color="icon-indigo" />
          </div>
        )}

        {/* ── User Table ─────────────────────────────────────── */}
        <div className="admin-card">
          <div className="table-toolbar">
            <div className="search-wrap">
              <Search size={16} className="search-icon" />
              <input
                className="search-input"
                placeholder="Search by email, name, affiliation…"
                value={search}
                onChange={e => setSearch(e.target.value)}
              />
            </div>
            <span className="result-count">{filteredUsers.length} of {users.length} users</span>
          </div>

          <div className="table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  {[
                    { key: 'id',         label: 'ID'       },
                    { key: 'email',      label: 'Email'    },
                    { key: 'full_name',  label: 'Name'     },
                    { key: 'affiliation',label: 'Org'      },
                    { key: 'created_at', label: 'Joined'   },
                  ].map(col => (
                    <th key={col.key} onClick={() => toggleSort(col.key)} className="sortable-th">
                      {col.label} <SortIcon field={col.key} />
                    </th>
                  ))}
                  <th>Status</th>
                  <th>Role</th>
                  <th className="text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="empty-row">No matching users found.</td>
                  </tr>
                ) : filteredUsers.map(u => (
                  <tr key={u.id} className="table-row">
                    <td className="td-mono">#{u.id}</td>
                    <td>
                      <div className="cell-email">
                        <Mail size={14} className="text-slate-500" />
                        {u.email}
                      </div>
                    </td>
                    <td>{u.full_name || <span className="muted">—</span>}</td>
                    <td>{u.affiliation || <span className="muted">—</span>}</td>
                    <td className="td-date">
                      {u.created_at ? new Date(u.created_at).toLocaleDateString('en-IN', { day:'2-digit', month:'short', year:'numeric' }) : '—'}
                    </td>
                    <td>
                      <Badge type={u.is_active ? 'active' : 'pending'} />
                    </td>
                    <td>
                      <Badge type={u.is_admin ? 'admin' : 'user'} />
                    </td>
                    <td>
                      <div className="action-btns">
                        {/* Edit */}
                        <button className="action-btn action-edit" onClick={() => setEditUser(u)} title="Edit user">
                          <Edit3 size={14} />
                        </button>
                        {/* Toggle admin */}
                        <button
                          className={`action-btn ${u.is_admin ? 'action-demote' : 'action-promote'}`}
                          onClick={() => handleToggleAdmin(u.id)}
                          title={u.is_admin ? 'Revoke admin' : 'Promote to admin'}
                        >
                          {u.is_admin ? <Shield size={14} /> : <ShieldCheck size={14} />}
                        </button>
                        {/* Toggle active */}
                        <button
                          className={`action-btn ${u.is_active ? 'action-suspend' : 'action-activate'}`}
                          onClick={() => handleToggleStatus(u.id)}
                          title={u.is_active ? 'Suspend account' : 'Activate account'}
                        >
                          {u.is_active ? <UserX size={14} /> : <UserCheck size={14} />}
                        </button>
                        {/* Delete */}
                        <button className="action-btn action-delete" onClick={() => handleDelete(u.id)} title="Delete user">
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </div>

      <style>{`
        /* ── Layout ─────────────────────────────── */
        .admin-wrap { max-width: 1200px; margin: 0 auto; padding: 0 0 64px; }
        .admin-loading { display:flex; flex-direction:column; align-items:center; justify-content:center; gap:16px; padding:80px; color:#94a3b8; }
        .admin-error  { display:flex; flex-direction:column; align-items:center; gap:16px; padding:80px; text-align:center; color:#cbd5e1; }
        .admin-error h2 { font-size:1.75rem; font-weight:700; color:#f1f5f9; }

        .spinner { width:40px; height:40px; border:3px solid #1e3a5f; border-top-color:#3b82f6; border-radius:50%; animation:spin 0.8s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }

        /* ── Header ─────────────────────────────── */
        .admin-header { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:32px; }
        .admin-header-title { display:flex; align-items:center; gap:12px; }
        .admin-header-title h1 { font-size:2rem; font-weight:800; color:#f1f5f9; letter-spacing:-0.5px; }
        .admin-subtitle { color:#64748b; margin-top:4px; font-size:0.875rem; }
        .refresh-btn { display:flex; align-items:center; gap:6px; font-size:0.8rem; }
        .spinning svg { animation:spin 0.8s linear infinite; }

        /* ── Stats ───────────────────────────────── */
        .stats-grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(200px,1fr)); gap:16px; margin-bottom:28px; }
        .stat-card  { background:rgba(15,23,42,0.8); border:1px solid #1e3a5f; border-radius:16px; padding:20px; display:flex; align-items:center; gap:16px; }
        .stat-icon  { width:44px; height:44px; border-radius:12px; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
        .icon-blue   { background:rgba(59,130,246,0.15); color:#60a5fa; }
        .icon-green  { background:rgba(16,185,129,0.15); color:#34d399; }
        .icon-amber  { background:rgba(245,158,11,0.15); color:#fbbf24; }
        .icon-indigo { background:rgba(99,102,241,0.15); color:#818cf8; }
        .stat-label { font-size:0.75rem; color:#64748b; text-transform:uppercase; letter-spacing:0.05em; }
        .stat-value { font-size:1.75rem; font-weight:800; color:#f1f5f9; line-height:1; margin-top:4px; }

        /* ── Card ────────────────────────────────── */
        .admin-card { background:rgba(15,23,42,0.8); border:1px solid #1e3a5f; border-radius:20px; overflow:hidden; }

        /* ── Toolbar ─────────────────────────────── */
        .table-toolbar { display:flex; justify-content:space-between; align-items:center; padding:16px 20px; border-bottom:1px solid #1e3a5f; }
        .search-wrap  { position:relative; }
        .search-icon  { position:absolute; left:12px; top:50%; transform:translateY(-50%); color:#64748b; }
        .search-input { background:#0f172a; border:1px solid #1e3a5f; border-radius:10px; padding:8px 12px 8px 36px; color:#e2e8f0; font-size:0.875rem; width:320px; outline:none; transition:border-color .2s; }
        .search-input:focus { border-color:#3b82f6; }
        .search-input::placeholder { color:#475569; }
        .result-count { font-size:0.8rem; color:#64748b; }

        /* ── Table ───────────────────────────────── */
        .table-wrap  { overflow-x:auto; }
        .admin-table { width:100%; border-collapse:collapse; font-size:0.875rem; color:#cbd5e1; }
        .admin-table thead tr { background:rgba(15,23,42,0.5); }
        .admin-table th { padding:12px 16px; text-align:left; font-size:0.75rem; font-weight:600; color:#64748b; text-transform:uppercase; letter-spacing:0.05em; white-space:nowrap; }
        .sortable-th { cursor:pointer; user-select:none; display:table-cell; }
        .sortable-th:hover { color:#94a3b8; }
        .table-row { border-top:1px solid rgba(30,58,95,0.4); transition:background .15s; }
        .table-row:hover { background:rgba(30,58,95,0.25); }
        .admin-table td { padding:12px 16px; vertical-align:middle; }
        .td-mono  { font-family:monospace; color:#475569; font-size:0.8rem; }
        .td-date  { color:#64748b; font-size:0.8rem; white-space:nowrap; }
        .muted    { color:#475569; }
        .empty-row { text-align:center; padding:40px; color:#475569; }
        .cell-email { display:flex; align-items:center; gap:8px; }

        /* ── Badges ──────────────────────────────── */
        .badge        { display:inline-flex; padding:3px 10px; border-radius:99px; font-size:0.7rem; font-weight:700; letter-spacing:0.04em; }
        .badge-active  { background:rgba(16,185,129,0.15); color:#34d399; border:1px solid rgba(16,185,129,0.3); }
        .badge-pending { background:rgba(245,158,11,0.15); color:#fbbf24; border:1px solid rgba(245,158,11,0.3); }
        .badge-admin   { background:rgba(139,92,246,0.15); color:#a78bfa; border:1px solid rgba(139,92,246,0.3); }
        .badge-user    { background:rgba(100,116,139,0.1); color:#94a3b8; border:1px solid rgba(100,116,139,0.2); }

        /* ── Action buttons ─────────────────────── */
        .action-btns { display:flex; gap:6px; justify-content:flex-end; }
        .action-btn  { width:30px; height:30px; border-radius:8px; border:1px solid transparent; display:flex; align-items:center; justify-content:center; cursor:pointer; transition:all .15s; background:transparent; }
        .action-edit    { border-color:rgba(59,130,246,0.3);  color:#60a5fa;  } .action-edit:hover    { background:rgba(59,130,246,0.2); }
        .action-promote { border-color:rgba(139,92,246,0.3);  color:#a78bfa;  } .action-promote:hover { background:rgba(139,92,246,0.2); }
        .action-demote  { border-color:rgba(245,158,11,0.3);  color:#fbbf24;  } .action-demote:hover  { background:rgba(245,158,11,0.2); }
        .action-suspend  { border-color:rgba(251,146,60,0.3); color:#fb923c;  } .action-suspend:hover  { background:rgba(251,146,60,0.2); }
        .action-activate { border-color:rgba(16,185,129,0.3); color:#34d399;  } .action-activate:hover { background:rgba(16,185,129,0.2); }
        .action-delete  { border-color:rgba(239,68,68,0.3);   color:#f87171;  } .action-delete:hover   { background:rgba(239,68,68,0.2); }

        /* ── Buttons ─────────────────────────────── */
        .btn-primary { padding:9px 20px; background:#2563eb; color:#fff; border:none; border-radius:10px; font-weight:600; cursor:pointer; transition:background .2s; }
        .btn-primary:hover    { background:#1d4ed8; }
        .btn-primary:disabled { opacity:0.5; cursor:not-allowed; }
        .btn-danger  { padding:9px 20px; background:#dc2626; color:#fff; border:none; border-radius:10px; font-weight:600; cursor:pointer; transition:background .2s; }
        .btn-danger:hover { background:#b91c1c; }
        .btn-ghost   { padding:9px 20px; background:transparent; color:#94a3b8; border:1px solid #334155; border-radius:10px; font-weight:500; cursor:pointer; transition:all .2s; }
        .btn-ghost:hover { border-color:#475569; color:#e2e8f0; }
        .icon-btn    { background:transparent; border:none; color:#64748b; cursor:pointer; padding:4px; border-radius:6px; display:flex; }
        .icon-btn:hover { color:#e2e8f0; }

        /* ── Modals ─────────────────────────────── */
        .modal-overlay { position:fixed; inset:0; background:rgba(0,0,0,0.6); backdrop-filter:blur(4px); z-index:9999; display:flex; align-items:center; justify-content:center; padding:16px; }
        .modal-box    { background:linear-gradient(160deg,#0f172a,#1e293b); border:1px solid #1e3a5f; border-radius:20px; padding:32px; max-width:440px; width:100%; text-align:center; }
        .modal-box-lg { max-width:560px; text-align:left; }
        .modal-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; }
        .modal-icon   { width:56px; height:56px; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto 20px; }
        .modal-icon-danger { background:rgba(239,68,68,0.15); color:#f87171; }
        .modal-icon-warn   { background:rgba(245,158,11,0.15); color:#fbbf24; }
        .modal-title   { font-size:1.25rem; font-weight:700; color:#f1f5f9; margin-bottom:10px; }
        .modal-message { color:#94a3b8; font-size:0.9rem; line-height:1.6; margin-bottom:24px; }
        .modal-actions { display:flex; gap:12px; justify-content:flex-end; margin-top:24px; }

        /* ── Edit form ──────────────────────────── */
        .edit-grid  { display:grid; gap:16px; margin-bottom:20px; }
        .field-label { display:flex; flex-direction:column; gap:6px; font-size:0.8rem; font-weight:600; color:#94a3b8; text-transform:uppercase; letter-spacing:0.05em; }
        .field-input { background:#0f172a; border:1px solid #1e3a5f; border-radius:10px; padding:10px 14px; color:#e2e8f0; font-size:0.875rem; outline:none; transition:border-color .2s; }
        .field-input:focus { border-color:#3b82f6; }

        /* ── Toggle ──────────────────────────────── */
        .toggle-row   { display:flex; gap:24px; flex-wrap:wrap; margin-bottom:4px; }
        .toggle-label { display:flex; align-items:center; gap:10px; cursor:pointer; color:#cbd5e1; font-size:0.875rem; }
        .toggle-label input[type="checkbox"] { display:none; }
        .toggle-track { position:relative; width:40px; height:22px; background:#334155; border-radius:99px; transition:background .2s; flex-shrink:0; }
        .toggle-label input:checked ~ .toggle-track { background:#2563eb; }
        .toggle-thumb { position:absolute; top:3px; left:3px; width:16px; height:16px; background:#fff; border-radius:50%; transition:transform .2s; }
        .toggle-label input:checked ~ .toggle-track .toggle-thumb { transform:translateX(18px); }

        /* ── Toast ───────────────────────────────── */
        .admin-toast { position:fixed; bottom:28px; right:28px; z-index:99999; display:flex; align-items:center; gap:10px; padding:12px 20px; border-radius:12px; font-size:0.875rem; font-weight:600; box-shadow:0 8px 32px rgba(0,0,0,0.4); animation:slideUp .3s ease; }
        .toast-success { background:#14532d; color:#4ade80; border:1px solid rgba(74,222,128,0.3); }
        .toast-error   { background:#450a0a; color:#f87171; border:1px solid rgba(248,113,113,0.3); }
        @keyframes slideUp { from { opacity:0; transform:translateY(16px); } to { opacity:1; transform:translateY(0); } }
      `}</style>
    </>
  );
}
