"use client";

import { useCallback, useEffect, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { ApiError } from "@/lib/api/client";
import { ManagedUser, getUsers, removeUser, updateUserRole } from "@/lib/auth";

export function UserManagement() {
  const { user: currentUser, logout } = useAuth();
  const [users, setUsers] = useState<ManagedUser[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [pendingId, setPendingId] = useState<number | null>(null);
  const loadUsers = useCallback(async () => {
    try { setUsers(await getUsers()); }
    catch (error) { setMessage(error instanceof ApiError ? error.message : "Unable to load users."); }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void loadUsers(), 0);
    return () => window.clearTimeout(timer);
  }, [loadUsers]);

  async function changeRole(user: ManagedUser) {
    setMessage(null); setPendingId(user.id);
    try {
      const updated = await updateUserRole(user.id, user.role === "admin" ? "consultant" : "admin");
      setUsers((current) => current.map((entry) => entry.id === updated.id ? updated : entry));
    } catch (error) { setMessage(error instanceof ApiError ? error.message : "Unable to change the user role."); }
    finally { setPendingId(null); }
  }

  async function deleteUser(user: ManagedUser) {
    if (!window.confirm(`Delete ${user.name}? This cannot be undone.`)) return;
    setMessage(null); setPendingId(user.id);
    try {
      await removeUser(user.id);
      if (user.id === currentUser?.id) { await logout(); return; }
      setUsers((current) => current.filter((entry) => entry.id !== user.id));
    } catch (error) { setMessage(error instanceof ApiError ? error.message : "Unable to delete the user."); }
    finally { setPendingId(null); }
  }

  return <section className="user-management">
    <div><p className="eyebrow">Administration</p><h2>User access</h2><p>Promote consultants, revoke administrator access, or remove accounts. The final active administrator is protected.</p></div>
    {message ? <p className="form-error" role="alert">{message}</p> : null}
    <div className="user-table" role="table">{users.map((user) => {
      const isCurrentUser = user.id === currentUser?.id;
      return <div className="user-row" key={user.id} role="row">
        <div role="cell"><strong>{user.name}</strong><span>{user.email}</span></div>
        <span className="role-badge" role="cell">{user.role}</span>
        <div className="user-actions" role="cell">
          {!isCurrentUser ? <button disabled={pendingId === user.id} onClick={() => void changeRole(user)} type="button">Make {user.role === "admin" ? "consultant" : "admin"}</button> : <span>Your account</span>}
          <button disabled={pendingId === user.id} onClick={() => void deleteUser(user)} type="button">Delete</button>
        </div>
      </div>;
    })}</div>
  </section>;
}
