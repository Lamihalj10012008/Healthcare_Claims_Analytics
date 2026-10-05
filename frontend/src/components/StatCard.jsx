import { ArrowUpRight } from 'lucide-react'
export default function StatCard({ label, value, note, tone = '' }) { return <div className={`stat-card ${tone}`}><div className="stat-label">{label}<ArrowUpRight size={15} /></div><strong>{value}</strong><span>{note}</span></div> }
