# myAcademic platform: handoff for building new pages and features

This guide is for anyone adding a page, a feature or a whole new section (for example career matching) to Prof. Dhar's myAcademic platform. Follow it and the new work will look and behave like the rest of the platform: same shell, same colours, same type, same components, same data and auth wiring.

Everything below was read from the code. Each rule gives the file it comes from so you can check it yourself.

| Repo (GitHub org `AcademicEDM`) | Commit read |
|---|---|
| `EDM-React-New` | `e4ba349`, 2026-11-02 |
| `EDM-Node-New` | `aca20a6`, 2026-11-02 |
| `EDM-Django` | `097379d`, 2026-10-25 |

If those repos have moved on, check the files named here again before relying on a value.

## 0. If you are an AI coding agent working from this file

Give this file to the agent together with the task. The agent should follow these steps.

**Before writing code, read:**
1. `EDM-React-New/src/v3/pages/upcomingAssessments.jsx` and `src/css/UpcomingAssessments.module.css`, the page template.
2. `src/css/App.css` lines 1 to 127, the colour variables.
3. `src/css/index.css`, the global button rules.
4. `src/Routes.jsx` and `src/components/layout/Sidebar.jsx`, routing and navigation.
5. For backend work, `EDM-Node-New/V3/router.js` and the four `caseStudy` files listed at the end of this document.

**Hard rules:**
- Work only in `EDM-React-New`, `EDM-Node-New` and `EDM-Django`, on a feature branch. Never push to `main` directly. Never touch the `*-MyAcademic` repos or run `to_prod.bat`.
- Colours only through `var(--color-...)` tokens, written with the slate fallbacks shown in section 4. No new fonts, no new icon library, no react-bootstrap, no styled-components.
- New pages go in `src/v3/pages/`, registered in `Routes.jsx`. Every API call goes through `src/v3/utils/axios.js`. New Node routes go under `/v3`, mounted with `authenticateUser`, and return `{ success, message, data }`.
- Every new page handles four states: logged out, loading, error with retry, and empty.
- Never read, print, copy or commit values from any `.env` file, and never hard-code a key, password or service URL. Refer to configuration only by variable name, and list new variable names in the pull request description.
- Do not copy anything listed in section 14.

**When finished:**
- Run Prettier and ESLint on the changed files.
- Check the page in light and dark mode, and at 375px width.
- Work through the checklist in section 15 and report each item as done or not done.

---

## 1. Where to build

| Repo | What it is | Build here? |
|---|---|---|
| `EDM-React-New` | React frontend, development copy | Yes, all UI work |
| `EDM-Node-New` | Node/Express API (MongoDB), development copy | Yes, all API work |
| `EDM-Django` | Python/Django AI services (LangGraph, OpenAI) | Yes, for AI endpoints |
| `EDM-React-MyAcademic`, `EDM-Node-MyAcademic`, `EDM-Django-MyAcademic` | Production copies | No. They are filled by the promote script (section 12) |

- Work on a branch named `<firstname>/<feature>` (for example `arin/case-study`) and merge it into `main` with a pull request.
- Commit subjects mostly follow Conventional Commits with a scope, for example `feat(career): add match page` or `fix(s3): ...`.
- Production lags behind development. For example, `src/utils/auth.js` (the role helpers) exists only in `EDM-React-New` so far. A page that uses it works in production only after that change is promoted.

## 2. Running the frontend locally

```bash
cd EDM-React-New
npm ci          # .npmrc sets legacy-peer-deps; postinstall applies patches/react-scripts+5.0.1.patch
npm start       # uses .env; "npm run start-stage" uses .env.stage
```

- **Stack:** Create React App with React 17, react-router-dom v5, Redux + redux-thunk, MUI v6, axios, zustand and @tanstack/react-query v4.
- **Node version:** not pinned. CI uses Node 20, so use that.
- **Password gate:** in development every route first redirects to `/validate`, a page-access password page, because `REACT_APP_PROD` is not set in `.env`. Ask the team for that password. Never commit it anywhere new.
- **Backend:** the backend at `REACT_APP_BASE_URL` must be reachable, because login is a cookie session (section 9).

## 3. The look in one paragraph

A fixed 90px vertical sidebar in SJSU blue `#0055A2` sits on the left, with white lucide icons and small labels. A light header carries the "myAcademic" wordmark in blue. Content sits on a near-white background in flat white cards with a 1px grey border and 12px corners. Buttons are 38px tall with 8px corners, are not uppercase, and use primary blue when filled. Dark mode exists and works only if you use the colour variables below, never raw hex.

## 4. Colours: use the CSS variables, never raw hex

The design system is a set of CSS custom properties, not an MUI theme. They are defined in `src/css/App.css`:
- `:root` defaults: lines 1 to 60
- light overrides, `:root[data-theme='light']`: lines 112 to 127
- dark mode, `:root[data-theme='dark']`: lines 62 to 110

The app always sets `data-theme` on `<html>` (`src/App.jsx` lines 40 to 55), so the light override values are the ones that actually apply in light mode.

### Core tokens

| Variable | Light (what users see) | Dark | Use for |
|---|---|---|---|
| `--color-primary` | `#0055a2` | `#2b7acb` | Buttons, links, active states, icons in titles |
| `--color-primary-hover` | `#0076d1` | `#3a8fe0` | Hover on primary |
| `--color-accent` | `#f7c82f` | `#f2b544` | Small gold highlights and badges only |
| `--color-bg` | `#f7f7f7` | `#0f141b` | Page background behind cards |
| `--color-surface-1` | `#ffffff` | `#151b23` | Cards, panels, header, dialogs |
| `--color-surface-2` | `#f2f4f8` | `#1b2430` | Inputs, table headers, hover rows, secondary panels |
| `--color-surface-3` | `#e9edf3` | `#222c3a` | Third level, rarely needed |
| `--color-text` | `#1a1f2b` | `#f1f5fa` | Body and heading text |
| `--color-text-muted` | `#4b5565` | `#c2cad6` | Subtitles, meta text, helper text |
| `--color-border` | `#d8dee8` | `#2a3441` | Every border and divider |
| `--color-error` | `#c62828` | `#e57373` | Error text |
| `--color-input-bg` | `#ffffff` | `#101821` | Input backgrounds |
| `--color-success-bg` / `--color-danger-bg` | `#ddffdd` / `#ffdddd` | `#143225` / `#3a1414` | Soft success and danger panels |
| `--bg-sidebar` | `#0055A2` | `#0055A2` | Sidebar. It stays blue in both modes |

Other tokens you will see:
- `--accent-red #ef4444`, `--accent-red-hover #dc2626`, `--accent-red-light #fee2e2`, `--accent-green #10b981`
- `--shadow-sm`, `--shadow-soft`, `--shadow-strong`, `--shadow-popover`
- `--border-radius-sm 6px`, `--border-radius-md 10px`, `--border-radius-lg 16px`
- `--transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1)`

### How the newest code writes colours

Write the token with a slate fallback, exactly like this:

```css
color: var(--color-text, #0f172a);
color: var(--color-text-muted, #64748b);
border: 1px solid var(--color-border, #e2e8f0);
background: var(--color-surface-1, #ffffff);
background: var(--color-surface-2, #f8fafc);
color: var(--color-primary, #0055a2);
```

### Primary blue tints

These rgba values recur everywhere:

| Value | Use |
|---|---|
| `rgba(0, 85, 162, 0.08)` | Selected or hover background |
| `rgba(0, 85, 162, 0.25)` | Active border |
| `rgba(0, 85, 162, 0.12)` | Focus ring: `box-shadow: 0 0 0 3px rgba(0, 85, 162, 0.12)` |

### Status colours

| Status | Strong (filled chips, filled alerts) | Text-level |
|---|---|---|
| Success | `#2e7d32` | `#059669` / `#10b981` |
| Warning | `#f57c00` | `#f59e0b` |
| Error | `#d32f2f` | `#dc2626` / `#ef4444` |
| Info | Primary blue | |

### Do not use

- `#007bff` / `#0069d9`: old Bootstrap blue, still in the admin panel and some create modals.
- `#1976d2`: MUI's default blue. It shows up when you pass `color="primary"` to MUI components that `App.css` does not repaint, such as Fab, Switch, Checkbox and CircularProgress.
- `#3B6FF0` and the navy `#0B1437`: belong only to the analytics page's private palette.
- `--color-text-secondary`: never defined anywhere. Use `--color-text-muted`.

## 5. Typography

- **Body font:** MUI's default stack, `"Roboto", "Helvetica", "Arial", sans-serif`, at 16px with line-height 1.5, set through `<CssBaseline/>` in `MainLayout.jsx`. Roboto is never actually loaded, so users see Helvetica or Arial.
  - Do not introduce a new font on your page.
  - Some quiz pages declare `'DM Sans'` without loading it. Do not copy that.
- **Shell wordmark:** "myAcademic" at 2.1rem, weight 700, letter-spacing −0.4px, in `#0055A2`, with an italic "my" (`src/components/layout/MainLayout.css` lines 58 to 72).
- **Page title (newest style):** `font-size: clamp(1.75rem, 3.5vw, 2.25rem); font-weight: 800; letter-spacing: -0.03em;` with a primary-coloured lucide icon beside it.
- **Page subtitle:** `1rem`, `var(--color-text-muted)`, `line-height: 1.6`, `max-width: 650px`.
  - Both title and subtitle are in `src/css/UpcomingAssessments.module.css` lines 22 to 43.
- **Section and card titles:** 1.15 to 1.25rem, weight 700.
- **Meta text, labels and badges:** 0.75 to 0.85rem. Weight 600 to 700 for badges, otherwise muted.
- **Weights in use:** 600 and 700 dominate, then 500 and 800. Avoid 300.
- **MUI Typography:** used with default variants, most often `body2`, `caption`, `h6`, `subtitle2`.

## 6. Spacing, corners, shadows and breakpoints

- **Spacing:** MUI's 8px scale in `sx` (`gap: 1`, `mb: 2`, `p: 2`, `px: 3`). In CSS, use gaps of 8, 10, 12 or 16px and padding of 1 to 1.5rem.
- **Page container (newest style):** `max-width: 1240px; margin: 0 auto; padding: 2.25rem 1.5rem 4rem;`
- **Older pages:** use `--padding-horizontal: max(1.2rem, 3vw)` from `src/css/Page.module.css`.
- **Corners:**

  | Element | Radius |
  |---|---|
  | Buttons and inputs | 8px |
  | Cards | 12px |
  | Sections, popovers and dialogs | 16px |
  | Pills and badges | 9999px |

  Course cards are a special case at 24px.
- **Shadows:** cards are flat (`elevation={0}` with a 1px border). Hover gets a gentle lift: `transform: translateY(-2px); box-shadow: 0 6px 16px -2px rgba(0, 0, 0, 0.06); border-color: rgba(0, 85, 162, 0.4);`
- **The one breakpoint that matters: 768px** (`MainLayout.css` lines 222 and 355). Below it:
  - the sidebar disappears and a 60px bottom navigation bar takes its place;
  - the header shrinks to 60px.

  Design every page so it works at 375px wide.
- **Card grids:** `grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 1.25rem;`
- **MUI breakpoints:** the defaults (600, 900, 1200, 1536). Responsive `sx` objects like `{ xs: 2, md: 4 }` are fine.

## 7. Icons, logo, images

- **Icon libraries:**
  - **lucide-react** for anything in the shell, page titles, navigation and new pages. Use 22px in navigation and 14 to 20px inline.
  - **@mui/icons-material** for buttons and actions inside forms (Add, Delete, Edit, Close, Search, UploadFile), where most older code uses it.
  - Do not add a third icon library. The Font Awesome import in `src/css/FAIcons.css` is unused.
- **Logo:** `public/logo-new.png`, used for the sidebar logo and the favicon.
- **Other images:** avatar placeholder `public/images/UserAvatarLogo.png`, file-type icons in `public/icons/`.

## 8. The app shell: what every page gets automatically

`src/Routes.jsx` wraps every route in `MainLayout` (`src/components/layout/MainLayout.jsx`), which supplies:
- the left `Sidebar` on desktop, or the bottom bar on mobile;
- the fixed header with wordmark, date badge and Virtual TA button;
- the scrolling content area and the footer;
- the notification drawer, profile popover and Virtual TA side panel.

Your page renders inside the content area. Do not add your own navbar, sidebar or footer.

`components/commons/NavBar.jsx`, `FloatingButton.jsx` and `ThemeToggle.jsx` are old and not rendered anywhere. Do not use them.

For a full-screen experience (as quizzes do), hide the chrome with:

```js
window.dispatchEvent(new CustomEvent('toggle-quiz-ui', { detail: { hideNav: true, hideSidebar: true, hideTA: true } }))
```

Send it again with `false` values when leaving.

## 9. Adding a page, step by step

### 9.1 Create the files

Put new pages in `src/v3/pages/` and their styles in a CSS module. The newest page keeps its module in `src/css/`, so either location works.

```
src/v3/pages/CareerMatchPage.jsx
src/css/CareerMatch.module.css
```

### 9.2 Register the route

In `src/Routes.jsx`, add the lazy import beside the others (the existing pages are imported around lines 72 to 175). Then add the route inside the `<Switch>`, above the `NotFound` catch-all at the end.

```jsx
const CareerMatchPage = React.lazy(() => import('./v3/pages/CareerMatchPage.jsx'))
...
<Route exact path="/career-match" component={CareerMatchPage} />
```

There are no route guards. Each page checks login and role itself (section 10.3).

### 9.3 Add the sidebar entry

In `src/components/layout/Sidebar.jsx`, inside the `isLoggedIn && (...)` block, copy the Assessments link:

```jsx
import { Briefcase } from 'lucide-react'
...
<NavLink activeClassName="sidebar-item-active" className="sidebar-item" to="/career-match">
    <Briefcase />
    <span>Careers</span>
</NavLink>
```

- **Admin-only link:** wrap it in `{isAdmin && (...)}` as the Admin Panel link does.
- **Mobile:** if the section should also appear in the mobile bottom bar, add it in `MainLayout.jsx` (around lines 433 to 528).

### 9.4 Page template

This is the structure of `src/v3/pages/upcomingAssessments.jsx`, the newest page. Copy it for new work: it handles all four states (logged out, loading, error with retry, empty) and uses only theme variables.

```jsx
import React, { useState, useEffect, useCallback } from 'react'
import { useSelector } from 'react-redux'
import { useHistory } from 'react-router-dom'
import { Button } from '@mui/material'
import { Briefcase } from 'lucide-react'
import axiosInstance from '../utils/axios'
import styles from '../../css/CareerMatch.module.css'

export default function CareerMatchPage() {
    const history = useHistory()
    const { user, userFetchCompleted } = useSelector((state) => state.userData)
    const isLoggedIn = Boolean(user && user.id !== undefined)

    const [data, setData] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    const fetchData = useCallback(async () => {
        setLoading(true)
        setError(null)
        try {
            const res = await axiosInstance.get('/v3/career/matches')
            if (res.data?.success) setData(res.data.data)
            else setError('Failed to load matches.')
        } catch (err) {
            setError(err?.response?.data?.message || 'Unable to load matches. Please try again later.')
        } finally {
            setLoading(false)
        }
    }, [])

    useEffect(() => {
        if (userFetchCompleted && isLoggedIn) fetchData()
        else if (userFetchCompleted) setLoading(false)
    }, [userFetchCompleted, isLoggedIn, fetchData])

    if (userFetchCompleted && !isLoggedIn) {
        return (
            <div className={styles.container}>
                <div className={styles.emptyState}>
                    <p>Please log in to see your matches.</p>
                    <Button variant="contained" onClick={() => history.push('/login')}>Log in</Button>
                </div>
            </div>
        )
    }

    return (
        <div className={styles.container}>
            <header className={styles.header}>
                <h1 className={styles.title}>
                    <Briefcase className={styles.titleIcon} size={30} /> Career matches
                </h1>
                <p className={styles.subtitle}>Jobs ranked against the skills in your resume.</p>
            </header>

            {loading && (
                <div className={styles.grid}>
                    {[1, 2, 3].map((i) => <div key={i} className={styles.skeletonCard} />)}
                </div>
            )}
            {!loading && error && (
                <div className={styles.emptyState}>
                    <p>{error}</p>
                    <Button variant="outlined" onClick={fetchData}>Retry</Button>
                </div>
            )}
            {!loading && !error && data.length === 0 && (
                <div className={styles.emptyState}><p>No matches yet.</p></div>
            )}
            {!loading && !error && data.length > 0 && (
                <div className={styles.grid}>
                    {data.map((item) => (
                        <div key={item.id} className={styles.card}>{/* card content */}</div>
                    ))}
                </div>
            )}
        </div>
    )
}
```

Matching CSS module. The values are taken from `src/css/UpcomingAssessments.module.css`.

```css
.container { max-width: 1240px; margin: 0 auto; padding: 2.25rem 1.5rem 4rem; min-height: 85vh; }
.header { margin-bottom: 2rem; }
.title { font-size: clamp(1.75rem, 3.5vw, 2.25rem); font-weight: 800; color: var(--color-text);
         letter-spacing: -0.03em; margin: 0 0 0.5rem; display: flex; align-items: center; gap: 0.75rem; }
.titleIcon { color: var(--color-primary, #0055a2); }
.subtitle { font-size: 1rem; color: var(--color-text-muted, #64748b); margin: 0; max-width: 650px; line-height: 1.6; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 1.25rem; }
.card { background: var(--color-surface-1, #ffffff); border: 1px solid var(--color-border, #e2e8f0);
        border-radius: 12px; padding: 1.25rem; transition: all 0.2s ease; }
.card:hover { border-color: rgba(0, 85, 162, 0.4); box-shadow: 0 6px 16px -2px rgba(0, 0, 0, 0.06);
              transform: translateY(-2px); }
.emptyState { text-align: center; padding: 4rem 2rem; margin: 2rem 0; background: var(--color-surface-1, #ffffff);
              border: 1px dashed var(--color-border, #cbd5e1); border-radius: 16px; }
.skeletonCard { height: 200px; border-radius: 12px; border: 1px solid var(--color-border, #e2e8f0);
                background: linear-gradient(90deg, var(--color-surface-2, #f1f5f9) 25%,
                var(--color-surface-1, #ffffff) 50%, var(--color-surface-2, #f1f5f9) 75%);
                background-size: 200% 100%; animation: shimmer 1.5s ease-in-out infinite; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
```

### 9.5 A section with several views

Keep the active view in the URL (`?tab=`), as `src/components/courses-new/Course.jsx` does. Render it with MUI `<Tabs variant="scrollable" scrollButtons="auto">` followed by a `<Divider/>`. Tab colours are already themed globally.

## 10. Components: which one to use and how it should look

### 10.1 Rules that apply automatically

`src/css/index.css` forces a style on every MUI `Button` with `!important`:
- 8px radius, no uppercase, weight 600, height 38px, 0.875rem, no shadow;
- `variant="contained"` is filled with `--color-primary` and hovers to `--color-primary-hover`.

So:
- Use `<Button variant="contained">` for the main action and `variant="outlined"` for secondary ones.
- Do not try to restyle button radius or colour through `sx`. It is silently ignored unless you add `!important`.
- The one deliberate exception is the pill-shaped call to action in page headers (`src/components/courses-new/Courses.module.css` lines 243 to 252): `border-radius: 24px !important; height: 42px !important; box-shadow: 0 3px 8px rgba(0, 85, 162, 0.25) !important;`

`src/css/App.css` also repaints MUI inputs, tabs, chips, alerts, Paper and dialogs for light and dark mode.

### 10.2 Recipes

**Text input.** Use `<TextField size="small">` with this `sx`, as in `src/v3/pages/QuizInstructorPage.jsx`:

```js
sx={{ '& .MuiOutlinedInput-root': {
    color: 'var(--color-text, #0f172a)', bgcolor: 'var(--color-surface-2, #f8fafc)', borderRadius: '8px',
    '& fieldset': { borderColor: 'var(--color-border, #cbd5e1)' },
    '&:hover fieldset': { borderColor: 'var(--color-primary, #0055A2)' } } }}
```

**Card.** Surface-1 background, 1px border, 12px radius, 16 to 20px padding, hover lift (section 9.4).

**Badge or status pill.**
- Shape: `border-radius: 9999px; padding: 0.2rem 0.6rem; font-size: 0.75rem; font-weight: 700;`
- Colour: tint background `rgba(0, 85, 162, 0.1)` with primary text.
- Alternatively, use MUI `<Chip size="small" color="primary|success|warning|error">`, which `App.css` repaints to the status colours.

**Table.**
- Large admin-style data uses AG Grid with `className="ag-theme-quartz"` (see `src/components/AdminPanel.jsx`; dark mode is handled in `App.css`).
- Small tables use MUI `Table` inside:

  ```jsx
  <TableContainer component={Paper} elevation={0} sx={{ border: '1px solid var(--color-border)', borderRadius: '12px' }}>
  ```

  Give the header surface-2 background and bold text.

**Dialog.** MUI `Dialog`, with Cancel (outlined) and the main action (contained) on the right:

```jsx
<Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth
    PaperProps={{ sx: { bgcolor: 'var(--color-surface-1)', color: 'var(--color-text)',
                        border: '1px solid var(--color-border)', borderRadius: '12px' } }}>
    <DialogTitle>...</DialogTitle>
    <DialogContent>...</DialogContent>
    <DialogActions sx={{ px: 3, pb: 2 }}>...</DialogActions>
</Dialog>
```

**Feedback.**
- **Toast:** `src/components/commons/Notification.jsx` (MUI Snackbar + Alert, top right, closes after 6s). Props are `show`, `onClose`, `severity`, `message`.
- **During a save:** `<Backdrop open><CircularProgress color="inherit"/></Backdrop>`.
- **Page loading:** skeleton cards or MUI `Skeleton`.
- **Never** use `alert()`.

**Global loading pill.** Render `<TopLoader message="Loading..."/>` from `src/components/commons/TopLoader.jsx` while something loads. The pill itself is already mounted in `App.jsx`.

### 10.3 Shared components worth reusing

All live in `src/components/commons/`.

| Component | Use it for | Props |
|---|---|---|
| `TopLoader` | Global loading pill | `message` |
| `Notification` | Toast messages | `show`, `onClose`, `severity`, `message` |
| `LoginPrompt` | "Log in required" dialog that sends to `/login` | `open`, `onClose`, `message` |
| `UploadFileModal` | File upload dialog, for example a resume | `open`, `handleClose`, `onSubmit`, `accept` |
| `DragAndDrop` | Drop zone | `accept`, `file`, `handleUpload` |
| `FileDisplayModal` | Viewing a PDF or file | `open`, `handleClose`, `fileKey`, `fileBlob` |
| `RTE` | Rich text editor (CKEditor 5) | `value`, `setValue`, `placeholder`, `disabled`, `readOnly` |

## 11. Data, login and roles

### 11.1 Calling the API

- Use the shared axios instance `src/v3/utils/axios.js`. It is `axios.create({ baseURL: process.env.REACT_APP_BASE_URL, withCredentials: true })`.
- Older code builds `${process.env.REACT_APP_BASE_URL}/...` by hand. Do not copy that.

### 11.2 Login

- Login is an httpOnly cookie named `jwt` set by the Node API. Requests carry it automatically because of `withCredentials`, so never read or store tokens yourself.
- `aws-amplify` is installed but not used.

### 11.3 Current user and role

- The user lives in Redux: `useSelector((state) => state.userData)` gives `{ user, userFetchCompleted, ... }`. The user is logged in when `user && user.id !== undefined`.
- Wait for `userFetchCompleted` before deciding anything.
- Roles are `ADMIN`, `Instructor`, `TA`, `Student`. Check them with `src/utils/auth.js`:

  ```js
  import { useAuthRole } from '../../utils/auth'
  const { user, isAdmin, isInstructor, isTA } = useAuthRole()
  ```

  The checks are hierarchical: an admin passes `isInstructor`, and an instructor passes `isTA`.
- Course-level roles are per course and come from the course's student list (see `Course.jsx`).

### 11.4 Where state goes

| Kind of state | Use |
|---|---|
| Page-local data | `useState` + `useEffect` (most pages do this) |
| Complex state for one feature | A zustand store in `src/v3/store/useXStore.js` |
| Polling or shared server data | react-query `useQuery` (object syntax) |
| The current user | Redux, read only |

Do not put sensitive data in react-query, because its cache is persisted to `localStorage`.

### 11.5 Environment variable names (frontend)

| Variable | Points to |
|---|---|
| `REACT_APP_BASE_URL` | Node API |
| `REACT_APP_DJANGO_URL` | Django AI service |

A new microservice should get its own variable in the same style, for example `REACT_APP_CAREER_URL`. Better still, call it through Node (section 12.2) so the browser keeps talking to one origin.

## 12. Backend conventions

### 12.1 Node API (`EDM-Node-New`)

Three API generations are mounted in `app.js`: `/` (v1), `/api/v2` and `/v3`. Build new features in V3, which is the cleanest:

```
V3/routes/career.routes.js          # maps verbs to controller functions
V3/controllers/career.controller.js # request in, response out
V3/services/career/service.js       # logic, validation, calls to other services
V3/models/careerMatch.model.js      # Mongoose model
```

**Mount the router** with authentication in `V3/router.js`, beside the existing ones:

```js
router.use("/career", authenticateUser, careerRouter);
```

**Use the V3 response shape** (from `V3/controllers/caseStudy.controller.js`):

```js
return res.status(200).json({ success: true, message: "...", data: result });
// on error
return res.status(err.httpCode || 500).json({ success: false, message: err.message || "..." });
```

Other conventions:
- **Auth:** `authenticateUser` reads the `jwt` cookie (or a Bearer header) and sets `req.user`.
- **Roles:** role middleware lives in `utils/roles.js` (`requireRole`, `requireAdmin`). Most features also check roles inside the service.
- **Models:**
  - PascalCase model names. Prefix with `V3` if a name could collide, as `V3CaseStudy` does.
  - `{ timestamps: true }`.
  - References written as `{ type: mongoose.Schema.Types.ObjectId, ref: "User", index: true }`.
- **IDs:** IDs leave the API encrypted (`utils/encryption.js`, and `maskIds()` in `V3/utils/responseFormatter.js`). Decrypt incoming IDs with `decrypt()`.
- **Logging:** `console.error("Error in <function>:", err)`.

### 12.2 Calling a separate service, such as the matching microservice, from Node

Copy `V3/services/pdfParser.service.js`, which calls Django:
- read the URL from an env variable, with a localhost fallback;
- use `fetch` with an `AbortController` timeout;
- check `response.ok`;
- return `{ error }` rather than throwing.

For mapping failures to status codes, copy `V3/controllers/virtualTa.controller.js` and `quiz.controller.js`: 504 on timeout, 502 or 503 when the service is unreachable.

Add the new URL variable (for example `CAREER_SERVICE_URL`) to the Node `.env` files.

### 12.3 Existing career code you will meet

| Code | What it does |
|---|---|
| `controllers/jobs.js` (`GET /jobs`) | Calls the Adzuna job API |
| `controllers/resumeJobs.js` (`POST /resume-jobs`) | Matches a resume against a fixed list of 16 keywords |
| `POST /v3/profile/parse-pdf` | Sends the resume to Django's resume parser. A better extraction service would plug in here |
| `/careers` (`src/components/Careers.jsx`) | Frontend career page in the older visual style. Not linked from the sidebar |

### 12.4 Django AI service (`EDM-Django`)

Features follow nodes, then graph, then view, then URL:
- functions in `app/nodes/`;
- a LangGraph builder in `app/graphs/`;
- a DRF `APIView` in `app/langgraph_views.py` (model: `ResumeParserAPIView`);
- a `re_path` in `project/urls.py`.

Get LLMs only through `app/utils/llm_factory.py` (`get_llm`).

Success responses are a feature-specific JSON body; errors are `{"error": "..."}` with status 400 or 500. `REPOSITORY_DEVELOPER_DOCUMENTATION.md` (lines 608 to 690) walks through adding a feature.

URL patterns in `project/urls.py` are unanchored regexes, and the first match wins, so a new path containing the word "search" would be caught by the existing `search` route. Anchor new patterns, for example `r'^career-match/?$'`, or place them above the others.

### 12.5 Deployment and the promote step

- **Deploys:** pushing to `main` in a development repo deploys it to the development servers through GitHub Actions and AWS CodeDeploy.
- **Promoting to production:** run `to_prod.bat` (Windows) from the development repo. It copies the code into the matching `*-MyAcademic` repo and pushes a commit like `Promote from dev: <date> - NODE - <last commit subject>`.
- **Env files are never copied by the promote step.** A new environment variable must be added by hand to the production repo's env file.

## 13. Code style

- **Prettier** (`.prettierrc`): 4-space indent, no semicolons, single quotes, `trailingComma: es5`.
- **Lint on commit:** husky runs `lint-staged`, which is `eslint --fix --max-warnings=0` then `prettier --write`, on staged files.
- **New files:** do not start them with `/* eslint-disable */`, even though older files do.
- **Components:** function components with hooks, `.jsx`, PascalCase file names, react-router v5 hooks (`useHistory`, `useParams`, `useLocation`).
- **Styling:** a CSS module per page, plus `sx` for small MUI tweaks. Use theme variables in both.

## 14. Do not copy these patterns

The codebase has some patterns that new work should avoid:

- **Styling:**
  - react-bootstrap: legacy, and Bootstrap's own CSS is not even loaded.
  - styled-components sidebars.
  - The old `NavBar`.
- **Colours and fonts:**
  - Hard-coded hex colours without a variable, which break dark mode.
  - `#007bff` or `#1976d2` as "primary".
  - Loading a new web font.
- **CSS leaks:** element selectors in CSS modules such as `h1, p { margin: 0 }` or `* { margin: 0 }`. They leak to the whole app.
- **Errors:** `alert()` for errors, or errors only sent to `console.log`.
- **Secrets:** API keys written into frontend source, and committing `.env` files with real values. Keep keys on the server side.
- **Node errors:** relying on the status argument of `new AppError(message, 400)`. The constructor in `customErrors/appError.js` ignores it, so a V3 controller that answers with `err.httpCode || 500` sends a 500. Set `err.httpCode` yourself, or fix the constructor in a separate change.
- **Inter-service calls:** the special header some Django-to-Node calls use to skip login. New services should forward the user's `jwt` cookie instead (see `V3/controllers/virtualTa.controller.js`).
- **Caching:** in-memory caches inside the Node process. They are not shared between processes.

## 15. Checklist before opening a pull request

- [ ] The page is registered in `Routes.jsx` and, if users should reach it, linked in `Sidebar.jsx` (and in the mobile bar if needed).
- [ ] Every colour is a `var(--...)` token. You toggled dark mode (profile menu, Sun/Moon) and the page still reads well.
- [ ] It works below 768px and at 375px wide, with the bottom navigation bar visible.
- [ ] It handles logged out, loading, error with retry, and empty.
- [ ] Buttons are plain MUI `contained` or `outlined`, cards are 12px with a 1px border, icons are lucide.
- [ ] All API calls go through `src/v3/utils/axios.js`. New Node routes are under `/v3` with `authenticateUser` and return `{ success, message, data }`.
- [ ] No keys, passwords or URLs with credentials in the code. New env variable names are listed in the PR description so they can be added to production by hand.
- [ ] Prettier and ESLint pass on the changed files.

### Reference files to keep open while building

| Use | File |
|---|---|
| Page structure | `src/v3/pages/upcomingAssessments.jsx` |
| Page styling | `src/css/UpcomingAssessments.module.css` |
| Theme variables | `src/css/App.css` |
| Global button rules | `src/css/index.css` |
| Navigation | `src/components/layout/Sidebar.jsx` and `Sidebar.css` |
| Shell | `src/components/layout/MainLayout.jsx` and `MainLayout.css` |
| Cards | `src/components/courses-new/tabs/assignments/Assignments.module.css` |
| Page header with call to action | `src/components/courses-new/Courses.module.css` |
| Backend feature template | `V3/routes/caseStudy.routes.js`, `V3/controllers/caseStudy.controller.js`, `V3/services/caseStudy/service.js`, `V3/models/caseStudy.model.js` in `EDM-Node-New` |
