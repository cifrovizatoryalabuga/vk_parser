from aio_pika.patterns import NackMessage


class AmqpPermanentException(Exception):
    pass


class UnpackException(AmqpPermanentException):
    pass


class AmqpTmpError(NackMessage):
    pass
