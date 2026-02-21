#define MyAppName "OpenH3CSystemControl"
#define MyAppVersion GetEnv('VERSION')
#define MyAppPublisher "Remi & Community"
#define MyAppURL "https://github.com/Remik1r3n/OpenH3CSystemControl"
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

function BuildTaskRunnerCommand(const AppPath: String): String;
begin
  // Keep /TR as simple as possible.
  // Important: The *stored* task action must quote paths with spaces.
  // Passing \"...\" through schtasks ensures the task runs correctly when installed under Program Files.
  // The app itself is responsible for setting a stable working directory.
  Result := '\"' + AppPath + '\"';
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
  // Use a simple /TR to avoid nested quoting issues.
  // /RL LIMITED is typically sufficient for a tray app and avoids environments that reject HIGHEST without explicit credentials.
  Params := '/Create /F /SC ONLOGON /DELAY 0000:10 /RL LIMITED '
    + '/TN "' + TaskName + '" /TR "' + BuildTaskRunnerCommand(AppPath) + '"';
  Result := ExecCommand(SchedTasksExe(), Params, ResultCode);

  if not Result then
    MsgBox(
      'Failed to create startup task. Error code: ' + IntToStr(ResultCode)
      + ' (0x' + IntToHex(Cardinal(ResultCode), 8) + ')',
      mbError,
      MB_OK
    );
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
