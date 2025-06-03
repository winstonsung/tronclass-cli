from tronclass_cli.api.auth.zjuam import ZjuamAuthProvider
from tronclass_cli.api.auth.tkuam import TkuamAuthProvider
_auth_providers = {'zju': ZjuamAuthProvider, 'tku': TkuamAuthProvider}


def get_auth_provider(name):
    return _auth_providers[name]


def get_all_auth_providers():
    return _auth_providers
