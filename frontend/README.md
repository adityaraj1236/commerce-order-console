# Commerce Order Console: Frontend

Next.js (App Router) console used by store staff to browse the catalogue, create orders, find
orders and move them through fulfilment. All business rules live in the backend; the frontend
shows what the API returns and gives clear feedback.

Setup and the full run guide are in the [root README](../README.md).

---

## Contents

1. [Quick commands](#quick-commands)
2. [Pages](#pages)
3. [Project layout](#project-layout)
4. [Design system](#design-system)
5. [Base components](#base-components)
6. [Data fetching](#data-fetching)
7. [Utilities](#utilities)
8. [Notable behaviour](#notable-behaviour)
9. [Quality checks](#quality-checks)
10. [Adding a page](#adding-a-page)

---

## Quick commands

```bash
npm install
cp .env.example .env.local        # NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
npm run dev                       # http://localhost:3000
npm run check                     # ESLint + design-token check + TypeScript + Prettier
npm run build && npm run start    # production build
```

| Script                    | What it does                                                                                               |
| ------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `dev`                     | Development server with hot reload                                                                         |
| `build` / `start`         | Production build / serve it                                                                                |
| `lint`                    | ESLint (Next.js + TypeScript rules)                                                                        |
| `lint:tokens`             | Fails on hardcoded colors, lengths, inline styles or utility classes (see [Design system](#design-system)) |
| `typecheck`               | `tsc --noEmit` in strict mode                                                                              |
| `format` / `format:check` | Prettier                                                                                                   |
| `check`                   | Runs `lint`, `lint:tokens`, `typecheck` and `format:check`                                                 |

---

## Pages

| Route               | Page         | What staff can do                                                                       |
| ------------------- | ------------ | --------------------------------------------------------------------------------------- |
| `/`                 |              | Redirects to `/dashboard`                                                               |
| `/dashboard`        | Dashboard    | See order counts by status and stock counts; each card opens the matching filtered list |
| `/products`         | Products     | Browse every product with SKU, description, price, available units and stock badge      |
| `/orders/new`       | Create Order | Search the catalogue, build a cart, see line totals and the total, place the order      |
| `/orders`           | Orders       | Search by reference, filter by status, page through results, open an order              |
| `/orders/[orderId]` | Order detail | See items and totals, mark as packed / shipped, cancel with confirmation                |

Every page handles loading (skeletons), empty results and errors (with a _Try again_ button).

---

## Project layout

```
src/
├── app/                          Routes only (thin files that render a page component)
│   ├── theme.css                 All design tokens
│   ├── globals.css               Tailwind import, resets, base element styles
│   ├── layout.tsx                Font, <html>/<body>, providers
│   ├── providers.tsx             TanStack Query client + toast provider
│   ├── page.tsx                  Redirect to /dashboard
│   └── (console)/                Route group: every page inside the sidebar shell
│       ├── layout.tsx
│       ├── dashboard/page.tsx
│       ├── products/page.tsx
│       └── orders/  page.tsx, new/page.tsx, [orderId]/page.tsx
├── components/
│   ├── base_components/          Reusable UI primitives + base_components.css
│   └── global_components/        AppShell, Sidebar, PageHeader, ProductIdentity, navigation.ts
├── page_components/              One folder per page: its components and its own CSS
│   ├── dashboard_page/
│   ├── products_page/
│   ├── create_order_page/
│   ├── orders_page/
│   └── order_detail_page/
├── hooks/                        TanStack Query hooks and the cart hook
├── lib/api/                      HTTP client and one module per backend feature
├── types/                        TypeScript types mirroring the API schemas
└── utils/                        Money, dates, labels, class names, error messages
scripts/check-design-tokens.mjs   The lint:tokens checker
```

---

## Design system

All visual values are defined once in [`src/app/theme.css`](src/app/theme.css) and used
everywhere through `var(--token)`.

**Theme.** Navy primary (`#0f2a44`) with an indigo accent, slate neutrals, Plus Jakarta Sans.

| Token group             | Examples                                                                                                                 |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Colors                  | `--color-primary`, `--color-text-secondary`, `--color-border`, `--color-danger`                                          |
| Order status colors     | `--color-status-placed` (blue), `-packed` (amber), `-shipped` (green), `-cancelled` (red), each with `-text` and `-soft` |
| Stock colors            | `--color-stock-in`, `--color-stock-low`, `--color-stock-out`                                                             |
| Typography              | `--text-h1` … `--text-h3` (fluid), `--text-display`, `--text-body`, `--text-caption`, `--font-weight-*`                  |
| Spacing                 | `--space-4` … `--space-64` (name = pixel size), `--space-page-padding`, `--space-section-gap` (fluid)                    |
| Shape                   | `--radius-xs` … `--radius-pill`, `--shadow-sm` … `--shadow-xl`, `--border-width-*`                                       |
| Sizes                   | `--size-control-md`, `--size-sidebar`, `--size-content-max`, `--size-dialog`, …                                          |
| Motion, focus, stacking | `--motion-fast`, `--focus-ring`, `--z-modal`, `--z-toast`                                                                |
| Breakpoints             | `--breakpoint-tablet` (40rem), `--breakpoint-desktop` (64rem)                                                            |

**Rules** (checked by `npm run lint:tokens`):

1. Only `theme.css` may contain raw colors (`#hex`, `rgb()`, `hsl()`) or lengths (`px`, `rem`, `em`).
2. Components use **semantic class names** (`button button-primary`, `order-table-row`) styled
   in CSS files. No Tailwind utility class strings and no inline `style={{}}` in TSX.
3. Responsive rules use `@variant tablet { … }` / `@variant desktop { … }` inside a rule, so
   breakpoints also come from `theme.css`.
4. One component per concept: one `Button`, one `StatusBadge`, one money formatter. Styles and
   formatting logic are never duplicated.

Where styles live:

| File                                                 | Contents                                                                            |
| ---------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `app/globals.css`                                    | Resets, body and heading styles, focus ring, `.visually-hidden`, `.tabular-figures` |
| `components/base_components/base_components.css`     | Every base component                                                                |
| `components/global_components/global_components.css` | Shell, sidebar, page header, product identity                                       |
| `page_components/<page>/<page>.css`                  | Page-specific layout only                                                           |

---

## Base components

`src/components/base_components/`

| Component                                                            | Key props                                                                                                                      | Used for                                                                    |
| -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------- |
| `Button`                                                             | `variant` (`primary` \| `secondary` \| `ghost` \| `danger`), `size` (`sm` \| `md`), `icon`, `loading`, `fullWidth`, `iconOnly` | Every action                                                                |
| `ButtonLink`                                                         | `href`, `variant`, `size`, `icon`                                                                                              | Navigation that looks like a button                                         |
| `Input`                                                              | `icon`, `invalid` + native input props                                                                                         | Search boxes                                                                |
| `Select<T>`                                                          | `options`, `value`, `onValueChange`                                                                                            | Status filter (typed values)                                                |
| `FormField`                                                          | `htmlFor`, `label`, `hint`, `error`                                                                                            | Label + control + message                                                   |
| `QuantityStepper`                                                    | `value`, `onChange`, `min`, `max`, `label`                                                                                     | Cart quantities, clamped to stock                                           |
| `Card`                                                               | `title`, `actions`, `flush`                                                                                                    | Panels and table containers                                                 |
| `Table`, `TableRow`, `TableCell`, `TableHeaderCell`, `TableSkeleton` | `caption`, `interactive`, `numeric`, `muted`                                                                                   | Every table, with loading rows                                              |
| `Badge`, `StatusBadge`, `StockBadge`                                 | `status` / `level`                                                                                                             | The only way a status or stock level is shown                               |
| `Alert`                                                              | `tone` (`error` \| `warning` \| `success` \| `info`), `title`, `items`                                                         | Order results, stock warnings                                               |
| `EmptyState`                                                         | `icon`, `title`, `description`, `action`, `tone`                                                                               | Empty lists, no results, load errors                                        |
| `Skeleton`, `Spinner`                                                | `variant` / `size`                                                                                                             | Loading states                                                              |
| `Pagination`                                                         | `page`, `totalPages`, `totalItems`, `onPageChange`                                                                             | Order list                                                                  |
| `SummaryList`                                                        | `items: {label, value, emphasis}[]`                                                                                            | Cart and order summaries                                                    |
| `Modal`, `ConfirmDialog`                                             | `open`, `title`, `description`, `onConfirm`, `destructive`, `loading`                                                          | Cancellation confirmation (native `<dialog>`: focus trap, Escape, backdrop) |
| `ToastProvider`, `useToast()`                                        | `showToast({tone, title, description})`                                                                                        | Success and error notifications                                             |

Global components (`src/components/global_components/`): `AppShell`, `Sidebar`, `PageHeader`
(`title`, `description`, `actions`, `backLink`), `ProductIdentity` (name + SKU), and
`navigation.ts` with `ROUTES` and `NAVIGATION_ITEMS` (every URL is defined there).

---

## Data fetching

```
page component → hook (TanStack Query) → lib/api/*Api.ts → apiClient.apiRequest() → backend
```

**`lib/api/apiClient.ts`**

| Export                                         | Purpose                                                                                                                                                                             |
| ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `apiRequest<T>(path, { method, body, query })` | `fetch` wrapper: builds the URL from `NEXT_PUBLIC_API_URL`, sends JSON, returns typed data                                                                                          |
| `ApiError`                                     | Thrown on any failure, with `status`, `code`, `message`, `details` from the backend error body. Network failures become `status 0`, `code "network_error"` with a readable message. |

**API modules** (one function per endpoint)

| Module            | Functions                                                                                                                                                              |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `productsApi.ts`  | `listProducts()`, `getProduct(productId)`                                                                                                                              |
| `ordersApi.ts`    | `listOrders({reference, status, page, pageSize})`, `getOrder(orderId)`, `getOrderByReference(reference)`, `createOrder(payload)`, `updateOrderStatus(orderId, status)` |
| `dashboardApi.ts` | `getDashboardSummary()`                                                                                                                                                |
| `queryKeys.ts`    | Every cache key (`products`, `orders.list(params)`, `orders.detail(id)`, `dashboard`)                                                                                  |

**Hooks** (`src/hooks/`)

| Hook                            | Returns                                                       | Notes                                                                           |
| ------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `useProducts()`                 | query                                                         | Shared by Products and Create Order                                             |
| `useOrders(params)`             | query                                                         | Keeps the previous page visible while the next loads                            |
| `useOrder(orderId)`             | query                                                         | Order detail                                                                    |
| `useDashboardSummary()`         | query                                                         | Dashboard counts                                                                |
| `useCreateOrder()`              | mutation                                                      | Afterwards refreshes products, orders and dashboard                             |
| `useUpdateOrderStatus(orderId)` | mutation                                                      | Shows the returned order immediately, then refreshes lists, stock and dashboard |
| `useCart()`                     | `{quantities, addProduct, setQuantity, removeProduct, clear}` | Cart state: product id → quantity only                                          |

**Keeping the UI consistent with the database.** Every mutation, successful or not, invalidates
the affected queries. After an order is placed or cancelled, the catalogue stock, order lists and
dashboard reload from the server. Client errors (4xx) are not retried; other failures retry once.

---

## Utilities

`src/utils/`

| Function                                                         | File            | Purpose                                                        |
| ---------------------------------------------------------------- | --------------- | -------------------------------------------------------------- |
| `formatMoney(amount)`                                            | `money.ts`      | `"10897.00"` → `₹10,897.00` (en-IN, INR)                       |
| `toPaise(amount)`                                                | `money.ts`      | Parses a decimal string into whole paise, without `parseFloat` |
| `multiplyPaise(unitPrice, quantity)`                             | `money.ts`      | Exact line total in paise                                      |
| `formatPaise(paise)`                                             | `money.ts`      | Formats a paise integer as currency                            |
| `formatDateTime(iso)` / `formatDate(iso)`                        | `dateUtils.ts`  | UTC from the API → local time, e.g. `26 Nov 2026, 9:34 am`     |
| `ORDER_STATUS_LABEL`, `STATUS_ACTION_LABEL`, `STOCK_LEVEL_LABEL` | `labels.ts`     | The only place enum values become UI text                      |
| `getErrorMessage(error)`, `getErrorDetails(error)`               | `apiErrors.ts`  | User-facing message and per-field details from any error       |
| `cx(...classNames)`                                              | `classNames.ts` | Joins class names, skipping falsy values                       |

Types in `src/types/` (`Product`, `Order`, `OrderSummary`, `OrderStatus`, `DashboardSummary`,
`ApiErrorBody`, …) mirror the backend schemas. `isOrderStatus(value)` narrows untrusted input
such as URL parameters.

---

## Notable behaviour

**Create Order**

- The cart stores only `{productId: quantity}`. Name, price and stock are always read from the
  latest catalogue, so a stale price is never shown.
- The preview total is calculated in integer paise. The backend calculates the real total.
- _Add_ is disabled for out-of-stock products and when all available units are already in the cart.
- Low-stock products show _Only N left_.
- When a line holds all remaining stock, a **Stock limit reached** warning bar appears at the top
  and the line shows _Maximum available quantity added_. Both are derived from the cart and stock,
  so they update immediately.
- If stock drops below the cart quantity (another order took it), the line shows
  _Only N available_ and _Place order_ is disabled.
- On a 409 from the server, each `details` entry (`items.1.quantity`) is mapped back to its cart
  line, and the page says that nothing was ordered and no stock changed.
- Catalogue search is client-side: a case-insensitive match on name or SKU
  (`matchesSearch()` in `ProductPicker.tsx`).

**Orders list**

- Filters live in the URL (`/orders?reference=5cq&status=PACKED&page=2`): they survive opening an
  order and coming back, and the dashboard links straight to a filtered list. Invalid values in
  the URL are ignored.
- The reference search waits 300 ms after typing stops before calling the API.
- The reference is a real link (keyboard, middle-click, screen readers) and the whole row is clickable.
- Separate empty states for "no orders yet" and "no orders match your filters".

**Order detail**

- Action buttons are built from the order's `allowed_transitions`, so the UI never duplicates the
  state machine. A shipped or cancelled order shows that no further actions are available.
- Cancelling opens a confirmation dialog that states how many items return to stock.
- If the order changed elsewhere, the server's 409 message is shown in a toast and the page reloads
  the real status.
- An unknown or malformed id shows _Order not found_.

**Accessibility**

- One `<h1>` per page, labelled form controls, table captions, `aria-current` on the active
  navigation link, visible focus ring, `role="alert"` on errors, labels on icon-only buttons.
- Animations are disabled when the user prefers reduced motion.

**Responsive layout**

- Below 1024 px the sidebar becomes a top navigation bar, the Create Order cart and the order
  summary move under the main content, and wide tables scroll horizontally inside their card.

---

## Quality checks

```bash
npm run check
```

| Check         | Tool                                                                          |
| ------------- | ----------------------------------------------------------------------------- |
| Lint          | ESLint with `next/core-web-vitals`, `next/typescript`, Prettier compatibility |
| Design tokens | `scripts/check-design-tokens.mjs`                                             |
| Types         | TypeScript strict mode, no `any`                                              |
| Formatting    | Prettier                                                                      |

---

## Adding a page

1. Create `src/page_components/<name>_page/<Name>Page.tsx` and `<name>.css`.
2. Add a thin route file under `src/app/(console)/<route>/page.tsx` that renders it.
3. Add the URL to `ROUTES` (and to `NAVIGATION_ITEMS` if it belongs in the sidebar).
4. Add the API function in `lib/api/`, a cache key in `queryKeys.ts` and a hook in `hooks/`.
5. Build the UI from base components; add tokens to `theme.css` if a value is missing.
6. Run `npm run check`.
