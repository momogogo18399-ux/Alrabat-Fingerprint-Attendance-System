; Inno Setup Script for Attendance Admin Desktop App
; 1) قم أولاً ببناء ملف exe عبر PyInstaller إلى: dist\AttendanceAdmin\
; 2) ثم شغّل هذا السكربت عبر ISCC.exe لإنتاج المُثبّت النهائي

#define MyAppName "Attendance Admin"
#ifndef MyAppVersion
#define MyAppVersion "1.0.0"
#endif
#define MyAppPublisher "Your Company"
#define MyAppURL "http://localhost"
#define MyAppExeName "AttendanceAdmin.exe"

[Setup]
AppId={{D1E7A10B-9D45-4611-9B87-8D4C9E1E0C3A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\AttendanceAdmin
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=no
OutputDir=deploy\output
OutputBaseFilename=AttendanceAdminInstaller
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "arabic"; MessagesFile: "compiler:Languages\\Arabic.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &Desktop icon"; GroupDescription: "Additional icons:"
Name: "firewall"; Description: "Add Windows Firewall rule for the app"; GroupDescription: "Security:"; Flags: unchecked

[Files]
; انسخ كل محتويات مجلد PyInstaller الناتج
Source: "..\\dist\\AttendanceAdmin\\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"
Name: "{group}\\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{cmd}"; Parameters: "/C netsh advfirewall firewall add rule name=""{#MyAppName}"" dir=out action=allow program=""{app}\{#MyAppExeName}"" enable=yes"; Flags: runhidden; Tasks: firewall; Check: IsWin64
Filename: "{app}\\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Code]
var
  PageDB: TWizardPage;
  EdServer, EdDBName, EdUser, EdPass, EdPort: TNewEdit;

procedure InitializeWizard;
var
  Bevel: TNewStaticText;
begin
  PageDB := CreateCustomPage(wpSelectTasks, 'Database Settings', 'Configure connection to the central server');

  Bevel := TNewStaticText.Create(PageDB);
  Bevel.Parent := PageDB.Surface;
  Bevel.Caption := 'Enter your PostgreSQL connection details (used to write .env):';
  Bevel.Left := ScaleX(0);
  Bevel.Top := ScaleY(0);
  Bevel.AutoSize := True;

  EdServer := TNewEdit.Create(PageDB);
  EdServer.Parent := PageDB.Surface;
  EdServer.Left := ScaleX(0);
  EdServer.Top := ScaleY(24);
  EdServer.Width := ScaleX(360);
  EdServer.Text := 'SERVER_IP_OR_DOMAIN';
  { Text hint not supported in all versions }

  EdDBName := TNewEdit.Create(PageDB);
  EdDBName.Parent := PageDB.Surface;
  EdDBName.Left := EdServer.Left;
  EdDBName.Top := EdServer.Top + ScaleY(28);
  EdDBName.Width := EdServer.Width;
  EdDBName.Text := 'attendance';
  { no TextHint }

  EdUser := TNewEdit.Create(PageDB);
  EdUser.Parent := PageDB.Surface;
  EdUser.Left := EdServer.Left;
  EdUser.Top := EdDBName.Top + ScaleY(28);
  EdUser.Width := EdServer.Width;
  EdUser.Text := 'attendance';
  { no TextHint }

  EdPass := TNewEdit.Create(PageDB);
  EdPass.Parent := PageDB.Surface;
  EdPass.Left := EdServer.Left;
  EdPass.Top := EdUser.Top + ScaleY(28);
  EdPass.Width := EdServer.Width;
  EdPass.PasswordChar := '*';

  EdPort := TNewEdit.Create(PageDB);
  EdPort.Parent := PageDB.Surface;
  EdPort.Left := EdServer.Left;
  EdPort.Top := EdPass.Top + ScaleY(28);
  EdPort.Width := EdServer.Width;
  EdPort.Text := '5432';
  { no TextHint }
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  EnvPath, DatabaseUrl, Content: string;
begin
  if CurStep = ssPostInstall then
  begin
    EnvPath := ExpandConstant('{app}') + '\\.env';
    if (EdServer.Text <> '') and (EdDBName.Text <> '') and (EdUser.Text <> '') and (EdPort.Text <> '') then
    begin
      DatabaseUrl := 'postgresql://' + EdUser.Text + ':' + EdPass.Text + '@' + EdServer.Text + ':' + EdPort.Text + '/' + EdDBName.Text;
      Content := 'DATABASE_URL=' + DatabaseUrl + #13#10 +
                 'THEME_DIR=assets/themes' + #13#10;
      SaveStringToFile(EnvPath, Content, False);
    end;
  end;
end;



