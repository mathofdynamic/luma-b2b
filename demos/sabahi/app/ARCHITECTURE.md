# معماری فنی دمو صباحی

## هدف

این prototype یک مسیر قابل ارائه و deterministic برای بررسی اولیه RFQ نشان می‌دهد. هدف آن قابل تعویض بودن موتور demo با یک سرویس production است؛ نه شبیه‌سازی اتصال به ERP یا ادعای دسترسی به فرایند داخلی صباحی.

## اجزا

### `data.js`

یک لایه داده ایستا در `window.SABAHI_DEMO_DATA` است و شامل موارد زیر می‌شود:

- مرجع کوچک محصولات منتخب از صفحات عمومی صباحی؛
- URL و عنوان منبع برای هر رکورد؛
- سه RFQ ساختگی؛
- flagهای عمومی/فنی برای کنترل اینکه مشخصات حدس زده نشوند.

`data/sample-rfqs.json` نسخه قابل استناد و خوانا برای داده RFQ است. در prototype برای اجرای بدون fetch، همان fixtureها به‌صورت self-contained در `data.js` هم قرار گرفته‌اند.

### `matcher.js`

لایه deterministic استخراج و تطبیق است. `analyzeRFQ(rfqId)` خروجی استاندارد زیر را می‌سازد:

```text
{
  rfq,
  items: [{ requested, quantity, attributes, missing, confidence }],
  allMatches: [[{ product, confidence, classification, matches, missing, conflicts }]],
  clarificationCount,
  completeness,
  draft,
  kpis
}
```

در صورت نبودن گرید، استاندارد یا مشخصات فنی، آن فیلد در `missing` ثبت می‌شود. این لایه حق ندارد مقدار جاافتاده را پر کند یا قیمت/موجودی بسازد.

### `app.js`

state مرکزی شامل RFQ انتخاب‌شده، مرحله، تحلیل، متن قابل ویرایش، وضعیت approval و وضعیت presentation است. رندر مرحله‌ای باعث می‌شود presenter با یک مسیر کوتاه حرکت کند، اما همان state برای مرور عادی و آزمون‌های headless هم قابل استفاده باشد.

مراحل:

1. `input`
2. `extraction`
3. `matching`
4. `ambiguity`
5. `response`
6. `approval`

### `styles.css`

سیستم بصری self-contained با فونت‌های local/system، رنگ‌های navy/teal/amber، layout واکنش‌گرا، focus state و reduced-motion است. هیچ تصویر، font CDN، analytics یا asset بیرونی در مسیر پایه وجود ندارد.

## جایگزینی با backend واقعی

در نسخه production، یک adapter می‌تواند به‌جای `window.SABAHI_DEMO_MATCHER.analyzeRFQ` همان shape را از API برگرداند. این adapter باید:

- دسترسی و tenant را کنترل کند؛
- منبع هر claim و نسخه مرجع محصول را برگرداند؛
- confidence را با policy قابل توضیح ثبت کند؛
- UNKNOWN را از known-low جدا نگه دارد؛
- قبل از هر قیمت، انتخاب نهایی یا ارسال، approval token انسانی بگیرد؛
- timeout، خطا و fallback دستی داشته باشد.

در این prototype هیچ API call، ذخیره‌سازی بیرونی، ارسال پیام یا اتصال به حساب کاربری وجود ندارد.
