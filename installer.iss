; GST Billing Suite — Inno Setup Installer Script
; Download Inno Setup from: https://jrsoftware.org/isdl.php
; Open this file in Inno Setup Compiler and click Build (F9)

[Setup]
AppName=GST Billing Suite
AppVersion=3.0
AppPublisher=GST Billing Suite
DefaultDirName={autopf}\GST Billing Suite
DefaultGroupName=GST Billing Suite
UninstallDisplayIcon={app}\GSTBillingSuite.exe
SetupIconFile=assets\app.ico
OutputDir=installer_output
OutputBaseFilename=GST-Billing-Suite-Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
; All portable app files
Source: "GST-Billing-Suite-Portable\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\GST Billing Suite"; Filename: "{app}\GSTBillingSuite.exe"; WorkingDir: "{app}"; Comment: "Launch GST Billing Suite"
Name: "{group}\Uninstall GST Billing Suite"; Filename: "{uninstallexe}"
Name: "{autodesktop}\GST Billing Suite"; Filename: "{app}\GSTBillingSuite.exe"; WorkingDir: "{app}"; Comment: "Launch GST Billing Suite"; Tasks: desktopicon

[Run]
Filename: "{app}\GSTBillingSuite.exe"; Description: "Launch GST Billing Suite now"; Flags: nowait postinstall skipifsilent
