# CUDA Setup & Environment Guide
_For Windows 11 Pro with NVIDIA GPU — Container-Ready Configuration_

---

## 🚀 Quick Start for Developers

1. Install the latest NVIDIA driver and ensure `nvidia-smi` works.
2. Run `py -3 generate_cuda_report.py` to generate `cuda_env_report.txt`.
3. Install NVIDIA Container Toolkit in WSL2 (Ubuntu).
4. Use the recommended base image (e.g., `nvidia/cuda:12.4-devel-ubuntu22.04`) in your Dockerfile.
5. Build and run your container using GPU acceleration.

---

## 1. Verify NVIDIA GPU and Driver

Run PowerShell:
```powershell
nvidia-smi
```

Confirm:
- **Driver Version** matches or exceeds your project’s CUDA requirement.
- **CUDA Version** ≤ your container base image.

---

## 2. Generate CUDA Environment Report

Run the provided Python script:
```powershell
py -3 generate_cuda_report.py
```
Generates `cuda_env_report.txt` — includes GPU model, VRAM, compute capability, and recommended CUDA base image.

---

## 3. Install NVIDIA Container Toolkit

Enable WSL2:
```powershell
wsl --install
wsl --set-default-version 2
```

Then in Ubuntu (WSL2):
```bash
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

Verify:
```bash
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi
```

---

## 4. Build CUDA-Enabled Containers

Example Dockerfile:
```dockerfile
FROM nvidia/cuda:12.4-devel-ubuntu22.04
WORKDIR /workspace
RUN apt-get update && apt-get install -y python3 python3-pip
COPY . .
RUN nvcc --version
```

Build and run:
```powershell
docker build -t my-cuda-app .
docker run --gpus all my-cuda-app
```

---

## 5. Compute Capability Reference

| GPU Model | Compute Capability | CUDA Version |
|------------|--------------------|---------------|
| RTX 4090   | 8.9                | ≥ 12.0        |
| RTX 3090   | 8.6                | ≥ 11.1        |
| RTX 2080Ti | 7.5                | ≥ 10.1        |

Use:
```bash
nvcc -arch=sm_86 -o my_app my_app.cu
```

---

## 6. Troubleshooting

| Issue | Possible Cause | Solution |
|-------|----------------|-----------|
| `nvidia-smi` not found | Driver missing or PATH not updated | Reinstall NVIDIA driver |
| GPU not accessible in container | Toolkit not installed | Install NVIDIA Container Toolkit |
| CUDA mismatch errors | Base image newer than host CUDA | Use equal or lower CUDA version than host |

---

## 7. Maintenance Tips

- Keep **drivers** and **CUDA runtime** aligned.
- Regenerate `cuda_env_report.txt` after driver updates.
- Store reports in CI/CD artifacts for environment validation.

---
