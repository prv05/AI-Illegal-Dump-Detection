import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { ArrowLeft, Check, FileImage, MapPin, Plus, Upload, X } from "lucide-react";
import exifr from "exifr";
import { NavLink, useNavigate, useParams } from "react-router-dom";

const apiBase = import.meta.env.VITE_API_BASE_URL || `${window.location.protocol}//${window.location.hostname}:8000`;
const categories = [
  ["mixed_household", "Mixed / household waste"],
  ["construction_demolition", "Construction and demolition waste"],
  ["plastic", "Plastic waste"],
  ["electronic", "Electronic waste"],
  ["green_garden", "Green / garden waste"],
  ["industrial_chemical", "Industrial / chemical-looking waste"],
  ["other", "Other / not sure"],
] as const;

type Evidence = { id: number; original_filename: string; mime_type: string; url: string };
type Report = { id: number; case_code: string; latitude: number; longitude: number; status: string; waste_category: string; source: string; created_at: string; evidence_count: number; evidence?: Evidence[] };
type Notification = { id: number; title: string; message: string; notification_type: string; related_case_id: number | null; is_read: boolean; created_at: string; read_at: string | null };
type DashboardData = { counts: Record<string, number>; recent_reports: Report[] };
type Preview = { file: File; url: string };

function formatDate(value: string) { return new Date(value).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" }); }
function categoryLabel(value: string) { return categories.find(([key]) => key === value)?.[1] || value.split("_").join(" "); }
function statusLabel(value: string) { return value.split("_").join(" "); }

export function UploaderDashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  async function loadDashboard() {
    setLoading(true); setError("");
    try {
      const response = await fetch(`${apiBase}/api/v1/my/dashboard`, { credentials: "include" });
      if (!response.ok) throw new Error((await response.json().catch(() => ({}))).detail || "Unable to load your reports.");
      setData(await response.json());
    } catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Unable to load your reports."); }
    finally { setLoading(false); }
  }
  useEffect(() => { void loadDashboard(); }, []);
  const counts = data?.counts || {};
  return <section className="page-view uploader-page">
    <div className="uploader-heading"><div><p className="eyebrow">UPLOADER WORKSPACE</p><h1>My reports</h1><p className="page-lede">Keep your local observations together and follow each report through review.</p></div><NavLink className="uploader-primary" to="/reports/new"><Plus size={18} /> Create dump report</NavLink></div>
    {error && <div className="uploader-alert">{error}<button onClick={() => void loadDashboard()}>Try again</button></div>}
    <div className="uploader-summary">
      <Summary label="Submitted" value={counts.total} />
      <Summary label="Awaiting review" value={counts.awaiting_review} />
      <Summary label="Needs evidence" value={counts.needs_more_evidence} emphasis={Boolean(counts.needs_more_evidence)} />
      <Summary label="Confirmed" value={counts.confirmed} />
      <Summary label="Rejected" value={counts.rejected} />
      <Summary label="Resolved" value={counts.resolved} />
    </div>
    <div className="uploader-section-head"><div><p className="eyebrow">YOUR ACTIVITY</p><h2>Recent reports</h2></div><span>{loading ? "Loading records..." : `${data?.recent_reports.length || 0} shown`}</span></div>
    {loading ? <div className="uploader-empty">Loading your reports...</div> : error ? <div className="uploader-empty"><FileImage size={30} /><strong>Your private reports are unavailable</strong><span>Sign in again to reconnect this dashboard.</span><NavLink className="uploader-secondary" to="/login">Sign in again</NavLink></div> : data?.recent_reports.length ? <div className="report-table-wrap"><table className="report-table"><thead><tr><th>Case</th><th>Submitted</th><th>Waste type</th><th>Location</th><th>Status</th><th /></tr></thead><tbody>{data.recent_reports.map((report) => <tr key={report.id}><td><NavLink to={`/my-reports/${report.id}`} className="case-link">{report.case_code}</NavLink></td><td>{formatDate(report.created_at)}</td><td>{categoryLabel(report.waste_category)}</td><td>{report.latitude.toFixed(4)}, {report.longitude.toFixed(4)}</td><td><span className={`status-pill status-${report.status}`}>{statusLabel(report.status)}</span></td><td><NavLink to={`/my-reports/${report.id}`} className="table-action">Open</NavLink></td></tr>)}</tbody></table></div> : <div className="uploader-empty"><FileImage size={30} /><strong>You haven't submitted a report yet</strong><span>Start with three photos of the same suspected dump.</span><NavLink className="uploader-secondary" to="/reports/new"><Upload size={16} /> Create your first report</NavLink></div>}
    {Boolean(counts.needs_more_evidence) && <div className="evidence-callout"><MapPin size={22} /><div><strong>Additional evidence requested</strong><p>Open the highlighted report to review its current status. Official decisions remain with inspectors and administrators.</p></div></div>}
  </section>;
}

export function UploaderReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => { fetch(`${apiBase}/api/v1/my/dashboard`, { credentials: "include" }).then(async (response) => { if (!response.ok) throw new Error((await response.json().catch(() => ({}))).detail || "Unable to load your reports."); return response.json(); }).then((body: DashboardData) => setReports(body.recent_reports)).catch((requestError) => setError(requestError instanceof Error ? requestError.message : "Unable to load your reports.")).finally(() => setLoading(false)); }, []);
  return <section className="page-view my-reports-page"><div className="uploader-heading"><div><p className="eyebrow">MY WORKSPACE</p><h1>My reports</h1><p className="page-lede">Reports submitted by you, with their current review status and submitted evidence.</p></div><NavLink className="uploader-primary" to="/reports/new"><Plus size={18} /> Submit report</NavLink></div>{error && <div className="uploader-alert">{error}<NavLink to="/login">Sign in again</NavLink></div>}{loading ? <div className="uploader-empty">Loading submitted reports...</div> : reports.length ? <div className="report-table-wrap"><table className="report-table"><thead><tr><th>Case ID</th><th>Submitted</th><th>Waste type</th><th>Location</th><th>Photos</th><th>Status</th><th /></tr></thead><tbody>{reports.map((report) => <tr key={report.id}><td><NavLink to={`/my-reports/${report.id}`} className="case-link">{report.case_code}</NavLink></td><td>{formatDate(report.created_at)}</td><td>{categoryLabel(report.waste_category)}</td><td>{report.latitude.toFixed(4)}, {report.longitude.toFixed(4)}</td><td>{report.evidence_count}</td><td><span className={`status-pill status-${report.status}`}>{statusLabel(report.status)}</span></td><td><NavLink to={`/my-reports/${report.id}`} className="table-action">Open report</NavLink></td></tr>)}</tbody></table></div> : !error && <div className="uploader-empty"><FileImage size={30} /><strong>You haven't submitted a report yet</strong><span>Your first submitted report will appear here.</span><NavLink className="uploader-secondary" to="/reports/new"><Plus size={16} /> Submit your first report</NavLink></div>}</section>;
}

export function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [error, setError] = useState("");
  useEffect(() => { fetch(`${apiBase}/api/v1/notifications`, { credentials: "include" }).then(async (response) => { if (!response.ok) throw new Error((await response.json().catch(() => ({}))).detail || "Unable to load notifications."); return response.json(); }).then(setNotifications).catch((requestError) => setError(requestError instanceof Error ? requestError.message : "Unable to load notifications.")); }, []);
  async function openNotification(notification: Notification) { if (notification.is_read) return; const response = await fetch(`${apiBase}/api/v1/notifications/${notification.id}/read`, { method: "POST", credentials: "include" }); if (response.ok) setNotifications((current) => current.map((item) => item.id === notification.id ? { ...item, is_read: true, read_at: new Date().toISOString() } : item)); }
  return <section className="page-view notifications-page"><div className="uploader-heading"><div><p className="eyebrow">MY WORKSPACE</p><h1>Notifications</h1><p className="page-lede">Welcome messages and updates about your submitted reports.</p></div><span className="notification-count">{notifications.filter((item) => !item.is_read).length} unread</span></div>{error && <div className="uploader-alert">{error}</div>}{!error && <div className="notification-list">{notifications.length ? notifications.map((notification) => <button type="button" key={notification.id} className={`notification-item ${notification.is_read ? "read" : "unread"}`} onClick={() => void openNotification(notification)}><span className="notification-dot" /><div><strong>{notification.title}</strong><p>{notification.message}</p><small>{formatDate(notification.created_at)}{notification.is_read ? " · Read" : " · Unread"}</small></div>{notification.related_case_id && <NavLink to={`/my-reports/${notification.related_case_id}`} onClick={(event) => event.stopPropagation()}>Open report</NavLink>}</button>) : <div className="uploader-empty">No notifications yet.</div>}</div>}</section>;
}

export function UploaderProfilePage() {
  const [form, setForm] = useState({ current_password: "", new_password: "", new_password_confirmation: "" });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  async function submit(event: FormEvent) { event.preventDefault(); setMessage(""); setError(""); if (form.new_password !== form.new_password_confirmation) { setError("New passwords do not match."); return; } setPending(true); try { const response = await fetch(`${apiBase}/api/v1/auth/change-password`, { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify(form) }); const body = await response.json().catch(() => ({})); if (!response.ok) throw new Error(body.detail || "Unable to change password."); setMessage(body.detail); setForm({ current_password: "", new_password: "", new_password_confirmation: "" }); } catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Unable to change password."); } finally { setPending(false); } }
  return <section className="page-view profile-page"><p className="eyebrow">MY WORKSPACE</p><h1>My Profile</h1><p className="page-lede">Keep your account secure and manage your uploader access.</p><div className="profile-panel"><p className="eyebrow">ACCOUNT SECURITY</p><h2>Change password</h2><p className="panel-copy">Use at least 8 characters, including one uppercase letter and one number.</p>{message && <div className="profile-success">{message}</div>}{error && <div className="uploader-alert">{error}</div>}<form className="profile-form" onSubmit={submit}><label>Current password<input type="password" autoComplete="current-password" required value={form.current_password} onChange={(event) => setForm({ ...form, current_password: event.target.value })} /></label><label>New password<input type="password" autoComplete="new-password" minLength={8} required value={form.new_password} onChange={(event) => setForm({ ...form, new_password: event.target.value })} /></label><label>Confirm new password<input type="password" autoComplete="new-password" minLength={8} required value={form.new_password_confirmation} onChange={(event) => setForm({ ...form, new_password_confirmation: event.target.value })} /></label><button className="uploader-primary" disabled={pending}>{pending ? "Updating..." : "Change password"}</button></form></div></section>;
}

function Summary({ label, value = 0, emphasis = false }: { label: string; value?: number; emphasis?: boolean }) { return <div className={`summary-card ${emphasis ? "attention" : ""}`}><strong>{value}</strong><span>{label}</span></div>; }

export function UploaderReportPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [previews, setPreviews] = useState<Preview[]>([]);
  const [category, setCategory] = useState("other");
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [locationSource, setLocationSource] = useState("");
  const [locating, setLocating] = useState(false);
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const [created, setCreated] = useState<{ id: number; case_code: string } | null>(null);
  const chooseFiles = async (event: ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(event.target.files || []);
    const valid = selected.filter((file) => ["image/jpeg", "image/png", "image/webp"].includes(file.type) && file.size <= 10 * 1024 * 1024);
    if (selected.length !== valid.length) setError("Use JPEG, PNG, or WebP photos up to 10 MB each.");
    if (valid.length > 5 || previews.length + valid.length > 5) { setError("Choose no more than 5 photos."); return; }
    const gpsResults = await Promise.all(valid.map(async (file) => { try { return await exifr.gps(file); } catch { return null; } }));
    const photoGps = gpsResults.find((gps) => gps?.latitude !== undefined && gps.longitude !== undefined);
    if (photoGps && !latitude && !longitude) { setLatitude(String(photoGps.latitude)); setLongitude(String(photoGps.longitude)); setLocationSource("GPS from photo"); }
    setPreviews((current) => [...current, ...valid.map((file) => ({ file, url: URL.createObjectURL(file) }))]);
    event.target.value = "";
  };
  const removePhoto = (index: number) => { URL.revokeObjectURL(previews[index].url); setPreviews((current) => current.filter((_, itemIndex) => itemIndex !== index)); };
  const locateDevice = () => { if (!navigator.geolocation) { setError("Device location is not available in this browser."); return; } setLocating(true); setError(""); navigator.geolocation.getCurrentPosition((position) => { setLatitude(String(position.coords.latitude)); setLongitude(String(position.coords.longitude)); setLocationSource("Device GPS"); setLocating(false); }, () => { setError("Location permission was unavailable. Enable device location and try again."); setLocating(false); }, { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }); };
  const next = () => { setError(""); if (step === 1 && (previews.length < 3 || previews.length > 5)) { setError("Select 3 to 5 photos before continuing."); return; } if (step === 2 && (!latitude || !longitude)) { locateDevice(); return; } setStep((current) => Math.min(4, current + 1)); };
  async function submit(event: FormEvent) {
    event.preventDefault(); setPending(true); setError("");
    const formData = new FormData(); previews.forEach(({ file }) => formData.append("files", file)); formData.append("waste_category", category); formData.append("latitude", latitude); formData.append("longitude", longitude); formData.append("description", description);
    try { const response = await fetch(`${apiBase}/api/v1/my/reports`, { method: "POST", credentials: "include", body: formData }); const body = await response.json().catch(() => ({})); if (!response.ok) throw new Error(body.detail || "Could not submit this report."); setCreated(body); } catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Could not submit this report."); } finally { setPending(false); }
  }
  if (created) return <section className="page-view report-success"><div className="success-mark"><Check size={30} /></div><p className="eyebrow">REPORT RECEIVED</p><h1>{created.case_code}</h1><p>Your photos and location are saved for review. No AI or inspection decision has been applied.</p><div className="success-actions"><NavLink className="uploader-primary" to={`/my-reports/${created.id}`}>View my report</NavLink><NavLink className="uploader-secondary" to="/dashboard">Back to dashboard</NavLink></div></section>;
  return <section className="page-view report-page"><div className="report-heading"><p className="eyebrow">NEW UPLOADER REPORT</p><h1>Create dump report</h1><p>Upload 3–5 photos of the same location, confirm where they were taken, and send them for review.</p></div><div className="flow-steps">{["Photos", "Location", "Waste type", "Review"].map((label, index) => <span className={step === index + 1 ? "active" : step > index + 1 ? "complete" : ""} key={label}><b>{index + 1}</b>{label}</span>)}</div>{error && <div className="uploader-alert">{error}</div>}
    {step === 1 && <div className="report-panel"><h2>Show us the site</h2><p className="panel-copy">Choose 3–5 clear angles showing the waste and its surroundings. These photos stay private.</p><div className="photo-grid">{previews.map((preview, index) => <div className="photo-preview" key={preview.url}><img src={preview.url} alt={preview.file.name} /><button type="button" onClick={() => removePhoto(index)} aria-label={`Remove ${preview.file.name}`}><X size={15} /></button><span>{preview.file.name}</span></div>)}{previews.length < 5 && <label className="photo-add"><Upload size={25} /><strong>{previews.length ? "Add another photo" : "Choose photos"}</strong><span>JPEG, PNG, or WebP · 10 MB max</span><input type="file" accept="image/jpeg,image/png,image/webp" multiple onChange={chooseFiles} /></label>}</div><div className="report-actions"><button className="uploader-primary" onClick={next}>Continue <ArrowLeft className="turn-right" size={16} /></button></div></div>}
    {step === 2 && <div className="report-panel"><h2>Confirm the location</h2><p className="panel-copy">WasteWatch uses GPS from your photos when available. Otherwise, allow your device location to place the report.</p><div className={`location-confirm ${latitude && longitude ? "located" : ""}`}><MapPin size={28} /><div><strong>{latitude && longitude ? "Location ready" : "Location needed"}</strong><span>{locationSource || "No GPS location selected yet"}</span>{latitude && longitude && <small>{Number(latitude).toFixed(5)}, {Number(longitude).toFixed(5)}</small>}</div>{(!latitude || !longitude) && <button className="uploader-primary" type="button" onClick={locateDevice} disabled={locating}>{locating ? "Finding device..." : "Use device location"}</button>}</div><div className="street-note"><MapPin size={20} /><div><strong>Street View preview unavailable</strong><p>Google Maps is not configured in this project yet. The report can continue with your confirmed GPS location.</p></div></div><div className="report-actions"><button className="uploader-secondary" onClick={() => setStep(1)}>Back</button><button className="uploader-primary" onClick={next}>Continue <ArrowLeft className="turn-right" size={16} /></button></div></div>}
    {step === 3 && <div className="report-panel"><h2>What kind of waste is this?</h2><p className="panel-copy">This is your observation, not an AI-confirmed classification.</p><label className="select-field">Waste type<select value={category} onChange={(event) => setCategory(event.target.value)}>{categories.map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label><label className="select-field">Optional note<textarea value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Nearby landmarks, access, or anything that may help a reviewer." maxLength={1000} /></label><div className="report-actions"><button className="uploader-secondary" onClick={() => setStep(2)}>Back</button><button className="uploader-primary" onClick={next}>Review report <ArrowLeft className="turn-right" size={16} /></button></div></div>}
    {step === 4 && <form className="report-panel" onSubmit={submit}><h2>Review and submit</h2><div className="review-strip">{previews.map((preview) => <img key={preview.url} src={preview.url} alt="Selected report" />)}</div><dl className="review-facts"><dt>Waste type</dt><dd>{categoryLabel(category)}</dd><dt>Location</dt><dd>{latitude}, {longitude}</dd><dt>Street View</dt><dd>Unavailable, report can continue</dd><dt>Description</dt><dd>{description || "No description added"}</dd></dl><div className="report-actions"><button type="button" className="uploader-secondary" onClick={() => setStep(3)}>Back</button><button className="uploader-primary" disabled={pending}>{pending ? "Submitting..." : "Submit report"}</button></div></form>}
  </section>;
}

export function UploaderReportDetailsPage() {
  const { caseId } = useParams(); const [report, setReport] = useState<Report | null>(null); const [evidence, setEvidence] = useState<File[]>([]); const [selectedImage, setSelectedImage] = useState<Evidence | null>(null); const [pending, setPending] = useState(false); const [error, setError] = useState("");
  useEffect(() => { fetch(`${apiBase}/api/v1/my/reports/${caseId}`, { credentials: "include" }).then(async (response) => { if (!response.ok) throw new Error((await response.json().catch(() => ({}))).detail || "Report not found"); return response.json(); }).then(setReport).catch((requestError) => setError(requestError instanceof Error ? requestError.message : "Unable to load report.")); }, [caseId]);
  async function uploadEvidence() { if (!caseId || !evidence.length) return; setPending(true); setError(""); const formData = new FormData(); evidence.forEach((file) => formData.append("files", file)); try { const response = await fetch(`${apiBase}/api/v1/my/reports/${caseId}/evidence`, { method: "POST", credentials: "include", body: formData }); const body = await response.json().catch(() => ({})); if (!response.ok) throw new Error(body.detail || "Unable to add evidence."); setReport(body); setEvidence([]); } catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Unable to add evidence."); } finally { setPending(false); } }
  return <section className="page-view report-detail"><NavLink className="back-link" to="/dashboard"><ArrowLeft size={16} /> My reports</NavLink>{error && <div className="uploader-alert">{error}</div>}{report ? <><p className="eyebrow">REPORT DETAIL</p><h1>{report.case_code}</h1><span className={`status-pill status-${report.status}`}>{statusLabel(report.status)}</span><div className="detail-grid"><div><span className="detail-label">Submitted</span><strong>{formatDate(report.created_at)}</strong></div><div><span className="detail-label">Waste type</span><strong>{categoryLabel(report.waste_category)}</strong></div><div><span className="detail-label">Location</span><strong>{report.latitude.toFixed(5)}, {report.longitude.toFixed(5)}</strong></div><div><span className="detail-label">Photos</span><strong>{report.evidence_count} private photos</strong></div></div><div className="evidence-gallery"><div className="evidence-gallery-head"><div><p className="eyebrow">SUBMITTED EVIDENCE</p><h2>Report photos</h2></div><span>{report.evidence_count} images</span></div>{report.evidence?.length ? <div className="evidence-grid">{report.evidence.map((item) => <EvidencePhoto key={item.id} item={item} onOpen={() => setSelectedImage(item)} />)}</div> : <div className="evidence-empty">No submitted images are available.</div>}</div>{report.status === "needs_more_evidence" && <div className="evidence-upload"><strong>Add requested evidence</strong><p>Upload up to five additional JPEG, PNG, or WebP photos.</p><input type="file" accept="image/jpeg,image/png,image/webp" multiple onChange={(event) => setEvidence(Array.from(event.target.files || []))} /><button className="uploader-primary" disabled={pending || !evidence.length} onClick={() => void uploadEvidence()}>{pending ? "Uploading..." : "Upload evidence"}</button></div>}<div className="street-note"><MapPin size={20} /><div><strong>What happens next</strong><p>An admin or inspector reviews the submitted evidence. You cannot change official case status or inspection decisions.</p></div></div>{selectedImage && <EvidenceLightbox item={selectedImage} onClose={() => setSelectedImage(null)} />}</> : !error && <div className="uploader-empty">Loading report...</div>}</section>;
}

function EvidencePhoto({ item, onOpen }: { item: Evidence; onOpen: () => void }) { const [src, setSrc] = useState(""); useEffect(() => { let active = true; fetch(`${apiBase}${item.url}`, { credentials: "include" }).then((response) => response.blob()).then((blob) => { if (active) setSrc(URL.createObjectURL(blob)); }).catch(() => undefined); return () => { active = false; }; }, [item.url]); return <button className="evidence-photo" onClick={onOpen} type="button">{src ? <img src={src} alt={item.original_filename} /> : <span>Loading image...</span>}<small>{item.original_filename}</small></button>; }
function EvidenceLightbox({ item, onClose }: { item: Evidence; onClose: () => void }) { const [src, setSrc] = useState(""); useEffect(() => { fetch(`${apiBase}${item.url}`, { credentials: "include" }).then((response) => response.blob()).then((blob) => setSrc(URL.createObjectURL(blob))).catch(() => undefined); }, [item.url]); return <div className="evidence-lightbox" role="dialog" aria-modal="true" onClick={onClose}><div onClick={(event) => event.stopPropagation()}><button className="lightbox-close" onClick={onClose} type="button">Close</button>{src && <img src={src} alt={item.original_filename} />}<strong>{item.original_filename}</strong></div></div>; }
