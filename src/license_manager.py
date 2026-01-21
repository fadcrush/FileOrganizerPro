"""
License Management System for FileOrganizer Pro

Handles license validation, activation, and trial periods.
"""

import hashlib
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict


class LicenseManager:
    """
    Manages software licensing and activation

    Features:
    - License key validation
    - Trial period (14 days)
    - Activation persistence
    - Offline validation
    """

    def __init__(self, license_file: Optional[Path] = None):
        """
        Initialize license manager

        Args:
            license_file: Path to license storage file
        """
        self.license_file = license_file or (Path.home() / '.fileorganizer_license.json')
        self.license_data = self._load_license()

    def _load_license(self) -> Dict:
        """Load license data from file"""
        if self.license_file.exists():
            try:
                with open(self.license_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_license(self):
        """Save license data to file"""
        with open(self.license_file, 'w') as f:
            json.dump(self.license_data, f, indent=2)

    def _generate_key_hash(self, license_key: str) -> str:
        """Generate hash from license key"""
        # Simple validation - replace with your own algorithm
        return hashlib.sha256(license_key.encode()).hexdigest()

    def is_trial_active(self) -> bool:
        """Check if trial period is still active"""
        if 'trial_start' not in self.license_data:
            # First run - start trial
            self.license_data['trial_start'] = datetime.now().isoformat()
            self._save_license()
            return True

        trial_start = datetime.fromisoformat(self.license_data['trial_start'])
        trial_end = trial_start + timedelta(days=14)  # 14-day trial

        return datetime.now() < trial_end

    def get_trial_days_remaining(self) -> int:
        """Get number of trial days remaining"""
        if 'trial_start' not in self.license_data:
            return 14

        trial_start = datetime.fromisoformat(self.license_data['trial_start'])
        trial_end = trial_start + timedelta(days=14)
        days_remaining = (trial_end - datetime.now()).days

        return max(0, days_remaining)

    def validate_license_key(self, license_key: str) -> bool:
        """
        Validate license key format and checksum

        Args:
            license_key: License key to validate

        Returns:
            True if valid, False otherwise
        """
        # Expected format: XXXX-XXXX-XXXX-XXXX
        if not license_key or len(license_key) != 19:
            return False

        parts = license_key.split('-')
        if len(parts) != 4:
            return False

        # Each part should be 4 characters
        if not all(len(part) == 4 for part in parts):
            return False

        # Simple checksum validation
        # Replace this with your own algorithm or server validation
        key_hash = self._generate_key_hash(license_key)

        # Example: Check against hardcoded valid keys or server
        # For production, validate against your license server

        return True  # Placeholder - implement your validation

    def activate(self, license_key: str) -> bool:
        """
        Activate software with license key

        Args:
            license_key: Valid license key

        Returns:
            True if activation successful
        """
        if not self.validate_license_key(license_key):
            return False

        self.license_data['license_key'] = license_key
        self.license_data['activated'] = True
        self.license_data['activation_date'] = datetime.now().isoformat()
        self._save_license()

        return True

    def is_activated(self) -> bool:
        """Check if software is activated with valid license"""
        if self.license_data.get('activated', False):
            # Verify license key is still valid
            license_key = self.license_data.get('license_key', '')
            return self.validate_license_key(license_key)
        return False

    def is_valid(self) -> bool:
        """
        Check if software can be used (activated or trial active)

        Returns:
            True if user can use software
        """
        return self.is_activated() or self.is_trial_active()

    def get_status(self) -> Dict:
        """
        Get current license status

        Returns:
            Dictionary with license status information
        """
        return {
            'activated': self.is_activated(),
            'trial_active': self.is_trial_active(),
            'trial_days_remaining': self.get_trial_days_remaining(),
            'can_use': self.is_valid(),
            'license_key': self.license_data.get('license_key', 'TRIAL'),
        }

    def deactivate(self):
        """Deactivate license (for license transfer)"""
        self.license_data = {}
        self._save_license()


# Example usage in main app
if __name__ == '__main__':
    license_mgr = LicenseManager()

    status = license_mgr.get_status()
    print(f"License Status: {status}")

    if not status['can_use']:
        print("Software cannot be used. License expired or invalid.")
    elif status['trial_active']:
        print(f"Trial active. {status['trial_days_remaining']} days remaining.")
    else:
        print(f"Licensed to: {status['license_key']}")
