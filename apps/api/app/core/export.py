"""Data export utilities for generating CSV and Excel files."""

import csv
import io
from datetime import datetime
from typing import Any, Dict, List

from fastapi.responses import StreamingResponse


class DataExporter:
    """Export data to various formats."""

    @staticmethod
    def to_csv(
        data: List[Dict[str, Any]],
        filename: str = "export.csv",
        include_headers: bool = True,
    ) -> StreamingResponse:
        """Export data to CSV format."""
        if not data:
            # Return empty CSV with error message
            output = io.StringIO()
            output.write("# No data to export\n")
            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )

        # Get headers from first row
        headers = list(data[0].keys())

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)

        if include_headers:
            writer.writeheader()

        # Write data rows
        for row in data:
            # Convert datetime objects to strings
            processed_row = {}
            for key, value in row.items():
                if isinstance(value, datetime):
                    processed_row[key] = value.isoformat()
                elif value is None:
                    processed_row[key] = ""
                else:
                    processed_row[key] = str(value)
            writer.writerow(processed_row)

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    @staticmethod
    def cooperatives_to_csv(cooperatives: List[Any]) -> StreamingResponse:
        """Export cooperatives to CSV."""
        data = []
        for coop in cooperatives:
            data.append(
                {
                    "ID": coop.id,
                    "Name": coop.name,
                    "Region": coop.region or "",
                    "Altitude (m)": coop.altitude_m or "",
                    "Varieties": coop.varieties or "",
                    "Certifications": coop.certifications or "",
                    "Contact Email": coop.contact_email or "",
                    "Website": coop.website or "",
                    "Status": coop.status or "",
                    "Next Action": coop.next_action or "",
                    "Quality Score": coop.quality_score or "",
                    "Reliability Score": coop.reliability_score or "",
                    "Economics Score": coop.economics_score or "",
                    "Total Score": coop.total_score or "",
                    "Confidence": coop.confidence or "",
                    "Created At": coop.created_at,
                    "Updated At": coop.updated_at,
                }
            )

        filename = (
            f"cooperatives_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        return DataExporter.to_csv(data, filename)

    @staticmethod
    def roasters_to_csv(roasters: List[Any]) -> StreamingResponse:
        """Export roasters to CSV."""
        data = []
        for roaster in roasters:
            data.append(
                {
                    "ID": roaster.id,
                    "Name": roaster.name,
                    "City": roaster.city or "",
                    "Contact Email": roaster.contact_email or "",
                    "Website": roaster.website or "",
                    "Peru Focus": roaster.peru_focus,
                    "Specialty Focus": roaster.specialty_focus,
                    "Price Position": roaster.price_position or "",
                    "Status": roaster.status or "",
                    "Next Action": roaster.next_action or "",
                    "Total Score": roaster.total_score or "",
                    "Confidence": roaster.confidence or "",
                    "Created At": roaster.created_at,
                    "Updated At": roaster.updated_at,
                }
            )

        filename = f"roasters_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        return DataExporter.to_csv(data, filename)

    @staticmethod
    def lots_to_csv(lots: List[Any]) -> StreamingResponse:
        """Export lots to CSV."""
        data = []
        for lot in lots:
            data.append(
                {
                    "ID": lot.id,
                    "Lot Number": lot.lot_number,
                    "Cooperative ID": lot.cooperative_id or "",
                    "Weight (kg)": lot.weight_kg or "",
                    "Grade": lot.grade or "",
                    "Cup Score": lot.cup_score or "",
                    "Price per kg (USD)": lot.price_per_kg_usd or "",
                    "Harvest Date": lot.harvest_date or "",
                    "Status": lot.status or "",
                    "Varietals": ", ".join(lot.varietals or []),
                    "Processing Method": lot.processing_method or "",
                    "Altitude (masl)": lot.altitude_masl or "",
                    "Notes": lot.notes or "",
                    "Created At": lot.created_at,
                    "Updated At": lot.updated_at,
                }
            )

        filename = f"lots_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        return DataExporter.to_csv(data, filename)
