/*
 * Deterministic demo matcher.
 *
 * This module is intentionally small and replaceable. A production adapter
 * can expose the same analyzeRFQ() shape while moving extraction, retrieval
 * and approval rules behind an API.
 */
(function () {
  const { products, rfqs } = window.SABAHI_DEMO_DATA;

  const toLatinDigits = (value) => String(value || "")
    .replace(/[۰-۹]/g, (digit) => String("۰۱۲۳۴۵۶۷۸۹".indexOf(digit)))
    .replace(/[٠-٩]/g, (digit) => String("٠١٢٣٤٥٦٧٨٩".indexOf(digit)));

  const normalize = (value) => toLatinDigits(value)
    .toLowerCase()
    .replace(/[يى]/g, "ی")
    .replace(/ك/g, "ک")
    .replace(/[‌‏‎]/g, " ")
    .replace(/[–—−]/g, "-")
    .replace(/\s+/g, " ")
    .trim();

  const faNumber = (value) => String(value).replace(/[0-9]/g, (digit) => "۰۱۲۳۴۵۶۷۸۹"[Number(digit)]);

  function productById(id) {
    return products.find((product) => product.id === id);
  }

  function item(id, requested, quantity, unit, attributes, missing, confidence, productIds) {
    return {
      id,
      requested,
      quantity,
      quantityLabel: `${faNumber(quantity.toLocaleString("en-US"))} ${unit}`,
      unit,
      attributes,
      missing,
      confidence,
      productIds
    };
  }

  function extractItems(rfq) {
    if (rfq.id === "rfq-a-easy") {
      return [item(
        "item-1",
        "Pexide MV 35kV Alpha",
        8000,
        "کیلوگرم",
        [
          { label: "کلاس ولتاژ", value: "MV · ۳۵ kV", tone: "positive" },
          { label: "گرید", value: "Alpha", tone: "positive" },
          { label: "کاربرد", value: "عایق کابل فشار متوسط", tone: "positive" },
          { label: "مقصد تحویل", value: "تهران", tone: "neutral" }
        ],
        [],
        98,
        ["pexide-mv-35-alpha", "pexide-mv-35-pro"]
      )];
    }

    if (rfq.id === "rfq-b-ambiguous") {
      return [item(
        "item-1",
        "Pexide 35kV",
        12000,
        "kg",
        [
          { label: "کلاس ولتاژ", value: "MV · ۳۵ kV", tone: "positive" },
          { label: "کاربرد", value: "کابل فشار متوسط", tone: "positive" },
          { label: "مقصد تحویل", value: "تهران", tone: "neutral" }
        ],
        [
          { label: "گرید", question: "گرید مورد نظر Alpha است یا Pro؟" },
          { label: "مرجع فنی", question: "استاندارد پروژه یا دیتاشیت مرجع را می‌فرمایید؟" }
        ],
        76,
        ["pexide-mv-35-alpha", "pexide-mv-35-pro"]
      )];
    }

    return [
      item(
        "item-1",
        "Pexide HV 170kV Alpha",
        4500,
        "kg",
        [
          { label: "کلاس ولتاژ", value: "HV · ۱۷۰ kV", tone: "positive" },
          { label: "گرید", value: "Alpha", tone: "positive" },
          { label: "استاندارد پروژه", value: "IEC 60840", tone: "positive" },
          { label: "کاربرد", value: "عایق کابل فشار قوی", tone: "positive" }
        ],
        [],
        97,
        ["pexide-hv-170-alpha", "pexide-hv-252-alpha"]
      ),
      item(
        "item-2",
        "Black Masterbatch",
        1200,
        "کیلوگرم",
        [
          { label: "کاربرد", value: "تولید قطعات پلیمری مشکی", tone: "positive" },
          { label: "رنگ", value: "مشکی", tone: "positive" }
        ],
        [
          { label: "مشخصات فنی", question: "گرید، درصد کربن بلک و پایه پلیمری چیست؟" }
        ],
        71,
        ["mpc-black-masterbatch"]
      ),
      item(
        "item-3",
        "Aluminium Hydroxide",
        800,
        "kg",
        [
          { label: "کاربرد", value: "کامپاند کندسوزکننده", tone: "positive" }
        ],
        [
          { label: "مشخصات فنی", question: "خلوص، اندازه ذره و الزامات آزمون کدام است؟" }
        ],
        68,
        ["mpc-aluminium-hydroxide"]
      )
    ];
  }

  function matchScore(product, request) {
    const requested = normalize(request.requested);
    const productTerms = normalize(`${product.name} ${product.faName} ${product.tags.join(" ")}`);
    const isPexide = product.family === "Pexide";
    const requestedFamily = requested.includes("pexide") || requested.includes("پکساید");
    let score = 0;
    const matches = [];
    const conflicts = [];
    const missing = [];

    if (requestedFamily && isPexide) {
      score += 30;
      matches.push("خانواده Pexide");
    } else if (!requestedFamily && productTerms.includes(requested)) {
      score += 38;
      matches.push("نام محصول");
    } else if (!requestedFamily && productTerms.includes(normalize(request.requested.split(" ")[0]))) {
      score += 20;
      matches.push("دسته محصول");
    }

    if (request.attributes.some((attribute) => normalize(attribute.value).includes("۳۵") || normalize(attribute.value).includes("35"))) {
      if (product.voltage === 35) {
        score += 26;
        matches.push("کلاس ۳۵ kV");
      } else if (isPexide) {
        conflicts.push("کلاس ولتاژ با درخواست هم‌خوان نیست");
      }
    }
    if (request.attributes.some((attribute) => normalize(attribute.value).includes("۱۷۰") || normalize(attribute.value).includes("170"))) {
      if (product.voltage === 170) {
        score += 28;
        matches.push("کلاس ۱۷۰ kV");
      } else if (isPexide) {
        conflicts.push("کلاس ولتاژ با درخواست هم‌خوان نیست");
      }
    }
    if (request.attributes.some((attribute) => normalize(attribute.value).includes("alpha"))) {
      if (product.grade === "Alpha") {
        score += 19;
        matches.push("گرید Alpha");
      } else if (isPexide) {
        conflicts.push("گرید محصول متفاوت است");
      }
    } else if (isPexide && requestedFamily) {
      missing.push("گرید Alpha یا Pro");
    }
    if (request.attributes.some((attribute) => normalize(attribute.value).includes("iec 60840"))) {
      if (product.standard === "IEC 60840") {
        score += 18;
        matches.push("مرجع IEC 60840");
      } else if (isPexide) {
        missing.push("تأیید سازگاری با IEC 60840");
      }
    }
    if (request.attributes.some((attribute) => normalize(attribute.value).includes("کابل"))) {
      if (product.application === "cable_insulation") {
        score += 16;
        matches.push("کاربرد کابل");
      }
    }
    if (request.id === "item-2" && product.id === "mpc-black-masterbatch") {
      score = 76;
      matches.push("دسته مستربچ سیاه");
      missing.push("گرید و پایه پلیمری");
    }
    if (request.id === "item-3" && product.id === "mpc-aluminium-hydroxide") {
      score = 72;
      matches.push("دسته هیدروکسید آلومینیوم");
      missing.push("خلوص و اندازه ذره");
    }

    if (!product.publicDetail && score > 0) {
      missing.push("مشخصات فنی تکمیلی از مرجع رسمی");
    }

    const hasConflict = conflicts.length > 0;
    const confidence = Math.max(32, Math.min(98, score - (hasConflict ? 22 : 0) - Math.min(missing.length * 5, 15)));
    const classification = hasConflict
      ? "کاندید ناسازگار"
      : missing.length > 0
        ? "تطبیق اولیه"
        : "تطبیق پیشنهادی";

    return {
      product,
      confidence,
      classification,
      matches: [...new Set(matches)],
      conflicts: [...new Set(conflicts)],
      missing: [...new Set(missing)],
      reason: matches.length > 0
        ? `بر اساس ${matches.slice(0, 2).join(" و ")} در اطلاعات عمومی محصول.`
        : "نشانه کافی برای تطبیق مستقیم پیدا نشد."
    };
  }

  function matchesFor(request) {
    return request.productIds
      .map(productById)
      .filter(Boolean)
      .map((product) => {
        const result = matchScore(product, request);
        if (request.missing.length > 0 && result.conflicts.length === 0) {
          result.missing = [...new Set([
            ...result.missing,
            ...request.missing.map((entry) => entry.label)
          ])];
          result.classification = "تطبیق اولیه";
        }
        return result;
      })
      .sort((left, right) => right.confidence - left.confidence);
  }

  function buildDraft(rfq, items, allMatches) {
    const lines = [
      `سلام وقت بخیر،`,
      "",
      `درخواست شما با موضوع «${rfq.title}» دریافت و به اقلام زیر ساختاربندی شد:`,
      ""
    ];
    items.forEach((request, index) => {
      const top = allMatches[index][0];
      lines.push(`${index + 1}. ${request.requested} · ${request.quantityLabel}`);
      if (top) {
        lines.push(`   گزینه پیشنهادی اولیه: ${top.product.name}`);
      }
      if (request.missing.length > 0) {
        lines.push(`   برای بررسی نهایی: ${request.missing.map((missing) => missing.question).join("؛ ")}`);
      }
    });
    lines.push("", "مشخصات، قیمت و زمان تأمین پس از بررسی و تأیید کارشناس تکمیل می‌شود.", "", "با احترام");
    return lines.join("\n");
  }

  function analyzeRFQ(rfqId) {
    const rfq = rfqs.find((entry) => entry.id === rfqId) || rfqs[0];
    const items = extractItems(rfq);
    const allMatches = items.map(matchesFor);
    const clarificationCount = items.reduce((count, request) => count + request.missing.length, 0);
    const presentCount = items.reduce((count, request) => count + request.attributes.length, 0);
    const possibleCount = items.reduce((count, request) => count + request.attributes.length + request.missing.length, 0);
    const completeness = Math.round((presentCount / Math.max(1, possibleCount)) * 100);
    return {
      rfq,
      items,
      allMatches,
      clarificationCount,
      completeness,
      hasAmbiguity: clarificationCount > 0,
      draft: buildDraft(rfq, items, allMatches),
      kpis: {
        processingTime: rfq.id === "rfq-c-multi" ? "۰۰:۰۶" : rfq.id === "rfq-b-ambiguous" ? "۰۰:۰۴" : "۰۰:۰۳",
        extractedItems: faNumber(items.length),
        needsReview: faNumber(clarificationCount),
        completeness: `${faNumber(completeness)}٪`
      }
    };
  }

  window.SABAHI_DEMO_MATCHER = { analyzeRFQ, normalize };
}());
