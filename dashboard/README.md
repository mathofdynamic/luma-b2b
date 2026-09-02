# LUMA B2B Review Dashboard

داشبورد محلی و خصوصی برای مرور انسانیِ پژوهش شرکت‌های B2B تهران. این ابزار برای پاسخ‌دادن سریع به سه سؤال ساخته شده است: این شرکت چیست؟ شواهد ما چیست؟ قدم بعدی قابل دفاع چیست؟

## اجرا

از ریشه‌ی repository:

```bash
npm install
npm run data:build
npm run dev
```

سپس در مرورگر به [http://127.0.0.1:5174](http://127.0.0.1:5174) بروید. سرور فقط روی loopback گوش می‌دهد و به database، cloud، حساب کاربری یا AI API نیاز ندارد.

`npm run data:build` باید پس از هر تغییر در خروجی‌های پژوهشی اجرا شود. این فرمان فایل‌های canonical را بازنویسی نمی‌کند؛ فقط `dashboard/data/index.json`، `dashboard/data/company_details.jsonl` و `dashboard/data/build-meta.json` را دوباره تولید می‌کند.

## معماری

- `dashboard/scripts/build-index.mjs` لایه‌ی ingestion و indexing است.
- `dashboard/data/index.json` فهرست سبک و قابل‌جست‌وجوی همه‌ی شرکت‌هاست.
- `dashboard/data/company_details.jsonl` جزئیات هر شرکت را برای route جزئیات نگه می‌دارد.
- `dashboard/server.mjs` یک HTTP server کوچک Node است که API محلی، فایل‌های Markdown، تصاویر evidence و demoهای repository را serve می‌کند.
- `dashboard/app/app.js` state، navigation، filtering، compare، material loading و review persistence را مدیریت می‌کند.
- `dashboard/app/views.js` لایه‌ی ارائه‌ی RTL است؛ داده‌ی شرکت‌ها داخل آن hardcode نشده است.
- `dashboard/app/styles.css` design system و رفتار responsive را نگه می‌دارد.
- فونت‌های `IRANYekanX` و `IRANYekanXFaNum` به‌صورت local در `dashboard/app/fonts/` نگه‌داری و توسط server محلی serve می‌شوند؛ داشبورد برای typography به CDN یا network runtime وابسته نیست.

شواهد متنی، source familyها، confidenceها و تفاوت fact / inference / unknown از داده‌ی اصلی حفظ می‌شوند. در صفحه‌ی detail، سندهای داخلی، proposal، outreach، dossier و فایل‌های demo به‌صورت Markdown محلی render می‌شوند.

## مرور انسانی

تصمیم‌های انسانی در `dashboard/.local/review_state.json` ذخیره می‌شوند و با `.gitignore` از commit خارج‌اند. وضعیت‌های ممکن:

- `UNREVIEWED`
- `APPROVED_FOR_OUTREACH`
- `NEEDS_MORE_RESEARCH`
- `REJECTED_BY_HUMAN`
- `FOLLOW_UP_LATER`

یادداشت، favorite و تاریخ review به داده‌ی canonical یا evidence اضافه نمی‌شوند. در نتیجه refresh مرورگر تصمیم شما را از بین نمی‌برد، اما اطلاعات خصوصی محلی هم به Git push نمی‌شود.

## مسیرهای اصلی

- Overview: جهت‌گیری سریع و شاخص کیفیت پژوهش
- Companies: جست‌وجو، فیلتر، sort و pagination برای ۶۰۰۰+ رکورد
- Sales Ready: نمای curated موج‌های تماس
- Evidence: بررسی مستقل‌بودن source family، screenshot و certainty
- Review: صف تصمیم انسانی محلی
- Compare: مقایسه‌ی ۲ تا ۴ شرکت انتخاب‌شده
- Company detail: پرونده، workflow، شواهد، sourceها، مواد فروش و تاریخچه

برای بازکردن فرمان سریع از `⌘K` در macOS یا `Ctrl+K` استفاده کنید. لینک‌های website و LinkedIn فقط actionهای بازکردن منبع‌اند؛ هیچ پیام، ایمیل، تماس یا فرم از داشبورد ارسال نمی‌شود.

## حریم خصوصی و محدودیت‌ها

این ابزار local-only است و public deploy نشده است. مسیرهای `/repo` و `/api/material` به prefixهای کنترل‌شده‌ی repository محدودند و به فایل‌های دلخواه سیستم دسترسی نمی‌دهند. داده‌ی dashboard همچنان public-research output است و private portal یا credential را وارد نمی‌کند.

در این نسخه، indexing بر اساس خروجی فعلی repository انجام شده است. اگر رکورد جدیدی به canonical outputs اضافه شود، `npm run data:build` کافی است؛ frontend برای هر شرکت جدید نیاز به تغییر دستی ندارد. برای کیفیت بالاتر هنوز قضاوت انسانی، بررسی زنده‌ی sourceها و تصمیم release لازم است.

در عرض‌های tablet و موبایل، پنل‌های مکمل پرونده به‌صورت عمودی stack می‌شوند؛ فهرست‌های بلند تماس با disclosure باز می‌شوند و اسناد Markdown در ورود مستقیم به تب مواد فروش به‌صورت خودکار load می‌شوند.

فایل‌های font با URLهای ارائه‌شده توسط کاربر در ۲ سپتامبر ۲۰۲۶ دریافت شده‌اند. مجوز و provenance آن‌ها در این repository به‌طور مستقل راستی‌آزمایی نشده است.

## تست و QA

```bash
npm run qa
```

QA ساختاری، routeهای API، سلامت index، نبودن external asset و نگاشت Sabah را بررسی می‌کند. مرور تصویری نهایی با مرورگر headless انجام می‌شود و artifactها در `dashboard/screenshots/` ذخیره می‌شوند. هیچ browser headed یا پنجره‌ی macOS برای QA لازم نیست.

## وضعیت design

فرایند طراحی و QA بهبود با OCD Designer در `dashboard/.ocd-designer/` ثبت شده است. remediation plan این run با تأیید صریح کاربر اجرا شده، اما Brand Book و release acceptance هنوز pending هستند؛ بنابراین این build به‌عنوان release نهایی یا public product معرفی نمی‌شود.
