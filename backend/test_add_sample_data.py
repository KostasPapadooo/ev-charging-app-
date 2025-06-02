import asyncio
from app.models.station import Station, StationLocation, ConnectorInfo, OperatorInfo
from app.repositories.station_repository import station_repository

async def add_sample_stations():
    sample_stations = [
        Station(
            tomtom_id="test_001",
            name="Test Station 1",
            location=StationLocation(
                type="Point",
                coordinates=[23.7275, 37.9755]  # Athens
            ),
            address="Test Address 1, Athens",
            connectors=[
                ConnectorInfo(
                    type="Type2",
                    max_power_kw=22.0,
                    current_type="AC",
                    status="AVAILABLE"
                )
            ],
            operator=OperatorInfo(
                name="Test Operator",
                website="https://test.com",
                phone="+30210123456"
            ),
            status="AVAILABLE",
            data_source="TEST"
        ),
        Station(
            tomtom_id="test_002",
            name="Test Station 2",
            location=StationLocation(
                type="Point",
                coordinates=[23.7300, 37.9800]  # Athens
            ),
            address="Test Address 2, Athens",
            connectors=[
                ConnectorInfo(
                    type="CCS",
                    max_power_kw=50.0,
                    current_type="DC",
                    status="BUSY"
                )
            ],
            operator=OperatorInfo(
                name="Test Operator 2",
                website="https://test2.com",
                phone="+30210123457"
            ),
            status="BUSY",
            data_source="TEST"
        )
    ]
    
    for station in sample_stations:
        await station_repository.create_station(station)
        print(f"Added station: {station.name}")

if __name__ == "__main__":
    asyncio.run(add_sample_stations()) 