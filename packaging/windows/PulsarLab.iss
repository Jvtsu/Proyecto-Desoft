#define MyAppName "PulsarLab"
#ifndef MyAppVersion
#define MyAppVersion "1.0.0"
#endif
#define MyAppPublisher "PulsarLab"
#define MyAppExeName "PulsarLab.exe"

[Setup]
AppId={{641EFED8-0470-4FBB-A12A-61802474E240}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\PulsarLab
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\..\dist\installer
OutputBaseFilename=PulsarLab-Setup-{#MyAppVersion}-Windows-x64
SetupIconFile=pulsarlab.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ChangesAssociations=yes
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"; Flags: unchecked
Name: "fileassoc"; Description: "Abrir archivos .par, .dat y .tim con PulsarLab"; GroupDescription: "Asociaciones de archivos:"; Flags: unchecked

[Files]
Source: "..\..\dist\PulsarLab\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Registry]
Root: HKA; Subkey: "Software\Classes\.par\OpenWithProgids"; ValueType: string; ValueName: "PulsarLab.ProjectFile"; ValueData: ""; Flags: uninsdeletevalue; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\.dat\OpenWithProgids"; ValueType: string; ValueName: "PulsarLab.ProjectFile"; ValueData: ""; Flags: uninsdeletevalue; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\.tim\OpenWithProgids"; ValueType: string; ValueName: "PulsarLab.ProjectFile"; ValueData: ""; Flags: uninsdeletevalue; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\PulsarLab.ProjectFile"; ValueType: string; ValueName: ""; ValueData: "Archivo de PulsarLab"; Flags: uninsdeletekey; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\PulsarLab.ProjectFile\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\PulsarLab.ProjectFile\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: fileassoc

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir {#MyAppName}"; Flags: nowait postinstall skipifsilent
