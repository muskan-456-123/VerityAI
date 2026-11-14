import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react';
import { Link, NavLink, Route, Routes, useNavigate, useParams } from 'react-router-dom';
import { ArrowDownRight, ArrowLeft, ArrowRight, ArrowUpRight, Check, ChevronDown, Clipboard, Clock3, ExternalLink, FileSearch, Filter, History, LoaderCircle, Menu, Search, Settings as SettingsIcon, ShieldCheck, SlidersHorizontal, Sparkles, X } from 'lucide-react';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Claim, Evidence, getHealth, getHistory, getReport, HistoryItem, Report, startVerification, deleteReport, errorMessage } from './api';

const SAMPLE = 'The European Union currently has 27 member states. Pluto is the ninth planet in the Solar System. The first iPhone was released in 2007.';
const verdictOrder = ['CURRENT', 'STALE', 'CONTRADICTED', 'UNSUPPORTED', 'CONFLICTING', 'STABLE'] as const;
const verdictLabels: Record<string, string> = { CURRENT: 'Current', STALE: 'Stale', CONTRADICTED: 'Contradicted', UNSUPPORTED: 'Unsupported', CONFLICTING: 'Conflicting', STABLE: 'Stable' };

function Brand({ small = false }: { small?: boolean }) {
  return <Link to="/" className={`brand ${small ? 'brand-small' : ''}`} aria-label="Verity home"><span className="brand-mark"><span></span><span></span></span><span>VERITY<span className="brand-dot">.</span></span></Link>;
}

function Header() {
  const [open, setOpen] = useState(false);
  return <header className="site-header">
    <div className="header-inner"><Brand />
      <nav className={`main-nav ${open ? 'nav-open' : ''}`} aria-label="Main navigation">
        <NavLink to="/workspace" onClick={() => setOpen(false)}>Investigate</NavLink>
        <NavLink to="/history" onClick={() => setOpen(false)}>History</NavLink>
        <NavLink to="/settings" onClick={() => setOpen(false)}>Settings</NavLink>
        <NavLink to="/about" onClick={() => setOpen(false)}>About</NavLink>
        <a href="/api/docs" target="_blank" rel="noreferrer">Documentation <ArrowUpRight size={13}/></a>
      </nav>
      <Link to="/workspace" className="button button-dark header-cta">New investigation <ArrowRight size={15}/></Link>
      <button className="mobile-menu" onClick={() => setOpen(!open)} aria-label={open ? 'Close menu' : 'Open menu'}>{open ? <X/> : <Menu/>}</button>
    </div>
  </header>;
}

function Footer() {
  return <footer className="site-footer"><div className="footer-top"><Brand small/><span className="mono">INDEPENDENT THINKING. VERIFIED INFORMATION.</span><nav className="footer-links" aria-label="Footer navigation"><Link to="/workspace">Product</Link><a href="/api/docs" target="_blank" rel="noreferrer">Documentation</a><a href="https://github.com" target="_blank" rel="noopener noreferrer">GitHub <ArrowUpRight size={13}/></a><Link to="/about">About</Link><a href="mailto:hello@verity.example">Contact</a></nav></div><div className="footer-bottom"><span>© 2026 VERITY INTELLIGENCE / 001</span><span>THE TRUTH IS WORTH CHECKING.</span></div></footer>;
}

function AppShell({ children, minimal = false }: { children: React.ReactNode; minimal?: boolean }) {
  return <><Header/><main>{children}</main>{!minimal && <Footer/>}</>;
}

function InputForm({ compact = false }: { compact?: boolean }) {
  const navigate = useNavigate();
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const remaining = 12_000 - text.length;
  const paste = async () => {
    try {
      const pasted = await navigator.clipboard.readText();
      if (pasted.length > 12_000) {
        setText(pasted.slice(0, 12_000));
        setError('Clipboard text exceeded 12,000 characters. Only the first 12,000 were added.');
      } else { setText(pasted); setError(''); }
    }
    catch { setError('Clipboard access was blocked. Paste directly into the text area instead.'); }
  };
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (text.trim().length < 20) { setError('Add at least 20 characters so there is enough context to investigate.'); return; }
    setBusy(true); setError('');
    try { const id = await startVerification(text.trim()); navigate(`/report/${id}`); }
    catch (e) { setError(errorMessage(e)); setBusy(false); }
  };
  return <form className={`input-panel ${compact ? 'input-panel-compact' : ''}`} onSubmit={submit}>
    <div className="input-panel-top"><span className="eyebrow"><span className="live-dot"/> INVESTIGATION INPUT</span><span className="mono muted">SOURCE TEXT / 001</span></div>
    <label htmlFor={compact ? 'workspace-source' : 'landing-source'} className="sr-only">Paste your AI-generated answer</label>
    <textarea id={compact ? 'workspace-source' : 'landing-source'} maxLength={12000} value={text} onChange={e => setText(e.target.value)} placeholder="Drop your text here. Let’s find out what’s actually true…" />
    {error && <p className="form-error" role="alert">{error}</p>}
    <div className="input-toolbar"><div className="input-actions"><button type="button" className="text-button" onClick={paste}><Clipboard size={14}/> Paste text</button><button type="button" className="text-button" onClick={() => setText(SAMPLE)}>Try sample</button><button type="button" className="text-button" onClick={() => {setText(''); setError('');}}>Clear</button></div><span className={`mono char-count ${remaining < 500 ? 'count-low' : ''}`}>{text.length.toLocaleString()} / 12,000</span></div>
    <button type="submit" className="button button-red investigate-button" disabled={busy || text.trim().length < 20}>{busy ? <><LoaderCircle className="spin" size={17}/> Connecting to analysis…</> : <>INVESTIGATE <ArrowRight size={18}/></>}</button>
    <div className="input-foot"><ShieldCheck size={14}/> Your text is sent securely to the verification engine. Analysis can take a few moments.</div>
  </form>;
}

function Landing() {
  return <AppShell>
    <section className="hero-wrap"><div className="hero-topline"><span className="eyebrow"><span className="status-block"/> INDEPENDENT THINKING. VERIFIED INFORMATION.</span><span className="mono">EST. 2026&nbsp; / &nbsp;INTELLIGENCE 001</span></div>
      <div className="hero-grid"><div className="hero-copy"><p className="hero-kicker mono">DON'T JUST TRUST AI. VERIFY IT.</p><h1>AI CAN BE<br/>CONFIDENT.<br/><span>BUT IS IT</span><br/><span className="hero-red">CORRECT?</span></h1><p className="hero-subtitle">Investigate AI-generated answers.<br/>Detect outdated claims. Verify with live evidence.</p><div className="hero-notes"><span><Check size={14}/> Claim-by-claim analysis</span><span><Check size={14}/> Live web sources</span></div></div>
      <div className="hero-work"><div className="hero-index"><span className="mono">HOW IT WORKS / 003</span><div><b>01</b><span>EXTRACT</span><ArrowDownRight size={17}/></div><div><b>02</b><span>VERIFY</span><ArrowDownRight size={17}/></div><div><b>03</b><span>CORRECT</span><Check size={17}/></div><p>Independent thinking.<br/>Verified information.</p></div><InputForm/></div></div>
      <div className="hero-ticker"><span>CLAIMS ARE NOT EVIDENCE</span><span>↗</span><span>FRESHNESS MATTERS</span><span>↗</span><span>SHOW YOUR SOURCES</span><span>↗</span><span>CLAIMS ARE NOT EVIDENCE</span></div>
    </section>
    <section className="section section-method" id="method"><div className="section-heading"><div><span className="eyebrow">A BETTER QUESTION / 01</span><h2>From confident<br/>to <em>checked.</em></h2></div><p>Verity treats every answer as a set of claims to investigate—not a response to trust on faith.</p></div><div className="method-list"><article><span className="big-number">01</span><div><h3>Extract the claims</h3><p>Separate an answer into individual facts worth checking. Compound statements become clear, specific questions.</p></div><span className="method-mark">01 / EXTRACT</span></article><article><span className="big-number">02</span><div><h3>Follow the evidence</h3><p>Search live sources, compare what they say, and keep the original source links and available dates visible.</p></div><span className="method-mark">02 / VERIFY</span></article><article><span className="big-number">03</span><div><h3>Correct with care</h3><p>See what still holds, what changed, and what remains uncertain—then read a source-linked correction.</p></div><span className="method-mark">03 / CORRECT</span></article></div></section>
    <section className="section features-section"><div className="features-intro"><span className="eyebrow">THE INVESTIGATION TOOLKIT / 06</span><h2>Trust the<br/>trail, not<br/>the tone.</h2><p>Fluent language can sound like certainty. Verity makes the evidence legible.</p><Link className="button button-dark" to="/about">How it works <ArrowRight size={15}/></Link></div><div className="feature-grid"><div className="feature-card feature-wide"><span className="mono">01 / CLAIM EXTRACTION</span><FileSearch/><h3>Find the facts<br/>inside the answer.</h3><p>Split compound ideas into claims you can actually verify.</p></div><div className="feature-card feature-lime"><span className="mono">02 / FRESHNESS</span><Clock3/><h3>Old can be<br/>out of date.</h3><p>Look for evidence of change—not just an old timestamp.</p></div><div className="feature-card feature-red"><span className="mono">03 / LIVE SOURCES</span><Search/><h3>Look beyond<br/>the model.</h3><p>Bring retrieved source material and links into the report.</p></div><div className="feature-card feature-tall"><span className="mono">04—06 / EVIDENCE • ATTRIBUTION • CORRECTION</span><ShieldCheck/><h3>Show your<br/>working.</h3><p>Inspect the supporting and contradicting evidence. Keep uncertainty where it belongs. Correct only what the evidence can support.</p><span className="feature-index">VERITY / 001</span></div></div></section>
    <section className="preview-section"><div className="preview-heading"><span className="eyebrow">A REPORT, NOT A GUESS</span><span className="mono">ILLUSTRATIVE UI / NO LIVE FINDINGS</span></div><div className="preview-report"><div className="preview-report-head"><span className="mono">VERIFICATION REPORT / PREVIEW</span><span className="preview-stamp">ILLUSTRATIVE<br/>ONLY</span></div><div className="preview-report-body"><div><span className="mono muted">CLAIM / 01</span><h3>“The claim is the beginning<br/>of the investigation.”</h3><span className="verdict-chip verdict-current">EXAMPLE STATUS</span></div><div className="preview-source"><span className="mono">EVIDENCE / NOT CONNECTED</span><p>This preview shows the report layout only. Actual verdicts and source links appear after a live investigation.</p><span className="source-line"><i/> Retrieved evidence will appear here</span></div></div><div className="preview-report-foot"><span>CLAIMS / EVIDENCE / UNCERTAINTY</span><span>VERITY AI</span></div></div></section>
    <section className="final-cta"><div className="cta-ornament">V<span>?</span></div><span className="eyebrow">DON’T HAND OVER YOUR JUDGMENT.</span><h2>STOP GUESSING.<br/><span>START VERIFYING.</span></h2><Link to="/workspace" className="button button-dark">Start an investigation <ArrowRight size={16}/></Link><span className="mono cta-fine">NO BLIND TRUST. JUST BETTER QUESTIONS.</span></section>
  </AppShell>;
}

function Workspace() {
  return <AppShell><div className="workspace-page page-pad"><div className="page-head"><div><span className="eyebrow">WORKSPACE / 001</span><h1>Start an<br/><em>investigation.</em></h1><p>Paste the answer you want to check. Verity will extract claims and search for evidence.</p></div><div className="workspace-aside"><span className="mono">INPUT SPECIFICATION</span><span>Plain text · 20–12,000 characters</span><span>One investigation at a time</span><span>Live evidence may take a few moments</span></div></div><InputForm compact/><p className="privacy-note"><ShieldCheck size={15}/> Provider credentials stay on the server. Your submitted text is stored with its report in this initial SQLite implementation.</p></div></AppShell>;
}

function ProgressPanel({ stages }: { stages: Report['stages'] }) {
  return <div className="progress-card"><div className="progress-top"><div><span className="eyebrow">INVESTIGATION IN PROGRESS</span><h2>Following the evidence.</h2></div><span className="live-pill"><i/> LIVE</span></div><div className="progress-steps">{stages.map((stage, index) => <div className={`progress-step stage-${stage.status}`} key={stage.key}><span className="progress-index">{String(index + 1).padStart(2, '0')}</span><span className="progress-symbol">{stage.status === 'complete' ? <Check size={16}/> : stage.status === 'active' ? <LoaderCircle size={17} className="spin"/> : stage.status === 'error' ? <X size={16}/> : <span/>}</span><div><b>{stage.label}</b><small>{stage.detail || (stage.status === 'pending' ? 'Waiting for the previous stage' : 'Working…')}</small></div></div>)}</div><div className="progress-honesty mono">Stages update from backend request state. No work is marked complete ahead of the response.</div></div>;
}

function SummaryTiles({ claims }: { claims: Claim[] }) {
  const counts = [{ key: 'total', label: 'TOTAL CLAIMS', value: claims.length }, ...verdictOrder.map(v => ({ key: v.toLowerCase(), label: verdictLabels[v], value: claims.filter(c => c.verdict === v).length }))];
  return <div className="summary-tiles">{counts.map(({ key, label, value }) => <div className={`summary-tile tile-${key.toLowerCase()}`} key={key}><span className="mono">{label.toUpperCase()}</span><strong>{String(value).padStart(2, '0')}</strong></div>)}</div>;
}

function EvidenceCard({ evidence, compact = false }: { evidence: Evidence; compact?: boolean }) {
  return <article className={`evidence-card ${compact ? 'evidence-compact' : ''}`}><div className="evidence-card-head"><span className={`source-type source-${evidence.classification}`}>{evidence.classification}</span><span className="mono">{evidence.source_id}</span></div><h4>{evidence.title}</h4><a href={evidence.url} target="_blank" rel="noopener noreferrer" className="source-domain">{evidence.domain}<ExternalLink size={13}/></a>{evidence.excerpt && <p>{evidence.excerpt}</p>}<div className="evidence-meta"><span>Relevance {Math.round(evidence.relevance * 100)} / 100</span>{evidence.published_date && <span>Published {evidence.published_date}</span>}{evidence.updated_date && <span>Updated {evidence.updated_date}</span>}</div></article>;
}

function ClaimDetail({ claim, reportId }: { claim: Claim; reportId: string }) {
  const [expanded, setExpanded] = useState(true);
  return <aside className="claim-detail"><div className="detail-head"><span className="mono">CLAIM / {claim.claim_id.replace('claim-', '')}</span><span className={`verdict-chip verdict-${claim.verdict.toLowerCase()}`}>{verdictLabels[claim.verdict]}</span></div><h2>{claim.statement}</h2><p className="detail-explanation">{claim.explanation}</p><div className="detail-tags"><span>{claim.category}</span><span>{claim.temporal_sensitivity} temporal sensitivity</span><span>{claim.confidence} confidence</span></div><div className="freshness-block"><div><span className="mono">FRESHNESS / SEPARATE FROM CONFIDENCE</span><b>{claim.freshness.label}</b></div><p>{claim.freshness.explanation}</p></div><button className="accordion-toggle" onClick={() => setExpanded(!expanded)} aria-expanded={expanded}><span><FileSearch size={16}/> Retrieved evidence ({claim.evidence.length})</span><ChevronDown size={16} className={expanded ? '' : 'rotate-180'}/></button>{expanded && <div className="detail-evidence">{claim.evidence.length ? claim.evidence.map(item => <EvidenceCard evidence={item} compact key={item.source_id}/>) : <div className="no-evidence">No source records were returned for this claim. The verdict should be read with that limitation.</div>}</div>}<Link className="text-link evidence-link" to={`/evidence/${reportId}/${claim.claim_id}`}>Open evidence explorer <ArrowRight size={14}/></Link></aside>;
}

function InlineClaimText({ text, claims, selected, onSelect }: { text: string; claims: Claim[]; selected: string; onSelect: (id: string) => void }) {
  const lower = text.toLowerCase();
  const ranges: { start: number; end: number; claim: Claim }[] = [];
  for (const claim of claims) {
    let start = lower.indexOf(claim.statement.toLowerCase());
    let end = start < 0 ? -1 : start + claim.statement.length;
    if (start < 0) {
      const words = claim.statement.match(/[A-Za-z0-9]+/g) || [];
      for (let size = Math.min(8, words.length); size >= 3 && start < 0; size--) {
        for (let offset = 0; offset <= words.length - size; offset++) {
          const phrase = words.slice(offset, offset + size).map(word => word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('[\\s,.;:!?–—’\'"()/-]+');
          const match = new RegExp(`\\b${phrase}\\b`, 'iu').exec(text);
          if (match) { start = match.index; end = start + match[0].length; break; }
        }
      }
    }
    if (start >= 0 && end > start && !ranges.some(range => start < range.end && end > range.start)) ranges.push({ start, end, claim });
  }
  ranges.sort((a, b) => a.start - b.start);
  const pieces: React.ReactNode[] = [];
  let cursor = 0;
  for (const range of ranges) {
    if (range.start < cursor) continue;
    if (range.start > cursor) pieces.push(text.slice(cursor, range.start));
    pieces.push(<button type="button" key={range.claim.claim_id} title={`${verdictLabels[range.claim.verdict]} — select to inspect`} aria-label={`${verdictLabels[range.claim.verdict]} claim: ${range.claim.statement}`} onClick={() => onSelect(range.claim.claim_id)} className={`inline-claim inline-${range.claim.verdict.toLowerCase()} ${selected === range.claim.claim_id ? 'inline-selected' : ''}`}>{text.slice(range.start, range.end)}</button>);
    cursor = range.end;
  }
  pieces.push(text.slice(cursor));
  return <>{pieces}</>;
}

function renderCitations(answer: string): React.ReactNode[] {
  return answer.split(/(\[[^\]]+\]\(https:\/\/[^)\s]+\))/g).map((part, index) => {
    const match = /^\[([^\]]+)\]\((https:\/\/[^)\s]+)\)$/.exec(part);
    if (!match) return part;
    try {
      const url = new URL(match[2]);
      if (url.protocol !== 'https:') return match[1];
      return <a key={`citation-${index}`} href={url.href} target="_blank" rel="noopener noreferrer">{match[1]} <ExternalLink size={12}/></a>;
    } catch { return match[1]; }
  });
}

function ReportPage() {
  const { reportId = '' } = useParams();
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState('');
  const [filter, setFilter] = useState('ALL');
  const [sort, setSort] = useState('source');
  const [copied, setCopied] = useState(false);
  const refresh = useCallback(async () => {
    try { const data = await getReport(reportId); setReport(data); setError(''); }
    catch (e) { setError(errorMessage(e)); }
  }, [reportId]);
  useEffect(() => { setReport(null); void refresh(); }, [refresh]);
  useEffect(() => {
    if (!report || report.status !== 'processing') return;
    const timer = window.setInterval(() => { void refresh(); }, 1600);
    return () => window.clearInterval(timer);
  }, [report?.status, refresh]);
  useEffect(() => { if (report?.claims.length && !selected) setSelected(report.claims[0].claim_id); }, [report, selected]);
  const visible = useMemo(() => {
    const list = (report?.claims || []).filter(c => filter === 'ALL' || c.verdict === filter);
    if (sort === 'confidence') list.sort((a, b) => b.confidence_rank - a.confidence_rank);
    else if (sort === 'verdict') list.sort((a, b) => verdictOrder.indexOf(a.verdict) - verdictOrder.indexOf(b.verdict));
    return list;
  }, [report, filter, sort]);
  const activeClaim = report?.claims.find(c => c.claim_id === selected) || visible[0];
  const copyAnswer = async () => { if (!report?.corrected_answer) return; await navigator.clipboard.writeText(report.corrected_answer); setCopied(true); window.setTimeout(() => setCopied(false), 1800); };
  if (error && !report) return <AppShell><div className="page-pad error-page"><span className="eyebrow">REPORT / UNAVAILABLE</span><h1>We couldn’t find<br/>that report.</h1><p>{error}</p><Link className="button button-dark" to="/history">Go to history</Link></div></AppShell>;
  if (!report) return <AppShell><div className="report-loading"><LoaderCircle className="spin"/><span className="mono">OPENING INVESTIGATION / {reportId}</span></div></AppShell>;
  if (report.status === 'processing') return <AppShell><div className="page-pad"><div className="report-overline"><span className="eyebrow">INVESTIGATION / {report.report_id}</span><span className="mono">{new Date(report.created_at).toLocaleString()}</span></div><ProgressPanel stages={report.stages}/></div></AppShell>;
  if (report.status === 'error') return <AppShell><div className="page-pad"><div className="report-overline"><span className="eyebrow">INVESTIGATION / {report.report_id}</span><span className="verdict-chip verdict-stale">ANALYSIS STOPPED</span></div><div className="report-error"><h1>We hit a source<br/>or model error.</h1><p>{report.error || 'The verification engine could not finish the report.'}</p><p>Check the server/provider status in Settings, then start a new investigation.</p><Link className="button button-dark" to="/settings">Open settings <ArrowRight size={15}/></Link></div></div></AppShell>;
  if (!report.claims.length) return <AppShell><div className="page-pad"><div className="report-overline"><span className="eyebrow">REPORT / {report.report_id}</span><span className="mono">{new Date(report.created_at).toLocaleString()}</span></div><div className="empty-report"><Sparkles/><h1>No factual claims<br/>to investigate.</h1><p>The submitted text did not contain an independently verifiable factual claim.</p><Link to="/workspace" className="button button-dark">Try another answer</Link></div></div></AppShell>;
  const chartData = verdictOrder.map(v => ({ name: verdictLabels[v], count: report.claims.filter(c => c.verdict === v).length, key: v }));
  return <AppShell><div className="report-page page-pad"><div className="report-overline"><span className="eyebrow">VERIFICATION REPORT / {report.report_id}</span><span className="mono">{new Date(report.created_at).toLocaleString()}</span></div><div className="report-title-row"><div><h1>The answer,<br/><em>investigated.</em></h1><p>Claims are assessed individually. Open the evidence before you decide what to trust.</p></div><div className="report-actions"><button className="button button-outline" onClick={() => window.print()}>Export PDF <ArrowUpRight size={14}/></button><button className="button button-red" onClick={() => void navigator.clipboard.writeText(window.location.href)}>Copy report link <Clipboard size={14}/></button></div></div>
    <SummaryTiles claims={report.claims}/><div className="report-chart"><div><span className="eyebrow">VERDICT DISTRIBUTION</span><span className="mono">CLAIMS / {String(report.claims.length).padStart(2, '0')}</span></div><ResponsiveContainer width="100%" height={132}><BarChart data={chartData} margin={{ top: 10, right: 8, left: -28, bottom: 0 }}><CartesianGrid vertical={false} stroke="#ddd8ce"/><XAxis dataKey="name" tick={{ fontSize: 10, fill: '#555' }} axisLine={false} tickLine={false}/><YAxis allowDecimals={false} tick={{ fontSize: 10, fill: '#777' }} axisLine={false} tickLine={false}/><Tooltip contentStyle={{ border: '2px solid #171717', borderRadius: 0, fontFamily: 'DM Mono' }}/><Bar dataKey="count" fill="#ff613d" maxBarSize={42}/></BarChart></ResponsiveContainer></div>
    <div className="investigation-layout"><section className="original-panel"><div className="panel-heading"><span className="eyebrow">ORIGINAL ANSWER</span><span className="mono">SOURCE TEXT / 001</span></div><p className="original-text"><InlineClaimText text={report.source_text} claims={report.claims} selected={selected} onSelect={setSelected}/></p><div className="claim-list-head"><span className="eyebrow">CLAIMS / {String(report.claims.length).padStart(2, '0')}</span><span className="mono">SELECT TO INVESTIGATE</span></div><div className="claim-list-tools"><label><Filter size={13}/><select aria-label="Filter claims" value={filter} onChange={e => setFilter(e.target.value)}><option value="ALL">All verdicts</option>{verdictOrder.map(v => <option key={v} value={v}>{verdictLabels[v]}</option>)}</select></label><label><SlidersHorizontal size={13}/><select aria-label="Sort claims" value={sort} onChange={e => setSort(e.target.value)}><option value="source">Source order</option><option value="verdict">Verdict</option><option value="confidence">Confidence</option></select></label></div><div className="claim-buttons">{visible.map((claim, index) => <button key={claim.claim_id} className={`claim-button ${selected === claim.claim_id ? 'claim-selected' : ''} mark-${claim.verdict.toLowerCase()}`} onClick={() => setSelected(claim.claim_id)}><span className="mono">{String(index + 1).padStart(2, '0')}</span><span>{claim.statement}</span><span className={`verdict-chip verdict-${claim.verdict.toLowerCase()}`}>{verdictLabels[claim.verdict]}</span></button>)}{!visible.length && <p className="muted">No claims match this filter.</p>}</div></section>{activeClaim ? <ClaimDetail claim={activeClaim} reportId={report.report_id}/> : <div className="claim-detail no-evidence">Select a claim to inspect.</div>}</div>
    {report.corrected_answer && <section className="corrected-panel"><div className="corrected-header"><div><span className="eyebrow">EVIDENCE-GROUNDED REVISION</span><h2>A more careful answer.</h2></div><button className="button button-dark" onClick={() => void copyAnswer()}>{copied ? <><Check size={14}/> Copied</> : <>Copy answer <Clipboard size={14}/></>}</button></div><p>{renderCitations(report.corrected_answer)}</p><small>Corrections use supported evidence only. Source citations link to sources returned for this report.</small></section>}
    </div></AppShell>;
}

function EvidenceExplorer() {
  const { reportId = '', claimId = '' } = useParams();
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState('');
  useEffect(() => { getReport(reportId).then(setReport).catch(e => setError(errorMessage(e))); }, [reportId]);
  const claim = report?.claims.find(item => item.claim_id === claimId);
  return <AppShell><div className="page-pad evidence-page"><Link className="back-link" to={`/report/${reportId}`}><ArrowLeft size={14}/> Back to report</Link>{error && <p className="form-error">{error}</p>}{!report ? <div className="report-loading"><LoaderCircle className="spin"/> Loading evidence…</div> : claim ? <><div className="page-head evidence-page-head"><div><span className="eyebrow">EVIDENCE EXPLORER / {claim.claim_id}</span><h1>Follow the<br/><em>source trail.</em></h1></div><span className={`verdict-chip verdict-${claim.verdict.toLowerCase()}`}>{verdictLabels[claim.verdict]}</span></div><div className="evidence-query"><span className="mono">SEARCH QUERY</span><p>{claim.search_query}</p></div><blockquote className="evidence-claim">“{claim.statement}”</blockquote><p className="evidence-note">These are source records returned for this claim. Publication and update dates appear only when available from the source-search response.</p><div className="evidence-explorer-grid">{claim.evidence.map(item => <EvidenceCard evidence={item} key={item.source_id}/>)}</div>{!claim.evidence.length && <div className="no-evidence">No sources were returned. The system cannot treat this as confirmation.</div>}</> : <div className="no-evidence">This claim is not available in the report.</div>}</div></AppShell>;
}

function HistoryPage() {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | HistoryItem['status']>('ALL');
  const [sortNewest, setSortNewest] = useState(true);
  const load = useCallback(() => getHistory().then(setItems).catch(e => setError(errorMessage(e))), []);
  useEffect(() => { void load(); }, [load]);
  const visible = useMemo(() => { const rows = items.filter(item => (statusFilter === 'ALL' || item.status === statusFilter) && `${item.report_id} ${item.preview}`.toLowerCase().includes(query.toLowerCase())); return rows.sort((a,b) => sortNewest ? b.created_at.localeCompare(a.created_at) : a.created_at.localeCompare(b.created_at)); }, [items, query, sortNewest, statusFilter]);
  const remove = async (id: string) => { if (!window.confirm(`Delete report ${id}? This cannot be undone.`)) return; try { await deleteReport(id); await load(); } catch(e) { setError(errorMessage(e)); } };
  const hasFilter = query || statusFilter !== 'ALL';
  return <AppShell><div className="page-pad history-page"><div className="page-head"><div><span className="eyebrow">ARCHIVE / 002</span><h1>Past<br/><em>investigations.</em></h1><p>Reports are saved to this installation’s SQLite history.</p></div><Link to="/workspace" className="button button-red">New investigation <ArrowRight size={15}/></Link></div><div className="history-tools"><label className="history-search"><Search size={16}/><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search report ID or submitted text"/></label><label className="history-filter"><Filter size={14}/><select aria-label="Filter reports by status" value={statusFilter} onChange={e => setStatusFilter(e.target.value as typeof statusFilter)}><option value="ALL">All statuses</option><option value="complete">Completed</option><option value="processing">In progress</option><option value="error">Failed</option></select></label><button className="button button-outline" onClick={() => setSortNewest(!sortNewest)}><SlidersHorizontal size={14}/> {sortNewest ? 'Newest first' : 'Oldest first'}</button></div>{error && <p className="form-error">{error}</p>}{visible.length ? <div className="history-table"><div className="history-table-head"><span>REPORT / PREVIEW</span><span>CLAIMS</span><span>CURRENT</span><span>DATE</span><span>ACTIONS</span></div>{visible.map(item => <article className="history-row" key={item.report_id}><Link to={`/report/${item.report_id}`} className="history-report"><span className="mono">REPORT / {item.report_id}</span><strong>{item.preview || 'Empty submitted text'}</strong><small className="history-summary">{item.result_summary}</small><span className={`history-status ${item.status}`}>{item.status === 'complete' ? 'READY' : item.status.toUpperCase()}</span></Link><span className="history-number">{String(item.claim_count).padStart(2,'0')}</span><span className="history-number">{String(item.current_count).padStart(2,'0')}</span><span className="mono history-date">{new Date(item.created_at).toLocaleDateString()}</span><div className="history-actions"><Link to={`/report/${item.report_id}`} aria-label="Open report"><ArrowUpRight size={16}/></Link><button onClick={() => void remove(item.report_id)} aria-label={`Delete report ${item.report_id}`}><X size={16}/></button></div></article>)}</div> : <div className="empty-state"><History/><h2>{hasFilter ? 'No matching reports.' : 'No reports yet.'}</h2><p>{hasFilter ? 'Try another search or status filter.' : 'Your completed investigations will appear here.'}</p>{!hasFilter && <Link to="/workspace" className="button button-dark">Start an investigation</Link>}</div>}</div></AppShell>;
}

function AboutPage() {
  return <AppShell><div className="about-page page-pad"><div className="page-head"><div><span className="eyebrow">ABOUT VERITY / 001</span><h1>Confidence is<br/>not <em>evidence.</em></h1><p>Verity helps people inspect AI-generated answers claim by claim—and ask the harder question: is this information still current?</p></div><div className="about-stamp">TRUTH<br/>WORTH<br/>CHECKING<span>↗</span></div></div><div className="about-columns"><section><span className="mono">01 / WHAT WE DO</span><h2>Investigate,<br/>don’t autocomplete.</h2><p>Verity extracts facts from an answer, searches live web sources, compares evidence, and shows what supports or challenges each claim. It is not a generic chatbot and it does not make evidence appear by sounding certain.</p></section><section><span className="mono">02 / WHAT WE DON’T</span><h2>No source<br/>is a verdict.</h2><p>A retrieved page can be incomplete, outdated or in conflict with another source. Verity separates freshness from confidence, shows available source dates, and explains when the evidence is insufficient.</p></section></div><div className="about-principle"><span className="big-number">?</span><p>Independent thinking.<br/><strong>Verified information.</strong></p><span className="mono">VERITY INTELLIGENCE / 001</span></div><div className="about-cta"><Link to="/workspace" className="button button-red">Investigate an answer <ArrowRight size={15}/></Link></div></div></AppShell>;
}

function SettingsPage() {
  const [health, setHealth] = useState<{status:string;groq_configured:boolean;tavily_configured:boolean}|null>(null);
  const [error, setError] = useState('');
  useEffect(() => { getHealth().then(setHealth).catch(e => setError(errorMessage(e))); }, []);
  return <AppShell><div className="page-pad settings-page"><div className="page-head"><div><span className="eyebrow">SYSTEM / 003</span><h1>Settings &<br/><em>readiness.</em></h1><p>Provider connection status is reported by the backend. Secret values are never shown here.</p></div><SettingsIcon className="settings-hero-icon"/></div><section className="settings-card"><div className="settings-card-head"><span className="eyebrow">BACKEND PROVIDERS</span><span className="mono">HEALTH / {health?.status?.toUpperCase() || 'CHECKING'}</span></div>{error && <p className="form-error">{error}</p>}<div className="provider-row"><div><b>Groq / structured language model</b><span>Claim extraction, evidence evaluation, answer correction</span></div><span className={`connection ${health?.groq_configured ? 'connected' : 'missing'}`}><i/>{health?.groq_configured ? 'Configured' : 'Missing key'}</span></div><div className="provider-row"><div><b>Tavily / live web search</b><span>Search and optional extraction of source pages</span></div><span className={`connection ${health?.tavily_configured ? 'connected' : 'missing'}`}><i/>{health?.tavily_configured ? 'Configured' : 'Missing key'}</span></div><p className="settings-footnote">Manage keys through protected project settings. The UI receives only a configured/not configured status—not key values.</p></section><section className="settings-card settings-info"><span className="eyebrow">DATA / STORAGE</span><p>Reports are stored in an initial SQLite database. This version is designed for local/prototype use; container filesystems may be ephemeral in a published deployment.</p><span className="mono">MAX INPUT / 12,000 CHARACTERS</span></section></div></AppShell>;
}

function NotFound() { return <AppShell><div className="page-pad error-page"><span className="eyebrow">404 / NOT FOUND</span><h1>This page<br/>isn’t in evidence.</h1><Link className="button button-dark" to="/">Return home</Link></div></AppShell>; }

export default function App() {
  return <Routes><Route path="/" element={<Landing/>}/><Route path="/workspace" element={<Workspace/>}/><Route path="/report/:reportId" element={<ReportPage/>}/><Route path="/evidence/:reportId/:claimId" element={<EvidenceExplorer/>}/><Route path="/history" element={<HistoryPage/>}/><Route path="/about" element={<AboutPage/>}/><Route path="/settings" element={<SettingsPage/>}/><Route path="*" element={<NotFound/>}/></Routes>;
}
