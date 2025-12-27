"""Database storage backend using SQLAlchemy."""
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Boolean, Text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.future import select
from datetime import date

from models.ship import Ship
from storage.base_storage import BaseStorage
from logger import setup_logger

logger = setup_logger(__name__)

Base = declarative_base()


class ShipModel(Base):
    """SQLAlchemy model for ships table."""
    __tablename__ = "ships"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(500), nullable=False)
    link = Column(String(500), nullable=False, unique=True)
    tier = Column(Integer)
    faction = Column(String(100))
    type = Column(String(200))
    released = Column(Date)
    device_slots = Column(Integer)
    
    # Weapons
    fore_weapons = Column(Integer)
    aft_weapons = Column(Integer)
    can_equip_dual_cannons = Column(Boolean, default=False)
    
    # Stats
    max_hull = Column(Integer)
    hull_modifier = Column(Float)
    shield_modifier = Column(Float)
    impulse_modifier = Column(Float)
    turn_rate = Column(Float)
    inertia_rating = Column(Integer)
    
    # Additional fields
    bridge_officers = Column(Text)
    console_slots = Column(Text)
    

class DatabaseStorage(BaseStorage):
    """Database storage implementation."""
    
    def __init__(self, database_url: str):
        """Initialize database storage.
        
        Args:
            database_url: SQLAlchemy database URL
        """
        # Convert sync URL to async if needed
        if database_url.startswith("sqlite:"):
            database_url = database_url.replace("sqlite:", "sqlite+aiosqlite:")
        elif database_url.startswith("postgresql:"):
            database_url = database_url.replace("postgresql:", "postgresql+asyncpg:")
        elif database_url.startswith("mysql:"):
            database_url = database_url.replace("mysql:", "mysql+aiomysql:")
        
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async def init_db(self):
        """Initialize database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized")
    
    async def save_ships(self, ships: List[Ship]) -> bool:
        """Save ships to database.
        
        Args:
            ships: List of Ship instances
            
        Returns:
            True if successful
        """
        try:
            async with self.async_session() as session:
                for ship in ships:
                    # Check if ship already exists
                    stmt = select(ShipModel).where(ShipModel.link == str(ship.link))
                    result = await session.execute(stmt)
                    existing = result.scalar_one_or_none()
                    
                    if existing:
                        # Update existing ship
                        self._update_ship_model(existing, ship)
                    else:
                        # Create new ship
                        ship_model = self._ship_to_model(ship)
                        session.add(ship_model)
                
                await session.commit()
            
            logger.info(f"Saved {len(ships)} ships to database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save ships to database: {e}")
            return False
    
    async def get_ships(self, faction: Optional[str] = None) -> List[Ship]:
        """Retrieve ships from database.
        
        Args:
            faction: Optional faction filter
            
        Returns:
            List of Ship instances
        """
        try:
            async with self.async_session() as session:
                stmt = select(ShipModel)
                
                if faction:
                    stmt = stmt.where(ShipModel.faction == faction)
                
                result = await session.execute(stmt)
                ship_models = result.scalars().all()
            
            ships = [self._model_to_ship(model) for model in ship_models]
            logger.info(f"Loaded {len(ships)} ships from database")
            return ships
            
        except Exception as e:
            logger.error(f"Failed to load ships from database: {e}")
            return []
    
    async def delete_all_ships(self) -> bool:
        """Delete all ships from database.
        
        Returns:
            True if successful
        """
        try:
            async with self.async_session() as session:
                await session.execute(ShipModel.__table__.delete())
                await session.commit()
            
            logger.info("Deleted all ships from database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete ships from database: {e}")
            return False
    
    async def get_ship_count(self) -> int:
        """Get total ship count from database.
        
        Returns:
            Total ship count
        """
        try:
            async with self.async_session() as session:
                stmt = select(ShipModel)
                result = await session.execute(stmt)
                return len(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to get ship count: {e}")
            return 0
    
    def _ship_to_model(self, ship: Ship) -> ShipModel:
        """Convert Ship pydantic model to SQLAlchemy model."""
        return ShipModel(
            name=ship.name,
            link=str(ship.link),
            tier=ship.tier,
            faction=ship.faction,
            type=ship.type,
            released=ship.released,
            device_slots=ship.device_slots,
            fore_weapons=ship.weapons.fore if ship.weapons else None,
            aft_weapons=ship.weapons.aft if ship.weapons else None,
            can_equip_dual_cannons=ship.weapons.can_equip_dual_cannons if ship.weapons else False,
            max_hull=ship.stats.max_hull if ship.stats else None,
            hull_modifier=ship.stats.hull_modifier if ship.stats else None,
            shield_modifier=ship.stats.shield_modifier if ship.stats else None,
            impulse_modifier=ship.stats.impulse_modifier if ship.stats else None,
            turn_rate=ship.stats.turn_rate if ship.stats else None,
            inertia_rating=ship.stats.inertia_rating if ship.stats else None,
            bridge_officers=ship.bridge_officers,
            console_slots=ship.console_slots,
        )
    
    def _update_ship_model(self, model: ShipModel, ship: Ship):
        """Update SQLAlchemy model with Ship data."""
        model.name = ship.name
        model.tier = ship.tier
        model.faction = ship.faction
        model.type = ship.type
        model.released = ship.released
        model.device_slots = ship.device_slots
        
        if ship.weapons:
            model.fore_weapons = ship.weapons.fore
            model.aft_weapons = ship.weapons.aft
            model.can_equip_dual_cannons = ship.weapons.can_equip_dual_cannons
        
        if ship.stats:
            model.max_hull = ship.stats.max_hull
            model.hull_modifier = ship.stats.hull_modifier
            model.shield_modifier = ship.stats.shield_modifier
            model.impulse_modifier = ship.stats.impulse_modifier
            model.turn_rate = ship.stats.turn_rate
            model.inertia_rating = ship.stats.inertia_rating
        
        model.bridge_officers = ship.bridge_officers
        model.console_slots = ship.console_slots
    
    def _model_to_ship(self, model: ShipModel) -> Ship:
        """Convert SQLAlchemy model to Ship pydantic model."""
        from models.ship import ShipWeapons, ShipStats
        
        weapons = None
        if model.fore_weapons is not None or model.aft_weapons is not None:
            weapons = ShipWeapons(
                fore=model.fore_weapons or 0,
                aft=model.aft_weapons or 0,
                can_equip_dual_cannons=model.can_equip_dual_cannons
            )
        
        stats = ShipStats(
            max_hull=model.max_hull,
            hull_modifier=model.hull_modifier,
            shield_modifier=model.shield_modifier,
            impulse_modifier=model.impulse_modifier,
            turn_rate=model.turn_rate,
            inertia_rating=model.inertia_rating
        )
        
        return Ship(
            name=model.name,
            link=model.link,
            tier=model.tier,
            faction=model.faction,
            type=model.type,
            released=model.released,
            device_slots=model.device_slots,
            weapons=weapons,
            stats=stats,
            bridge_officers=model.bridge_officers,
            console_slots=model.console_slots
        )