; Inno Setup script for DevOps Tracker
; 1) Build the app first (build.bat) so dist\DevOpsTracker exists
; 2) Open this file in Inno Setup Compiler and press Ctrl+F9 (or run: ISCC installer.iss)
; Output: installer_output\DevOpsTracker-Setup.exe

#define MyAppName "DevOps Tracker"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Harikrishnan Punnasseri"
#define MyAppExe "DevOpsTracker.exe"

[Setup]
AppId={{B7C1E4D2-5A3F-4E8B-9C21-7D6F0A1B2C34}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=DevOpsTracker-Setup
SetupIconFile=app.ico
; Installs for the current user without admin rights; the user can choose "all users" in a dialog
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=installer_output
OutputBaseFilename=DevOpsTracker-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExe}
ArchitecturesInstallIn64BitMode=x64compatible
; Optional extras (uncomment after adding the files next to this script):
; SetupIconFile=app.ico
; LicenseFile=LICENSE.txt

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
Source: "dist\desktop\DevOpsTracker.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\desktop\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExe}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Code]
// Warn (do not block) if the Microsoft Edge WebView2 Runtime is missing.
function WebView2Installed(): Boolean;
var v: String;
begin
  Result :=
    RegQueryStringValue(HKLM, 'SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', v) or
    RegQueryStringValue(HKCU, 'Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', v);
  if Result then Result := (v <> '') and (v <> '0.0.0.0');
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
  if not WebView2Installed() then
    MsgBox('DevOps Tracker needs the Microsoft Edge WebView2 Runtime. It is built into Windows 11 and most updated Windows 10 PCs.' + #13#10 +
           'If the app opens a blank window, install it from: https://developer.microsoft.com/microsoft-edge/webview2/', mbInformation, MB_OK);
end;
