"use client";
import Image from "next/image";
import DocumentPanel, { type Doc } from "./components/DocumentPanel";
import AccessPanel from "./components/AccessPanel";
import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
type Product = {
  image_url?: string | null;
  id: number;
  standard: number;
  standard_code: string;
  system_code: string;
  technical_code: string;
  name: string;
  size: string;
  length: string;
  grade: string;
  finish: string;
};
type Me = {
  username: string;
  permissions: string[];
  units: { id: number; name: string }[];
};
type Row = Record<string, unknown>;
const fmt = (v: unknown) =>
  String(v || "0").replace(/\B(?=(\d{3})+(?!\d))/g, ",");

function today() {
  const p = new Intl.DateTimeFormat("en-US-u-ca-persian", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    timeZone: "Asia/Tehran",
  }).formatToParts(new Date());
  return ["year", "month", "day"]
    .map((k) => p.find((x) => x.type === k)?.value)
    .join("-");
}
const sections = [
  {
    key: "access",
    label: "نقش‌ها و دسترسی",
    icon: "◇",
    perm: "iam.role.manage",
  },
  { key: "catalog", label: "کاتالوگ محصولات", icon: "◈" },
  {
    key: "documents",
    label: "فروش و خرید",
    icon: "▤",
    perm: "sales.document.view",
  },
  {
    key: "parties",
    label: "مشتریان و اشخاص",
    icon: "♧",
    perm: "crm.party.view",
  },
  {
    key: "ledger",
    label: "دفتر حسابداری",
    icon: "▥",
    perm: "accounting.voucher.view",
  },
  {
    key: "payments",
    label: "خزانه و پرداخت‌ها",
    icon: "↔",
    perm: "treasury.payment.view",
  },
  {
    key: "cheques",
    label: "مدیریت چک‌ها",
    icon: "▣",
    perm: "treasury.cheque.view",
  },
  {
    key: "letters",
    label: "دبیرخانه",
    icon: "✉",
    perm: "secretariat.letter.view",
  },
];
function Fastener({ nut = false }: { nut?: boolean }) {
  return (
    <svg
      viewBox="0 0 220 140"
      role="img"
      aria-label={nut ? "نقش شماتیک مهره" : "نقش شماتیک پیچ"}
    >
      <defs>
        <linearGradient id={nut ? "nut" : "bolt"} x1="0" y1="0" x2="1" y2="1">
          <stop stopColor="#e6edf0" />
          <stop offset=".45" stopColor="#99abb3" />
          <stop offset="1" stopColor="#405862" />
        </linearGradient>
      </defs>
      {nut ? (
        <g transform="translate(110 70)">
          <path
            d="M-48 -28 0 -53 48 -28 48 28 0 53 -48 28Z"
            fill="url(#nut)"
            stroke="#4d626b"
            strokeWidth="2"
          />
          <ellipse
            rx="23"
            ry="28"
            fill="#f2f1eb"
            stroke="#607883"
            strokeWidth="8"
          />
        </g>
      ) : (
        <g transform="translate(35 73) rotate(-22)">
          <rect
            x="25"
            y="-13"
            width="139"
            height="26"
            rx="3"
            fill="url(#bolt)"
            stroke="#596f79"
          />
          {Array.from({ length: 17 }, (_, i) => (
            <path
              key={i}
              d={`M${50 + i * 6} -13 l-8 26`}
              stroke="#627b85"
              strokeWidth="1.4"
            />
          ))}
          <path
            d="M0 -26 28 -26 40 -13 40 13 28 26 0 26 -11 13 -11 -13Z"
            fill="url(#bolt)"
            stroke="#4d626b"
            strokeWidth="2"
          />
          <path
            d="M0 -26 10 -12 10 12 0 26M10 -12H40M10 12H40"
            fill="none"
            stroke="#758d97"
          />
        </g>
      )}
    </svg>
  );
}
export default function Home() {
  const [date, setDate] = useState("");
  const [section, setSection] = useState("catalog"),
    [me, setMe] = useState<Me | null>(null),
    [q, setQ] = useState(""),
    [products, setProducts] = useState<Product[]>([]),
    [loading, setLoading] = useState(true),
    [message, setMessage] = useState(""),
    [engine, setEngine] = useState(""),
    [searchHint, setSearchHint] = useState(""),
    [selected, setSelected] = useState<Product | null>(null),
    [dimensions, setDimensions] = useState<Row | null>(null),
    [loginOpen, setLoginOpen] = useState(false),
    [inquiryOpen, setInquiryOpen] = useState(false),
    [rows, setRows] = useState<Row[]>([]),
    [formOpen, setFormOpen] = useState(false),
    [documentOpen, setDocumentOpen] = useState<Doc | null>(null),
    [unit, setUnit] = useState("1"),
    [parties, setParties] = useState<Row[]>([]),
    [basket, setBasket] = useState<Product[]>([]),
    [dark, setDark] = useState(false);
  useEffect(() => {
    const refresh = () =>
      setDate(
        new Intl.DateTimeFormat("fa-IR", {
          dateStyle: "full",
          timeZone: "Asia/Tehran",
        }).format(new Date()),
      );
    refresh();
    const timer = setInterval(refresh, 60000);
    return () => clearInterval(timer);
  }, []);
  const searchRef = useRef<HTMLInputElement>(null);
  const authEpoch = useRef(0);
  const [authRevision, setAuthRevision] = useState(0);
  const [authBusy, setAuthBusy] = useState(false);
  function clearPrivate() {
    setRows([]);
    setParties([]);
    setDocumentOpen(null);
    setFormOpen(false);
  }
  function applyMe(value: Me) {
    authEpoch.current += 1;
    setAuthRevision((v) => v + 1);
    clearPrivate();
    setMe(value);
    setUnit((previous) =>
      value.units.some((u) => String(u.id) === previous)
        ? previous
        : String(value.units[0]?.id || 1),
    );
  }
  function beginAuthChange() {
    authEpoch.current += 1;
    setAuthRevision((v) => v + 1);
    clearPrivate();
    setSection("catalog");
  }

  useEffect(() => {
    if (!selected && !loginOpen && !formOpen && !inquiryOpen) return;
    const previous = document.activeElement as HTMLElement | null;
    const modal = document.querySelector(".modal") as HTMLElement | null;
    const focusable = () =>
      Array.from(
        modal?.querySelectorAll<HTMLElement>(
          "button,input,select,textarea,a[href]",
        ) || [],
      ).filter((el) => !el.hasAttribute("disabled"));
    focusable()[0]?.focus();
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setSelected(null);
        setLoginOpen(false);
        setFormOpen(false);
        setInquiryOpen(false);
      }
      if (event.key === "Tab") {
        const elements = focusable();
        if (!elements.length) return;
        const first = elements[0],
          last = elements[elements.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener("keydown", handler);
    return () => {
      document.removeEventListener("keydown", handler);
      previous?.focus();
    };
  }, [selected, loginOpen, formOpen, inquiryOpen]);
  const api = useCallback(async (path: string, options: RequestInit = {}) => {
    const epoch = authEpoch.current;
    const assertCurrent = () => {
      if (epoch !== authEpoch.current)
        throw new DOMException("Stale authentication request", "AbortError");
    };
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (options.method && options.method !== "GET") {
      const csrf = await fetch("/api/v1/session/").then((r) => r.json());
      assertCurrent();
      headers["X-CSRFToken"] = csrf.csrfToken;
    }
    const response = await fetch("/api/v1/" + path, { ...options, headers });
    assertCurrent();
    if (!response.ok) {
      if (response.status === 401 || response.status === 403) {
        clearPrivate();
        setSection("catalog");
        if(path.startsWith("me/permissions"))setMe(null);
        if (
          !path.startsWith("me/permissions") &&
          !path.startsWith("session/")
        ) {
          fetch("/api/v1/me/permissions/")
            .then((r) => (r.ok ? r.json() : null))
            .then((value) => {
              if (epoch !== authEpoch.current) return;
              if (value) applyMe(value);
              else { beginAuthChange(); setMe(null); }
            })
            .catch(() => {});
        }
      }
      let detail;
      try {
        detail = await response.json();
      } catch {
        detail = { detail: `خطای سرویس (${response.status})` };
      }
      assertCurrent();
      throw Error(
        typeof detail.detail === "string"
          ? detail.detail
          : JSON.stringify(detail),
      );
    }
    const value = response.status === 204 ? null : await response.json();
    assertCurrent();
    if(options.method&&options.method!=="GET"&&/^(roles|users|scopes|overrides)\//.test(path)){
      const refreshed=await fetch("/api/v1/me/permissions/").then(r=>r.ok?r.json():null);assertCurrent();if(refreshed)applyMe(refreshed);
    }
    return value;
  }, []);
  const loadRows = useCallback(() => {
    if (["catalog", "access"].includes(section)) return;
    const epoch = authEpoch.current;
    setRows([]);
    setLoading(true);
    api(
      section === "ledger"
        ? `ledger/?unit=${unit}`
        : `${section}/?unit=${unit}`,
    )
      .then(setRows)
      .catch((e) => {
        if (e.name !== "AbortError") setMessage(e.message);
      })
      .finally(() => {
        if (epoch === authEpoch.current) setLoading(false);
      });
  }, [api, section, unit]);
  useEffect(() => {
    api("me/permissions/")
      .then(applyMe)
      .catch(() => {});
    const saved = localStorage.getItem("karma-theme") === "dark";
    setDark(saved);
    document.documentElement.dataset.theme = saved ? "dark" : "light";
  }, [api]);
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        setSection("catalog");
        searchRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);
  useEffect(() => {
    if (section !== "catalog") {
      loadRows();
      return;
    }
    const controller = new AbortController();
    const timer = setTimeout(() => {
      setLoading(true);
      fetch("/api/v1/products/?q=" + encodeURIComponent(q), {
        signal: controller.signal,
      })
        .then((r) => {
          if (!r.ok) throw Error("دریافت کاتالوگ ناموفق بود");
          return r.json();
        })
        .then((data) => {
          setProducts(
            data.results.map(
              ({ cost: _cost, ...product }: Product & { cost?: unknown }) =>
                product,
            ),
          );
          setEngine(data.engine);
          setSearchHint(data.query?.notice || "");
        })
        .catch((e) => {
          if (e.name !== "AbortError") {
            setProducts([]);
            setMessage(e.message);
          }
        })
        .finally(() => {
          if (!controller.signal.aborted) setLoading(false);
        });
    }, 250);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [
    q,
    section,
    loadRows,
    me?.username,
    me?.permissions.join("|"),
    authRevision,
  ]);
  useEffect(() => {
    if (formOpen && section === "documents")
      api("parties/")
        .then(setParties)
        .catch((e) => setMessage(e.message));
  }, [formOpen, section, api, unit, me?.username]);
  async function login(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.currentTarget));
    beginAuthChange();
    setAuthBusy(true);
    try {
      await api("session/", { method: "POST", body: JSON.stringify(data) });
      applyMe(await api("me/permissions/"));
      setLoginOpen(false);
      setMessage("با موفقیت وارد شدید");
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setAuthBusy(false);
    }
  }
  async function sendInquiry(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const values = Object.fromEntries(new FormData(e.currentTarget));
    try {
      await api("inquiries/", {
        method: "POST",
        body: JSON.stringify({
          ...values,
          business_unit: Number(unit),
          items: basket.map((p) => ({
            product: p.id,
            quantity: values["inquiry-qty-" + p.id] || "1",
          })),
        }),
      });
      setBasket([]);
      setInquiryOpen(false);
      setMessage("درخواست استعلام شما ثبت شد.");
    } catch (e) {
      setMessage((e as Error).message);
    }
  }
  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const values = Object.fromEntries(new FormData(e.currentTarget));
    let payload: Row = { ...values, business_unit: Number(unit) };
    if (section === "documents") {
      payload = {
        ...payload,
        customer: Number(values.customer),
        lines: basket.map((p) => ({
          product: p.id,
          quantity: values[`qty-${p.id}`] || "1",
          unit_price: values[`price-${p.id}`] || "0",
        })),
      };
    }

    try {
      await api(section + "/", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setFormOpen(false);
      loadRows();
      setMessage("پیش‌نویس ذخیره شد");
    } catch (e) {
      setMessage((e as Error).message);
    }
  }
  async function action(id: unknown, name: string) {
    try {
      await api(`documents/${id}/${name}/`, { method: "POST", body: "{}" });
      loadRows();
      setMessage(
        name === "issue"
          ? "سند صادر شد؛ رویداد حسابداری در صف است"
          : "سند باطل شد",
      );
    } catch (e) {
      setMessage((e as Error).message);
    }
  }
  async function detail(p: Product) {
    setSelected(p);
    setDimensions(null);
    try {
      setDimensions(await api(`standards/${p.standard}/`));
    } catch (e) {
      setMessage((e as Error).message);
    }
  }
  const current = sections.find((s) => s.key === section)!;
  const basicCanCreate = me?.permissions.includes(
    (
      {
        documents: "sales.document.create",
        parties: "crm.party.create",
        letters: "secretariat.letter.create",
        settings: "settings.revision.create",
      } as Record<string, string>
    )[section],
  );
  const canCreate =
    basicCanCreate ||
    (section === "documents" &&
      ["quote", "invoice", "purchase"].some((kind) =>
        me?.permissions.includes(`sales.${kind}.create`),
      ));
  return (
    <div className="shell">
      <aside className="sidebar">
        <a href="/" className="brand">
          <span className="brand-mark">K</span>
          <span>
            کارما<small>KARMA INDUSTRIAL GROUP</small>
          </span>
        </a>
        <div className="workspace">
          <span className="status-dot" /> فضای کار یکپارچه{" "}
          <small>نسخهٔ آزمایشی ۲٫۰٫۰</small>
        </div>
        <p className="nav-title">فضای کار شما</p>
        <nav>
          {sections
            .filter(
              (s) =>
                !s.perm ||
                me?.permissions.includes(s.perm) ||
                (s.key === "documents" &&
                  me?.permissions.some(
                    (p) => p.startsWith("sales.") && p.endsWith(".view"),
                  )),
            )
            .map((s) => (
              <button
                key={s.key}
                className={section === s.key ? "active" : ""}
                onClick={() => {
                  setSection(s.key);
                  setMessage("");
                }}
              >
                <span>{s.icon}</span>
                {s.label}
                {s.key === "catalog" && <small>DIN / ASTM</small>}
              </button>
            ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="help-card">
            <span>دادهٔ دقیق، انتخاب مطمئن</span>
            <p>ابعاد استاندارد و کد فنی محصولات، در یک مرجع.</p>
          </div>
          {me && (
            <a className="admin-link" href="/admin/">
              مدیریت نقش‌ها و دسترسی‌ها ↗
            </a>
          )}
          <button
            className="profile"
            disabled={authBusy}
            onClick={() => {
              setMessage("");
              setLoginOpen(true);
            }}
          >
            <span className="avatar">{me ? "ک" : "↗"}</span>
            <span>
              {me?.username || "ورود به فضای کارکنان"}
              <small>{me ? "حساب کاربری" : "دسترسی امن به سامانه"}</small>
            </span>
          </button>
        </div>
      </aside>
      <main>
        <header>
          <div className="breadcrumbs">
            کارما <span>/</span> {current.label}
          </div>
          <div className="top-actions">
            <span>{date}</span>
            <button
              aria-label="تغییر پوسته"
              onClick={() => {
                document.documentElement.dataset.theme = dark
                  ? "light"
                  : "dark";
                localStorage.setItem("karma-theme", dark ? "light" : "dark");
                setDark(!dark);
              }}
            >
              {dark ? "☀" : "◐"}
            </button>
            {me && (
              <button
                disabled={authBusy}
                onClick={async () => {
                  beginAuthChange();
                  setMe(null);
                  setBasket([]);
                  setUnit("1");
                  setAuthBusy(true);
                  try {
                    await api("session/", { method: "DELETE" });
                  } catch (e) {
                    setMessage((e as Error).message);
                  } finally {
                    setAuthBusy(false);
                  }
                }}
              >
                خروج
              </button>
            )}
          </div>
        </header>
        <div className="content">
          <div className="page-heading">
            <div>
              <span className="eyebrow">KARMA / WORKSPACE</span>
              <h1>{current.label}</h1>
              <p>
                {section === "catalog"
                  ? "از استاندارد تا انتخاب؛ مشخصات فنی را سریع و دقیق پیدا کنید."
                  : "اطلاعات مشترک، گردش کار مشخص و کنترل در سمت سرور."}
              </p>
            </div>
            <div className="heading-actions">
              {section === "catalog" ? (
                <button
                  className="basket-count"
                  onClick={() => setInquiryOpen(true)}
                >
                  لیست انتخاب <b>{basket.length}</b>
                </button>
              ) : (
                <>
                  <label className="unit-label">
                    واحد تجاری
                    <select
                      aria-label="واحد تجاری"
                      value={unit}
                      onChange={(e) => setUnit(e.target.value)}
                    >
                      {me?.units.map((u) => (
                        <option key={u.id} value={String(u.id)}>
                          {u.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  {canCreate && (
                    <button
                      className="primary"
                      onClick={() => setFormOpen(true)}
                    >
                      ＋ ثبت جدید
                    </button>
                  )}
                </>
              )}
            </div>
          </div>
          {message && (
            <div className="notice" role="status">
              {message}
              <button aria-label="بستن پیام" onClick={() => setMessage("")}>
                ×
              </button>
            </div>
          )}
          {section === "catalog" ? (
            <>
              <section className="hero">
                <div>
                  <span className="hero-tag">مرجع فنی اتصالات صنعتی</span>
                  <h2>
                    جزئیات کوچک.
                    <br />
                    <em>اتصال‌های بزرگ.</em>
                  </h2>
                  <p>
                    داده‌های استاندارد DIN، کدهای پایدار و جدول‌های ابعادی
                    <br />
                    برای تصمیم‌گیری دقیق در هر سفارش.
                  </p>
                  <div className="hero-meta">
                    <span>
                      DIN <b>۳۲۹ استاندارد منبع</b>
                    </span>
                    <i />
                    <span>
                      دادهٔ فنی <b>قابل ردیابی تا منبع</b>
                    </span>
                  </div>
                </div>
                <div className="hero-art">
                  <Fastener />
                  <span className="dimension-mark">M × L</span>
                  <span className="art-caption">ENGINEERED TO CONNECT</span>
                </div>
              </section>
              <section className="search-section">
                <div className="search-box">
                  <span aria-hidden>⌕</span>
                  <input
                    ref={searchRef}
                    aria-label="جستجوی محصول"
                    placeholder="نام کالا، کد فنی یا ابعاد… مثلاً پیچ آلن ۸ در ۲۰"
                    value={q}
                    onChange={(e) => setQ(e.target.value)}
                  />
                  <kbd>Ctrl K</kbd>
                </div>
                <div className="quick-filters">
                  <span>پیشنهاد جستجو</span>
                  {[
                    "پیچ آلن",
                    "مهره ۱۶",
                    "واشر فنری ۱۰",
                    "DIN933 M10",
                    "M8X20",
                  ].map((t) => (
                    <button
                      key={t}
                      className={q === t ? "selected" : ""}
                      onClick={() => setQ(q === t ? "" : t)}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </section>
              {searchHint && <p className="notice">{searchHint}</p>}
              <div className="results-heading">
                <h2>
                  {q ? "نتیجهٔ جستجو" : "محصولات کاتالوگ"}{" "}
                  <span>{products.length} مورد نمایش‌داده‌شده</span>
                </h2>
                <div className="engine">
                  <span className="status-dot" />
                  {engine === "elasticsearch"
                    ? "Elasticsearch"
                    : "جستجوی توسعه"}
                </div>
              </div>
              {loading ? (
                <div className="empty">در حال دریافت اطلاعات…</div>
              ) : products.length === 0 ? (
                <div className="empty">
                  کالایی با این مشخصات پیدا نشد.
                  <button onClick={() => setQ("")}>نمایش همه محصولات</button>
                </div>
              ) : (
                <div className="product-grid">
                  {products.map((p) => (
                    <article key={p.id} className="product-card">
                      <div className="product-image">
                        <span className="standard-tag">{p.standard_code}</span>
                        {p.image_url ? (
                          <Image
                            src={p.image_url}
                            alt={p.name}
                            width={220}
                            height={140}
                            style={{
                              objectFit: "contain",
                              maxWidth: "85%",
                              height: "85%",
                            }}
                          />
                        ) : (
                          <Fastener
                            nut={
                              p.standard_code.includes("934") ||
                              p.standard_code.includes("125")
                            }
                          />
                        )}
                        {!p.image_url && (
                          <span className="schematic">نمای شماتیک</span>
                        )}
                      </div>
                      <div className="product-info">
                        <div className="product-code" dir="ltr">
                          {p.system_code}
                        </div>
                        <h3>{p.name}</h3>
                        <p dir="ltr" className="tech-code">
                          {p.technical_code}
                        </p>
                        <div className="specs">
                          <span>
                            سایز <b dir="ltr">{p.size}</b>
                          </span>
                          <span>
                            طول <b>{p.length || "—"}</b>
                          </span>
                          <span>
                            گرید <b>{p.grade || "تعیین نشده"}</b>
                          </span>
                        </div>
                        <div className="card-actions">
                          <button onClick={() => detail(p)}>
                            مشخصات فنی ↗
                          </button>
                          <button
                            className={
                              basket.some((x) => x.id === p.id) ? "added" : ""
                            }
                            aria-label={`انتخاب ${p.technical_code}`}
                            onClick={() =>
                              setBasket(
                                basket.some((x) => x.id === p.id)
                                  ? basket.filter((x) => x.id !== p.id)
                                  : [...basket, p],
                              )
                            }
                          >
                            {basket.some((x) => x.id === p.id) ? "✓" : "＋"}
                          </button>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
              )}
              <div className="catalog-note">
                سایزهای استخراج‌شده بدون جنس، گرید و پوشش قطعی هستند. انتخاب در
                این فهرست به معنی موجودی یا ثبت سفارش نیست.
              </div>
            </>
          ) : section === "access" ? (
            <AccessPanel api={api} />
          ) : (
            <section className="data-panel">
              <div className="panel-heading">
                <h2>{current.label}</h2>
                <button onClick={loadRows}>↻ به‌روزرسانی</button>
              </div>
              {loading ? (
                <div className="empty">در حال دریافت…</div>
              ) : rows.length === 0 ? (
                <div className="empty">هنوز رکوردی ثبت نشده است.</div>
              ) : (
                <div className="table-scroll">
                  <table>
                    <thead>
                      <tr>
                        {(section === "documents"
                          ? [
                              "شماره",
                              "نوع",
                              "تاریخ",
                              "وضعیت",
                              "مبلغ (ریال)",
                              "عملیات",
                            ]
                          : section === "parties"
                            ? ["نام", "موبایل", "شهر", "واحد تجاری"]
                            : section === "ledger"
                              ? ["کد حساب", "نام حساب", "بدهکار", "بستانکار"]
                              : ["شناسه", "شرح", "تاریخ", "وضعیت"]
                        ).map((t) => (
                          <th key={t}>{t}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map((r, i) => (
                        <tr key={String(r.id || i)}>
                          {section === "documents" ? (
                            <>
                              <td dir="ltr">
                                {String(r.number || "پیش‌نویس")}
                              </td>
                              <td>{String(r.kind)}</td>
                              <td>{String(r.doc_date)}</td>
                              <td>
                                <span className="badge">
                                  {String(r.status)}
                                </span>
                              </td>
                              <td className="numeric">{fmt(r.total)}</td>
                              <td className="row-actions">
                                <button
                                  onClick={() => setDocumentOpen(r as Doc)}
                                >
                                  جزئیات
                                </button>
                                {r.status === "draft" &&
                                  me?.permissions.includes(
                                    "sales.document.issue",
                                  ) && (
                                    <button
                                      onClick={() => action(r.id, "issue")}
                                    >
                                      صدور
                                    </button>
                                  )}
                                {r.status === "issued" &&
                                  me?.permissions.includes(
                                    "sales.document.void",
                                  ) && (
                                    <button
                                      onClick={() => {
                                        if (
                                          confirm(
                                            "سند باطل و ثبت حسابداری آن معکوس شود؟",
                                          )
                                        )
                                          action(r.id, "void");
                                      }}
                                    >
                                      ابطال
                                    </button>
                                  )}
                                {me?.permissions.includes(
                                  "sales.document.print",
                                ) && (
                                  <a
                                    href={`/api/v1/documents/${r.id}/pdf/`}
                                    target="_blank"
                                    rel="noreferrer"
                                  >
                                    PDF ↗
                                  </a>
                                )}
                              </td>
                            </>
                          ) : section === "parties" ? (
                            <>
                              <td>{String(r.name)}</td>
                              <td dir="ltr">{String(r.mobile || "—")}</td>
                              <td>{String(r.city || "—")}</td>
                              <td>{String(r.business_unit)}</td>
                            </>
                          ) : section === "ledger" ? (
                            <>
                              <td>{String(r.account__code)}</td>
                              <td>{String(r.account__name)}</td>
                              <td className="numeric">{fmt(r.debit)}</td>
                              <td className="numeric">{fmt(r.credit)}</td>
                            </>
                          ) : (
                            <>
                              <td>{String(r.id)}</td>
                              <td>
                                {String(
                                  r.subject ||
                                    r.key ||
                                    r.number ||
                                    r.party ||
                                    "—",
                                )}
                              </td>
                              <td>
                                {String(
                                  r.doc_date ||
                                    r.due_date ||
                                    r.created_at ||
                                    "—",
                                )}
                              </td>
                              <td>
                                {String(r.state || r.status || r.amount || "—")}
                              </td>
                            </>
                          )}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          )}
          <footer>
            <span>
              گروه صنعتی کارما <b> / </b> آلیاژ پیچ کار ماد
            </span>
            <span>نسخهٔ آزمایشی ۲٫۰٫۰ · مبالغ به ریال</span>
          </footer>
        </div>
      </main>
      {documentOpen && (
        <DocumentPanel
          document={documentOpen}
          api={api}
          onClose={() => setDocumentOpen(null)}
          onChange={loadRows}
          permissions={me?.permissions || []}
        />
      )}
      {selected && (
        <div className="modal-backdrop" onClick={() => setSelected(null)}>
          <section
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-label="مشخصات فنی"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="close"
              aria-label="بستن"
              onClick={() => setSelected(null)}
            >
              ×
            </button>
            <span className="eyebrow">TECHNICAL DATA</span>
            <h2>{selected.name}</h2>
            <p dir="ltr">{selected.technical_code}</p>
            <h3>جدول ابعاد استاندارد</h3>
            <a className="admin-link" href={`/standards/${selected.standard}`}>
              مشاهدهٔ صفحهٔ استاندارد و جدول‌ها ↗
            </a>
            {dimensions ? (
              <pre dir="ltr">
                {JSON.stringify(dimensions.dimensions, null, 2)}
              </pre>
            ) : (
              <p>در حال دریافت جدول…</p>
            )}
          </section>
        </div>
      )}
      {inquiryOpen && (
        <div className="modal-backdrop">
          <form
            className="modal narrow"
            role="dialog"
            aria-modal="true"
            aria-label="ثبت استعلام"
            onSubmit={sendInquiry}
          >
            <button
              type="button"
              className="close"
              aria-label="بستن"
              onClick={() => setInquiryOpen(false)}
            >
              ×
            </button>
            <h2>لیست استعلام شما</h2>
            {basket.length === 0 ? (
              <p>هنوز کالایی انتخاب نکرده‌اید.</p>
            ) : (
              <>
                {basket.map((p) => (
                  <label key={p.id}>
                    <span dir="ltr">{p.technical_code}</span>
                    <input
                      name={"inquiry-qty-" + p.id}
                      type="number"
                      min="0.001"
                      step="0.001"
                      defaultValue="1"
                      aria-label={"تعداد " + p.technical_code}
                      required
                    />
                  </label>
                ))}
                <label>
                  نام و نام خانوادگی
                  <input name="name" required maxLength={200} />
                </label>
                <label>
                  شماره موبایل
                  <input name="mobile" dir="ltr" inputMode="tel" required />
                </label>
                <button className="primary">ثبت درخواست استعلام</button>
              </>
            )}
          </form>
        </div>
      )}
      {loginOpen && (
        <div className="modal-backdrop">
          <form className="modal narrow" onSubmit={login}>
            <button
              type="button"
              className="close"
              aria-label="بستن"
              onClick={() => setLoginOpen(false)}
            >
              ×
            </button>
            <span className="eyebrow">KARMA / SECURE ACCESS</span>
            <h2>ورود به فضای کارکنان</h2>
            <p>از حسابی که مدیر سامانه تعریف کرده استفاده کنید.</p>
            {message && <p role="alert">{message}</p>}
            <label>
              نام کاربری
              <input
                name="username"
                required
                autoComplete="username"
                dir="ltr"
              />
            </label>
            <label>
              رمز عبور
              <input
                name="password"
                type="password"
                required
                autoComplete="current-password"
                dir="ltr"
              />
            </label>
            <label>
              رمز دومرحله‌ای (حساب‌های حساس)
              <input
                name="otp"
                inputMode="numeric"
                autoComplete="one-time-code"
                dir="ltr"
              />
            </label>
            <button className="primary" disabled={authBusy}>
              ورود امن ←
            </button>
          </form>
        </div>
      )}
      {formOpen && (
        <div className="modal-backdrop">
          <form className="modal" onSubmit={save}>
            <button
              type="button"
              className="close"
              aria-label="بستن"
              onClick={() => setFormOpen(false)}
            >
              ×
            </button>
            <h2>ثبت {current.label}</h2>
            {section === "parties" ? (
              <>
                <label>
                  نام / شرکت
                  <input name="name" required />
                </label>
                <label>
                  نوع
                  <select name="kind">
                    <option value="person">حقیقی</option>
                    <option value="company">حقوقی</option>
                  </select>
                </label>
                <div className="form-grid">
                  <label>
                    موبایل
                    <input name="mobile" dir="ltr" />
                  </label>
                  <label>
                    شناسه ملی
                    <input name="national_id" dir="ltr" />
                  </label>
                  <label>
                    شهر
                    <input name="city" />
                  </label>
                  <label>
                    کد اقتصادی
                    <input name="economic_code" />
                  </label>
                </div>
                <label>
                  نشانی
                  <textarea name="address" />
                </label>
              </>
            ) : section === "documents" ? (
              <>
                <div className="form-grid">
                  <label>
                    نوع سند
                    <select name="kind">
                      {[
                        ["quote", "پیش‌فاکتور"],
                        ["invoice", "فاکتور فروش"],
                        ["purchase", "فاکتور خرید"],
                      ]
                        .filter(
                          ([v]) =>
                            me?.permissions.includes("sales.document.create") ||
                            me?.permissions.includes(`sales.${v}.create`),
                        )
                        .map(([v, l]) => (
                          <option key={v} value={v}>
                            {l}
                          </option>
                        ))}
                    </select>
                  </label>
                  <label>
                    تاریخ سند (شمسی)
                    <input
                      name="doc_date"
                      defaultValue={today()}
                      pattern="[0-9]{4}-[0-9]{2}-[0-9]{2}"
                      dir="ltr"
                      required
                    />
                  </label>
                </div>
                <label>
                  انتخاب مشتری
                  <select name="customer" required>
                    <option value="">یک مشتری انتخاب کنید</option>
                    {parties
                      .filter((p) => String(p.business_unit) === unit)
                      .map((p) => (
                        <option key={String(p.id)} value={String(p.id)}>
                          {String(p.name)} · {String(p.mobile || "")}
                        </option>
                      ))}
                  </select>
                </label>
                <h3>کالاهای انتخاب‌شده از کاتالوگ</h3>
                {basket.length === 0 ? (
                  <p>
                    ابتدا از کاتالوگ، کالاهای سند را با دکمهٔ + انتخاب کنید.
                  </p>
                ) : (
                  basket.map((p) => (
                    <div className="line-input" key={p.id}>
                      <span dir="ltr">{p.technical_code}</span>
                      <label>
                        تعداد
                        <input
                          name={`qty-${p.id}`}
                          type="number"
                          min="0.001"
                          step="0.001"
                          defaultValue="1"
                          required
                        />
                      </label>
                      <label>
                        قیمت واحد (ریال)
                        <input
                          name={`price-${p.id}`}
                          type="number"
                          min="0"
                          step="1"
                          required
                        />
                      </label>
                    </div>
                  ))
                )}
                <div className="form-grid">
                  <label>
                    نرخ مالیات ٪
                    <input
                      name="tax_rate"
                      type="number"
                      min="0"
                      max="100"
                      step="0.01"
                      defaultValue="0"
                    />
                  </label>
                  <label>
                    تخفیف (ریال)
                    <input
                      name="discount"
                      type="number"
                      min="0"
                      defaultValue="0"
                    />
                  </label>
                </div>
                <label>
                  توضیحات
                  <textarea name="notes" />
                </label>
              </>
            ) : section === "letters" ? (
              <>
                <label>
                  نوع نامه
                  <select name="kind">
                    <option value="incoming">وارده</option>
                    <option value="outgoing">صادره</option>
                    <option value="internal">داخلی</option>
                  </select>
                </label>
                <label>
                  موضوع
                  <input name="subject" required />
                </label>
                <label>
                  تاریخ شمسی
                  <input
                    name="doc_date"
                    defaultValue={today()}
                    required
                    dir="ltr"
                  />
                </label>
                <label>
                  متن نامه
                  <textarea name="body" required />
                </label>
              </>
            ) : null}
            <button
              className="primary"
              disabled={section === "documents" && basket.length === 0}
            >
              ذخیرهٔ پیش‌نویس
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
