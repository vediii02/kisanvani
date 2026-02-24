"""
Farmer Profile Management Service
Complete farmer information and history tracking
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from datetime import datetime, timedelta

from db.models.farmer import Farmer
from db.models.case import Case
from schemas.farmer import FarmerCreate, FarmerUpdate

logger = logging.getLogger(__name__)


class FarmerProfileService:
    """Comprehensive farmer profile management"""
    
    async def get_or_create_farmer(
        self,
        phone_number: str,
        db: AsyncSession,
        auto_create: bool = True
    ) -> Optional[Farmer]:
        """
        Get existing farmer or create new profile
        
        Args:
            phone_number: Farmer's phone number
            db: Database session
            auto_create: Create profile if doesn't exist
            
        Returns:
            Farmer object or None
        """
        try:
            # Try to find existing farmer
            stmt = select(Farmer).where(Farmer.phone_number == phone_number)
            result = await db.execute(stmt)
            farmer = result.scalar_one_or_none()
            
            if farmer:
                return farmer
            
            if not auto_create:
                return None
            
            # Create new farmer profile
            new_farmer = Farmer(
                phone_number=phone_number,
                preferred_language=FarmerLanguage.HINDI,
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            db.add(new_farmer)
            await db.commit()
            await db.refresh(new_farmer)
            
            logger.info(f"Created new farmer profile: {phone_number}")
            return new_farmer
            
        except Exception as e:
            logger.error(f"Error getting/creating farmer: {e}", exc_info=True)
            await db.rollback()
            return None
    
    async def update_farmer_profile(
        self,
        farmer_id: int,
        update_data: Dict[str, Any],
        db: AsyncSession
    ) -> Optional[Farmer]:
        """
        Update farmer profile information
        
        Args:
            farmer_id: Farmer ID
            update_data: Fields to update
            db: Database session
            
        Returns:
            Updated Farmer object
        """
        try:
            farmer = await db.get(Farmer, farmer_id)
            if not farmer:
                return None
            
            # Update allowed fields
            allowed_fields = [
                'name', 'email', 'location', 'district', 'state',
                'preferred_language', 'primary_crop', 'land_area_acres',
                'soil_type', 'irrigation_type', 'farming_experience_years'
            ]
            
            for field in allowed_fields:
                if field in update_data:
                    setattr(farmer, field, update_data[field])
            
            farmer.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(farmer)
            
            logger.info(f"Updated farmer profile: {farmer_id}")
            return farmer
            
        except Exception as e:
            logger.error(f"Error updating farmer profile: {e}", exc_info=True)
            await db.rollback()
            return None
    
    async def get_farmer_history(
        self,
        farmer_id: int,
        db: AsyncSession,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get farmer's interaction history
        
        Args:
            farmer_id: Farmer ID
            db: Database session
            limit: Max number of records
            
        Returns:
            Complete history with statistics
        """
        try:
            # Get farmer
            farmer = await db.get(Farmer, farmer_id)
            if not farmer:
                return {"error": "Farmer not found"}
            
            # Get cases
            cases_stmt = select(Case).where(
                Case.farmer_id == farmer_id
            ).order_by(desc(Case.created_at)).limit(limit)
            
            cases_result = await db.execute(cases_stmt)
            cases = cases_result.scalars().all()
            
            # Calculate statistics
            total_cases = await db.scalar(
                select(func.count(Case.id)).where(Case.farmer_id == farmer_id)
            )
            
            resolved_cases = await db.scalar(
                select(func.count(Case.id)).where(
                    and_(
                        Case.farmer_id == farmer_id,
                        Case.status == "resolved"
                    )
                )
            )
            
            # Get common crops
            common_crops_stmt = select(
                Case.crop,
                func.count(Case.id).label('count')
            ).where(
                and_(
                    Case.farmer_id == farmer_id,
                    Case.crop.isnot(None)
                )
            ).group_by(Case.crop).order_by(desc('count')).limit(5)
            
            common_crops_result = await db.execute(common_crops_stmt)
            common_crops = [
                {"crop": row[0], "count": row[1]}
                for row in common_crops_result.all()
            ]
            
            # Get common problems
            common_problems_stmt = select(
                Case.problem_category,
                func.count(Case.id).label('count')
            ).where(
                and_(
                    Case.farmer_id == farmer_id,
                    Case.problem_category.isnot(None)
                )
            ).group_by(Case.problem_category).order_by(desc('count')).limit(5)
            
            common_problems_result = await db.execute(common_problems_stmt)
            common_problems = [
                {"category": row[0], "count": row[1]}
                for row in common_problems_result.all()
            ]
            
            return {
                "farmer": {
                    "id": farmer.id,
                    "name": farmer.name,
                    "phone_number": farmer.phone_number,
                    "location": farmer.location,
                    "primary_crop": farmer.primary_crop,
                    "land_area_acres": farmer.land_area_acres,
                    "farming_experience_years": farmer.farming_experience_years
                },
                "statistics": {
                    "total_cases": total_cases,
                    "resolved_cases": resolved_cases,
                    "resolution_rate": round(resolved_cases / total_cases * 100, 1) if total_cases > 0 else 0,
                    "member_since": farmer.created_at.strftime("%Y-%m-%d"),
                    "last_contact": farmer.updated_at.strftime("%Y-%m-%d") if farmer.updated_at else None
                },
                "common_crops": common_crops,
                "common_problems": common_problems,
                "recent_cases": [
                    {
                        "id": case.id,
                        "crop": case.crop,
                        "problem_category": case.problem_category,
                        "status": case.status,
                        "created_at": case.created_at.strftime("%Y-%m-%d %H:%M"),
                        "summary": case.summary
                    }
                    for case in cases
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting farmer history: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def get_farmer_recommendations(
        self,
        farmer_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Get personalized recommendations for farmer
        
        Args:
            farmer_id: Farmer ID
            db: Database session
            
        Returns:
            Recommendations based on profile and history
        """
        try:
            history = await self.get_farmer_history(farmer_id, db)
            
            if "error" in history:
                return history
            
            farmer = history["farmer"]
            common_problems = history["common_problems"]
            
            recommendations = {
                "preventive_measures": [],
                "seasonal_advice": [],
                "product_suggestions": [],
                "training_topics": []
            }
            
            # Preventive measures based on common problems
            if any(p["category"] == "pest" for p in common_problems):
                recommendations["preventive_measures"].append({
                    "title": "नियमित कीट निगरानी",
                    "description": "हर हफ्ते फसल की जांच करें। शुरुआती लक्षण दिखने पर तुरंत उपाय करें।"
                })
            
            if any(p["category"] == "disease" for p in common_problems):
                recommendations["preventive_measures"].append({
                    "title": "बीज उपचार",
                    "description": "बुवाई से पहले बीज उपचार जरूर करें। फंगल रोगों से बचाव होगा।"
                })
            
            # Seasonal advice
            current_month = datetime.now().month
            if current_month in [6, 7, 8]:  # Monsoon
                recommendations["seasonal_advice"].append({
                    "season": "मॉनसून",
                    "advice": "बारिश के मौसम में फंगल रोगों का खतरा बढ़ जाता है। जल निकासी का ध्यान रखें।"
                })
            
            # Product suggestions based on crops
            if farmer.get("primary_crop"):
                recommendations["product_suggestions"].append({
                    "category": "बीज",
                    "suggestion": f"{farmer['primary_crop']} के लिए उच्च गुणवत्ता वाले हाइब्रिड बीज"
                })
            
            # Training topics
            if farmer.get("farming_experience_years", 0) < 5:
                recommendations["training_topics"].extend([
                    "आधुनिक खेती तकनीक",
                    "एकीकृत कीट प्रबंधन",
                    "जैविक खेती"
                ])
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def search_farmers(
        self,
        db: AsyncSession,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Search farmers with filters
        
        Args:
            db: Database session
            filters: Search filters (location, crop, etc.)
            page: Page number
            page_size: Items per page
            
        Returns:
            Paginated farmer list
        """
        try:
            stmt = select(Farmer).where(Farmer.is_active == True)
            
            if filters:
                if filters.get("location"):
                    stmt = stmt.where(Farmer.location.ilike(f"%{filters['location']}%"))
                
                if filters.get("district"):
                    stmt = stmt.where(Farmer.district == filters["district"])
                
                if filters.get("primary_crop"):
                    stmt = stmt.where(Farmer.primary_crop == filters["primary_crop"])
                
                if filters.get("language"):
                    stmt = stmt.where(Farmer.preferred_language == filters["language"])
            
            # Get total count
            total_stmt = select(func.count()).select_from(stmt.subquery())
            total = await db.scalar(total_stmt)
            
            # Apply pagination
            stmt = stmt.order_by(desc(Farmer.created_at))
            stmt = stmt.offset((page - 1) * page_size).limit(page_size)
            
            result = await db.execute(stmt)
            farmers = result.scalars().all()
            
            return {
                "success": True,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
                "farmers": [
                    {
                        "id": f.id,
                        "name": f.name,
                        "phone_number": f.phone_number,
                        "location": f.location,
                        "district": f.district,
                        "state": f.state,
                        "primary_crop": f.primary_crop,
                        "created_at": f.created_at.strftime("%Y-%m-%d")
                    }
                    for f in farmers
                ]
            }
            
        except Exception as e:
            logger.error(f"Error searching farmers: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }


# Global instance
farmer_profile_service = FarmerProfileService()
