"""General strict Enjarify adapters, without altering the original APK/DEX.

DEX handlers may target address zero when they discard the exception. Enjarify's
IR writer already emits a separate POP + GOTO handler in that case; its parser
incorrectly rejected the address unconditionally. Keep normal verifier checks.
"""
from enjarify import parsedex, dalvik

def install():
    original = dalvik.parseBytecode
    def parse(dex, start, shorts, handlers):
        ops = original(dex, start, shorts, handlers - {0})
        if 0 in handlers and ops and ops[0].type == dalvik.MoveResult:
            raise ValueError('Exception register at normal DEX entry has no value')
        return ops
    parsedex.parseBytecode = parse
