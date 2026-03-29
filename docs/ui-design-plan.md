# FinanceRAG Web UI Design Plan

## Overview
A clean, professional web interface for querying financial regulatory documents using natural language. Built on top of the existing FastAPI backend.

---

## Pages / Views

### 1. Main Chat Interface (Home)
The primary experience. Think ChatGPT meets Bloomberg Terminal.

**Layout:**
- Left sidebar: Document library (list of ingested docs)
- Center: Chat area with question input and AI responses
- Right panel (collapsible): Source documents with relevance scores

**Chat Features:**
- Text input with "Ask a question..." placeholder
- Submit button + Enter key support
- Response displays: answer text, source cards, response time
- Source cards show: document name, relevance score (%), preview snippet
- Click source card to highlight the exact passage
- Query history (pulled from PostgreSQL query_logs table)

**Example interaction:**
```
User: What are the minimum capital requirements under Basel III?

FinanceRAG: Under Basel III, financial institutions must maintain:
- CET1: 4.5% of Risk-Weighted Assets
- Tier 1: 6.0% of RWA  
- Total Capital: 8.0% of RWA
- Capital Conservation Buffer: 2.5%

Sources:
[1] Basel III Capital Requirements (relevance: 79%) - "The minimum CET1..."
[2] Credit Risk Framework (relevance: 72%) - "Capital adequacy under..."
```

### 2. Document Management
Upload and manage the document library.

**Features:**
- Drag-and-drop file upload (PDF, DOCX, TXT, MD)
- Upload progress indicator
- Document list with: filename, type, chunks created, date ingested, status
- Delete document option
- Bulk upload support
- Storage stats (total docs, total chunks, collection size)

### 3. Analytics Dashboard
Powered by PostgreSQL query_logs table (already collecting data).

**Metrics:**
- Total queries processed
- Average response time (ms)
- Most queried topics (word cloud or bar chart)
- Queries per day (line chart)
- Document usage (which docs get cited most)
- Response quality indicators

### 4. Query History
Searchable log of all past queries.

**Columns:**
- Timestamp
- Question
- Documents retrieved
- Response time (ms)
- Model used
- View full response (expandable)

---

## Design Language

### Color Palette
- **Primary:** Deep navy (#1a1a2e) - trust, finance, authority
- **Accent:** Teal (#0f9b8e) - modern, tech-forward
- **Background:** Off-white (#f8f9fa) - clean, readable
- **Cards:** White (#ffffff) with subtle shadow
- **Text:** Dark gray (#2d2d2d) for readability
- **Success:** Green (#28a745) for relevance scores > 70%
- **Warning:** Amber (#ffc107) for scores 50-70%
- **Muted:** Light gray (#6c757d) for metadata

### Typography
- **Headings:** Inter or IBM Plex Sans (professional, fintech feel)
- **Body:** Same family, regular weight
- **Code/Data:** JetBrains Mono or Fira Code (for document excerpts)

### Design Principles
1. **Finance-grade trust.** No playful colors. Professional, clean, authoritative.
2. **Information density.** Show sources, scores, timing. Users want transparency.
3. **Speed perception.** Show loading states, stream responses if possible.
4. **Mobile responsive.** Sidebar collapses on mobile, chat remains primary.

---

## Technical Stack

### Frontend
- **Framework:** Next.js 14 (React, server components, API routes)
- **Styling:** Tailwind CSS (fast, utility-first, professional look)
- **Charts:** Recharts (lightweight, React-native charting)
- **Icons:** Lucide React (clean, consistent icon set)
- **File upload:** react-dropzone
- **State:** React hooks (no Redux needed for this scope)

### Deployment
- **Frontend:** Vercel (free tier, automatic deploys from GitHub)
- **API:** Existing EC2 instance (already running)
- **Domain:** financerag.veristack.ca (subdomain of existing domain)
- **SSL:** Automatic via Vercel + Let's Encrypt on EC2

### API Integration
All endpoints already exist:

| UI Action | API Endpoint | Method |
|-----------|-------------|--------|
| Ask question | /query | POST |
| Chat with history | /chat | POST |
| Upload document | /ingest/upload | POST |
| Ingest from path | /ingest | POST |
| Health check | /health | GET |
| View stats | /stats | GET |
| Clear collection | /collection | DELETE |

### CORS Configuration
Already enabled in FastAPI (allow_origins=["*"]). For production, restrict to:
```python
allow_origins=["https://financerag.veristack.ca"]
```

---

## Implementation Plan

### Phase 1: Core Chat (2-3 hours)
1. Create Next.js project
2. Build chat interface component
3. Connect to /query endpoint
4. Display answers with source cards
5. Basic responsive layout

### Phase 2: Document Management (2 hours)
1. Build upload page with drag-and-drop
2. Connect to /ingest/upload endpoint
3. Display document list from /stats
4. Add delete functionality

### Phase 3: Polish (2 hours)
1. Loading states and animations
2. Error handling and user feedback
3. Mobile responsiveness
4. Query history page (from PostgreSQL)
5. Dark mode toggle

### Phase 4: Deploy (1 hour)
1. Push to GitHub repo
2. Connect to Vercel
3. Set up financerag.veristack.ca DNS
4. Configure CORS for production domain
5. Test end-to-end

---

## Wireframes (Text-based)

### Main Chat View
```
+--------------------------------------------------+
| FinanceRAG          [Docs] [History] [Analytics]  |
+--------------------------------------------------+
|           |                          |            |
| Documents |   Welcome to FinanceRAG  |  Sources   |
|           |                          |            |
| > Basel   |   Ask questions about    |  (empty)   |
| > AML     |   your financial         |            |
| > Credit  |   documents using        |            |
| > Data    |   natural language.      |            |
| > Loan    |                          |            |
|           |                          |            |
|           |   [Ask a question...]    |            |
+--------------------------------------------------+
```

### After Query
```
+--------------------------------------------------+
| FinanceRAG          [Docs] [History] [Analytics]  |
+--------------------------------------------------+
|           |                          |            |
| Documents |  Q: What are Basel III   | Sources    |
|           |  capital requirements?   |            |
| > Basel   |                          | [1] Basel  |
| > AML     |  A: Under Basel III,     | III Cap..  |
| > Credit  |  institutions must       | Score: 79% |
| > Data    |  maintain CET1 at 4.5%   |            |
| > Loan    |  of RWA, Tier 1 at 6.0%, | [2] Credit |
|           |  Total Capital at 8.0%   | Risk Fr..  |
|           |  ...                     | Score: 72% |
|           |                          |            |
|           |  Response: 7.8s | gpt-4o |            |
|           |                          |            |
|           |   [Ask a question...]    |            |
+--------------------------------------------------+
```

### Document Upload
```
+--------------------------------------------------+
| FinanceRAG          [Docs] [History] [Analytics]  |
+--------------------------------------------------+
|                                                   |
|  Document Management                              |
|                                                   |
|  +--------------------------------------------+  |
|  |                                            |  |
|  |   Drag and drop files here                 |  |
|  |   or click to browse                       |  |
|  |                                            |  |
|  |   Supports: PDF, DOCX, TXT, MD            |  |
|  +--------------------------------------------+  |
|                                                   |
|  Ingested Documents (5)          40 chunks total  |
|  +--------------------------------------------+  |
|  | File              | Type | Chunks | Date   |  |
|  |--------------------|------|--------|--------|  |
|  | aml_policy.md      | MD   | 8      | Mar 27 |  |
|  | basel_iii.md        | MD   | 6      | Mar 27 |  |
|  | credit_risk.md      | MD   | 8      | Mar 27 |  |
|  | data_governance.md  | MD   | 9      | Mar 27 |  |
|  | loan_underwrite.md  | MD   | 9      | Mar 27 |  |
|  +--------------------------------------------+  |
+--------------------------------------------------+
```

---

## VeriStack Branding Integration

- Header: "FinanceRAG" with subtle "Powered by VeriStack" tagline
- Footer: VeriStack logo + link to veristack.ca
- Color palette aligns with VeriStack brand (professional, trust-oriented)
- "Built for financial services compliance teams" messaging

---

## Future Enhancements (Post-Launch)

1. **User authentication** (login, API keys per user)
2. **Multi-tenant** (separate document collections per organization)
3. **Streaming responses** (show answer as it generates)
4. **Document preview** (view the full source document inline)
5. **Export** (download answers as PDF reports)
6. **Slack/Teams integration** (query from chat tools)
7. **Fine-tuned models** (domain-specific financial models)
8. **Feedback loop** (thumbs up/down on answers to improve retrieval)

---

*Plan created March 28, 2026. Ready to build after Week 4 deployment guide completion.*
