"""Device manager for MPS/CPU/CUDA fallback"""
import torch
import logging
logger = logging.getLogger(__name__)

class DeviceManager:
    def __init__(self):
        self._mps_available = torch.backends.mps.is_available() if hasattr(torch.backends, 'mps') else False
        self._cuda_available = torch.cuda.is_available()
        self._mps_tested = False
        self._mps_working = False
    
    def get_device(self, prefer_mps=True, stage_name=None):
        if self._cuda_available:
            return 'cuda'
        if prefer_mps and self._mps_available:
            if not self._mps_tested:
                try:
                    torch.zeros(1, device='mps')
                    self._mps_working = True
                except:
                    self._mps_working = False
                self._mps_tested = True
            if self._mps_working:
                return 'mps'
        return 'cpu'

device_manager = DeviceManager()
def get_device(prefer_mps=True, stage_name=None):
    return device_manager.get_device(prefer_mps, stage_name)
