"""
Create test package for friends - FIXED VERSION

Works around PyInstaller + Anaconda issues.
"""

import os
import sys
import subprocess
from pathlib import Path
import zipfile
import shutil


def check_and_fix_pathlib():
    """Remove obsolete pathlib package if present"""

    print("Checking for PyInstaller compatibility issues...")
    print()

    # Check if pathlib package exists (it shouldn't - it's built-in since Python 3.4)
    try:
        import pathlib
        pathlib_location = pathlib.__file__

        # If pathlib has a __file__ attribute, it's the old backport package
        if pathlib_location and 'site-packages' in pathlib_location:
            print("⚠ Found obsolete pathlib backport package")
            print(f"   Location: {pathlib_location}")
            print()
            print("Removing it...")

            # Use conda to remove it
            try:
                subprocess.check_call(['conda', 'remove', '-y', 'pathlib'])
                print("✓ Removed obsolete pathlib package")
                print()
            except:
                print("❌ Could not auto-remove. Please run manually:")
                print("   conda remove pathlib")
                print()
                return False
    except ImportError:
        # Good - pathlib is built-in, not installed as package
        pass

    return True


def create_simple_spec_file():
    """
    Create PyInstaller spec file manually
    This gives more control than command-line approach
    """

    spec_content = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['file_organizer_pro_scifi.py'],
    pathex=[],
    binaries=[],
    datas=[('src', 'src')],
    hiddenimports=['PIL._tkinter_finder'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'pytest',
        'IPython',
        'jupyter',
        'notebook'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FileOrganizerPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""

    with open('FileOrganizerPro.spec', 'w') as f:
        f.write(spec_content)

    print("✓ Created PyInstaller spec file")
    return True


def build_with_spec():
    """Build using spec file instead of command line"""

    print()
    print("Building executable (this takes 2-3 minutes)...")
    print("Please wait...")
    print()

    try:
        # Build using spec file
        subprocess.check_call([
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            'FileOrganizerPro.spec'
        ])

        print()
        print("✓ Executable created successfully!")
        print()
        return True

    except subprocess.CalledProcessError as e:
        print()
        print("❌ Build failed!")
        print()
        print("Error:", str(e))
        return False


def create_readme():
    """Create simple README for testers"""

    readme_content = """
FileOrganizer Pro - Beta Test Version
======================================

Thanks for testing! Here's how to get started:

QUICK START (30 seconds)
------------------------

1. Run FileOrganizerPro.exe
   (If Windows blocks it, click "More info" -> "Run anyway")

2. Press Ctrl+K to open command palette
   Type "settings" to see theme options

3. Try organizing files:
   - Click "Organize" tab
   - Browse to a test folder
   - Enable "DRY RUN" (preview mode)
   - Click "Start Organization"

WHAT TO TEST
------------

Please try these features:

[✓] App launches without errors
[✓] Can switch Dark/Light theme (Settings)
[✓] Can search for files (Search tab)
[✓] Can organize files with DRY RUN
[✓] Settings save between sessions

FEEDBACK NEEDED
---------------

Please tell me:

1. Did it work on your computer?
2. Was it useful to you?
3. Would you pay $49 for this?
4. What did you like/dislike?
5. Any bugs or crashes?

KNOWN ISSUES
------------

- First launch: 10-15 seconds (normal)
- Windows might show "Unknown Publisher" warning (safe)
- Some antivirus may flag it (false positive)

Send feedback to: [YOUR EMAIL HERE]

Thanks for helping! 🚀
"""

    Path('dist').mkdir(exist_ok=True)

    with open("dist/README_BETA.txt", "w") as f:
        f.write(readme_content)

    print("✓ README created")


def create_test_zip():
    """Create ZIP package for distribution"""

    print()
    print("Creating ZIP package...")

    zip_name = "FileOrganizerPro_BetaTest.zip"

    # Check if executable exists
    exe_path = Path("dist/FileOrganizerPro.exe")
    if not exe_path.exists():
        print(f"❌ Executable not found at {exe_path}")
        return None

    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add executable
        zipf.write("dist/FileOrganizerPro.exe", "FileOrganizerPro.exe")

        # Add README
        if Path("dist/README_BETA.txt").exists():
            zipf.write("dist/README_BETA.txt", "README_BETA.txt")

    # Get file size
    size_mb = os.path.getsize(zip_name) / (1024 * 1024)

    print(f"✓ ZIP created: {zip_name} ({size_mb:.1f} MB)")
    print()

    return zip_name


def print_instructions(zip_file):
    """Print final instructions"""

    print()
    print("=" * 60)
    print("✓ TEST PACKAGE READY!")
    print("=" * 60)
    print()
    print(f"📦 Package: {zip_file}")
    print()
    print("📤 HOW TO SHARE:")
    print()
    print("1. Upload to Google Drive")
    print("   • Go to drive.google.com")
    print("   • Drag and drop the ZIP file")
    print("   • Right-click → Get link → Copy")
    print()
    print("2. OR Upload to WeTransfer (easiest!)")
    print("   • Go to wetransfer.com")
    print("   • Add file")
    print("   • Enter friend's email")
    print("   • Send!")
    print()
    print("3. Send this message to friends:")
    print()
    print("-" * 60)
    print("Hey! Can you test my file organizer app?")
    print()
    print("Download: [PASTE YOUR LINK HERE]")
    print()
    print("Takes 2 minutes:")
    print("1. Extract ZIP")
    print("2. Run FileOrganizerPro.exe")
    print("3. Let me know what you think!")
    print()
    print("Would you pay $49 for this? 😊")
    print("-" * 60)
    print()
    print("💡 TIP: Start with 1-2 tech-savvy friends first!")
    print()


def main():
    """Main build process"""

    print()
    print("=" * 60)
    print("FileOrganizer Pro - Test Package Creator")
    print("=" * 60)
    print()

    # Step 1: Check/fix pathlib issue
    if not check_and_fix_pathlib():
        print()
        print("Please run this command first:")
        print("   conda remove pathlib")
        print()
        print("Then run this script again.")
        return

    # Step 2: Check if PyInstaller is installed
    try:
        import PyInstaller
        print("✓ PyInstaller is installed")
        print()
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller installed")
        print()

    # Step 3: Create spec file
    if not create_simple_spec_file():
        return

    # Step 4: Build executable
    if not build_with_spec():
        print()
        print("Build failed. Common fixes:")
        print()
        print("1. Make sure file_organizer_pro_scifi.py exists")
        print("2. Make sure src/ folder exists")
        print("3. Try running: conda remove pathlib")
        print("4. Try: pip install --upgrade pyinstaller")
        print()
        return

    # Step 5: Create README
    create_readme()

    # Step 6: Create ZIP
    zip_file = create_test_zip()

    if not zip_file:
        print("❌ Failed to create ZIP")
        return

    # Step 7: Print instructions
    print_instructions(zip_file)

    print()
    print("🎉 Done! Ready to share with friends!")
    print()


if __name__ == '__main__':
    main()
