from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class GovernmentDataAdapter(ABC):
    @abstractmethod
    async def search_vehicle_record(self, plate_number: str) -> dict[str, Any] | None:
        pass

    @abstractmethod
    async def search_person_reference(self, reference_id: str) -> dict[str, Any] | None:
        pass


class MockGovernmentDataAdapter(GovernmentDataAdapter):
    """
    Mock adapter for demonstration & development.
    Simulates integration with official VAHAN & Police Registry records.
    Never exposes raw government endpoints. Returns simulated authorized response.
    """

    def __init__(self):
        self._mock_vehicles = {
            "GJ01AB1234": {
                "plate_number": "GJ01AB1234",
                "owner_name": "Ramesh Kumar Patel",
                "maker_model": "Hyundai Creta - White",
                "registration_date": "2021-04-15",
                "rto_location": "Ahmedabad RTO (GJ-01)",
                "chassis_number": "MA3xxxxxxxx12345",
                "stolen_status": "CLEAR",
                "blacklisted": False,
                "verified_source": "VAHAN_AUTHORIZATION_MOCK",
            },
            "GJ05CD5678": {
                "plate_number": "GJ05CD5678",
                "owner_name": "Suresh Shah",
                "maker_model": "Mahindra Bolero - Silver",
                "registration_date": "2019-11-20",
                "rto_location": "Surat RTO (GJ-05)",
                "chassis_number": "MA3xxxxxxxx56789",
                "stolen_status": "FLAGGED_STOLEN",
                "blacklisted": True,
                "stolen_FIR": "FIR-2026-SURAT-00412",
                "verified_source": "VAHAN_POLICE_FLAGGED_MOCK",
            },
            "GJ18EF9012": {
                "plate_number": "GJ18EF9012",
                "owner_name": "Vikram Singh",
                "maker_model": "Tata Harrier - Black",
                "registration_date": "2023-01-10",
                "rto_location": "Gandhinagar RTO (GJ-18)",
                "chassis_number": "MA3xxxxxxxx90123",
                "stolen_status": "CLEAR",
                "blacklisted": False,
                "verified_source": "VAHAN_AUTHORIZATION_MOCK",
            },
        }

    async def search_vehicle_record(self, plate_number: str) -> dict[str, Any] | None:
        normalized = plate_number.replace("-", "").replace(" ", "").upper()
        if normalized in self._mock_vehicles:
            return self._mock_vehicles[normalized]
        # Return generic authorized mock result for unknown plate
        return {
            "plate_number": normalized,
            "owner_name": "AUTHORIZED RECORD FOUND",
            "maker_model": "Sedan / SUV Class",
            "registration_date": "2022-08-01",
            "rto_location": "Gujarat State RTO",
            "stolen_status": "CLEAR",
            "blacklisted": False,
            "verified_source": "VAHAN_MOCK_FALLBACK",
        }

    async def search_person_reference(self, reference_id: str) -> dict[str, Any] | None:
        return {
            "reference_id": reference_id,
            "authorization_status": "PERMITTED_LOOKUP",
            "source": "GUJARAT_POLICE_MOCK_DB",
            "disclaimer": "Probabilistic match for operational verification only.",
        }
