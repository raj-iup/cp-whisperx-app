#!/usr/bin/env python3
"""
Preflight Validation Script (Enhanced)
Validates all prerequisites before running the pipeline.
Saves results to out directory and supports daily caching.
"""
import sys
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Optional, Any

# Add paths for imports
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))
from scripts.manifest import ManifestBuilder

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


class PreflightCheck:
    """Preflight validation checks with manifest integration."""
    
    def __init__(self, output_dir: Path = None, force: bool = False):
        """
        Initialize preflight checker.
        
        Args:
            output_dir: Directory to save results (default: ./out)
            force: Force re-run even if recent check passed
        """
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = 0
        self.check_details = {}
        self.force = force
        
        # Setup output directory
        self.output_dir = output_dir or Path("out")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Results file location
        self.results_file = self.output_dir / "preflight_results.json"
        self.start_time = time.time()
    
    def should_run_checks(self) -> bool:
        """
        Check if preflight needs to run based on last successful run.
        
        Returns:
            True if checks should run, False if recent check is valid
        """
        if self.force:
            return True
        
        if not self.results_file.exists():
            return True
        
        try:
            with open(self.results_file, 'r') as f:
                last_results = json.load(f)
            
            # Check if last run was successful
            if last_results.get("checks_failed", 1) > 0:
                print(f"{YELLOW}Last preflight check failed - re-running{RESET}")
                return True
            
            # Check if last run was within 24 hours
            last_run = datetime.fromisoformat(last_results.get("timestamp", "2000-01-01T00:00:00"))
            age = datetime.now() - last_run
            
            if age < timedelta(hours=24):
                print(f"{GREEN}✓ Preflight check passed within last 24 hours{RESET}")
                print(f"  Last run: {last_run.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"  Age: {age.seconds // 3600}h {(age.seconds % 3600) // 60}m ago")
                print(f"  Passed: {last_results.get('checks_passed', 0)}")
                print(f"  Failed: {last_results.get('checks_failed', 0)}")
                print(f"  Warnings: {last_results.get('warnings', 0)}")
                print(f"\n{BLUE}Skipping preflight checks (use --force to re-run){RESET}")
                return False
            else:
                print(f"{YELLOW}Preflight check is older than 24 hours - re-running{RESET}")
                print(f"  Last run: {last_run.strftime('%Y-%m-%d %H:%M:%S')}")
                return True
                
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"{YELLOW}Could not read previous results: {e}{RESET}")
            return True
    
    def save_results(self, devices: Dict = None):
        """Save preflight results to output directory."""
        duration = time.time() - self.start_time
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "warnings": self.warnings,
            "duration_seconds": duration,
            "status": "success" if self.checks_failed == 0 else "failed",
            "details": self.check_details
        }
        
        # Add device information if available
        if devices:
            results["devices"] = devices
            results["pipeline_device"] = self.determine_best_device(devices)
            
            # Add note about MPS support
            if devices.get("mps", {}).get("available") and results["pipeline_device"] == "cpu":
                results["device_note"] = "MPS available but not yet supported - using CPU"
        
        # Save to output directory
        with open(self.results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Also save timestamped copy in logs
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"preflight_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n{BLUE}Results saved:{RESET}")
        print(f"  Main: {self.results_file}")
        print(f"  Log:  {log_file}")
    
    
    def print_header(self, message: str):
        """Print section header."""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}{message}{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")
    
    def print_check(self, name: str, passed: bool, details: str = ""):
        """Print check result."""
        if passed:
            self.checks_passed += 1
            status = f"{GREEN}✓ PASS{RESET}"
        else:
            self.checks_failed += 1
            status = f"{RED}✗ FAIL{RESET}"
        
        print(f"{status} {name}")
        if details:
            print(f"       {details}")
        
        # Store details
        self.check_details[name] = {
            "status": "pass" if passed else "fail",
            "details": details
        }
    
    def print_warning(self, message: str):
        """Print warning message."""
        self.warnings += 1
        print(f"{YELLOW}⚠ WARNING{RESET} {message}")
        
        # Store warning
        warning_key = f"warning_{self.warnings}"
        self.check_details[warning_key] = {
            "status": "warning",
            "message": message
        }
    
    def check_docker(self) -> bool:
        """Check if Docker is installed and running."""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True
            )
            version = result.stdout.strip()
            self.print_check("Docker installed", True, version)
            
            # Check if Docker daemon is running
            result = subprocess.run(
                ["docker", "ps"],
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )
            self.print_check("Docker daemon running", True)
            return True
            
        except subprocess.TimeoutExpired:
            self.print_check("Docker", False, "Timeout - Docker not responding")
            return False
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.print_check("Docker", False, "Docker not found or not running")
            return False
    
    def check_docker_compose(self) -> bool:
        """Check if Docker Compose is installed."""
        try:
            result = subprocess.run(
                ["docker", "compose", "version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True
            )
            version = result.stdout.strip()
            self.print_check("Docker Compose installed", True, version)
            return True
            
        except subprocess.TimeoutExpired:
            self.print_check("Docker Compose", False, "Timeout")
            return False
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.print_check("Docker Compose", False, "Not found")
            return False
    
    def check_directories(self) -> bool:
        """Check if required directories exist."""
        required_dirs = [
            "in",
            "out",
            "logs",
            "temp",
            "config",
            "shared",
            "docker"
        ]
        
        all_exist = True
        for dir_name in required_dirs:
            dir_path = Path(dir_name)
            exists = dir_path.exists() and dir_path.is_dir()
            self.print_check(f"Directory: {dir_name}/", exists)
            if not exists:
                all_exist = False
        
        return all_exist
    
    def check_config_file(self) -> Tuple[bool, Dict]:
        """Check if .env file exists and is valid."""
        config_file = Path("config/.env")
        
        if not config_file.exists():
            self.print_check("Config file (config/.env)", False, "File not found")
            return False, {}
        
        # Read and validate config
        config = {}
        try:
            with open(config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
            
            self.print_check("Config file (config/.env)", True, f"{len(config)} settings found")
            return True, config
            
        except Exception as e:
            self.print_check("Config file parsing", False, str(e))
            return False, {}
    
    def check_input_file(self, config: Dict) -> bool:
        """Check if input file exists."""
        input_file = config.get("INPUT_FILE", "")
        
        if not input_file:
            self.print_warning("INPUT_FILE not set in config/.env")
            return True  # Not a hard requirement for preflight
        
        input_path = Path(input_file)
        exists = input_path.exists() and input_path.is_file()
        
        if exists:
            size_mb = input_path.stat().st_size / (1024 * 1024)
            self.print_check(f"Input file: {input_file}", True, f"Size: {size_mb:.2f} MB")
        else:
            self.print_check(f"Input file: {input_file}", False, "File not found")
        
        return exists
    
    def check_docker_compose_config(self) -> bool:
        """Check if docker-compose configuration is valid."""
        compose_file = Path("docker-compose.yml")
        
        if not compose_file.exists():
            self.print_check("Docker Compose config", False, "docker-compose.yml not found")
            return False
        
        try:
            # Read and parse the compose file
            with open(compose_file, 'r') as f:
                content = f.read()
            
            # Check for all 10 required services according to workflow-arch.txt
            # Note: TMDB is handled inline by orchestrator, not a separate service
            required_services = [
                ("demux", "Stage 1: FFmpeg audio extraction"),
                ("pre-ner", "Stage 3: Pre-ASR NER"),
                ("silero-vad", "Stage 4: Silero VAD"),
                ("pyannote-vad", "Stage 5: PyAnnote VAD"),
                ("diarization", "Stage 6: PyAnnote Diarization (MANDATORY)"),
                ("asr", "Stage 7: WhisperX ASR"),
                ("post-ner", "Stage 8: Post-ASR NER"),
                ("subtitle-gen", "Stage 9: Subtitle Generation"),
                ("mux", "Stage 10: FFmpeg Mux"),
            ]
            
            services_found = []
            services_missing = []
            
            for service, description in required_services:
                # Check if service is defined in the compose file
                if f"\n  {service}:" in content or f"\n  {service}:\n" in content:
                    services_found.append(f"{service} ({description})")
                else:
                    services_missing.append(f"{service} ({description})")
            
            if services_missing:
                self.print_check("Docker Compose config", False, f"Missing services: {len(services_missing)}")
                for service in services_missing:
                    self.print_warning(f"  Missing: {service}")
                return False
            else:
                self.print_check("Docker Compose config", True, f"All 9 containerized services configured")
                print(f"{GREEN}       Note: TMDB (Stage 2) handled by orchestrator{RESET}")
                return True
            
            return True
            
        except Exception as e:
            self.print_warning(f"Could not validate Docker Compose config: {str(e)}")
            return True
    
    def check_docker_images(self) -> bool:
        """Check if Docker images are available."""
        try:
            result = subprocess.run(
                ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"],
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )
            
            images = result.stdout.strip().split('\n')
            
            # Check for base image
            base_image = f"rajiup/cp-whisperx-app-base:latest"
            has_base = any(base_image in img for img in images)
            
            if has_base:
                self.print_check("Docker base image", True, base_image)
            else:
                self.print_warning(f"Base image not found: {base_image}")
                self.print_warning("Run: docker build -f docker/base/Dockerfile -t rajiup/cp-whisperx-app-base:latest .")
            
            # Check for all 10 pipeline stage images (according to workflow-arch.txt)
            stage_images = [
                ("demux", "rajiup/cp-whisperx-app-demux:latest", "Stage 1: FFmpeg audio extraction"),
                ("tmdb", "rajiup/cp-whisperx-app-tmdb:latest", "Stage 2: TMDB metadata fetch"),
                ("pre-ner", "rajiup/cp-whisperx-app-pre-ner:latest", "Stage 3: Pre-ASR NER"),
                ("silero-vad", "rajiup/cp-whisperx-app-silero-vad:latest", "Stage 4: Silero VAD"),
                ("pyannote-vad", "rajiup/cp-whisperx-app-pyannote-vad:latest", "Stage 5: PyAnnote VAD"),
                ("diarization", "rajiup/cp-whisperx-app-diarization:latest", "Stage 6: PyAnnote Diarization"),
                ("asr", "rajiup/cp-whisperx-app-asr:latest", "Stage 7: WhisperX ASR"),
                ("post-ner", "rajiup/cp-whisperx-app-post-ner:latest", "Stage 8: Post-ASR NER"),
                ("subtitle-gen", "rajiup/cp-whisperx-app-subtitle-gen:latest", "Stage 9: Subtitle Generation"),
                ("mux", "rajiup/cp-whisperx-app-mux:latest", "Stage 10: FFmpeg Mux"),
            ]
            
            images_found = 0
            images_missing = 0
            
            for stage_name, stage_image, description in stage_images:
                has_stage = any(stage_image in img for img in images)
                
                if has_stage:
                    self.print_check(f"  {stage_name}", True, description)
                    images_found += 1
                else:
                    self.print_warning(f"Image missing: {stage_image}")
                    self.print_warning(f"  {description}")
                    images_missing += 1
            
            if images_missing > 0:
                self.print_warning(f"\n{images_missing} of 10 container images not built")
                self.print_warning("Run: docker compose build")
            else:
                print(f"{GREEN}       All 10 container images ready!{RESET}")
            
            return True
            
        except subprocess.CalledProcessError:
            self.print_warning("Could not check Docker images")
            return True
    
    def check_secrets(self) -> bool:
        """Check if API keys and tokens are configured."""
        secrets_file = Path("config/secrets.json")
        
        if not secrets_file.exists():
            self.print_warning("Secrets file not found: config/secrets.json")
            self.print_warning("Some features may not work without API keys")
            self.print_warning("  Create from: cp config/secrets.example.json config/secrets.json")
            return True  # Not a hard requirement
        
        try:
            with open(secrets_file, 'r') as f:
                secrets = json.load(f)
            
            # Check TMDB API Key (both uppercase and lowercase)
            has_tmdb = (secrets.get("TMDB_API_KEY") or secrets.get("tmdb_api_key"))
            if has_tmdb:
                self.print_check("TMDB API key", True, "For movie metadata enrichment")
            else:
                self.print_warning("TMDB API key not found in secrets")
                self.print_warning("  Used by: TMDB metadata stage")
                self.print_warning("  Impact: Cannot fetch movie cast, plot, keywords")
            
            # Check HuggingFace Token (both uppercase and lowercase)
            has_hf = (secrets.get("HF_TOKEN") or secrets.get("hf_token"))
            if has_hf:
                self.print_check("HuggingFace token", True, "For PyAnnote VAD and Diarization")
            else:
                self.print_warning("HuggingFace token not found in secrets")
                self.print_warning("  Used by: PyAnnote VAD and Diarization stages")
                self.print_warning("  Impact: PyAnnote models may fail to load")
                self.print_warning("  Get token: https://huggingface.co/settings/tokens")
            
            return True
            
        except json.JSONDecodeError:
            self.print_warning("Secrets file is not valid JSON")
            return True
        except Exception as e:
            self.print_warning(f"Could not read secrets file: {e}")
            return True
    
    def check_disk_space(self) -> bool:
        """Check available disk space."""
        try:
            import shutil
            stat = shutil.disk_usage(".")
            
            free_gb = stat.free / (1024 ** 3)
            total_gb = stat.total / (1024 ** 3)
            
            # Warn if less than 10GB free
            if free_gb < 10:
                self.print_check("Disk space", False, f"{free_gb:.1f}GB free (need at least 10GB)")
                return False
            else:
                self.print_check("Disk space", True, f"{free_gb:.1f}GB free / {total_gb:.1f}GB total")
                return True
                
        except Exception:
            self.print_warning("Could not check disk space")
            return True
    
    def check_compute_devices(self) -> Dict[str, Any]:
        """
        Check available compute devices (CUDA, MPS, CPU).
        Cross-platform: Windows (CUDA), Linux (CUDA), macOS (MPS/CUDA).
        
        Returns:
            Dict with device capabilities
        """
        import platform
        system = platform.system()
        
        devices = {
            "platform": system,
            "cuda": {"available": False, "device_count": 0, "devices": []},
            "mps": {"available": False},
            "cpu": {"available": True}  # CPU always available
        }
        
        try:
            import torch
            
            # Check CUDA (Windows, Linux, macOS with eGPU)
            if torch.cuda.is_available():
                devices["cuda"]["available"] = True
                devices["cuda"]["device_count"] = torch.cuda.device_count()
                devices["cuda"]["cuda_version"] = torch.version.cuda
                devices["cuda"]["cudnn_version"] = torch.backends.cudnn.version() if torch.backends.cudnn.is_available() else None
                
                for i in range(torch.cuda.device_count()):
                    device_info = {
                        "id": i,
                        "name": torch.cuda.get_device_name(i),
                        "compute_capability": f"{torch.cuda.get_device_capability(i)[0]}.{torch.cuda.get_device_capability(i)[1]}",
                        "total_memory_gb": torch.cuda.get_device_properties(i).total_memory / (1024**3)
                    }
                    devices["cuda"]["devices"].append(device_info)
                
                # Platform-specific CUDA info
                if system == 'Windows':
                    self.print_check("CUDA available (Windows)", True, 
                                   f"{devices['cuda']['device_count']} device(s), CUDA {devices['cuda']['cuda_version']}")
                else:
                    self.print_check("CUDA available", True, 
                                   f"{devices['cuda']['device_count']} device(s), CUDA {devices['cuda']['cuda_version']}")
                
                for dev in devices["cuda"]["devices"]:
                    print(f"       GPU {dev['id']}: {dev['name']} ({dev['total_memory_gb']:.1f}GB VRAM, CC {dev['compute_capability']})")
                
                # Windows-specific: Check if NVIDIA driver version is sufficient
                if system == 'Windows':
                    try:
                        result = subprocess.run(
                            ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
                            capture_output=True,
                            text=True,
                            timeout=10,
                            check=True
                        )
                        driver_version = result.stdout.strip()
                        print(f"       NVIDIA Driver: {driver_version}")
                        devices["cuda"]["driver_version"] = driver_version
                    except:
                        pass
                
            else:
                if system == 'Windows':
                    self.print_check("CUDA available (Windows)", False, "No NVIDIA GPU detected or CUDA not installed")
                    self.print_warning("For GPU acceleration on Windows, install:")
                    self.print_warning("  1. NVIDIA Driver 560.94+ from https://www.nvidia.com/Download/index.aspx")
                    self.print_warning("  2. CUDA Toolkit 12.6+ from https://developer.nvidia.com/cuda-downloads")
                    self.print_warning("  3. PyTorch with CUDA: pip install torch --index-url https://download.pytorch.org/whl/cu121")
                else:
                    self.print_check("CUDA available", False, "No NVIDIA GPU detected")
            
            # Check MPS (macOS Apple Silicon only)
            if system == 'Darwin':  # macOS
                if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                    devices["mps"]["available"] = True
                    self.print_check("MPS available (Apple Silicon)", True, "Metal Performance Shaders acceleration")
                else:
                    self.print_check("MPS available", False, "Not available (Intel Mac or macOS < 12.3)")
            
            # CPU is always available
            self.print_check("CPU available", True, f"Fallback device on {system}")
            
            # Determine recommended device
            if devices["cuda"]["available"]:
                recommended = "cuda"
                if system == 'Windows':
                    print(f"{GREEN}       Recommended: CUDA (Windows native with NVIDIA GPU){RESET}")
                else:
                    print(f"{GREEN}       Recommended: CUDA (NVIDIA GPU acceleration){RESET}")
            elif devices["mps"]["available"]:
                recommended = "mps"
                print(f"{GREEN}       Recommended: MPS (Apple Silicon acceleration){RESET}")
            else:
                recommended = "cpu"
                print(f"{YELLOW}       Recommended: CPU (no GPU acceleration available){RESET}")
            
            devices["recommended"] = recommended
            
        except ImportError:
            self.print_warning("PyTorch not installed - cannot check GPU support")
            self.print_warning("Install PyTorch to enable GPU acceleration")
            if system == 'Windows':
                self.print_warning("  For Windows with CUDA: pip install torch --index-url https://download.pytorch.org/whl/cu121")
            devices["recommended"] = "cpu"
        except Exception as e:
            self.print_warning(f"Error checking compute devices: {e}")
            devices["recommended"] = "cpu"
        
        return devices 
                               f"{devices['cuda']['device_count']} device(s)")
                for dev in devices["cuda"]["devices"]:
                    print(f"       GPU {dev['id']}: {dev['name']}")
                    print(f"       Compute: {dev['compute_capability']}, Memory: {dev['total_memory_gb']:.1f}GB")
            else:
                # CUDA not available - not a failure, just informational
                print(f"{BLUE}ℹ INFO{RESET} CUDA not available (no NVIDIA GPUs)")
            
            # Check MPS (Apple Silicon)
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                devices["mps"]["available"] = True
                self.print_check("MPS (Apple Silicon) available", True, "Metal Performance Shaders enabled")
            else:
                print(f"{BLUE}ℹ INFO{RESET} MPS not available (not Apple Silicon)")
            
            # CPU is always available
            import platform
            cpu_info = f"{platform.processor()} ({platform.machine()})"
            self.print_check("CPU available", True, cpu_info)
            
            # At least one GPU acceleration should be available for best performance
            if not devices["cuda"]["available"] and not devices["mps"]["available"]:
                self.print_warning("No GPU acceleration available - pipeline will use CPU (slower)")
            
        except ImportError:
            self.print_warning("PyTorch not installed - cannot detect GPU capabilities")
            self.print_warning("  Install: pip install torch")
        except Exception as e:
            self.print_warning(f"Error checking compute devices: {e}")
        
        return devices
    
    def determine_best_device(self, devices: Dict) -> str:
        """
        Determine the best compute device to use (cross-platform).
        
        Priority (Windows/Linux): CUDA > CPU
        Priority (macOS): MPS > CPU
        
        Returns:
            Device string: "cuda", "mps", or "cpu"
        """
        system = devices.get("platform", "Unknown")
        
        if system == "Darwin":  # macOS
            # Prefer MPS on Apple Silicon
            if devices.get("mps", {}).get("available"):
                return "mps"
            # Fallback to CUDA if available (Intel Mac with eGPU)
            if devices.get("cuda", {}).get("available"):
                return "cuda"
        else:  # Windows or Linux
            # Prefer CUDA on Windows/Linux
            if devices.get("cuda", {}).get("available"):
                return "cuda"
        
        # Ultimate fallback
        return "cpu"
    
    def check_memory(self) -> bool:
        """Check available system memory."""
        try:
            import psutil
            mem = psutil.virtual_memory()
            
            total_gb = mem.total / (1024 ** 3)
            available_gb = mem.available / (1024 ** 3)
            
            # Warn if less than 8GB available
            if available_gb < 8:
                self.print_warning(f"Low memory: {available_gb:.1f}GB available (recommend at least 8GB)")
            else:
                self.print_check("System memory", True, f"{available_gb:.1f}GB available / {total_gb:.1f}GB total")
            
            return True
            
        except ImportError:
            self.print_warning("psutil not installed - cannot check memory")
            return True
        except Exception:
            self.print_warning("Could not check system memory")
            return True
    
    def run_all_checks(self) -> bool:
        """Run all preflight checks."""
        # Print banner
        print(f"\n{BLUE}╔{'═'*58}╗{RESET}")
        print(f"{BLUE}║{' '*58}║{RESET}")
        print(f"{BLUE}║  CP-WHISPERX-APP PREFLIGHT VALIDATION{' '*20}║{RESET}")
        print(f"{BLUE}║{' '*58}║{RESET}")
        print(f"{BLUE}╚{'═'*58}╝{RESET}")
        
        # Check if we need to run based on last successful check
        if not self.should_run_checks():
            return True  # Valid recent check exists
        
        # Docker checks
        self.print_header("Docker Environment")
        docker_ok = self.check_docker()
        compose_ok = self.check_docker_compose()
        
        if not docker_ok or not compose_ok:
            print(f"\n{RED}✗ CRITICAL: Docker environment not ready{RESET}")
            self.save_results()
            return False
        
        # Directory structure
        self.print_header("Directory Structure")
        self.check_directories()
        
        # Configuration
        self.print_header("Configuration")
        config_ok, config = self.check_config_file()
        if config_ok:
            self.check_input_file(config)
            self.check_secrets()
        
        # Docker images
        self.print_header("Docker Images")
        self.check_docker_images()
        
        # Docker Compose configuration
        self.print_header("Docker Compose Configuration")
        self.check_docker_compose_config()
        
        # System resources
        self.print_header("System Resources")
        self.check_disk_space()
        self.check_memory()
        
        # Compute devices
        self.print_header("Compute Devices")
        devices = self.check_compute_devices()
        best_device = self.determine_best_device(devices)
        
        print(f"\n{GREEN}Pipeline device: {best_device.upper()}{RESET}")
        if best_device == "cuda":
            if devices.get("platform") == "Windows":
                print(f"       Using CUDA GPU acceleration (Windows native)")
            else:
                print(f"       Using CUDA GPU acceleration")
        elif best_device == "mps":
            print(f"       Using MPS GPU acceleration (Apple Silicon)")
        else:
            print(f"       Using CPU (no GPU acceleration available)")
        
        # Summary
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}PREFLIGHT CHECK SUMMARY{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")
        print(f"{GREEN}Passed: {self.checks_passed}{RESET}")
        print(f"{RED}Failed: {self.checks_failed}{RESET}")
        print(f"{YELLOW}Warnings: {self.warnings}{RESET}")
        
        # Save results with device info
        self.save_results(devices)
        
        if self.checks_failed == 0:
            print(f"\n{GREEN}✓ All critical checks passed!{RESET}")
            print(f"{GREEN}Pipeline is ready to run.{RESET}")
            
            if self.warnings > 0:
                print(f"\n{YELLOW}Note: {self.warnings} warning(s) detected.{RESET}")
                print(f"{YELLOW}Pipeline may still run, but some features might be limited.{RESET}")
            
            return True
        else:
            print(f"\n{RED}✗ {self.checks_failed} critical check(s) failed.{RESET}")
            print(f"{RED}Please fix the issues before running the pipeline.{RESET}")
            return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Preflight validation for CP-WhisperX-App pipeline")
    parser.add_argument("--output-dir", type=Path, default=Path("out"),
                       help="Output directory for results (default: ./out)")
    parser.add_argument("--force", action="store_true",
                       help="Force re-run even if recent check passed")
    args = parser.parse_args()
    
    checker = PreflightCheck(output_dir=args.output_dir, force=args.force)
    success = checker.run_all_checks()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
