# LUMA — Tehran B2B AI & Workflow Automation Market Study (2026–2027)

**A note on methodology and evidence quality (read first)**

This report was compiled using web research (English and Persian sources) combined with structural reasoning about B2B technology buying behavior, applied to what is verifiably known about Tehran's economic geography, chambers of commerce, and the sanctions/infrastructure environment. It is **not** a database of named companies with verified financials — no such public dataset exists in a form I could responsibly cite. Throughout, claims are labeled:

- **[Verified]** — confirmed via a specific, citable source found during this research.
- **[Estimate]** — a reasonable numeric or qualitative approximation based on known Iranian economic structure, not from a specific cited source. Treat as a planning assumption, not a fact to quote to clients.
- **[Assumption]** — a working hypothesis this report relies on that should be tested during LUMA's own discovery phase (Section 12).

Two important 2026 context facts that shape everything below are **[Verified]**:

- Tehran's chambers of commerce are real, active, and well-documented: the **Tehran Chamber of Commerce, Industries, Mines and Agriculture (TCCIMA)**, founded 1884, has roughly **47,500 members** as of mid-2025, and the national **Iran Chamber of Commerce, Industries, Mines & Agriculture (ICCIMA)** has about 20,000 members. Both maintain active websites, committees by sector, and public activity (tccim.ir / iccima.ir).
- Iran's technology environment in 2026 is materially harder than in prior years. Following escalation of US–Iran tensions in 2026, Iranian developers and businesses have been losing access to GitHub, npm, VS Code extensions, most major cloud platforms, and most payment processors, on top of the pre-existing OFAC-driven restrictions on AWS, Azure, and Google Cloud that have applied for years. Iran has also built its own "National Information Network" intranet (via domestic providers such as ArvanCloud, which itself was sanctioned by the US Treasury in 2023 for its role in state censorship infrastructure). This has two direct consequences for LUMA: (1) **foreign SaaS AI tools are functionally unavailable or unreliable for most Tehran companies**, which is a structural tailwind for a *local, custom-built* alternative; and (2) LUMA's own delivery stack (LLM APIs, cloud hosting, dev tooling) must be built around domestic or circumvention-resilient infrastructure, which is itself a client-facing risk factor to plan for.

This second fact is arguably the single most important market condition in this whole report: **it is a major reason a domestic AI vendor like LUMA has a real moat that a foreign competitor cannot easily cross**, and it should shape the executive conclusion.

---

## 1. Executive Conclusion

**The strongest B2B opportunity for LUMA is mid-size, multi-branch/multi-plant Iranian manufacturers, importer-distributors, and trading houses (bazaar-adjacent or industrial-estate-based) with 50–500 employees, ~10–30 years of operating history, and revenue/scale sufficient to run several departments (sales, procurement, warehousing, accounting, customer service) — but whose internal software stack is still spreadsheets, Telegram/WhatsApp, phone calls, and at most a legacy/local ERP (e.g., Iranian ERPs like Hamkaran System's "Rayvarz," Sepidar, or Comfar-type systems) that was never extended into AI-era capabilities.**

This is the classic "digital-maturity paradox sweet spot" the brief describes: these companies are large enough to have real operational pain (dozens of daily quotations, thousands of invoices, hundreds of supplier/customer WhatsApp threads) and real budget authority (a single owner-CEO or small executive team who can approve a project without a twelve-committee procurement process), but they have **no internal software engineering team**, so they cannot build what they need themselves — and because of sanctions, they largely cannot buy an off-the-shelf Western SaaS AI tool even if they wanted to. That combination — real pain, real budget, no internal build capacity, no easy external substitute — is exactly the gap LUMA should fill.

**[Assumption]** Within this broad segment, the industries with the clearest, most numerically defensible ROI stories (Section 2) are: **B2B trading/import-distribution companies** (customs, quotation, and inventory-heavy), **industrial manufacturers producing for other businesses** (auto parts, packaging, construction materials, food processing at scale), and **larger private healthcare/diagnostic groups and pharma distributors** (document- and compliance-heavy, high transaction volume, strong ability to pay). These three should be LUMA's first three verticals, in that priority order, because they combine the largest defensible pain points with the fewest political/regulatory landmines.

**Segments to actively avoid at this stage** (detailed in Section 4) include: fintech/proptech startups and app-based platforms (they build internally), state-owned/quasi-governmental giants (procurement too slow, political risk too high), and micro-retail or single-location small shops (no budget, no data, no ROI case).

---

## 2. Ranked Industries (Top ~20)

Each entry gives an **opportunity score (0–100)**, using the model defined in Section 8, plus the required detail. Scores are **[Estimate]**, built from reasoning about typical structure of each industry in Iran, not from audited data — they are directional, meant to guide where LUMA spends its first outreach effort, and should be refined once real company-level data is gathered (Section 12).

| # | Industry / Category | Score | Digital Maturity | Sales Difficulty |
|---|---|---|---|---|
| 1 | Import/export & wholesale trading houses (general goods, machinery, chemicals, electronics) | 84 | Low–Moderate | Moderate |
| 2 | Auto parts manufacturing & distribution | 82 | Low–Moderate | Moderate |
| 3 | Construction materials manufacturing & distribution | 80 | Low | Moderate–Hard |
| 4 | Pharmaceutical distribution & wholesale | 79 | Moderate | Moderate |
| 5 | Food & beverage manufacturing (mid-size, B2B-heavy) | 78 | Low–Moderate | Moderate |
| 6 | Private hospital groups & large diagnostic laboratory chains | 77 | Moderate | Moderate–Hard |
| 7 | Packaging manufacturing (industrial, print+package) | 75 | Low | Moderate |
| 8 | Freight forwarding / customs brokerage / logistics operators | 75 | Low–Moderate | Moderate |
| 9 | Medical equipment importers/distributors | 74 | Moderate | Moderate |
| 10 | Real estate developers (mid-size, multi-project) | 73 | Low–Moderate | Moderate–Hard |
| 11 | Insurance brokerage agencies (multi-branch) | 72 | Moderate | Moderate |
| 12 | Industrial equipment / machinery manufacturers | 71 | Low | Hard |
| 13 | Accounting/audit & tax advisory firms (mid-size, multi-client) | 70 | Moderate | Easy–Moderate |
| 14 | Property management companies (commercial portfolios) | 68 | Low | Moderate |
| 15 | Consumer goods distribution (FMCG regional distributors) | 68 | Low–Moderate | Moderate |
| 16 | Textile & garment manufacturing (mid-size factories) | 66 | Low | Hard |
| 17 | Automotive maintenance/service chains (multi-branch) | 65 | Low | Moderate |
| 18 | HR/recruitment & staffing agencies | 64 | Moderate | Easy–Moderate |
| 19 | Advertising/marketing & production agencies (mid-size) | 62 | Moderate–High | Moderate |
| 20 | Private educational institutions & training organizations (multi-branch) | 60 | Low–Moderate | Moderate |
| 21 | Legal services firms (mid-size, multi-partner) | 58 | Low | Hard (conservative culture) |
| 22 | Tourism/hospitality operators (multi-property or agency chains) | 55 | Moderate | Moderate |
| 23 | Agriculture-related trading/processing companies (Tehran HQ, provincial operations) | 54 | Low | Hard (owner often traditional, remote ops) |

### Detail for the top 8

**1. Import/export & wholesale trading houses — Score 84**
- *Typical profile:* Family-owned or founder-led, 20–200 employees, 10–40+ years old, often clustered near Tehran's traditional trading districts (e.g., around the Grand Bazaar and adjacent commercial streets) or in newer commercial towers. Revenue driven by volume of transactions rather than headcount.
- *Workflow problems:* Quotations built manually in Excel/Word per customer; supplier communication scattered across WhatsApp/Telegram/email with no central record; customs and shipping documentation tracked on paper or in spreadsheets; pricing recalculated manually against currency fluctuation; no unified view of open orders vs. inventory in transit.
- *AI opportunities:* AI-assisted quotation generation from a product/price database; a WhatsApp/Telegram-integrated conversation-log-to-CRM extractor (turning informal chats into structured customer/order records — very high value in Iran given reliance on these channels); automated customs-document drafting and checklist compliance; a natural-language internal search across years of supplier/customer correspondence.
- *Buyer:* Owner/Managing Director, sometimes a "Commercial Director." Very short chain of approval — this is a major advantage over larger companies.
- *Barriers:* Low trust in outside vendors seeing pricing/margin data (confidentiality concerns); currency-volatility-driven short-term thinking can crowd out "long-term efficiency" investments; owner may be older and less digitally fluent, requiring a very concrete, in-person ROI pitch rather than a technical one.
- *Potential project value:* **[Estimate]** initial pilot projects of $3,000–$15,000 equivalent (in local currency), with expansion contracts $15,000–$60,000 for multi-department rollouts.

**2. Auto parts manufacturing & distribution — Score 82**
- *Typical profile:* Concentrated in and around Tehran's industrial belt (western/southwestern industrial estates near the auto manufacturing corridor toward Karaj, and southern industrial zones). 50–500 employees, serving both OEM supply chains (Iran Khodro, SAIPA ecosystem) and aftermarket/wholesale.
- *Workflow problems:* Quality control still largely manual visual inspection with paper checklists; inventory across multiple SKUs (parts catalogs can run into thousands of items) tracked in disconnected spreadsheets between production, warehouse, and sales; order-to-delivery communication with distributors via phone/WhatsApp; warranty/defect claims processed manually.
- *AI opportunities:* Computer-vision-assisted quality control (defect/classification on production line images); demand forecasting and inventory optimization from historical sales data; AI-assisted parts-catalog search (matching customer descriptions to SKUs, which is a huge time sink in auto parts sales); automated claims-processing triage.
- *Buyer:* Production/Operations Director for QC and inventory projects; Commercial/Sales Director for the parts-catalog search tool.
- *Barriers:* Integration with legacy production-line hardware may be difficult; safety-critical QC applications require careful liability framing; possible resistance from floor supervisors who see AI QC as a threat to their role.
- *Potential project value:* **[Estimate]** $10,000–$40,000 for a QC pilot; $5,000–$20,000 for a catalog-search/quotation tool.

**3. Construction materials manufacturing & distribution — Score 80**
- *Typical profile:* Cement, steel products, tile, fixtures, prefabricated components — companies serving Tehran's large and continuous construction sector. Often family businesses with 30–300 employees, sometimes multi-generational.
- *Workflow problems:* Project-based quotation processes that are slow (days, not hours) because pricing depends on manually checking current material costs, discounts, and project specifics; delivery scheduling coordinated by phone; no unified dashboard for management to see pipeline of projects/orders.
- *AI opportunities:* AI-assisted quotation and proposal generation tied to a live cost database; management dashboard aggregating sales pipeline, production capacity, and delivery schedules; document analysis for incoming project specifications/RFQs (extracting requirements automatically from PDFs sent by contractors).
- *Buyer:* Managing Director or Commercial Director.
- *Barriers:* Construction sector cash-flow is volatile with Iran's economic cycles, which can make companies budget-cautious; some players are effectively project-based/informal and don't have consistent digital records to build on.
- *Potential project value:* **[Estimate]** $5,000–$25,000.

**4. Pharmaceutical distribution & wholesale — Score 79**
- *Typical profile:* Regulated, higher-professionalism sector than most others on this list; distributors and wholesalers serving pharmacies and hospitals across Tehran province and beyond, 50–400 employees.
- *Workflow problems:* Regulatory/compliance documentation is heavy and largely manual; order processing from thousands of pharmacy customers involves repetitive phone/fax/WhatsApp-based ordering; expiry-date and batch tracking often semi-manual even where an ERP exists; customer service volume is high (order status, availability queries).
- *AI opportunities:* AI customer-service assistant handling routine pharmacy order/availability queries; document processing for regulatory paperwork and batch/expiry tracking; demand forecasting per product/region to reduce stockouts and overstock.
- *Buyer:* Operations Director or a dedicated "IT/Systems Manager" if one exists (more likely here than in trading companies) — but the Managing Director typically still signs off on spend.
- *Barriers:* Regulatory sensitivity (medicine data, patient-adjacent information) increases caution; if a legacy pharma-specific ERP is already in place, integration complexity rises; data privacy concerns are more real here than elsewhere.
- *Potential project value:* **[Estimate]** $8,000–$35,000.

**5. Food & beverage manufacturing (mid-size, B2B-heavy) — Score 78**
- *Typical profile:* Factories supplying retail chains, wholesalers, and food-service; 50–400 employees; frequently have some basic production-line automation but weak "office-side" digitization.
- *Workflow problems:* Order aggregation from many retail/wholesale buyers is manual; production planning reconciled against orders by spreadsheet; quality/compliance documentation (health/safety certificates) tracked on paper.
- *AI opportunities:* Demand forecasting/production planning assistant; automated order intake from multiple channels (phone, WhatsApp, email) into one system; document management for certifications and compliance audits.
- *Buyer:* Operations Director, sometimes Commercial Director for the order-intake tool specifically.
- *Barriers:* Food safety regulatory environment adds caution; margins can be thin, making ROI framing (cost/time savings) essential rather than "nice to have" framing.
- *Potential project value:* **[Estimate]** $6,000–$25,000.

**6. Private hospital groups & large diagnostic laboratory chains — Score 77**
- *Typical profile:* Multi-branch private hospitals, clinic groups, and diagnostic lab chains in Tehran (a sector with real scale and real budgets, distinct from single-doctor clinics).
- *Workflow problems:* Patient intake and record-keeping fragmented across departments; report generation (lab results, imaging summaries) partly manual; call-center volume for scheduling and inquiries is high and repetitive; internal knowledge (protocols, insurance rules) scattered and hard to search for staff.
- *AI opportunities:* AI-assisted call-center/scheduling assistant; automated report drafting/summarization from structured lab data; internal knowledge-base assistant for staff (insurance rules, protocols); document classification for incoming referrals and insurance paperwork.
- *Buyer:* Hospital/Clinic Group Administrator or Operations Director — rarely the physicians themselves.
- *Barriers:* Higher regulatory and data-privacy sensitivity (patient data); more bureaucratic decision processes than a family trading company; may already have some hospital information system (HIS) in place, requiring integration.
- *Potential project value:* **[Estimate]** $10,000–$45,000, largest ceiling of the group.

**7. Packaging manufacturing (industrial print + package) — Score 75**
- *Typical profile:* Mid-size factories producing packaging for FMCG, pharma, and food clients; 30–250 employees.
- *Workflow problems:* Custom-order quotation is slow (each client design/spec is unique); print-quality control still largely manual visual check; order tracking across design-approval-production-delivery stages is fragmented.
- *AI opportunities:* Quotation automation from spec sheets; computer-vision print-defect detection; production-status dashboard visible to sales and management.
- *Buyer:* Production Director or Managing Director.
- *Barriers:* Smaller player fragmentation (many small competitors) can mean weaker individual budgets; equipment-integration variability.
- *Potential project value:* **[Estimate]** $5,000–$20,000.

**8. Freight forwarding / customs brokerage / logistics operators — Score 75**
- *Typical profile:* Companies handling import/export logistics, customs clearance, and domestic freight; 20–150 employees, often clustered near ports-adjacent Tehran offices and customs zones.
- *Workflow problems:* Enormous volume of shipping/customs documents processed manually; client status inquiries handled by phone; tracking of shipments across multiple carriers/customs stages is fragmented.
- *AI opportunities:* Document extraction/classification for bills of lading, customs forms, invoices; automated client status-update messaging; internal search across shipment history.
- *Buyer:* Operations Manager or Managing Director.
- *Barriers:* High document variability (many formats/languages) increases build complexity; regulatory/customs-process changes require ongoing maintenance.
- *Potential project value:* **[Estimate]** $8,000–$30,000.

---

## 3. Top Priority Segments (First 5–8 to Target)

**[Assumption]** Ranked by a combination of opportunity score, sales-cycle speed, and how quickly LUMA could get a credible reference case:

1. **Import/export & wholesale trading houses** — fastest sales cycle, single decision-maker, high pain, immediate WhatsApp/Telegram-to-CRM value story.
2. **Auto parts manufacturing & distribution** — large, well-organized sector with strong existing chambers/associations to reach through, clear ROI in QC and catalog search.
3. **Construction materials manufacturing & distribution** — continuous underlying demand (construction is persistent even in downturns), clear quotation-speed ROI story.
4. **Pharmaceutical distribution & wholesale** — high transaction volume, strong ability to pay, and a sector where a working case study builds enormous credibility with regulators-adjacent buyers.
5. **Private hospital groups & diagnostic labs** — highest ceiling project value; slower sales cycle but worth cultivating in parallel to #1–4, not instead of them.
6. **Packaging manufacturing** — good "adjacent-sale" target once LUMA has a reference in food/pharma/FMCG (packaging companies serve the same clients).
7. **Freight forwarding / customs brokerage** — high document-processing pain, and freight companies are natural referral sources into trading houses and manufacturers (#1–3).
8. **Insurance brokerage agencies (multi-branch)** — good target for a document-processing/claims-triage pitch, easier sales cycle than insurers themselves, decent existing digital baseline to build on.

**Why this order:** segments 1–3 let LUMA build its first 3–5 reference projects quickly with short sales cycles and clear before/after metrics (time-to-quote, order-processing time). Those references then become the credibility asset needed to approach the higher-value but slower-moving segments (5, 8) and the harder-to-reach professional segments (legal, accounting) later.

---

## 4. Segments to Avoid (At This Stage)

- **Fintech, proptech, and app-based digital platforms.** These companies look attractive because they're "tech-forward," but per the brief's digital-maturity paradox, they almost always have internal engineering and often internal AI/ML capability. They are more likely to want an API or infrastructure partnership than an outsourced custom build, and their technical teams will often view external AI vendors skeptically.
- **State-owned and quasi-governmental large enterprises** (e.g., major state industrial holding companies, national banks). Procurement cycles are extremely long, political risk is high, decision-making is diffuse across committees, and payment terms are frequently unfavorable to vendors. **[Assumption]** These may become viable *later*, once LUMA has scale and formal certifications/relationships, but are a poor early-stage target.
- **Very small, single-location retail or service shops.** Per the brief, these lack budget, organizational readiness, and enough operational data to make a custom AI project sensible. A single-branch shop with 5 employees is a weak target regardless of how "manual" its processes look.
- **Heavily foreign-currency-exposed export businesses currently under acute sanctions pressure** (e.g., companies directly on OFAC lists or in sectors under intense international scrutiny — defense-adjacent, some petrochemical exporters). Beyond ethical and reputational risk, doing business with sanctioned entities creates legal exposure for LUMA if it ever wants to use foreign cloud infrastructure, foreign LLM APIs, or seek any international partnership. **This is worth treating as a hard filter, not just a scoring deduction.**
- **Advertising/marketing agencies and other "creative-tech-native" service firms**, despite decent scores — many already use AI content tools directly (ChatGPT-style tools, even through workarounds) and see themselves as AI-savvy already, making them harder to convince they need a *custom* build rather than a subscription.

---

## 5. Ideal Customer Profiles (ICPs)

### ICP-A: "The Established Trading House"
- **Industry:** Wholesale import/export, general trading, industrial supply distribution.
- **Employees:** 20–150.
- **Scale:** Owner-founded, 10–40 years in business, regional or national customer base, meaningful but not massive revenue (enough to run several departments and afford real estate/office presence, but not enough to run an internal dev team).
- **Operational characteristics:** High volume of quotations, orders, and supplier/customer communications; multiple product lines; currency-sensitive pricing.
- **Digital maturity:** Low–moderate — Excel-heavy, WhatsApp/Telegram-dependent, maybe a basic accounting package, no real CRM.
- **Likely existing software:** Accounting software (possibly a local package), no CRM, no BI/dashboarding.
- **Organizational pain:** Slow, inconsistent quotations; lost/forgotten customer conversations; no visibility into which customers/products are actually most profitable.
- **Likely decision-maker:** Owner/Managing Director, occasionally a "Commercial Director" if the company has grown past founder-only management.
- **Budget potential:** **[Estimate]** Moderate — willing to spend if ROI is concrete and framed in terms of time saved or deals not lost.
- **Trigger events:** Recent growth that has outpaced their manual processes; a costly mistake (lost order, pricing error) that got the owner's attention; a competitor visibly modernizing.
- **Warning signs of a bad fit:** Business is purely relationship/trust-based with very few repeatable transactions (e.g., a broker doing 5 large deals a year, not hundreds of small ones); owner is resistant to any change in how the business "has always worked"; company is in active financial distress.

### ICP-B: "The Under-Digitized Manufacturer"
- **Industry:** Auto parts, construction materials, packaging, food manufacturing.
- **Employees:** 50–400.
- **Scale:** Has a real factory/production facility, serves multiple B2B customers, likely has some ERP or production-planning software but it's old, poorly used, or not extended to newer needs.
- **Operational characteristics:** Physical production plus a sales/admin office; quality control, inventory, and order management are the core pain points.
- **Digital maturity:** Low — production may have some automation, but "white-collar" workflows (sales, QC records, planning) are manual.
- **Likely existing software:** A legacy or partial ERP (possibly a domestic Iranian ERP vendor), used mainly for accounting, not operations.
- **Organizational pain:** QC inconsistency, inventory mismatches, slow quotation-to-order cycle, management lacking real-time visibility into production/sales status.
- **Likely decision-maker:** Operations/Production Director for shop-floor projects; Managing Director for anything requiring significant spend.
- **Budget potential:** **[Estimate]** Moderate–high, especially if the company supplies larger OEM customers who are themselves pushing for quality/traceability improvements.
- **Trigger events:** A quality complaint from a major customer; entry into a new, larger customer relationship requiring better documentation/traceability; management succession (a newer, more digitally comfortable generation taking over).
- **Warning signs of a bad fit:** Production is highly artisanal/custom (low repeatability, so little data to leverage); the factory is in active decline (shrinking orders, layoffs); ownership is disengaged from operations.

### ICP-C: "The Multi-Branch Professional/Healthcare Group"
- **Industry:** Private hospital/clinic groups, diagnostic labs, larger pharmacy chains, insurance brokerages, accounting firms with multiple offices.
- **Employees:** 50–500, spread across multiple locations.
- **Scale:** Meaningful brand recognition, professional management structure (not just a single owner), formal HR/finance functions.
- **Operational characteristics:** High client/patient/case volume; document- and compliance-heavy; call-center or front-desk-heavy customer interaction.
- **Digital maturity:** Moderate — likely has *some* system (HIS, practice management, accounting), but internal knowledge search, reporting, and communication automation are weak.
- **Likely existing software:** Sector-specific software (hospital information system, insurance management system) that is functional but not extended with AI capability.
- **Organizational pain:** High administrative overhead, slow report turnaround, front-desk/call-center bottlenecks, difficulty finding institutional knowledge quickly.
- **Likely decision-maker:** Group Administrator, Operations Director, or (in professional firms) a Managing Partner.
- **Budget potential:** **[Estimate]** Highest of the three ICPs, but slowest sales cycle.
- **Trigger events:** Expansion to a new branch straining existing manual processes; regulatory audit exposing documentation gaps; leadership change bringing modernization mandate.
- **Warning signs of a bad fit:** Heavily bureaucratic public/semi-public institution rather than a private group; already has (or is actively building) an internal IT/software team; extremely conservative culture with low tolerance for pilot experimentation.

---

## 6. AI Opportunity Map (Workflow → AI Product)

| Business Workflow | Common Problem | AI/Automation Solution | Primary User |
|---|---|---|---|
| Sales quotation | Manual, slow, inconsistent pricing across reps | AI-assisted quotation generator tied to a pricing/product database | Sales team, Commercial Director |
| Customer/supplier chat (WhatsApp/Telegram) | Informal, unsearchable, no CRM record | Chat-to-CRM extraction & structured logging assistant | Sales, Management |
| Document intake (invoices, customs forms, contracts) | Manual data entry, slow, error-prone | AI document processing/extraction pipeline | Admin/finance staff |
| Internal knowledge (policies, protocols, product specs) | Scattered across people's heads, old files, group chats | Internal knowledge assistant / semantic search | All staff, especially new hires |
| Customer service / call center | High call volume, repetitive questions | AI-assisted or AI-first customer response system | Customer service reps |
| Quality control (visual inspection) | Manual, inconsistent, slow | Computer-vision defect/classification assistant | Production/QC staff |
| Inventory & demand planning | Spreadsheet-based, reactive not predictive | Demand forecasting and inventory optimization model | Operations/warehouse managers |
| Management reporting | Manually compiled from multiple sources, delayed | Automated dashboard aggregating sales/ops/finance data | Owners, Directors |
| Contract/document review | Manual reading, slow, inconsistent | Contract analysis assistant (flagging terms, deadlines, risks) | Legal/procurement staff |
| HR/recruitment screening | Manual resume review, slow shortlisting | AI-assisted candidate screening and matching | HR staff |
| Employee onboarding/training | Repetitive manual instruction, inconsistent | AI-guided onboarding copilot / internal FAQ bot | HR, new employees |
| Marketing/content production | Slow manual content creation | AI-assisted content drafting workflow (with human review) | Marketing staff |

---

## 7. Decision-Maker Map

| Segment | Primary Contact | Why | Secondary Contact |
|---|---|---|---|
| Trading houses | Owner / Managing Director | Sole authority, understands the pain directly | Commercial Director (if exists) |
| Manufacturers (auto parts, construction, packaging, food) | Operations/Production Director | Owns the workflow pain; MD signs off on budget | Managing Director (final approval) |
| Pharma distribution | Operations Director or Systems/IT Manager | More formal structure than trading houses | Managing Director |
| Hospitals/diagnostic labs | Hospital/Group Administrator | Runs day-to-day operations and budget for admin systems | Operations Director |
| Insurance brokerages | Managing Director or Operations Manager | Multi-branch coordination needs central buy-in | Branch managers (as champions/pilot sites) |
| Logistics/freight forwarding | Operations Manager | Owns document/process pain directly | Managing Director |
| Accounting/legal/professional firms | Managing Partner | Partnership governance model | Office/Operations Manager |

**General rule [Assumption]:** In founder-led companies (most of ICP-A and much of ICP-B), go straight to the owner/MD — layers of hierarchy are thin and the MD both understands and controls budget. In larger, more structured organizations (ICP-C, larger manufacturers), start with the operational director who feels the pain daily, and use them as an internal champion to reach the MD/administrator who controls budget.

---

## 8. Company Scoring System (0–100 Prospect Qualification Model)

### Design principle

Per the brief's core constraint, **digital maturity must not simply increase the score** — it should be scored as a *band*, peaking at "moderate" and penalized at both extremes (too low = no readiness/data/budget; too high = builds internally or needs infrastructure not custom software).

### Formula

```
Total Score = 
    (0.20 × Company Strength) +
    (0.18 × Operational Complexity) +
    (0.18 × AI ROI Potential) +
    (0.15 × Digital Maturity Band Score) +
    (0.12 × Decision-Maker Accessibility) +
    (0.10 × Low Internal Tech Capability, inverted) +
    (0.07 × Regulatory/Implementation Ease)
```

Each factor is scored 0–100 individually, then weighted as above.

### Factor definitions

1. **Company Strength (0.20)** — Signals: multiple branches/locations, years in business (10+ ideal), visible corporate/B2B clients, factory or warehouse facilities, stable or growing hiring activity, national (not just local) distribution.

2. **Operational Complexity (0.18)** — Signals: multiple departments, multiple product lines/SKUs, high transaction/document/communication volume, multi-step approval workflows.

3. **AI ROI Potential (0.18)** — Can the pain be tied to a number (hours saved, errors reduced, orders processed per employee, time-to-quote)? Score high only where a believable numeric story exists.

4. **Digital Maturity Band Score (0.15)** — **This is the non-linear factor.** Scored as a curve, not a line:
   - 0–20 (almost no digital presence, no usable data): score **20/100** — too little to build on.
   - 21–45 (basic website, some spreadsheets, an old accounting package): score **60/100**.
   - 46–70 (a working but under-extended ERP/CRM, structured data exists, some staff comfort with software): score **100/100** — the sweet spot.
   - 71–90 (modern SaaS stack, API-comfortable staff, some internal automation already): score **55/100** — declining, they may not need LUMA.
   - 91–100 (in-house dev team, proprietary systems, dedicated IT/AI staff): score **10/100** — will build internally.

5. **Decision-Maker Accessibility (0.12)** — Signals: flat/founder-led org structure, publicly listed leadership contact info, evidence of an approachable single decision point vs. a diffuse committee.

6. **Low Internal Tech Capability, inverted (0.10)** — Absence of negative signals from Section 9 (no ML/AI job postings, no dedicated engineering department, no proprietary software products). Scored inverted: fewer internal-capability signals = higher score.

7. **Regulatory/Implementation Ease (0.07)** — Lower score for heavily regulated data (health, finance, government-adjacent); higher score for straightforward commercial/operational data.

### Interpretation bands

- **75–100:** Priority prospect — pursue immediately.
- **55–74:** Good prospect — pursue in normal outreach cadence.
- **35–54:** Marginal — worth a light-touch approach (e.g., inclusion in broader outreach campaigns) but not a priority.
- **0–34:** Deprioritize — either too small/weak or too digitally advanced/self-sufficient.

---

## 9. Public Qualification Signals (For Automated Website/Public-Data Analysis)

### Signals of company quality (raise score)
- Multiple office/branch/factory locations listed.
- Stated years in operation ("since 19XX" / "تأسیس ۱۳XX").
- Named major clients or "trusted by" sections, especially other well-known companies.
- Visible product catalog with meaningful breadth (dozens+ of SKUs).
- Factory/warehouse photos or facility descriptions.
- Active job postings (signals stability/growth) — but check *what kind* of jobs (see negative signals below).
- Certifications displayed (ISO, ministry approvals, ISIPO industrial-estate membership, TCCIMA/ICCIMA membership badges).
- Presence in an industrial estate (شهرک صنعتی) directory, which is itself a strong scale/legitimacy signal since ISIPO (Iran Small Industries and Industrial Parks Organization) formally registers occupants.

### Signals of low/moderate digital maturity (raise score, within the "sweet spot" band)
- Outdated website design (old templates, no mobile responsiveness, broken links).
- Product catalog only available as downloadable PDF, not a searchable web catalog.
- Contact forms that clearly route to manual follow-up ("we will call you") rather than instant self-service.
- No online ordering, quoting, or customer portal.
- Heavy reliance on a phone number and WhatsApp/Telegram link as the *only* contact methods.
- References to legacy or generic accounting software rather than modern cloud tools.
- Job postings for manual/clerical roles ("data entry," "office admin," "order-taking operator") — this is a particularly strong positive signal, since it shows a workflow LUMA could partially automate.

### Signals of high internal technical capability (lower score — likely bad fit)
- Dedicated "Careers" pages advertising software engineer, ML engineer, or data scientist roles.
- An engineering or "Digital/Tech" department named on an org chart or About page.
- The company's own product *is* software (SaaS platform, app, marketplace).
- Public GitHub presence, technical blog, or engineering-culture content.
- Explicit mentions of "our AI team" or "our in-house development."

**[Assumption]** Because Iran's public job-board and LinkedIn presence is thinner than in Western markets, these signals will often need to be triangulated from Persian-language sources (company Instagram pages, Divar/Jobinja-style Iranian job boards, and direct company websites) rather than LinkedIn alone, which has lower penetration among traditional Iranian SMEs.

---

## 10. Tehran Company-Discovery Sources

| Source | What it provides | Reliability | Coverage | Notes |
|---|---|---|---|---|
| **TCCIMA (tccim.ir)** — Tehran Chamber of Commerce, Industries, Mines & Agriculture | Member directory, sector committees, news, trade events | High (official body, ~47,500 members as of 2025) [Verified] | Broad, Tehran-focused | Best single starting point; has sector-specific committees (industry, transport, energy, etc.) that indicate active associations to approach for introductions |
| **ICCIMA (iccima.ir)** — Iran national chamber | National-level directory and sector data | High (official) [Verified] | National, includes Tehran-based HQs | Useful for companies headquartered in Tehran but operating nationally |
| **ISIPO (isipo.ir) / Tehran provincial branch (tehran.isipo.ir)** — Iran Small Industries & Industrial Parks Organization | Registry of formal industrial estates/parks (شهرک‌های صنعتی) in Tehran province, with occupant directories | High (official government body) [Verified] | Strong for manufacturing specifically | Extremely valuable — companies located in a registered industrial estate are, by definition, formal, scaled businesses (a strong pre-filter) |
| **Industry-specific associations/unions (اتحادیه/انجمن صنفی)** | Sector membership lists (e.g., auto parts makers' association, food industry association, pharma distributors' union) | Moderate–High (varies by association) | Sector-deep, not broad | Requires per-sector discovery; often the best source of "who's who" in a given vertical |
| **Google Maps / local map listings** | Business name, address, category, sometimes phone/website, reviews | Moderate (self-reported, uneven completeness) | Very broad | Good for initial geographic clustering (e.g., mapping all "auto parts wholesale" listings in a district) but needs manual verification |
| **Iranian business directories (e.g., sector-specific B2B directories, trade-fair exhibitor lists)** | Company listings, sometimes with contact details | Moderate | Sector-dependent | Trade-fair exhibitor lists (from Tehran International Fairground events) are a particularly strong source since exhibiting requires real budget |
| **LinkedIn** | Company pages, employee counts, job postings, leadership names | Moderate for larger/more international firms, weak for traditional SMEs | Uneven — biased toward more digitally-savvy companies | Useful mainly for cross-checking ICP-C (professional/healthcare) and larger manufacturers; less useful for ICP-A trading houses |
| **Iranian job boards (e.g., Jobinja and similar platforms)** | Job postings — a strong proxy for both scale (are they hiring) and tech capability (what roles) | Moderate–High for active job-posting signal | Broad among formal companies | Central to Section 9's signal detection — check both volume and *type* of postings |
| **Company websites directly** | Self-description, product catalogs, client lists, contact info, About/history pages | Varies widely | Universal (if a website exists) | Primary input to the eventual AI-agent website-analysis stage (Section 11's dataset depends heavily on this) |
| **Instagram / social media pages** | For many Iranian SMEs, Instagram is the *primary* online presence, sometimes more active than a website | Moderate | Very broad among Iranian SMEs | Should not be skipped — likely more current than a static company website for many targets |
| **Tehran International Permanent Fairground event/exhibitor archives** | Exhibitor lists per industry trade fair | Moderate–High | Sector-specific, strong signal of scale/budget | Exhibiting at a trade fair is itself a positive company-strength signal |
| **News archives (Tehran Times, IRNA, ILNA, Fars, Persian business press)** | Company mentions, expansion news, leadership changes, financial distress signals | Moderate (varies by outlet and topic) | Uneven, better for larger/more visible companies | Useful for "trigger event" detection (Section 5) — expansions, new factories, leadership changes |

**[Assumption]** No single source will be comprehensive. The realistic methodology is: (1) use ISIPO industrial-estate registries and chamber-of-commerce sector committees to build an initial seed list of formal, scaled companies per target industry; (2) cross-reference against Google Maps and Instagram/websites for digital-maturity signal collection; (3) use job-board postings as an ongoing signal feed; (4) use trade-fair exhibitor archives to validate company strength and discover companies missed elsewhere.

---

## 11. Dataset Schema (Future Master Company Database)

| Field | Type | Notes |
|---|---|---|
| Company Name (Persian) | Text | |
| Company Name (English/Latin transliteration) | Text | |
| Website | URL | |
| Industry | Category | From taxonomy in Section 2 |
| Sub-industry | Category | Free-text sub-tag |
| Description | Text | Short, from website/public sources |
| Address | Text | |
| Tehran District / Area | Category | e.g., specific industrial estate name if applicable |
| Google Maps Listing URL | URL | |
| Phone | Text | |
| Public Email | Text | |
| LinkedIn URL | URL | |
| Instagram / Other Social URL | URL | Often the primary online presence — do not treat as secondary |
| Approximate Employee Count | Number/Range | From job postings, LinkedIn, or estimation |
| Approximate Company Size (Small/Mid/Large) | Category | Derived field |
| Number of Locations | Number | |
| Company Age (years) | Number | |
| Products / Services | Text | |
| Customer Type (B2B / B2C / Mixed) | Category | |
| Digital Maturity Score (0–100, banded) | Number | Per Section 8 methodology |
| Company Strength Score (0–100) | Number | |
| AI Opportunity Score (0–100) | Number | |
| Internal Tech Capability Score (0–100, inverted) | Number | |
| Estimated B2B Opportunity Score (0–100) | Number | Composite, per Section 8 formula |
| Potential Workflow Problems | Text (list) | Inferred from public evidence |
| Suggested AI Solutions | Text (list) | Mapped from Section 6 |
| Likely Decision Maker (Role) | Text | Per Section 7 |
| Decision Maker Name (if public) | Text | Only if publicly available — do not scrape private data |
| Evidence / Sources | Text (list of URLs/citations) | Critical for the "verified vs. inferred" distinction required for credible AI-generated proposals |
| Confidence Level (Verified/Estimate/Inferred) | Category | Applied per-field where possible, not just per-record |
| Trade Association / Chamber Membership | Text | e.g., TCCIMA member, ISIPO estate occupant |
| Research Date | Date | |
| Outreach Status | Category | Not contacted / Contacted / In discussion / Won / Lost |

**[Assumption] Recommended additional fields:**
- **Currency/pricing sensitivity flag** — whether the business model is highly exposed to exchange-rate volatility (affects timing of outreach and framing of ROI in cost-savings vs. revenue-growth terms).
- **Primary communication channel observed** (WhatsApp/Telegram/phone/email) — directly informs which AI product to lead with in outreach.
- **Existing software stack (if identifiable)** — named ERP/CRM/accounting system, to flag integration complexity early.
- **Trigger event log** — a running list of detected news/signals (new branch, new hire spree, leadership change) with dates, to time outreach.

---

## 12. Recommended Acquisition Strategy

**Stage 1 — Market research (this document).** Establish which industries and ICPs to pursue and why. *Status: complete.*

**Stage 2 — Company discovery.** Using Section 10's sources — starting with TCCIMA/ICCIMA sector committees and ISIPO industrial-estate registries as the highest-reliability seed lists — build an initial list of 200–500 candidate companies across the top 5–8 priority segments (Section 3). Prioritize completeness of contact information (website, phone, decision-maker name if public) over volume at this stage.

**Stage 3 — Automated qualification.** Score each company using the Section 8 model, populated from Section 9's public signals. This will require both English- and Persian-language data collection (websites, Instagram, job postings) — **[Assumption]** Persian-language sources will often carry more signal than English ones for this specific market, so qualification tooling should be built Persian-first, not Persian-as-an-afterthought.

**Stage 4 — Website/public-data analysis.** For each qualified company (score ≥55), run a deeper AI-assisted analysis of their public footprint to produce the specific, evidence-grounded outputs described in the brief: what they do, how operations probably work, which workflows are likely inefficient, and which claims are evidence-based versus inferred. **Critically, this stage must preserve the verified/estimated/inferred distinction at the company level** — an AI-generated "we noticed you're using X" claim that turns out to be wrong will destroy credibility on first contact, which is a bigger risk in a relationship-driven market like Iran's than in a colder Western B2B market.

**Stage 5 — AI opportunity detection.** Map each qualified company's likely pain points to a specific proposed LUMA product using Section 6's workflow map, tailored with whatever company-specific evidence Stage 4 produced.

**Stage 6 — Personalized proposal generation.** Draft a short, specific proposal per company: what LUMA noticed, why it matters, what could be built, and an estimated (clearly labeled as estimated) impact. Keep it short — one page, concrete, no generic "AI can transform your business" language, consistent with the research standard set for this report itself.

**Stage 7 — Human review.** Every AI-generated proposal should be reviewed by a LUMA team member before outreach, both to catch factual errors and — importantly in the Iranian business context — to adjust tone and approach for relationship-based selling norms (a purely automated, impersonal outreach message is likely to underperform relative to one that references a real, warm introduction path such as a shared chamber-of-commerce membership or industrial-estate connection).

**Stage 8 — Outreach.** Favor warm paths first: chamber-of-commerce and industrial-estate association connections, trade-fair encounters, and referrals from Stage-1-priority-segment reference clients, before cold outreach. Given the short decision chains in ICP-A and much of ICP-B, a direct, in-person or phone conversation with the owner/MD — backed by the one-page proposal — will likely outperform a purely digital funnel.

**A closing strategic note:** LUMA's most durable competitive advantage in this market is not "we can build AI" — plenty of global tools claim that. It is that **LUMA is a domestic provider that can operate reliably under Iran's sanctions-constrained infrastructure environment while foreign AI SaaS vendors functionally cannot serve this market at all.** Every proposal and every piece of positioning should lean into that: LUMA isn't competing against ChatGPT-based tools that Tehran companies could theoretically subscribe to — for practical purposes, in 2026, most of them can't. LUMA is the accessible option.
