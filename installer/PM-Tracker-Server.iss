#define MyAppName "PM Tracker Server"
#define MyAppVersion "1.0.0"
#define MyAppExeName "PM Tracker.exe"

[Setup]
AppId={{2DA91ED5-9331-4F5D-8EF0-EE3D4272677E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={commonappdata}\PM Tracker
DisableProgramGroupPage=yes
PrivilegesRequired=admin
OutputDir=installer-output
OutputBaseFilename=PM-Tracker-Server-Setup
Compression=lzma
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
Source: "..\dist\PM Tracker.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\site_config.example.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\PM_Tracker_Import_Template.xlsx"; DestDir: "{app}"; Flags: ignoreversion uninsneveruninstall
Source: "..\server\install-server.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\server\uninstall-server.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\deployments\EZ-WMF\README.md"; DestDir: "{app}\docs"; DestName: "EZ-WMF-DEPLOYMENT.md"; Flags: ignoreversion
Source: "..\deployments\EZ-WMF\IT_REVIEW.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "..\deployments\EZ-WMF\MIGRATION.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "..\deployments\EZ-WMF\site_config.EZ.example.json"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "..\deployments\EZ-WMF\site_config.WMF.example.json"; DestDir: "{app}\docs"; Flags: ignoreversion

[Run]
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\install-server.ps1"" -InstallDir ""{app}"""; Flags: runhidden waituntilterminated

[UninstallRun]
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\uninstall-server.ps1"" -InstallDir ""{app}"""; Flags: runhidden waituntilterminated
