# کارما — نسخهٔ 2.0.0-alpha.1

این نسخه یک **نسخهٔ توسعهٔ اجراشدنی** از بازنویسی است؛ جایگزین آمادهٔ بهره‌برداری برای نسخهٔ ۱٫۳ نیست و تکمیل تمام شش فاز سند تحویل محسوب نمی‌شود. وضعیت هر بخش و کارهای باقی‌مانده در [گزارش تحویل](docs/RELEASE-2.0.0-alpha.1.md) مشخص شده است.

## آنچه قابل اجراست

- Django 5.2 / DRF، PostgreSQL 16، Redis و Celery؛ Next.js / TypeScript با RTL، فونت وزیرمتن، پوستهٔ روشن و تیره و نمای موبایل.
- نقش و مجوز قابل تعریف، ماتریس نقش‌ها، استثنای allow/deny، محدودهٔ واحد تجاری و رکوردهای خود کاربر؛ اعمال مجوز در API. قیمت تمام‌شده از API و Excel کاربران فاقد مجوز حذف می‌شود.
- ورود با Session و CSRF، Argon2، الزام TOTP برای حساب‌های حساس و پنل مدیریت، محدودیت تلاش ورود، گزارش ممیزی با منع تغییر و حذف در دیتابیس.
- مهاجرت ۲۱٬۲۹۷ کد KR واقعی، ۳۵۰ استاندارد، ۶۱۳ alias کد فنی قدیمی و ۱٬۰۲۰ تصویر از بستهٔ ارائه‌شده. فایل‌های حساب‌های کاربری و رمزهای نمونهٔ نسخهٔ قدیمی وارد این پروژه نشده‌اند.
- جستجوی Elasticsearch با نرمال‌سازی فارسی و پارسر ویژگی‌ها؛ تطبیق دقیق کد، نمایش هشدار برای نتایج تقریبی؛ بازسازی ایندکس با تعویض اتمیک alias. صفحهٔ استاندارد SSR و جدول‌های ابعاد.
- CRM پایه، استعلام عمومی با سقف ده درخواست روزانه برای هر موبایل، پیش‌نویس و صدور اسناد، تأیید پیش‌فاکتور، برگهٔ تأمین، تبدیل به فاکتور و بسته‌بندی، برگشتی و ابطال؛ تاریخ شمسی و زمان سیستمی جدا، مشخصات مشتری/کالا و قواعد ثبت در snapshot.
- دفترکل دوطرفه، جلوگیری از ثبت نامتوازن، منع تغییر سند دائم در دیتابیس، سند معکوس، قواعد ثبت قابل تنظیم، outbox با retry و idempotency؛ تأمین و بسته‌بندی اثر انباری یا حسابداری ندارند.
- API پرداخت و تخصیص، چرخهٔ چک، حقوق با نرخ‌های قابل تنظیم، بستن سال به روش ادواری؛ این بخش‌ها هنوز همهٔ رابط‌ها و گزارش‌های سند اصلی را ندارند.
- PDF سمت سرور با وزیرمتن و منع دریافت منابع خارجی؛ آزمون صفحه‌بندی ۱۵ ردیف در یک صفحه و ۴۰ ردیف در دو صفحه.

## اجرای توسعه با Docker

پیش‌نیاز: Docker Engine / Compose، حدود ۴ گیگابایت RAM آزاد و دسترسی به رجیستری‌های بسته و تصاویر. فرمان‌ها از پوشهٔ `platform/` اجرا شوند:

```bash
python3 scripts/init_env.py
docker compose build backend frontend
docker compose up -d postgres redis elasticsearch
docker compose run --rm backend python manage.py migrate --noinput
docker compose run --rm backend python manage.py seed_platform
docker compose run --rm backend python manage.py seed_accounts
docker compose run --rm backend python manage.py import_legacy_catalog --source /source/legacy
docker compose run --rm backend python manage.py import_dimensions /source/output/DIN_full_tables.json /source/legacy/astm-dimensions.json
docker compose run --rm backend python manage.py reindex
docker compose up -d backend frontend worker beat
```

در محیط ابری دارای پراکسی، به‌جای فرمان build از `python3 scripts/cloud_build.py` استفاده کنید. این فرمان پراکسی و CA معتبر تزریق‌شده را فقط برای build به Docker می‌دهد؛ بررسی TLS را غیرفعال نمی‌کند و CA را داخل تصویر نهایی نگه نمی‌دارد.

رابط روی پورت ۳۰۰۰ و API روی ۸۰۰۰، فقط روی loopback، اجرا می‌شوند. `BACKEND_PORT` و `FRONTEND_PORT` قابل تغییرند. سلامت API در `/api/v1/health/`، پنل مدیریت در `/admin/` و مستندات API در `/api/v1/docs/` قرار دارند. مستندات API نیاز به ورود مدیر دارند.

`init_env.py` فقط یک بار مقادیر تصادفی توسعه تولید می‌کند و فایل موجود را بازنویسی نمی‌کند. هیچ نام کاربری یا رمز عبور پیش‌فرضی وجود ندارد:

```bash
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py enroll_totp YOUR_USERNAME
```

URI فعال‌سازی TOTP یک اعتبارنامه است؛ فقط در ترمینال خصوصی خود به برنامهٔ احراز هویت اضافه کنید. برای مدیر سیستم و حساب‌های دارای مجوز حسابداری/حقوق/مدیریت دسترسی، ورود بدون TOTP مجاز نیست. پس از ورود مدیر، نقش‌ها، کاربران و محدوده‌ها را تنظیم کنید. پیش از صدور نخستین سند، سال مالی و دورهٔ باز واحد تجاری را در مدیریت تعریف کنید. قواعد حسابداری و نرخ‌های حقوق باید توسط حسابدار شرکت تأیید و تنظیم شوند.

## اجرای بدون کانتینر برنامه

برای توسعهٔ سریع می‌توان از Python 3.12 و Node 24 استفاده کرد. کتابخانه‌های Pango و HarfBuzz سیستم برای PDF لازم‌اند:

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements-dev.txt
cd backend
../.venv/bin/python manage.py migrate
../.venv/bin/python manage.py seed_platform
../.venv/bin/python manage.py seed_accounts
../.venv/bin/python manage.py import_legacy_catalog --source ../data/legacy
../.venv/bin/python manage.py import_dimensions ../../output/DIN_full_tables.json ../data/legacy/astm-dimensions.json
../.venv/bin/python manage.py runserver 8000
```

در ترمینال دیگری از `platform/frontend/`، `npm ci` و سپس `npm run dev` را اجرا کنید. بدون `POSTGRES_HOST`، SQLite و بدون `ELASTICSEARCH_URL`، جستجوی محدود توسعه استفاده می‌شود؛ این حالت معیار کارایی یا هم‌زمانی تولید نیست. برای جلوگیری از گرد شدن NUMERIC در SQLite، ثبت مبلغ با قدر مطلق ۱٬۰۰۰٬۰۰۰٬۰۰۰٬۰۰۰٬۰۰۰ ریال یا بیشتر در این حالت رد می‌شود؛ مبالغ بزرگ در PostgreSQL با دقت کامل پشتیبانی می‌شوند. حالت تولید بدون PostgreSQL راه‌اندازی نمی‌شود. برای استفاده از سرویس‌های Docker و اجرای برنامه روی میزبان، `scripts/with_services.py` تنظیمات محلی `.env` را می‌خواند، بدون چاپ مقادیر آن‌ها. اطلاعات واقعی را در فایل‌های نمونه یا Git قرار ندهید.

## آزمون‌ها

از `platform/backend/`:

```bash
python manage.py makemigrations --check --dry-run
python manage.py test tests --noinput
ruff check .
ruff format --check .
```

از `platform/frontend/`:

```bash
npm ci
npm run build
npx playwright install chromium
npm test
```

چهار آزمون کاتالوگ/موبایل روی برنامهٔ در حال اجرا انجام می‌شوند. آزمون پنجم زنجیرهٔ فروش به دیتابیس **دورریختنی** نیاز دارد؛ بدون `KARMA_E2E_CREDENTIALS` عمداً skip می‌شود. در اعتبارسنجی این نسخه هر پنج آزمون اجرا شده‌اند، بدون skip. CI برای آن دیتابیس `karma_e2e`، کاربر موقت، worker و beat می‌سازد. `scripts/e2e_fixture.py` روی دیتابیس دیگری اجرا نمی‌شود. آن را روی دیتابیس اصلی اجرا نکنید. CI تعریف شده؛ نتیجهٔ اجرای GitHub Actions هنوز در این تحویل وجود ندارد.

## داده، پشتیبان و انتشار

- منابع محصولات در `data/legacy/` فقط داده‌های کاتالوگ و تصاویر هستند؛ کد HTML/Apps Script و حساب‌های نمونه کپی نشده‌اند.
- `import_legacy_catalog` تکرارپذیر است، کد KR متعارض را بازنویسی نمی‌کند و مغایرت را با خطا متوقف می‌کند. برای انتقال به یک دیتابیس دارای کالاهای آزمایشی، از دیتابیس تازه استفاده کنید.
- تصاویر توسعه در storage فایل Django هستند و volume `media` باید حفظ شود. اتصال S3/MinIO و پشتیبان Object Storage هنوز تکمیل نشده است.
- `python3 scripts/backup.py --verify` از دیتابیس نسخهٔ محلی پشتیبان خصوصی می‌گیرد و آن را در دیتابیس تازه بازیابی و کنترل می‌کند؛ دیتابیس موقت بعد از بررسی حذف می‌شود. زمان‌بندی روزانه، نگهداری ۳۰ روزه و آزمون ماهانه باید در استقرار واقعی تنظیم شوند.
- Compose حاضر تنظیمات توسعه دارد. انتشار تولیدی، TLS، دامنه، سرویس‌های پیامک/ایمیل/درگاه/مؤدیان و بررسی مستقل امنیتی انجام نشده‌اند. نمونهٔ Nginx صرفاً در `deploy/` ارائه شده است.
- هر وظیفهٔ ابری از قبل محیط مجزا دارد؛ از checkout موجود استفاده کنید و بدون درخواست صریح، Git worktree نسازید.
