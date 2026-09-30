class PartnerError(Exception):
    """Base partner exception."""
    pass


class PartnerNotFoundError(PartnerError):
    pass


class PartnerKAnonymityError(PartnerError):
    pass


class PartnerReplayError(PartnerError):
    pass
