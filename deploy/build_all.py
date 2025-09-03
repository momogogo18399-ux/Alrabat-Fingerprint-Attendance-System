# type: ignore
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        """Fallback function when python-dotenv is not available"""
        pass


def safe_import_pyinstaller():
    """Safely import PyInstaller and return version info"""
    try:
        import importlib.util
        spec = importlib.util.find_spec("PyInstaller")
        if spec is not None:
            PyInstaller = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(PyInstaller)
            version = getattr(PyInstaller, '__version__', 'unknown')
            return True, version
        else:
            return False, None
    except Exception:
        return False, None


def print_step(message: str) -> None:
	print(f"\n[+] {message}")


def run_cmd(cmd: list[str], cwd: Path | None = None, check: bool = True) -> int:
	print(f"$ {' '.join(cmd)}")
	return subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=check).returncode


def read_app_version(project_root: Path) -> str:
	version_file = project_root / "app" / "version.py"
	text = version_file.read_text(encoding="utf-8")
	m = re.search(r'APP_VERSION\s*=\s*"(.*?)"', text)
	return m.group(1) if m else "1.0.0"


def _detect_repo_from_git(project_root: Path) -> str | None:
	"""Try to infer owner/repo from `git remote get-url origin`."""
	try:
		result = subprocess.run([
			"git", "-C", str(project_root), "remote", "get-url", "origin"
		], capture_output=True, text=True, check=True)
		url = result.stdout.strip()
		# Support SSH and HTTPS forms
		# git@github.com:owner/repo.git -> owner/repo
		# https://github.com/owner/repo.git -> owner/repo
		m = re.search(r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+)", url)
		if m:
			return f"{m.group('owner')}/{m.group('repo')}"
	except Exception:
		return None
	return None


def find_iscc_exe() -> Path | None:
	"""
	Locate ISCC.exe (Inno Setup 6 compiler) using multiple strategies:
	- Environment variables: INNOSETUP_ISCC (full path) or INNOSETUP_DIR (directory containing ISCC.exe)
	- PATH lookup via shutil.which("iscc") / shutil.which("ISCC.exe")
	- Default install locations under Program Files
	"""
	env_candidates: list[Path] = []
	env_iscc = os.environ.get("INNOSETUP_ISCC")
	if env_iscc:
		env_candidates.append(Path(env_iscc))
	env_dir = os.environ.get("INNOSETUP_DIR")
	if env_dir:
		env_candidates.append(Path(env_dir) / "ISCC.exe")

	which_iscc = shutil.which("iscc") or shutil.which("ISCC.exe")
	if which_iscc:
		env_candidates.append(Path(which_iscc))

	default_candidates = [
		Path(os.environ.get("ProgramFiles(x86)", r"C:\\Program Files (x86)") + r"\Inno Setup 6\ISCC.exe"),
		Path(os.environ.get("ProgramFiles", r"C:\\Program Files") + r"\Inno Setup 6\ISCC.exe"),
	]

	for candidate in [*env_candidates, *default_candidates]:
		try:
			if candidate.exists():
				return candidate
		except Exception:
			continue
	return None


def _get_github_token(project_root: Path, args: argparse.Namespace) -> str | None:
	"""
	Resolve GitHub token from, in order:
	- CLI arg --token
	- env var GITHUB_TOKEN (after loading .env if present)
	- deploy/github_token.txt
	"""
	# Ensure .env is loaded once
	# (safe to call multiple times; it's idempotent)
	load_dotenv()
	if getattr(args, "token", None):
		return _sanitize_token(args.token)
	token = os.environ.get("GITHUB_TOKEN")
	if token:
		return _sanitize_token(token)
	token_file = project_root / "deploy" / "github_token.txt"
	try:
		if token_file.exists():
			return _sanitize_token(token_file.read_text(encoding="utf-8"))
	except Exception:
		pass
	return None


def _save_github_token(project_root: Path, token: str) -> None:
	token_file = project_root / "deploy" / "github_token.txt"
	token_file.write_text(_sanitize_token(token), encoding="utf-8")
	try:
		os.chmod(token_file, 0o600)
	except Exception:
		pass


def _sanitize_token(raw: str) -> str:
	"""Remove BOM/zero-width and any non-ASCII printable chars from token."""
	if not raw:
		return ""
	# Strip whitespace and quotes first
	clean = raw.strip().strip('"').strip("'")
	# Remove BOM and common zero-width marks
	for ch in ("\ufeff", "\u200b", "\u200c", "\u200d", "\u200e", "\u200f", "\u202a", "\u202b", "\u202c", "\u202d", "\u202e"):
		clean = clean.replace(ch, "")
	# Keep only ASCII printable range
	clean = "".join(c for c in clean if 32 <= ord(c) <= 126)
	return clean


def ensure_venv(project_root: Path, venv_dir: Path) -> Path:
	if not venv_dir.exists():
		print_step(f"Create venv: {venv_dir}")
		run_cmd([sys.executable, "-m", "venv", str(venv_dir)])
	py = venv_dir / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")
	return py


def install_deps(venv_python: Path, project_root: Path) -> None:
	print_step("Upgrade pip")
	run_cmd([str(venv_python), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"]) 
	print_step("Install requirements + PyInstaller")
	run_cmd([str(venv_python), "-m", "pip", "install", "-r", "requirements.txt", "--prefer-binary"], cwd=project_root)
	run_cmd([str(venv_python), "-m", "pip", "install", "pyinstaller==6.15.0"]) 


def build_exe(venv_python: Path, project_root: Path) -> Path:
	print_step("Build EXE with PyInstaller")
	pyinstaller_cmd = [
		str(venv_python), "-m", "PyInstaller",
		"-n", "AttendanceAdmin", "--noconfirm", "--clean", "--windowed",
		"--add-data", "assets\\themes;assets/themes",
		"--add-data", "assets\\icons;assets/icons",
		"--add-data", "translations;translations",
		"--add-data", "templates;templates",
		"app\\main.py",
	]
	run_cmd(pyinstaller_cmd, cwd=project_root)
	out = project_root / "dist" / "AttendanceAdmin" / "AttendanceAdmin.exe"
	if not out.exists():
		raise RuntimeError("PyInstaller output not found: dist/AttendanceAdmin/AttendanceAdmin.exe")
	print(f"[✓] EXE: {out}")
	return out


def build_installer(project_root: Path, version: str) -> Path | None:
	"""Build installers using PyInstaller and Inno Setup"""
	print_step("Building installer with PyInstaller and Inno Setup")
	
	# Check basic requirements
	required_files = [
		project_root / "requirements.txt",
		project_root / "app" / "main.py",
		project_root / "deploy" / "installer.iss"
	]
	
	for file_path in required_files:
		if not file_path.exists():
			print(f"❌ Required file not found: {file_path}")
			return None
	
	# Search for ISCC.exe
	iscc_exe = find_iscc_exe()
	if not iscc_exe:
		print("❌ ISCC.exe not found. Please install Inno Setup 6")
		print("   Download from: https://jrsoftware.org/isdl.php")
		return None
	
	# Create output directory
	output_dir = project_root / "deploy" / "deploy" / "output"
	output_dir.mkdir(parents=True, exist_ok=True)
	
	# Check PyInstaller availability
	pyinstaller_available, pyinstaller_version = safe_import_pyinstaller()
	if pyinstaller_available:
		print_step(f"PyInstaller version: {pyinstaller_version}")
	else:
		print("❌ PyInstaller not installed. Installing...")
		try:
			subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller==6.15.0"], check=True)
			# Try to get version after installation
			pyinstaller_available, pyinstaller_version = safe_import_pyinstaller()
			if pyinstaller_available:
				print_step(f"PyInstaller installed successfully, version: {pyinstaller_version}")
			else:
				print("⚠️  PyInstaller installed but version could not be determined")
		except subprocess.CalledProcessError:
			print("❌ Failed to install PyInstaller")
			return None
	
	# Update Inno Setup file
	iss_file = project_root / "deploy" / "installer.iss"
	if iss_file.exists():
		iss_content = iss_file.read_text(encoding="utf-8")
		iss_content = iss_content.replace('{#VERSION}', version)
		iss_file.write_text(iss_content, encoding="utf-8")
		print_step("Updated installer.iss with version")
	
	# Build installer
	try:
		print_step("Running Inno Setup compiler...")
		run_cmd([str(iscc_exe), str(iss_file)], cwd=project_root / "deploy")
		print_step("Inno Setup build completed successfully")
	except subprocess.CalledProcessError as e:
		print(f"❌ Inno Setup build failed: {e}")
		print("   Check the installer.iss file and Inno Setup installation")
		return None
	except Exception as e:
		print(f"❌ Unexpected error during build: {e}")
		return None
	
	# Check for required files
	installer_path = output_dir / f"AttendanceAdminInstaller.exe"
	if installer_path.exists():
		size_mb = installer_path.stat().st_size / (1024 * 1024)
		print_step(f"Installer created successfully: {installer_path.name} ({size_mb:.1f} MB)")
		return installer_path
	else:
		print("❌ Installer file not found after build")
		print("   Check Inno Setup logs for errors")
		return None


def upload_release_assets(repo: str, tag: str, release_name: str, release_body: str, asset_paths: list[Path], github_token: str) -> None:
	import requests
	# Decide initial scheme by token prefix: classic PATs use 'token', fine-grained often prefer 'Bearer'
	preferred_scheme = "Bearer" if github_token.startswith("github_pat_") else "token"
	session = requests.Session()
	session.headers.update({
		"Accept": "application/vnd.github+json",
		"X-GitHub-Api-Version": "2022-11-28",
	})

	def set_auth_scheme(scheme: str) -> None:
		if scheme == "Bearer":
			session.headers["Authorization"] = f"Bearer {github_token}"
		else:
			session.headers["Authorization"] = f"token {github_token}"

	def request(method: str, url: str, **kwargs):
		# Try preferred scheme, then fallback to the other on 401
		set_auth_scheme(preferred_scheme)
		resp = session.request(method, url, **kwargs)
		if resp.status_code == 401:
			alt = "token" if preferred_scheme == "Bearer" else "Bearer"
			set_auth_scheme(alt)
			resp = session.request(method, url, **kwargs)
			if resp.status_code == 401:
				raise RuntimeError("GitHub authentication failed (401). Check token validity, scopes, and SSO authorization.")
		return resp

	api_base = f"https://api.github.com/repos/{repo}"
	uploads_base = f"https://uploads.github.com/repos/{repo}"

	# Quick auth preflight
	preflight_resp = request("GET", "https://api.github.com/user")
	try:
		user_login = preflight_resp.json().get("login")
		scheme_used = (session.headers.get("Authorization", "").split(" ")[0] or "?")
		scopes_hdr = preflight_resp.headers.get("X-OAuth-Scopes") or preflight_resp.headers.get("x-oauth-scopes") or ""
		print_step(f"GitHub auth OK: user={user_login} scheme={scheme_used} scopes={scopes_hdr}")
	except Exception:
		pass

	def get_release_by_tag(tag_name: str):
		resp = request("GET", f"{api_base}/releases/tags/{tag_name}")
		if resp.status_code == 200:
			return resp.json()
		if resp.status_code == 404:
			return None
		raise RuntimeError(f"GitHub API error ({resp.status_code}): {resp.text}")

	def create_release(tag_name: str, name: str, body: str):
		payload = {
			"tag_name": tag_name,
			"name": name,
			"body": body or "",
			"draft": False,
			"prerelease": False,
		}
		resp = request("POST", f"{api_base}/releases", json=payload)
		if resp.status_code not in (200, 201):
			raise RuntimeError(f"Failed to create release: {resp.status_code} {resp.text}")
		return resp.json()

	def delete_asset(asset_id: int):
		resp = request("DELETE", f"{api_base}/releases/assets/{asset_id}")
		if resp.status_code not in (204, 404):
			raise RuntimeError(f"Failed to delete asset {asset_id}: {resp.status_code} {resp.text}")

	def upload_asset(release_id: int, file_path: Path):
		name = file_path.name
		# Remove existing asset with same name if present
		assets_resp = request("GET", f"{api_base}/releases/{release_id}/assets")
		if assets_resp.status_code != 200:
			raise RuntimeError(f"Failed to list assets: {assets_resp.status_code} {assets_resp.text}")
		for asset in assets_resp.json():
			if asset.get("name") == name:
				delete_asset(asset.get("id"))
				break
		with file_path.open("rb") as fh:
			upload_headers = dict(session.headers)
			upload_headers["Content-Type"] = "application/octet-stream"
			upload_url = f"{uploads_base}/releases/{release_id}/assets?name={name}"
			upload_resp = session.post(upload_url, headers=upload_headers, data=fh.read())
			if upload_resp.status_code not in (200, 201):
				raise RuntimeError(f"Failed to upload asset {name}: {upload_resp.status_code} {upload_resp.text}")

	# Ensure release exists
	release = get_release_by_tag(tag)
	if not release:
		print_step(f"Create GitHub release: {tag}")
		release = create_release(tag, release_name, release_body)
	else:
		print_step(f"Using existing GitHub release: {tag}")

	release_id = release.get("id")
	for asset in asset_paths:
		print_step(f"Upload asset: {asset}")
		upload_asset(release_id, asset)


def _create_env_template(project_root: Path, args: argparse.Namespace) -> None:
	"""إنشاء ملف .env.example مع الإعدادات المطلوبة"""
	env_template = project_root / ".env.example"
	
	# تحديد GitHub repo من المعاملات أو git
	github_repo = getattr(args, 'github_repo', None)
	if not github_repo:
		github_repo = _detect_repo_from_git(project_root)
	
	github_owner = None
	if github_repo:
		parts = github_repo.split('/')
		if len(parts) == 2:
			github_owner, github_repo = parts
	
	env_content = f"""# Flask Settings
FLASK_DEBUG=0
FLASK_ENV=production

# Database Settings
# DATABASE_URL=postgresql://attendance:strongpass@127.0.0.1:5432/attendance
SQLITE_FILE=attendance.db

# Update Server Settings
UPDATE_SERVER_URL=https://your-domain.com
FALLBACK_SERVER_URL=http://localhost:5000
UPDATE_TIMEOUT=10.0
DOWNLOAD_TIMEOUT=60.0
UPDATE_MAX_RETRIES=3

# GitHub Settings (for updates)
GITHUB_OWNER={github_owner or 'your-username'}
GITHUB_REPO={github_repo or 'your-repo-name'}

# Public URLs
PUBLIC_BASE_URL=https://your-domain.com

# Update Configuration
UPDATE_NOTES=- تحسينات عامة وإصلاحات أخطاء.\\n- دعم التحقق التلقائي من الUpdateات.\\n- تحسينات في الأداء والاستقرار.
MANDATORY_UPDATE=false
MIN_SUPPORTED_VERSION=1.0.0

# Desktop App Settings
THEME_DIR=assets/themes
NOTIFIER_HOST=localhost
NOTIFIER_PORT=8989

# Security Settings
SECRET_KEY=your-secret-key-here
"""
	
	env_template.write_text(env_content, encoding="utf-8")
	print_step(f"Created .env.example template")


class SubstDrive:
	def __init__(self, target: Path, letter: str = "X"):
		self.target = target
		self.letter = letter.rstrip(": ")
		self.created = False

	def __enter__(self) -> Path:
		if os.name != "nt":
			return self.target
		# Map only if path is long
		if len(str(self.target)) > 150:
			try:
				subprocess.run(["subst", f"{self.letter}:", str(self.target)], check=True)
				self.created = True
				return Path(f"{self.letter}:")
			except Exception:
				pass
		return self.target

	def __exit__(self, exc_type, exc, tb) -> None:
		if os.name == "nt" and self.created:
			subprocess.run(["subst", f"{self.letter}:", "/D"], check=False)


def upload_to_github(project_root: Path, version: str, github_token: str, args: argparse.Namespace) -> None:
	"""رفع المثبتات إلى GitHub Releases"""
	repo = getattr(args, 'github_repo', None) or _detect_repo_from_git(project_root)
	if not repo:
		print("❌ No GitHub repository specified. Use --github-repo or ensure git remote is set")
		return
	
	print_step(f"Uploading to GitHub repository: {repo}")
	
	# الSearch عن الملفات المطلوبة
	installer_path = project_root / "deploy" / "deploy" / "output" / f"AttendanceAdminInstaller.exe"
	exe_path = project_root / "deploy" / "deploy" / "output" / f"FingerprintAttendanceSystem.exe"
	
	assets = []
	if installer_path.exists():
		assets.append(installer_path)
	if exe_path.exists():
		assets.append(exe_path)
	
	if not assets:
		print("❌ No installer files found. Run build first.")
		return
	
	# إنشاء أو Update الإصدار
	tag = f"v{version}"
	release_name = f"Attendance Admin {version}"
	release_body = f"""## ما الجديد في الإصدار {version}

- تحسينات عامة وإصلاحات أخطاء
- دعم التحقق التلقائي من الUpdateات
- تحسينات في الأداء والاستقرار
- دعم قاعدة البيانات المشتركة
- تحسينات في الأمان

### التثبيت
1. قم بتحميل `AttendanceAdminInstaller.exe`
2. شغل الملف كمسؤول
3. اتبع خطوات التثبيت

### الUpdate التلقائي
سيتم التحقق من الUpdateات تلقائيًا عند تشغيل البرنامج.
"""
	
	upload_release_assets(repo, tag, release_name, release_body, assets, github_token)
	print_step("GitHub upload completed successfully")


def main() -> None:
	parser = argparse.ArgumentParser(description="Build and deploy attendance system")
	parser.add_argument("--token", help="GitHub token for releases")
	parser.add_argument("--github-repo", help="GitHub repository (owner/repo)")
	parser.add_argument("--skip-build", action="store_true", help="Skip building installer")
	parser.add_argument("--skip-upload", action="store_true", help="Skip uploading to GitHub")
	parser.add_argument("--create-env", action="store_true", help="Create .env.example template")
	
	args = parser.parse_args()
	project_root = Path(__file__).parent.parent
	
	print_step("Starting build process")
	
	# إنشاء ملف .env.example إذا طُلب
	if args.create_env:
		_create_env_template(project_root, args)
		return
	
	version = read_app_version(project_root)
	print_step(f"Building version {version}")
	
	if not args.skip_build:
		build_installer(project_root, version)
	
	if not args.skip_upload:
		github_token = _get_github_token(project_root, args)
		if not github_token:
			print("❌ No GitHub token found. Set GITHUB_TOKEN env var or use --token")
			return
		
		upload_to_github(project_root, version, github_token, args)
	
	print_step("Build process completed")


if __name__ == "__main__":
	main()


