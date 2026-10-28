"use client";
import { FormEvent, useState } from "react";
type Row = Record<string, unknown>;
type Doc = Row & {
  id: number;
  kind: string;
  status: string;
  doc_date: string;
  lines: (Row & {
    product: number;
    quantity: string;
    unit_price: string;
    progress?: { quantity: string; source: string; notes: string };
  })[];
};
type Api = (path: string, options?: RequestInit) => Promise<any>;
const kinds: Record<string, string> = {
  quote: "پیش‌فاکتور",
  supply: "برگهٔ تأمین",
  invoice: "فاکتور فروش",
  packing: "لیست بسته‌بندی",
  return: "برگشت از فروش",
  purchase_return: "برگشت از خرید",
};
export default function DocumentPanel({
  document,
  api,
  onClose,
  onChange,
  permissions,
}: {
  document: Doc;
  api: Api;
  onClose: () => void;
  onChange: () => void;
  permissions: string[];
}) {
  const [doc, setDoc] = useState(document),
    [message, setMessage] = useState(""),
    [busy, setBusy] = useState(false);
  const can = (action: string, kind = doc.kind) =>
    permissions.includes(`sales.document.${action}`) ||
    permissions.includes(`sales.${kind}.${action}`);
  async function act(action: string, body: unknown = {}) {
    setBusy(true);
    try {
      const response = await api(`documents/${doc.id}/${action}/`, {
        method: "POST",
        body: JSON.stringify(body),
      });
      setDoc(response);
      onChange();
      setMessage("تغییرات ثبت شد");
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.currentTarget));
    setBusy(true);
    try {
      const payload = {
        doc_date: data.doc_date,
        tax_rate: data.tax_rate,
        discount: data.discount,
        shipping: data.shipping,
        notes: data.notes,
        lines: doc.lines.map((l, i) => ({
          product: l.product,
          quantity: data["qty-" + i],
          unit_price: data["price-" + i],
          description: l.description || "",
          notes: l.notes || "",
        })),
      };
      setDoc(
        await api(`documents/${doc.id}/`, {
          method: "PATCH",
          body: JSON.stringify(payload),
        }),
      );
      onChange();
      setMessage("پیش‌نویس ذخیره شد");
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function supply(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.currentTarget));
    await act("fulfill", {
      items: doc.lines.map((l, i) => ({
        line: l.id,
        quantity: data["supply-" + i],
        source: data["source-" + i],
        notes: data["note-" + i],
      })),
      complete: data.complete === "on",
    });
  }
  const conversions =
    doc.kind === "quote" && doc.status === "approved"
      ? ["supply", "invoice"]
      : doc.kind === "quote" && doc.status === "sent"
        ? ["quote"]
        : doc.kind === "supply" && doc.status === "completed"
          ? ["invoice"]
          : doc.kind === "invoice" && doc.status === "issued"
            ? ["packing", "return"]
            : doc.kind === "purchase" && doc.status === "issued"
              ? ["purchase_return"]
              : [];
  return (
    <div className="modal-backdrop">
      <section
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label="جزئیات سند"
      >
        <button className="close" onClick={onClose} aria-label="بستن">
          ×
        </button>
        <h2>
          {kinds[doc.kind] || doc.kind} · {String(doc.number || "پیش‌نویس")}
        </h2>
        <p>
          {String((doc.buyer_snapshot as Row)?.name || doc.customer_name || "")} · تاریخ سند: {doc.doc_date}
        </p>
        <p>
          ثبت سیستمی:{" "}
          {new Intl.DateTimeFormat("fa-IR", {
            dateStyle: "short",
            timeStyle: "short",
            timeZone: "Asia/Tehran",
          }).format(new Date(String(doc.created_at)))}
        </p>
        {message && (
          <div className="notice" role="status">
            {message}
          </div>
        )}
        {doc.status === "draft" && can("edit") ? (
          <form onSubmit={save}>
            <div className="form-grid">
              <label>
                تاریخ شمسی
                <input
                  name="doc_date"
                  defaultValue={doc.doc_date}
                  dir="ltr"
                  required
                />
              </label>
              <label>
                مالیات ٪
                <input
                  name="tax_rate"
                  type="number"
                  min="0"
                  max="100"
                  step=".01"
                  defaultValue={String(doc.tax_rate)}
                />
              </label>
              <label>
                تخفیف (ریال)
                <input
                  name="discount"
                  type="number"
                  min="0"
                  defaultValue={String(doc.discount)}
                />
              </label>
              <label>
                حمل (ریال)
                <input
                  name="shipping"
                  type="number"
                  min="0"
                  defaultValue={String(doc.shipping)}
                />
              </label>
            </div>
            {doc.lines.map((l, i) => (
              <div className="line-input" key={i}>
                <span>
                  {String(
                    (l.product_snapshot as Row)?.technical_code ||
                      l.description ||
                      "ردیف " + (i + 1),
                  )}
                </span>
                <label>
                  تعداد
                  <input
                    name={"qty-" + i}
                    type="number"
                    min=".001"
                    step=".001"
                    defaultValue={l.quantity}
                    required
                  />
                </label>
                <label>
                  قیمت واحد (ریال)
                  <input
                    name={"price-" + i}
                    type="number"
                    min="0"
                    step="1"
                    defaultValue={l.unit_price}
                    required
                  />
                </label>
              </div>
            ))}
            <label>
              یادداشت
              <textarea name="notes" defaultValue={String(doc.notes || "")} />
            </label>
            <button className="primary" disabled={busy}>
              ذخیرهٔ پیش‌نویس
            </button>
          </form>
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>شرح</th>
                  <th>تعداد</th>
                  <th>قیمت واحد (ریال)</th>
                </tr>
              </thead>
              <tbody>
                {doc.lines.map((l, i) => (
                  <tr key={i}>
                    <td>
                      {String(
                        (l.product_snapshot as Row)?.technical_code ||
                          l.description ||
                          "—",
                      )}
                    </td>
                    <td>{l.quantity}</td>
                    <td>
                      {String(l.unit_price).replace(
                        /\B(?=(\d{3})+(?!\d))/g,
                        ",",
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {doc.kind === "supply" &&
          ["draft", "issued"].includes(doc.status) &&
          can("fulfill") && (
            <form onSubmit={supply}>
              <h3>پیشرفت تأمین سفارش</h3>
              {doc.lines.map((l, i) => (
                <div key={i} className="form-grid">
                  <label>
                    مقدار تأمین‌شده
                    <input
                      name={"supply-" + i}
                      type="number"
                      min="0"
                      max={l.quantity}
                      step=".001"
                      defaultValue={l.progress?.quantity || "0"}
                    />
                  </label>
                  <label>
                    منبع تأمین
                    <input
                      name={"source-" + i}
                      defaultValue={l.progress?.source || ""}
                    />
                  </label>
                  <label>
                    یادداشت چندخطی
                    <textarea
                      name={"note-" + i}
                      defaultValue={l.progress?.notes || ""}
                    />
                  </label>
                </div>
              ))}
              <label>
                <input
                  type="checkbox"
                  name="complete"
                  style={{ width: 18, display: "inline" }}
                />{" "}
                تأمین همهٔ ردیف‌ها تکمیل شده است
              </label>
              <button className="primary" disabled={busy}>
                ثبت پیشرفت تأمین
              </button>
            </form>
          )}
        <div className="heading-actions" style={{ marginTop: 24 }}>
          {doc.status === "draft" && can("issue") && (
            <button
              className="primary"
              disabled={busy}
              onClick={() => act("issue")}
            >
              صدور سند
            </button>
          )}
          {doc.kind === "quote" && doc.status === "sent" && can("approve") && (
            <button
              className="primary"
              disabled={busy}
              onClick={() => act("approve")}
            >
              تأیید پیش‌فاکتور
            </button>
          )}
          {conversions
            .filter((kind) => can("create", kind))
            .map((kind) => (
              <button
                className="basket-count"
                disabled={busy}
                key={kind}
                onClick={() => act("convert", { kind })}
              >
                {kind === "quote" ? "ایجاد اصلاحیه" : "ساخت " + kinds[kind]}
              </button>
            ))}
        </div>
      </section>
    </div>
  );
}
export type { Doc };
