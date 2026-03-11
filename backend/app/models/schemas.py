from enum import Enum

from pydantic import BaseModel


class RoomType(str, Enum):
    OFFICE = "office"
    CORRIDOR = "corridor"
    STAIRWELL = "stairwell"
    ELEVATOR = "elevator"
    BATHROOM = "bathroom"
    KITCHEN = "kitchen"
    STORAGE = "storage"
    TECHNICAL = "technical"
    SERVER_ROOM = "server_room"
    GARAGE = "garage"
    LOBBY = "lobby"
    CONFERENCE = "conference"
    RESIDENTIAL = "residential"
    BEDROOM = "bedroom"
    LIVING_ROOM = "living_room"
    BALCONY = "balcony"
    UNKNOWN = "unknown"


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    CONVERTING = "converting"
    PARSING = "parsing"
    DETECTING_ROOMS = "detecting_rooms"
    CLASSIFYING = "classifying"
    GENERATING = "generating"
    EXPORTING = "exporting"
    COMPLETED = "completed"
    FAILED = "failed"


class Point(BaseModel):
    x: float
    y: float


class RoomPolygon(BaseModel):
    id: int
    points: list[Point]
    room_type: RoomType = RoomType.UNKNOWN
    label: str = ""
    area: float = 0.0


class WallSegment(BaseModel):
    start: Point
    end: Point
    thickness: float = 0.2


class DoorInfo(BaseModel):
    position: Point
    width: float
    angle: float = 0.0
    fire_rating: str = ""


class StairInfo(BaseModel):
    polygon: list[Point]
    direction: str = "up"


class FloorPlanData(BaseModel):
    """Internal representation of a parsed floor plan."""

    filename: str
    floor_label: str = ""
    walls: list[WallSegment] = []
    doors: list[DoorInfo] = []
    stairs: list[StairInfo] = []
    rooms: list[RoomPolygon] = []
    bounds: tuple[float, float, float, float] = (0, 0, 0, 0)  # minx, miny, maxx, maxy
    scale: float = 1.0
    unit: str = "mm"
    fire_walls: list[WallSegment] = []
    fire_doors: list[DoorInfo] = []
    windows: list[WallSegment] = []
    has_sprinkler: bool = False


class UploadResponse(BaseModel):
    job_id: str
    filename: str
    status: ProcessingStatus


class JobStatus(BaseModel):
    job_id: str
    status: ProcessingStatus
    progress: float = 0.0
    message: str = ""
    result_svg: str | None = None
    result_pdf: str | None = None


class ProcessingResult(BaseModel):
    job_id: str
    floor_plan: FloorPlanData
    svg_path: str
    pdf_path: str | None = None
