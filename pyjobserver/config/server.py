"""Server configuration
"""

# Local Imports:
from .base import BaseConfig
from .security import SecurityConfig

class ServerConfig(BaseConfig):
    """Server configuration container
    """
    def __init__(self, raw):
        self.jobs_max = int(raw["env"].get("JOBS_MAX", 3))
        self.jobs_cache_max = int(raw["env"].get("JOBS_CACHE_MAX", 20))
        self.jobs_cache_ttl = int(raw["env"].get("JOBS_CACHE_TTL", 3600))
        self.job_runner_threads = int(raw["env"].get("JOB_RUNNER_THREADS", 20))
        self.job_timeout = int(raw["env"].get("JOB_RUNNER_TIMEOUT", 20 * 60))
        self.port = int(raw["env"].get("PORT") or raw["env"].get("VCAP_PORT") or 4000)
        
        self.security = SecurityConfig(raw)
