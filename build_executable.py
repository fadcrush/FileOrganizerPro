"""
Build script for creating FileOrganizer Pro executable

Creates standalone executable with PyInstaller for distribution.
"""

import os
import sys
import subprocess
from pathlib import Path


def build_executable():
    """Build standalone executable with PyInstaller"""

    print("=" * 60)
    print("FileOrganizer Pro - Build Script")
    print("=" * 60)
    print()

    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("❌ PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller installed")
        print()

    # Build configuration
    app_name = "FileOrganizerPro"
    main_script = "file_organizer_pro_scifi.py"
    icon_file = "assets/icon.ico" if Path("assets/icon.ico").exists() else None

    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--name", app_name,
        "--onefile",  # Single executable
        "--windowed",  # No console window
        "--clean",  # Clean build

        # Add icon if exists
        *(["--icon", icon_file] if icon_file else []),

        # Add data directories
        "--add-data", f"src{os.pathsep}src",

        # Hidden imports (ensure all modules included)
        "--hidden-import", "PIL._tkinter_finder",
        "--hidden-import", "tkinter",
        "--hidden-import", "tkinter.ttk",

        # Exclude unnecessary modules (reduce size)
        "--exclude-module", "matplotlib",
        "--exclude-module", "numpy",
        "--exclude-module", "scipy",

        # UPX compression (if available)
        # "--upx-dir", "path/to/upx",  # Uncomment if you have UPX

        main_script
    ]

    print("Building executable...")
    print(f"Command: {' '.join(cmd)}")
    print()

    try:
        subprocess.check_call(cmd)
        print()
        print("=" * 60)
        print("✓ Build successful!")
        print("=" * 60)
        print()
        print(f"Executable location: dist/{app_name}.exe")
        print()
        print("Next steps:")
        print("1. Test the executable: dist/{}.exe".format(app_name))
        print("2. Create installer with Inno Setup (see installer_script.iss)")
        print("3. Test on clean Windows machine")
        print("4. Prepare for distribution")
        print()

    except subprocess.CalledProcessError as e:
        print()
        print("=" * 60)
        print("❌ Build failed!")
        print("=" * 60)
        print()
        print(f"Error: {e}")
        print()
        print("Common fixes:")
        print("- Ensure all imports are correct")
        print("- Check that all dependencies are installed")
        print("- Try cleaning build: rm -rf build dist *.spec")
        sys.exit(1)


def create_installer_script():
    """Create Inno Setup script for Windows installer"""

    script_content = """
; FileOrganizer Pro - Inno Setup Script
; Creates Windows installer package

#define MyAppName "FileOrganizer Pro"
#define MyAppVersion "4.0.0"
#define MyAppPublisher "JSMS Academy"
#define MyAppURL "https://yourwebsite.com"
#define MyAppExeName "FileOrganizerPro.exe"

[Setup]
AppId={{YOUR-GUID-HERE}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE.txt
OutputDir=installer_output
OutputBaseFilename=FileOrganizerPro_Setup_v{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"
Name: "{group}\\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Name: "{app}\\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
  MsgBox('Welcome to FileOrganizer Pro Setup!' + #13#10 + #13#10 +
         'This wizard will install FileOrganizer Pro on your computer.',
         mbInformation, MB_OK);
end;
"""

    with open("installer_script.iss", "w") as f:
        f.write(script_content)

    print("✓ Inno Setup script created: installer_script.iss")
    print()


if __name__ == '__main__':
    print()

    # Step 1: Build executable
    build_executable()

    # Step 2: Create installer script
    create_installer_script()

    print("=" * 60)
    print("Build process complete!")
    print("=" * 60)
    print()
