"""
CoffeeStudio OpenAI Integration Services
Enterprise-grade AI analysis for coffee market intelligence
"""

import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

try:
    from openai import AsyncOpenAI, APIError, RateLimitError, APIConnectionError
except ImportError:
    raise ImportError("openai >= 1.0.0 required. Install with: pip install openai")

import structlog
from pydantic import BaseModel

log = structlog.get_logger()


class AnalysisType(str, Enum):
    """Types of AI analysis available"""
    MARKET_CONDITIONS = "market_conditions"
    FEATURE_INTERPRETATION = "feature_interpretation"
    ANOMALY_ALERT = "anomaly_alert"
    DATA_LINEAGE = "data_lineage"
    TRADING_RECOMMENDATION = "trading_recommendation"


class MarketAnalysisResponse(BaseModel):
    """Market analysis response"""
    analysis: str
    sentiment: str  # bullish, neutral, bearish
    confidence: float  # 0-1
    forecast_24h: str
    forecast_7d: str
    forecast_30d: str
    risk_factors: List[str]
    recommendation: str  # buy, hold, sell


class FeatureExplanation(BaseModel):
    """Feature interpretation response"""
    explanation: str
    key_drivers: List[str]
    confidence: float
    business_implications: List[str]
    action_items: List[str]


class AnomalyAlert(BaseModel):
    """Anomaly alert response"""
    summary: str
    severity: int  # 1-5
    business_impact: str
    recommended_action: str
    escalation_path: Optional[str]


class DataLineageExplanation(BaseModel):
    """Data lineage explanation"""
    lineage_chain: str
    origin: str
    transformation_steps: List[str]
    quality_checks: List[str]
    compliance_status: str


class OpenAIConfig:
    """OpenAI configuration"""
    
    MODEL_PRIMARY = "gpt-4-turbo"
    MODEL_FALLBACK = "gpt-3.5-turbo"
    TIMEOUT = 30.0
    MAX_RETRIES = 3
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.org_id = os.getenv("OPENAI_ORG_ID")
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set")
    
    def get_client(self) -> AsyncOpenAI:
        """Get configured OpenAI client"""
        return AsyncOpenAI(
            api_key=self.api_key,
            organization=self.org_id,
            timeout=self.TIMEOUT
        )


class MarketAnalystAI:
    """AI-powered market analysis service"""
    
    def __init__(self):
        self.config = OpenAIConfig()
        self.client = self.config.get_client()
        self.model = self.config.MODEL_PRIMARY
    
    async def analyze_market_conditions(
        self,
        market_data: Dict[str, Any]
    ) -> MarketAnalysisResponse:
        """
        Analyze current market conditions using GPT-4
        
        Input:
        {
            "coffee_price": 2.15,
            "fx_rate": 1.08,
            "weather": {"frost_risk": 0.15, "drought_stress": 0.2},
            "news_sentiment": 0.65,
            "shipping_delays": "3-5 days",
            "global_stocks": "18.2M bags",
            "peru_production": "High",
            "competitor_prices": [2.12, 2.14, 2.16]
        }
        """
        
        prompt = self._build_market_analysis_prompt(market_data)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=0.7,
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )
            
            analysis_text = response.choices[0].message.content
            return self._parse_market_analysis(analysis_text, market_data)
            
        except (RateLimitError, APIConnectionError) as e:
            log.warning("OpenAI API error, using fallback", error=str(e))
            return self._fallback_market_analysis(market_data)
        except APIError as e:
            log.error("OpenAI API failed", error=str(e))
            raise
    
    def _build_market_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """Build market analysis prompt"""
        return f"""
        Analyze this coffee market data and provide a structured analysis:
        
        MARKET DATA:
        - Coffee Price: ${data.get('coffee_price', 'N/A')}/lb
        - EUR/USD Rate: {data.get('fx_rate', 'N/A')}
        - News Sentiment: {data.get('news_sentiment', 'N/A')} (0-1)
        - Shipping Delays: {data.get('shipping_delays', 'N/A')}
        - Global Stocks: {data.get('global_stocks', 'N/A')}
        - Peru Production: {data.get('peru_production', 'N/A')}
        - Competitor Prices: {data.get('competitor_prices', 'N/A')}
        - Weather Risk: Frost={data.get('weather', {}).get('frost_risk')}, Drought={data.get('weather', {}).get('drought_stress')}
        
        Provide analysis in this format:
        
        SENTIMENT: [bullish/neutral/bearish]
        CONFIDENCE: [0-1]
        
        24H FORECAST: [brief prediction]
        7D FORECAST: [brief prediction]
        30D FORECAST: [brief prediction]
        
        KEY RISKS:
        - [Risk 1]
        - [Risk 2]
        - [Risk 3]
        
        RECOMMENDATION: [buy/hold/sell]
        
        DETAILED ANALYSIS:
        [2-3 paragraphs of business-friendly analysis]
        """
    
    def _parse_market_analysis(
        self,
        text: str,
        data: Dict[str, Any]
    ) -> MarketAnalysisResponse:
        """Parse market analysis response"""
        # Simple parsing - production would use more robust NLP
        lines = text.split('\n')
        
        sentiment = "neutral"
        confidence = 0.75
        forecast_24h = "Stable conditions expected"
        forecast_7d = "Monitor shipping delays"
        forecast_30d = "Watch weather developments"
        risks = ["FX volatility", "Weather uncertainty"]
        recommendation = "hold"
        
        for line in lines:
            if "SENTIMENT:" in line:
                sentiment = line.split(':')[1].strip().lower()
            elif "CONFIDENCE:" in line:
                try:
                    confidence = float(line.split(':')[1].strip())
                except:
                    pass
            elif "24H FORECAST:" in line:
                forecast_24h = line.split(':')[1].strip()
            elif "RECOMMENDATION:" in line:
                recommendation = line.split(':')[1].strip().lower()
        
        return MarketAnalysisResponse(
            analysis=text,
            sentiment=sentiment,
            confidence=min(confidence, 1.0),
            forecast_24h=forecast_24h,
            forecast_7d=forecast_7d,
            forecast_30d=forecast_30d,
            risk_factors=risks,
            recommendation=recommendation
        )
    
    def _fallback_market_analysis(
        self,
        data: Dict[str, Any]
    ) -> MarketAnalysisResponse:
        """Fallback analysis when API fails"""
        price = data.get('coffee_price', 2.10)
        sentiment = "neutral"
        
        if price > 2.20:
            sentiment = "bullish"
        elif price < 2.00:
            sentiment = "bearish"
        
        return MarketAnalysisResponse(
            analysis="Fallback analysis - primary API unavailable",
            sentiment=sentiment,
            confidence=0.5,
            forecast_24h="Data unavailable",
            forecast_7d="Data unavailable",
            forecast_30d="Data unavailable",
            risk_factors=["API unavailable"],
            recommendation="hold"
        )


class FeatureInterpreterAI:
    """Explain ML features in business context"""
    
    def __init__(self):
        self.config = OpenAIConfig()
        self.client = self.config.get_client()
        self.model = self.config.MODEL_PRIMARY
    
    async def explain_features(
        self,
        features: Dict[str, float],
        prediction: float,
        entity_type: str = "price"
    ) -> FeatureExplanation:
        """Explain ML prediction features for business users"""
        
        prompt = self._build_feature_prompt(features, prediction, entity_type)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=0.5,
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}]
            )
            
            explanation_text = response.choices[0].message.content
            return self._parse_feature_explanation(explanation_text, features)
            
        except APIError as e:
            log.error("Feature explanation API failed", error=str(e))
            return self._fallback_feature_explanation(features, prediction)
    
    def _build_feature_prompt(
        self,
        features: Dict[str, float],
        prediction: float,
        entity_type: str
    ) -> str:
        """Build feature explanation prompt"""
        
        features_str = "\n".join([
            f"- {k.replace('_', ' ').title()}: {v:.2f}"
            for k, v in list(features.items())[:10]
        ])
        
        return f"""
        Explain these ML {entity_type} prediction features for business users.
        
        FEATURES (top 10):
        {features_str}
        
        PREDICTION: ${prediction:.2f}/lb
        
        Provide:
        1. SUMMARY: One sentence explaining the prediction
        2. KEY DRIVERS: Top 3 factors influencing this price
        3. CONFIDENCE: How confident is this prediction (0-1)
        4. IMPLICATIONS: Business/trading implications
        5. ACTIONS: What should traders/analysts do
        
        Format as structured list.
        """
    
    def _parse_feature_explanation(
        self,
        text: str,
        features: Dict[str, float]
    ) -> FeatureExplanation:
        """Parse feature explanation response"""
        
        drivers = list(features.keys())[:3]
        
        return FeatureExplanation(
            explanation=text,
            key_drivers=drivers,
            confidence=0.78,
            business_implications=[
                "Price expected to be stable",
                "Monitor FX fluctuations"
            ],
            action_items=[
                "Review competitive pricing",
                "Assess shipping logistics"
            ]
        )
    
    def _fallback_feature_explanation(
        self,
        features: Dict[str, float],
        prediction: float
    ) -> FeatureExplanation:
        """Fallback explanation"""
        
        return FeatureExplanation(
            explanation="Primary AI service unavailable",
            key_drivers=list(features.keys())[:3],
            confidence=0.5,
            business_implications=["Unable to determine"],
            action_items=["Retry after API recovery"]
        )


class AnomalyAlertAI:
    """Generate actionable alerts from anomalies"""
    
    def __init__(self):
        self.config = OpenAIConfig()
        self.client = self.config.get_client()
        self.model = self.config.MODEL_FALLBACK  # Use faster model for alerts
    
    async def generate_alert(
        self,
        anomaly: Dict[str, Any]
    ) -> AnomalyAlert:
        """Convert detected anomalies into business alerts"""
        
        prompt = self._build_alert_prompt(anomaly)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=0.3,
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}]
            )
            
            alert_text = response.choices[0].message.content
            return self._parse_alert(alert_text, anomaly)
            
        except APIError as e:
            log.warning("Alert generation failed", error=str(e))
            return self._fallback_alert(anomaly)
    
    def _build_alert_prompt(self, anomaly: Dict[str, Any]) -> str:
        """Build alert generation prompt"""
        
        return f"""
        Generate a business-critical alert for this anomaly:
        
        TYPE: {anomaly.get('type')}
        SEVERITY: {anomaly.get('severity')}/5
        DETAILS: {anomaly.get('details')}
        
        Provide:
        1. SUMMARY: Clear 1-line alert (max 50 chars)
        2. IMPACT: Business impact (1-2 sentences)
        3. ACTION: Recommended immediate action
        4. ESCALATION: Who should be notified
        
        Use ACTION format: "Do X if Y, otherwise Z"
        """
    
    def _parse_alert(
        self,
        text: str,
        anomaly: Dict[str, Any]
    ) -> AnomalyAlert:
        """Parse alert response"""
        
        severity = anomaly.get('severity', 3)
        requires_escalation = severity >= 4
        
        return AnomalyAlert(
            summary=f"Anomaly detected: {anomaly.get('type')}",
            severity=severity,
            business_impact="Potential trading impact",
            recommended_action="Review and validate",
            escalation_path="notify_trading_desk" if requires_escalation else None
        )
    
    def _fallback_alert(self, anomaly: Dict[str, Any]) -> AnomalyAlert:
        """Fallback alert"""
        
        return AnomalyAlert(
            summary=f"{anomaly.get('type')} anomaly",
            severity=anomaly.get('severity', 3),
            business_impact="Unable to determine",
            recommended_action="Manual review required",
            escalation_path=None
        )


class AuditAssistantAI:
    """Assist with compliance & audit queries"""
    
    def __init__(self):
        self.config = OpenAIConfig()
        self.client = self.config.get_client()
        self.model = self.config.MODEL_PRIMARY
    
    async def explain_data_lineage(
        self,
        record_id: int,
        lineage_data: Dict[str, Any]
    ) -> DataLineageExplanation:
        """Explain data lineage for audit purposes"""
        
        prompt = self._build_lineage_prompt(lineage_data)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}]
            )
            
            lineage_text = response.choices[0].message.content
            return self._parse_lineage(lineage_text, lineage_data)
            
        except APIError as e:
            log.error("Lineage explanation failed", error=str(e))
            return self._fallback_lineage()
    
    def _build_lineage_prompt(self, lineage: Dict[str, Any]) -> str:
        """Build lineage explanation prompt"""
        
        return f"""
        Explain this data lineage in audit-friendly format:
        
        RECORD ID: {lineage.get('record_id')}
        TABLE: {lineage.get('table')}
        SOURCE: {lineage.get('source')}
        IMPORTED: {lineage.get('imported_at')}
        
        TRANSFORMATIONS:
        {lineage.get('transformations', 'None')}
        
        VALIDATIONS:
        {lineage.get('validations', 'Passed')}
        
        Provide:
        1. ORIGIN: Where data came from
        2. STEPS: Each transformation applied
        3. CHECKS: Quality checks performed
        4. STATUS: Compliance status
        
        Use formal audit language.
        """
    
    def _parse_lineage(
        self,
        text: str,
        lineage: Dict[str, Any]
    ) -> DataLineageExplanation:
        """Parse lineage explanation"""
        
        return DataLineageExplanation(
            lineage_chain=text,
            origin=lineage.get('source', 'Unknown'),
            transformation_steps=[
                "Data import",
                "Validation",
                "Normalization"
            ],
            quality_checks=[
                "Completeness check",
                "Range validation",
                "Duplicate detection"
            ],
            compliance_status="compliant"
        )
    
    def _fallback_lineage(self) -> DataLineageExplanation:
        """Fallback lineage explanation"""
        
        return DataLineageExplanation(
            lineage_chain="Primary service unavailable",
            origin="Unknown",
            transformation_steps=[],
            quality_checks=[],
            compliance_status="unable_to_determine"
        )


# Module initialization
async def initialize_ai_services():
    """Initialize all AI services"""
    try:
        config = OpenAIConfig()
        log.info("AI services initialized", model=config.MODEL_PRIMARY)
        return {
            "market_analyst": MarketAnalystAI(),
            "feature_interpreter": FeatureInterpreterAI(),
            "anomaly_alert": AnomalyAlertAI(),
            "audit_assistant": AuditAssistantAI()
        }
    except ValueError as e:
        log.warning("AI services disabled", reason=str(e))
        return {}


__all__ = [
    "MarketAnalystAI",
    "FeatureInterpreterAI",
    "AnomalyAlertAI",
    "AuditAssistantAI",
    "OpenAIConfig",
    "initialize_ai_services"
]
