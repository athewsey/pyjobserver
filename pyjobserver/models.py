# Built-Ins:
from datetime import datetime
from typing import Any, ClassVar, List, Type, Union

# External Dependencies:
from dataclasses import field
from marshmallow import Schema
from marshmallow_dataclass import dataclass

@dataclass
class BaseApiModel:
    Schema: ClassVar[Type[Schema]] = Schema

@dataclass
class BaseJobSpec(BaseApiModel):
    """Base job input/specification class from which to derive input classes

    :ivar job_type: (str) Tells the runner what handler to use (what type of job this is)
    """
    job_type: str = field(metadata={ "load_from": "jobType", "required": True })

@dataclass
class JobProgress(BaseApiModel):
    """A progress update object for a Job"""
    pct: float = field(metadata={ "required": True })
    message: str = field(default=None)
    # TODO: What data type should our elapsed and remaining times be?
    timestamp: datetime = field(default_factory=datetime.now)
    time_elapsed: Any = field(default=None, metadata={ "load_from": "timeElapsed", "dump_to": "timeElapsed" })
    time_remaining: Any = field(default=None, metadata={ "load_from": "timeRemaining", "dump_to": "timeRemaining" })

@dataclass
class BaseJobStatus(BaseJobSpec):
    job_id: str = field(metadata={ "load_from": "id", "dump_to": "id" })
    errors: Union[None, List[Any]] = field(default=None, metadata={ "required": False })
    warnings: Union[None, List[Any]] = field(default=None, metadata={ "required": False })

@dataclass
class JobCreatedResult(BaseApiModel):
    """Response for successful job creation"""
    # TODO: Why not just return the initial BaseJobStatus?
    job_id: str = field(metadata={ "load_from": "id", "dump_to": "id" })
