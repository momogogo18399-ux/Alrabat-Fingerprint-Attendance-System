import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from dotenv import load_dotenv


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


def build_installer(project_root: Path, app_version: str) -> Path:
	print_step("Build installer with Inno Setup")
	iscc = find_iscc_exe()
	if not iscc:
		raise RuntimeError("ISCC.exe (Inno Setup 6) not found. Please install Inno Setup 6.")
	iss_dir = project_root / "deploy"
	iss = iss_dir / "installer.iss"
	# Run ISCC from the script directory so OutputDir relative paths work as expected
	run_cmd([str(iscc), f"/DMyAppVersion={app_version}", iss.name], cwd=iss_dir)
	out = iss_dir / "output" / "AttendanceAdminInstaller.exe"
	if not out.exists():
		raise RuntimeError("Installer not found in deploy/output. Check Inno logs.")
	print(f"[✓] Installer: {out}")
	return out



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


def main() -> None:
	parser = argparse.ArgumentParser(description="Build EXE and Inno Setup installer (Windows)")
	parser.add_argument("--version", help="Override app version (defaults to app/version.py)")
	parser.add_argument("--use-subst", action="store_true", help="Use temporary SUBST drive for long paths (auto-enabled when needed)")
	# GitHub release options (manual mode only)
	parser.add_argument("--upload-release", action="store_true", help="Upload EXE/installer to GitHub release (manual mode)")
	parser.add_argument("--repo", help="GitHub repository in owner/repo format (auto-detected from git remote or GITHUB_REPOSITORY)")
	parser.add_argument("--tag", help="Release tag (defaults to v<version>)")
	parser.add_argument("--release-name", help="Release name (defaults to Attendance Admin <version>)")
	parser.add_argument("--release-body", help="Release body/notes")
	parser.add_argument("--token", help="GitHub token (overrides env/file)")
	parser.add_argument("--save-token", action="store_true", help="Persist provided token to deploy/github_token.txt")
	args = parser.parse_args()

	project_root = Path(__file__).resolve().parents[1]
	app_version = args.version or read_app_version(project_root)
	print_step(f"Project root: {project_root}")
	print_step(f"App version: {app_version}")

	use_subst = args.use_subst or (os.name == "nt" and len(str(project_root)) > 150)
	if use_subst and os.name == "nt":
		with SubstDrive(project_root, "X") as mapped_root:
			run_all(Path(mapped_root), app_version, args)
	else:
		run_all(project_root, app_version, args)


def run_all(root: Path, app_version: str, args: argparse.Namespace) -> None:
	venv_dir = root / ".buildvenv"
	venv_python = ensure_venv(root, venv_dir)
	install_deps(venv_python, root)
	exe_path = build_exe(venv_python, root)
	installer_path = build_installer(root, app_version)
	# Manual GitHub release upload only (requires --upload-release flag)
	repo = (
		args.repo
		or os.environ.get("GITHUB_REPOSITORY")
		or _detect_repo_from_git(root)
	)
	github_token = _get_github_token(root, args)
	if args.save_token and args.token:
		_save_github_token(root, args.token)
	# Manual GitHub release upload only (requires --upload-release flag)
	if getattr(args, "upload_release", False):
		if not repo:
			raise SystemExit("--repo is required when using --upload-release")
		if not github_token:
			raise SystemExit("GITHUB_TOKEN environment variable or --token is required for --upload-release")
		tag = args.tag or f"v{app_version}"
		release_name = args.release_name or f"Attendance Admin {app_version}"
		release_body = args.release_body or "Automated release"
		assets = [exe_path, installer_path]
		print_step(f"Upload release assets to GitHub: {repo} tag={tag}")
		upload_release_assets(repo, tag, release_name, release_body, assets, github_token)
	else:
		print_step("GitHub release upload skipped (use --upload-release to enable).")
	print("\nAll done.")


if __name__ == "__main__":
	main()


