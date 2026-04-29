# LaundryMS — Developer Phase Plan
**App:** `laundryms` | **Module:** `LaundryMS` | **Stack:** Frappe v15 + ERPNext v15
**Patching pattern:** csf_tz (README.md)

---

## Read This Before Touching Any Phase

### The One Rule
**Use what ERPNext 15 already provides before writing a single line of custom code.**

This is not a preference. It is the architecture. ERPNext ships with a complete accounting engine, a layered pricing and discount system, a Contract DocType, a website and customer portal, BOM-based inventory deduction, SLA tracking, and a purchase/expense module. None of these are rebuilt in this app. They are configured.

Custom code is written only when ERPNext has no equivalent. After exhausting all ERPNext capabilities, exactly **8 custom DocTypes** are needed. Everything else is ERPNext configuration.

Before writing any code, ask: *does ERPNext already do this?* If the answer is yes, configure it. If you are unsure, check the ERPNext docs before writing anything.

### Configure vs Code — The Decision

| If you are... | Then you are... | Lives in... |
|---|---|---|
| Setting up Items, Price Lists, BOMs, Customer Groups, Warehouses | **Configuring** | ERPNext database — document this as a setup step |
| Adding a field to a standard ERPNext DocType (Sales Order, Customer, Contract) | **Patching** | `patches/custom_fields/custom_fields_json/` |
| Changing behaviour of an existing standard field (make it mandatory, change label) | **Patching** | `patches/property_setter/property_setter_json/` |
| Creating a new DocType that ERPNext has no equivalent of | **Coding** | `laundryms/doctype/` |
| Creating roles, Payment Terms records, seed data — once only | **Seeding** | `patches/setup_data/` + `patches.txt` |
| Writing business logic that fires on a DocType event | **Coding** | Python controller on that DocType |

### What Has Been Deliberately Removed
The following features were considered and explicitly cut. Do not add them back without a decision from the project owner.

- Pickup and delivery service (no drivers, no routing)
- WhatsApp and SMS notifications
- Barcode and RFID garment tagging
- TRA/VFD tax device integration (system is country-agnostic)
- Power Outage Log (lower priority, may be added later)

### Garment Tracking Without Barcodes — The Approach
Barcodes have been removed. This is not an oversight. The system tracks garments using two things:

1. **Description on Sales Order Item** — quantity, colour, type, and care notes. Example: *"2x White Shirt, 1 has button missing on cuff — pre-noted on Condition Check"*
2. **Count verification at each workflow stage** — staff confirm the item count going in matches the count coming out. Any discrepancy holds the order until resolved.

The `item_stage` custom field on Sales Order Item (Select: Pending / Washing / Drying / Ironing / Packed / Collected) gives staff per-item visibility without a scanner. For institutional linen, each Linen Inward batch gets a sequential number (e.g. `INWARD-HOTEL-XYZ-0042`) printed on a plain paper label. No scanner hardware required.

This mirrors how Tanzanian laundry shops already operate. The ERP adds discipline to the count step and creates a digital record — it does not change the physical process.

### The Two Institutional Billing Modes — Read Carefully
This is the most complex part of the system. Hotels and hospitals operate in one of two fundamentally different modes. Getting the data model wrong here breaks invoicing.

**Mode 1 — Guest Direct (Pass-Through Billing)**
The hotel sends a guest's *personal* laundry. The guest pays, not the hotel.
- The **Customer on the Sales Order is the individual guest** — not the hotel.
- The hotel is recorded only in the `referring_hotel` custom field on the Sales Order.
- The Sales Invoice goes to the guest. The hotel forwards it to the room bill.
- The `referring_hotel` field is for reporting only — it produces the monthly guest-charges-by-hotel statement.

**Mode 2 — Hotel Account (Outsourcing)**
Laundry is included in the room rate. The hotel pays, guests pay nothing.
- The **Customer on the Sales Order is the hotel or hospital** — never an individual guest.
- Orders are never created by guests. Staff create them from a Linen Inward batch.
- The institution gets one consolidated Sales Invoice per billing cycle.
- A separate Price List per institution holds the negotiated rates.

The `billing_mode` field (Select: `Guest Direct / Hotel Account`) lives on both the Customer record and is mirrored to each Sales Order. When `billing_mode = Hotel Account`, the Sales Order customer must belong to the Institutional customer group — enforced in the controller.

### Known Discrepancy in Source Document
The architecture document (safisha_v3.docx) lists **7 custom DocTypes** in the narrative section but **8** in the summary table. The discrepancy is `Laundry Job` — it appears in the table but not in the "Custom DocTypes — What Must Be Built" list. It is also described as "ERPNext Work Order (adapted)" in the DocType reference.

**Decision for this build:** Laundry Job is built as a **new custom Standard DocType**. ERPNext's Work Order is manufacturing-oriented (BOM-driven production orders) and does not map cleanly to a machine load of laundry items. The adaptation would require more hacking than building fresh. Total custom DocTypes: **8**.

---

## Phase 0 — App Scaffold
*Developer addition — not in the original architecture document. Required before anything else.*

**Goal:** The `laundryms` Frappe app exists, installs cleanly on a fresh site, and the patching infrastructure is wired and proven with an empty run. Every subsequent phase drops files into this structure.

### What Gets Built
This phase creates the skeleton only. No DocTypes, no business logic, no ERPNext configuration.

**App skeleton via `bench new-app laundryms`:**
```
laundryms/
├── hooks.py
├── patches.txt
├── laundryms/                        ← inner module (same name as app)
│   ├── __init__.py
│   └── doctype/                      ← custom DocTypes go here, one per phase
├── patches/
│   ├── __init__.py
│   ├── custom_fields/
│   │   ├── __init__.py
│   │   └── custom_fields_json/
│   │       └── 01_init.json          ← empty array [] for now
│   ├── property_setter/
│   │   ├── __init__.py
│   │   └── property_setter_json/
│   │       └── 01_init.json          ← empty array [] for now
│   └── setup_data/
│       └── __init__.py
└── utils/
    ├── __init__.py
    ├── create_custom_fields.py       ← exact pattern from README
    └── create_property_setter.py     ← exact pattern from README
```

**hooks.py** — wire both install and migrate to the same two utils:
```python
after_install = [
    "laundryms.utils.create_custom_fields.execute",
    "laundryms.utils.create_property_setter.execute",
]
after_migrate = [
    "laundryms.utils.create_custom_fields.execute",
    "laundryms.utils.create_property_setter.execute",
]
```

**patches.txt** — empty sections, ready for seed data in Phase 1:
```
[pre_model_sync]

[post_model_sync]
```

**utils/create_custom_fields.py** and **utils/create_property_setter.py** — copy exact code from README.md. Do not modify.

### Roles — Seeded Once Here, Used in Every Phase
Roles are one-time data. They go in `patches.txt`, not `after_migrate`.

Create `patches/setup_data/create_roles.py` with these five roles:

| Role | Who it represents |
|---|---|
| `Laundry Manager` | Full access. Sets prices, manages contracts, views all reports, changes settings |
| `Laundry Staff` | Creates and processes orders, condition checks, drying logs, laundry jobs |
| `Cashier` | Creates orders at counter, records payments, issues invoices, applies discounts within limit |
| `Institutional Client` | Portal read-only: their institution's orders and invoices only. Cannot create orders |
| `Retail Customer` | Portal: submits orders via Web Form, views own orders and invoices only |

Add to `patches.txt`:
```
[post_model_sync]
laundryms.patches.setup_data.create_roles
```

### Test Criteria
- `bench install-app laundryms` — zero errors
- `bench migrate` — zero errors, empty JSON files produce nothing
- All five roles exist in ERPNext Role list
- Roles patch does not error on second `bench migrate` (existence check guards it)

---

## Phase 1 — ERPNext Foundation
*Configuration only. Zero custom DocTypes. Zero Python.*

**Goal:** ERPNext is configured as a laundry business. A complete retail Sales Order — from creation through stock deduction to invoice — works using only native ERPNext features. This proves the ERPNext layer before any custom code is written.

### What ERPNext Provides — Nothing to Code Here
Every item in this phase is ERPNext configuration. If you find yourself writing Python for any of these, stop — you are solving a configuration problem with code.

### Step 1 — Company & Accounting
- Create or confirm the Company record with correct currency
- Chart of Accounts: use ERPNext default. Add one income account: `Laundry Revenue` under Income
- Confirm Fiscal Year and Accounting Period
- **Cost Centers:** one per branch (`Main Branch`), one per institutional department (added as needed in Phase 5). This enables P&L by branch without creating separate companies.

### Step 2 — Warehouses
One Warehouse per branch. Start with `Main Store`. Consumable stock is tracked per warehouse — this enables per-branch cost reporting natively.

### Step 3 — Items
**Item Group: `Laundry Services`**

| Item | UOM | Shown on Website |
|---|---|---|
| Wash & Fold | Kg | Yes |
| Express Wash | Kg | Yes |
| Dry Clean | Piece | Yes |
| Iron Only | Piece | Yes |
| Alterations | Piece | Yes |

**Item Group: `Laundry Consumables`**

| Item | UOM | Notes |
|---|---|---|
| Detergent | Gram | Tracked via BOM deduction |
| Fabric Softener | Ml | Tracked via BOM deduction |
| Bleach | Ml | Tracked via BOM deduction |
| Laundry Bag | Piece | |
| Hanger | Piece | |
| Label Roll | Piece | |
| Water | Litre | Also tracked by Water Tank Log (Phase 6) |

Consumable items are **not** shown on the website. Service items are marked `Show in Website` — this makes the website price page live automatically.

### Step 4 — Price Lists
| Price List | Purpose |
|---|---|
| `Standard` | Default. Retail walk-in prices. Website shows this list. |
| `Express` | Same-day service. Higher rate than Standard. |
| `Contract - Placeholder` | One placeholder. Real institution price lists are created per client in Phase 5. |

Enter one **Item Price** record per service item per price list. This is the single source of truth for pricing — the website reads from here, Sales Orders pull from here, nothing needs syncing.

**Discount resolution order in ERPNext (no code needed):**
1. Pricing Rule matched by customer group or item — applied automatically
2. Coupon code entered at checkout — overrides or stacks with Pricing Rule
3. Manual discount entered by staff on the invoice — final override

### Step 5 — Bills of Materials (BOMs)
One BOM per service item. ERPNext auto-deducts these on order submission via Stock Entry. Staff never create Stock Entries manually.

| Service | Consumables per 1 Kg |
|---|---|
| Wash & Fold | 30g Detergent + 10ml Softener |
| Express Wash | 30g Detergent + 10ml Softener + 5ml Bleach |
| Dry Clean | No BOM (define per local process or leave empty) |
| Iron Only | No BOM (electricity is a utility expense, not a stock item) |

### Step 6 — Customer Groups
- `Retail` — walk-in customers. Standard price list assigned at group level.
- `Institutional` — hotels, hospitals, corporates. Contract price list assigned per customer in Phase 5.

A new institutional client added to the `Institutional` group automatically inherits the group-level defaults.

### Step 7 — Stock
- Set Item Reorder levels on all consumables. When stock falls to or below the reorder level, ERPNext triggers a Material Request or Purchase Order automatically.
- Enter opening stock for all consumables in the Main Store warehouse.

### Step 8 — Assets (Machines)
Register each washing machine, dryer, and iron as an ERPNext **Asset**. ERPNext handles depreciation schedules automatically. The Laundry Job DocType (Phase 3) links to Asset — machines must exist before Laundry Jobs can be created.

### Test Criteria
- Create a manual Sales Order: Retail customer, `Wash & Fold 5kg`, Standard price list → correct total
- Submit the Sales Order → Stock Entry auto-created, deducts 150g Detergent + 50ml Softener
- Cancel the Sales Order → Stock Entry auto-reversed
- Update an Item Price → new Sales Order reflects new price immediately
- Stock falls to reorder level → Material Request created automatically

---

## Phase 2 — Laundry Settings
*First custom DocType. Builds the master control switch that every other phase reads from.*

**Goal:** `Laundry Settings` exists as a Single DocType and is the global configuration store for the app. Every phase after this reads defaults from here rather than hardcoding values.

### Why This Must Be a Custom DocType
ERPNext has no concept of a laundry operation mode, a water tank, or a drying method default. These cannot be configured in any native ERPNext DocType — hence a custom Single DocType.

### What Gets Built

**DocType: `Laundry Settings`** — Type: Single (one record, never deleted, never submitted)

| Section | Field | Type | Purpose |
|---|---|---|---|
| **Mode** | `business_mode` | Select: `Business / Institutional` | Master switch. Controls which modules are active and visible. `Business` = retail-only. `Institutional` = enables Linen Inward, Contracts, SLA, consolidated invoicing. |
| **Operations** | `default_drying_method` | Select: `Sun / Machine / Both` | Default applied to every new Sales Order. Staff can override per order. |
| **Operations** | `default_turnaround_hours` | Int | Default SLA hours when no Contract defines a specific turnaround. |
| **Water Tank** | `water_tank_capacity` | Float (litres) | Total capacity of the water tank. Used to calculate fill percentage. |
| **Water Tank** | `water_tank_alert_threshold` | Float (litres) | Level that triggers a low-water warning ToDo for Laundry Manager. |
| **Water Tank** | `water_tank_critical_threshold` | Float (litres) | Level that blocks new Laundry Job creation entirely. Must be less than alert threshold. |
| **Branding** | `company_logo` | Attach Image | Logo used in print formats for invoices and Linen Inward batch labels. |

**Python controller (`laundry_settings.py`):**
- `validate`: `critical_threshold < alert_threshold < water_tank_capacity` — raise ValidationError if not
- No `on_submit` — Single DocTypes have no submit/cancel lifecycle

**Client Script:**
- When `business_mode` is changed to `Business`: hide the Institutional sections of the form (cosmetic only)
- When `business_mode` is changed to `Institutional`: show them
- Server enforces mode constraints — the client script is UI convenience only

**Role Permissions:**

| Role | Permission |
|---|---|
| Laundry Manager | Read + Write |
| Laundry Staff | Read only |
| Cashier | Read only |

### Patching
Laundry Settings is a custom DocType — it lives in `laundryms/doctype/laundry_settings/`. It is not a custom field on a standard DocType, so it does not go through the custom fields JSON. The DocType JSON and controller go directly in the app.

### Test Criteria
- `Laundry Settings` form opens from the LaundryMS module
- Save with valid values → saves cleanly
- Save with `critical_threshold` > `alert_threshold` → ValidationError raised, save blocked
- `Laundry Staff` opens the form → read-only, no save button
- `business_mode = Business` → Institutional sections hidden in UI

---

## Phase 3 — Order Lifecycle
*The core of the system. Five DocTypes built. ERPNext Workflow configured.*

**Goal:** A complete laundry order can be created at the counter or online, processed through every workflow stage, and reach Collected status. The garment tracking approach (description + count, no barcodes) is enforced by the system.

### What ERPNext Provides — Configure, Not Code
- **Sales Order** — already exists. Extended with custom fields via the patching system.
- **Sales Order Item** — already exists. Extended with custom fields.
- **Workflow Builder** — configured in the ERPNext UI. No Python for stage transitions.
- **Stock Entry** — auto-created by ERPNext when BOM consumables are deducted. Staff never create these.

### Custom Fields Added to Standard DocTypes
These go in `patches/custom_fields/custom_fields_json/`. They are not new DocTypes — they extend existing ones.

**File: `02_sales_order.json`** — fields added to Sales Order:

| Fieldname | Type | Purpose |
|---|---|---|
| `drying_method` | Select: `Sun / Machine / Both` | Defaults from `Laundry Settings.default_drying_method` on new order. Staff can change. |
| `total_weight_kg` | Float | Recorded at the Received stage when items are physically weighed. Mandatory before moving to Washing. |
| `billing_mode` | Select: `Guest Direct / Hotel Account` | Mirrors the Customer's billing_mode. Determines invoicing path. Only visible when customer is Institutional group. |
| `referring_hotel` | Link → Customer | Mode 1 only. Records which hotel sent the guest's laundry. Used for reporting — not for invoicing. |
| `sla_deadline` | Datetime | Auto-calculated on Confirmed: `confirmed_at + Laundry Settings.default_turnaround_hours` (or Contract turnaround if institutional). Read-only. |
| `order_stage` | Select (mirrors workflow) | Read-only. Displayed in list view for quick filtering. Set by the workflow controller. |

**File: `03_sales_order_item.json`** — fields added to Sales Order Item:

| Fieldname | Type | Purpose |
|---|---|---|
| `ironing_flag` | Check | If ticked, this item line goes through the Ironing stage. Orders with no ironing_flag ticked skip Ironing entirely. |
| `care_notes` | Small Text | Staff notes on special care instructions for this item. Printed on the order slip. |
| `item_stage` | Select: `Pending / Washing / Drying / Ironing / Packed / Collected` | Per-item tracking. Staff update as each garment type moves through the process. This is the no-barcode tracking mechanism. |

### DocType 1: `Garment Condition Check` — Custom Child of Sales Order

**Why it exists:** Physical goods inspection before service begins. There is no equivalent in ERPNext — Sales Order has no intake damage documentation concept.

| Field | Type | Purpose |
|---|---|---|
| `sales_order_item` | Link → Sales Order Item | Which item line this damage applies to |
| `damage_type` | Select: `Stain / Tear / Missing Button / Colour Fade / Pre-existing Wear / Other` | Category of damage |
| `description` | Small Text | Staff describes the damage in plain language |
| `acknowledged_by_customer` | Check | Staff confirms the customer has seen and accepted the pre-existing damage note |

**Enforcement rule (Python controller on Sales Order):**
When transitioning to `Confirmed` stage — the `Garment Condition Check` child table must either:
- Have at least one row with `acknowledged_by_customer = 1`, OR
- Have zero rows **and** the order has a note confirming "no damage found"

The transition is blocked until this is satisfied. This cannot be configured in the Workflow Builder — it requires a Python `before_save` or `validate` check.

### DocType 2: `Sun Drying Log` — Custom Standard

**Why it exists:** ERPNext has no outdoor drying workflow concept. The Water Tank Log tracks physical water level; the Sun Drying Log tracks physical outdoor drying time.

| Field | Type | Purpose |
|---|---|---|
| `sales_order` | Link → Sales Order | Which order's items are drying outside |
| `time_out` | Datetime | When items were hung outside |
| `time_in` | Datetime | When items were brought in (blank = still outside) |
| `weather_note` | Select: `Clear / Cloudy / Light Rain / Strong Wind / Other` | Staff records conditions at time of hanging |
| `staff_member` | Link → Employee | Who hung the items |
| `alert_sent` | Check | System flag — has the overtime alert already fired for this session? Set to 1 after first alert to prevent repeat notifications. |

**Scheduled job (every 15 minutes, wired in hooks.py):**
Find all Sun Drying Logs where `time_in` is blank and `time_out` is older than `Laundry Settings.default_turnaround_hours` → create a ToDo for Laundry Manager + set `alert_sent = 1`. The `alert_sent` flag prevents the same log from generating multiple ToDos.

**Workflow gate:** When `drying_method = Sun`, the Drying stage cannot be completed until a linked Sun Drying Log with a `time_in` value exists.

### DocType 3: `Laundry Job` — Custom Standard

**Why it exists:** One machine load groups multiple Sales Order items. ERPNext's Work Order is manufacturing-oriented (produce a finished item from a BOM) and does not fit this use case. Built fresh.

**Note on Assets:** Each washing machine is already registered as an ERPNext Asset in Phase 1. The `machine` field links to that Asset record.

| Field | Type | Purpose |
|---|---|---|
| `machine` | Link → Asset | The washing machine being loaded (Asset registered in Phase 1) |
| `load_items` | Table → Laundry Job Item (child) | One row per Sales Order Item in this load |
| `total_load_kg` | Float | Sum of weights in this load. Must not exceed machine capacity. |
| `start_time` | Datetime | When the machine started |
| `end_time` | Datetime | When the machine finished |
| `status` | Select: `Queued / Running / Done` | |

**Child: `Laundry Job Item`** — one row per Sales Order Item in this load:

| Field | Type |
|---|---|
| `sales_order` | Link → Sales Order |
| `sales_order_item` | Link → Sales Order Item |
| `weight_kg` | Float |

**Blocker (added in Phase 6 after Water Tank Log exists):** Laundry Job creation is blocked if `Water Tank Log.status = Critical` for the relevant branch warehouse.

### ERPNext Workflow — Configured in Workflow Builder (No Python for Transitions)

The Workflow Builder in ERPNext v15 handles all stage transitions visually. Python is only written for the *business logic triggered at a stage* — not for the transition itself.

| Stage | Acted by | Business logic (Python) |
|---|---|---|
| Draft | Cashier / Portal user | Order created at counter or via website Web Form |
| Confirmed | Cashier | **Garment Condition Check completeness validated.** `sla_deadline` auto-calculated and set. |
| Received | Cashier | `total_weight_kg` becomes mandatory. Physical items counted against order lines. |
| Washing | Laundry Staff | **Laundry Job must be linked.** BOM Stock Entry fires (ERPNext native). |
| Drying | Laundry Staff | If `drying_method = Sun`: Sun Drying Log must be created and linked. |
| Ironing | Ironing Staff | Only reachable if at least one `ironing_flag = 1` on the order items. Bypassed entirely if none. |
| Folding & Packing | Laundry Staff | Item count verified against intake. Any discrepancy creates a hold ToDo. |
| Ready | System (auto) | Status set automatically. Customer sees "Ready" in portal. Cashier gets a ToDo to contact customer. |
| Collected | Cashier | Final stage for retail orders. |
| Invoiced | Cashier / System | Sales Invoice created. Retail: per order. Institutional: deferred to billing cycle (Phase 5). |

### Test Criteria
- New order defaults `drying_method` from `Laundry Settings`
- Cannot reach `Confirmed` without a completed `Garment Condition Check` row
- Reaching `Washing` → BOM Stock Entry fires, consumables deducted
- Order with `drying_method = Sun` → cannot advance past Drying without a Sun Drying Log with `time_in` set
- Order with no `ironing_flag` items → Ironing stage skipped in workflow
- `item_stage` field on Sales Order Items updates correctly as each stage is reached
- Sun Drying alert ToDo created when a log is open past the threshold (trigger manually in test)

---

## Phase 4 — Pricing, Discounts & Payments
*ERPNext native configuration. Zero custom code.*

**Goal:** All pricing models work. Discounts apply automatically. Retail invoices are correct. Institutional consolidated invoicing is proven. Payment modes are set up.

### What ERPNext Provides — Configure, Not Code
Every item in this phase is native ERPNext. No Python, no custom DocTypes.

### Pricing Rules
Configure in ERPNext → Pricing Rule:

| Rule | Trigger | Effect |
|---|---|---|
| Customer group discount | Customer group = `Institutional` | Use their assigned Price List — not a Pricing Rule, handled by Price List assignment on Customer |
| Bulk discount | Item group = `Laundry Services`, qty > 10 Kg | 5% discount applied automatically |
| First order promotion | Customer has 0 prior Sales Orders | 10% discount — or use a Coupon Code for simplicity |
| Free bag | Item group = `Laundry Services`, 10th order | Free item: `Laundry Bag x 1` added automatically |

### Coupon Codes
ERPNext has a native Coupon Code DocType. Create 3 test codes, each linked to a Pricing Rule. The cashier enters the code in the Sales Order — discount fires automatically. No custom code needed.

### Payment Terms Templates
Configure three templates in ERPNext:

| Template | Used for |
|---|---|
| `Net 30` | Hotels billed monthly |
| `End of Month` | Hospitals billed at month end |
| `Per Batch` | Institutions billed per Linen Inward delivery |

Assign the correct template to each institutional Customer record. This controls when their consolidated invoice is due and triggers Dunning automatically if payment is late.

### Payment Modes
Configure as manual payment modes in ERPNext → Mode of Payment:
- Cash
- Card
- Mobile Money (M-Pesa, Tigopesa, or similar — name per local context)

### Consolidated Invoicing for Institutional Clients
ERPNext's native "Create Invoice from Multiple Sales Orders" handles this. No custom code.
The process (documented as a staff procedure):
1. Filter delivered Sales Orders by institution and billing period
2. Select all → Actions → Create Invoice
3. ERPNext groups them into one consolidated Sales Invoice
4. Apply any SLA penalty deductions (added in Phase 5)

### Dunning Configuration
Configure Dunning in ERPNext for overdue institutional invoices:
- Level 1: 7 days overdue — reminder notice, no charge
- Level 2: 14 days overdue — second notice + dunning fee
- Level 3: 30 days overdue — final notice + escalated fee

ERPNext Dunning fires automatically based on Payment Terms due date. No code needed.

### Test Criteria
- Retail order 5kg Wash & Fold → correct total from Item Price
- Order over 10kg → 5% Pricing Rule fires automatically, no manual action
- Coupon code entered in Sales Order → discount applies
- Manual discount entered by cashier → overrides rule
- Two Sales Orders for same institution → consolidated into one Sales Invoice using native ERPNext function
- Payment Terms due date passes → Dunning triggers

---

## Phase 5 — Institutional Module
*The most complex phase. Three new custom DocTypes. One Python function for penalty calculation.*

**Goal:** Hotels and hospitals are fully onboarded. Both billing modes produce correct invoices. Linen arrives via Linen Inward, auto-creates Sales Orders, and processes through the full workflow. SLA breaches generate penalty deductions on consolidated invoices.

### What ERPNext Provides — Configure, Not Code
- **Contract** — native ERPNext DocType. Extended with custom fields.
- **Service Level Agreement** — native ERPNext Support module. Linked to Customer. ERPNext marks overdue orders `SLA Breached` automatically.
- **Subscription** — native ERPNext. Used for fixed-retainer institutional clients.
- **Customer Portal** — native Frappe. Institutional clients read their own orders and invoices.

### Custom Fields Added to Standard DocTypes

**File: `04_customer.json`** — fields on Customer:

| Fieldname | Type | Purpose |
|---|---|---|
| `billing_mode` | Select: `Guest Direct / Hotel Account` | Determines which invoicing path applies to this institution |
| `contract_price_list` | Link → Price List | The institution's negotiated price list, created specifically for them |
| `preferred_billing_cycle` | Select: `Monthly / Fortnightly / Per Batch` | |

**File: `05_contract.json`** — fields on Contract:

| Fieldname | Type | Purpose |
|---|---|---|
| `turnaround_hours` | Int | Maximum hours before an order is considered SLA breached |
| `penalty_rate_per_hour` | Currency | Deducted per hour overdue on breached orders |
| `billing_cycle` | Select: `Monthly / Fortnightly / Per Batch` | |
| `billing_mode` | Select: `Guest Direct / Hotel Account` | Must match the Customer's billing_mode |

### Service Level Agreement Setup
For each institutional client:
1. Create an SLA record in ERPNext (Support → Service Level Agreement)
2. Set `Resolution Time = Contract.turnaround_hours` for that institution
3. Link to the institution's Customer record

ERPNext then automatically marks any Sales Order past its deadline as `SLA Breached`. This is a standard ERPNext field — no custom code needed to set it.

### DocType 4: `Linen Inward` — Custom Standard

**Why it exists:** ERPNext has no "inward batch receipt for service" concept. A Sales Order is created for something the business will sell — not for a batch of goods arriving for processing. This DocType is the point of accountability for what arrives from an institution.

| Field | Type | Purpose |
|---|---|---|
| `institution` | Link → Customer | Must be Institutional customer group — validated in controller |
| `department` | Link → Cost Center | Which department sent the batch (enables charge-back reporting) |
| `receiving_date` | Date | |
| `bag_count` | Int | Physical bags received |
| `estimated_weight_kg` | Float | Weighed at intake |
| `receiving_staff` | Link → Employee | Who accepted the batch |
| `batch_number` | Data | Auto-generated: `INWARD-{INSTITUTION_ABBREV}-{NNNN}`. Printed on the batch label. Read-only. |
| `linked_sales_order` | Link → Sales Order | Auto-set by controller on submit. Read-only. |
| `linen_items` | Table → Linen Inward Item | Child table — one row per linen type |

**Python controller (`linen_inward.py`):**

`before_submit`:
- Validate `institution` belongs to `Institutional` customer group
- Validate `bag_count > 0`
- Generate `batch_number` using ERPNext naming series

`on_submit`:
- Auto-create a Sales Order against the institution's Customer record
- Set Price List to `Customer.contract_price_list`
- Set `Sales Order.billing_mode` from `Customer.billing_mode`
- Set `Sales Order.sla_deadline` from `Contract.turnaround_hours`
- Set Sales Order status to `Received` (skip Draft and Confirmed — batch receipt is the confirmation)
- Write the new Sales Order name back to `linked_sales_order`

`on_cancel`:
- Cancel `linked_sales_order` only if its status is still `Received` (not yet processed)
- If already in Washing or beyond — raise an error: cannot cancel an in-progress order

### DocType 5: `Linen Inward Item` — Custom Child of Linen Inward

| Field | Type | Purpose |
|---|---|---|
| `item` | Link → Item | Linen type (Bed Sheet, Pillow Case, Bath Towel, Scrub Top, etc.) |
| `quantity` | Int | |
| `notes` | Small Text | Condition notes at receipt — stains, tears noted here for return comparison |

### SLA Penalty Calculation — The One Custom Function in This Phase
This is a Python function called at consolidated invoice creation time. It is not a scheduled job.

**Logic:**
```
For each SLA-breached Sales Order in the billing period for this institution:
    hours_overdue = (now - sla_deadline) in hours
    penalty = hours_overdue × Contract.penalty_rate_per_hour

total_penalty = sum of all penalty amounts

Add to consolidated Sales Invoice:
    One negative line item per breached order
    Label: "SLA Breach Deduction — Order [SO-XXXX], [Y] hours overdue"
    Amount: -penalty (negative, reduces the invoice total)
```

**Where it lives:** A Python function on the Sales Invoice controller, triggered when the invoice is created from multiple Sales Orders for an institutional customer.

**Inputs available at that point:** ERPNext's native `SLA Breached` checkbox + `sla_deadline` field on Sales Order; `Contract.penalty_rate_per_hour` fetched from the institution's Contract.

### Mode 1 Setup (Guest Direct)
- Create retail Customer records for individual hotel guests (or a generic "Hotel Guest" placeholder if the guest is not registered)
- Set `Sales Order.billing_mode = Guest Direct`
- Set `Sales Order.referring_hotel = [the hotel's Customer record]`
- Invoice goes to the guest Customer
- The Guest Charges by Hotel report (Phase 8) groups these by `referring_hotel`

### Mode 2 Setup (Hotel Account)
- Institution's Customer record has `billing_mode = Hotel Account`
- Dedicated Price List per institution (e.g. `Grand Hotel Contract`)
- All orders created via Linen Inward only — never directly
- Consolidated invoice at billing cycle end using ERPNext's native multi-SO invoicing

### Subscription — Fixed Retainer Contracts
For institutions on a fixed monthly fee: configure ERPNext Subscription linked to their Customer record. ERPNext auto-generates a Sales Invoice at cycle end for the contracted minimum volume. No custom code.

### Test Criteria
- Submit Linen Inward → Sales Order auto-created at institution's contract price, status = Received
- Mode 1: guest Sales Order has correct Customer (guest) and `referring_hotel` (hotel)
- Mode 2: Sales Order Customer is the institution itself
- SLA deadline passes on a test order → `SLA Breached` set by ERPNext
- Generate consolidated invoice for institution → SLA penalty deduction appears as negative line item with correct label and calculated amount
- Cancel Linen Inward before processing → linked Sales Order cancelled
- Cancel Linen Inward after washing started → blocked with error

---

## Phase 6 — Water Management
*Two custom DocTypes. One scheduled job. One blocker added to Laundry Job.*

**Goal:** Water tank levels are tracked. Alerts fire at configurable thresholds. A water delivery updates the tank and auto-creates the expense entry. Critically low tank blocks new wash jobs.

### Why These Cannot Use ERPNext Inventory
ERPNext's stock system tracks consumable **items** in a **warehouse** — quantities that arrive via Purchase Invoice and are consumed via BOM deduction. It does not track the current fill level of a physical tank. A tank has a capacity, a current level, and a status — these require a dedicated DocType.

### DocType 6: `Water Tank Log` — Custom Standard

One record per branch. This is a running state record, not a transaction log.

| Field | Type | Purpose |
|---|---|---|
| `branch` | Link → Warehouse | One tank per branch warehouse |
| `current_level_litres` | Float | Current fill level. Updated by Water Purchase on submit. |
| `last_refill_date` | Date | Auto-set when a Water Purchase is submitted for this tank |
| `last_checked_by` | Link → Employee | Staff who physically verified the level |
| `status` | Select: `OK / Low / Critical` | Auto-calculated by scheduled job. Read-only — never set manually. |

**Status logic (set by scheduled job every hour):**
- `current_level_litres > Laundry Settings.water_tank_alert_threshold` → `OK`
- `≤ alert_threshold` and `> critical_threshold` → `Low`
- `≤ critical_threshold` → `Critical`

**Scheduled job (`check_tank_levels`, every hour, wired in hooks.py):**
For each Water Tank Log:
1. Recalculate and set `status`
2. If status changed to `Critical` → create ToDo for Laundry Manager: "Water tank critically low at [branch]. Block on new wash jobs is active."
3. If status changed to `Low` → create ToDo for Laundry Staff: "Water tank low at [branch]. Schedule a water delivery."

### DocType 7: `Water Purchase` — Custom Standard

**Why it exists:** A Purchase Invoice records the cost of a water delivery. But it cannot also update the Water Tank Log fill level. That link — delivery → tank level update + expense entry — requires a custom DocType with a controller.

| Field | Type | Purpose |
|---|---|---|
| `vendor` | Link → Supplier | Water delivery vendor |
| `water_tank_log` | Link → Water Tank Log | Which tank is being filled |
| `litres_delivered` | Float | |
| `cost` | Currency | |
| `delivery_date` | Date | |
| `journal_entry` | Link → Journal Entry | Auto-created on submit. Read-only. |

**Python controller (`water_purchase.py`):**

`on_submit`:
1. Fetch linked `Water Tank Log`
2. `new_level = current_level_litres + litres_delivered`
3. Cap at `Laundry Settings.water_tank_capacity` — tank cannot overflow
4. Set `Water Tank Log.current_level_litres = new_level`
5. Set `Water Tank Log.last_refill_date = today`
6. Recalculate `status` immediately (don't wait for the scheduled job)
7. Create a Journal Entry: Debit `Water Expense` account, Credit `Cash / Bank` account, amount = `cost`
8. Save the Journal Entry name back to `journal_entry`

`on_cancel`:
1. Reverse: `Water Tank Log.current_level_litres -= litres_delivered`
2. Recalculate `status`
3. Cancel the linked `journal_entry`

### Laundry Job Blocker — Added Now
Go back to the Laundry Job controller from Phase 3. Add this check in `before_insert`:

```
Fetch Water Tank Log where branch = (branch of the Sales Orders in this job)
If Water Tank Log.status == "Critical":
    Raise ValidationError: "Water tank is critically low at [branch].
    A Water Purchase must be submitted before new wash jobs can start."
```

This completes the connection between Phases 3 and 6.

### Test Criteria
- Submit `Water Purchase` → `Water Tank Log.current_level_litres` increases correctly; Journal Entry created
- Submit two Water Purchases that would overflow → level capped at tank capacity
- Cancel `Water Purchase` → level decreases; Journal Entry cancelled
- Set level to below `critical_threshold` → scheduled job (or manual trigger) sets status to `Critical`; ToDo created for Laundry Manager
- Attempt `Laundry Job` creation when status is `Critical` → blocked with clear error message
- Submit a new Water Purchase → status returns to `OK` → Laundry Job creation succeeds

---

## Phase 7 — Website & Customer Portal
*ERPNext and Frappe native features only. Zero custom code.*

**Goal:** The public website shows live prices from ERPNext. Customers register, submit orders, and track order status in the portal. A price change in the ERP is immediately visible on the website with no export, no sync, and no CMS update.

### Why No Custom Code Is Needed Here
Frappe ships with a full website module, a customer portal, and a Web Form DocType. These are not third-party integrations — they are part of the framework. The data flow is direct:

```
Item Price record in ERP
    → Website Item (flag on the Item DocType)
        → Public price page on the website
```

When a Laundry Manager changes a price in `Item Price`, it is immediately visible on the website. There is no sync step because the website reads directly from the ERPNext database.

### Public Website Configuration
All done in the ERPNext / Frappe UI — no code:

- **Website Settings** (Frappe Single): company name, logo, homepage hero text, footer links, banner text
- **Item → Show in Website**: tick this on all service Items. Add description and a category image.
- **Web Pages** (Frappe DocType): create these static pages:
  - `Services & Prices` — pulls item list from Item Group `Laundry Services` automatically
  - `How It Works` — static content describing the laundry process
  - `Contact Us` — static content with contact details

### Online Order Submission — Web Form
Frappe's Web Form DocType creates a public form linked to Sales Order. Configure (not code):
- Customer selects service type from Item Group `Laundry Services`
- Enters garment counts and quantities
- Selects Standard or Express
- Picks preferred date
- Submits → Sales Order created in `Draft` status for staff to confirm

This is configured in the Frappe Web Form DocType. No Python.

### Customer Portal
Frappe's portal is enabled by adding DocTypes to the Portal Menu (Settings → Portal → Portal Menu):
- Add `Sales Order` → customers see their own orders and real-time status
- Add `Sales Invoice` → customers can download their invoices

The `Portal Users` tab on the Customer form (ERPNext v15 native) links a portal account to a Customer record. When a customer registers on the website, staff link their account to their Customer record here.

**Retail Customer** portal access: submit orders via Web Form, view own orders and invoices.
**Institutional Client** portal access: read-only on their institution's orders and invoices. Cannot create orders (staff create from Linen Inward).

### Test Criteria
- Change a price in `Item Price` → reload the website services page → new price shown immediately (no action taken in between)
- Customer submits order on the website → appears as `Draft` Sales Order in ERPNext, assigned to the correct customer
- Staff advance order to `Ready` → customer logs into portal → sees `Ready` status in real time
- Customer downloads their Sales Invoice PDF from the portal
- Institutional client logs in → sees only their institution's orders, not other customers' data

---

## Phase 8 — Reports & Dashboards
*ERPNext Report Builder + Script Reports where custom logic is needed.*

**Goal:** Management has all key metrics without querying the database manually. Operational reports give staff the information they need during the day.

### Report Types — When to Use Which

| Type | When | Tool |
|---|---|---|
| Query Report | Joins across standard ERPNext DocTypes, no complex logic | ERPNext Query Report (SQL) |
| Script Report | Custom logic needed (penalty calculations, cross-DocType aggregations) | ERPNext Script Report (Python) |

### Reports to Build

| Report | Type | What it shows |
|---|---|---|
| Daily Order Summary | Script | Orders by status, total revenue, average turnaround time — filterable by date and branch |
| Consumables Consumption | Script | Item, quantity consumed, cost per order — reads BOM Stock Entries linked to Sales Orders |
| SLA Breach Report | Script | Orders past deadline, hours overdue, penalty amount calculated from Contract.penalty_rate_per_hour |
| Machine Utilisation | Script | Laundry Jobs per day per machine (Asset), total load kg, idle time percentage |
| Institutional Monthly Summary | Script | One row per institution: orders processed, total weight, total billed amount, penalty deductions |
| Water Usage | Script | Water purchased (from Water Purchase) vs estimated consumed per kg (from BOM Water item) |
| Revenue by Channel | Query | Retail (walk-in), Portal (orders from Web Form), Institutional (from Linen Inward) — split by order source |
| Discount Analysis | Query | Total discount given, broken down by Pricing Rule type and Customer Group |
| Guest Charges by Hotel | Script | Mode 1 only. Groups Guest Direct Sales Orders by `referring_hotel`. The hotel's monthly guest statement. |

### Dashboard
One Frappe Dashboard in the LaundryMS module with number cards:

| Card | Source |
|---|---|
| Orders today (by status) | Sales Order — today's date filter |
| Revenue today | Sales Invoice — today's date |
| Water tank level | Water Tank Log — current_level_litres as % of capacity |
| Open SLA breaches | Sales Order — SLA Breached = 1, status not Collected |
| Overdue institutional invoices | Dunning — count of open Level 1+ Dunning records |

### Test Criteria
- All reports render with real order data — no empty results with data in the system
- SLA Breach Report penalty amounts match the calculation: hours_overdue × Contract.penalty_rate_per_hour
- Discount Analysis totals match the sum of discounts on issued Sales Invoices
- Guest Charges by Hotel shows correct grouping for Mode 1 orders only
- Dashboard cards update without page reload (use Frappe Dashboard auto-refresh setting)
- Dashboard loads in under 3 seconds with 30 days of order data

---

## Full Dependency Map

```
Phase 0 — App Scaffold + Roles
    └── Phase 1 — ERPNext Foundation (Items, BOMs, Price Lists, Warehouses, Assets)
            └── Phase 2 — Laundry Settings (master switch; all other phases read from here)
                    └── Phase 3 — Order Lifecycle (Sales Order extensions, Workflow, 3 custom DocTypes)
                            ├── Phase 4 — Pricing & Payments (ERPNext config; no new DocTypes)
                            │       └── Phase 5 — Institutional Module (3 custom DocTypes + penalty function)
                            └── Phase 6 — Water Management (2 custom DocTypes + Laundry Job blocker)

Phase 7 — Website & Portal (requires Phase 1 for Items; Phase 3 for Sales Order portal)
Phase 8 — Reports (requires all phases above for real data)
```

---

## Custom DocType Inventory — All 8

| # | DocType | Phase | Type | Depends on |
|---|---|---|---|---|
| 1 | `Laundry Settings` | 2 | Single | — |
| 2 | `Garment Condition Check` | 3 | Child → Sales Order | Sales Order (Phase 1) |
| 3 | `Sun Drying Log` | 3 | Standard | Sales Order (Phase 1) |
| 4 | `Laundry Job` | 3 | Standard | Sales Order, Asset/Machine (Phase 1) |
| 5 | `Linen Inward` | 5 | Standard | Customer-Institutional, Cost Center (Phase 1) |
| 6 | `Linen Inward Item` | 5 | Child → Linen Inward | Linen Inward (#5), Item (Phase 1) |
| 7 | `Water Tank Log` | 6 | Standard | Warehouse (Phase 1) |
| 8 | `Water Purchase` | 6 | Standard | Water Tank Log (#7), Supplier (Phase 1) |

---

## Patching Cheat Sheet

| What you are doing | Where it goes | Runs |
|---|---|---|
| New field on a standard ERPNext DocType | `patches/custom_fields/custom_fields_json/NN_name.json` | Every `bench migrate` |
| Change behaviour of an existing standard field | `patches/property_setter/property_setter_json/NN_name.json` | Every `bench migrate` |
| New custom DocType for this app | `laundryms/doctype/doctype_name/` | On install (Frappe auto-registers DocTypes) |
| Roles, Payment Terms, seed records | `patches/setup_data/script_name.py` + `patches.txt` | Once only |
| Scheduled tasks | `hooks.py → scheduler_events` | Per schedule |
| Client Scripts on standard DocTypes | `hooks.py → doctype_js` → `public/js/doctype_name.js` | On page load |

---

*LaundryMS — Developer Phase Plan*
*Architecture source: safisha_v3.docx | Patching pattern: README.md (csf_tz)*
*App: `laundryms` | Module: `LaundryMS` | Stack: Frappe v15 + ERPNext v15*