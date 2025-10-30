#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Generates a CUDA environment report on Windows 11 Pro machines with NVIDIA GPUs.
- Prefers NVML (pynvml), falls back to nvidia-smi, and finally to WMI for GPU names.
- Produces a text report with driver, CUDA runtime support, GPUs, compute capability.
- Recommends a CUDA container base image tag that will be compatible with the host driver.

Run:
  py -3 generate_cuda_report.py
  # Report: cuda_env_report.txt in the current directory
"""

import os
import re
import subprocess
import sys
import datetime
import platform
from shutil import which

REPORT_PATH = os.path.abspath("cuda_env_report.txt")

# Known CUDA tags to choose from (descending). Update over time if needed.
KNOWN_CUDA_VERSIONS = [
    "12.6", "12.5", "12.4", "12.3", "12.2", "12.1", "12.0",
    "11.8", "11.7", "11.6", "11.5", "11.4", "11.3", "11.2", "11.1", "11.0"
]

def run(cmd):
    try:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        return e.output or ""

def parse_cuda_version_from_nvidia_smi_header(text):
    # Typical header line example:
    # | NVIDIA-SMI 552.22       Driver Version: 552.22       CUDA Version: 12.4   |
    m = re.search(r"CUDA Version:\s*([0-9]+\.[0-9]+)", text)
    return m.group(1).strip() if m else None

def parse_driver_version_from_nvidia_smi_header(text):
    m = re.search(r"Driver Version:\s*([0-9\.]+)", text)
    return m.group(1).strip() if m else None

def query_with_nvidia_smi():
    if not which("nvidia-smi"):
        return None
    header = run("nvidia-smi")
    cuda_ver = parse_cuda_version_from_nvidia_smi_header(header)
    driver_ver = parse_driver_version_from_nvidia_smi_header(header)

    # Query per-GPU fields (compute capability supported in newer drivers)
    # Fields list: run "nvidia-smi --help-query-gpu"
    qfields = [
        "index", "name", "memory.total", "compute_cap"
    ]
    q = run(f'nvidia-smi --query-gpu={",".join(qfields)} --format=csv,noheader')
    gpus = []
    for line in q.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= len(qfields):
            idx, name, mem, cc = parts[:4]
            # normalize mem like "24576 MiB"
            mem_gib = None
            mm = re.search(r"([0-9]+)\s*MiB", mem)
            if mm:
                mem_mib = int(mm.group(1))
                mem_gib = round(mem_mib / 1024.0, 2)
            gpus.append({
                "index": idx,
                "name": name,
                "memory_gib": mem_gib,
                "compute_cap": cc if cc and cc.lower() != "n/a" else None
            })
    return {
        "source": "nvidia-smi",
        "driver_version": driver_ver,
        "cuda_runtime_version": cuda_ver,
        "gpus": gpus,
        "raw_header": header,
    }

def query_with_pynvml():
    try:
        import pynvml
    except Exception:
        return None
    try:
        pynvml.nvmlInit()
    except Exception:
        return None
    try:
        count = pynvml.nvmlDeviceGetCount()
        gpus = []
        for i in range(count):
            h = pynvml.nvmlDeviceGetHandleByIndex(i)
            name = pynvml.nvmlDeviceGetName(h).decode("utf-8", errors="ignore")
            mem = pynvml.nvmlDeviceGetMemoryInfo(h).total  # bytes
            mem_gib = round(mem / (1024**3), 2)

            # Try compute capability (not always available via NVML Python)
            # Use device minor attributes if present; else leave None.
            cc = None
            try:
                # NVML 12+ exposes nvmlDeviceGetCudaComputeCapability
                major = pynvml.nvmlDeviceGetCudaComputeCapability(h)[0]
                minor = pynvml.nvmlDeviceGetCudaComputeCapability(h)[1]
                cc = f"{major}.{minor}"
            except Exception:
                pass

            gpus.append({
                "index": str(i),
                "name": name,
                "memory_gib": mem_gib,
                "compute_cap": cc
            })
        driver_ver = pynvml.nvmlSystemGetDriverVersion().decode("utf-8", errors="ignore")
        # NVML doesn’t directly expose host CUDA runtime support; we’ll fill from nvidia-smi later if available.
        return {
            "source": "pynvml",
            "driver_version": driver_ver,
            "cuda_runtime_version": None,
            "gpus": gpus
        }
    finally:
        try:
            pynvml.nvmlShutdown()
        except Exception:
            pass

def query_gpu_names_wmi():
    # Last-resort GPU names using WMI
    try:
        import wmi
        c = wmi.WMI()
        names = [x.Name for x in c.Win32_VideoController()]
        return names
    except Exception:
        return None

def choose_cuda_tag(host_cuda_ver_str):
    """
    Given a host-supported CUDA version string like "12.4",
    choose the highest known CUDA version <= host version.
    """
    if not host_cuda_ver_str:
        return None
    def ver_tuple(s): return tuple(int(x) for x in s.split("."))
    host_t = ver_tuple(host_cuda_ver_str)
    for v in KNOWN_CUDA_VERSIONS:
        if ver_tuple(v) <= host_t:
            return v
    return None

def build_report(data):
    lines = []
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os_str = f"{platform.system()} {platform.release()} ({platform.version()})"
    lines.append("CUDA Environment Report")
    lines.append("=" * 80)
    lines.append(f"Generated:           {now}")
    lines.append(f"Host OS:             {os_str}")
    lines.append("")
    lines.append("Detection")
    lines.append("-" * 80)
    lines.append(f"Primary data source: {data.get('source','(unknown)')}")
    lines.append(f"NVIDIA Driver:       {data.get('driver_version') or '(unknown)'}")
    lines.append(f"CUDA (host support): {data.get('cuda_runtime_version') or '(unknown)'}")
    lines.append("")

    lines.append("GPUs")
    lines.append("-" * 80)
    gpus = data.get("gpus") or []
    if not gpus:
        lines.append("No GPUs detected.")
    else:
        for g in gpus:
            idx = g.get("index","?")
            nm = g.get("name","?")
            mem = f"{g['memory_gib']} GiB" if g.get("memory_gib") is not None else "unknown"
            cc = g.get("compute_cap") or "unknown"
            lines.append(f"GPU {idx}: {nm} | VRAM: {mem} | Compute Capability: {cc}")
    lines.append("")

    # Recommendation
    host_cuda = data.get("cuda_runtime_version")
    chosen = choose_cuda_tag(host_cuda) if host_cuda else None
    lines.append("Recommendation")
    lines.append("-" * 80)
    if chosen:
        lines.append(f"Recommended CUDA base image tag (compatible): {chosen}")
        lines.append(f"Examples:")
        lines.append(f"  - nvidia/cuda:{chosen}-devel-ubuntu22.04")
        lines.append(f"  - nvidia/cuda:{chosen}-runtime-ubuntu22.04")
        lines.append("")
        lines.append("Rationale:")
        lines.append(f"  Use a container CUDA version ≤ host-supported CUDA ({host_cuda}) to ensure driver compatibility.")
    else:
        lines.append("Could not determine a recommended CUDA tag (no host CUDA reported).")
        lines.append("Ensure NVIDIA drivers are installed and `nvidia-smi` is on PATH, then re-run.")

    lines.append("")
    lines.append("Notes")
    lines.append("-" * 80)
    lines.append("* NVIDIA drivers are backward-compatible with container CUDA runtimes (same major, lower/equal minor).")
    lines.append("* For performance-tuned builds, also match the compute capability (sm_XY) to your GPUs during compilation.")
    lines.append("* To run CUDA containers on Windows, install the NVIDIA Container Toolkit on the host.")
    lines.append("")

    return "\n".join(lines)

def main():
    # Try NVML first
    data = query_with_pynvml()

    # Overlay with nvidia-smi (adds CUDA runtime and compute_cap if available)
    smi = query_with_nvidia_smi()
    if smi:
        if not data:
            data = smi
        else:
            # Merge: prefer driver from NVML if both present, but take CUDA from nvidia-smi
            data.setdefault("gpus", [])
            # If NVML had no GPUs but nvidia-smi does, take them
            if not data["gpus"] and smi.get("gpus"):
                data["gpus"] = smi["gpus"]
            else:
                # If NVML GPUs lack compute_cap but nvidia-smi has it, merge by index
                smi_map = {g["index"]: g for g in (smi.get("gpus") or [])}
                for g in data["gpus"]:
                    sm = smi_map.get(g.get("index"))
                    if sm and not g.get("compute_cap") and sm.get("compute_cap"):
                        g["compute_cap"] = sm["compute_cap"]
                    if sm and not g.get("memory_gib") and sm.get("memory_gib"):
                        g["memory_gib"] = sm["memory_gib"]
            # Driver: keep NVML’s if present, else take from nvidia-smi
            if not data.get("driver_version") and smi.get("driver_version"):
                data["driver_version"] = smi["driver_version"]
            # CUDA runtime support definitely comes from nvidia-smi
            data["cuda_runtime_version"] = smi.get("cuda_runtime_version")

    if not data:
        data = {
            "source": "fallback",
            "driver_version": None,
            "cuda_runtime_version": None,
            "gpus": []
        }
        # Try WMI just to at least list adapter names
        names = query_gpu_names_wmi()
        if names:
            data["gpus"] = [{"index": str(i), "name": nm, "memory_gib": None, "compute_cap": None}
                            for i, nm in enumerate(names)]

    report = build_report(data)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nReport written to: {REPORT_PATH}\n")
    print(report)

if __name__ == "__main__":
    main()