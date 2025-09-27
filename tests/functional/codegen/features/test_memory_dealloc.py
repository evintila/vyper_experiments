def test_memory_deallocation(get_contract):
    code = """
event Shimmy:
    a: indexed(address)
    b: uint256

interface Other:
    def sendit(): nonpayable

@external
def foo(target: address) -> uint256[2]:
    log Shimmy(a=empty(address), b=3)
    amount: uint256 = 1
    flargen: uint256 = 42
    extcall Other(target).sendit()
    return [amount, flargen]
    """

    code2 = """

@external
def sendit() -> bool:
    return True
    """

    c = get_contract(code)
    c2 = get_contract(code2)

    assert c.foo(c2.address) == [1, 42]

def test_early_deallocation(get_contract):
    code = """
@external
def foo() -> uint256[2]:
    a: uint256 = 0
    b: uint256 = 0
    a = 13
    b = a + 14
    return [a, b]
    """
    c = get_contract(code)
    assert c.foo() == [13, 27]

    # actually do some early deallocations
    code = """
@external
def foo() -> uint256:
    a: uint256 = 0
    for i: uint256 in range(1, 3):
        a += i
    b: uint256 = 0
    b += 1
    return b
    """
    c = get_contract(code)
    assert c.foo() == 1

    # multiple last uses
    code = """
@external
def foo() -> uint256:
    a: uint256 = 0
    c: uint256 = 0
    for i: uint256 in range(1, 3):
        a += i + c
    b: uint256 = 0
    b += 1
    return b
    """
    c = get_contract(code)
    assert c.foo() == 1

    # multiple last uses and one is a write
    code = """
@external
def foo() -> uint256:
    a: uint256 = 0
    c: uint256 = 0
    for i: uint256 in range(1, 3):
        a = i + c
    b: uint256 = 0
    b += 1
    return b
    """
    c = get_contract(code)
    assert c.foo() == 1

    # allocate in for
    code = """
@external
def foo() -> uint256:
    a: uint256 = 0
    for i: uint256 in range(1, 3):
        c: uint256 = 0
        a = i + c
        c += 1
    b: uint256 = 0
    b += 1
    return b
    """
    c = get_contract(code)
    assert c.foo() == 1

    # use on one branch
    code = """
@external
def foo() -> uint256:
    a: uint256 = 0
    b: uint256 = 0
    if b == 0:
        a = 12

    b += 1
    return b
    """
    c = get_contract(code)
    assert c.foo() == 1

    # using parameters
    code = """
@external
def foo(param: uint256) -> uint256:
    for i: uint256 in range(1, 3):
        c: uint256 = 0
        c = i + param
        c += 1
    b: uint256 = 0
    b += 1
    return b
    """
    c = get_contract(code)
    assert c.foo(1) == 1

def test_early_deallocation_not_used(get_contract):
    code = """
@external
def foo() -> uint256:
    a: uint256 = 0
    b: uint256 = 0
    b = 14
    return b
    """
    c = get_contract(code)

    assert c.foo() == 14

    # not used dynarray
    code = """
@external
def foo() -> uint256:
    buf1: DynArray[uint256, 500] = [1, 2, 3, 4, 5]
    b: uint256 = 0
    b = 14
    return b
    """
    c = get_contract(code)
    assert c.foo() == 14

    # not used dynarray parameters
    code = """
@external
def foo(param: uint256) -> uint256:
    buf1: DynArray[uint256, 500] = [1, 2, 3, 4, 5]
    b: uint256 = 0
    b = 14
    return b
    """
    c = get_contract(code)
    assert c.foo(12) == 14

def test_early_deallocation_internal_call(get_contract):
    # call an internal
    code = """
@internal
def bar(b: uint256) -> uint256:
    a: uint256 = 0
    for i: uint256 in range(1, 3):
        a += i # <- can't dealoc, defer
        if a == 2:
            assert(a < b)
            return 42 + b
    return b
@external
def foo() -> uint256:
    a1: uint256 = 0
    for i: uint256 in range(1, 3):
        a1 += i
        if a1 >= 1:
            self.bar(i + 3)
    b1: uint256 = 0
    b1 += 1
    return b1
    """
    c = get_contract(code)
    assert c.foo() == 1

    # call an internal as the last use
    code = """
@internal
def bar(b: uint256) -> uint256:
    a: uint256 = 0
    for i: uint256 in range(1, 3):
        a += i # <- can't dealoc, defer
        if a == 2:
            assert(a < b)
            return 42 + b
    return b
@external
def foo() -> uint256:
    a1: uint256 = 0
    for i: uint256 in range(1, 3):
        a1 += i
        self.bar(a1)
    b1: uint256 = 0
    b1 += 1
    return b1
    """
    c = get_contract(code)
    assert c.foo() == 1

    # call an two internals that might leak
    code = """
@internal
def no_uses_dyn_array(b: uint256) -> uint256:
    buf: DynArray[uint256, 500] = [1, 2, 3, 4, 5]
    b5: uint256 = 0
    b5 += 3
    return b5

@internal
def no_uses_dyn_array2(b: uint256) -> uint256:
    buf2: DynArray[uint256, 500] = [1, 2, 3, 4, 5]
    b6: uint256 = 0
    b6 += 3
    return b6

@external
def foo() -> uint256:
    a7: uint256 = 0
    a7 = self.no_uses_dyn_array(1)
    a7 += self.no_uses_dyn_array2(4)
    return a7
    """
    c = get_contract(code)
    assert c.foo() == 6

# def test_early_deallocation_builtin_param(get_contract):
#     # sqrt bultin
#     code = """
# @external
# def foo() -> decimal:
#     a: decimal = 0.0
#     b: decimal = 0.0
#     for i: uint256 in range(1, 3):
#         a = sqrt(a)
#         b += a
#     return b
#     """
#     c = get_contract(code)
#     assert c.foo() == 0.0
#
#     # the sqrt parameter is a const
#     code = """
# @external
# def foo() -> decimal:
#     a: decimal = 0.0
#     b: decimal = 0.0
#     for i: uint256 in range(1, 3):
#         a = sqrt(0.0)
#         b += a
#     return b
#     """
#     c = get_contract(code)
#     assert c.foo() == 0.0
#
#     # the sqrt param is a parameter from outside
#     code = """
# @external
# def foo(param: decimal) -> decimal:
#     a: decimal = 0.0
#     b: decimal = 0.0
#     for i: uint256 in range(1, 3):
#         a = sqrt(param)
#         b += a
#     return b
#     """
#     c = get_contract(code)
#     assert c.foo(0.0) == 0.0
