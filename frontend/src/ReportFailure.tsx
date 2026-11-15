import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowRight, LoaderCircle } from 'lucide-react';
import { Report, startVerification, errorMessage } from './api';

export default function ReportFailure({ report }: { report: Report }) {
  const navigate = useNavigate();
  const [retrying, setRetrying] = useState(false);
  const [retryError, setRetryError] = useState('');
  const rateLimited = /HTTP 429|rate.?limit|quota/i.test(report.error || '');
  const jsonFormatMismatch = /unexpected format|JSON (array|string|number|boolean|null)|expected an object/i.test(report.error || '');
  const legacyJsonFailure = /Groq returned JSON in an unexpected format/i.test(report.error || '');

  async function retry() {
    setRetrying(true);
    setRetryError('');
    try {
      const nextId = await startVerification(report.source_text);
      navigate(`/report/${encodeURIComponent(nextId)}`);
    } catch (error) {
      setRetryError(errorMessage(error));
    } finally {
      setRetrying(false);
    }
  }

  return <div className="report-error" role="alert">
    <h1>We hit a source<br/>or model error.</h1>
    <p>{legacyJsonFailure
      ? 'This saved report was stopped by an older response-format check. It contains no verified findings, and refreshing this report will keep showing its saved error.'
      : report.error || 'The verification engine could not finish the report.'}</p>
    <p>{rateLimited
      ? 'This is a Groq rate or available-quota response. Wait for the limit window to reset, then retry. If it continues, check usage, limits and model access in the Groq Console. Settings shows whether a key is present, not its remaining quota.'
      : jsonFormatMismatch
        ? 'Groq returned JSON in a shape this verification step could not validate. This report was stopped rather than treating that response as verified. Retry the same text; if the format error repeats, check model access or use a compatible chat model.'
        : 'You can retry the same text or check provider configuration in Settings.'}</p>
    <div className="report-error-actions">
      <button className="button button-red" type="button" onClick={() => void retry()} disabled={retrying}>
        {retrying ? <><LoaderCircle className="spin" size={14}/> Starting…</> : <>{legacyJsonFailure ? 'Run fresh investigation' : 'Retry same text'} <ArrowRight size={15}/></>}
      </button>
      <Link className="button button-dark" to="/settings">Open settings <ArrowRight size={15}/></Link>
    </div>
    {retryError && <p className="form-error" role="status">{retryError}</p>}
  </div>;
}
