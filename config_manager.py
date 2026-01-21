"""
Configuration Manager for FileOrganizer Pro 2.0
Handles saving and loading user preferences
"""

import json
from pathlib import Path
import os

class ConfigManager:
    """Manages application configuration and user preferences"""
    
    def __init__(self, config_file=None):
        if config_file:
            self.config_file = Path(config_file)
        else:
            # Default location: user's home directory
            config_dir = Path.home() / '.fileorganizer_pro'
            config_dir.mkdir(exist_ok=True)
            self.config_file = config_dir / 'config.json'
        
        self.config = self.load_config()
    
    def get_default_config(self):
        """Return default configuration"""
        return {
            'version': '2.0.0',
            'preferences': {
                'operation_mode': 'move',  # move or copy
                'organization_mode': 'category',  # category, year, or category_year
                'organize_by_year': True,
                'skip_duplicates': True,
                'create_backup': True,
                'dry_run': True,
                'apply_folder_icons': True,
                'auto_save_reports': True,
                'show_notifications': True,
                'theme': 'light'  # light or dark
            },
            'categories': {
                'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', 
                          '.svg', '.ico', '.heic', '.heif', '.raw', '.cr2', '.nef', '.arw', 
                          '.dng', '.orf', '.psd'],
                'Videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', 
                          '.mpg', '.mpeg', '.3gp', '.ogv'],
                'Documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.tex', '.wpd', 
                             '.md', '.markdown'],
                'Spreadsheets': ['.xls', '.xlsx', '.csv', '.ods', '.xlsm', '.xlsb'],
                'Presentations': ['.ppt', '.pptx', '.odp', '.key'],
                'Audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus', 
                         '.aiff', '.ape'],
                'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso', 
                            '.dmg', '.pkg'],
                'Code': ['.py', '.js', '.java', '.cpp', '.c', '.h', '.cs', '.php', '.rb', 
                        '.go', '.rs', '.swift', '.kt', '.ts', '.html', '.css', '.scss', '.sql',
                        '.sh', '.bat', '.ps1', '.r', '.m', '.scala', '.lua'],
                'Executables': ['.exe', '.msi', '.app', '.deb', '.rpm', '.apk', '.dmg'],
                'Fonts': ['.ttf', '.otf', '.woff', '.woff2', '.eot'],
                'Others': []
            },
            'recent_paths': [],
            'max_recent_paths': 10,
            'backup_settings': {
                'backup_location': 'default',  # 'default' or custom path
                'max_backups': 5,
                'compress_backups': False
            },
            'performance': {
                'max_threads': 4,
                'chunk_size': 4096,
                'progress_update_interval': 10
            },
            'advanced': {
                'follow_symlinks': False,
                'preserve_timestamps': True,
                'verify_copies': False,
                'log_level': 'INFO'  # DEBUG, INFO, WARNING, ERROR
            }
        }
    
    def load_config(self):
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                # Merge with defaults to handle new settings
                default_config = self.get_default_config()
                return self.merge_configs(default_config, loaded_config)
            
            except Exception as e:
                print(f"Error loading config: {e}")
                return self.get_default_config()
        else:
            return self.get_default_config()
    
    def merge_configs(self, default, loaded):
        """Recursively merge loaded config with defaults"""
        result = default.copy()
        
        for key, value in loaded.items():
            if key in result:
                if isinstance(value, dict) and isinstance(result[key], dict):
                    result[key] = self.merge_configs(result[key], value)
                else:
                    result[key] = value
            else:
                result[key] = value
        
        return result
    
    def save_config(self):
        """Save configuration to file"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            
            return True
        
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get(self, key, default=None):
        """Get configuration value using dot notation (e.g., 'preferences.theme')"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key, value):
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def add_recent_path(self, path):
        """Add path to recent paths list"""
        recent = self.get('recent_paths', [])
        
        # Remove if already exists
        if path in recent:
            recent.remove(path)
        
        # Add to front
        recent.insert(0, path)
        
        # Limit list size
        max_recent = self.get('max_recent_paths', 10)
        recent = recent[:max_recent]
        
        self.set('recent_paths', recent)
        self.save_config()
    
    def get_recent_paths(self):
        """Get list of recent paths"""
        return self.get('recent_paths', [])
    
    def add_custom_extension(self, category, extension):
        """Add custom file extension to category"""
        categories = self.get('categories', {})
        
        if category not in categories:
            categories[category] = []
        
        # Ensure extension starts with dot
        if not extension.startswith('.'):
            extension = '.' + extension
        
        extension = extension.lower()
        
        if extension not in categories[category]:
            categories[category].append(extension)
            self.set('categories', categories)
            self.save_config()
            return True
        
        return False
    
    def remove_custom_extension(self, category, extension):
        """Remove file extension from category"""
        categories = self.get('categories', {})
        
        if category in categories:
            # Ensure extension starts with dot
            if not extension.startswith('.'):
                extension = '.' + extension
            
            extension = extension.lower()
            
            if extension in categories[category]:
                categories[category].remove(extension)
                self.set('categories', categories)
                self.save_config()
                return True
        
        return False
    
    def add_custom_category(self, category_name, extensions):
        """Add a new custom category"""
        categories = self.get('categories', {})
        
        if category_name in categories:
            return False  # Category already exists
        
        # Ensure all extensions start with dot
        formatted_extensions = []
        for ext in extensions:
            if not ext.startswith('.'):
                ext = '.' + ext
            formatted_extensions.append(ext.lower())
        
        categories[category_name] = formatted_extensions
        self.set('categories', categories)
        self.save_config()
        return True
    
    def export_config(self, export_path):
        """Export configuration to file"""
        try:
            export_path = Path(export_path)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            
            return True
        
        except Exception as e:
            print(f"Error exporting config: {e}")
            return False
    
    def import_config(self, import_path):
        """Import configuration from file"""
        try:
            import_path = Path(import_path)
            
            if not import_path.exists():
                return False
            
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # Merge with defaults
            default_config = self.get_default_config()
            self.config = self.merge_configs(default_config, imported_config)
            
            self.save_config()
            return True
        
        except Exception as e:
            print(f"Error importing config: {e}")
            return False
    
    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self.config = self.get_default_config()
        self.save_config()


# Test the config manager
if __name__ == "__main__":
    config = ConfigManager()
    print(f"Config file: {config.config_file}")
    print(f"Operation mode: {config.get('preferences.operation_mode')}")
    print(f"Recent paths: {config.get_recent_paths()}")
    
    # Test adding recent path
    config.add_recent_path("/test/path/1")
    config.add_recent_path("/test/path/2")
    print(f"After adding paths: {config.get_recent_paths()}")