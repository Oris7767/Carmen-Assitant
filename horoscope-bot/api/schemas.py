from pydantic import BaseModel
from typing import Optional, Any


class NakshatraInfo(BaseModel):
    name: Optional[str] = None
    lord: Optional[str] = None
    pada: Optional[int] = None
    startDegree: Optional[float] = None
    endDegree: Optional[float] = None


class SignInfo(BaseModel):
    name: Optional[str] = None
    longitude: Optional[float] = None
    degree: Optional[int] = None
    minutes: Optional[int] = None


class HouseRef(BaseModel):
    number: Optional[int] = None
    sign: Optional[str] = None


class AspectInfo(BaseModel):
    planet: Optional[str] = None
    aspect: Optional[str] = None
    orb: Optional[float] = None


class PlanetData(BaseModel):
    planet: Optional[str] = None
    sign: Optional[SignInfo] = None
    house: Optional[HouseRef] = None
    isRetrograde: Optional[bool] = False
    nakshatra: Optional[NakshatraInfo] = None
    aspects: Optional[list[AspectInfo]] = None
    aspectingPlanets: Optional[list[str]] = None


class HouseData(BaseModel):
    number: Optional[int] = None
    sign: Optional[str] = None
    degree: Optional[int] = None
    planets: Optional[list[str]] = None


class DashaPeriod(BaseModel):
    planet: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    duration: Optional[float] = None


class Dashas(BaseModel):
    current: Optional[DashaPeriod] = None
    sequence: Optional[list[DashaPeriod]] = None


class AscendantInfo(BaseModel):
    longitude: Optional[float] = None
    sign: Optional[SignInfo] = None
    nakshatra: Optional[NakshatraInfo] = None


class Metadata(BaseModel):
    date: Optional[str] = None
    time: Optional[str] = None
    timezone: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ChartRequest(BaseModel):
    """The full chart data JSON from web API."""
    ascendant: Optional[AscendantInfo] = None
    dashas: Optional[Dashas] = None
    houses: Optional[list[HouseData]] = None
    metadata: Optional[Metadata] = None
    planets: Optional[list[PlanetData]] = None
    # Allow extra fields
    model_config = {"extra": "allow"}


class ReadingResponse(BaseModel):
    free: str
    full: str
    model: str
    char_count_free: int
    char_count_full: int
    rag_chunks_used: int


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    chunks_count: int = 0
    index_loaded: bool = False
