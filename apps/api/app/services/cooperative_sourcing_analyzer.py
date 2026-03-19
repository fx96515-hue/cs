"""
Cooperative Sourcing Analyzer Service.

Comprehensive scoring and analysis system for evaluating Peru coffee cooperatives
for sourcing decisions. Implements multi-dimensional scoring across supply capacity,
export readiness, communication quality, pricing, and risk assessment.
"""

from typing import Any
from datetime import datetime, timezone, timedelta
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
                parsed = self._parse_cached_at(cached_at)
                if parsed and not self._is_cache_stale(parsed):
                    return coop.sourcing_scores
            else:
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

    def _parse_cached_at(self, value: str) -> datetime | None:
        try:
            raw = value.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(raw)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except Exception:
            return None

    def _is_cache_stale(self, cached_at: datetime) -> bool:
        from app.core.config import settings

        max_age = timedelta(days=settings.SOURCING_ANALYSIS_STALE_DAYS)
        return datetime.now(timezone.utc) - cached_at > max_age

    @staticmethod
    def _score_from_thresholds(
        value: float | int,
        thresholds: list[tuple[float, int]],
        default_score: int,
    ) -> int:
        for threshold, score in thresholds:
            if value >= threshold:
                return score
        return default_score

    @staticmethod
    def _label_from_thresholds(
        value: float,
        thresholds: list[tuple[float, str]],
        default_label: str,
    ) -> str:
        for threshold, label in thresholds:
            if value >= threshold:
                return label
        return default_label

    @staticmethod
    def _license_score(has_license: bool, license_expiry: Any) -> int:
        if has_license and license_expiry:
            return 25
        if has_license:
            return 20
        return 0

    @staticmethod
    def _certification_score(cert_count: int) -> int:
        if cert_count >= 3:
            return 25
        if cert_count == 2:
            return 20
        if cert_count == 1:
            return 15
        return 5

    @staticmethod
    def _customs_score(customs_issues: int) -> int:
        if customs_issues == 0:
            return 15
        if customs_issues <= 2:
            return 10
        if customs_issues <= 5:
            return 5
        return 0

    @staticmethod
    def _response_score(avg_response_hours: float | int) -> int:
        if avg_response_hours <= 24:
            return 25
        if avg_response_hours <= 48:
            return 20
        if avg_response_hours <= 72:
            return 10
        return 5

    @staticmethod
    def _meeting_score(missed_meetings: int) -> int:
        if missed_meetings == 0:
            return 15
        if missed_meetings <= 1:
            return 12
        if missed_meetings <= 3:
            return 8
        return 3

    @staticmethod
    def _pricing_assessment(competitiveness_score: float) -> str:
        if competitiveness_score >= 70:
            return "competitive"
        if competitiveness_score >= 50:
            return "market_rate"
        return "expensive"

    @staticmethod
    def _financial_risk_score(annual_revenue: float | int) -> int:
        if annual_revenue < 50000:
            return 25
        if annual_revenue < 100000:
            return 20
        if annual_revenue < 250000:
            return 15
        if annual_revenue < 500000:
            return 10
        return 5

    @staticmethod
    def _quality_risk_score(quality_score: float) -> int:
        if quality_score >= 80:
            return 5
        if quality_score >= 70:
            return 10
        if quality_score >= 60:
            return 15
        return 20

    @staticmethod
    def _base_delivery_risk(years_exp: float | int) -> int:
        if years_exp >= 5:
            return 15
        if years_exp >= 2:
            return 20
        return 25

    @staticmethod
    def _geographic_risk_score(altitude_m: float | int | None) -> int:
        if altitude_m is None:
            return 10
        if altitude_m > 2000:
            return 15
        if altitude_m > 1500:
            return 10
        return 5

    @staticmethod
    def _communication_risk_score(
        avg_response: float | int, missed_meetings: int
    ) -> int:
        response_risk = 0
        if avg_response > 72:
            response_risk = 10
        elif avg_response > 48:
            response_risk = 5
        return min(15, response_risk + min(5, missed_meetings))

    @staticmethod
    def _risk_assessment(total_risk: float) -> str:
        if total_risk < 30:
            return "low"
        if total_risk < 50:
            return "moderate"
        return "high"

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
        op_data = coop.operational_data or {}
        volume_kg = op_data.get("annual_volume_kg", 0)
        farmer_count = op_data.get("farmer_count", 0)
        storage_kg = op_data.get("storage_capacity_kg", 0)
        facilities = op_data.get("processing_facilities", [])
        years_exporting = op_data.get("years_exporting", 0)
        volume_score = self._score_from_thresholds(
            volume_kg, [(100000, 30), (50000, 25), (25000, 20), (10000, 15)], 5
        )
        farmer_score = self._score_from_thresholds(
            farmer_count, [(500, 20), (200, 17), (100, 14), (50, 10)], 5
        )
        storage_score = self._score_from_thresholds(
            storage_kg, [(200000, 20), (100000, 17), (50000, 14), (25000, 10)], 5
        )
        facility_score = (8 if "wet_mill" in facilities else 0) + (
            7 if "dry_mill" in facilities else 0
        )
        experience_score = self._score_from_thresholds(
            years_exporting, [(10, 15), (5, 12), (3, 9), (1, 6)], 2
        )

        score = float(
            volume_score
            + farmer_score
            + storage_score
            + facility_score
            + experience_score
        )
        breakdown = {
            "volume": {"score": volume_score, "volume_kg": volume_kg},
            "farmers": {"score": farmer_score, "count": farmer_count},
            "storage": {"score": storage_score, "capacity_kg": storage_kg},
            "facilities": {"score": facility_score, "types": facilities},
            "experience": {"score": experience_score, "years": years_exporting},
        }
        assessment = self._label_from_thresholds(
            score, [(75, "strong"), (50, "adequate")], "limited"
        )

        return {
            "score": round(score, 2),
            "max_score": 100,
            "breakdown": breakdown,
            "assessment": assessment,
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
        export_data = coop.export_readiness or {}
        has_license = export_data.get("has_export_license", False)
        license_expiry = export_data.get("license_expiry_date")
        senasa_registered = export_data.get("senasa_registered", False)
        senasa_score = 25 if senasa_registered else 0
        cert_list = export_data.get("certifications", [])
        cert_count = len(cert_list)
        customs_issues = export_data.get("customs_issues_count", 0)
        has_coordinator = export_data.get("has_document_coordinator", False)
        license_score = self._license_score(has_license, license_expiry)
        cert_score = self._certification_score(cert_count)
        customs_score = self._customs_score(customs_issues)
        coordinator_score = 10 if has_coordinator else 0

        score = float(
            license_score
            + senasa_score
            + cert_score
            + customs_score
            + coordinator_score
        )
        breakdown = {
            "license": {
                "score": license_score,
                "valid": has_license,
                "expiry": license_expiry,
            },
            "senasa": {"score": senasa_score, "registered": senasa_registered},
            "certifications": {
                "score": cert_score,
                "count": cert_count,
                "list": cert_list,
            },
            "customs": {"score": customs_score, "issues": customs_issues},
            "coordinator": {"score": coordinator_score, "has": has_coordinator},
        }
        assessment = self._label_from_thresholds(
            score, [(75, "ready"), (50, "partially_ready")], "not_ready"
        )

        return {
            "score": round(score, 2),
            "max_score": 100,
            "breakdown": breakdown,
            "assessment": assessment,
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
        comm_data = coop.communication_metrics or {}
        digital_data = coop.digital_footprint or {}
        avg_response_hours = comm_data.get(
            "avg_response_hours", MAX_RESPONSE_TIME_HOURS
        )
        languages = comm_data.get("languages", [])
        missed_meetings = comm_data.get("missed_meetings", 0)
        response_score = self._response_score(avg_response_hours)
        language_set = {str(lang).lower() for lang in languages}
        lang_score = (
            5
            + (15 if "english" in language_set else 0)
            + (10 if "german" in language_set else 0)
        )
        digital_score = (
            (8 if digital_data.get("has_website") else 0)
            + (4 if digital_data.get("has_facebook") else 0)
            + (4 if digital_data.get("has_instagram") else 0)
            + (4 if digital_data.get("has_whatsapp") else 0)
        )
        doc_score = (8 if digital_data.get("has_photos") else 0) + (
            7 if digital_data.get("has_cupping_scores") else 0
        )
        meeting_score = self._meeting_score(missed_meetings)

        score = float(
            response_score + lang_score + digital_score + doc_score + meeting_score
        )
        breakdown = {
            "response_time": {"score": response_score, "avg_hours": avg_response_hours},
            "languages": {"score": lang_score, "list": languages},
            "digital_presence": {"score": digital_score, "channels": digital_data},
            "documentation": {"score": doc_score},
            "meetings": {"score": meeting_score, "missed": missed_meetings},
        }
        assessment = self._label_from_thresholds(
            score, [(80, "excellent"), (60, "good")], "needs_improvement"
        )

        return {
            "score": round(score, 2),
            "max_score": 100,
            "breakdown": breakdown,
            "assessment": assessment,
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
            "assessment": self._pricing_assessment(competitiveness_score),
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
        fin_data = coop.financial_data or {}
        annual_revenue = fin_data.get("annual_revenue_usd", 0)
        quality_score = coop.quality_score or 50
        export_data = coop.export_readiness or {}
        op_data = coop.operational_data or {}
        years_exp = op_data.get("years_exporting", 0)
        customs_issues = export_data.get("customs_issues_count", 0)
        comm_data = coop.communication_metrics or {}
        avg_response = comm_data.get("avg_response_hours", MAX_RESPONSE_TIME_HOURS)
        missed_meetings = comm_data.get("missed_meetings", 0)
        fin_risk = self._financial_risk_score(annual_revenue)
        qual_risk = self._quality_risk_score(quality_score)
        base_delivery_risk = self._base_delivery_risk(years_exp)
        delivery_risk = max(
            0, min(25, base_delivery_risk + min(10, customs_issues * 2))
        )
        geo_risk = self._geographic_risk_score(coop.altitude_m)
        comm_risk = self._communication_risk_score(avg_response, missed_meetings)

        total_risk = float(fin_risk + qual_risk + delivery_risk + geo_risk + comm_risk)
        breakdown = {
            "financial": {"risk_score": fin_risk, "revenue": annual_revenue},
            "quality": {"risk_score": qual_risk, "quality_score": quality_score},
            "delivery": {
                "risk_score": delivery_risk,
                "years_exp": years_exp,
                "customs_issues": customs_issues,
            },
            "geographic": {"risk_score": geo_risk, "altitude_m": coop.altitude_m},
            "communication": {
                "risk_score": comm_risk,
                "avg_response_hours": avg_response,
                "missed_meetings": missed_meetings,
            },
        }
        assessment = self._risk_assessment(total_risk)

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
