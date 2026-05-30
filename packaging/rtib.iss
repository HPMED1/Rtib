; Inno Setup script for Rtib.
;
; Build with: powershell -ExecutionPolicy Bypass -File scripts\build-installer.ps1
;
; The script expects ..\dist\Rtib.exe and ..\dist\cli\rtib.exe to exist
; (produced by build-dist.ps1).

#define AppName "Rtib"
#define AppVersion "0.1.0"
#define AppPublisher "HPMED"
#define AppExeName "Rtib.exe"
#define CliExeName "rtib.exe"

[Setup]
; A new AppId == a separate install entry. Keep this GUID stable across
; versions so upgrades replace the previous install.
AppId={{A4C3B9D2-6F4E-4B8A-9E2D-7B5F3C2A1D8E}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
PrivilegesRequired=lowest
; PrivilegesRequiredOverridesAllowed=dialog shows a "Install for: All users / Just me" prompt.
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist\installer
OutputBaseFilename=Rtib-{#AppVersion}-setup
SetupIconFile=..\src\rtib\resources\icons\rtib.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName} {#AppVersion}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "addtopath"; Description: "Add the rtib CLI to PATH (for terminal usage: rtib --input X --output Y)"; GroupDescription: "Other:"; Flags: unchecked

[Files]
Source: "..\dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\cli\{#CliExeName}"; DestDir: "{app}\cli"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\CHANGELOG.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent unchecked

[Registry]
; Per-user install: write CLI path into HKCU\Environment.
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; \
    ValueData: "{olddata};{app}\cli"; Flags: preservestringtype; \
    Check: not IsAdminInstallMode() and NeedsAddPath(ExpandConstant('{app}\cli')); \
    Tasks: addtopath
; System-wide install: write CLI path into HKLM PATH.
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; \
    ValueType: expandsz; ValueName: "Path"; \
    ValueData: "{olddata};{app}\cli"; Flags: preservestringtype; \
    Check: IsAdminInstallMode() and NeedsAddPath(ExpandConstant('{app}\cli')); \
    Tasks: addtopath

[Code]
function NeedsAddPath(NewPath: string): boolean;
var
  OrigPath: string;
  Root: integer;
  Key: string;
begin
  if IsAdminInstallMode() then begin
    Root := HKEY_LOCAL_MACHINE;
    Key := 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment';
  end else begin
    Root := HKEY_CURRENT_USER;
    Key := 'Environment';
  end;
  if not RegQueryStringValue(Root, Key, 'Path', OrigPath) then
  begin
    Result := True;
    exit;
  end;
  // Surround with ; so partial-match collisions are impossible.
  Result := Pos(';' + Uppercase(NewPath) + ';',
                ';' + Uppercase(OrigPath) + ';') = 0;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  OrigPath: string;
  NewPath: string;
  Root: integer;
  Key: string;
  CliPath: string;
begin
  if CurUninstallStep <> usUninstall then
    exit;
  CliPath := ExpandConstant('{app}\cli');
  if IsAdminInstallMode() then begin
    Root := HKEY_LOCAL_MACHINE;
    Key := 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment';
  end else begin
    Root := HKEY_CURRENT_USER;
    Key := 'Environment';
  end;
  if not RegQueryStringValue(Root, Key, 'Path', OrigPath) then
    exit;
  // StringChange is var-passed (modifies the first argument in place), so
  // we have to copy into a variable first.
  NewPath := ';' + OrigPath + ';';
  StringChange(NewPath, ';' + CliPath + ';', ';');
  // Trim the leading/trailing ; we added.
  if (Length(NewPath) > 0) and (Copy(NewPath, 1, 1) = ';') then
    NewPath := Copy(NewPath, 2, Length(NewPath) - 1);
  if (Length(NewPath) > 0) and (Copy(NewPath, Length(NewPath), 1) = ';') then
    NewPath := Copy(NewPath, 1, Length(NewPath) - 1);
  if NewPath <> OrigPath then
    RegWriteExpandStringValue(Root, Key, 'Path', NewPath);
end;
