"use client";
import { FormEvent, useEffect, useState } from "react";
type Role = {
  id: number;
  name: string;
  permissions: number[];
  users: number[];
};
type Capability = { id: number; code: string };
type User = { id: number; username: string };
type Scope = {
  id: number;
  user: number;
  business_unit: number;
  own_only: boolean;
};
type Api = (path: string, options?: RequestInit) => Promise<any>;
export default function AccessPanel({ api }: { api: Api }) {
  const [roles, setRoles] = useState<Role[]>([]),
    [capabilities, setCapabilities] = useState<Capability[]>([]),
    [users, setUsers] = useState<User[]>([]),
    [scopes, setScopes] = useState<Scope[]>([]),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function load() {
    try {
      const [r, c, u, s] = await Promise.all([
        api("roles/"),
        api("capabilities/"),
        api("users/"),
        api("scopes/"),
      ]);
      setRoles(r);
      setCapabilities(c);
      setUsers(u);
      setScopes(s);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  useEffect(() => {
    load();
  }, [api]);
  async function toggle(role: Role, permission: number) {
    setBusy(true);
    try {
      await api(`roles/${role.id}/`, {
        method: "PATCH",
        body: JSON.stringify({
          permissions: role.permissions.includes(permission)
            ? role.permissions.filter((p) => p !== permission)
            : [...role.permissions, permission],
        }),
      });
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function addRole(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const name = new FormData(form).get("name");
    try {
      await api("roles/", {
        method: "POST",
        body: JSON.stringify({ name, permissions: [], users: [] }),
      });
      form.reset();
      load();
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function assign(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const values = Object.fromEntries(new FormData(e.currentTarget));
    const user = Number(values.user),
      role = roles.find((r) => r.id === Number(values.role));
    try {
      if (role && !role.users.includes(user))
        await api(`roles/${role.id}/`, {
          method: "PATCH",
          body: JSON.stringify({ users: [...role.users, user] }),
        });
      const existing = scopes.find(
        (s) =>
          s.user === user && s.business_unit === Number(values.business_unit),
      );
      const payload = {
        user,
        business_unit: Number(values.business_unit),
        own_only: values.own_only === "on",
      };
      await api(existing ? `scopes/${existing.id}/` : "scopes/", {
        method: existing ? "PATCH" : "POST",
        body: JSON.stringify(payload),
      });
      await load();
      setError("نقش و محدوده ذخیره شد؛ از درخواست بعدی اعمال می‌شود.");
    } catch (e) {
      setError((e as Error).message);
    }
  }
  return (
    <section className="data-panel">
      <div className="panel-heading">
        <h2>ماتریس نقش‌ها و مجوزها</h2>
        <span>تغییرات بلافاصله در سرور اعمال می‌شوند</span>
      </div>
      {error && (
        <p className="notice" role="status">
          {error}
        </p>
      )}
      <form onSubmit={addRole} className="access-form">
        <label>
          نقش تازه
          <input
            name="name"
            required
            maxLength={150}
            placeholder="مثلاً کارشناس فروش کارما"
          />
        </label>
        <button className="primary">ایجاد نقش</button>
      </form>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>ماژول / منبع / عملیات</th>
              {roles.map((r) => (
                <th key={r.id}>{r.name}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {capabilities.map((c) => (
              <tr key={c.id}>
                <th dir="ltr">{c.code}</th>
                {roles.map((r) => (
                  <td key={r.id}>
                    <input
                      type="checkbox"
                      disabled={busy || r.name === "مدیر سیستم"}
                      checked={r.permissions.includes(c.id)}
                      aria-label={`${r.name}: ${c.code}`}
                      onChange={() => toggle(r, c.id)}
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <form className="access-form" onSubmit={assign}>
        <label>
          کاربر
          <select name="user" required>
            {users.map((u) => (
              <option key={u.id} value={u.id}>
                {u.username}
              </option>
            ))}
          </select>
        </label>
        <label>
          نقش
          <select name="role">
            {roles.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          واحد تجاری
          <select name="business_unit">
            <option value="1">کارما</option>
            <option value="2">آلیاژ پیچ کار ماد</option>
          </select>
        </label>
        <label>
          <input type="checkbox" name="own_only" /> فقط رکوردهای خودش
        </label>
        <button className="primary">ذخیرهٔ دسترسی</button>
      </form>
      <p className="catalog-note">
        استثناهای allow/deny، ایجاد کاربر و لغو نشست‌ها از API مدیریت و پنل
        مدیریت امن در دسترس‌اند.
      </p>
    </section>
  );
}
