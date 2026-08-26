#define MyAppName "SHOPFAVE"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "SHOPFAVE"
#define MyAppExeName "SHOPFAVE.exe"

[Setup]
AppId={{8B4D5F31-7A7B-4F0B-9C37-SHOPFAVE2026}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={autopf}\SHOPFAVE
DefaultGroupName={#MyAppName}

OutputDir=installer
OutputBaseFilename=SHOPFAVE_Setup
Compression=lzma
SolidCompression=yes

SetupIconFile=assets\shopfave.ico
UninstallDisplayIcon={app}\SHOPFAVE.exe

ArchitecturesInstallIn64BitMode=x64compatible

PrivilegesRequired=admin

DisableProgramGroupPage=yes

[Files]
Source: "dist\SHOPFAVE\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autodesktop}\SHOPFAVE"; Filename: "{app}\SHOPFAVE.exe"; IconFilename: "{app}\SHOPFAVE.exe"
Name: "{autoprograms}\SHOPFAVE"; Filename: "{app}\SHOPFAVE.exe"; IconFilename: "{app}\SHOPFAVE.exe"

[Run]
Filename: "{app}\SHOPFAVE.exe"; Description: "Launch SHOPFAVE"; Flags: nowait postinstall skipifsilent