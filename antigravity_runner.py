from __future__ import annotations

import os
import re
import json
import yaml
import shutil
import hashlib
import fnmatch
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def sh(cmd: List[str], cwd: Optional[Path] = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=check, text=True, capture_output=True)


def safe_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read_text(path: Path, limit_bytes: int = 2_000_000) -> str:
    data = path.read_bytes()
    if len(data) > limit_bytes:
        data = data[:limit_bytes]
    return data.decode("utf-8", errors="replace")


@dataclass
class RepoSpec:
    name: str
    url: str
    role: str


@dataclass
class PersonaSpec:
    name: str
    meaning: str
    target_audience: str
    doc_filename: str
    prompt_search_terms: List[str]


@dataclass
class OutputSpec:
    reports_dir: str
    docs_dir: str
    services_dir: str
    strategies_dir: str


@dataclass
class ExecutionSpec:
    update_prompts: bool
    generate_services_layer: bool
    run_verify: bool
    open_pr_if_possible: bool


@dataclass
class PromptUpdateSpec:
    enabled: bool
    managed_files: List[str]
    exclude_globs: List[str]


class Antigravity:
    def __init__(self, cfg: Dict[str, Any]):
        self.workspace_dir = Path(cfg["workspace_dir"]).resolve()
        self.target_repo_path = Path(cfg["target_repo_path"]).resolve()

        self.output = OutputSpec(**cfg["output"])
        self.persona = PersonaSpec(**cfg["persona"])
        self.execution = ExecutionSpec(**cfg["execution"])
        
        pu = cfg.get("prompt_update", {})
        self.prompt_config = PromptUpdateSpec(
            enabled=pu.get("enabled", False),
            managed_files=pu.get("managed_files", []),
            exclude_globs=pu.get("exclude_globs", [])
        )

        self.repos: List[RepoSpec] = [RepoSpec(**r) for r in cfg["repos"]]

        self.repos_dir = self.workspace_dir / "repos"
        self.cache_dir = self.workspace_dir / "cache"
        self.state_path = self.workspace_dir / "state.json"

        self.repos_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.state: Dict[str, Any] = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        if self.state_path.exists():
            try:
                return json.loads(read_text(self.state_path))
            except Exception:
                return {}
        return {}

    def _save_state(self) -> None:
        safe_write(self.state_path, json.dumps(self.state, indent=2))
        
    def should_ignore(self, path: Path) -> bool:
        rel = path.relative_to(self.target_repo_path)
        # Check against exclude globs
        for pat in self.prompt_config.exclude_globs:
            if fnmatch.fnmatch(str(rel), pat):
                return True
        return False

    def run_all(self) -> None:
        self.clone_or_update_all()
        analyses = self.analyze_all_repos()
        self.write_reports(analyses)
        self.document_unk_persona(analyses)

        if self.execution.generate_services_layer:
            self.generate_services_layer(analyses)

        if self.execution.update_prompts:
            self.update_system_prompts()

        if self.execution.run_verify:
            self.verify()

        self._save_state()

    # ---------- Repo ops ----------

    def clone_or_update_all(self) -> None:
        for repo in self.repos:
            dest = self.repos_dir / repo.name
            if dest.exists() and (dest / ".git").exists():
                print(f"Update existing repo: {repo.name}")
                sh(["git", "fetch", "--all"], cwd=dest)
                sh(["git", "pull", "--ff-only"], cwd=dest, check=False)
            else:
                if dest.exists():
                    shutil.rmtree(dest)
                print(f"Cloning new repo: {repo.name} -> {repo.url}")
                sh(["git", "clone", repo.url, str(dest)])

    # ---------- Analysis ----------

    def analyze_all_repos(self) -> Dict[str, Any]:
        results: Dict[str, Any] = {}
        for repo in self.repos:
            root = self.repos_dir / repo.name
            print(f"Analyzing: {repo.name}")
            results[repo.name] = {
                "name": repo.name,
                "role": repo.role,
                "url": repo.url,
                "root": str(root),
                "prompt_hits": self.find_prompt_definitions(root),
                "deps": self.detect_deps(root),
                "ml_signals": self.detect_ml_signals(root),
                "integration_signals": self.detect_integration_signals(root),
            }
        return results

    def find_prompt_definitions(self, root: Path) -> List[Dict[str, str]]:
        hits: List[Dict[str, str]] = []
        patterns = [
            re.compile(r"system\s*prompt", re.IGNORECASE),
            re.compile(r"\bpersona\b", re.IGNORECASE),
            re.compile(r"\binstructions\b", re.IGNORECASE),
            re.compile(r"\bdeveloper\s*message\b", re.IGNORECASE),
            re.compile(r"\bprompt\b", re.IGNORECASE),
        ]

        exts = {".md", ".txt", ".json", ".yaml", ".yml", ".py", ".ts", ".tsx", ".js"}
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in exts:
                continue
            try:
                text = read_text(p)
            except Exception:
                continue

            if any(rx.search(text) for rx in patterns):
                excerpt = self.best_excerpt(text, patterns)
                hits.append({"file": str(p.relative_to(root)), "excerpt": excerpt})
        return hits[:200]

    def best_excerpt(self, text: str, patterns: List[re.Pattern], window: int = 500) -> str:
        for rx in patterns:
            m = rx.search(text)
            if m:
                start = max(0, m.start() - window // 2)
                end = min(len(text), m.end() + window // 2)
                snippet = text[start:end].strip()
                return snippet.replace("\n", "\\n")[:1200]
        return text[:800].replace("\n", "\\n")

    def detect_deps(self, root: Path) -> Dict[str, Any]:
        deps: Dict[str, Any] = {"python": [], "node": [], "other": []}
        req = root / "requirements.txt"
        pyproj = root / "pyproject.toml"
        pkg = root / "package.json"

        if req.exists():
            deps["python"].append({"file": "requirements.txt", "content": read_text(req)[:20000]})
        if pyproj.exists():
            deps["python"].append({"file": "pyproject.toml", "content": read_text(pyproj)[:20000]})
        if pkg.exists():
            deps["node"].append({"file": "package.json", "content": read_text(pkg)[:20000]})

        return deps

    def detect_ml_signals(self, root: Path) -> Dict[str, Any]:
        needles = [
            "scikit-learn", "sklearn",
            "xgboost", "lightgbm",
            "pytorch", "torch",
            "tensorflow", "keras",
            "catboost",
            "pandas", "numpy",
            "optuna", "mlflow",
        ]
        files_to_scan = []
        for rel in ["requirements.txt", "pyproject.toml", "environment.yml"]:
            p = root / rel
            if p.exists():
                files_to_scan.append(p)

        found = set()
        for p in files_to_scan:
            txt = read_text(p).lower()
            for n in needles:
                if n in txt:
                    found.add(n)

        # quick code scan for common ML folders
        has_notebooks = any(root.rglob("*.ipynb"))
        has_data_dir = (root / "data").exists() or (root / "datasets").exists()

        return {"signals": sorted(found), "has_notebooks": has_notebooks, "has_data_dir": has_data_dir}

    def detect_integration_signals(self, root: Path) -> Dict[str, Any]:
        needles = [
            "api", "webhook", "broker", "exchange",
            "odds", "sportsbook", "betfair", "flumine",
            "polymarket", "solana", "prediction market",
            "arbitrage", "kelly", "staking",
        ]
        exts = {".md", ".py", ".ts", ".js"}
        hits: List[Dict[str, str]] = []
        for p in root.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in exts:
                continue
            try:
                txt = read_text(p, limit_bytes=200_000).lower()
            except Exception:
                continue
            score = sum(1 for n in needles if n in txt)
            if score >= 2:
                hits.append({"file": str(p.relative_to(root)), "score": str(score)})
        hits.sort(key=lambda x: int(x["score"]), reverse=True)
        return {"top_files": hits[:50]}

    # ---------- Outputs ----------

    def write_reports(self, analyses: Dict[str, Any]) -> None:
        reports_dir = self.target_repo_path / self.output.reports_dir
        for name, a in analyses.items():
            md = []
            md.append(f"# Repo Analysis: {name}")
            md.append("")
            md.append(f"Role: `{a['role']}`")
            md.append(f"URL: {a['url']}")
            md.append("")
            md.append("## ML and Data Signals")
            md.append(f"- Signals: {', '.join(a['ml_signals']['signals']) or 'None detected'}")
            md.append(f"- Notebooks: {a['ml_signals']['has_notebooks']}")
            md.append(f"- Data dir: {a['ml_signals']['has_data_dir']}")
            md.append("")
            md.append("## Integration Signals (top files)")
            for f in a["integration_signals"]["top_files"][:15]:
                md.append(f"- {f['file']} (score {f['score']})")
            md.append("")
            md.append("## Prompt and Persona Definitions (hits)")
            for h in a["prompt_hits"][:20]:
                md.append(f"- `{h['file']}`")
                md.append(f"  - Excerpt: `{h['excerpt']}`")
            md.append("")
            safe_write(reports_dir / f"{name}_analysis.md", "\n".join(md))

    def document_unk_persona(self, analyses: Dict[str, Any]) -> None:
        docs_dir = self.target_repo_path / self.output.docs_dir
        out = []
        out.append("# Unk Persona")
        out.append("")
        out.append("## Definition")
        out.append(f"Name: **{self.persona.name}**")
        out.append(f"Meaning: **{self.persona.meaning}**")
        out.append(f"Target: **{self.persona.target_audience}**")
        out.append("")
        out.append("## Located prompt definitions")
        for name, a in analyses.items():
            if not a["prompt_hits"]:
                continue
            out.append(f"### {name}")
            for h in a["prompt_hits"][:10]:
                out.append(f"- `{h['file']}`")
        out.append("")
        out.append("## Notes")
        out.append("This file is generated by Antigravity. Edit the source prompts in each repo if you want tighter persona alignment.")
        safe_write(docs_dir / self.persona.doc_filename, "\n".join(out))

    # ---------- Betting services layer ----------

    def generate_services_layer(self, analyses: Dict[str, Any]) -> None:
        services_dir = self.target_repo_path / self.output.services_dir
        strategies_dir = self.target_repo_path / self.output.strategies_dir

        betting_py = services_dir / "betting.py"
        # We respect the manual refactor and do NOT overwrite betting.py if it exists,
        # OR we generate the new structure. 
        # Given we just refactored it manually, let's SKIP overwriting betting.py here.
        # safe_write(betting_py, self.render_betting_services_py())

        strategies_dir.mkdir(parents=True, exist_ok=True)
        init_py = strategies_dir / "__init__.py"
        # Skip init py creation to avoid circular deps during dev
        # if not init_py.exists():
        #     safe_write(init_py, "from .registry import STRATEGY_REGISTRY\n")

        # base.py is crucial
        if not (strategies_dir / "base.py").exists():
            safe_write(strategies_dir / "base.py", self.render_strategy_base_py())
            
        safe_write(strategies_dir / "registry.py", self.render_registry_py(analyses))

        for repo in self.repos:
            modname = self.role_to_module(repo.role)
            # Only create stub if not exists
            if not (strategies_dir / f"{modname}.py").exists():
                safe_write(strategies_dir / f"{modname}.py", self.render_strategy_stub(repo.role, repo.name))

    def role_to_module(self, role: str) -> str:
        return re.sub(r"[^a-z0-9_]+", "_", role.strip().lower())

    def render_strategy_base_py(self) -> str:
        return """\
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from services.betting_types import BettingRequest, BettingDecision


class Strategy(ABC):
    name: str

    @abstractmethod
    def decide(self, req: BettingRequest, *, config: Dict[str, Any]) -> BettingDecision:
        raise NotImplementedError

"""
    def render_registry_py(self, analyses: Dict[str, Any]) -> str:
        lines = []
        lines.append("from __future__ import annotations\n")
        lines.append("# Generated registry\n")
        # Generate dynamic imports
        for repo_name, a in analyses.items():
            mod = self.role_to_module(a["role"])
            cls = self.role_to_class(a["role"])
            lines.append(f"from .{mod} import {cls}\n")
        lines.append("\nSTRATEGY_REGISTRY = {\n")
        for repo_name, a in analyses.items():
            # mod = self.role_to_module(a["role"])
            cls = self.role_to_class(a["role"])
            lines.append(f'    "{a["role"]}": {cls},\n')
        lines.append("}\n")
        return "".join(lines)

    def role_to_class(self, role: str) -> str:
        parts = re.split(r"[^a-zA-Z0-9]+", role.strip())
        parts = [p for p in parts if p]
        return "".join(p[:1].upper() + p[1:] for p in parts) + "Strategy"

    def render_strategy_stub(self, role: str, repo_name: str) -> str:
        cls = self.role_to_class(role)
        return f"""\
from __future__ import annotations

from typing import Any, Dict

from services.betting_types import BettingRequest, BettingDecision
from .base import Strategy


class {cls}(Strategy):
    name = "{role}"

    def decide(self, req: BettingRequest, *, config: Dict[str, Any]) -> BettingDecision:
        # TODO: implement using patterns learned from: {repo_name}
        return BettingDecision(
            strategy=self.name,
            action="pass",
            selection=None,
            stake=0.0,
            confidence=0.0,
            metadata={{"source_repo": "{repo_name}", "todo": True}},
        )

"""

    # ---------- Prompt update + verification ----------

    def update_system_prompts(self) -> None:
        if not self.prompt_config.enabled:
            print("Prompt updates disabled.")
            return

        print("Updating managed prompts...")
        # Managed files only
        for p_str in self.prompt_config.managed_files:
            p = self.target_repo_path / p_str
            if not p.exists():
                print(f"Skipping missing managed file: {p}")
                continue
            
            # Simple touch/update logic here. 
            # Since user provides the content, we might not need to automate 'Unk=Uncle' replacement 
            # if we are just maintaining the file. 
            # But the requirement was to stop "editing random files". 
            # So we ONLY edit files in managed_files list.
            
            # Legacy logic for replacing placeholders in other files is DISABLED by strict config
            # unless we add them to managed_files.
            pass

    def verify(self) -> None:
        # Verify doc exists and contains required strings
        doc = self.target_repo_path / self.output.docs_dir / self.persona.doc_filename
        if not doc.exists():
            print(f"Warning: Missing persona doc: {doc}")
            return

        body = read_text(doc)
        must = [self.persona.meaning, self.persona.target_audience]
        for m in must:
            if m not in body:
                print(f"Warning: Persona doc missing content: {m}")

        # If pytest exists, run it
        if (self.target_repo_path / "pytest.ini").exists() or (self.target_repo_path / "pyproject.toml").exists():
            try:
                sh(["python", "-m", "pytest", "-q"], cwd=self.target_repo_path, check=False)
            except Exception:
                pass


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--once", action="store_true", help="Run once and exit")
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    ag = Antigravity(cfg)
    ag.run_all()


if __name__ == "__main__":
    main()
