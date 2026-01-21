"""
Scheduled Auto-Organization System for FileOrganizer Pro
Enables automatic file organization on a schedule

Author: David - JSMS Academy
License: Proprietary
"""

import schedule
import time
import threading
import json
from pathlib import Path
from datetime import datetime, time as dt_time
from typing import List, Dict, Callable, Optional
from enum import Enum


class ScheduleFrequency(Enum):
    """Frequency options for scheduled jobs"""
    DAILY = "daily"
    WEEKLY = "weekly"
    HOURLY = "hourly"
    CUSTOM = "custom"


class ScheduledJob:
    """Represents a scheduled organization job"""

    def __init__(self, job_id: str, name: str, frequency: ScheduleFrequency,
                 time_str: str, source_path: Path, config: Dict):
        self.job_id = job_id
        self.name = name
        self.frequency = frequency
        self.time_str = time_str  # Format: "HH:MM" or "Monday 14:30"
        self.source_path = Path(source_path)
        self.config = config  # Organization settings
        self.enabled = True
        self.last_run = None
        self.next_run = None
        self.total_runs = 0
        self.created_at = datetime.now()

    def to_dict(self) -> Dict:
        """Serialize to dictionary"""
        return {
            'job_id': self.job_id,
            'name': self.name,
            'frequency': self.frequency.value,
            'time': self.time_str,
            'source_path': str(self.source_path),
            'config': self.config,
            'enabled': self.enabled,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'total_runs': self.total_runs,
            'created_at': self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ScheduledJob':
        """Deserialize from dictionary"""
        job = cls(
            data['job_id'],
            data['name'],
            ScheduleFrequency(data['frequency']),
            data['time'],
            data['source_path'],
            data['config']
        )
        job.enabled = data.get('enabled', True)
        job.total_runs = data.get('total_runs', 0)

        if data.get('last_run'):
            job.last_run = datetime.fromisoformat(data['last_run'])
        if data.get('next_run'):
            job.next_run = datetime.fromisoformat(data['next_run'])
        if data.get('created_at'):
            job.created_at = datetime.fromisoformat(data['created_at'])

        return job


class OrganizationScheduler:
    """
    Manages scheduled automatic file organization

    Features:
    - Daily, weekly, hourly scheduling
    - Multiple concurrent jobs
    - Persistent job storage
    - Error handling and retry
    - Job status monitoring
    """

    def __init__(self, jobs_file: Optional[Path] = None, callback: Optional[Callable] = None):
        self.jobs_file = jobs_file or Path("./scheduled_jobs.json")
        self.callback = callback  # Function to call when organizing
        self.jobs: Dict[str, ScheduledJob] = {}
        self.is_running = False
        self.scheduler_thread = None

        # Load persisted jobs
        self.load_jobs()

    def add_job(self, name: str, frequency: ScheduleFrequency, time_str: str,
                source_path: Path, config: Dict) -> str:
        """
        Add a new scheduled job

        Args:
            name: User-friendly name
            frequency: How often to run
            time_str: When to run (format depends on frequency)
            source_path: Directory to organize
            config: Organization settings (mode, options, etc.)

        Returns:
            job_id of created job
        """
        job_id = f"job_{int(datetime.now().timestamp())}"

        job = ScheduledJob(job_id, name, frequency, time_str, source_path, config)
        self.jobs[job_id] = job

        # Schedule the job
        self._schedule_job(job)

        # Save to disk
        self.save_jobs()

        return job_id

    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job"""
        if job_id in self.jobs:
            del self.jobs[job_id]
            schedule.clear(job_id)
            self.save_jobs()
            return True
        return False

    def enable_job(self, job_id: str):
        """Enable a job"""
        if job_id in self.jobs:
            self.jobs[job_id].enabled = True
            self._schedule_job(self.jobs[job_id])
            self.save_jobs()

    def disable_job(self, job_id: str):
        """Disable a job (won't run but stays configured)"""
        if job_id in self.jobs:
            self.jobs[job_id].enabled = False
            schedule.clear(job_id)
            self.save_jobs()

    def _schedule_job(self, job: ScheduledJob):
        """Internal: Schedule a job with the schedule library"""
        if not job.enabled:
            return

        def run_job():
            """Wrapper to execute the organization job"""
            try:
                print(f"[Scheduler] Running job: {job.name}")
                job.last_run = datetime.now()
                job.total_runs += 1

                if self.callback:
                    # Call the organization function
                    result = self.callback(job.source_path, job.config)
                    print(f"[Scheduler] Job completed: {result}")
                else:
                    print(f"[Scheduler] No callback configured")

                self.save_jobs()

            except Exception as e:
                print(f"[Scheduler] Job failed: {e}")

        # Schedule based on frequency
        if job.frequency == ScheduleFrequency.DAILY:
            schedule.every().day.at(job.time_str).do(run_job).tag(job.job_id)

        elif job.frequency == ScheduleFrequency.WEEKLY:
            # Format: "Monday 14:30"
            day, time_part = job.time_str.split()
            getattr(schedule.every(), day.lower()).at(time_part).do(run_job).tag(job.job_id)

        elif job.frequency == ScheduleFrequency.HOURLY:
            # Format: ":30" (minute of hour)
            minutes = int(job.time_str.split(':')[1])
            schedule.every().hour.at(f":{minutes:02d}").do(run_job).tag(job.job_id)

        # Update next run time
        job.next_run = self._get_next_run_time(job)

    def _get_next_run_time(self, job: ScheduledJob) -> Optional[datetime]:
        """Get the next scheduled run time for a job"""
        # This is a simplified version - schedule library has internal tracking
        jobs = schedule.get_jobs(job.job_id)
        if jobs:
            return jobs[0].next_run
        return None

    def start(self):
        """Start the scheduler in a background thread"""
        if self.is_running:
            return

        self.is_running = True

        def run_scheduler():
            """Background thread function"""
            print("[Scheduler] Started")
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)
            print("[Scheduler] Stopped")

        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()

    def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=2)

    def get_all_jobs(self) -> List[ScheduledJob]:
        """Get list of all scheduled jobs"""
        return list(self.jobs.values())

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get detailed status of a job"""
        if job_id not in self.jobs:
            return None

        job = self.jobs[job_id]
        return {
            'job_id': job.job_id,
            'name': job.name,
            'enabled': job.enabled,
            'frequency': job.frequency.value,
            'next_run': job.next_run.strftime('%Y-%m-%d %H:%M:%S') if job.next_run else 'Not scheduled',
            'last_run': job.last_run.strftime('%Y-%m-%d %H:%M:%S') if job.last_run else 'Never',
            'total_runs': job.total_runs,
            'source_path': str(job.source_path)
        }

    def save_jobs(self):
        """Persist jobs to disk"""
        try:
            data = {
                'version': '1.0',
                'saved_at': datetime.now().isoformat(),
                'jobs': {job_id: job.to_dict() for job_id, job in self.jobs.items()}
            }

            with open(self.jobs_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"Warning: Could not save scheduled jobs: {e}")

    def load_jobs(self):
        """Load persisted jobs"""
        if not self.jobs_file.exists():
            return

        try:
            with open(self.jobs_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for job_id, job_data in data.get('jobs', {}).items():
                job = ScheduledJob.from_dict(job_data)
                self.jobs[job_id] = job

                # Re-schedule enabled jobs
                if job.enabled:
                    self._schedule_job(job)

            print(f"[Scheduler] Loaded {len(self.jobs)} jobs")

        except Exception as e:
            print(f"Warning: Could not load scheduled jobs: {e}")


# Example usage
if __name__ == "__main__":
    def mock_organize(source_path, config):
        """Mock organization function"""
        print(f"  Organizing: {source_path}")
        print(f"  Config: {config}")
        return {'success': True, 'files': 100}

    # Create scheduler
    scheduler = OrganizationScheduler(callback=mock_organize)

    # Add a daily job
    job_id = scheduler.add_job(
        name="Daily Downloads Cleanup",
        frequency=ScheduleFrequency.DAILY,
        time_str="02:00",  # 2 AM
        source_path=Path("C:/Users/Downloads"),
        config={'mode': 'category', 'skip_duplicates': True}
    )

    print(f"Created job: {job_id}")

    # Check status
    status = scheduler.get_job_status(job_id)
    print(f"Status: {status}")

    # Start scheduler (in real app, this runs continuously)
    print("\nScheduler ready! Jobs will run at scheduled times.")
    print("In production, call scheduler.start() to begin.")
