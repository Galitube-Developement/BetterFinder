#define MyAppName "BetterFinder"
#define MyAppVersion "1.0"
#define MyAppPublisher "BetterFinder"
#define MyAppURL "https://www.example.com/"
#define MyAppExeName "BetterFinder.exe"

; Prüfen, ob Release existiert, sonst Debug verwenden
#define UseRelease GetEnv("RELEASE_BUILD") == "1"
#if UseRelease
  #define BuildConfig "Release"
#else
  #define BuildConfig "Debug"
#endif

[Setup]
; Eindeutige ID für den Installer
AppId={{F5A4B928-9F62-4512-B55A-6F3F2B63F75D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Icon für den Installer
SetupIconFile=BetterFinder\Resources\BetterFinder-Icon.ico
; Die Wizard-Bilder werden entfernt, da sie Probleme verursachen
; WizardImageFile und WizardSmallImageFile benötigen spezielle Formate/Größen
OutputDir=..\installer
OutputBaseFilename=BetterFinder_Setup
Compression=lzma2/ultra64
SolidCompression=true
InternalCompressLevel=ultra64
LZMAUseSeparateProcess=yes
; Reduziert False-Positive-Erkennungen
UninstallDisplayName={#MyAppName}
VersionInfoDescription=Installer für {#MyAppName}
VersionInfoProductName={#MyAppName}
VersionInfoCompany={#MyAppPublisher}
VersionInfoCopyright=(c) 2025 {#MyAppPublisher}
AppCopyright=(c) 2025 {#MyAppPublisher}
PrivilegesRequired=lowest
WizardStyle=modern
; NoEncryption hilft gegen False-Positives
Encryption=no

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
Source: "BetterFinder\bin\{#BuildConfig}\net6.0-windows\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// Optionaler Code für zusätzliche Funktionen während der Installation
// z.B. Prüfen auf bereits installierte Versionen, etc.

function GetUninstallString(): String;
var
  sUnInstPath: String;
  sUnInstallString: String;
begin
  sUnInstPath := ExpandConstant('Software\Microsoft\Windows\CurrentVersion\Uninstall\{#emit SetupSetting("AppId")}_is1');
  sUnInstallString := '';
  if not RegQueryStringValue(HKLM, sUnInstPath, 'UninstallString', sUnInstallString) then
    RegQueryStringValue(HKCU, sUnInstPath, 'UninstallString', sUnInstallString);
  Result := sUnInstallString;
end;

function IsUpgrade(): Boolean;
begin
  Result := (GetUninstallString() <> '');
end;

function InitializeSetup(): Boolean;
var
  V: Integer;
  iResultCode: Integer;
  sUnInstallString: String;
begin
  Result := True;
  if IsUpgrade() then
  begin
    V := MsgBox(ExpandConstant('Eine ältere Version von {#MyAppName} ist bereits installiert. Möchten Sie diese vor der Installation entfernen?'), mbInformation, MB_YESNO);
    if V = IDYES then
    begin
      sUnInstallString := GetUninstallString();
      sUnInstallString := RemoveQuotes(sUnInstallString);
      Exec(sUnInstallString, '/SILENT', '', SW_SHOW, ewWaitUntilTerminated, iResultCode);
      Result := True;
    end;
  end;
end; 