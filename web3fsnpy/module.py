from eth_utils.toolz import (
    curry,
    pipe,
)


@curry
def retrieve_blocking_method_call_fn(w3, module, method):
    def caller(*args, **kwargs):
        (method_str, params), output_formatters = method.process_params(module, *args, **kwargs)
        return pipe(
            w3.manager.request_blocking(method_str, params),
            *output_formatters)
    return caller


@curry
def retrieve_async_method_call_fn(w3, module, method):
    async def caller(*args, **kwargs):
        (method_str, params), output_formatters = method.process_params(module, *args, **kwargs)
        raw_result = await w3.manager.coro_request(method_str, params)
        return pipe(raw_result, *output_formatters)
    return caller


#  TODO: Replace this with ModuleV2 when ready.
class Module:
    web3fsnpy = None

    def __init__(self, web3fsnpy):
        self.web3fsnpy = web3fsnpy

    @classmethod
    def attach(cls, target, module_name=None):
        if not module_name:
            module_name = cls.__name__.lower()

        if hasattr(target, module_name):
            raise AttributeError(
                "Cannot set {0} module named '{1}'.  The web3fsnpy object "
                "already has an attribute with that name".format(
                    target,
                    module_name,
                )
            )

        if isinstance(target, Module):
            web3fsnpy = target.web3fsnpy
        else:
            web3fsnpy = target

        setattr(target, module_name, cls(web3fsnpy))


#  Module should no longer have access to the full web3fsnpy api.
#  Only the calling functions need access to the request methods.
#  Any "re-entrant" shinanigans can go in the middlewares, which do
#  have web3fsnpy access.
class ModuleV2(Module):
    is_async = False

    def __init__(self, web3fsnpy):
        if self.is_async:
            self.retrieve_caller_fn = retrieve_async_method_call_fn(web3fsnpy, self)
        else:
            self.retrieve_caller_fn = retrieve_blocking_method_call_fn(web3fsnpy, self)
