import pytest

from vyper.exceptions import InvalidOperation


def test_increment(assert_compile_failed, get_contract):
    code = """
counter: public(uint256)

@external
def test():
    self.counter = self.counter + 1
    """
    c = get_contract(code)
    c.test()
    assert c.counter() == 1

def test_increment_side_effects(assert_compile_failed, get_contract):
    code = """
counter: public(uint256)

@internal
def get_index_with_side_effect() -> uint256:
    self.counter += 1 # side effect
    return 3

@external
def test() -> DynArray[uint256, 5]:
    buf: DynArray[uint256, 5] = [1, 2, 3, 4, 5]
    a: uint256 = 3
    buf[self.get_index_with_side_effect()] = buf[a]  + 2
    return buf
    """
    c = get_contract(code)
    c.test()
    assert c.counter() == 1

def test_increment_side_effects_2(assert_compile_failed, get_contract):
    code = """
counter: public(uint256)

@internal
def get_index_with_side_effect() -> uint256:
    self.counter += 1 # side effect
    return 3

@external
def test() -> DynArray[uint256, 5]:
    buf: DynArray[uint256, 5] = [1, 2, 3, 4, 5]
    a: uint256 = 3
    buf[self.get_index_with_side_effect()] += buf[a]  + 2
    return buf
    """
    c = get_contract(code)
    c.test()
    assert c.counter() == 1

def test_increment_side_effects_bounds_check(assert_compile_failed, get_contract):
    code = """
counter: public(uint256)

@internal
def get_index_with_side_effect() -> uint256:
    self.counter += 1 # side effect
    return 1

@external
def test() -> DynArray[uint256, 5]:
    buf: DynArray[uint256, 5] = [1, 2, 3, 4, 5]
    a: uint256 = 3
    buf[self.get_index_with_side_effect() + a] += 2
    return buf
    """
    c = get_contract(code)
    c.test()
    assert c.counter() == 1

def test_increment_side_effects_also_rhs(assert_compile_failed, get_contract):
    code = """
counter: public(uint256)

@internal
def get_index_with_side_effect() -> uint256:
    self.counter += 1 # side effect
    return self.counter

@external
def test() -> DynArray[uint256, 5]:
    buf: DynArray[uint256, 5] = [1, 2, 3, 4, 5]
    a: uint256 = 0
    buf[self.get_index_with_side_effect() + a] = buf[self.get_index_with_side_effect() + a] + 2
    return buf
    """
    c = get_contract(code)
    c.test()
    assert c.counter() == 2

def test_increment_side_effects_also_rhs_2(assert_compile_failed, get_contract):
    code = """
counter: public(uint256)

@internal
def get_index_with_side_effect() -> uint256:
    self.counter += 1 # side effect
    return self.counter

@external
def test() -> DynArray[uint256, 5]:
    buf: DynArray[uint256, 5] = [1, 2, 3, 4, 5]
    a: uint256 = 1
    buf[self.get_index_with_side_effect() + a] += buf[self.get_index_with_side_effect() + a] + 2
    return buf
    """
    c = get_contract(code)
    c.test()
    assert c.counter() == 2
