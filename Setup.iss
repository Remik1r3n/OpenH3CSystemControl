#define MyAppName "OpenH3CSystemControl"
#define MyAppVersion GetEnv('VERSION')
#define MyAppPublisher "Remi & Community"
#define MyAppURL "https://github.com/RemiK1Rn/OpenH3CSystemControl"
#define MyAppExeName "OpenH3CSystemControl.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{3669316D-B63C-4F9F-9FE8-A30669D56A3D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
; Remove the following line to run in administrative install mode (install for all users.)
PrivilegesRequired=admin
OutputDir=dist
OutputBaseFilename=OpenH3CSystemControl_Setup_x64
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "autostart"; Description: "Start automatically with Windows (via Task Scheduler)"; GroupDescription: "Logon settings"; Flags: checkedonce

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
; Use ShellExecute for better compatibility with UAC-elevated executables
Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent shellexec

[Code]
function ExecCommand(const Command: String; const Params: String; var ResultCode: Integer): Boolean;
begin
  ResultCode := -1;
  if not Exec(Command, Params, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    Result := False;
    Exit;
  end;

  Result := (ResultCode = 0);
end;

function SchedTasksExe(): String;
begin
  Result := ExpandConstant('{sys}\schtasks.exe');
end;

function PowerShellExe(): String;
begin
  // Avoid relying on PATH at logon.
  Result := ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe');
end;

function QuoteForPowerShellSingle(const S: String): String;
begin
  // Escape single quotes for PowerShell single-quoted strings.
  Result := StringChange(S, '''', '''''');
end;

function BuildTaskRunnerCommand(const AppPath: String): String;
var
  AppDir: String;
begin
  // Start the app with an explicit working directory.
  // Scheduled tasks frequently start in System32, which can break relative-path lookups.
  AppDir := ExtractFileDir(AppPath);

  // Use PowerShell Start-Process to set WorkingDirectory and avoid flashing a console.
  // We single-quote paths to keep quoting rules predictable.
  Result := '"' + PowerShellExe() + '" -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden '
    + '-Command "Start-Process -FilePath ''' + QuoteForPowerShellSingle(AppPath)
    + ''' -WorkingDirectory ''' + QuoteForPowerShellSingle(AppDir) + '''"';
end;

procedure DeleteScheduledTaskIfExists(const TaskName: String);
var
  ResultCode: Integer;
begin
  ExecCommand(SchedTasksExe(), '/Delete /TN "' + TaskName + '" /F', ResultCode);
end;

function CreateLogonTaskHighest(const TaskName: String; const AppPath: String): Boolean;
var
  Params: String;
  ResultCode: Integer;
begin
  // Note: With schtasks.exe and no explicit /RU, the task is created for the current user.
  // Delay a bit so Explorer/System Tray is fully up; otherwise tray-only apps can appear to "not start".
  // /IT: run only when the user is logged on (interactive), required for tray apps.
  // Use a runner that sets WorkingDirectory explicitly.
  Params := '/Create /F /SC ONLOGON /DELAY 0000:10 /RL HIGHEST /IT '
    + '/TN "' + TaskName + '" /TR "' + BuildTaskRunnerCommand(AppPath) + '"';
  Result := ExecCommand(SchedTasksExe(), Params, ResultCode);

  // Some configurations reject /IT unless /RU is explicitly specified.
  // Retry without /IT to avoid breaking the install flow.
  if not Result then
  begin
    Params := '/Create /F /SC ONLOGON /DELAY 0000:10 /RL HIGHEST '
      + '/TN "' + TaskName + '" /TR "' + BuildTaskRunnerCommand(AppPath) + '"';
    Result := ExecCommand(SchedTasksExe(), Params, ResultCode);
  end;

  if not Result then
    MsgBox('Failed to create startup task. Error code: ' + IntToStr(ResultCode), mbError, MB_OK);
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  TaskName: String;
  AppPath: String;
begin
  if CurStep = ssPostInstall then
  begin
    if WizardIsTaskSelected('autostart') then
    begin
      TaskName := 'OpenH3CSystemControl';
      AppPath := ExpandConstant('{app}\{#MyAppExeName}');

      DeleteScheduledTaskIfExists(TaskName);
      CreateLogonTaskHighest(TaskName, AppPath);
    end;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  TaskName: String;
begin
  if CurUninstallStep = usUninstall then
  begin
    TaskName := 'OpenH3CSystemControl';
    DeleteScheduledTaskIfExists(TaskName);
  end;
end;
