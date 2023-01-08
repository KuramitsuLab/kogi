from expr import spec, old_testcase

API = '''\
`` abs <float>
`` all <iterable>
`` any <iterable>
`` ascii <object>
`` bin <int>
`` bool <int>
`` bytearray <str> encoding="utf-8"
`` bytes <str> encoding="utf-8"
`` bytearray <str> errors="ignore"
`` bytes <str> errors="strict"
`` bool <int>
`` callable <func>
`` chr <int>
`` complex <int> <int>
`` complex <str>
`` delattr <object> <name>
`` dir <object>
`` dict <dict>
`` divmod <int> <int>
`` enumerate <iterable>
`` enumerate <iterable> <int>
`` enumerate <iterable> start=0
`` filter <func> <iterable>
`` float <str>
`` float <int>
`` frozenset <iterable>
`` getattr <object> <name>
`` hasattr <object> <name>
`` hash <object>
`` hex <int>
`` id <object>
`` int <str>
`` int <str> <int>
`` int <str> base=16
`` isinstance <object> <class>
`` issubclass <class> <class>
`` iter <seq>
`` iter <seq> <int>
`` len <seq>
`` list <iterable>
`` map <func> <iterable>
`` max <iterable>
`` max <int> <int>
`` min <iterable>
`` min <int> <int>
`` next <iterator>
`` oct <int>
`` open <filename>
`` ord <str>
`` pow <int> <int>
`` pow <int> <int> <int>
`` print <str>
`` print <str> sep=":"
`` print <str> end=""
`` range <int>
`` range <int> <int>
`` range <int> <int> <int>
`` reversed <seq>
`` round <float>
`` round <float> <int>
`` set <iterable>
`` setattr <object> <name> <object>
`` slice <int>
`` slice <int> <int> <int>
`` sorted <iterable>
`` sorted <iterable> key=None
`` sorted <iterable> reverse=False
`` str <object>
`` str <bytes> encoding="utf-8"
`` str <bytes> errors="ignore"
`` sum <iterable>
`` sum <iterable> start=0
`` tuple <iterable>
`` type <object>
`` zip <iterable> <iterable>
'''
