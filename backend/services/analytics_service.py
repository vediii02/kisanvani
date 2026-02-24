"""
Analytics and Reporting Service
Comprehensive analytics for calls, farmers, and performance
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, distinct
from datetime import datetime, timedelta

from db.models.farmer import Farmer
from db.models.case import Case
from db.models.call_session import CallSession

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Analytics and reporting for the system"""
    
    async def get_dashboard_stats(
        self,
        db: AsyncSession,
        organisation_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive dashboard statistics
        
        Args:
            db: Database session
            organisation_id: Filter by organisation
            date_from: Start date
            date_to: End date
            
        Returns:
            Complete dashboard stats
        """
        try:
            # Default to last 30 days
            if not date_from:
                date_from = datetime.utcnow() - timedelta(days=30)
            if not date_to:
                date_to = datetime.utcnow()
            
            # Build base filters
            call_filters = [
                CallSession.created_at >= date_from,
                CallSession.created_at <= date_to
            ]
            case_filters = [
                Case.created_at >= date_from,
                Case.created_at <= date_to
            ]
            
            if organisation_id:
                call_filters.append(CallSession.organisation_id == organisation_id)
                case_filters.append(Case.organisation_id == organisation_id)
            
            # Total calls
            total_calls = await db.scalar(
                select(func.count(CallSession.id)).where(and_(*call_filters))
            )
            
            # Completed calls
            completed_calls = await db.scalar(
                select(func.count(CallSession.id)).where(
                    and_(
                        *call_filters,
                        CallSession.status == 'completed'
                    )
                )
            )
            
            # Average call duration
            avg_duration = await db.scalar(
                select(func.avg(CallSession.duration_seconds)).where(
                    and_(*call_filters)
                )
            )
            
            # Total farmers
            total_farmers = await db.scalar(
                select(func.count(distinct(Farmer.id))).where(Farmer.is_active == True)
            )
            
            # Active farmers (called in period)
            active_farmers = await db.scalar(
                select(func.count(distinct(CallSession.farmer_id))).where(
                    and_(*call_filters)
                )
            )
            
            # Total cases
            total_cases = await db.scalar(
                select(func.count(Case.id)).where(and_(*case_filters))
            )
            
            # Resolved cases
            resolved_cases = await db.scalar(
                select(func.count(Case.id)).where(
                    and_(
                        *case_filters,
                        Case.status == 'resolved'
                    )
                )
            )
            
            # Problem categories distribution
            problem_dist_stmt = select(
                Case.problem_category,
                func.count(Case.id).label('count')
            ).where(
                and_(*case_filters, Case.problem_category.isnot(None))
            ).group_by(Case.problem_category)
            
            problem_dist_result = await db.execute(problem_dist_stmt)
            problem_distribution = [
                {"category": row[0], "count": row[1]}
                for row in problem_dist_result.all()
            ]
            
            # Daily call trends (last 7 days)
            daily_trends = []
            for i in range(7):
                day = datetime.utcnow() - timedelta(days=6-i)
                day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
                
                day_calls = await db.scalar(
                    select(func.count(CallSession.id)).where(
                        and_(
                            CallSession.created_at >= day_start,
                            CallSession.created_at <= day_end,
                            *([CallSession.organisation_id == organisation_id] if organisation_id else [])
                        )
                    )
                )
                
                daily_trends.append({
                    "date": day.strftime("%Y-%m-%d"),
                    "calls": day_calls
                })
            
            return {
                "success": True,
                "period": {
                    "from": date_from.strftime("%Y-%m-%d"),
                    "to": date_to.strftime("%Y-%m-%d")
                },
                "calls": {
                    "total": total_calls or 0,
                    "completed": completed_calls or 0,
                    "completion_rate": round((completed_calls or 0) / (total_calls or 1) * 100, 1),
                    "avg_duration_seconds": round(avg_duration or 0, 1)
                },
                "farmers": {
                    "total": total_farmers or 0,
                    "active": active_farmers or 0,
                    "engagement_rate": round((active_farmers or 0) / (total_farmers or 1) * 100, 1)
                },
                "cases": {
                    "total": total_cases or 0,
                    "resolved": resolved_cases or 0,
                    "resolution_rate": round((resolved_cases or 0) / (total_cases or 1) * 100, 1),
                    "pending": (total_cases or 0) - (resolved_cases or 0)
                },
                "problem_distribution": problem_distribution,
                "daily_trends": daily_trends
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_call_analytics(
        self,
        db: AsyncSession,
        organisation_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get detailed call analytics
        
        Returns:
            Call performance metrics
        """
        try:
            # Default to last 30 days
            if not date_from:
                date_from = datetime.utcnow() - timedelta(days=30)
            if not date_to:
                date_to = datetime.utcnow()
            
            filters = [
                CallSession.created_at >= date_from,
                CallSession.created_at <= date_to
            ]
            
            if organisation_id:
                filters.append(CallSession.organisation_id == organisation_id)
            
            # Call status distribution
            status_dist_stmt = select(
                CallSession.status,
                func.count(CallSession.id).label('count')
            ).where(and_(*filters)).group_by(CallSession.status)
            
            status_dist_result = await db.execute(status_dist_stmt)
            status_distribution = [
                {"status": row[0], "count": row[1]}
                for row in status_dist_result.all()
            ]
            
            # Call state distribution
            state_dist_stmt = select(
                CallSession.current_state,
                func.count(CallSession.id).label('count')
            ).where(and_(*filters)).group_by(CallSession.current_state)
            
            state_dist_result = await db.execute(state_dist_stmt)
            state_distribution = [
                {"state": row[0], "count": row[1]}
                for row in state_dist_result.all()
            ]
            
            # Hourly distribution
            hourly_dist = []
            for hour in range(24):
                hour_calls = await db.scalar(
                    select(func.count(CallSession.id)).where(
                        and_(
                            *filters,
                            func.extract('hour', CallSession.created_at) == hour
                        )
                    )
                )
                
                if hour_calls and hour_calls > 0:
                    hourly_dist.append({
                        "hour": hour,
                        "calls": hour_calls
                    })
            
            return {
                "success": True,
                "status_distribution": status_distribution,
                "state_distribution": state_distribution,
                "hourly_distribution": hourly_dist
            }
            
        except Exception as e:
            logger.error(f"Error getting call analytics: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_farmer_analytics(
        self,
        db: AsyncSession,
        organisation_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get farmer engagement analytics
        
        Returns:
            Farmer engagement metrics
        """
        try:
            # Location distribution
            location_dist_stmt = select(
                Farmer.district,
                func.count(Farmer.id).label('count')
            ).where(
                and_(
                    Farmer.is_active == True,
                    Farmer.district.isnot(None)
                )
            ).group_by(Farmer.district).order_by(desc('count')).limit(10)
            
            location_dist_result = await db.execute(location_dist_stmt)
            location_distribution = [
                {"district": row[0], "count": row[1]}
                for row in location_dist_result.all()
            ]
            
            # Crop distribution
            crop_dist_stmt = select(
                Farmer.primary_crop,
                func.count(Farmer.id).label('count')
            ).where(
                and_(
                    Farmer.is_active == True,
                    Farmer.primary_crop.isnot(None)
                )
            ).group_by(Farmer.primary_crop).order_by(desc('count')).limit(10)
            
            crop_dist_result = await db.execute(crop_dist_stmt)
            crop_distribution = [
                {"crop": row[0], "count": row[1]}
                for row in crop_dist_result.all()
            ]
            
            # Language distribution
            lang_dist_stmt = select(
                Farmer.preferred_language,
                func.count(Farmer.id).label('count')
            ).where(Farmer.is_active == True).group_by(Farmer.preferred_language)
            
            lang_dist_result = await db.execute(lang_dist_stmt)
            language_distribution = [
                {"language": row[0], "count": row[1]}
                for row in lang_dist_result.all()
            ]
            
            return {
                "success": True,
                "location_distribution": location_distribution,
                "crop_distribution": crop_distribution,
                "language_distribution": language_distribution
            }
            
        except Exception as e:
            logger.error(f"Error getting farmer analytics: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_report(
        self,
        db: AsyncSession,
        report_type: str,
        organisation_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive report
        
        Args:
            report_type: "daily", "weekly", "monthly", "custom"
            organisation_id: Filter by organisation
            date_from: Start date
            date_to: End date
            
        Returns:
            Complete report data
        """
        try:
            # Set date range based on report type
            if report_type == "daily":
                date_from = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                date_to = datetime.utcnow()
            elif report_type == "weekly":
                date_from = datetime.utcnow() - timedelta(days=7)
                date_to = datetime.utcnow()
            elif report_type == "monthly":
                date_from = datetime.utcnow() - timedelta(days=30)
                date_to = datetime.utcnow()
            
            # Get all analytics
            dashboard = await self.get_dashboard_stats(db, organisation_id, date_from, date_to)
            call_analytics = await self.get_call_analytics(db, organisation_id, date_from, date_to)
            farmer_analytics = await self.get_farmer_analytics(db, organisation_id)
            
            return {
                "success": True,
                "report_type": report_type,
                "generated_at": datetime.utcnow().isoformat(),
                "organisation_id": organisation_id,
                "dashboard": dashboard,
                "call_analytics": call_analytics,
                "farmer_analytics": farmer_analytics
            }
            
        except Exception as e:
            logger.error(f"Error generating report: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }


# Global instance
analytics_service = AnalyticsService()
