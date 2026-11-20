#define MyAppName "FPV Uhyliant"
#ifndef MyAppVersion
  #define MyAppVersion "2.0.7"
#endif
#define MyAppPublisher "Uhilyant-gg"
#define MyLauncher "FPV-Uhyliant-Launcher.exe"

[Setup]
AppId={{B04099DB-F161-4C00-AE55-24B39D95744A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\FPV Uhyliant
DefaultGroupName=FPV Uhyliant
DisableProgramGroupPage=yes
UsePreviousAppDir=no
OutputDir=..\installer-output
OutputBaseFilename=FPV-Uhyliant-Setup-{#MyAppVersion}
SetupIconFile=..\assets\fpv-uhyliant.ico
UninstallDisplayIcon={app}\app\current\FPV-Uhyliant.exe
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
PrivilegesRequired=lowest
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "ukrainian"; MessagesFile: "compiler:Languages\Ukrainian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Створити ярлик на робочому столі"; GroupDescription: "Додаткові ярлики:"; Flags: unchecked

[Files]
Source: "..\bootstrap-output\FPV-Uhyliant-Launcher.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\bootstrap-output\FPV-Uhyliant-Update.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\FPV-Uhyliant\*"; DestDir: "{app}\app\current"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\FPV Uhyliant"; Filename: "{app}\{#MyLauncher}"; WorkingDir: "{app}"; IconFilename: "{app}\app\current\FPV-Uhyliant.exe"
Name: "{autodesktop}\FPV Uhyliant"; Filename: "{app}\{#MyLauncher}"; WorkingDir: "{app}"; IconFilename: "{app}\app\current\FPV-Uhyliant.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyLauncher}"; Description: "Запустити FPV Uhyliant"; Flags: nowait postinstall skipifsilent
