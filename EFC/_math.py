from expr import spec, old_testcase

API = '''\
math ceil <float>
math fabs <float>
math floor <float>
math trunc <float>
math ulp <float> #注意_バージョン
math cbrt <float> #注意_バージョン
math exp <float>
math exp2 <float> #注意_バージョン
math expm1 <float>
math log <float>
math log1p <float>
math log2 <float>
math log10 <float>
math sqrt <float>
math sin <float>
math cos <float>
math tan <float>
math asin <float>
math acos <float>
math atan <float>
math sinh <float>
math cosh <float>
math tanh <float>
math asinh <float>
math acosh <float>
math atanh <float>
math degrees <float>
math radians <float>
math erf <float>
math erfc <float>
math gamma <float>
math lgamma <float>
math frexp <float>
math modf <float>
math isfinite <float>
math isinf <float>
math isnan <float>
math isqrt <int> #注意_バージョン
math isfinite <float>
math isfinite <float>
math copysign <float> <float>
math fmod <float> <float>
math ldexp <float> <int>
math nextafter <float> <float> #注意_バージョン
math remainder <float> <float>
math log <float> <float>
math pow <float> <float>
math atan2 <float> <float>
math isclose <float> <float>
math comb <int> <int>
math factorial <int>
math gcd <int> <int> <int>
math gcd <int> <int>
math lcm <int> <int> <int> #注意_バージョン
math lcm <int> <int> #注意_バージョン
math perm <int> <int> #注意_バージョン
math perm <int> #注意_バージョン
math prod <iterable> #注意_バージョン
math prod <iterable> start=1 #注意_バージョン
math pi_
math e_
math tau_
math inf_
math nan_
'''


def FaultSuite():
    import math

    SPECS = [
        spec(None,
             vars=dict(
                 math=math,
             ),
             ),
    ]
    return SPECS, API.splitlines()
