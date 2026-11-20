#define MyAppName "FPV Uhyliant"
#ifndef MyAppVersion
  #define MyAppVersion "2.0.2"
#endif
#define MyAppPublisher "Uhilyant-gg"
#define MyAppExeName "FPV-Uhyliant.exe"
[Setup]
AppId={{D142945E-91C4-49AA-A3D0-D07A41CB7B3A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\FPV Uhyliant
DefaultGroupName=FPV Uhyliant
DisableProgramGroupPage=yes
OutputDir=..\installer-output
OutputBaseFilename=FPV-Uhyliant-Setup-{#MyAppVersion}
SetupIconFile=..\assets\fpv-uhyliant.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
CloseApplications=yes
RestartApplications=no
[Languages]
Name: "ukrainian"; MessagesFile: "compiler:Languages\Ukrainian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
[Tasks]
Name: "desktopicon"; Description: "Створити ярлик на робочому столі"; GroupDescription: "Додаткові ярлики:"; Flags: unchecked
[Files]
Source: "..\dist\FPV-Uhyliant\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{autoprograms}\FPV Uhyliant"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\FPV Uhyliant"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Запустити FPV Uhyliant"; Flags: nowait postinstall skipifsilent
