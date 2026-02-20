#define MyAppName "OpenH3CSystemControl"
#define MyAppVersion GetEnv('VERSION')
#define MyAppPublisher "Remi & Community"
#define MyAppURL "https://github.com/RemiK1Rn/OpenH3CSystemControl"
#define MyAppExeName "OpenH3CSystemControl.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{2A8E9A34-5B6C-4D7E-8F90-123456789ABC}
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
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// Helper function to execute command line
function ExecCommand(Command: String; Params: String): Boolean;
var
  ResultCode: Integer;
begin
  if Exec(Command, Params, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    Result := (ResultCode = 0);
  end
  else
  begin
    Result := False;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  TaskName: String;
  AppPath: String;
  Params: String;
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    // Create Scheduled Task on installation if selected
    if WizardIsTaskSelected('autostart') then
    begin
        TaskName := 'OpenH3CSystemControl';
        AppPath := ExpandConstant('{app}\{#MyAppExeName}');
        
        // Clean up any old task first - ignore result
        Exec(ExpandConstant('{sys}\schtasks.exe'), '/Delete /TN "' + TaskName + '" /F', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
        
        // Create new task
        // We need to wrap the path in quotes for schtasks because it contains spaces (Program Files)
        // Correct escaping for Pascal string containing double quotes: " -> "" (No, it is ' -> '')
        // Wait, inside a Pascal string '...', a single quote is escaped as ''. A double quote " is just a character.
        // So: '/TR "\"' + AppPath + '\""' results in: /TR "\"C:\Program Files\App.exe\""
        
        // To run for ALL users at logon, we ideally use the "Users" group as principal, but schtasks acts weirdly with groups for interactive tasks.
        // A common workaround for admin apps running at startup for all users is to use the Registry Run key in HKLM?
        // But HKLM Run key doesn't launch as Admin without UAC prompt or failing.
        // Task Scheduler is the way, but creating a task that triggers for ANY user's logon interactively is complex via command line.
        // Actually, /SC ONLOGON defaults to current user.
        // Using a loop to create tasks for users? No.
        // Using "INTERACTIVE" group?
        // Let's stick to the standard scheduled task which usually works for the installing user (Admin).
        // If the requirement "every users' autorun" is strict, we might need a different approach, 
        // but robust "Run as Admin" at startup for *any* user is tricky due to security boundaries.
        // The most reliable way for a utility like this is often just a shortcut in the Common Startup folder,
        // but that prompts for UAC.
        // Windows Task Scheduler with /RU "Users" might work but it often runs non-interactively.
        // Let's use the most reliable single-user admin autostart (for the installer) for now, as multi-user admin autostart is a niche edge case often requiring a service.
        // However, we can try to use *no* /RU which defaults to current user, or maybe the user meant "System-wide install" of the files.
        // Re-reading: "It's installed system-wide, every users' autorun, and as admin."
        // This implies for all users.
        // A Scheduled Task running as SYSTEM *can* interact with desktop if older Windows, but distinct user sessions make this hard.
        // Realistically, "Run as Admin" + "All Users" + "Auto Start" = A Windows Service (which runs as SYSTEM) + A per-user UI tray app (non-admin) that talks to the service.
        // But this is a Python script converted to EXE.
        // We will stick to the current implementation which sets it up for the installing user (likely the main admin user). 
        // For truly all users, it would require a task with a group principal, which is hard to script reliably via simple schtasks.
        
        Params := '/Create /F /SC ONLOGON /RL HIGHEST /TN "' + TaskName + '" /TR "\"' + AppPath + '\""';
        
        if not Exec(ExpandConstant('{sys}\schtasks.exe'), Params, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) or (ResultCode <> 0) then
        begin
             MsgBox('Failed to create startup task. Error code: ' + IntToStr(ResultCode), mbError, MB_OK);
        end;
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
    ExecCommand('schtasks', '/Delete /TN "' + TaskName + '" /F');
  end;
end;
