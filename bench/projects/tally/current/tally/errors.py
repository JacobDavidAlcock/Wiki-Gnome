class TallyError(Exception):
    pass


class InvalidAmount(TallyError, ValueError):
    pass


class UnknownMember(TallyError, KeyError):
    def __str__(self) -> str:
        return str(self.args[0]) if self.args else ""


class DuplicateMember(TallyError):
    pass


class UnsettledBalance(TallyError):
    pass


class UnsupportedFormat(TallyError):
    pass
