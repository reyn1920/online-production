#!/usr / bin / env python3
"""
Environment Configuration Manager

This module handles secure loading and validation of environment variables
following go - live security best practices:
- Never hardcode secrets
- Use environment variable hierarchy
- Validate required configurations
- Provide secure defaults
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

@dataclass


class DatabaseConfig:
    """Database configuration settings"""

    url: str
    pool_size: int = 10
    max_overflow: int = 20
    echo: bool = False

@dataclass


class SecurityConfig:
    """Security and authentication settings"""

    secret_key: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

@dataclass


class PetCareAPIs:
    """Pet care and animal API configurations"""

    ebird_token: Optional[str] = None
    dog_api_key: Optional[str] = None
    cat_api_key: Optional[str] = None
    petfinder_key: Optional[str] = None
    petfinder_secret: Optional[str] = None

    @property


    def is_ebird_enabled(self) -> bool:
        return bool(self.ebird_token)

    @property


    def is_dog_api_enabled(self) -> bool:
        return bool(self.dog_api_key)

    @property


    def is_cat_api_enabled(self) -> bool:
        return bool(self.cat_api_key)

    @property


    def is_petfinder_enabled(self) -> bool:
        return bool(self.petfinder_key and self.petfinder_secret)

@dataclass


class VetServicesAPIs:
    """Veterinary and scheduling service APIs"""

    vetster_key: Optional[str] = None
    pawp_key: Optional[str] = None
    airvet_key: Optional[str] = None
    calendly_token: Optional[str] = None

    @property


    def is_vetster_enabled(self) -> bool:
        return bool(self.vetster_key)

    @property


    def is_pawp_enabled(self) -> bool:
        return bool(self.pawp_key)

    @property


    def is_airvet_enabled(self) -> bool:
        return bool(self.airvet_key)

    @property


    def is_calendly_enabled(self) -> bool:
        return bool(self.calendly_token)

@dataclass


class GeocodingAPIs:
    """Geocoding and places API configurations"""

    nominatim_user_agent: Optional[str] = None
    opencage_api_key: Optional[str] = None
    foursquare_api_key: Optional[str] = None
    google_places_key: Optional[str] = None
    yelp_api_key: Optional[str] = None

    @property


    def is_nominatim_enabled(self) -> bool:
        return bool(self.nominatim_user_agent)

    @property


    def is_opencage_enabled(self) -> bool:
        return bool(self.opencage_api_key)

    @property


    def is_foursquare_enabled(self) -> bool:
        return bool(self.foursquare_api_key)

    @property


    def is_google_places_enabled(self) -> bool:
        return bool(self.google_places_key)

    @property


    def is_yelp_enabled(self) -> bool:
        return bool(self.yelp_api_key)

@dataclass


class AffiliateConfig:
    """Affiliate program configurations"""

    chewy_id: Optional[str] = None
    petco_key: Optional[str] = None
    tractor_supply_key: Optional[str] = None
    only_natural_pet_key: Optional[str] = None
    barkbox_id: Optional[str] = None

    @property


    def enabled_programs(self) -> List[str]:
        """Return list of enabled affiliate programs"""
        programs = []
        if self.chewy_id:
            programs.append("chewy")
        if self.petco_key:
            programs.append("petco")
        if self.tractor_supply_key:
            programs.append("tractor_supply")
        if self.only_natural_pet_key:
            programs.append("only_natural_pet")
        if self.barkbox_id:
            programs.append("barkbox")
        return programs

@dataclass


class FeatureFlags:
    """Feature flag configurations"""

    affiliate_processing: bool = True
    pet_search: bool = True
    vet_booking: bool = False
    content_generation: bool = True
    analytics: bool = True
    pet_care_apis: bool = True
    geocoding_apis: bool = False
    places_apis: bool = False


class EnvironmentConfig:
    """Main environment configuration manager"""


    def __init__(self):
        self.environment = self._get_env("ENVIRONMENT", "development")
        self.debug = self._get_bool_env("DEBUG", True)
        self.port = self._get_int_env("PORT", 8000)
        self.host = self._get_env("HOST", "0.0.0.0")

        # Load configurations
        self.database = self._load_database_config()
        self.security = self._load_security_config()
        self.pet_care_apis = self._load_pet_care_apis()
        self.vet_services = self._load_vet_services()
        self.geocoding_apis = self._load_geocoding_apis()
        self.affiliates = self._load_affiliate_config()
        self.features = self._load_feature_flags()

        # Validate critical configurations
        self._validate_config()

        logger.info(f"Environment configuration loaded: {self.environment}")
        logger.info(f"Enabled affiliate programs: {self.affiliates.enabled_programs}")
        logger.info(
            f"Pet care APIs status: eBird={self.pet_care_apis.is_ebird_enabled}, "
            f"Dog={self.pet_care_apis.is_dog_api_enabled}, "
            f"Cat={self.pet_care_apis.is_cat_api_enabled}, "
            f"Petfinder={self.pet_care_apis.is_petfinder_enabled}"
        )
        logger.info(
            f"Geocoding APIs status: Nominatim={self.geocoding_apis.is_nominatim_enabled}, "
            f"OpenCage={self.geocoding_apis.is_opencage_enabled}, "
            f"Foursquare={self.geocoding_apis.is_foursquare_enabled}, "
            f"Google Places={self.geocoding_apis.is_google_places_enabled}, "
            f"Yelp={self.geocoding_apis.is_yelp_enabled}"
        )


    def _get_env(self, key: str, default: str = "") -> str:
        """Get environment variable with default"""
        return os.getenv(key, default)


    def _get_int_env(self, key: str, default: int) -> int:
        """Get integer environment variable with default"""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            logger.warning(f"Invalid integer value for {key}, using default: {default}")
            return default


    def _get_bool_env(self, key: str, default: bool) -> bool:
        """Get boolean environment variable with default"""
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")


    def _load_database_config(self) -> DatabaseConfig:
        """Load database configuration"""
        return DatabaseConfig(
            url = self._get_env("DATABASE_URL", "sqlite:///./data / app.db"),
                pool_size = self._get_int_env("DATABASE_POOL_SIZE", 10),
                max_overflow = self._get_int_env("DATABASE_MAX_OVERFLOW", 20),
                echo = self._get_bool_env("DATABASE_ECHO", False),
                )


    def _load_security_config(self) -> SecurityConfig:
        """Load security configuration"""
        secret_key = self._get_env("SECRET_KEY")
        jwt_secret = self._get_env("JWT_SECRET")

        # Generate secure defaults for development
        if not secret_key and self.environment == "development":
            secret_key = "dev - secret - key - change - in - production"
            logger.warning("Using default secret key for development")

        if not jwt_secret and self.environment == "development":
            jwt_secret = "dev - jwt - secret - change - in - production"
            logger.warning("Using default JWT secret for development")

        return SecurityConfig(
            secret_key = secret_key,
                jwt_secret = jwt_secret,
                jwt_algorithm = self._get_env("JWT_ALGORITHM", "HS256"),
                jwt_expiration_hours = self._get_int_env("JWT_EXPIRATION_HOURS", 24),
                )


    def _load_pet_care_apis(self) -> PetCareAPIs:
        """Load pet care API configurations"""
        return PetCareAPIs(
            ebird_token = self._get_env("EBIRD_API_TOKEN") or None,
                dog_api_key = self._get_env("DOG_API_KEY") or None,
                cat_api_key = self._get_env("CAT_API_KEY") or None,
                petfinder_key = self._get_env("PETFINDER_KEY") or None,
                petfinder_secret = self._get_env("PETFINDER_SECRET") or None,
                )


    def _load_vet_services(self) -> VetServicesAPIs:
        """Load veterinary service API configurations"""
        return VetServicesAPIs(
            vetster_key = self._get_env("VETSTER_API_KEY") or None,
                pawp_key = self._get_env("PAWP_API_KEY") or None,
                airvet_key = self._get_env("AIRVET_API_KEY") or None,
                calendly_token = self._get_env("CALENDLY_TOKEN") or None,
                )


    def _load_geocoding_apis(self) -> GeocodingAPIs:
        """Load geocoding and places API configurations"""
        return GeocodingAPIs(
            nominatim_user_agent = self._get_env("NOMINATIM_USER_AGENT") or None,
                opencage_api_key = self._get_env("OPENCAGE_API_KEY") or None,
                foursquare_api_key = self._get_env("FOURSQUARE_API_KEY") or None,
                google_places_key = self._get_env("GOOGLE_PLACES_KEY") or None,
                yelp_api_key = self._get_env("YELP_API_KEY") or None,
                )


    def _load_affiliate_config(self) -> AffiliateConfig:
        """Load affiliate program configurations"""
        return AffiliateConfig(
            chewy_id = self._get_env("CHEWY_AFFILIATE_ID") or None,
                petco_key = self._get_env("PETCO_AFFILIATE_KEY") or None,
                tractor_supply_key = self._get_env("TRACTOR_SUPPLY_KEY") or None,
                only_natural_pet_key = self._get_env("ONLY_NATURAL_PET_KEY") or None,
                barkbox_id = self._get_env("BARKBOX_AFFILIATE_ID") or None,
                )


    def _load_feature_flags(self) -> FeatureFlags:
        """Load feature flag configurations"""
        return FeatureFlags(
            affiliate_processing = self._get_bool_env(
                "ENABLE_AFFILIATE_PROCESSING", True
            ),
                pet_search = self._get_bool_env("ENABLE_PET_SEARCH", True),
                vet_booking = self._get_bool_env("ENABLE_VET_BOOKING", False),
                content_generation = self._get_bool_env("ENABLE_CONTENT_GENERATION", True),
                analytics = self._get_bool_env("ENABLE_ANALYTICS", True),
                pet_care_apis = self._get_bool_env("ENABLE_PET_CARE_APIS", True),
                geocoding_apis = self._get_bool_env("ENABLE_GEOCODING_APIS", False),
                places_apis = self._get_bool_env("ENABLE_PLACES_APIS", False),
                )


    def _validate_config(self):
        """Validate critical configuration settings"""
        errors = []

        # Validate production security
        if self.environment == "production":
            if not self.security.secret_key or "dev-" in self.security.secret_key:
                errors.append("Production SECRET_KEY must be set and secure")

            if not self.security.jwt_secret or "dev-" in self.security.jwt_secret:
                errors.append("Production JWT_SECRET must be set and secure")

        # Validate database URL
        if not self.database.url:
            errors.append("DATABASE_URL must be configured")

        if errors:
            for error in errors:
                logger.error(f"Configuration error: {error}")
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")


    def get_api_status(self) -> Dict[str, Any]:
        """Get status of all configured APIs"""
        return {
            "pet_care": {
                "ebird": self.pet_care_apis.is_ebird_enabled,
                    "dog_api": self.pet_care_apis.is_dog_api_enabled,
                    "cat_api": self.pet_care_apis.is_cat_api_enabled,
                    "petfinder": self.pet_care_apis.is_petfinder_enabled,
                    },
                "vet_services": {
                "vetster": self.vet_services.is_vetster_enabled,
                    "pawp": self.vet_services.is_pawp_enabled,
                    "airvet": self.vet_services.is_airvet_enabled,
                    "calendly": self.vet_services.is_calendly_enabled,
                    },
                "geocoding_apis": {
                "nominatim": self.geocoding_apis.is_nominatim_enabled,
                    "opencage": self.geocoding_apis.is_opencage_enabled,
                    "foursquare": self.geocoding_apis.is_foursquare_enabled,
                    "google_places": self.geocoding_apis.is_google_places_enabled,
                    "yelp": self.geocoding_apis.is_yelp_enabled,
                    },
                "affiliates": {
                "enabled_programs": self.affiliates.enabled_programs,
                    "total_enabled": len(self.affiliates.enabled_programs),
                    },
                "features": {
                "affiliate_processing": self.features.affiliate_processing,
                    "pet_search": self.features.pet_search,
                    "vet_booking": self.features.vet_booking,
                    "content_generation": self.features.content_generation,
                    "analytics": self.features.analytics,
                    "geocoding_apis": self.features.geocoding_apis,
                    "places_apis": self.features.places_apis,
                    },
                }

# Global configuration instance
config = EnvironmentConfig()

# Export commonly used configurations
__all__ = [
    "config",
        "EnvironmentConfig",
        "DatabaseConfig",
        "SecurityConfig",
        "PetCareAPIs",
        "VetServicesAPIs",
        "GeocodingAPIs",
        "AffiliateConfig",
        "FeatureFlags",
]
