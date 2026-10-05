export default function UploadBox({ onChange }) { return <input type="file" accept=".csv,text/csv" onChange={event => onChange?.(event.target.files[0])} /> }
