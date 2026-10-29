import { useState } from 'react';
import { useAuth } from '../../../core/auth/AuthContext.jsx';
import { useAsync, useDebounced } from '../../../core/hooks/useAsync.js';
import {
  AsyncBoundary, Badge, Card, ConfirmDialog, EmptyState, PageHeader, Pagination, SearchInput, Select, Toggle, useToast,
} from '../../../core/ui/index.js';
import { fmtDateTime } from '../../../core/utils/format.js';
import { listUsers, updateUser } from '../api.js';

export default function UsersPage() {
  const { user: me } = useAuth();
  const toast = useToast();
  const [search, setSearch] = useState('');
  const [role, setRole] = useState('');
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);
  const [pending, setPending] = useState(null); // user awaiting deactivate confirmation
  const [busyId, setBusyId] = useState(null);
  const debounced = useDebounced(search);

  const state = useAsync(() => listUsers({ search: debounced, role, status, page, per_page: 15 }), [debounced, role, status, page]);

  const apply = async (target, changes, message) => {
    setBusyId(target.id);
    try {
      await updateUser(target.id, changes);
      toast.success(message);
      await state.reload({ silent: true });
    } catch (err) {
      toast.error(err.message);
    } finally {
      setBusyId(null);
      setPending(null);
    }
  };

  const onToggle = (target, active) => {
    if (active) apply(target, { is_active: true }, `${target.full_name} activated.`);
    else setPending(target);
  };

  return (
    <>
      <PageHeader title="Manage users" subtitle="Search accounts, change roles and activate or deactivate access." />
      <div className="toolbar">
        <SearchInput value={search} onChange={(v) => { setSearch(v); setPage(1); }} placeholder="Search by name, email or ID" label="Search users" />
        <Select aria-label="Filter by role" value={role} onChange={(e) => { setRole(e.target.value); setPage(1); }}>
          <option value="">All roles</option>
          <option>Student</option>
          <option>Faculty</option>
          <option>Admin</option>
        </Select>
        <Select aria-label="Filter by status" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
          <option value="">Any status</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </Select>
      </div>

      <Card flush>
        <AsyncBoundary state={state}>
          {(data) =>
            data.users.length === 0 ? (
              <EmptyState title="No users match your filters" />
            ) : (
              <>
                <div className="table-wrap">
                  <table className="table">
                    <thead>
                      <tr><th>User</th><th>Institutional ID</th><th>Role</th><th>Last sign-in</th><th>Active</th></tr>
                    </thead>
                    <tbody>
                      {data.users.map((u) => {
                        const self = u.id === me.id;
                        return (
                          <tr key={u.id}>
                            <td>
                              <div className="cell-main">{u.full_name} {u.is_temporary_password && <Badge tone="warning">Temp password</Badge>}</div>
                              <div className="cell-sub">{u.email}</div>
                            </td>
                            <td className="mono">{u.institutional_id}</td>
                            <td>
                              <Select
                                aria-label={`Role for ${u.full_name}`}
                                value={u.role}
                                disabled={self || busyId === u.id}
                                onChange={(e) => apply(u, { role: e.target.value }, `${u.full_name} is now ${e.target.value}.`)}
                                style={{ minWidth: 120 }}
                              >
                                <option>Student</option>
                                <option>Faculty</option>
                                <option>Admin</option>
                              </Select>
                            </td>
                            <td className="cell-sub">{fmtDateTime(u.last_login_at)}</td>
                            <td>
                              <div className="row">
                                <Toggle checked={u.is_active} disabled={self || busyId === u.id} label={`${u.is_active ? 'Deactivate' : 'Activate'} ${u.full_name}`} onChange={(v) => onToggle(u, v)} />
                                <Badge tone={u.is_active ? 'success' : 'danger'}>{u.is_active ? 'Active' : 'Inactive'}</Badge>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
                <Pagination page={data.page} pages={data.pages} total={data.total} onChange={setPage} />
              </>
            )
          }
        </AsyncBoundary>
      </Card>

      {pending && (
        <ConfirmDialog
          danger
          title="Deactivate account?"
          message={`${pending.full_name} will be signed out immediately and blocked from signing in until reactivated. This is recorded in the audit log.`}
          confirmLabel="Deactivate"
          loading={busyId === pending.id}
          onCancel={() => setPending(null)}
          onConfirm={() => apply(pending, { is_active: false }, `${pending.full_name} deactivated.`)}
        />
      )}
    </>
  );
}
