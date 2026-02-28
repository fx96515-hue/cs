"""
Cooperative Sourcing Analyzer Service.

Comprehensive scoring and analysis system for evaluating Peru coffee cooperatives
for sourcing decisions. Implements multi-dimensional scoring across supply capacity,
export readiness, communication quality, pricing, and risk assessment.
"""

from typing import Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.cooperative import Cooperative
from app.services.data_sources.peru_data_sources import fetch_ico_price_data


# Constants for default values
MAX_RESPONSE_TIME_HOURS = 999  # Default for missing response time data (>40 days)


class CooperativeSourcingAnalyzer:
    """Analyzer for cooperative sourcing evaluation with comprehensive scoring."""

    def __init__(self, db: Session):
        self.db = db

    def analyze_for_sourcing(
        self, cooperative_id: int, force_refresh: bool = False
    ) -> dict[str, Any]:
        """
        Perform comprehensive sourcing analysis for a cooperative.

        Args:
            cooperative_id: ID of the cooperative to analyze
            force_refresh: If True, bypass cache and recalculate

        Returns:
            Complete analysis with scores, benchmarks, and recommendation
        """
        coop = self.db.get(Cooperative, cooperative_id)
        if not coop:
            raise ValueError(f"Cooperative {cooperative_id} not found")

        # Check cache if not forcing refresh
        if not force_refresh and coop.sourcing_scores:
            cached_at = coop.sourcing_scores.get("analyzed_at")
            if cached_at:
                return coop.sourcing_scores

        # Perform fresh analysis
        supply_capacity = self.check_supply_capacity(coop)
        export_readiness = self.check_export_readiness(coop)
        communication = self.assess_communication_quality(coop)
        pricing = self.benchmark_pricing(coop)
        risk = self.calculate_sourcing_risk(coop)

        # Calculate total score (weighted)
        quality_score = (
            coop.quality_score or 50
        )  # Use existing quality score or default

        total_score = (
            supply_capacity["score"] * 0.30
            + quality_score * 0.25
            + export_readiness["score"] * 0.20
            + pricing["competitiveness_score"] * 0.15
            + communication["score"] * 0.10
        )
        total_score_rounded = round(total_score, 2)

        # Generate recommendation
        recommendation = self.generate_recommendation(
            total_score, risk["total_risk_score"]
        )

        # Prepare result
        result = {
            "cooperative_id": cooperative_id,
            "cooperative_name": coop.name,
            "region": coop.region,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "supply_capacity": supply_capacity,
            "export_readiness": export_readiness,
            "communication_quality": communication,
            "price_benchmark": pricing,
            "risk_assessment": risk,
            "total_score": total_score_rounded,
            "scores": {
                "supply_capacity": supply_capacity["score"],
                "quality": quality_score,
                "export_readiness": export_readiness["score"],
                "price_competitiveness": pricing["competitiveness_score"],
                "communication": communication["score"],
                "total": total_score_rounded,
            },
            "recommendation": recommendation,
        }

        # Cache result
        coop.sourcing_scores = result
        self.db.commit()

        return result

    def check_supply_capacity(self, coop: Cooperative) -> dict[str, Any]:
        """
        Evaluate supply capacity (100-point scale).

        Components:
        - Volume: 30 points
        - Farmer count: 20 points
        - Storage capacity: 20 points
        - Processing facilities: 15 points
        - Export experience: 15 points

        Args:
            coop: Cooperative model instance

        Returns:
            Dictionary with score breakdown
        """
        score = 0.0
        breakdown = {}

        op_data = coop.operational_data or {}

        # Volume score (30 points)
        volume_kg = op_data.get("annual_volume_kg", 0)
        if volume_kg >= 100000:
            volume_score = 30
        elif volume_kg >= 50000:
            volume_score = 25
        elif volume_kg >= 25000:
            volume_score = 20
        elif volume_kg >= 10000:
            volume_score = 15
        else:
            volume_score = 5
        score += volume_score
        breakdown["volume"] = {"score": volume_score, "volume_kg": volume_kg}

        # Farmer count (20 points)
        farmer_count = op_data.get("farmer_count", 0)
        if farmer_count >= 500:
            farmer_score = 20
        elif farmer_count >= 200:
            farmer_score = 17
        elif farmer_count >= 100:
            farmer_score = 14
        elif farmer_count >= 50:
            farmer_score = 10
        else:
            farmer_score = 5
        score += farmer_score
        breakdown["farmers"] = {"score": farmer_score, "count": farmer_count}

        # Storage capacity (20 points)
        storage_kg = op_data.get("storage_capacity_kg", 0)
        if storage_kg >= 200000:
            storage_score = 20
        elif storage_kg >= 100000:
            storage_score = 17
        elif storage_kg >= 50000:
            storage_score = 14
        elif storage_kg >= 25000:
            storage_score = 10
        else:
            storage_score = 5
        score += storage_score
        breakdown["storage"] = {"score": storage_score, "capacity_kg": storage_kg}

        # Processing facilities (15 points)
        facilities = op_data.get("processing_facilities", [])
        facility_score = 0
        if "wet_mill" in facilities:
            facility_score += 8
        if "dry_mill" in facilities:
            facility_score += 7
        score += facility_score
        breakdown["facilities"] = {"score": facility_score, "types": facilities}

        # Export experience (15 points)
        years_exporting = op_data.get("years_exporting", 0)
        if years_exporting >= 10:
            experience_score = 15
        elif years_exporting >= 5:
            experience_score = 12
        elif years_exporting >= 3:
            experience_score = 9
        elif years_exporting >= 1:
            experience_score = 6
        else:
            experience_score = 2
        score += experience_score
        breakdown["experience"] = {"score": experience_score, "years": years_exporting}

        return {
            "score": round(score, 2),
            "max_score": 100,
            "breakdown": breakdown,
            "assessment": "strong"
            if score >= 75
            else "adequate"
            if score >= 50
            else "limited",
        }

    def check_export_readiness(self, coop: Cooperative) -> dict[str, Any]:
        """
        Evaluate export readiness (100-point scale).

        Components:
        - Export license: 25 points
        - SENASA registration: 25 points
        - Certifications: 25 points
        - Customs history: 15 points
        - Document coordinator: 10 points

        Args:
            coop: Cooperative model instance

        Returns:
            Dictionary with score breakdown
        """
        score = 0.0
        breakdown = {}

        export_data = coop.export_readiness or {}

        # Export license (25 points)
        has_license = export_data.get("has_export_license", False)
        license_expiry = export_data.get("license_expiry_date")
        if has_license and license_expiry:
            license_score = 25
        elif has_license:
            license_score = 20
        else:
            license_score = 0
        score += license_score
        breakdown["license"] = {
            "score": license_score,
            "valid": has_license,
            "expiry": license_expiry,
        }

        # SENASA registration (25 points)
        senasa_registered = export_data.get("senasa_registered", False)
        senasa_score = 25 if senasa_registered else 0
        score += senasa_score
        breakdown["senasa"] = {"score": senasa_score, "registered": senasa_registered}

        # Certifications (25 points)
        cert_list = export_data.get("certifications", [])
        cert_count = len(cert_list)
        if cert_count >= 3:
            cert_score = 25
        elif cert_count == 2:
            cert_score = 20
        elif cert_count == 1:
            cert_score = 15
        else:
            cert_score = 5
        score += cert_score
        breakdown["certifications"] = {
            "score": cert_score,
            "count": cert_count,
            "list": cert_list,
        }

        # Customs history (15 points)
        customs_issues = export_data.get("customs_issues_count", 0)
        if customs_issues == 0:
            customs_score = 15
        elif customs_issues <= 2:
            customs_score = 10
        elif customs_issues <= 5:
            customs_score = 5
        else:
            customs_score = 0
        score += customs_score
        breakdown["customs"] = {"score": customs_score, "issues": customs_issues}

        # Document coordinator (10 points)
        has_coordinator = export_data.get("has_document_coordinator", False)
        coordinator_score = 10 if has_coordinator else 0
        score += coordinator_score
        breakdown["coordinator"] = {"score": coordinator_score, "has": has_coordinator}

        return {
            "score": round(score, 2),
            "max_score": 100,
            "breakdown": breakdown,
            "assessment": "ready"
            if score >= 75
            else "partially_ready"
            if score >= 50
            else "not_ready",
        }

    def assess_communication_quality(self, coop: Cooperative) -> dict[str, Any]:
        """
        Assess communication quality (100-point scale).

        Components:
        - Response time: 25 points
        - Languages: 25 points
        - Digital presence: 20 points
        - Documentation quality: 15 points
        - Meeting reliability: 15 points

        Args:
            coop: Cooperative model instance

        Returns:
            Dictionary with score breakdown
        """
        score = 0.0
        breakdown = {}

        comm_data = coop.communication_metrics or {}
        digital_data = coop.digital_footprint or {}

        # Response time (25 points)
        avg_response_hours = comm_data.get(
            "avg_response_hours", MAX_RESPONSE_TIME_HOURS
        )
        if avg_response_hours <= 24:
            response_score = 25
        elif avg_response_hours <= 48:
            response_score = 20
        elif avg_response_hours <= 72:
            response_score = 10
        else:
            response_score = 5
        score += response_score
        breakdown["response_time"] = {
            "score": response_score,
            "avg_hours": avg_response_hours,
        }

        # Languages (25 points)
        languages = comm_data.get("languages", [])
        lang_score = 5  # Base for Spanish
        if "english" in [lang.lower() for lang in languages]:
            lang_score += 15
        if "german" in [lang.lower() for lang in languages]:
            lang_score += 10
        score += lang_score
        breakdown["languages"] = {"score": lang_score, "list": languages}

        # Digital presence (20 points)
        digital_score = 0
        if digital_data.get("has_website"):
            digital_score += 8
        if digital_data.get("has_facebook"):
            digital_score += 4
        if digital_data.get("has_instagram"):
            digital_score += 4
        if digital_data.get("has_whatsapp"):
            digital_score += 4
        score += digital_score
        breakdown["digital_presence"] = {
            "score": digital_score,
            "channels": digital_data,
        }

        # Documentation quality (15 points)
        doc_score = 0
        if digital_data.get("has_photos"):
            doc_score += 8
        if digital_data.get("has_cupping_scores"):
            doc_score += 7
        score += doc_score
        breakdown["documentation"] = {"score": doc_score}

        # Meeting reliability (15 points)
        missed_meetings = comm_data.get("missed_meetings", 0)
        if missed_meetings == 0:
            meeting_score = 15
        elif missed_meetings <= 1:
            meeting_score = 12
        elif missed_meetings <= 3:
            meeting_score = 8
        else:
            meeting_score = 3
        score += meeting_score
        breakdown["meetings"] = {"score": meeting_score, "missed": missed_meetings}

        return {
            "score": round(score, 2),
            "max_score": 100,
            "breakdown": breakdown,
            "assessment": "excellent"
            if score >= 80
            else "good"
            if score >= 60
            else "needs_improvement",
        }

    def benchmark_pricing(self, coop: Cooperative) -> dict[str, Any]:
        """
        Benchmark cooperative pricing against regional and ICO data.

        Args:
            coop: Cooperative model instance

        Returns:
            Dictionary with price comparison and competitiveness score
        """
        fin_data = coop.financial_data or {}
        coop_fob_price = fin_data.get("fob_price_per_kg")

        if not coop_fob_price:
            return {
                "competitiveness_score": 50,
                "note": "No pricing data available",
                "coop_price": None,
                "benchmark_price": None,
                "assessment": "market_rate",
            }

        # Try to get regional benchmark
        benchmark_price = None
        benchmark_source = None

        # Note: Region model doesn't have benchmark_price field yet
        # We'll use ICO fallback for now

        # Use ICO fallback
        ico_data = fetch_ico_price_data()
        benchmark_price = ico_data["fallback_prices"]["peru_fob_benchmark"][
            "price_usd_per_kg"
        ]
        benchmark_source = "ICO fallback"

        # Calculate competitiveness score
        if benchmark_price:
            price_diff_pct = (
                (coop_fob_price - benchmark_price) / benchmark_price
            ) * 100
            # Score: 100 - (abs(difference_pct) * 2)
            # Capped between 0 and 100
            competitiveness_score = max(0, min(100, 100 - (abs(price_diff_pct) * 2)))
        else:
            competitiveness_score = 50
            price_diff_pct = 0

        return {
            "competitiveness_score": round(competitiveness_score, 2),
            "coop_price": coop_fob_price,
            "benchmark_price": benchmark_price,
            "benchmark_source": benchmark_source,
            "price_difference_pct": round(price_diff_pct, 2),
            "assessment": "competitive"
            if competitiveness_score >= 70
            else "market_rate"
            if competitiveness_score >= 50
            else "expensive",
        }

    def calculate_sourcing_risk(self, coop: Cooperative) -> dict[str, Any]:
        """
        Calculate comprehensive sourcing risk score (lower is better).

        Components:
        - Financial risk: max 25 points
        - Quality risk: max 20 points
        - Delivery risk: max 25 points
        - Geographic risk: max 15 points
        - Communication risk: max 15 points

        Total risk: 0-100 (lower is better)

        Args:
            coop: Cooperative model instance

        Returns:
            Dictionary with risk breakdown
        """
        total_risk = 0.0
        breakdown = {}

        # Financial risk (max 25 points)
        fin_data = coop.financial_data or {}
        annual_revenue = fin_data.get("annual_revenue_usd", 0)
        if annual_revenue < 50000:
            fin_risk = 25
        elif annual_revenue < 100000:
            fin_risk = 20
        elif annual_revenue < 250000:
            fin_risk = 15
        elif annual_revenue < 500000:
            fin_risk = 10
        else:
            fin_risk = 5
        total_risk += fin_risk
        breakdown["financial"] = {"risk_score": fin_risk, "revenue": annual_revenue}

        # Quality risk (max 20 points)
        quality_score = coop.quality_score or 50
        if quality_score >= 80:
            qual_risk = 5
        elif quality_score >= 70:
            qual_risk = 10
        elif quality_score >= 60:
            qual_risk = 15
        else:
            qual_risk = 20
        total_risk += qual_risk
        breakdown["quality"] = {"risk_score": qual_risk, "quality_score": quality_score}

        # Delivery risk (max 25 points)
        export_data = coop.export_readiness or {}
        op_data = coop.operational_data or {}
        years_exp = op_data.get("years_exporting", 0)
        customs_issues = export_data.get("customs_issues_count", 0)

        delivery_risk = 25  # Start with maximum risk
        # Reduce risk based on export experience
        if years_exp >= 5:
            delivery_risk -= 10
        elif years_exp >= 2:
            delivery_risk -= 5

        # Add risk for customs issues (2 points per issue, max 10 additional points)
        delivery_risk += min(10, customs_issues * 2)
        delivery_risk = max(0, min(25, delivery_risk))

        total_risk += delivery_risk
        breakdown["delivery"] = {
            "risk_score": delivery_risk,
            "years_exp": years_exp,
            "customs_issues": customs_issues,
        }

        # Geographic risk (max 15 points)
        # Based on altitude and region logistics
        geo_risk = 10  # Default moderate risk
        if coop.altitude_m:
            if coop.altitude_m > 2000:
                geo_risk = 15
            elif coop.altitude_m > 1500:
                geo_risk = 10
            else:
                geo_risk = 5
        total_risk += geo_risk
        breakdown["geographic"] = {
            "risk_score": geo_risk,
            "altitude_m": coop.altitude_m,
        }

        # Communication risk (max 15 points)
        comm_data = coop.communication_metrics or {}
        avg_response = comm_data.get("avg_response_hours", MAX_RESPONSE_TIME_HOURS)
        missed_meetings = comm_data.get("missed_meetings", 0)

        comm_risk = 0
        if avg_response > 72:
            comm_risk += 10
        elif avg_response > 48:
            comm_risk += 5

        comm_risk += min(5, missed_meetings)
        comm_risk = min(15, comm_risk)

        total_risk += comm_risk
        breakdown["communication"] = {
            "risk_score": comm_risk,
            "avg_response_hours": avg_response,
            "missed_meetings": missed_meetings,
        }

        # Overall assessment
        if total_risk < 30:
            assessment = "low"
        elif total_risk < 50:
            assessment = "moderate"
        else:
            assessment = "high"

        return {
            "total_risk_score": round(total_risk, 2),
            "max_risk_score": 100,
            "breakdown": breakdown,
            "assessment": assessment,
        }

    def generate_recommendation(
        self, total_score: float, risk_score: float
    ) -> dict[str, Any]:
        """
        Generate sourcing recommendation based on scores.

        Thresholds:
        - HIGHLY RECOMMENDED: score ≥80 AND risk <30
        - RECOMMENDED: score ≥70 AND risk <40
        - CONSIDER WITH CAUTION: score ≥60 AND risk <50
        - MONITOR CLOSELY: moderate scores
        - NOT RECOMMENDED: score <60 OR risk ≥60

        Args:
            total_score: Overall sourcing score (0-100)
            risk_score: Overall risk score (0-100, lower is better)

        Returns:
            Dictionary with recommendation level and reasoning
        """
        if total_score >= 80 and risk_score < 30:
            level = "HIGHLY RECOMMENDED"
            reasoning = "Excellent overall score with low risk profile. Strong candidate for sourcing."
        elif total_score >= 70 and risk_score < 40:
            level = "RECOMMENDED"
            reasoning = (
                "Good overall score with manageable risk. Suitable for sourcing."
            )
        elif total_score >= 60 and risk_score < 50:
            level = "CONSIDER WITH CAUTION"
            reasoning = "Adequate scores but some risk factors present. Requires closer evaluation."
        elif total_score < 60 or risk_score >= 60:
            level = "NOT RECOMMENDED"
            reasoning = "Low scores or high risk factors. Not suitable for sourcing at this time."
        else:
            level = "MONITOR CLOSELY"
            reasoning = "Moderate scores and risk. Consider for future once improvements are made."

        return {
            "level": level,
            "reasoning": reasoning,
            "total_score": round(total_score, 2),
            "risk_score": round(risk_score, 2),
        }
