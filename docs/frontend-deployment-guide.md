# FinanceRAG Frontend: How It Was Built

A clear, simple walkthrough of how the web UI was built and deployed. Written for learning and interview discussions.

---

## The Problem

We had a working API (FastAPI on AWS EC2) that you could only talk to via terminal commands like `curl`. That's fine for developers, but not for anyone else. We needed a web interface.

## The Solution

A Next.js frontend deployed on Vercel that talks to your existing API.

---

## Architecture (Simple Version)

```
User's Browser
    |
    v
Vercel (hosts the frontend)
    |
    v
API Proxy (runs on Vercel's servers)
    |
    v
Your EC2 Backend (FastAPI + Docker)
```

**Why a proxy?** The frontend is served over HTTPS (secure). Your API runs on HTTP (not secure). Browsers block this mix. The proxy sits on the server side where browsers don't enforce this rule, so it can talk to your HTTP backend without issues.

---

## Key Concepts

### 1. What is Next.js?

A React framework that makes building web apps simpler. React handles what the user sees (buttons, text, layout). Next.js adds routing (pages), server-side code (API routes), and deployment optimization.

Think of React as the engine. Next.js is the car built around it.

### 2. What is Vercel?

A hosting platform built by the creators of Next.js. You connect your GitHub repo, and every time you push code, Vercel automatically builds and deploys your site. Free for personal projects.

Similar to how GitHub Actions auto-deploys your backend to EC2, Vercel auto-deploys your frontend.

### 3. What is Tailwind CSS?

A CSS framework where you style elements directly in the HTML using utility classes instead of writing separate CSS files.

Instead of:
```css
.button { background-color: blue; padding: 12px; border-radius: 8px; }
```

You write:
```html
<button class="bg-blue-500 px-3 py-2 rounded-lg">Click</button>
```

Faster to write, easier to maintain, consistent across the app.

### 4. What is an API Proxy?

A middleman. Instead of the browser calling your API directly:

```
Browser --> Your API (blocked by browser security)
```

The browser calls your own server, which then calls the API:

```
Browser --> Vercel Server --> Your API (works fine)
```

The browser trusts Vercel (same domain). Vercel's server has no browser security restrictions, so it can call any API.

---

## How We Built It: Step by Step

### Step 1: Create the Next.js Project

```bash
npx create-next-app@latest frontend --typescript --tailwind
```

This generates a project folder with:
- `src/app/page.tsx` - the main page
- `src/app/layout.tsx` - the page wrapper (title, fonts)
- `src/app/globals.css` - global styles
- `package.json` - dependencies

### Step 2: Build the Chat Interface

The main page (`page.tsx`) has these parts:

**State management** - tracks messages, user input, loading status, API key
```typescript
const [messages, setMessages] = useState([]);
const [input, setInput] = useState("");
const [loading, setLoading] = useState(false);
const [apiKey, setApiKey] = useState("");
```

**API key modal** - prompts user for their key, saves to browser storage
```typescript
localStorage.setItem("financerag-api-key", apiKey);
```

**Send message** - calls the proxy with the question and API key
```typescript
const res = await fetch("/api/proxy", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ endpoint: "/query", apiKey, question: input, k: 5 }),
});
```

**Display response** - shows the answer, source documents with relevance scores, response time

**Suggested questions** - clickable buttons to help first-time users

### Step 3: Build the API Proxy

File: `src/app/api/proxy/route.ts`

This is a Next.js API route. It runs on Vercel's servers, not in the browser.

```typescript
// Browser sends request here (same domain, HTTPS)
export async function POST(request) {
  const { endpoint, apiKey, ...data } = await request.json();
  
  // Proxy forwards to your EC2 backend (HTTP, server-to-server)
  const res = await fetch(`http://35.171.2.221${endpoint}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": apiKey,
    },
    body: JSON.stringify(data),
  });
  
  return NextResponse.json(await res.json());
}
```

### Step 4: Build the Upload Proxy

Separate route for file uploads because they use `FormData` instead of JSON.

File: `src/app/api/upload/route.ts`

Same concept: browser sends file to Vercel, Vercel forwards to EC2.

### Step 5: Deploy to Vercel

1. Push code to GitHub
2. Go to vercel.com, sign up with GitHub
3. Click "Add New Project"
4. Select the FinanceRAG repo
5. Set root directory to `frontend`
6. Add environment variable: `API_URL` = `http://35.171.2.221`
7. Click Deploy

Vercel builds the app and gives you a live URL. Every future push to GitHub auto-deploys.

---

## File Structure

```
frontend/
  src/
    app/
      page.tsx          # Main chat interface
      layout.tsx         # Page wrapper (title, metadata)
      globals.css        # Global styles
      api/
        proxy/
          route.ts       # Server-side proxy for API calls
        upload/
          route.ts       # Server-side proxy for file uploads
  .env.local             # Local environment variables
  next.config.ts         # Next.js configuration
  package.json           # Dependencies
  tailwind.config.ts     # Tailwind CSS config
```

---

## How to Discuss This in an Interview

### When asked "How does the frontend work?"

> "The frontend is a Next.js app deployed on Vercel. It has a chat interface where users type questions about financial documents and get AI-generated answers with source citations. The app uses server-side API routes as a proxy to communicate with the FastAPI backend on EC2. This avoids mixed content issues since Vercel serves over HTTPS but the backend runs on HTTP."

### When asked "Why Next.js?"

> "Three reasons. First, it supports server-side API routes, which I needed for the proxy layer. Second, it deploys to Vercel with zero configuration, giving me automatic CI/CD for the frontend. Third, it's the industry standard for React apps, so the codebase is familiar to most developers."

### When asked "Why not just call the API directly from the browser?"

> "Browsers enforce mixed content restrictions. The frontend is served over HTTPS from Vercel, but the API runs on HTTP on EC2. Browsers block HTTPS pages from making HTTP requests. The proxy runs server-side on Vercel where these restrictions don't apply. In production, I'd add SSL to the EC2 instance so the frontend could call the API directly over HTTPS."

### When asked "What would you improve?"

> "Three things. First, add SSL to the backend so I can eliminate the proxy layer. Second, add streaming responses so answers appear word by word instead of all at once. Third, add user authentication so different users have separate document collections and query histories."

---

## Key Takeaways

1. **Frontend and backend are separate.** Different repos, different hosting, different deployment pipelines. This is standard in modern web development.

2. **Proxies solve security restrictions.** When the browser can't call an API directly, route through your own server.

3. **Vercel makes deployment trivial.** Connect GitHub, push code, get a live URL. No server management needed.

4. **The API is the hard part.** Building a good API (which we did first) makes the frontend straightforward. The UI just calls endpoints that already exist.

5. **Every piece is replaceable.** Don't like Vercel? Use Netlify. Don't like Next.js? Use any framework. The API doesn't care what calls it.

---

*Document created March 29, 2026. Written for Wale's learning and interview preparation.*
