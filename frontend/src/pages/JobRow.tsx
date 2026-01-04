import React from 'react';
import { Job } from './Dashboard';

interface JobRowProps {
  job: Job;
}

// ⚡ Bolt: Memoizing JobRow to prevent unnecessary re-renders on Dashboard poll
const JobRow: React.FC<JobRowProps> = React.memo(({ job }) => {
  return (
    <tr key={job.job_id}>
      <td>{job.project_name}</td>
      <td>{job.job_id}</td>
      <td>{job.result?.target_url || '-'}</td>
      <td>
        <span className={`badge ${job.status}`}>
          {job.status}
        </span>
      </td>
      <td>{new Date(job.created_at).toLocaleString()}</td>
      <td>
        {job.result ? (
          <div style={{ fontSize: '0.8rem' }}>
            {job.result.web_scan && `Web: ${job.result.web_scan.vulnerabilities?.length || 0} `}
            {job.result.nuclei && `Nuclei: ${job.result.nuclei.findings?.length || 0}`}
          </div>
        ) : '-'}
      </td>
    </tr>
  );
});

export default JobRow;
