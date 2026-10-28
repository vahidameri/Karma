import Image from "next/image";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
type Table = {
  k: string;
  sizes?: string[];
  rows?: { sym: string; q: string; v: string[] }[];
  head?: { t: string; cs?: number; rs?: number }[][];
  body?: string[][];
};
async function load(id: string) {
  if (!/^\d+$/.test(id)) notFound();
  const res = await fetch(
    `${process.env.BACKEND_URL || "http://127.0.0.1:8000"}/api/v1/standards/${id}/`,
    { cache: "no-store" },
  );
  if (res.status === 404) notFound();
  if (!res.ok) throw Error("Standard service unavailable");
  return res.json();
}
export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const s = await load(id);
  return {
    title: `${s.code} | ${s.name} | کارما`,
    description: `مشخصات فنی و جدول ابعاد استاندارد ${s.code}، ${s.name}`,
  };
}
export default async function StandardPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const standard = await load(id);
  const tables: Table[] = standard.dimensions?.tables || [];
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Product",
    name: standard.name,
    model: standard.code,
    description: `داده فنی استاندارد ${standard.code}`,
  };
  return (
    <div className="content">
      <a href="/">← بازگشت به کاتالوگ</a>
      <section className="data-panel" style={{ padding: 28, marginTop: 25 }}>
        <span className="eyebrow">KARMA / TECHNICAL REFERENCE</span>
        <h1 dir="ltr">{standard.code}</h1>
        <p dir="ltr" style={{ marginTop: 12 }}>
          {standard.name}
        </p>
        <p style={{ marginTop: 16, color: "var(--muted)" }}>
          ابعاد از فایل‌های منبع مخزن استخراج شده‌اند. موارد نیازمند بازبینی در
          گزارش ممیزی داده ثبت شده‌اند.
        </p>
        {tables.map((t, i) => (
          <section key={i} style={{ marginTop: 28 }}>
            <h2>جدول {i + 1}</h2>
            <div className="table-scroll" dir="ltr">
              {t.k === "h" ? (
                <table>
                  <thead>
                    <tr>
                      <th>Symbol</th>
                      <th>Qualifier</th>
                      {t.sizes?.map((size, j) => (
                        <th key={j}>{size}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {t.rows?.map((r, j) => (
                      <tr key={j}>
                        <th>{r.sym}</th>
                        <td>{r.q}</td>
                        {r.v.map((v, k) => (
                          <td key={k}>{v}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <table>
                  <thead>
                    {t.head?.map((row, j) => (
                      <tr key={j}>
                        {row.map((c, k) => (
                          <th key={k} colSpan={c.cs || 1} rowSpan={c.rs || 1}>
                            {c.t}
                          </th>
                        ))}
                      </tr>
                    ))}
                  </thead>
                  <tbody>
                    {t.body?.map((row, j) => (
                      <tr key={j}>
                        {row.map((cell, k) => (
                          <td key={k}>{cell}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </section>
        ))}
        {tables.length === 0 && (
          <p style={{ marginTop: 20 }}>
            برای این استاندارد، فایل مرجع ASTM را مشاهده کنید؛ جدول وب هنوز وارد
            نشده است.
          </p>
        )}
      </section>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c"),
        }}
      />
    </div>
  );
}
