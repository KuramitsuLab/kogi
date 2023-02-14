import collections
from codebase import Seed, CodeBase, FaultSuite
from fault import DebugFaults, AllFaults
from kogi.task.diagnosis import convert_error_diagnosis, reload

reload('diagnosis_ja.txt')


class Generator(object):
    def __init__(self, faults=[]):
        self.generated = []
        self.faults = faults

    def generate(self, suite, n_times=1):
        seed = Seed(suite, logs=self.generated)
        if n_times == 0:
            seed.dump()
        for test in suite.cases * n_times:
            for fault in self.faults:
                seed.fault = str(fault)
                for index in range(-1, 5):
                    cc = CodeBase(seed, test)
                    if cc.emsg != '':
                        print('\033[32m[ERROR]\033[0m', test,
                              f'\n\t{cc.code}\n\t{cc.emsg}')
                        break
                    if fault.precheck(cc, index):
                        fault.inject(cc, index)
                    else:
                        break
        return self.generated

    def dump(self):
        UNDEFINED = collections.Counter()
        ss = []
        for d in self.generated:
            d2 = convert_error_diagnosis(d, UNDEFINED=UNDEFINED)
            ss.append(d2)
            print(d['fault'], d2['eline'])
            print('\033[31m', d2['emsg'], '\033[0m')
            print('   \033[32m' + d2['hint'], '\033[0m')
            print('   \033[33m' + d2['desc'], '\033[0m')
            if 'fix' in d:
                print('   \033[36m' + d['fix'], '\033[0m')
        print(len(ss))
        print(UNDEFINED.most_common())


def DebugFaultSuite():
    import math

    _DEBUG = '''\
    `` abs float:数
    int from_bytes bytes byteorder='big'
    float:数 / int
    str replace str str
    math sin float #D信じるな
    str:シーケンス __get int
    dict __get str
    `` tuple list:かイテラブル
    '''

    def myfunc(x, y=0, z=0):
        return (y+z)/x
    suite = FaultSuite()
    suite.namespace = dict(
        import_math='import math',
        math=math,
        f=myfunc,
        bytes=b'000',
    )
    suite.specs = []
    suite.testcase(_DEBUG)
    return suite


if __name__ == '__main__':
    gen = Generator(faults=DebugFaults)
    # gen = Generator()
    gen.generate(DebugFaultSuite(), n_times=1)
    gen.dump()
