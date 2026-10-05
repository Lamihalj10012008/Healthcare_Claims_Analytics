import { useState } from 'react'

export default function FeatureTable({ results, onSelect }) {
	const [sort, setSort] = useState('p_value')
	const sorted = [...results].sort((left, right) => sort === 'feature' ? left.feature.localeCompare(right.feature) : left[sort] - right[sort])
	return <div className="table-wrap"><div className="table-tools"><span className="muted">Sort results</span><select value={sort} onChange={event => setSort(event.target.value)}><option value="p_value">p-value</option><option value="chi_square">Chi-square</option><option value="feature">Feature name</option></select></div><table><thead><tr><th>Feature</th><th>Chi-square</th><th>p-value</th><th>df</th><th>Status</th></tr></thead><tbody>{sorted.map(item => <tr key={item.feature} onClick={() => onSelect?.(item.feature)}><td className="feature-name">{item.feature}</td><td>{item.chi_square.toFixed(3)}</td><td>{item.p_value < 0.001 ? '< 0.001' : item.p_value.toFixed(4)}</td><td>{item.degrees_of_freedom}</td><td><span className={`badge ${item.significant ? 'significant' : 'neutral'}`}>{item.significant ? 'SIGNIFICANT' : 'NOT SIGNIFICANT'}</span></td></tr>)}</tbody></table></div>
}
