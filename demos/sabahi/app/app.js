(function () {
  const data = window.SABAHI_DEMO_DATA;
  const matcher = window.SABAHI_DEMO_MATCHER;
  const steps = [
    { key: "input", label: "ورودی RFQ" },
    { key: "extraction", label: "استخراج" },
    { key: "matching", label: "تطبیق محصول" },
    { key: "ambiguity", label: "کنترل ابهام" },
    { key: "response", label: "پیش‌نویس پاسخ" },
    { key: "approval", label: "تأیید انسانی" }
  ];

  const state = {
    section: "workbench",
    selectedRfqId: "rfq-a-easy",
    analysis: null,
    stage: 0,
    loading: false,
    customText: "",
    draft: "",
    approval: "",
    presentation: false,
    presentationStage: 0,
    presentationAnalysis: null,
    toastTimer: null
  };

  const $ = (selector) => document.querySelector(selector);

  function escapeHTML(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function faNumber(value) {
    return String(value).replace(/[0-9]/g, (digit) => "۰۱۲۳۴۵۶۷۸۹"[Number(digit)]);
  }

  function currentRfq() {
    return data.rfqs.find((rfq) => rfq.id === state.selectedRfqId) || data.rfqs[0];
  }

  function currentAnalysis() {
    return state.analysis || matcher.analyzeRFQ(state.selectedRfqId);
  }

  function showToast(message) {
    const toast = $("#toast");
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add("is-visible");
    window.clearTimeout(state.toastTimer);
    state.toastTimer = window.setTimeout(() => toast.classList.remove("is-visible"), 2700);
  }

  function renderStepper() {
    const host = $("#stepper");
    host.innerHTML = steps.map((step, index) => {
      const isDone = index < state.stage && state.analysis;
      const isActive = index === state.stage;
      const canVisit = index === 0 || (state.analysis && index <= state.stage);
      return `<button class="step ${isDone ? "is-done" : ""} ${isActive ? "is-active" : ""}" type="button" data-step="${index}" ${canVisit ? "" : "disabled"} aria-current="${isActive ? "step" : "false"}">
        <span class="step-number">${isDone ? "✓" : faNumber(index + 1)}</span>
        <span class="step-label">${escapeHTML(step.label)}</span>
      </button>`;
    }).join("");
  }

  function renderPanelHeader(kicker, title, description, action) {
    return `<div class="panel-header"><div><span class="section-kicker">${escapeHTML(kicker)}</span><h2>${escapeHTML(title)}</h2>${description ? `<p>${escapeHTML(description)}</p>` : ""}</div>${action ? `<span class="panel-action">${action}</span>` : ""}</div>`;
  }

  function renderRfqCards() {
    return data.rfqs.map((rfq) => `<button class="rfq-card ${rfq.id === state.selectedRfqId ? "is-selected" : ""}" type="button" data-rfq="${rfq.id}">
      <span class="rfq-card-top"><span class="tag">${escapeHTML(rfq.label)}</span><span class="selected-mark">●</span></span>
      <h3>${escapeHTML(rfq.title)}</h3>
      <p>${escapeHTML(rfq.customer)}</p>
      <span class="rfq-card-foot"><span>${escapeHTML(rfq.channel)}</span><span>${escapeHTML(rfq.receivedAt)}</span></span>
    </button>`).join("");
  }

  function renderInput() {
    const rfq = currentRfq();
    const body = state.customText || rfq.body;
    return `<div class="screen-layout">
      <section class="panel inbox-panel">
        ${renderPanelHeader("ورودی‌های نمونه", "درخواست‌های منتخب", "سه سناریوی ساختگی برای ارائه کوتاه", `<span class="tag">۳ مورد</span>`)}
        <div class="inbox-meta"><span>انتخاب یک سناریو</span><span>همه ساختگی</span></div>
        <div class="inbox-items">${renderRfqCards()}</div>
      </section>
      <section class="panel input-panel">
        ${renderPanelHeader("گام اول", "درخواست ورودی", "متن آزاد مشتری را برای ساختاربندی آماده کنید.", `<span class="status-tag ${state.loading ? "warning" : "neutral"}">${state.loading ? "در حال تحلیل" : "آماده تحلیل"}</span>`)}
        <div class="input-context">
          <div class="context-row"><span>مشتری نمونه</span><strong>${escapeHTML(rfq.customer)}</strong></div>
          <div class="context-row"><span>موضوع</span><strong>${escapeHTML(rfq.title)}</strong></div>
          <div class="context-row"><span>زمان دریافت</span><strong>${escapeHTML(rfq.receivedAt)}</strong></div>
        </div>
        <label class="input-label" for="rfq-text"><span>متن درخواست</span><span class="tag">قابل ویرایش</span></label>
        <textarea class="rfq-textarea" id="rfq-text" spellcheck="false">${escapeHTML(body)}</textarea>
        <p class="input-footnote">محتوای این سناریو ساختگی است؛ برای دمو هیچ داده خصوصی یا قیمت واقعی استفاده نشده است.</p>
        <div class="input-actions">
          <button class="button button-teal" type="button" id="analyze-button" ${state.loading ? "disabled" : ""}><span class="button-icon">${state.loading ? "…" : "✦"}</span> ${state.loading ? "در حال تحلیل…" : "تحلیل درخواست"}</button>
          <button class="button button-light" type="button" id="reset-input-button">بازنشانی متن</button>
        </div>
      </section>
      <aside class="panel side-panel">
        ${renderPanelHeader("زمینه محصول", "مرجع عمومی صباحی", "اطلاعات قابل استفاده در این نمونه", `<span class="tag">عمومی</span>`)}
        ${renderPublicSurface()}
      </aside>
    </div>
    ${renderBottomBar("برای شروع، یک سناریو را انتخاب و تحلیل کنید.", false)}`;
  }

  function renderPublicSurface() {
    return `<div class="source-list">
      <div class="source-row"><span class="source-logo">SG</span><div><strong>Sabahi Group</strong><span>تنوع محصول و تأمین صنعتی</span></div></div>
      <div class="source-row"><span class="source-logo">MPC</span><div><strong>MPC</strong><span>پیگمنت، مستربچ، کامپاند و ATH</span></div></div>
      <div class="source-row"><span class="source-logo">PX</span><div><strong>Pexide</strong><span>مواد XLPE برای کابل MV / HV</span></div></div>
    </div>
    <div class="journey-box">
      <span class="section-kicker">مسیر پیشنهادی</span>
      ${["متن درخواست", "اقلام و مشخصات", "کاندیدهای عمومی", "تأیید کارشناس"].map((step, index) => `<div class="journey-step"><span class="journey-number">${faNumber(index + 1)}</span><span>${step}</span></div>`).join("")}
    </div>
    <div class="guard-note"><strong>AI آماده می‌کند؛ انسان تصمیم می‌گیرد.</strong> قیمت، انتخاب نهایی و پاسخ مشتری در این نمونه به کارشناس برمی‌گردد.</div>`;
  }

  function renderInputSummary(rfq) {
    return `<section class="panel input-panel compact-input">
      ${renderPanelHeader("متن مرجع", "درخواست انتخاب‌شده", "همان ورودی در تمام مراحل قابل ردیابی است.", `<span class="status-tag neutral">${escapeHTML(rfq.label_fa || rfq.label || "نمونه")}</span>`)}
      <div class="input-context">
        <div class="context-row"><span>فرستنده</span><strong>${escapeHTML(rfq.customer)}</strong></div>
        <div class="context-row"><span>کانال</span><strong>${escapeHTML(rfq.channel)}</strong></div>
      </div>
      <div class="source-tag">متن ساختگی برای ارائه</div>
      <p class="quoted-text">${escapeHTML(rfq.body).replace(/\n/g, "<br>")}</p>
    </section>`;
  }

  function renderKpis(analysis) {
    return `<div class="analysis-kpis">
      <div class="mini-kpi"><strong>${analysis.kpis.processingTime}</strong><span>زمان پردازش</span></div>
      <div class="mini-kpi"><strong>${analysis.kpis.extractedItems}</strong><span>قلم استخراج‌شده</span></div>
      <div class="mini-kpi"><strong>${analysis.kpis.needsReview}</strong><span>نیازمند تأیید</span></div>
    </div>`;
  }

  function renderAttributes(attributes) {
    return `<div class="attribute-grid">${attributes.map((attribute) => `<div class="attribute ${attribute.tone === "positive" ? "attribute-positive" : ""}"><span class="attribute-label">${escapeHTML(attribute.label)}</span><span class="attribute-value">${escapeHTML(attribute.value)}</span></div>`).join("")}</div>`;
  }

  function renderMissing(missing) {
    if (!missing || missing.length === 0) return "";
    return `<div class="missing-box"><span class="missing-symbol">!</span><div><strong>نیاز به تأیید کارشناس</strong><p>${missing.map((entry) => escapeHTML(entry.question)).join("<br>")}</p></div></div>`;
  }

  function renderExtractedItems(analysis) {
    return `<div class="item-list">${analysis.items.map((request, index) => `<article class="extracted-item ${request.missing.length ? "has-missing" : ""}">
      <div class="item-heading"><div class="item-heading-left"><span class="item-index">${faNumber(index + 1)}</span><div><h3>${escapeHTML(request.requested)}</h3><p>${escapeHTML(request.quantityLabel)} · فیلدهای استخراج‌شده</p></div></div><span class="item-confidence">${faNumber(request.confidence)}٪ تطبیق متن</span></div>
      ${renderAttributes(request.attributes)}
      ${renderMissing(request.missing)}
      <div class="confidence-track"><span style="width:${request.confidence}%"></span></div>
    </article>`).join("")}</div>`;
  }

  function renderActivityPanel(analysis) {
    const sourceCount = new Set(analysis.items.flatMap((item) => item.productIds.map((id) => {
      const product = data.products.find((entry) => entry.id === id);
      return product ? product.sourceUrl : "";
    }))).size;
    return `<aside class="panel side-panel">
      ${renderPanelHeader("کنترل کیفیت", "ردپای تحلیل", "هر خروجی به ورودی و مرجع عمومی برمی‌گردد.", `<span class="status-tag success">ثبت شد</span>`)}
      <div class="journey-box">
        ${["متن دریافت شد", "اقلام جدا شد", "مشخصات صریح ثبت شد", analysis.hasAmbiguity ? "ابهام‌ها علامت‌گذاری شد" : "مورد ناقص پیدا نشد"].map((step, index) => `<div class="journey-step"><span class="journey-number">${index < 3 || !analysis.hasAmbiguity ? "✓" : "!"}</span><span>${step}</span></div>`).join("")}
      </div>
      <div class="source-list">
        <div class="source-row"><span class="source-logo">${faNumber(analysis.items.length)}</span><div><strong>قلم مستقل</strong><span>ساختاربندی‌شده برای بررسی</span></div></div>
        <div class="source-row"><span class="source-logo">${faNumber(sourceCount)}</span><div><strong>مرجع عمومی</strong><span>بدون ادعای موجودی یا قیمت</span></div></div>
      </div>
      <div class="guard-note"><strong>اطمینان یعنی نشان‌دادن ابهام.</strong> مقدار یا مشخصه‌ای که در متن نبود، خودکار تکمیل نمی‌شود.</div>
    </aside>`;
  }

  function renderExtraction() {
    const analysis = currentAnalysis();
    return `<div class="screen-layout">
      ${renderInputSummary(analysis.rfq)}
      <section class="panel analysis-panel">
        ${renderPanelHeader("گام دوم", "استخراج ساختاریافته", "متن آزاد به اقلام و مشخصات قابل بررسی تبدیل شده است.", `<span class="status-tag success">تحلیل کامل شد</span>`)}
        <div class="analysis-overview"><div class="analysis-summary"><span class="summary-icon">✓</span><div><strong>${faNumber(analysis.items.length)} قلم از متن جدا شد</strong><span>${analysis.hasAmbiguity ? `${faNumber(analysis.clarificationCount)} مورد نیازمند تأیید است` : "همه فیلدهای اصلی این سناریو مشخص است"}</span></div></div>${renderKpis(analysis)}</div>
        ${renderExtractedItems(analysis)}
      </section>
      ${renderActivityPanel(analysis)}
    </div>
    ${renderBottomBar(analysis.hasAmbiguity ? "ابهام‌ها حفظ شده‌اند؛ در گام بعد کاندیدها و سؤال‌های روشن را می‌بینید." : "اطلاعات صریح آماده تطبیق با مرجع عمومی است.", true)}`;
  }

  function renderMatchRows(analysis) {
    return analysis.items.flatMap((request, itemIndex) => analysis.allMatches[itemIndex].map((match, matchIndex) => {
      const product = match.product;
      const points = match.matches.map((point) => `<span>${escapeHTML(point)}</span>`).join("");
      const missing = match.missing.map((point) => `<span class="needs">${escapeHTML(point)}</span>`).join("");
      return `<tr>
        <td><strong>${faNumber(itemIndex + 1)}. ${escapeHTML(request.requested)}</strong><br><span class="table-source">${escapeHTML(request.quantityLabel)}</span></td>
        <td><div class="product-name"><span class="product-swatch">${escapeHTML(product.family === "Pexide" ? "PX" : "MPC")}</span><div><strong>${escapeHTML(product.name)}</strong><span>${escapeHTML(product.faName)}</span></div></div></td>
        <td><div class="match-points">${points}${missing}</div></td>
        <td><span class="score-cell">${faNumber(match.confidence)}٪</span><br><span class="match-tag ${match.missing.length || match.conflicts.length ? "warning" : "success"}">${escapeHTML(match.classification)}</span></td>
        <td><a class="table-source" href="${escapeHTML(product.sourceUrl)}" target="_blank" rel="noreferrer">${escapeHTML(product.sourceTitle)}</a><br><span class="table-source">${escapeHTML(match.reason)}</span></td>
      </tr>`;
    })).join("");
  }

  function topMatch(analysis) {
    return analysis.allMatches.flatMap((matches) => matches).sort((left, right) => right.confidence - left.confidence)[0];
  }

  function renderMatching() {
    const analysis = currentAnalysis();
    const top = topMatch(analysis);
    const reviewCount = analysis.clarificationCount;
    return `<section class="workspace-card full-card">
      <div class="screen-title"><div><span class="section-kicker">گام سوم</span><h2>تطبیق با مرجع عمومی محصول</h2><p>گزینه‌ها بر اساس اطلاعات صریح RFQ و مشخصات منتشرشده نمایش داده می‌شوند.</p></div><span class="status-tag ${reviewCount ? "warning" : "success"}">${reviewCount ? "نیازمند کنترل" : "کاندید آماده بررسی"}</span></div>
      <div class="match-summary">
        <div class="match-hero"><div class="match-hero-top"><div><span class="section-kicker">بهترین کاندید این مرحله</span><h3>${escapeHTML(top ? top.product.name : "بدون کاندید")}</h3></div><div class="score-ring">${faNumber(top ? top.confidence : 0)}٪</div></div><p>${escapeHTML(top ? top.reason : "برای این درخواست داده کافی وجود ندارد.")} این عدد فقط شاخص نمایشی برای اولویت بررسی است.</p></div>
        <div class="review-summary"><h3>خلاصه بررسی</h3><div class="review-line"><span>اقلام پردازش‌شده</span><strong>${faNumber(analysis.items.length)}</strong></div><div class="review-line"><span>گزینه‌های کاندید</span><strong>${faNumber(analysis.allMatches.flatMap((matches) => matches).length)}</strong></div><div class="review-line"><span>موارد نیازمند تأیید</span><strong class="${reviewCount ? "pending-price" : ""}">${faNumber(reviewCount)}</strong></div><div class="review-line"><span>قیمت</span><strong class="pending-price">در انتظار قیمت‌گذاری</strong></div></div>
      </div>
      <div class="table-wrap"><table class="match-table"><thead><tr><th>قلم درخواست</th><th>محصول کاندید</th><th>چرا این گزینه؟</th><th>شاخص تطبیق</th><th>مرجع</th></tr></thead><tbody>${renderMatchRows(analysis)}</tbody></table></div>
      ${reviewCount ? `<div class="clarity-card"><div><h3>انتخاب نهایی هنوز زود است</h3><p>درخواست برای ${faNumber(reviewCount)} مورد اطلاعات کافی ندارد. گزینه‌ها به‌عنوان کاندید اولیه نمایش داده شده‌اند و هیچ مقدار یا گریدی به‌صورت حدسی تکمیل نشده است.</p></div><div class="question-list">${analysis.items.flatMap((item) => item.missing).map((entry) => `<div>${escapeHTML(entry.question)}</div>`).join("")}</div></div>` : `<div class="guard-note" style="margin-top:14px"><strong>مرجع و تصمیم نهایی جدا هستند.</strong> تطبیق پیشنهادی به معنی تأیید فنی، موجودی یا قیمت نیست.</div>`}
    </section>
    ${renderBottomBar(reviewCount ? "ابهام‌ها را به سؤال قابل پاسخ تبدیل کنید." : "کاندیدها آماده ساخت پیش‌نویس پاسخ هستند.", true)}`;
  }

  function renderAmbiguity() {
    const analysis = currentAnalysis();
    const missingItems = analysis.items.filter((item) => item.missing.length);
    return `<section class="workspace-card full-card">
      <div class="screen-title"><div><span class="section-kicker">گام چهارم</span><h2>کنترل ابهام قبل از پاسخ</h2><p>جایی که اطلاعات کافی نیست، سیستم سؤال می‌سازد و انتخاب را متوقف می‌کند.</p></div><span class="status-tag warning">${analysis.hasAmbiguity ? `${faNumber(analysis.clarificationCount)} مورد نیازمند تأیید` : "بدون ابهام"}</span></div>
      <div class="clarity-card" style="margin-top:0"><div><h3>${analysis.hasAmbiguity ? "این درخواست هنوز پاسخ نهایی ندارد." : "این سناریو ابهام باز ندارد."}</h3><p>${analysis.hasAmbiguity ? "در جلسه واقعی، کارشناس می‌تواند سؤال‌های زیر را برای تکمیل درخواست به مشتری برگرداند. سیستم گرید، استاندارد یا مشخصات جاافتاده را حدس نمی‌زند." : "با این حال، مشخصات نهایی، قیمت و زمان تأمین همچنان باید توسط صاحب فرایند تأیید شود."}</p></div><div class="question-list">${analysis.hasAmbiguity ? missingItems.flatMap((item) => item.missing).map((entry, index) => `<div><strong>${faNumber(index + 1)}.</strong> ${escapeHTML(entry.question)}</div>`).join("") : `<div>موردی برای سؤال خودکار ثبت نشده است.</div>`}</div></div>
      <div class="item-list" style="margin-top:14px">${analysis.items.map((item, index) => `<article class="extracted-item ${item.missing.length ? "has-missing" : ""}"><div class="item-heading"><div class="item-heading-left"><span class="item-index">${faNumber(index + 1)}</span><div><h3>${escapeHTML(item.requested)}</h3><p>${escapeHTML(item.quantityLabel)}</p></div></div><span class="status-tag ${item.missing.length ? "warning" : "success"}">${item.missing.length ? "متوقف تا تأیید" : "قابل ادامه"}</span></div><div class="attribute-grid">${item.attributes.slice(0, 4).map((attribute) => `<div class="attribute ${attribute.tone === "positive" ? "attribute-positive" : ""}"><span class="attribute-label">${escapeHTML(attribute.label)}</span><span class="attribute-value">${escapeHTML(attribute.value)}</span></div>`).join("")}</div>${item.missing.length ? renderMissing(item.missing) : ""}</article>`).join("")}</div>
    </section>
    ${renderBottomBar(analysis.hasAmbiguity ? "اطلاعات ناقص را مشخص کردیم؛ پیش‌نویس فقط با یادداشت‌های لازم ساخته می‌شود." : "کنترل ابهام کامل شد.", true)}`;
  }

  function renderResponse() {
    const analysis = currentAnalysis();
    const draft = state.draft || analysis.draft;
    const responseItems = analysis.items.map((item, index) => {
      const best = analysis.allMatches[index][0];
      return `<div class="review-line"><span>${escapeHTML(item.requested)}</span><strong>${escapeHTML(best ? best.product.name : "بررسی دستی")}</strong></div>`;
    }).join("");
    return `<section class="workspace-card full-card">
      <div class="screen-title"><div><span class="section-kicker">گام پنجم</span><h2>پیش‌نویس پاسخ تجاری</h2><p>خروجی برای بازبینی آماده است؛ این صفحه هیچ ارسال خودکاری ندارد.</p></div><span class="status-tag warning">قیمت در انتظار ورود</span></div>
      <div class="response-layout">
        <div class="draft-panel"><div class="draft-toolbar"><h3>پیش‌نویس قابل ویرایش</h3><span class="source-tag">متن پیشنهادی</span></div><textarea class="draft-editor" id="draft-editor" spellcheck="false">${escapeHTML(draft)}</textarea><div class="draft-footer"><span>پاسخ هنوز برای مشتری ارسال نشده است.</span><span class="pending-price">در انتظار قیمت‌گذاری</span></div></div>
        <aside class="response-aside"><div class="response-card"><h3>خلاصه خروجی</h3>${responseItems}<div class="review-line"><span>موارد باز</span><strong>${faNumber(analysis.clarificationCount)}</strong></div></div><div class="response-card"><h3>قبل از هر پاسخ</h3><ul><li>تأیید مشخصات و گزینه محصول</li><li>ورود قیمت و شرایط توسط مسئول مجاز</li><li>بازبینی متن و زمان تأمین</li></ul><div class="guard-note"><strong>کنترل انسانی</strong> خروجی برای تأیید کارشناس متوقف است.</div></div></aside>
      </div>
    </section>
    ${renderBottomBar("پیش‌نویس آماده بازبینی است؛ تصمیم نهایی با کارشناس می‌ماند.", true)}`;
  }

  function renderApproval() {
    const analysis = currentAnalysis();
    const statusCopy = state.approval === "approved"
      ? "خروجی برای ادامه فرایند داخلی تأیید شد؛ هیچ پیام یا پیش‌فاکتوری ارسال نشده است."
      : state.approval === "review"
        ? "خروجی برای بررسی بیشتر برگشت داده شد؛ ارسال همچنان مسدود است."
        : "پیش‌نویس آماده است و فقط پس از بررسی مسئول مربوط می‌تواند وارد فرایند واقعی شود.";
    return `<section class="workspace-card approval-card">
      <div class="approval-mark">${state.approval === "approved" ? "✓" : "⌁"}</div>
      <span class="section-kicker">گام ششم · نقطه تصمیم</span>
      <h2>${state.approval === "approved" ? "تأیید انسانی ثبت شد" : state.approval === "review" ? "نیاز به بررسی بیشتر" : "انسان در حلقه تصمیم"}</h2>
      <p>${statusCopy}</p>
      <div class="approval-grid"><div class="approval-fact"><span>درخواست</span><strong>${escapeHTML(analysis.rfq.title)}</strong></div><div class="approval-fact"><span>قیمت</span><strong class="pending-price">در انتظار قیمت‌گذاری</strong></div><div class="approval-fact"><span>وضعیت ارسال</span><strong>ارسال نمی‌شود</strong></div></div>
      <div class="approval-actions"><button class="button button-teal" type="button" data-approval="approved">تأیید خروجی</button><button class="button button-light" type="button" data-approval="edit">ویرایش پیش‌نویس</button><button class="button button-quiet" type="button" data-approval="review">نیاز به بررسی</button><button class="button button-danger" type="button" data-approval="back">بازگشت به کارشناس</button></div>
      <p class="approval-disclaimer">این دمو فقط آماده‌سازی و کنترل انسانی را نشان می‌دهد. هیچ اتصال ارسال، قیمت واقعی یا داده خصوصی در آن وجود ندارد.</p>
    </section>
    ${renderBottomBar("AI آماده می‌کند؛ انسان کنترل می‌کند.", true)}`;
  }

  function renderBottomBar(note, hasAnalysis) {
    const isFirst = state.stage === 0;
    const nextLabel = isFirst ? "تحلیل درخواست" : state.stage === steps.length - 1 ? "پایان دمو" : "مرحله بعد";
    return `<div class="bottom-bar"><div class="bottom-note"><span class="small-check">✓</span><span>${escapeHTML(note)}</span></div><div class="bottom-actions"><button class="button button-quiet" type="button" id="restart-button">شروع دوباره</button><button class="button button-light" type="button" id="previous-button" ${isFirst ? "disabled" : ""}>قبلی</button><button class="button button-dark" type="button" id="next-button">${nextLabel}<span class="button-icon">←</span></button></div></div>`;
  }

  function renderCatalog() {
    return `<section class="workspace-card full-card"><div class="screen-title"><div><span class="section-kicker">مرجع نمایشی</span><h2>محصولات منتخب از اطلاعات عمومی</h2><p>این فهرست کوچک است و فقط برای نشان‌دادن منبع تطبیق در دمو استفاده می‌شود.</p></div><span class="tag">${faNumber(data.products.length)} رکورد عمومی</span></div><div class="catalog-grid">${data.products.map((product) => `<article class="catalog-card"><span class="catalog-id">${escapeHTML(product.family)}</span><h3>${escapeHTML(product.name)}</h3><p>${product.attributes.slice(0, 2).map((attribute) => `${escapeHTML(attribute.label)}: ${escapeHTML(attribute.value)}`).join(" · ")}</p><a class="catalog-source" href="${escapeHTML(product.sourceUrl)}" target="_blank" rel="noreferrer">مشاهده مرجع عمومی ↗</a></article>`).join("")}</div><div class="bottom-bar"><div class="bottom-note"><span class="small-check">✓</span><span>قیمت، موجودی و دیتاشیت کامل در این فهرست وجود ندارد.</span></div><div class="bottom-actions"><button class="button button-dark" type="button" data-nav="workbench">بازگشت به میزکار</button></div></div></section>`;
  }

  function renderMetrics() {
    const analysis = state.analysis || matcher.analyzeRFQ(state.selectedRfqId);
    const metrics = [
      ["زمان پردازش نمونه", analysis.kpis.processingTime, "عدد نمایشی برای مسیر محلی"],
      ["قلم استخراج‌شده", analysis.kpis.extractedItems, "از درخواست انتخاب‌شده"],
      ["نیازمند تأیید", analysis.kpis.needsReview, "فیلدهای بدون مقدار صریح"],
      ["تکمیل درخواست", `${faNumber(analysis.completeness)}٪`, "محاسبه بر اساس فیلدهای همین نمونه"]
    ];
    return `<section class="workspace-card full-card"><div class="screen-title"><div><span class="section-kicker">اندازه‌گیری نمایشی</span><h2>شاخص‌های همین سناریو</h2><p>این اعداد عملکرد صباحی را نشان نمی‌دهند؛ فقط وضعیت داده ساختگی انتخاب‌شده را در دمو خلاصه می‌کنند.</p></div><span class="status-tag neutral">بدون ادعای صرفه‌جویی</span></div><div class="metric-grid">${metrics.map(([label, value, note]) => `<article class="metric-card"><span class="section-kicker">${escapeHTML(label)}</span><strong>${escapeHTML(value)}</strong><p class="metric-note">${escapeHTML(note)}</p></article>`).join("")}</div><div class="guard-note" style="margin-top:15px"><strong>در تولید، خط مبنا باید با Sabah تعریف شود.</strong> فقط پس از دسترسی مجاز به نمونه‌های واقعی می‌توان زمان، خطا، بازگشت و ظرفیت پاسخ‌گویی را اندازه گرفت.</div></section>`;
  }

  function renderPresentationCard(analysis, stage) {
    const step = steps[stage];
    const top = topMatch(analysis);
    if (stage === 0) {
      return `<div class="present-card"><span class="present-eyebrow">${escapeHTML(step.label)}</span><h3>${escapeHTML(analysis.rfq.title)}</h3><p class="present-description">یک درخواست نمونه از ${escapeHTML(analysis.rfq.customer)} وارد شده است. ابتدا متن آزاد را می‌بینیم و سپس آن را به اقلام و مشخصات قابل بررسی تبدیل می‌کنیم.</p><div class="present-grid"><div class="present-box"><h4>متن درخواست</h4><p class="present-text">${escapeHTML(analysis.rfq.body)}</p></div><div class="present-box"><h4>زمینه ورودی</h4><div class="review-line"><span>کانال</span><strong>${escapeHTML(analysis.rfq.channel)}</strong></div><div class="review-line"><span>دریافت</span><strong>${escapeHTML(analysis.rfq.receivedAt)}</strong></div><div class="review-line"><span>داده</span><strong>کاملاً ساختگی</strong></div></div></div></div>`;
    }
    if (stage === 1) {
      return `<div class="present-card"><span class="present-eyebrow">${escapeHTML(step.label)}</span><h3>متن آزاد، ساختاریافته شد.</h3><p class="present-description">اقلام و فیلدهای صریح جدا می‌شوند؛ هیچ مقدار ناموجودی به‌طور خودکار تکمیل نمی‌شود.</p><div class="present-grid"><div class="present-box"><h4>اقلام استخراج‌شده</h4>${analysis.items.map((item, index) => `<div class="review-line"><span>${faNumber(index + 1)} · ${escapeHTML(item.requested)}</span><strong>${escapeHTML(item.quantityLabel)}</strong></div>`).join("")}</div><div class="present-box"><h4>شاخص‌های همین نمونه</h4><div class="present-metric-row"><div class="present-metric"><strong>${analysis.kpis.extractedItems}</strong><span>قلم</span></div><div class="present-metric"><strong>${analysis.kpis.needsReview}</strong><span>نیازمند تأیید</span></div><div class="present-metric"><strong>${analysis.kpis.completeness}</strong><span>تکمیل</span></div></div></div></div></div>`;
    }
    if (stage === 2) {
      return `<div class="present-card"><span class="present-eyebrow">${escapeHTML(step.label)}</span><h3>کاندیدها از مرجع عمومی می‌آیند.</h3><p class="present-description">برای هر قلم، دلیل تطبیق و مرجع دیده می‌شود. «تطبیق پیشنهادی» تصمیم نهایی یا تضمین قیمت نیست.</p><div class="present-grid"><div class="present-box"><h4>بهترین کاندید</h4><div class="match-hero" style="padding:12px"><div class="match-hero-top"><h3>${escapeHTML(top ? top.product.name : "بدون کاندید")}</h3><div class="score-ring">${faNumber(top ? top.confidence : 0)}٪</div></div><p>${escapeHTML(top ? top.reason : "نیاز به بررسی دستی")}</p></div></div><div class="present-box"><h4>کنترل‌های پاسخ</h4><div class="review-line"><span>قلم‌ها</span><strong>${faNumber(analysis.items.length)}</strong></div><div class="review-line"><span>مرجع قیمت</span><strong class="pending-price">در انتظار</strong></div><div class="review-line"><span>تصمیم</span><strong>با کارشناس</strong></div></div></div></div>`;
    }
    if (stage === 3) {
      return `<div class="present-card"><span class="present-eyebrow">${escapeHTML(step.label)}</span><h3>${analysis.hasAmbiguity ? "ابهام متوقف‌کننده شناسایی شد." : "کنترل ابهام انجام شد."}</h3><p class="present-description">${analysis.hasAmbiguity ? "در این مرحله سیستم به‌جای حدس‌زدن، سؤال دقیق می‌سازد و کاندیدها را در وضعیت اولیه نگه می‌دارد." : "فیلدهای اصلی این نمونه صریح هستند؛ تأیید فنی و تجاری همچنان انسانی باقی می‌ماند."}</p><div class="present-box">${analysis.hasAmbiguity ? analysis.items.flatMap((item) => item.missing).map((entry, index) => `<div class="review-line"><span>${faNumber(index + 1)} · سؤال روشن</span><strong>${escapeHTML(entry.question)}</strong></div>`).join("") : `<div class="guard-note"><strong>هیچ فیلد ناشناخته‌ای پر نشد.</strong> مشخصات نهایی باید با مرجع رسمی و کارشناس تأیید شود.</div>`}</div></div>`;
    }
    if (stage === 4) {
      return `<div class="present-card"><span class="present-eyebrow">${escapeHTML(step.label)}</span><h3>پاسخ، قبل از ارسال آماده بازبینی است.</h3><p class="present-description">سیستم یک پیش‌نویس قابل ویرایش می‌سازد؛ قیمت و شرایط تجاری عمداً خالی می‌ماند.</p><div class="present-grid"><div class="present-box"><h4>پیش‌نویس</h4><p class="present-text">${escapeHTML(analysis.draft)}</p></div><div class="present-box"><h4>کنترل‌های باقی‌مانده</h4><div class="review-line"><span>قیمت</span><strong class="pending-price">در انتظار قیمت‌گذاری</strong></div><div class="review-line"><span>مشخصات</span><strong>نیازمند بررسی</strong></div><div class="review-line"><span>ارسال</span><strong>غیرفعال</strong></div></div></div></div>`;
    }
    return `<div class="present-card"><span class="present-eyebrow">${escapeHTML(step.label)}</span><h3>AI آماده می‌کند؛ انسان کنترل می‌کند.</h3><p class="present-description">در نقطه آخر، کارشناس می‌تواند خروجی را تأیید، ویرایش یا برای بررسی بیشتر برگرداند. هیچ مسیر ارسال خودکاری در این نمونه وجود ندارد.</p><div class="approval-grid"><div class="approval-fact"><span>پیشنهاد محصول</span><strong>${escapeHTML(top ? top.product.name : "بررسی دستی")}</strong></div><div class="approval-fact"><span>مبلغ</span><strong class="pending-price">در انتظار قیمت‌گذاری</strong></div><div class="approval-fact"><span>اقدام بیرونی</span><strong>هیچ‌کدام</strong></div></div></div>`;
  }

  function renderPresentation() {
    const layer = $("#presentation-layer");
    if (!state.presentation) {
      layer.hidden = true;
      layer.innerHTML = "";
      return;
    }
    const analysis = state.presentationAnalysis || matcher.analyzeRFQ(state.selectedRfqId);
    layer.hidden = false;
    layer.innerHTML = `<div class="presentation-shell"><div class="presentation-top"><div><span class="presentation-kicker">LUMA · ارائه نمونه برای صباحی</span><h2>پاسخ‌گویی کنترل‌شده به درخواست مشتری</h2></div><span class="presentation-progress">${faNumber(state.presentationStage + 1)} از ${faNumber(steps.length)} · ${escapeHTML(steps[state.presentationStage].label)}</span></div><div class="presentation-content">${renderPresentationCard(analysis, state.presentationStage)}</div><div class="presentation-bottom"><span class="present-note">اطلاعات عمومی + درخواست ساختگی · بدون ارسال</span><div class="presentation-actions"><button class="button button-quiet" type="button" data-present="restart">شروع دوباره</button><button class="button button-light" type="button" data-present="previous" ${state.presentationStage === 0 ? "disabled" : ""}>قبلی</button><button class="button button-teal" type="button" data-present="next">${state.presentationStage === steps.length - 1 ? "خروج از ارائه" : "بعدی"}<span class="button-icon">←</span></button><button class="button button-light" type="button" data-present="close">بستن</button></div></div></div>`;
  }

  function setActiveNav() {
    document.querySelectorAll("[data-nav]").forEach((element) => element.classList.toggle("is-active", element.dataset.nav === state.section));
  }

  function render() {
    renderStepper();
    setActiveNav();
    const host = $("#view-host");
    if (state.section === "catalog") host.innerHTML = renderCatalog();
    else if (state.section === "metrics") host.innerHTML = renderMetrics();
    else if (state.stage === 0) host.innerHTML = renderInput();
    else if (state.stage === 1) host.innerHTML = renderExtraction();
    else if (state.stage === 2) host.innerHTML = renderMatching();
    else if (state.stage === 3) host.innerHTML = renderAmbiguity();
    else if (state.stage === 4) host.innerHTML = renderResponse();
    else host.innerHTML = renderApproval();
    renderPresentation();
  }

  function runAnalysis() {
    if (state.loading) return;
    state.loading = true;
    render();
    window.setTimeout(() => {
      const base = matcher.analyzeRFQ(state.selectedRfqId);
      const customText = state.customText || $("#rfq-text")?.value || "";
      if (customText) base.rfq = { ...base.rfq, body: customText };
      state.analysis = base;
      state.draft = base.draft;
      state.approval = "";
      state.loading = false;
      state.stage = 1;
      render();
      showToast("درخواست با منطق نمایشی و بدون سرویس بیرونی تحلیل شد.");
    }, 520);
  }

  function nextStage() {
    if (state.section !== "workbench") {
      state.section = "workbench";
      render();
      return;
    }
    if (state.stage === 0) {
      runAnalysis();
      return;
    }
    if (state.stage < steps.length - 1) {
      state.stage += 1;
      render();
    } else {
      showToast("دمو به پایان رسید؛ هیچ خروجی برای مشتری ارسال نشده است.");
    }
  }

  function previousStage() {
    if (state.stage > 0) {
      state.stage -= 1;
      render();
    }
  }

  function restart() {
    state.analysis = null;
    state.stage = 0;
    state.loading = false;
    state.customText = "";
    state.draft = "";
    state.approval = "";
    state.section = "workbench";
    render();
    showToast("دمو به حالت شروع برگشت.");
  }

  function openPresentation() {
    state.presentation = true;
    state.presentationStage = 0;
    state.presentationAnalysis = matcher.analyzeRFQ(state.selectedRfqId);
    render();
  }

  function presentationAction(action) {
    if (action === "close") {
      state.presentation = false;
      render();
      return;
    }
    if (action === "restart") {
      state.presentationStage = 0;
      state.presentationAnalysis = matcher.analyzeRFQ(state.selectedRfqId);
      renderPresentation();
      return;
    }
    if (action === "previous") {
      state.presentationStage = Math.max(0, state.presentationStage - 1);
      renderPresentation();
      return;
    }
    if (action === "next") {
      if (state.presentationStage >= steps.length - 1) {
        state.presentation = false;
        render();
        showToast("ارائه تمام شد؛ ارسال خودکار در این نمونه وجود ندارد.");
      } else {
        state.presentationStage += 1;
        renderPresentation();
      }
    }
  }

  document.addEventListener("click", (event) => {
    const rfqButton = event.target.closest("[data-rfq]");
    if (rfqButton) {
      state.selectedRfqId = rfqButton.dataset.rfq;
      state.analysis = null;
      state.customText = "";
      state.draft = "";
      state.approval = "";
      state.stage = 0;
      state.section = "workbench";
      render();
      return;
    }
    const navButton = event.target.closest("[data-nav]");
    if (navButton) {
      state.section = navButton.dataset.nav;
      render();
      return;
    }
    const stepButton = event.target.closest("[data-step]");
    if (stepButton && !stepButton.disabled) {
      const target = Number(stepButton.dataset.step);
      if (target === 0 || state.analysis) {
        state.section = "workbench";
        state.stage = target;
        render();
      }
      return;
    }
    if (event.target.closest("#presentation-button")) {
      openPresentation();
      return;
    }
    const presentButton = event.target.closest("[data-present]");
    if (presentButton) {
      presentationAction(presentButton.dataset.present);
      return;
    }
    if (event.target.closest("#analyze-button") || event.target.closest("#next-button") && state.stage === 0) {
      runAnalysis();
      return;
    }
    if (event.target.closest("#previous-button")) {
      previousStage();
      return;
    }
    if (event.target.closest("#next-button")) {
      nextStage();
      return;
    }
    if (event.target.closest("#restart-button")) {
      restart();
      return;
    }
    const approvalButton = event.target.closest("[data-approval]");
    if (approvalButton) {
      const action = approvalButton.dataset.approval;
      if (action === "edit") state.stage = 4;
      else if (action === "back") state.stage = 3;
      else if (action === "approved" || action === "review") state.approval = action;
      render();
      if (action === "approved") showToast("تأیید انسانی فقط در وضعیت نمایشی ثبت شد؛ ارسال انجام نشد.");
      return;
    }
    if (event.target.closest("#reset-input-button")) {
      state.customText = "";
      const textarea = $("#rfq-text");
      if (textarea) textarea.value = currentRfq().body;
      return;
    }
  });

  document.addEventListener("input", (event) => {
    if (event.target.id === "rfq-text") state.customText = event.target.value;
    if (event.target.id === "draft-editor") state.draft = event.target.value;
  });

  const params = new URLSearchParams(window.location.search);
  if (data.rfqs.some((rfq) => rfq.id === params.get("rfq"))) state.selectedRfqId = params.get("rfq");
  const requestedStage = Number(params.get("stage"));
  if (Number.isInteger(requestedStage) && requestedStage > 0 && requestedStage < steps.length) {
    state.analysis = matcher.analyzeRFQ(state.selectedRfqId);
    state.draft = state.analysis.draft;
    state.stage = requestedStage;
  }
  render();
}());
