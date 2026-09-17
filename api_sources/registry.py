"""Adapter registry."""
from api_sources.base import BaseAdapter
from api_sources.abuseipdb import AbuseIPDBAdapter
from api_sources.alienvault import AlienVaultOTXAdapter
from api_sources.openweather import OpenWeatherAdapter
from api_sources.virustotal import VirusTotalAdapter


def all_adapters() -> dict[str, BaseAdapter]:
    return {
        "virustotal": VirusTotalAdapter(),
        "abuseipdb": AbuseIPDBAdapter(),
        "alienvault": AlienVaultOTXAdapter(),
        "openweather": OpenWeatherAdapter(),
    }


def get_adapter(name: str) -> BaseAdapter | None:
    return all_adapters().get(name)
