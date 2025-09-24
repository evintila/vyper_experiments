import pytest

from vyper.exceptions import InvalidOperation


def test_increment(assert_compile_failed, get_contract):
    code = """
counter: public(uint256)

@external
def test_increment():
    self.counter = self.counter + 1
    """
    c = get_contract(code)
    c.test_increment()
    assert c.counter() == 1
