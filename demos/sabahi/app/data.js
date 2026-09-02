/*
 * Sabahi demo data layer.
 *
 * Product facts are limited to the public pages listed on each record. RFQs
 * and customer names are synthetic. Keep this file deterministic so the demo
 * remains usable in a sales meeting without a network or an AI API.
 */
window.SABAHI_DEMO_DATA = {
  meta: {
    company: "شرکت صباحی",
    badge: "نمونه پیشنهادی LUMA برای نمایش قابلیت",
    researchUpdated: "۱۴۰۵/۰۶/۱۱",
    noExternalAi: true
  },
  products: [
    {
      id: "pexide-mv-35-alpha",
      name: "Pexide MV 35kV Alpha",
      faName: "پکساید MV 35kV · گرید Alpha",
      family: "Pexide",
      type: "technical_material",
      tags: ["pexide", "mv", "35kv", "alpha", "xlpe", "کابل", "فشار متوسط"],
      attributes: [
        { label: "کلاس ولتاژ", value: "MV · تا ۳۵ kV" },
        { label: "گرید", value: "Alpha" },
        { label: "ویژگی عمومی", value: "≤ ۱۰ ناخالصی در ۱۰۰۰ گرم برای >۱۰۰μm" },
        { label: "کاربرد", value: "عایق کابل فشار متوسط" }
      ],
      sourceUrl: "https://sabahi.com/en/pexide/",
      sourceTitle: "Pexide · گروه صباحی",
      sourceNote: "مشخصات عمومی نمایش‌داده‌شده در صفحه برند؛ تأیید دیتاشیت لازم است.",
      grade: "Alpha",
      voltage: 35,
      voltageClass: "MV",
      application: "cable_insulation",
      publicDetail: true
    },
    {
      id: "pexide-mv-35-pro",
      name: "Pexide MV 35kV Pro",
      faName: "پکساید MV 35kV · گرید Pro",
      family: "Pexide",
      type: "technical_material",
      tags: ["pexide", "mv", "35kv", "pro", "xlpe", "کابل", "فشار متوسط"],
      attributes: [
        { label: "کلاس ولتاژ", value: "MV · تا ۳۵ kV" },
        { label: "گرید", value: "Pro" },
        { label: "فرمول عمومی", value: "XLPE پراکسیدی استاندارد" },
        { label: "کاربرد", value: "عایق کابل فشار متوسط" }
      ],
      sourceUrl: "https://sabahi.com/en/pexide/",
      sourceTitle: "Pexide · گروه صباحی",
      sourceNote: "مشخصات عمومی نمایش‌داده‌شده در صفحه برند؛ تأیید دیتاشیت لازم است.",
      grade: "Pro",
      voltage: 35,
      voltageClass: "MV",
      application: "cable_insulation",
      publicDetail: true
    },
    {
      id: "pexide-hv-170-alpha",
      name: "Pexide HV 170kV Alpha",
      faName: "پکساید HV 170kV · گرید Alpha",
      family: "Pexide",
      type: "technical_material",
      tags: ["pexide", "hv", "170kv", "alpha", "xlpe", "iec60840", "کابل", "فشار قوی"],
      attributes: [
        { label: "کلاس ولتاژ", value: "HV · ۱۷۰ kV" },
        { label: "گرید", value: "Alpha" },
        { label: "مرجع عمومی", value: "IEC 60840 پس از اکستروژن" },
        { label: "کاربرد", value: "عایق کابل فشار قوی" }
      ],
      sourceUrl: "https://sabahi.com/en/pexide/",
      sourceTitle: "Pexide · گروه صباحی",
      sourceNote: "مرجع عمومی صفحه برند؛ سازگاری پروژه باید توسط کارشناس تأیید شود.",
      grade: "Alpha",
      voltage: 170,
      voltageClass: "HV",
      standard: "IEC 60840",
      application: "cable_insulation",
      publicDetail: true
    },
    {
      id: "pexide-hv-252-alpha",
      name: "Pexide HV 252kV Alpha",
      faName: "پکساید HV 252kV · گرید Alpha",
      family: "Pexide",
      type: "technical_material",
      tags: ["pexide", "hv", "252kv", "alpha", "xlpe", "iec62067", "کابل", "فشار قوی"],
      attributes: [
        { label: "کلاس ولتاژ", value: "HV · ۲۵۲ kV" },
        { label: "گرید", value: "Alpha" },
        { label: "مرجع عمومی", value: "IEC 62067 پس از اکستروژن" },
        { label: "کاربرد", value: "عایق کابل فشار قوی" }
      ],
      sourceUrl: "https://sabahi.com/en/pexide/",
      sourceTitle: "Pexide · گروه صباحی",
      sourceNote: "مرجع عمومی صفحه برند؛ سازگاری پروژه باید توسط کارشناس تأیید شود.",
      grade: "Alpha",
      voltage: 252,
      voltageClass: "HV",
      standard: "IEC 62067",
      application: "cable_insulation",
      publicDetail: true
    },
    {
      id: "mpc-black-pigment",
      name: "Black Pigment",
      faName: "پیگمنت سیاه",
      family: "MPC",
      type: "product_category",
      tags: ["black", "pigment", "پیگمنت", "سیاه", "پلیمر"],
      attributes: [
        { label: "دسته محصول", value: "پیگمنت سیاه" },
        { label: "اطلاعات عمومی", value: "برای صنعت پلیمر معرفی شده است" },
        { label: "مشخصات لازم", value: "گرید، خلوص و اندازه ذره" }
      ],
      sourceUrl: "https://sabahi.com/mpc/",
      sourceTitle: "شرکت پودرهای میکرونیزه ایران · گروه صباحی",
      sourceNote: "صفحه عمومی نام دسته محصول را معرفی می‌کند؛ مشخصات فنی در این دمو حدس زده نمی‌شود.",
      application: "polymer",
      publicDetail: false
    },
    {
      id: "mpc-black-masterbatch",
      name: "Black Masterbatch",
      faName: "مستربچ سیاه",
      family: "MPC",
      type: "product_category",
      tags: ["black", "masterbatch", "مستربچ", "سیاه", "پلیمر"],
      attributes: [
        { label: "دسته محصول", value: "مستربچ سیاه" },
        { label: "اطلاعات عمومی", value: "تولیدشده در شرکت MPC معرفی‌شده در سایت" },
        { label: "مشخصات لازم", value: "گرید، درصد کربن بلک و پایه پلیمری" }
      ],
      sourceUrl: "https://sabahi.com/mpc/",
      sourceTitle: "شرکت پودرهای میکرونیزه ایران · گروه صباحی",
      sourceNote: "صفحه عمومی نام دسته محصول را معرفی می‌کند؛ مشخصات فنی در این دمو حدس زده نمی‌شود.",
      application: "polymer",
      publicDetail: false
    },
    {
      id: "mpc-black-compound",
      name: "Black Compound",
      faName: "کامپاند سیاه",
      family: "MPC",
      type: "product_category",
      tags: ["black", "compound", "کامپاند", "سیاه", "پلیمر"],
      attributes: [
        { label: "دسته محصول", value: "کامپاند سیاه" },
        { label: "اطلاعات عمومی", value: "برای صنعت پلیمر معرفی شده است" },
        { label: "مشخصات لازم", value: "پایه، کاربرد، خواص مکانیکی و حرارتی" }
      ],
      sourceUrl: "https://sabahi.com/mpc/",
      sourceTitle: "شرکت پودرهای میکرونیزه ایران · گروه صباحی",
      sourceNote: "صفحه عمومی نام دسته محصول را معرفی می‌کند؛ مشخصات فنی در این دمو حدس زده نمی‌شود.",
      application: "polymer",
      publicDetail: false
    },
    {
      id: "mpc-aluminium-hydroxide",
      name: "Aluminium Hydroxide",
      faName: "هیدروکسید آلومینیوم",
      family: "MPC",
      type: "product_category",
      tags: ["aluminium", "hydroxide", "هیدروکسید", "آلومینیوم", "پلیمر", "کندسوز"],
      attributes: [
        { label: "دسته محصول", value: "هیدروکسید آلومینیوم" },
        { label: "اطلاعات عمومی", value: "در فهرست محصولات عمومی MPC" },
        { label: "مشخصات لازم", value: "خلوص، اندازه ذره و کاربرد نهایی" }
      ],
      sourceUrl: "https://sabahi.com/mpc/",
      sourceTitle: "شرکت پودرهای میکرونیزه ایران · گروه صباحی",
      sourceNote: "صفحه عمومی نام دسته محصول را معرفی می‌کند؛ مشخصات فنی در این دمو حدس زده نمی‌شود.",
      application: "flame_retardant",
      publicDetail: false
    }
  ],
  rfqs: [
    {
      id: "rfq-a-easy",
      label: "RFQ A · واضح",
      title: "درخواست ماده اولیه عایق کابل فشار متوسط",
      customer: "مشتری نمونه · پارس کابل شرق",
      receivedAt: "۱۱ شهریور ۱۴۰۵ · ۰۹:۱۸",
      channel: "ایمیل ورودی · نمونه",
      body: "سلام وقت بخیر\nبرای تولید کابل فشار متوسط، لطفاً برای مورد زیر مشخصات فنی و امکان تأمین را اعلام فرمایید:\n\n• Pexide MV 35kV Alpha\n• گرید: Alpha\n• مقدار: ۸۰۰۰ کیلوگرم\n• کاربرد: عایق کابل فشار متوسط\n• مرجع مورد انتظار: سازگار با الزامات عمومی کابل ۳۵ کیلوولت\n• مقصد تحویل: تهران\n\nدر این مرحله قیمت قطعی لازم نیست؛ لطفاً اطلاعات لازم برای بررسی فنی را ارسال کنید.\nبا تشکر"
    },
    {
      id: "rfq-b-ambiguous",
      label: "RFQ B · نیازمند بررسی",
      title: "استعلام Pexide برای پروژه کابل",
      customer: "مشتری نمونه · تولیدکننده کابل آریا",
      receivedAt: "۱۱ شهریور ۱۴۰۵ · ۱۰:۴۲",
      channel: "پیام تجاری · نمونه",
      body: "سلام، برای پروژه کابل فشار متوسط به حدود ۱۲۰۰۰ kg از Pexide 35kV نیاز داریم.\n\nلطفاً مناسب‌ترین گزینه را پیشنهاد کنید و بفرمایید چه مدارکی برای تأیید فنی لازم است.\nتحویل در تهران و زمان‌بندی پروژه مهم است.\n\nسپاس"
    },
    {
      id: "rfq-c-multi",
      label: "RFQ C · چندقلمی",
      title: "درخواست چندقلمی مواد اولیه پروژه توسعه تولید",
      customer: "مشتری نمونه · توسعه پلیمر نوین",
      receivedAt: "۱۱ شهریور ۱۴۰۵ · ۱۳:۰۵",
      channel: "فرم داخلی · نمونه",
      body: "وقت بخیر\nبرای برنامه تأمین ماه آینده، لطفاً سه قلم زیر را جداگانه بررسی کنید:\n\n1) Pexide HV 170kV Alpha — مقدار ۴۵۰۰ kg — برای عایق کابل فشار قوی — استاندارد پروژه: IEC 60840\n2) Black Masterbatch — مقدار ۱۲۰۰ کیلو — کاربرد: تولید قطعات پلیمری مشکی\n3) Aluminium Hydroxide — مقدار ۸۰۰ kg — کاربرد: کامپاند کندسوزکننده\n\nلطفاً برای هر قلم، گزینه پیشنهادی، مشخصات قابل استناد و مواردی را که قبل از پاسخ باید تأیید کنیم اعلام کنید. قیمت قطعی فعلاً مورد نیاز نیست."
    }
  ]
};
