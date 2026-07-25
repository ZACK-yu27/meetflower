"""花园路由：1.2 种植/复种 / 1.3 聚合视图 / 1.4 照料 / 1.5 压花收藏。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import CareOut, GardenOut, PlantCreateRequest, PlantOut, PressOut
from ..services import garden as garden_service
from ..services import house as house_service

router = APIRouter(tags=["gardens"])


@router.post("/gardens/{garden_id}/plants", response_model=PlantOut)
def create_plant(garden_id: int, body: PlantCreateRequest, db: Session = Depends(get_db)):
    return garden_service.create_plant(
        db,
        garden_id,
        recognition_id=body.recognition_id,
        species=body.species,
        main_color=body.main_color,
    )


@router.get("/gardens/{garden_id}", response_model=GardenOut)
def get_garden(garden_id: int, db: Session = Depends(get_db)):
    return garden_service.get_garden_view(db, garden_id)


@router.post("/gardens/{garden_id}/plants/{plant_id}/care", response_model=CareOut)
def care(garden_id: int, plant_id: int, db: Session = Depends(get_db)):
    return garden_service.care(db, garden_id, plant_id)


@router.post("/gardens/{garden_id}/plants/{plant_id}/press", response_model=PressOut)
def press(garden_id: int, plant_id: int, db: Session = Depends(get_db)):
    return house_service.press_flower(db, garden_id, plant_id)
