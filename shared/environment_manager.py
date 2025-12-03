#!/usr/bin/env python3
"""
Environment Manager
Manages multiple Python virtual environments for pipeline stages
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class EnvironmentManager:
    """Manages multiple Python virtual environments"""
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize environment manager
        
        Args:
            project_root: Project root directory (defaults to parent of this file)
        """
        if project_root is None:
            project_root = Path(__file__).parent.parent
        
        self.project_root = Path(project_root).resolve()
        self.hardware_cache_file = self.project_root / "config" / "hardware_cache.json"
        self.hardware_cache = self._load_hardware_cache()
    
    def _load_hardware_cache(self) -> Dict:
        """Load hardware cache configuration"""
        if not self.hardware_cache_file.exists():
            raise FileNotFoundError(f"Hardware cache not found: {self.hardware_cache_file}")
        
        with open(self.hardware_cache_file, 'r') as f:
            return json.load(f)
    
    def get_environment_for_stage(self, stage_name: str) -> Optional[str]:
        """
        Get the environment name required for a specific stage
        
        Args:
            stage_name: Name of the pipeline stage
            
        Returns:
            Environment name or None if not found
        """
        mapping = self.hardware_cache.get("stage_to_environment_mapping", {})
        return mapping.get(stage_name)
    
    def get_environment_path(self, env_name: str) -> Path:
        """
        Get the path to a virtual environment
        
        Args:
            env_name: Name of the environment
            
        Returns:
            Path to the virtual environment
        """
        env_info = self.hardware_cache["environments"].get(env_name)
        if not env_info:
            raise ValueError(f"Unknown environment: {env_name}")
        
        env_path = self.project_root / env_info["path"]
        return env_path
    
    def get_python_executable(self, env_name: str) -> Path:
        """
        Get the Python executable path for an environment
        
        Args:
            env_name: Name of the environment
            
        Returns:
            Path to the Python executable
        """
        env_path = self.get_environment_path(env_name)
        python_exe = env_path / "bin" / "python"
        
        if not python_exe.exists():
            raise FileNotFoundError(f"Python executable not found: {python_exe}")
        
        return python_exe
    
    def get_activation_command(self, env_name: str) -> str:
        """
        Get the activation command for an environment
        
        Args:
            env_name: Name of the environment
            
        Returns:
            Activation command string
        """
        env_path = self.get_environment_path(env_name)
        activate_script = env_path / "bin" / "activate"
        
        if not activate_script.exists():
            raise FileNotFoundError(f"Activation script not found: {activate_script}")
        
        return f"source {activate_script}"
    
    def is_environment_installed(self, env_name: str) -> bool:
        """
        Check if an environment is installed
        
        Args:
            env_name: Name of the environment
            
        Returns:
            True if environment exists and is valid
        """
        try:
            python_exe = self.get_python_executable(env_name)
            return python_exe.exists()
        except (ValueError, FileNotFoundError):
            return False
    
    def get_environments_for_workflow(self, workflow: str) -> List[str]:
        """
        Get list of environments required for a workflow
        
        Args:
            workflow: Workflow name (transcribe, translate, subtitle)
            
        Returns:
            List of environment names
        """
        mapping = self.hardware_cache.get("workflow_to_environments_mapping", {})
        return mapping.get(workflow, [])
    
    def has_environment(self, env_name: str) -> bool:
        """
        Check if a specific environment exists and is installed
        
        Args:
            env_name: Name of the environment
            
        Returns:
            True if environment exists in hardware cache and is installed
        """
        if env_name not in self.hardware_cache.get("environments", {}):
            return False
        return self.is_environment_installed(env_name)
    
    def get_asr_environment(self, backend: Optional[str] = None) -> str:
        """
        Determine which environment to use for ASR based on backend
        
        This implements dynamic environment selection to ensure the correct
        virtual environment is used based on the requested Whisper backend.
        
        Args:
            backend: Requested backend (mlx, whisperx, auto, or None)
                    If None or auto, will be determined from hardware
            
        Returns:
            Environment name to use ('mlx' or 'whisperx')
            
        Note:
            - MLX backend requires the 'mlx' environment
            - Falls back to 'whisperx' if mlx not available
            - Logs warnings when fallback occurs
        """
        if not backend or backend.lower() == 'auto':
            # Determine backend from hardware
            has_mps = self.hardware_cache.get("hardware", {}).get("has_mps", False)
            backend = "mlx" if has_mps else "whisperx"
        
        backend_lower = backend.lower()
        
        if backend_lower == 'mlx':
            if self.has_environment('mlx'):
                return 'mlx'
            else:
                # Log warning but don't fail - caller will handle
                import sys
                logger.info(f"[WARNING] MLX backend requested but mlx environment not found", file=sys.stderr)
                logger.info(f"[WARNING] Falling back to whisperx environment", file=sys.stderr)
                return 'whisperx'
        else:
            return 'whisperx'
    
    def validate_environments_for_workflow(self, workflow: str) -> Tuple[bool, List[str]]:
        """
        Validate that all required environments are installed for a workflow
        
        Args:
            workflow: Workflow name
            
        Returns:
            Tuple of (all_valid, list_of_missing_environments)
        """
        required_envs = self.get_environments_for_workflow(workflow)
        missing = []
        
        for env_name in required_envs:
            if not self.is_environment_installed(env_name):
                missing.append(env_name)
        
        return len(missing) == 0, missing
    
    def run_in_environment(
        self,
        env_name: str,
        command: List[str],
        capture_output: bool = False,
        check: bool = True,
        **kwargs
    ) -> subprocess.CompletedProcess:
        """
        Run a command in a specific environment
        
        Args:
            env_name: Name of the environment
            command: Command and arguments to run
            capture_output: Whether to capture output
            check: Whether to check return code
            **kwargs: Additional arguments for subprocess.run
            
        Returns:
            CompletedProcess instance
        """
        python_exe = self.get_python_executable(env_name)
        
        # Build command with Python from the specific environment
        if command[0] == "python":
            command[0] = str(python_exe)
        else:
            # Prepend Python executable for Python scripts
            command = [str(python_exe)] + command
        
        # Set up environment variables
        env = os.environ.copy()
        env["VIRTUAL_ENV"] = str(self.get_environment_path(env_name))
        env["PATH"] = f"{self.get_environment_path(env_name) / 'bin'}:{env['PATH']}"
        
        # Set cache paths from hardware cache configuration
        cache_config = self.hardware_cache.get("cache", {})
        cache_paths_set = []
        
        if "torch_home" in cache_config:
            torch_home = str(self.project_root / cache_config["torch_home"])
            env["TORCH_HOME"] = torch_home
            cache_paths_set.append(f"TORCH_HOME={torch_home}")
            
        if "hf_home" in cache_config:
            hf_home = str(self.project_root / cache_config["hf_home"])
            env["HF_HOME"] = hf_home
            env["TRANSFORMERS_CACHE"] = hf_home
            cache_paths_set.append(f"HF_HOME={hf_home}")
            
        if "mlx_home" in cache_config:
            mlx_home = str(self.project_root / cache_config["mlx_home"])
            env["MLX_CACHE_DIR"] = mlx_home
            cache_paths_set.append(f"MLX_CACHE_DIR={mlx_home}")
        
        # Log cache paths (debug level) - visible when DEBUG_MODE=true
        if cache_paths_set and os.environ.get("DEBUG_MODE", "false").lower() == "true":
            logger.info(f"[CACHE] Using local cache directories:", file=sys.stderr)
            for cache_path in cache_paths_set:
                logger.info(f"[CACHE]   {cache_path}", file=sys.stderr)
        
        # Run the command
        return subprocess.run(
            command,
            capture_output=capture_output,
            check=check,
            env=env,
            **kwargs
        )
    
    def get_environment_info(self, env_name: str) -> Dict:
        """
        Get detailed information about an environment
        
        Args:
            env_name: Name of the environment
            
        Returns:
            Dictionary with environment information
        """
        env_info = self.hardware_cache["environments"].get(env_name)
        if not env_info:
            raise ValueError(f"Unknown environment: {env_name}")
        
        return env_info
    
    def list_all_environments(self) -> List[str]:
        """
        List all available environments
        
        Returns:
            List of environment names
        """
        return list(self.hardware_cache["environments"].keys())
    
    def get_stage_list_for_environment(self, env_name: str) -> List[str]:
        """
        Get list of stages that use a specific environment
        
        Args:
            env_name: Name of the environment
            
        Returns:
            List of stage names
        """
        env_info = self.get_environment_info(env_name)
        return env_info.get("stages", [])


def main():
    """CLI interface for environment manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Environment Manager CLI")
    parser.add_argument("command", choices=[
        "list", "info", "check", "validate", "python-path"
    ], help="Command to execute")
    parser.add_argument("--env", help="Environment name")
    parser.add_argument("--workflow", help="Workflow name")
    parser.add_argument("--stage", help="Stage name")
    
    args = parser.parse_args()
    
    manager = EnvironmentManager()
    
    if args.command == "list":
        envs = manager.list_all_environments()
        for env in envs:
            installed = "✓" if manager.is_environment_installed(env) else "✗"
            logger.info(f"{installed} {env}")
    
    elif args.command == "info":
        if not args.env:
            logger.error("Error: --env required", file=sys.stderr)
            sys.exit(1)
        
        info = manager.get_environment_info(args.env)
        logger.info(json.dumps(info, indent=2))
    
    elif args.command == "check":
        if not args.env:
            logger.error("Error: --env required", file=sys.stderr)
            sys.exit(1)
        
        if manager.is_environment_installed(args.env):
            logger.info(f"✓ {args.env} is installed")
            sys.exit(0)
        else:
            logger.info(f"✗ {args.env} is NOT installed")
            sys.exit(1)
    
    elif args.command == "validate":
        if not args.workflow:
            logger.error("Error: --workflow required", file=sys.stderr)
            sys.exit(1)
        
        valid, missing = manager.validate_environments_for_workflow(args.workflow)
        if valid:
            logger.info(f"✓ All environments for '{args.workflow}' are installed")
            sys.exit(0)
        else:
            logger.info(f"✗ Missing environments for '{args.workflow}': {', '.join(missing)}")
            sys.exit(1)
    
    elif args.command == "python-path":
        if not args.env:
            logger.error("Error: --env required", file=sys.stderr)
            sys.exit(1)
        
        python_exe = manager.get_python_executable(args.env)
        logger.info(python_exe)


if __name__ == "__main__":
    main()
