; CheckPause - Inno Setup 6.3+ script
;
; Normally invoked by build_exe.ps1. To build manually:
;   1) .venv\Scripts\python.exe -m PyInstaller CheckPause.spec --noconfirm
;   2) ISCC.exe /DAppVersion=<version> installer\CheckPause.iss
;
; Requires dist\CheckPause\ to already exist (PyInstaller onedir output).
;
; This file is intentionally ASCII-only: ISCC and Windows PowerShell 5.1 both
; mishandle non-ASCII scripts unless they carry a BOM.

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

#define AppVersionQuad AppVersion + ".0"

#define AppName "CheckPause"
#define AppPublisher "CometZZZ"
#define AppExeName "CheckPause.exe"
#define DistDir "..\dist\CheckPause"

[Setup]
; Keep this GUID stable forever - it is the identity used for upgrades/uninstall.
AppId={{7C3E1D92-4B6A-4E2F-9C8D-3A5B7E1F6D40}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
VersionInfoVersion={#AppVersionQuad}
VersionInfoCompany={#AppPublisher}
VersionInfoDescription={#AppName} Setup
VersionInfoProductName={#AppName}
VersionInfoProductVersion={#AppVersionQuad}

; Qt6 needs Windows 10+, so fail early instead of crashing after install.
MinVersion=10.0
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\{#AppExeName}

; Setup wizard icon, compiled from the same source as the exe icon.
SetupIconFile=..\assets\app.ico

; Per-user install: no UAC prompt, which matters for non-technical users.
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

DisableProgramGroupPage=yes
AllowNoIcons=yes
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern

; Close a running CheckPause so the update can overwrite its files.
; RestartApplications is off: the [Run] entry below already offers a launch,
; and restarting here would start a second copy.
CloseApplications=yes
RestartApplications=no

; The installer is written into dist\ next to the portable folder, so the whole
; distributable lives in one place.
OutputDir=..\dist
OutputBaseFilename={#AppName}_Setup_{#AppVersion}

[Languages]
; Inno Setup does not bundle the Simplified Chinese translation, so it is kept
; in this repo (installer\languages\ChineseSimplified.isl). Official source:
; https://jrsoftware.org/files/istrans/  (maintained by Zhenghan Yang)
#ifdef ChineseIslBundled
Name: "chinesesimplified"; MessagesFile: "languages\ChineseSimplified.isl"
#else
  #ifdef ChineseIslCompiler
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
  #endif
#endif
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
